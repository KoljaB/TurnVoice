from typing import List


def prepare_and_render(
        p_input_video: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        p_target_language: str = "",
        p_source_language: str = "",
        p_download_directory: str = "downloads",
        p_synthesis_directory: str = "synthesis",
        p_extract: bool = False,
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
        p_render: str = None,
        p_stable: bool = False
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
    p_extract (bool): Whether to enable extraction of audio from the
        video file (and perform download instead). Can result in lower
        quality but has lower file sizes.
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
    import time
    t_start = time.time()
    synthesis = None

    from .cli import verify_install
    if not verify_install("spleeter", "rubberband"):
        return

    from .processing import ensure_directories
    ensure_directories([p_download_directory, p_synthesis_directory])

    print("input parameters: \n"
          f"- video: {p_input_video}\n"
          f"- translation language: {p_target_language}\n"
          f"- input video language: {p_source_language}\n"
          f"- download directory: {p_download_directory}\n"
          f"- synthesis directory: {p_synthesis_directory}\n"
          f"- extract: {p_extract}\n"
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
          f"- debug: {p_debug}\n"
          f"- prepare: {p_prepare}\n"
          f"- render: {p_render}\n"
          )

    # Download video (if no local video provided)
    # Extract audio from video
    if not p_render:
        from .processing import get_audio_and_muted_video
        audio_file, video_file_muted = get_audio_and_muted_video(
            p_input_video,
            p_download_directory,
            p_extract
        )

        from moviepy.editor import AudioFileClip
        with AudioFileClip(audio_file) as audio_clip:
            duration = audio_clip.duration

        from os.path import basename, join, splitext
        audio_file_name, _ = splitext(basename(audio_file))
        download_sub_directory = join(p_download_directory, audio_file_name)
        ensure_directories([download_sub_directory])

        # Determine processing start and end times
        # Consider time files if provided
        from .processing import get_processing_times
        limit_times, processing_start, processing_end = get_processing_times(
            p_time_files,
            download_sub_directory,
            p_limit_start_time,
            p_limit_end_time,
            duration
        )

        # Split audio into vocals and accompaniment
        # if not clean audio requested
        if not p_clean_audio:

            print(f"[{(time.time() - t_start):.1f}s] "
                  "splitting audio..."
                  )
            from .cut import split_audio
            vocal_path, accompaniment_path = split_audio(
                audio_file,
                p_download_directory
            )

        print(f"[{(time.time() - t_start):.1f}s] "
              f"splitting finished, vocal path is {vocal_path}..."
              )

    if not p_analysis and not p_prepare:
        print(f"[{(time.time() - t_start):.1f}s] "
              "early start synthesis engine (grab vram)..."
              )

        from .synthesis import Synthesis
        synthesis = Synthesis(
            language=p_target_language,
            voices=p_voices,
            engine_names=p_engines
            )

    # Render a prepared full script if requested
    import json
    if p_render:

        with open(p_render, 'r', encoding='utf-8') as file:
            full_script = json.load(file)

        from .render import render_video
        render_video(
            full_script["sentences"],
            full_script["metadata"]["synthesis_language"],
            full_script["metadata"]["synthesis_directory"],
            full_script["metadata"]["clean_audio"],
            full_script["metadata"]["audio_file"],
            full_script["metadata"]["accompaniment_path"],
            full_script["metadata"]["video_file_muted"],
            full_script["metadata"]["output_video"],
            time.time(),
            synthesis
            )

        return

    # Transcribe audio to text
    transcription_audio = vocal_path
    print(f"[{(time.time() - t_start):.1f}s] "
          f"transcribing audio {transcription_audio} with "
          "stable_whisper..." if p_stable else "faster_whisper...",
          end="", flush=True
          )

    from .transcribe import transcribe
    transcribed_segments, transcription_info = transcribe(
        transcription_audio,
        language=p_source_language,
        model="large-v2",
        use_stable=p_stable
        )

    # Determine synthesis and target language
    source_language = transcription_info.language

    # Extract words with precise timestamps from transcription
    from .processing import get_extracted_words
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
    from .processing import filter_by_time_limits
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

    from .diarize import diarize
    speakers = diarize(
        vocal_path,
        p_num_speakers,
        p_min_speakers,
        p_max_speakers
        )

    from .diarize import filter_speakers
    speakers = filter_speakers(speakers, processing_start, processing_end)

    from .diarize import print_speakers, speaker_files_exist
    print_speakers(speakers)
    if not p_time_files or not speaker_files_exist(speakers):
        from .diarize import write_speaker_timefiles
        write_speaker_timefiles(speakers, download_sub_directory)
    if p_analysis:
        return

    # Filter words to a single speaker if requested
    from .processing import filter_by_speaker
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
        if synthesis:
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

    from .fragtokenizer import get_segments

    sentence_fragments = get_segments(transcribed_segments)

    from .fragtokenizer import create_synthesizable_fragments
    from .fragtokenizer import start_full_sentence_characters

    full_sentences = create_synthesizable_fragments(
        words,
        break_characters=start_full_sentence_characters
    )

    # Assign each fragment to it's parent full sentence
    from .fragtokenizer import assign_fragments_to_sentences
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
        from .prompt import transform_sentences
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

    # assign sentences to speakers based on best overlapping interval
    from .processing import assign_sentence_to_speakers
    assign_sentence_to_speakers(sentence_fragments, speakers)

    from .transcribe import unload_model
    unload_model(p_stable)

    from .translate import perform_translation
    perform_translation(
        sentence_fragments,
        source_language,
        p_target_language
    )

    # Determine and set synthesis language
    synthesis_language = (
        p_target_language if len(p_target_language) > 0 else source_language
    )

    print(f"[{(time.time() - t_start):.1f}s] "
          "input language detected from transcription: "
          f"{source_language}\n"
          f"language selected for synthesis: {synthesis_language}"
          )

    # transform pure youtube ID into url if needed
    input_video_path = p_input_video
    from .download import check_youtube, ensure_youtube_url
    if check_youtube(input_video_path):
        input_video_path = ensure_youtube_url(input_video_path)

    script_metadata = {
        "input_video": input_video_path,
        "download_sub_directory": download_sub_directory,
        "duration": duration,
        "target_language": p_target_language,
        "input_video_language": p_source_language,
        "synthesis_language": synthesis_language,
        "download_directory": p_download_directory,
        "synthesis_directory": p_synthesis_directory,
        "extract": p_extract,
        "voices": p_voices,
        "output_video": p_output_video,
        "clean_audio": p_clean_audio,
        "start": p_limit_start_time,
        "end": p_limit_end_time,
        "analysis": p_analysis,
        "speaker_number": p_speaker_number,
        "num_speakers": p_num_speakers,
        "min_speakers": p_min_speakers,
        "max_speakers": p_max_speakers,
        "time_files": p_time_files,
        "prompt": p_prompt,
        "render": p_render,
        "stable": p_stable,
        "audio_file": audio_file,
        "accompaniment_path": accompaniment_path,
        "video_file_muted": video_file_muted,
        "prepare_start": t_start,
    }
    full_script = {
        "metadata": script_metadata,
        "sentences": sentence_fragments
    }
    render_script_path = join(download_sub_directory, "render_script.txt")
    with open(render_script_path, 'w', encoding='utf-8') as file:
        json.dump(sentence_fragments, file, indent=4)
    full_script_path = join(download_sub_directory, "full_script.txt")
    with open(full_script_path, 'w', encoding='utf-8') as file:
        json.dump(full_script, file, indent=4)

    if p_prepare:
        print(f"[{(time.time() - t_start):.1f}s] "
              f"full script written to {full_script_path}\n"
              "preparation finished..."
              )
        return

    from .render import render_video
    render_video(
        sentence_fragments,
        synthesis_language,
        p_synthesis_directory,
        p_clean_audio,
        audio_file,
        accompaniment_path,
        video_file_muted,
        p_output_video,
        t_start,
        synthesis
    )
