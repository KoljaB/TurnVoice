import os
from typing import List

DEBUG_LOG = True
TIME_HANDLING_POLICY = "forgiving" # precise, balanced, forgiving (precise is strict, balanced is between strict and forgiving approaches)
TIME_HANDLING_CORRECTION = 0.2 # seconds

def is_spleeter_installed() -> bool:
    """
    Check if Deezer's Spleeter CLI is installed on the system.

    Returns:
    bool: True if Spleeter is installed, False otherwise.
    """
    import subprocess
    try:
        subprocess.run(["spleeter", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def process_video(
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

    Downloads a YouTube video, transcribes its audio, and replaces the original voice
    with a synthetic one.

    Parameters:
    p_input_video (str): URL of the YouTube video.
    p_language (str): Language code for synthesis translation.
    p_input_language (str): Language code for transcription. Can be set in case automatical detection goes wrong.
    p_download_directory (str): Directory to save downloaded files.
    p_synthesis_directory (str): Directory to save synthesized audio files.
    p_extract_disabled (bool): Whether to disable extraction of audio from the video file (and perform download instead).
    p_voices (List[str]): Voice or voices used for synthesis.
    p_output_video (str): Filename for the output video with synthetic voice.
    p_clean_audio (bool): No preserve of original audio in the final video. Returns clean synthesis.
    p_limit_start_time (str): Time to start processing the video from.
    p_limit_end_time (str): Time to stop processing the video at.
    p_analysis (bool): Prints analysis of the video.
    p_speaker_number (str): Speaker number to be turned.
    p_num_speakers (int): Helps diarization. Specify the exact number of speakers in the video if you know it in advance.
    p_min_speakers (int): Helps diarization. Specify the minimum number of speakers in the video if you know it in advance.
    p_max_speakers (int): Helps diarization. Specify the maximum number of speakers in the video if you know it in advance.
    p_time_files (List[str]): Define timestamp file(s) for processing (basically performs multiple --from/--to)
    p_prompt (str): Text prompt for video processing instructions. For example, "speak like a pirate".
    """

    from .transcribe import faster_transcribe, unload_faster_model, extract_words
    from .cut import create_composite_audio, overlay_audio_on_video, merge_video_audio, merge_audios, split_audio
    from .fragtokenizer import create_synthesizable_fragments, merge_short_sentences, create_full_sentences, assign_fragments_to_sentences, start_full_sentence_characters
    from .download import fetch_youtube_extract, check_youtube, local_file_extract, ensure_youtube_url
    from .diarize import diarize, print_speakers, write_speaker_timefiles, speaker_files_exist, import_time_file, filter_speakers, time_to_seconds
    from .translate import translate, translate_model_unload
    from .prompt import transform_sentences
    from os.path import basename, exists, join, splitext   
    from moviepy.editor import AudioFileClip
    from .synthesis import Synthesis
    from .word import Word    
    import json
    import time

    processing_start_time = time.time()
    extract = not p_extract_disabled

    if not is_spleeter_installed() and not p_clean_audio:
        p_clean_audio = True
        print ("Spleeter CLI is not installed, required for splitting original audio into vocals and accompaniment.")
        print ("Forced clean audio output.")
        print ("To install spleeter cli:")
        print ("- install python 3.8")
        print ("- run 'pipx install spleeter --python /path/to/python3.8' in your cli")

    init_log_string = f"turnvoice.py: process_video: input video: {p_input_video}, language: {p_language}, download_directory: {p_download_directory}, synthesis_directory: {p_synthesis_directory}, extract_disabled: {p_extract_disabled}, voices: {p_voices}, output_video: {p_output_video}, preserve_audio: {p_clean_audio}, start: {p_limit_start_time}, end: {p_limit_end_time}"
    print (init_log_string)

    if p_synthesis_directory and not os.path.exists(p_synthesis_directory):
        os.makedirs(p_synthesis_directory)

    if p_download_directory and not os.path.exists(p_download_directory):
        os.makedirs(p_download_directory)

    # download video and audio 
    print("checking if url is youtube url...")
    if check_youtube(p_input_video):
        print ("finished checking")
        p_input_video = ensure_youtube_url(p_input_video)
        print (f"[{(time.time() - processing_start_time):.1f}s] downloading video...")
        audio_file, video_file_muted = fetch_youtube_extract(p_input_video, extract=extract, directory=p_download_directory)
    else:
        print (f"[{(time.time() - processing_start_time):.1f}s] extracting from local file...")
        audio_file, video_file_muted = local_file_extract(p_input_video, directory=p_download_directory)

    with AudioFileClip(audio_file) as audio_clip:
        duration = audio_clip.duration

    audio_file_name, _ = splitext(basename(audio_file))
    download_sub_directory = join(p_download_directory, audio_file_name)
    if not os.path.exists(download_sub_directory):
        print (f"[{(time.time() - processing_start_time):.1f}s] creating download sub directory {download_sub_directory}...")
        os.makedirs(download_sub_directory)

    limit_times = None
    p_offset = 0
    p_duration = duration
    processing_start = 0
    processing_end = duration

    if p_time_files:
        limit_times = []
        for time_file in p_time_files:
            time_file_path = join(download_sub_directory, time_file)
            print (f"processing time file {time_file_path}...")
            limit_times.extend(import_time_file(time_file_path))

        print (f"processing will be limited to the following time ranges:")
        for single_time in limit_times:
            start_time, end_time = single_time
            print (f"[{start_time}s - {end_time}s] ", end="", flush=True)
        print()
    elif p_limit_start_time and p_limit_end_time:        
        p_limit_start_time = time_to_seconds(p_limit_start_time)
        p_limit_end_time = time_to_seconds(p_limit_end_time)
        processing_start = p_limit_start_time
        processing_end = p_limit_end_time
        print (f"both start and end time specified, processing from {p_limit_start_time:.1f} to {p_limit_end_time:.1f}")
        limit_times = [(p_limit_start_time, p_limit_end_time)]
    elif p_limit_start_time:        
        p_limit_start_time = time_to_seconds(p_limit_start_time)
        processing_start = p_limit_start_time
        print (f"start time specified, processing from {p_limit_start_time:.1f} to end (duration: {duration:.1f}s)")
        limit_times = [(p_limit_start_time, duration)]
    elif p_limit_end_time:
        p_limit_end_time = time_to_seconds(p_limit_end_time)
        processing_end = p_limit_end_time
        print (f"end time specified, processing from start to {p_limit_end_time:.1f}")
        limit_times = [(0, p_limit_end_time)]

    # start synthesis engine exactly before first 
    # early cause we want it to grab VRAM asap
    print (f"[{(time.time() - processing_start_time):.1f}s] early start synthesis engine (grab vram)...")
    synthesis = Synthesis(language=p_language, voices=p_voices, engine_name=p_engine)

    # split audio into vocals and accompaniment
    if not p_clean_audio:
        print (f"[{(time.time() - processing_start_time):.1f}s] splitting audio...")
        vocal_path, accompaniment_path = split_audio(audio_file, p_download_directory, p_offset, p_duration)

    # transcription (speech to text) of the audio
    print (f"[{(time.time() - processing_start_time):.1f}s] transcribing audio {audio_file} with faster_whisper...", end="", flush=True)
    transcribed_segments, transcription_info = faster_transcribe(audio_file, language=p_input_language, model="large-v2")

    detected_input_language = transcription_info.language
    print (f"[{(time.time() - processing_start_time):.1f}s] input language detected from transcription: {detected_input_language}")

    synthesis_language = p_language if len(p_language) > 0 else detected_input_language
    print (f"[{(time.time() - processing_start_time):.1f}s] output language selected for synthesis: {detected_input_language}")


    words_file = join(download_sub_directory, "words.txt")
    if exists(words_file):
        print (f"[{(time.time() - processing_start_time):.1f}s] words already exist, loading from {words_file}...")
        with open(words_file, 'r') as f:
            words_dicts = json.load(f)

        words = [Word(**word_dict) for word_dict in words_dicts]

    else:
        # extract words from the transcription
        print (f"[{(time.time() - processing_start_time):.1f}s] extracting words...", end="", flush=True)
        words = extract_words(transcribed_segments)

        # serialize words as json into download sub directory
        print (f"[{(time.time() - processing_start_time):.1f}s] saving words to {words_file}...")
        with open(words_file, "w") as f:
            json.dump([word.__dict__ for word in words], f, indent=4)
        print(f"[{(time.time() - processing_start_time):.1f}s] words saved successfully.")

    if DEBUG_LOG:
        print (f"Words:")
        for word in words:
            print (f"{word.start:.1f}s - {word.end:.1f}s: {word.text}  ", flush=True, end="")
        print ()    

    def is_overlap(t1start, t1end, t2start, t2end):
        # Check if there's no overlap
        if t1end <= t2start or t2end <= t1start:
            return False
        # Otherwise, there's an overlap
        return True        

    # Filter out words based on limit_times
    if limit_times:
        print (f"filtering words by time file...")
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
            print (f"Time filtered words:")
            for word in words:
                print (f"{word.start:.1f}s - {word.end:.1f}s: {word.text}  ", flush=True, end="")
            print ()    

    print (f"[{(time.time() - processing_start_time):.1f}s] analyzing audio...")

    speakers = diarize(vocal_path, p_num_speakers, p_min_speakers, p_max_speakers)
    speakers = filter_speakers(speakers, processing_start, processing_end)

    print_speakers(speakers)
    if not p_time_files or not speaker_files_exist(speakers):
        write_speaker_timefiles(speakers, download_sub_directory)
    if p_analysis:
        synthesis.close()
        return

    # filter words by speaker number
    if len(p_speaker_number) > 0:
        new_words = []
        for speaker_index, speaker in enumerate(speakers, start=1):
            if str(speaker_index) == p_speaker_number:
                print (f"filtering words by speaker number {p_speaker_number}...")
                for word in words:
                    middle_word = (word.start + word.end) / 2
                    for segment in speaker["segments"]:
                        if segment["start"] <= middle_word <= segment["end"]:
                            new_words.append(word)
                            break
        words = new_words

        if DEBUG_LOG:        
            print ("Speaker filtered words:")
            for word in words:
                print (f"{word.start:.1f}s - {word.end:.1f}s: {word.text}  ", flush=True, end="")
            print ()

    if len(words) == 0:
        print (f"[{(time.time() - processing_start_time):.1f}s] no words to be turned, aborting...")
        synthesis.close()
        return

    print (f"[{(time.time() - processing_start_time):.1f}s] {len(words)} words found...")

    # generate synthesizable fragments based on gaps and punctuation
    print (f"[{(time.time() - processing_start_time):.1f}s] creating synthesizable fragments...")
    synthesis.set_language(synthesis_language)

    sentence_fragments = create_synthesizable_fragments(words)
    full_sentences = create_synthesizable_fragments(words, break_characters=start_full_sentence_characters)
    
    assign_fragments_to_sentences(sentence_fragments, full_sentences)

    for sentence in full_sentences:
        print (f'{sentence["text"]} ({sentence["start"]:.1f}s - {sentence["end"]:.1f}s) contains {len(sentence["sentence_frags"])} fragments: ')
        for sentence_frag in sentence["sentence_frags"]:
            print (f'    {sentence_frag["text"]} ({sentence_frag["start"]:.1f}s - {sentence_frag["end"]:.1f}s)')

    if p_prompt:
        print (f"[{(time.time() - processing_start_time):.1f}s] transforming sentences, applying \"{p_prompt}\"...")
        transform_sentences(full_sentences, p_prompt)

    for sentence in full_sentences:
        print (f'{sentence["text"]} ({sentence["start"]:.1f}s - {sentence["end"]:.1f}s) contains {len(sentence["sentence_frags"])} fragments: ')
        for sentence_frag in sentence["sentence_frags"]:
            print (f'    {sentence_frag["text"]} ({sentence_frag["start"]:.1f}s - {sentence_frag["end"]:.1f}s)')

    # merging short sentences
    print (f"[{(time.time() - processing_start_time):.1f}s] merging short sentences from {len(sentence_fragments)} sentences...")
    sentence_fragments = merge_short_sentences(sentence_fragments, gap_duration=0.75, min_sentence_duration=1.5)
    print (f"[{(time.time() - processing_start_time):.1f}s] {len(sentence_fragments)} merged sentences created...")

    # if p_prompt:
    print (f"[{(time.time() - processing_start_time):.1f}s] assigning {len(sentence_fragments)} merged sentences to speakers...")

    def calculate_interval_overlap(start1, end1, start2, end2):
        if start2 > end1:
            return -(start2 - end1)
        if start1 > end2:
            return -(start1 - end2)
        maximum_start_time = max(start1, start2)
        minimum_end_time = min(end1, end2)
        return minimum_end_time - maximum_start_time

    # assign sentences to speakers
    for sentence in sentence_fragments:
        max_overlap = 0
        assigned_speaker_index = 0

        for speaker_index, speaker in enumerate(speakers):
            for segment in speaker["segments"]:

                overlap = calculate_interval_overlap(sentence["start"], sentence["end"], segment["start"], segment["end"])

                if overlap > max_overlap:
                    max_overlap = overlap
                    assigned_speaker_index = speaker_index

        sentence["speaker_index"] = assigned_speaker_index
        print(f"Assigning {sentence['text']} to speaker {assigned_speaker_index}")
        
    unload_faster_model()

    # translation if requested
    if len(p_language) > 0 and detected_input_language != p_language:

        print (f"[{(time.time() - processing_start_time):.1f}s] translating from {detected_input_language} to {p_language}...")

        for sentence in sentence_fragments:
            print (f"Translating \"{sentence['text']}\" from {detected_input_language} to {p_language}...")
            translated_sentence = translate(sentence["text"], source=detected_input_language, target=p_language)
            sentence["text"] = translated_sentence

        # get rid of translation model to free up VRAM
        translate_model_unload()

    # synthesis (text to speech) of the sentences incl fitting length of synthesized audio to the original audio
    print (f"[{(time.time() - processing_start_time):.1f}s] synthesizing audio...")
    synthesis.synthesize_sentences(sentence_fragments, p_synthesis_directory, processing_start_time)

    # combine the synthesized audio fragments into one audio file respecting the speech start times of the original audio
    final_cut_audio_path = "final_cut_audio.wav"
    print (f"[{(time.time() - processing_start_time):.1f}s] combining audio...")

    # filter sentences with a successful synthesis based on sentence["synthesis_result"] from sentences
    successful_synthesis_sentences = [sentence for sentence in sentence_fragments if sentence["synthesis_result"]]
    sentence_fragments = successful_synthesis_sentences
    if len(sentence_fragments) == 0:
        print (f"[{(time.time() - processing_start_time):.1f}s] no successful synthesis (no sentences created), aborting...")
        synthesis.close()
        return
    
    create_composite_audio(sentence_fragments, p_synthesis_directory, duration, final_cut_audio_path)

    if not p_clean_audio:
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
                    # Extend the end time of the previous segment if there is overlap
                    merged_time_stamps[-1] = (start_prev, max(end_prev, end))
                else:
                    # No overlap, add the segment as is
                    merged_time_stamps.append((start, end))
        
        time_stamps = merged_time_stamps

        # merge the synthesized audio with the original audio using timestamps
        # with timestamps we use the original audio when nothing was replaced and the vocal less audio when something was replaced
        # this is to preserve the original audio as much as possible
        final_cut_audio_merged = "final_cut_audio_merged.wav"
        print (f"[{(time.time() - processing_start_time):.1f}s] merging original {audio_file} and vocal less audios {accompaniment_path} into {final_cut_audio_merged}...")
        merge_audios(audio_file, accompaniment_path, time_stamps, final_cut_audio_merged)        

        # render the combined audio and the muted video into one video file
        print (f"[{(time.time() - processing_start_time):.1f}s] combining {video_file_muted} together with audios {final_cut_audio_path} and {final_cut_audio_merged} into video {p_output_video}...")
        total_duration = merge_video_audio(video_file_muted, final_cut_audio_path, final_cut_audio_merged, p_output_video)
    else:
        # render the combined audio and the muted video into one video file
        print (f"[{(time.time() - processing_start_time):.1f}s] combining audio {final_cut_audio_path} with video {video_file_muted} into {p_output_video}...")
        total_duration = overlay_audio_on_video(final_cut_audio_path, video_file_muted, p_output_video)

    # cleanup
    synthesis.close()

    # present stats
    print (f"[{(time.time() - processing_start_time):.1f}s] video processing complete: [[[ {p_output_video} ]]]")
    if total_duration and total_duration > 0:
        calculation_duration = time.time() - processing_start_time
        realtime_factor = calculation_duration / total_duration
        print (f"[{(time.time() - processing_start_time):.1f}s] calculation realtime factor for {total_duration:.1f}s video: {realtime_factor:.2f}x")

    # open the final video cut with the default player
    if os.name == 'nt':  # Windows
        os.startfile(p_output_video)
    elif os.name == 'posix':
        if sys.platform == "darwin":  # macOS
            os.system(f"open '{p_output_video}'")
        else:  # Linux and other POSIX OS
            os.system(f"xdg-open '{p_output_video}'")


def main():
    import argparse    
    parser = argparse.ArgumentParser(description="Replaces voices in Youtube videos. Can translate.")

    # URL as both positional and optional argument
    parser.add_argument('inputvideo', nargs='?', type=str, help='Input video. URL or ID of a YouTube video or path to a local video. (Positional)')
    parser.add_argument('-i', '--in', dest='source', type=str, help='Input video. URL or ID of a YouTube video or path to a local video. (Optional)')

    # Language as both positional and optional argument
    parser.add_argument('language', nargs='?', type=str, default='', help='Language code for translation. (Positional)')
    parser.add_argument('-l', '--language', dest='language_optional', type=str, help='Language code for translation. (Optional)')

    parser.add_argument('-il', '--input_language', type=str, default='', help='Language code for transcription. Can be set in case automatical detection goes wrong. (Optional)')
    parser.add_argument('-v', '--voice', nargs='+', help='Reference voices for synthesis. Accepts multiple values ro replace more than one speaker.')
    parser.add_argument('-o', '--output_video', '-out', type=str, default='final_cut.mp4', help='Filename for the final cut output video.')
    parser.add_argument('-a', '--analysis', action='store_true', help='Prints transcription and speaker analysis, then aborts without synthesizing and rendering. (Optional)')
    parser.add_argument('-from', '--from', dest='_from', type=str, help='Time to start processing the video from. (Optional)')
    parser.add_argument('-to', '--to', type=str, help='Time to stop processing the video at. (Optional)')
    parser.add_argument('-e', '--engine', type=str, default='coqui', help='Engine to synthesize with. Can be coqui, elevenlabs, azure, openai or system. (Optional, uses coqui as default)')   
    parser.add_argument('-s', '--speaker', type=str, default='', help='Speaker number to be turned. (Optional)')
    parser.add_argument('-snum', '--num_speakers', type=int, default='0', help='Helps diarization. Specify the exact number of speakers in the video if you know it in advance. (Optional)')
    parser.add_argument('-smin', '--min_speakers', type=int, default='0', help='Helps diarization. Specify the minimum number of speakers in the video if you know it in advance. (Optional)')
    parser.add_argument('-smax', '--max_speakers', type=int, default='0', help='Helps diarization. Specify the maximum number of speakers in the video if you know it in advance. (Optional)')
    parser.add_argument('-dd', '--download_directory', type=str, default='downloads', help='Directory to save downloaded files. (Optional)')
    parser.add_argument('-sd', '--synthesis_directory', type=str, default='synthesis', help='Directory to save synthesized audio files. (Optional)')
    parser.add_argument('-exoff', '--extractoff', action='store_true', help='Disables extraction of audio from the video file. Downloads audio and video files from the internet. (Optional)')
    parser.add_argument('-c', '--clean_audio', action='store_true', help='No preserve of original audio in the final video. Returns clean synthesis. (Optional)')
    parser.add_argument('-tf', '--timefile', nargs='?', help='Define timestamp file(s) for processing (basically performs multiple --from/--to) (Optional)')
    parser.add_argument('-p', '--prompt', type=str, help='Style prompt for video processing instructions. For example, "speaking style of captain jack sparrow". (Optional)')

    args = parser.parse_args()

    input_video = args.source if args.source is not None else args.inputvideo
    language = args.language_optional if args.language_optional is not None else args.language

    # Ensure directories exist
    if not os.path.exists(args.download_directory):
        os.makedirs(args.download_directory)
    
    if not os.path.exists(args.synthesis_directory):
        os.makedirs(args.synthesis_directory)

    # Call the main processing function
    print (f"starting turnvoice processing...")
    process_video(
        p_input_video=input_video,
        p_language=language,
        p_input_language=args.input_language,
        p_download_directory=args.download_directory,
        p_synthesis_directory=args.synthesis_directory,
        p_extract_disabled=args.extractoff,
        p_voices=args.voice,
        p_engine=args.engine,
        p_output_video=args.output_video,
        p_clean_audio=args.clean_audio,
        p_limit_start_time=args._from,
        p_limit_end_time=args.to,
        p_analysis=args.analysis,
        p_speaker_number=args.speaker,
        p_num_speakers=args.num_speakers,
        p_min_speakers=args.min_speakers,
        p_max_speakers=args.max_speakers,
        p_time_files=args.timefile,
        p_prompt=args.prompt,
    )

if __name__ == "__main__":
    main()