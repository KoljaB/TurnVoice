from moviepy.editor import AudioFileClip
from typing import List
import time


def synthesize_and_render(
        sentence_fragments,
        p_synthesis_directory,
        p_clean_audio,
        audio_file,
        accompaniment_path,
        video_file_muted,
        p_output_video,
        t_start,
        synthesis
        ):

    from .cut import (
        create_composite_audio,
        overlay_audio_on_video,
        merge_video_audio,
        merge_audios,
    )

    with AudioFileClip(audio_file) as audio_clip:
        duration = audio_clip.duration

    # Perform synthesis of each sentence fragment
    # while respecting the original speaking duration.
    # and save the synthesized audio to disk.
    print(f"[{(time.time() - t_start):.1f}s] "
          "synthesizing audio..."
          )
    synthesis.synthesize_sentences(
        sentence_fragments,
        p_synthesis_directory,
        t_start
        )

    # Filter sentences with a successful synthesis
    # based on synthesis_result
    successful_synthesis_sentences = [
        sentence for sentence in sentence_fragments
        if sentence["synthesis_result"]
    ]

    sentence_fragments = successful_synthesis_sentences
    if len(sentence_fragments) == 0:

        print(f"[{(time.time() - t_start):.1f}s] "
              "no successful synthesis (no sentences created), aborting..."
              )
        synthesis.close()
        return

    # Combine all synthesized audio fragments into one audio file
    final_cut_audio_path = "final_cut_audio.wav"
    print(f"[{(time.time() - t_start):.1f}s] "
          "combining audio..."
          )

    create_composite_audio(
        sentence_fragments,
        p_synthesis_directory,
        duration,
        final_cut_audio_path
    )

    # Render the combined audio and the muted video into one video file
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
        print(f"[{(time.time() - t_start):.1f}s] merging "
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
        print(f"[{(time.time() - t_start):.1f}s] "
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
        print(f"[{(time.time() - t_start):.1f}s] "
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

    print(f"[{(time.time() - t_start):.1f}s] "
          f"video processing complete: [[[ {p_output_video} ]]]"
          )
    if total_duration and total_duration > 0:
        calculation_duration = time.time() - t_start
        realtime_factor = calculation_duration / total_duration

        print(f"[{(time.time() - t_start):.1f}s] "
              f"calculation realtime factor for {total_duration:.1f}s "
              f"video: {realtime_factor:.2f}x"
              )


def prepare_and_start_rendering(
        p_input_video: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        p_target_language: str = "",
        p_source_language: str = "",
        p_download_directory: str = "downloads",
        p_synthesis_directory: str = "synthesis",
        p_extract_disabled: bool = False,
        p_voices: List[str] = None,
        p_engines: List[str] = ["coqui"],
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
        p_debug: bool = False,
        p_prepare: bool = False,
        p_render: str = None
        ):
    """
    Video Processing Workflow covering downloading, audio extraction,
    transcription, synthesis, and video combination.

    Downloads a YouTube video, transcribes its audio, and replaces
    the original voice with a synthetic one.

    Parameters:
    p_input_video (str): Path to local video or URL or ID of a YouTube video.
    p_target_language (str): Target language code for synthesis translation.
    p_source_language (str): Source language code for transcription.
        Automatically detected. Can be set manually in case that fails.
    p_download_directory (str): Directory to save downloaded files.
    p_synthesis_directory (str): Directory to save synthesized audio files.
    p_extract_disabled (bool): Whether to disable extraction of audio from the
        video file (and perform download instead). Can result in higher
        quality but takes longer.
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
    p_debug (bool): Prints extended debugging output.
    p_prepare (bool): Generates full script with speaker analysis, sentence
        prompt transformation and translation. Can be continued.
    p_render (str): Renders a prepared full script.
    """
    t_start = time.time()

    from .cli import verify_install
    if not verify_install("spleeter", "rubberband"):
        return

    from .transcribe import (
        faster_transcribe,
        unload_faster_model
    )
    from .cut import (
        split_audio
    )
    from .fragtokenizer import (
        create_synthesizable_fragments,
        merge_short_sentences,
        assign_fragments_to_sentences,
        start_full_sentence_characters
    )
    from .diarize import (
        diarize,
        print_speakers,
        write_speaker_timefiles,
        speaker_files_exist,
        filter_speakers,
    )
    from .processing import (
        ensure_directories,
        get_audio_and_muted_video,
        get_processing_times,
        get_extracted_words,
        filter_by_time_limits,
        filter_by_speaker,
        assign_sentence_to_speakers
    )
    from .translate import perform_translation
    from .prompt import transform_sentences
    from os.path import basename, join, splitext
    from .synthesis import Synthesis
    import json

    ensure_directories([p_download_directory, p_synthesis_directory])

    print("input parameters: \n"
          f"- video: {p_input_video}\n"
          f"- translation language: {p_target_language}\n"
          f"- input video language: {p_source_language}\n"
          f"- download directory: {p_download_directory}\n"
          f"- synthesis directory: {p_synthesis_directory}\n"
          f"- extract disabled: {p_extract_disabled}\n"
          f"- voices: {p_voices}\n"
          f"- output video: {p_output_video}\n"
          f"- clean audio: {p_clean_audio}\n"
          f"- start: {p_limit_start_time}\n"
          f"- end: {p_limit_end_time}\n"
          f"- analysis: {p_analysis}\n"
          f"- speaker number: {p_speaker_number}\n"
          f"- num speakers: {p_num_speakers}\n"
          f"- min speakers: {p_min_speakers}\n"
          f"- max speakers: {p_max_speakers}\n"
          f"- time files: {p_time_files}\n"
          f"- prompt: {p_prompt}"
          )

    # Download video (if no local video provided)
    # Extract audio from video
    audio_file, video_file_muted = get_audio_and_muted_video(
        p_input_video,
        p_download_directory,
        p_extract_disabled
    )

    with AudioFileClip(audio_file) as audio_clip:
        duration = audio_clip.duration

    audio_file_name, _ = splitext(basename(audio_file))
    download_sub_directory = join(p_download_directory, audio_file_name)
    ensure_directories([download_sub_directory])

    # Determine processing start and end times
    # Consider time files if provided
    limit_times, processing_start, processing_end = get_processing_times(
        p_time_files,
        download_sub_directory,
        p_limit_start_time,
        p_limit_end_time,
        duration
    )

    # Split audio into vocals and accompaniment if not clean audio requested
    if not p_clean_audio:

        print(f"[{(time.time() - t_start):.1f}s] "
              "splitting audio..."
              )
        vocal_path, accompaniment_path = split_audio(
            audio_file,
            p_download_directory,
            0, duration
        )

    print(f"[{(time.time() - t_start):.1f}s] "
          "early start synthesis engine (grab vram)..."
          )

    if not p_analysis:
        synthesis = Synthesis(
            language=p_target_language,
            voices=p_voices,
            engine_names=p_engines
            )

    if p_render:
        with open(p_render, 'r') as file:
            sentence_fragments = json.load(file)

        synthesize_and_render(
            sentence_fragments,
            p_synthesis_directory,
            p_clean_audio,
            audio_file,
            accompaniment_path,
            video_file_muted,
            p_output_video,
            t_start,
            synthesis
            )

        return

    # Transcribe audio to text
    print(f"[{(time.time() - t_start):.1f}s] "
          f"transcribing audio {audio_file} with "
          "faster_whisper...", end="", flush=True
          )

    transcribed_segments, transcription_info = faster_transcribe(
        audio_file,
        language=p_source_language,
        model="large-v2"
        )

    # Determine synthesis and target language
    source_language = transcription_info.language
    synthesis_language = (
        p_target_language if len(p_target_language) > 0 else source_language
    )

    print(f"[{(time.time() - t_start):.1f}s] "
          "input language detected from transcription: "
          f"{source_language}\n"
          f"language selected for synthesis: {synthesis_language}"
          )

    # Extract words with precise timestamps from transcription
    words = get_extracted_words(
        transcribed_segments,
        "words.txt",
        download_sub_directory,
        t_start
        )

    if p_debug:
        print("Words:")
        for word in words:
            print(f"{word.start:.1f}s - {word.end:.1f}s: "
                  f"{word.text}  ", flush=True, end=""
                  )
        print()

    # Only keep all words within the time limits
    words = filter_by_time_limits(
        words,
        limit_times,
        "forgiving",
        0.2
        )

    if p_debug:
        print("Time filtered words:")
        for word in words:
            print(f"{word.start:.1f}s - {word.end:.1f}s: "
                  f"{word.text}  ", flush=True, end=""
                  )
        print()

    # Perform speaker detection (diarization)
    print(f"[{(time.time() - t_start):.1f}s] analyzing audio...")

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
        return

    # Filter words to a single speaker if requested
    words = filter_by_speaker(
        p_speaker_number,
        words,
        speakers
        )

    if len(p_speaker_number) > 0 and p_debug:

        print("Speaker filtered words:")
        for word in words:

            print(f"{word.start:.1f}s - {word.end:.1f}s: "
                  f"{word.text}  ", flush=True, end=""
                  )
        print()

    if len(words) == 0:

        print(f"[{(time.time() - t_start):.1f}s] "
              "no words to be turned, aborting..."
              )
        synthesis.close()
        return

    print(f"[{(time.time() - t_start):.1f}s] "
          f"{len(words)} words found..."
          )

    # Generate synthesizable fragments from words
    # based on punctuation and gap size between words
    print(f"[{(time.time() - t_start):.1f}s] "
          "creating synthesizable fragments..."
          )
    synthesis.set_language(synthesis_language)

    sentence_fragments = create_synthesizable_fragments(words)

    full_sentences = create_synthesizable_fragments(
        words,
        break_characters=start_full_sentence_characters
    )

    # Assign each fragment to it's parent full sentence
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

    # Performs prompt action (style transformation) if requested
    # this changes the tone of each sentence fragment
    # while being aware of the speaking duration and the
    # parent full sentence.
    if p_prompt:
        print(f"[{(time.time() - t_start):.1f}s] "
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

    # Very short sentences are merged together.
    # This ensures higher synthesis quality.
    # Shorter sentences are more difficult to synthesize in
    # the same duration that they were originally spoken,
    # especially when translated.
    print(f"[{(time.time() - t_start):.1f}s] "
          f"merging short sentences from {len(sentence_fragments)} "
          "sentences..."
          )
    sentence_fragments = merge_short_sentences(
        sentence_fragments,
        gap_duration=0.75,
        min_sentence_duration=1.5
        )
    print(f"[{(time.time() - t_start):.1f}s] "
          f"{len(sentence_fragments)} merged sentences created..."
          )

    # assign sentences to speakers based on best overlapping interval
    assign_sentence_to_speakers(sentence_fragments, speakers)

    unload_faster_model()

    perform_translation(
        sentence_fragments,
        source_language,
        p_target_language
    )

    # Open a file in write mode
    full_script_path = join(download_sub_directory, "full_script.txt")
    with open(full_script_path, 'w') as file:
        json.dump(sentence_fragments, file, indent=4)

    if p_prepare:
        print(f"[{(time.time() - t_start):.1f}s] "
              f"full script written to {full_script_path}\n"
              "preparation finished..."
              )
        synthesis.close()
        return

    synthesize_and_render(
        sentence_fragments,
        p_synthesis_directory,
        p_clean_audio,
        audio_file,
        accompaniment_path,
        video_file_muted,
        p_output_video,
        t_start,
        synthesis
    )
