from .transcribe import stable_transcribe, unload_stable_model, faster_transcribe, unload_faster_model, extract_words
from .cut import create_composite_audio, overlay_audio_on_video, merge_video_audio, merge_audios, split_audio
from .fragtokenizer import create_synthesizable_fragments, merge_short_sentences
from .download import fetch_youtube_extract
from moviepy.editor import AudioFileClip
from .toseconds import time_to_seconds
from .synthesis import Synthesis
import subprocess
import argparse
import time
import os

USE_STABLE = False

def is_spleeter_installed() -> bool:
    """
    Check if Deezer's Spleeter CLI is installed on the system.

    Returns:
    bool: True if Spleeter is installed, False otherwise.
    """
    try:
        subprocess.run(["spleeter", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def process_video(
        url_or_id: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        language: str = "",
        download_directory: str = "downloads",
        synthesis_directory: str = "synthesis",
        extract_disabled: bool = False, 
        reference_wav: str = "reference.wav", 
        output_video: str = "final_cut.mp4",
        clean_audio: bool = False,
        start: str = None,
        end: str = None):
    """
    Video Processing Workflow covering downloading, audio extraction,
    transcription, synthesis, and video combination.

    Downloads a YouTube video, transcribes its audio, and replaces the original voice
    with a synthetic one.

    Parameters:
    url (str): URL of the YouTube video.
    language (str): Language code for transcription.
    download_dir (str): Directory to save downloaded files.
    synthesis_dir (str): Directory to save synthesized audio files.
    extract (bool): Whether to extract audio from the video file.
    reference_audio (str): Reference audio file for voice synthesis.
    output_video (str): Filename for the output video with synthetic voice.
    """

    processing_start_time = time.time()
    extract = not extract_disabled

    if not is_spleeter_installed() and not clean_audio:
        clean_audio = True
        print ("Spleeter CLI is not installed, required for splitting original audio into vocals and accompaniment.")
        print ("Forced clean audio output.")
        print ("To install spleeter cli:")
        print ("- install python 3.8")
        print ("- run 'pipx install spleeter --python /path/to/python3.8' in your cli")

    init_log_string = f"turnvoice.py: process_video: url_or_id: {url_or_id}, language: {language}, download_directory: {download_directory}, synthesis_directory: {synthesis_directory}, extract_disabled: {extract_disabled}, reference_wav: {reference_wav}, output_video: {output_video}, preserve_audio: {clean_audio}, start: {start}, end: {end}"
    print (init_log_string)

    if start:
        start_time = time_to_seconds(start)
        print (f"processing will start at time: {start_time}s")

    if end:
        end_time = time_to_seconds(end)
        print (f"processing will end at time: {end_time}s")

    # start synthesis engine early cause we want it to grab VRAM asap
    synthesis = Synthesis(language=language, reference_wav=reference_wav)

    # also accept video IDs
    if not "youtube.com" in url_or_id.lower():

        # YouTube video IDs are typically 11 characters long
        video_id_length = 11
        if len(url_or_id) > video_id_length:
            # Extract the last 11 characters, assuming they represent the video ID
            video_id = url_or_id[-video_id_length:]
        else:
            video_id = url_or_id

        url_or_id = "https://www.youtube.com/watch?v=" + video_id

    if synthesis_directory and not os.path.exists(synthesis_directory):
        os.makedirs(synthesis_directory)

    # download video and audio
    print (f"[{(time.time() - processing_start_time):.1f}s] downloading video...")
    audio_file, video_file_muted = fetch_youtube_extract(url_or_id, extract=extract, directory=download_directory)

    # split audio into vocals and accompaniment
    if not clean_audio:
        print (f"[{(time.time() - processing_start_time):.1f}s] splitting audio...")
        vocal_path, accompaniment_path = split_audio(audio_file, download_directory)

    # transcription (speech to text) of the audio
    if USE_STABLE:
        print (f"[{(time.time() - processing_start_time):.1f}s] transcribing audio (stable_whisper)...", end="", flush=True)
        transcribed_segments, transcription_info = stable_transcribe(audio_file, language=None, model="large-v2")
    else:
        print (f"[{(time.time() - processing_start_time):.1f}s] transcribing audio (faster_whisper)...", end="", flush=True)
        transcribed_segments, transcription_info = faster_transcribe(audio_file, language=None, model="large-v2")
    

    detected_input_language = transcription_info.language
    synthesis_language = language if len(language) > 0 else detected_input_language

    # extract words from the transcription
    print (f"[{(time.time() - processing_start_time):.1f}s] extracting words...", end="", flush=True)
    words = extract_words(transcribed_segments)

    # Filter out words based on start and end time
    if start:
        start_time = time_to_seconds(start)
        words = [word for word in words if word.start >= start_time]

    if end:
        end_time = time_to_seconds(end)
        words = [word for word in words if word.end <= end_time]

    if len(words) == 0:
        print (f"[{(time.time() - processing_start_time):.1f}s] no words to be turned, aborting...")
        exit(0)

    print (f"[{(time.time() - processing_start_time):.1f}s] {len(words)} words found...")

    # generate synthesizable fragments based on gaps and punctuation
    print (f"[{(time.time() - processing_start_time):.1f}s] creating synthesizable fragments...")
    synthesis.set_language(synthesis_language)
    sentences = create_synthesizable_fragments(words)
    sentences = merge_short_sentences(sentences, gap_duration=0.75, min_sentence_duration=1.5)

    # unload transcription model so synthesis model takes up the full vram resources (main bottleneck)
    # after that we lazy load the transcription model again after first synthesis
    if USE_STABLE:
        unload_stable_model()
    else:
        unload_faster_model()
    

    # translation if requested
    if len(language) > 0 and detected_input_language != language:
        from .translate import translate, translate_model_unload

        print (f"[{(time.time() - processing_start_time):.1f}s] translating from {detected_input_language} to {language}...")

        # translate every sentence
        translated_sentences = []
        for sentence in sentences:
            translated_sentence = translate(sentence["text"], source=detected_input_language, target=language)
            sentence["text"] = translated_sentence
            translated_sentences.append(sentence)

        sentences = translated_sentences

        # get rid of translation model to free up VRAM
        translate_model_unload()

    # synthesis (text to speech) of the sentences incl fitting length of synthesized audio to the original audio
    print (f"[{(time.time() - processing_start_time):.1f}s] synthesizing audio...")
    synthesis.synthesize_sentences(sentences, synthesis, synthesis_directory, processing_start_time, use_stable=USE_STABLE)
    #synthesis.synthesize_sentences(sentences, synthesis, synthesis_directory, start, use_stable=USE_STABLE)

    with AudioFileClip(audio_file) as audio_clip:
        duration = audio_clip.duration

    # combine the synthesized audio fragments into one audio file respecting the speech start times of the original audio
    final_cut_audio_path = "final_cut_audio.wav"
    print (f"[{(time.time() - processing_start_time):.1f}s] combining audio...")
    create_composite_audio(sentences, synthesis_directory, duration, final_cut_audio_path)

    if not clean_audio:
        time_stamps = []
        word_timestamp_correction = 0.3

        # Initial timestamp adjustment
        for sentence in sentences:
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
        # # time_stamps = []
        # # for sentence in sentences:
        # #     time_stamps.append((sentence["start"], sentence["end"]))
        # time_stamps = []
        # for sentence in sentences:
        #     # correction time for miscalculations of word timestamps
        #     word_timestamp_correction = 0.3

        #     start = max(0, sentence["start"] - word_timestamp_correction)
        #     end = min(sentence["end"] + word_timestamp_correction, duration)
        #     time_stamps.append((start, end))

            

        # for index, time_stamp in enumerate(time_stamps):
        #     if index >= 0:
        #         start, end = time_stamp
        #         start_prev, end_prev = time_stamps[index-1]
        #         if start < end_prev:
        #             # tbd: merge
        #             start = end_prev
        #             time_stamps[index] = (start, end)


        # merge the synthesized audio with the original audio
        final_cut_audio_merged = "final_cut_audio_merged.wav"
        print (f"[{(time.time() - processing_start_time):.1f}s] merging original {audio_file} and vocal less audios {accompaniment_path} into {final_cut_audio_merged}...")
        merge_audios(audio_file, accompaniment_path, time_stamps, final_cut_audio_merged)        

        # render the combined audio and the muted video into one video file
        print (f"[{(time.time() - processing_start_time):.1f}s] combining {video_file_muted} together with audios {final_cut_audio_path} and {final_cut_audio_merged} into video {output_video}...")
        total_duration = merge_video_audio(video_file_muted, final_cut_audio_path, final_cut_audio_merged, output_video)
    else:
        # render the combined audio and the muted video into one video file
        print (f"[{(time.time() - processing_start_time):.1f}s] combining audio {final_cut_audio_path} with video {video_file_muted} into {output_video}...")
        total_duration = overlay_audio_on_video(final_cut_audio_path, video_file_muted, output_video)

    # cleanup
    synthesis.close()

    # present stats
    print (f"[{(time.time() - processing_start_time):.1f}s] video processing complete: [[[ {output_video} ]]]")
    if total_duration and total_duration > 0:
        calculation_duration = time.time() - processing_start_time
        realtime_factor = calculation_duration / total_duration
        print (f"[{(time.time() - processing_start_time):.1f}s] calculation realtime factor for {total_duration:.1f}s video: {realtime_factor:.2f}x")

    # open the final video cut with the default player
    if os.name == 'nt':  # Windows
        os.startfile(output_video)
    elif os.name == 'posix':
        if sys.platform == "darwin":  # macOS
            os.system(f"open '{output_video}'")
        else:  # Linux and other POSIX OS
            os.system(f"xdg-open '{output_video}'")


def main():
    parser = argparse.ArgumentParser(description="Replaces voices in Youtube videos. Can translate.")

    # URL as both positional and optional argument
    parser.add_argument('url', nargs='?', type=str, help='URL or ID of the YouTube video. (Positional)')
    parser.add_argument('-i', '--in', dest='source', type=str, help='URL or ID of input YouTube video. (Optional)')

    # Language as both positional and optional argument
    parser.add_argument('language', nargs='?', type=str, default='', help='Language code for transcription. (Positional)')
    parser.add_argument('-l', '--language', dest='language_optional', type=str, help='Language code for transcription. (Optional)')

    parser.add_argument('-v', '--voice', type=str, default='male.wav', help='Reference audio file for voice synthesis.')
    parser.add_argument('-d', '--download_directory', type=str, default='downloads', help='Directory to save downloaded files.')
    parser.add_argument('-s', '--synthesis_directory', type=str, default='synthesis', help='Directory to save synthesized audio files.')
    parser.add_argument('-e', '--extractoff', action='store_true', help='Disables extraction of audio from the video file.')
    parser.add_argument('-o', '--output_video', '-out', type=str, default='final_cut.mp4', help='Filename for the output video with synthetic voice.')
    parser.add_argument('-c', '--clean_audio', action='store_true', help='No preserve of original audio in the final video. Returns clean synthesis.')
    parser.add_argument('-from', '--from', dest='_from', type=str, help='Time to start processing the video from. (Optional)')
    parser.add_argument('-to', '--to', type=str, help='Time to stop processing the video at. (Optional)')

    args = parser.parse_args()

    url = args.source if args.source is not None else args.url
    language = args.language_optional if args.language_optional is not None else args.language

    # Ensure directories exist
    if not os.path.exists(args.download_directory):
        os.makedirs(args.download_directory)
    
    if not os.path.exists(args.synthesis_directory):
        os.makedirs(args.synthesis_directory)

    # Call the main processing function
    process_video(
        url_or_id=url,
        language=language,
        download_directory=args.download_directory,
        synthesis_directory=args.synthesis_directory,
        extract_disabled=args.extractoff,
        reference_wav=args.voice,
        output_video=args.output_video,
        clean_audio=args.clean_audio,
        start=args._from,
        end=args.to
    )

if __name__ == "__main__":
    main()