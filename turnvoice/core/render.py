import os
from typing import List

DEBUG_LOG = True

# precise, balanced, forgiving
# precise is strict, balanced is between strict and forgiving approaches)
TIME_HANDLING_POLICY = "forgiving"
TIME_HANDLING_CORRECTION = 0.2  # seconds


def render_video(
        p_input_video: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        p_language: str = "",
        p_input_language: str = "",
        p_download_directory: str = "downloads",
        p_synthesis_directory: str = "synthesis",
        p_extract_disabled: bool = False,
        p_voices: List[str] = ["male.wav"],
        p_engine: str = "coqui",
        p_output_video: str = "final_cut.mp4",
        p_clean_audio: bool = False,
        p_limit_start_time: str = None,
        p_limit_end_time: str = None,
        p_analysis: bool = False,
        p_speaker_number: str = "",
        p_num_speakers: int = 0,
        p_min_speakers: int = 0,
        p_max_speakers: int = 0,
        p_time_files: List[str] = [],
        p_prompt: str = None,
        ):
    """
    Video Processing Workflow covering downloading, audio extraction,
    transcription, synthesis, and video combination.

    Downloads a YouTube video, transcribes its audio, and replaces
    the original voice with a synthetic one.

    Parameters:
    p_input_video (str): URL of the YouTube video.
    p_language (str): Language code for synthesis translation.
    p_input_language (str): Language code for transcription. Can be set
        in case automatical detection goes wrong.
    p_download_directory (str): Directory to save downloaded files.
    p_synthesis_directory (str): Directory to save synthesized audio files.
    p_extract_disabled (bool): Whether to disable extraction of audio from the
        video file (and perform download instead).
    p_voices (List[str]): Voice or voices used for synthesis.
    p_output_video (str): Filename for the output video with synthetic voice.
    p_clean_audio (bool): No preserve of original audio in the final video.
        Returns clean synthesis.
    p_limit_start_time (str): Time to start processing the video from.
    p_limit_end_time (str): Time to stop processing the video at.
    p_analysis (bool): Prints analysis of the video.
    p_speaker_number (str): Speaker number to be turned.
    p_num_speakers (int): Helps diarization. Specify the exact number of
        speakers in the video if you know it in advance.
    p_min_speakers (int): Helps diarization. Specify the minimum number of
        speakers in the video if you know it in advance.
    p_max_speakers (int): Helps diarization. Specify the maximum number of
        speakers in the video if you know it in advance.
    p_time_files (List[str]): Define timestamp file(s) for processing
        (basically performs multiple --from/--to)
    p_prompt (str): Text prompt for video processing instructions.
        For example, "speak like a pirate".
    """

    from .cli import verify_install
    if not verify_install("spleeter", "rubberband"):
        return

    from .transcribe import (
        faster_transcribe,
        unload_faster_model,
        extract_words
    )
    from .cut import (
        create_composite_audio,
        overlay_audio_on_video,
        merge_video_audio,
        merge_audios,
        split_audio
    )
    from .fragtokenizer import (
        create_synthesizable_fragments,
        merge_short_sentences,
        assign_fragments_to_sentences,
        start_full_sentence_characters
    )
    from .download import (
        fetch_youtube_extract,
        check_youtube,
        local_file_extract,
        ensure_youtube_url
    )
    from .diarize import (
        diarize,
        print_speakers,
        write_speaker_timefiles,
        speaker_files_exist,
        import_time_file,
        filter_speakers,
        time_to_seconds
    )
    from .translate import (
        translate,
        translate_model_unload
    )
    from .prompt import transform_sentences
    from os.path import basename, exists, join, splitext
    from moviepy.editor import AudioFileClip
    from .synthesis import Synthesis
    from .word import Word
    import json
    import time

    #
    # Ensure directories exist and log input parameters
    #

    if not os.path.exists(p_download_directory):
        os.makedirs(p_download_directory)

    if not os.path.exists(p_synthesis_directory):
        os.makedirs(p_synthesis_directory)

    processing_start_time = time.time()

    init_log_string = "input parameters: " \
                      f"input video: {p_input_video}, " \
                      f"language: {p_language}, " \
                      f"input language: {p_input_language}, " \
                      f"download directory: {p_download_directory}, " \
                      f"synthesis directory: {p_synthesis_directory}, " \
                      f"extract disabled: {p_extract_disabled}, " \
                      f"voices: {p_voices}, " \
                      f"output video: {p_output_video}, " \
                      f"preserve audio: {p_clean_audio}, " \
                      f"start: {p_limit_start_time}, " \
                      f"end: {p_limit_end_time}, " \
                      f"analysis: {p_analysis}, " \
                      f"speaker number: {p_speaker_number}, " \
                      f"num speakers: {p_num_speakers}, " \
                      f"min speakers: {p_min_speakers}, " \
                      f"max speakers: {p_max_speakers}, " \
                      f"time files: {p_time_files}, " \
                      f"prompt: {p_prompt}"

    print(init_log_string)

    if p_synthesis_directory and not os.path.exists(p_synthesis_directory):
        os.makedirs(p_synthesis_directory)

    if p_download_directory and not os.path.exists(p_download_directory):
        os.makedirs(p_download_directory)

    #
    # Download video and audio
    # - ensures a audio file and a muted video file exist
    #

    print("checking if url is youtube url...")
    if check_youtube(p_input_video):

        print("finished checking")
        p_input_video = ensure_youtube_url(p_input_video)

        print(f"[{(time.time() - processing_start_time):.1f}s] "
              "downloading video..."
              )
        audio_file, video_file_muted = fetch_youtube_extract(
            p_input_video,
            extract=not p_extract_disabled,
            directory=p_download_directory
            )
    else:
        print(f"[{(time.time() - processing_start_time):.1f}s] "
              "extracting from local file..."
              )
        audio_file, video_file_muted = local_file_extract(
            p_input_video,
            directory=p_download_directory
            )

    with AudioFileClip(audio_file) as audio_clip:
        duration = audio_clip.duration

    audio_file_name, _ = splitext(basename(audio_file))
    download_sub_directory = join(p_download_directory, audio_file_name)
    if not os.path.exists(download_sub_directory):

        print(f"[{(time.time() - processing_start_time):.1f}s] "
              f"creating download sub directory {download_sub_directory}..."
              )
        os.makedirs(download_sub_directory)

    #
    # Determine processing start and end times
    # - import time files
    #

    limit_times = None
    p_offset = 0
    p_duration = duration
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

    #
    # Start synthesis engine early
    # (we want it to grab VRAM asap to avoid it to bottleneck)
    #

    print(f"[{(time.time() - processing_start_time):.1f}s] "
          "early start synthesis engine (grab vram)..."
          )
    synthesis = Synthesis(
        language=p_language,
        voices=p_voices,
        engine_name=p_engine
        )

    #
    # Split audio into vocals and accompaniment
    #

    if not p_clean_audio:

        print(f"[{(time.time() - processing_start_time):.1f}s] "
              "splitting audio..."
              )
        vocal_path, accompaniment_path = split_audio(
            audio_file,
            p_download_directory,
            p_offset, p_duration
        )

    #
    # Transcribe audio to text
    #

    print(f"[{(time.time() - processing_start_time):.1f}s] "
          f"transcribing audio {audio_file} with "
          "faster_whisper...", end="", flush=True
          )
    transcribed_segments, transcription_info = faster_transcribe(
        audio_file,
        language=p_input_language,
        model="large-v2"
        )

    detected_input_language = transcription_info.language

    print(f"[{(time.time() - processing_start_time):.1f}s] "
          "input language detected from transcription: "
          f"{detected_input_language}"
          )

    synthesis_language = (
        p_language if len(p_language) > 0 else detected_input_language
    )

    print(f"[{(time.time() - processing_start_time):.1f}s] "
          "output language selected for synthesis: "
          f"{detected_input_language}"
          )

    #
    # Extract words with precise timestamps from transcription
    #

    words_file = join(download_sub_directory, "words.txt")
    if exists(words_file):
        print(f"[{(time.time() - processing_start_time):.1f}s] "
              f"words already exist, loading from {words_file}..."
              )
        with open(words_file, 'r') as f:
            words_dicts = json.load(f)

        words = [Word(**word_dict) for word_dict in words_dicts]

    else:
        print(f"[{(time.time() - processing_start_time):.1f}s] "
              f"extracting words...", end="", flush=True
              )
        words = extract_words(transcribed_segments)

        # Serialize words as json into download sub directory
        print(f"[{(time.time() - processing_start_time):.1f}s] "
              f"saving words to {words_file}..."
              )
        with open(words_file, "w") as f:
            json.dump([word.__dict__ for word in words], f, indent=4)
        print(f"[{(time.time() - processing_start_time):.1f}s] "
              "words saved successfully."
              )

    if DEBUG_LOG:
        print("Words:")
        for word in words:
            print(f"{word.start:.1f}s - {word.end:.1f}s: "
                  f"{word.text}  ", flush=True, end=""
                  )
        print()

    #
    # Only keep all words within the time limits
    #

    def is_overlap(t1start, t1end, t2start, t2end):
        if t1end <= t2start or t2end <= t1start:
            return False
        return True

    if limit_times:

        print("filtering words by time file...")
        new_words = []

        for word in words:
            for time_start, time_end in limit_times:
                tstart = time_start
                tend = time_end
                tstartc = time_start - TIME_HANDLING_CORRECTION
                tendc = time_end + TIME_HANDLING_CORRECTION

                if TIME_HANDLING_POLICY == "precise":
                    if word.start >= tstart and word.end <= tend:
                        new_words.append(word)
                        break
                elif TIME_HANDLING_POLICY == "forgiving":
                    if is_overlap(word.start, word.end, tstartc, tendc):
                        new_words.append(word)
                        break
                elif TIME_HANDLING_POLICY == "balanced":
                    if is_overlap(word.start, word.end, tstart, tend):
                        new_words.append(word)
                        break
                else:
                    if word.start >= tstartc and word.end <= tendc:
                        new_words.append(word)
                        break
        words = new_words

        if DEBUG_LOG:
            print("Time filtered words:")
            for word in words:
                print(f"{word.start:.1f}s - {word.end:.1f}s: "
                      f"{word.text}  ", flush=True, end=""
                      )
            print()

    #
    # Perform speaker detection (diarization)
    #

    print(f"[{(time.time() - processing_start_time):.1f}s] analyzing audio...")

    speakers = diarize(
        vocal_path,
        p_num_speakers,
        p_min_speakers,
        p_max_speakers
        )

    speakers = filter_speakers(speakers, processing_start, processing_end)

    print_speakers(speakers)
    if not p_time_files or not speaker_files_exist(speakers):
        write_speaker_timefiles(speakers, download_sub_directory)
    if p_analysis:
        synthesis.close()
        return

    #
    # Assign words to speakers
    #

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
        words = new_words

        if DEBUG_LOG:

            print("Speaker filtered words:")
            for word in words:

                print(f"{word.start:.1f}s - {word.end:.1f}s: "
                      f"{word.text}  ", flush=True, end=""
                      )
            print()

    if len(words) == 0:

        print(f"[{(time.time() - processing_start_time):.1f}s] "
              "no words to be turned, aborting..."
              )
        synthesis.close()
        return

    print(f"[{(time.time() - processing_start_time):.1f}s] "
          f"{len(words)} words found..."
          )

    #
    # Generate synthesizable fragments from words
    # based on punctuation and gap size between words
    #

    print(f"[{(time.time() - processing_start_time):.1f}s] "
          "creating synthesizable fragments..."
          )
    synthesis.set_language(synthesis_language)

    sentence_fragments = create_synthesizable_fragments(words)
    full_sentences = create_synthesizable_fragments(
        words,
        break_characters=start_full_sentence_characters
        )

    #
    # Assign each fragment to it's parent full sentence
    #

    assign_fragments_to_sentences(sentence_fragments, full_sentences)

    for sentence in full_sentences:
        print(f'{sentence["text"]} ({sentence["start"]:.1f}s - '
              f'{sentence["end"]:.1f}s) contains '
              f'{len(sentence["sentence_frags"])} fragments: '
              )
        for sentence_frag in sentence["sentence_frags"]:
            print(f'    {sentence_frag["text"]} '
                  f'({sentence_frag["start"]:.1f}s '
                  f'- {sentence_frag["end"]:.1f}s)'
                  )

    #
    # Performs prompt action (style transformation) if requested
    # this changes the tone of each sentence fragment
    # while being aware of the speaking duration and the
    # parent full sentence.
    #

    if p_prompt:
        print(f"[{(time.time() - processing_start_time):.1f}s] "
              f"transforming sentences, applying \"{p_prompt}\"..."
              )
        transform_sentences(full_sentences, p_prompt)

    for sentence in full_sentences:
        print(f'{sentence["text"]} ({sentence["start"]:.1f}s - '
              f'{sentence["end"]:.1f}s) contains '
              f'{len(sentence["sentence_frags"])} fragments: '
              )
        for sentence_frag in sentence["sentence_frags"]:
            print(f'    {sentence_frag["text"]} '
                  f'({sentence_frag["start"]:.1f}s '
                  f'- {sentence_frag["end"]:.1f}s)'
                  )

    #
    # Very short sentences are merged together.
    # This ensures higher synthesis quality.
    # Shorter sentences are more difficult to synthesize in 
    # the same duration that they were originally spoken,
    # especially when translated.
    #

    print(f"[{(time.time() - processing_start_time):.1f}s] "
          f"merging short sentences from {len(sentence_fragments)} "
          "sentences..."
          )
    sentence_fragments = merge_short_sentences(
        sentence_fragments,
        gap_duration=0.75,
        min_sentence_duration=1.5
        )
    print(f"[{(time.time() - processing_start_time):.1f}s] "
          f"{len(sentence_fragments)} merged sentences created..."
          )

    #
    # Assigning the sentences to the speakers based
    # on the best overlapping interval
    #

    def calculate_interval_overlap(start1, end1, start2, end2):
        if start2 > end1:
            return -(start2 - end1)
        if start1 > end2:
            return -(start1 - end2)
        maximum_start_time = max(start1, start2)
        minimum_end_time = min(end1, end2)
        return minimum_end_time - maximum_start_time

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

    unload_faster_model()

    #
    # Perform translation if requested
    #

    if len(p_language) > 0 and detected_input_language != p_language:

        print(f"[{(time.time() - processing_start_time):.1f}s] "
              f"translating from {detected_input_language} to {p_language}..."
              )

        for sentence in sentence_fragments:
            print(f"Translating \"{sentence['text']}\" from "
                  f"{detected_input_language} to {p_language}..."
                  )
            translated_sentence = translate(
                sentence["text"],
                source=detected_input_language,
                target=p_language
                )
            sentence["text"] = translated_sentence

        # get rid of translation model to free up VRAM
        translate_model_unload()

    #
    # Perform synthesis of each sentence fragment
    # while respecting the original speaking duration.
    # and save the synthesized audio to disk.
    #
    print(f"[{(time.time() - processing_start_time):.1f}s] "
          "synthesizing audio..."
          )
    synthesis.synthesize_sentences(
        sentence_fragments,
        p_synthesis_directory,
        processing_start_time
        )

    #
    # Filter sentences with a successful synthesis
    # based on synthesis_result
    #
    successful_synthesis_sentences = [
        sentence for sentence in sentence_fragments
        if sentence["synthesis_result"]
    ]

    sentence_fragments = successful_synthesis_sentences
    if len(sentence_fragments) == 0:

        print(f"[{(time.time() - processing_start_time):.1f}s] "
              "no successful synthesis (no sentences created), aborting..."
              )
        synthesis.close()
        return

    #
    # Combine all synthesized audio fragments into one audio file
    #
    final_cut_audio_path = "final_cut_audio.wav"
    print(f"[{(time.time() - processing_start_time):.1f}s] "
          "combining audio..."
          )

    create_composite_audio(
        sentence_fragments,
        p_synthesis_directory,
        duration,
        final_cut_audio_path
    )

    #
    # Render the combined audio and the muted video into one video file
    #
    if not p_clean_audio:
        #
        # Preparation of the background audiotrack.
        # We use the original audio when nothing was changed but
        # use the vocal-less audio as soon as we replaced a voice.
        # We word timestamps we aim at preserving as much
        # of the original audio as possible.
        # - add little time correction to the timestamps
        #   (due to word timestamp detection errors)
        # - merge the original audio with the vocal-less audio
        #
        time_stamps = []
        word_timestamp_correction = 0.5

        # Initial timestamp adjustment
        for sentence in sentence_fragments:
            start = max(0, sentence["start"] - word_timestamp_correction)
            end = min(sentence["end"] + word_timestamp_correction, duration)
            time_stamps.append((start, end))

        merged_time_stamps = []
        for start, end in time_stamps:
            if not merged_time_stamps:
                merged_time_stamps.append((start, end))
            else:
                start_prev, end_prev = merged_time_stamps[-1]
                if start < end_prev:
                    # Extend the end time of the
                    # previous segment if there is overlap
                    merged_time_stamps[-1] = (start_prev, max(end_prev, end))
                else:
                    # No overlap, add the segment as is
                    merged_time_stamps.append((start, end))

        time_stamps = merged_time_stamps

        #
        # Final merge cut of the background audio track
        #
        final_cut_audio_merged = "final_cut_audio_merged.wav"
        print(f"[{(time.time() - processing_start_time):.1f}s] merging "
              f"original {audio_file} and vocal less audios "
              f"{accompaniment_path} into {final_cut_audio_merged}..."
              )
        merge_audios(audio_file,
                     accompaniment_path,
                     time_stamps,
                     final_cut_audio_merged
                     )

        #
        # Finally render three things together:
        # - the synthesized audio track final_cut_audio_path
        # - the background audio track final_cut_audio_merged
        # - the muted video video_file_muted
        #
        print(f"[{(time.time() - processing_start_time):.1f}s] "
              f"combining {video_file_muted} together with audios "
              f"{final_cut_audio_path} and {final_cut_audio_merged} "
              f"into video {p_output_video}..."
              )
        total_duration = merge_video_audio(
            video_file_muted,
            final_cut_audio_path,
            final_cut_audio_merged,
            p_output_video
            )
    else:
        #
        # If we shall deliver a clean audio track, we only need to render
        # two things together:
        # - the synthesized audio track final_cut_audio_path
        # - the muted video video_file_muted
        #
        print(f"[{(time.time() - processing_start_time):.1f}s] "
              f"combining audio {final_cut_audio_path} with "
              f"video {video_file_muted} into {p_output_video}..."
              )
        total_duration = overlay_audio_on_video(
            final_cut_audio_path,
            video_file_muted,
            p_output_video)

    #
    # Some cleanup and stat presenting and we're done
    #
    synthesis.close()

    print(f"[{(time.time() - processing_start_time):.1f}s] "
          f"video processing complete: [[[ {p_output_video} ]]]"
          )
    if total_duration and total_duration > 0:
        calculation_duration = time.time() - processing_start_time
        realtime_factor = calculation_duration / total_duration

        print(f"[{(time.time() - processing_start_time):.1f}s] "
              f"calculation realtime factor for {total_duration:.1f}s "
              f"video: {realtime_factor:.2f}x"
              )

    # # open the final video cut with the default player
    # if os.name == 'nt':  # Windows
    #     os.startfile(p_output_video)
    # elif os.name == 'posix':
    #     if sys.platform == "darwin":  # macOS
    #         os.system(f"open '{p_output_video}'")
    #     else:  # Linux and other POSIX OS
    #         os.system(f"xdg-open '{p_output_video}'")