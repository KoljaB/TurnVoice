from pyannote.audio import Pipeline
from collections import defaultdict
import torch
import os
import re
import gc

access_token = os.getenv("HF_ACCESS_TOKEN")


def diarize(audio_file, num_speakers=0, min_speakers=0, max_speakers=0):
    """
    Perform speaker diarization on an audio file
    using a pre-trained model from pyannote.audio.

    Parameters:
    - audio_file (str): Path to the audio file.
    - num_speakers (int, optional): The number of speakers in the audio.
        Default is 0 (unknown).
    - min_speakers (int, optional): The minimum number of speakers
        expected in the audio. Default is 0.
    - max_speakers (int, optional): The maximum number of speakers
        expected in the audio. Default is 0.

    Returns:
    - list: A sorted list of dictionaries with speaker information
        ('name', 'total_time', 'segments').
    """

    print(f"Running diarization on {audio_file}...")

    access_token = os.getenv("HF_ACCESS_TOKEN")

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=access_token
    )

    # Send pipeline to GPU (when available)
    pipeline.to(torch.device("cuda"))
    print("Model moved to GPU.")

    # Prepare diarization options
    options = {}
    if num_speakers > 0:
        options['num_speakers'] = num_speakers
    if min_speakers > 0:
        options['min_speakers'] = min_speakers
    if max_speakers > 0:
        options['max_speakers'] = max_speakers

    # Apply diarization
    diarization = pipeline(audio_file, **options)
    results = [
        (turn.start, turn.end, speaker)
        for turn, _, speaker in diarization.itertracks(yield_label=True)
    ]

    # Print results
    for start, end, speaker in results:
        print(f"Speaker {speaker} ({start:.1f} - {end:.1f})")

    # Create a defaultdict to temporarily store the data
    temp_speaker_data = defaultdict(lambda: {"total_time": 0, "segments": []})

    # Process results
    for start, end, speaker_name in results:
        duration = end - start
        temp_speaker_data[speaker_name]["total_time"] += duration
        temp_speaker_data[speaker_name]["segments"].append(
            {"start": start, "end": end}
        )

    # Sort and format speaker data
    speakers = sorted(
        [
            {
                "name": name,
                "total_time": data["total_time"],
                "segments": data["segments"]
            }
            for name, data in temp_speaker_data.items()
        ],
        key=lambda x: x["total_time"],
        reverse=True,
    )

    # Clean-up resources
    del pipeline
    torch.cuda.empty_cache()
    gc.collect()

    return speakers


def print_speakers(speakers):
    """
    Prints the details of speakers detected in an audio file.

    This function lists each speaker along with their total time spoken.
    It also displays the time segments for when each speaker was talking.

    Args:
    speakers (list): A list of dictionaries where each dictionary
        represents a speaker. Each dictionary contains the total time
        spoken by the speaker and their speaking segments.
    """

    # Check the number of speakers and print it
    print(f"\nThere were {len(speakers)} speakers detected in the audio file. "
          "List of the speakers sorted by their total time spoken "
          "in descending order:")

    # Iterate over each speaker and print their details
    for speaker_number, speaker in enumerate(speakers, start=1):
        # Print total time spoken by the speaker
        print(f'Speaker {speaker_number} total: {speaker["total_time"]:.1f}s')

        # Iterate over each segment and print the start and end times
        for index, seg in enumerate(speaker["segments"]):
            print(f'  [{seg["start"]:.1f}s - {seg["end"]:.1f}s]', end="")

            # Add a new line after every 5 segments for better readability
            if (index + 1) % 5 == 0:
                print()

        # Print a newline for separation between speakers
        print()


def speaker_files_exist(speakers):
    """
    Checks if text files exist for each speaker.

    This function iterates over a list of speakers and checks if
    a corresponding text file named "speaker{speaker_number}.txt"
    exists for each speaker.

    Args:
    speakers (list): A list of speaker information, used to
        determine the number of speakers.

    Returns:
    bool: True if all speaker files exist, False otherwise.
    """

    # Iterate over each speaker
    for speaker_number, _ in enumerate(speakers, start=1):
        # Construct the filename for each speaker
        timefile = f"speaker{speaker_number}.txt"

        # Check if the file for the current speaker exists
        if not os.path.exists(timefile):
            # Return False immediately if a file is missing
            return False

    # Return True if all files are found
    return True


def import_time_file(timefile):
    """
    Imports a time file and returns a list of tuples.

    Parameters:
    - timefile (str): The path to the time file.

    Returns:
    - list: A list of tuples in the format of (start_time, end_time).
    """
    with open(timefile, "r") as f:
        lines = f.readlines()

    time_list = []

    for line in lines:
        # Remove whitespace and find time strings enclosed in square brackets
        line = line.strip()
        time_strings = re.findall(r"\[(.*?)\]", line)

        for time_string in time_strings:
            # Split each time string into start and end times
            start_time, end_time = time_string.split("-")

            # Convert time strings to seconds and add to list
            start_time = time_to_seconds(start_time)
            end_time = time_to_seconds(end_time)
            time_list.append((start_time, end_time))

    return time_list


