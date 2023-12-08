from .videocut import create_composite_audio, overlay_audio_on_video
from .fragtokenizer import create_synthesizable_fragments, merge_short_sentences
from .transcribe import stable_transcribe, unload_stable_model, faster_transcribe, unload_faster_model, extract_words
from moviepy.editor import AudioFileClip
from .download import fetch_youtube
from .synthesis import Synthesis
import argparse
import time
import os

USE_STABLE = True

def process_video(
        url_or_id: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        language: str = "",
        download_directory: str = "downloads",
        synthesis_directory: str = "synthesis",
        extract_disabled: bool = False, 
        reference_wav: str = "reference.wav", 
        output_video: str = "final_cut.mp4"):
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

    start = time.time()
    extract = not extract_disabled

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
    print (f"[{(time.time() - start):.1f}s] downloading video...")
    audio_file, video_file_muted = fetch_youtube(url_or_id, extract=extract, directory=download_directory)

    # transcription (speech to text) of the audio
    if USE_STABLE:
        print (f"[{(time.time() - start):.1f}s] transcribing audio (stable_whisper)...", end="", flush=True)
        transcribed_segments, transcription_info = stable_transcribe(audio_file, language=None, model="large-v2")
    else:
        print (f"[{(time.time() - start):.1f}s] transcribing audio (faster_whisper)...", end="", flush=True)
        transcribed_segments, transcription_info = faster_transcribe(audio_file, language=None, model="large-v2")
    

    detected_input_language = transcription_info.language
    synthesis_language = language if len(language) > 0 else detected_input_language

    # extract words from the transcription
    print (f"[{(time.time() - start):.1f}s] extracting words...", end="", flush=True)
    words = extract_words(transcribed_segments)

    # generate synthesizable fragments based on gaps and punctuation
    print (f"[{(time.time() - start):.1f}s] creating synthesizable fragments...")
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

        print (f"[{(time.time() - start):.1f}s] translating from {detected_input_language} to {language}...")

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
    print (f"[{(time.time() - start):.1f}s] synthesizing audio...")
    synthesis.synthesize_sentences(sentences, synthesis, synthesis_directory, start)
    #synthesis.synthesize_sentences(sentences, synthesis, synthesis_directory, start, use_stable=USE_STABLE)

    with AudioFileClip(audio_file) as audio_clip:
        duration = audio_clip.duration

    # combine the synthesized audio fragments into one audio file respecting the speech start times of the original audio
    print (f"[{(time.time() - start):.1f}s] combining audio...")
    create_composite_audio(sentences, synthesis_directory, duration, "final_cut_audio.wav")

    # render the combined audio and the muted video into one video file
    print (f"[{(time.time() - start):.1f}s] combining audio and video...")
    total_duration = overlay_audio_on_video("final_cut_audio.wav", video_file_muted, output_video)

    # cleanup
    synthesis.close()

    # present stats
    print (f"[{(time.time() - start):.1f}s] video processing complete: [[[ {output_video} ]]]")
    if total_duration and total_duration > 0:
        calculation_duration = time.time() - start
        realtime_factor = calculation_duration / total_duration
        print (f"[{(time.time() - start):.1f}s] calculation realtime factor for {total_duration:.1f}s video: {realtime_factor:.2f}x")

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
    parser.add_argument('-u', '--url', dest='url_optional', type=str, help='URL of the YouTube video. (Optional)')

    # Language as both positional and optional argument
    parser.add_argument('language', nargs='?', type=str, default='', help='Language code for transcription. (Positional)')
    parser.add_argument('-l', '--language', dest='language_optional', type=str, help='Language code for transcription. (Optional)')

    parser.add_argument('-d', '--download_directory', type=str, default='downloads', help='Directory to save downloaded files.')
    parser.add_argument('-s', '--synthesis_directory', type=str, default='synthesis', help='Directory to save synthesized audio files.')
    parser.add_argument('-e', '--extractoff', action='store_true', help='Disables extraction of audio from the video file.')
    parser.add_argument('-r', '--reference_wav', type=str, default='reference.wav', help='Reference audio file for voice synthesis.')
    parser.add_argument('-o', '--output_video', type=str, default='final_cut.mp4', help='Filename for the output video with synthetic voice.')

    args = parser.parse_args()

    url = args.url_optional if args.url_optional is not None else args.url
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
        reference_wav=args.reference_wav,
        output_video=args.output_video
    )

if __name__ == "__main__":
    main()