from .download import (
    fetch_youtube_extract,
    check_youtube,
    local_file_extract,
    ensure_youtube_url
)
from .diarize import (
    import_time_file,
    time_to_seconds
)
from .transcribe import (
    extract_words
)
from typing import List, Optional
from os.path import exists, join
from .word import Word
import time
import json
import os


def ensure_directories(directories: List[Optional[str]]) -> None:
    for directory in directories:
        if directory is not None and not os.path.exists(directory):
            os.makedirs(directory)


def get_audio_and_muted_video(
    p_input_video,
    p_download_directory,
    p_extract_disabled
):

    print("checking if url is youtube url...")
    if check_youtube(p_input_video):

        print("finished checking")
        p_input_video = ensure_youtube_url(p_input_video)

        print("downloading video...")
        return fetch_youtube_extract(
            p_input_video,
            extract=not p_extract_disabled,
            directory=p_download_directory
            )
    else:
        print("extracting from local file...")
        return local_file_extract(
            p_input_video,
            directory=p_download_directory
            )


def get_processing_times(
    p_time_files,
    download_sub_directory,
    p_limit_start_time,
    p_limit_end_time,
    duration
):
    limit_times = None
    processing_start = 0
    processing_end = duration

    if p_time_files:
        limit_times = []
        for time_file in p_time_files:
            time_file_path = join(download_sub_directory, time_file)

            print(f"processing time file {time_file_path}...")
            limit_times.extend(import_time_file(time_file_path))

        print("processing will be limited to the following time ranges:")
        for single_time in limit_times:
            start_time, end_time = single_time
            print(f"[{start_time}s - {end_time}s] ", end="", flush=True)

        print()
    elif p_limit_start_time and p_limit_end_time:
        p_limit_start_time = time_to_seconds(p_limit_start_time)
        p_limit_end_time = time_to_seconds(p_limit_end_time)

        processing_start = p_limit_start_time
        processing_end = p_limit_end_time

        print(f"both start and end time specified, processing from "
              f"{p_limit_start_time:.1f} to {p_limit_end_time:.1f}"
              )
        limit_times = [(p_limit_start_time, p_limit_end_time)]
    elif p_limit_start_time:
        p_limit_start_time = time_to_seconds(p_limit_start_time)
        processing_start = p_limit_start_time

        print("start time specified, processing from "
              f"{p_limit_start_time:.1f} "
              f"to end (duration: {duration:.1f}s)"
              )
        limit_times = [(p_limit_start_time, duration)]
    elif p_limit_end_time:
        p_limit_end_time = time_to_seconds(p_limit_end_time)
        processing_end = p_limit_end_time

        print("end time specified, processing from start "
              f"to {p_limit_end_time:.1f}"
              )
        limit_times = [(0, p_limit_end_time)]

    return limit_times, processing_start, processing_end


def get_extracted_words(
    transcribed_segments,
    words_file="words.txt",
    download_sub_directory="downloads",
    processing_start_time=time.time()
):
    words_file = join(download_sub_directory, words_file)
    if exists(words_file):

        print(f"[{(time.time() - processing_start_time):.1f}s] "
              f"words already exist, loading from {words_file}..."
              )
        with open(words_file, 'r') as f:
            words_dicts = json.load(f)

        words = [Word(**word_dict) for word_dict in words_dicts]

        return words

    else:
        print(f"[{(time.time() - processing_start_time):.1f}s] "
              f"extracting words...", end="", flush=True
              )
        words = extract_words(transcribed_segments)

        print(f"[{(time.time() - processing_start_time):.1f}s] "
              f"saving words to {words_file}..."
              )
        with open(words_file, "w") as f:
            json.dump([word.__dict__ for word in words], f, indent=4)

        print(f"[{(time.time() - processing_start_time):.1f}s] "
              "words saved successfully."
              )

        return words


def intervals_overlap(t1start, t1end, t2start, t2end):
    if t1end <= t2start or t2end <= t1start:
        return False
    return True


def filter_by_time_limits(
    words,
    limit_times,
    time_handling_policy,
    word_timestamp_correction,
):
    if limit_times:

        print("filtering words by time file...")
        new_words = []

        for word in words:
            for time_start, time_end in limit_times:
                tstart = time_start
                tend = time_end
                tstartc = time_start - word_timestamp_correction
                tendc = time_end + word_timestamp_correction

                if time_handling_policy == "precise":
                    if word.start >= tstart and word.end <= tend:
                        new_words.append(word)
                        break
                elif time_handling_policy == "forgiving":
                    if intervals_overlap(word.start, word.end, tstartc, tendc):
                        new_words.append(word)
                        break
                elif time_handling_policy == "balanced":
                    if intervals_overlap(word.start, word.end, tstart, tend):
                        new_words.append(word)
                        break
                else:
                    if word.start >= tstartc and word.end <= tendc:
                        new_words.append(word)
                        break
        return new_words
    return words


def filter_by_speaker(
    p_speaker_number,
    words,
    speakers
):
    if len(p_speaker_number) > 0:
        new_words = []
        for speaker_index, speaker in enumerate(speakers, start=1):
            if str(speaker_index) == p_speaker_number:

                print("filtering words by speaker number "
                      f"{p_speaker_number}..."
                      )
                for word in words:
                    middle_word = (word.start + word.end) / 2
                    for segment in speaker["segments"]:
                        if segment["start"] <= middle_word <= segment["end"]:
                            new_words.append(word)
                            break
        return new_words
    return words


def calculate_interval_overlap(start1, end1, start2, end2):
    if start2 > end1:
        return -(start2 - end1)
    if start1 > end2:
        return -(start1 - end2)
    maximum_start_time = max(start1, start2)
    minimum_end_time = min(end1, end2)
    return minimum_end_time - maximum_start_time


def assign_sentence_to_speakers(sentence_fragments, speakers):
    for sentence in sentence_fragments:
        max_overlap = 0
        assigned_speaker_index = 0

        for speaker_index, speaker in enumerate(speakers):
            for segment in speaker["segments"]:

                overlap = calculate_interval_overlap(
                    sentence["start"],
                    sentence["end"],
                    segment["start"],
                    segment["end"]
                    )

                if overlap > max_overlap:
                    max_overlap = overlap
                    assigned_speaker_index = speaker_index

        sentence["speaker_index"] = assigned_speaker_index
        print(f"Assigning {sentence['text']} to "
              f"speaker {assigned_speaker_index}"
              )