def read_speaker_timefiles(directory):
    """
    Reads speaker time files and returns a list of dictionaries
    with speaker information.

    Each dictionary in the list contains 'name', 'total_time',
    and 'segments' keys.

    Returns:
    - list: A list of dictionaries where each dictionary contains the
        name, total time spoken, and speaking segments of a speaker.
    """

    speakers = []

    speaker_number = 1
    while True:
        timefile = f"speaker{speaker_number}.txt"
        timefile = os.path.join(directory, timefile)
        if not os.path.exists(timefile):
            break

        segments = import_time_file(timefile)
        total_time = sum(end - start for start, end in segments)
        speakers.append({
            "name": f"Speaker{speaker_number}",
            "total_time": total_time,
            "segments": segments
        })

        speaker_number += 1

    return speakers


def write_speaker_timefiles(speakers, directory):
    """
    Writes time information of speakers to individual text files.

    For each speaker, this function creates a text file named
    "speaker{speaker_number}.txt". The file contains the total time
    spoken by the speaker and the time segments of their speech.

    Args:
    speakers (list): A list of dictionaries where each dictionary
        represents a speaker. Each dictionary contains the total time
        spoken by the speaker and their speaking segments.
    """

    # Iterate over each speaker
    for speaker_number, speaker in enumerate(speakers, start=1):
        # Define the filename for each speaker
        timefile = f"speaker{speaker_number}.txt"
        timefile = os.path.join(directory, timefile)
        print(f"Writing time file for speaker {speaker_number} "
              f"to {timefile}...")

        # Open the file in write mode
        with open(timefile, "w") as f:
            # Write the total time spoken by the speaker
            f.write(f"Speaker {speaker_number} total: "
                    f"{speaker['total_time']:.1f}s\n\n")

            # Write each time segment of the speaker
            for segment in speaker["segments"]:
                f.write(f"[{segment['start']:.1f}-{segment['end']:.1f}]\n")


def time_to_seconds(time_str):
    """
    Converts a time string in various formats to seconds, now including hours,
    decimal seconds, plain numbers, and decimal seconds without 's'.

    Supported formats:
    - 'XhYmZs': X hours, Y minutes and Z seconds (e.g., '1h2m3s')
    - 'XmYs': X minutes and Y seconds (e.g., '3m23s')
    - 'X.Ys': X.Y seconds with decimal (e.g., '34.4s', '38.92255s')
    - 'X.Y': X.Y seconds without 's' (e.g., '34.4', '38.92255')
    - 'Xs': X seconds (e.g., '34s')
    - 'X:Y:Z': X hours, Y minutes and Z seconds (e.g., '1:02:03')
    - 'X:Y': X minutes and Y seconds (e.g., '3:00')
    - 'X': X seconds (e.g., '45')

    Parameters:
    - time_str (str): The time string to convert.

    Returns:
    - float: The number of seconds.
    """

    time_str = time_str.strip()

    # Regex patterns for different time formats
    pattern_hours_minutes_seconds = r'(\d+)h(\d+)m(\d+)s'
    pattern_minutes_seconds = r'(\d+)m(\d+)s'
    pattern_decimal_seconds = r'(\d+\.\d+)s?'
    pattern_seconds = r'(\d+)s'
    pattern_hours_colon = r'(\d+):(\d+):(\d+)'
    pattern_minutes_colon = r'(\d+):(\d+)'
    pattern_plain_number = r'^\d+$'

    # Match the time string against different patterns
    if re.match(pattern_hours_minutes_seconds, time_str):
        hours, minutes, seconds = map(
            int,
            re.findall(pattern_hours_minutes_seconds, time_str)[0]
        )
        return hours * 3600 + minutes * 60 + seconds
    elif re.match(pattern_minutes_seconds, time_str):
        minutes, seconds = map(
            int,
            re.findall(pattern_minutes_seconds, time_str)[0]
        )
        return minutes * 60 + seconds
    elif re.match(pattern_decimal_seconds, time_str):
        seconds = float(re.findall(pattern_decimal_seconds, time_str)[0])
        return seconds
    elif re.match(pattern_seconds, time_str):
        seconds = int(re.findall(pattern_seconds, time_str)[0])
        return seconds
    elif re.match(pattern_hours_colon, time_str):
        hours, minutes, seconds = map(
            int,
            re.findall(pattern_hours_colon, time_str)[0]
        )
        return hours * 3600 + minutes * 60 + seconds
    elif re.match(pattern_minutes_colon, time_str):
        minutes, seconds = map(
            int,
            re.findall(pattern_minutes_colon, time_str)[0]
        )
        return minutes * 60 + seconds
    elif re.match(pattern_plain_number, time_str):
        seconds = int(time_str)
        return seconds
    else:
        raise ValueError("Unsupported time format")


def filter_speakers(speakers, time_start=0, time_end=None):
    """
    Filters a list of speakers based on a specified time window.

    Parameters:
    - speakers (list): A list of speaker dictionaries.
    - time_start (int): The start time of the filtering window in seconds.
    - time_end (int): The end time of the filtering window in seconds.

    Returns:
    - list: A new list of speakers filtered by the given time window.
    """
    filtered_speakers = []

    for speaker in speakers:
        # Filter segments within the time window
        filtered_segments = []
        for segment in speaker['segments']:
            start, end = segment['start'], segment['end']
            # Check if segment overlaps with the time window
            if start <= time_end and end >= time_start:
                filtered_segments.append(segment)

        # Update speaker data if there are filtered segments
        if filtered_segments:

            total_time = sum(
                [seg['end'] - seg['start'] for seg in filtered_segments]
            )

            filtered_speaker = {
                'name': speaker['name'],
                'total_time': total_time,
                'segments': filtered_segments
            }
            filtered_speakers.append(filtered_speaker)

    return filtered_speakers
