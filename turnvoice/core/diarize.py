from pyannote.audio import Pipeline
from collections import defaultdict
import os

access_token = os.getenv("HF_ACCESS_TOKEN")

def diarize(audio_file):
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1", 
        use_auth_token=access_token)

    # send pipeline to GPU (when available)
    import torch
    pipeline.to(torch.device("cuda"))

    # apply pretrained pipeline
    diarization = pipeline(audio_file, num_speakers = 2)

    # print the result
    results = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        results.append((turn.start, turn.end, speaker))

    for start, end, speaker in results:
        print(f"Speaker {speaker} ({start:.1f} - {end:.1f})")

    # Create a defaultdict to temporarily store the data
    temp_speaker_data = defaultdict(lambda: {"total_time": 0, "segments": []})

    # Process the results
    for start, end, speaker_name in results:
        duration = end - start
        temp_speaker_data[speaker_name]["total_time"] += duration
        temp_speaker_data[speaker_name]["segments"].append({"start": start, "end": end})

    # Convert to the desired list of dictionaries format
    speakers = []
    for name, data in temp_speaker_data.items():
        speaker_info = {"name": name, "total_time": data["total_time"], "segments": data["segments"]}
        speakers.append(speaker_info)

    # Sort speakers by total time spoken in descending order
    speakers_sorted = sorted(speakers, key=lambda x: x["total_time"], reverse=True)
    speakers = speakers_sorted

    return speakers

def print_speakers(speakers):
    print ()
    print (f"There were {len(speakers)} speakers detected in the audio file. List of the speakers sorted by their total time spoken in descending order:")

    for speaker_number, speaker in enumerate(speakers, start=1):
        print(f'Speaker {speaker_number} total: {speaker["total_time"]:.1f}s') 

        for index, segment in enumerate(speaker["segments"]):
            print(f'  [{segment["start"]:.1f}s - {segment["end"]:.1f}s]', end="", flush=True)
            if (index + 1) % 5 == 0:
                print()
        print()
