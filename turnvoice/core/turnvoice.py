import os
import argparse
from moviepy.editor import AudioFileClip

from .download import fetch_youtube
from .transcribe import transcribe, extract_words
from .fragtokenizer import create_synthesizable_fragments
from .videocut import create_composite_audio, overlay_audio_on_video
from .synthesis import Synthesis
from .translate import translate


def process_video(
        url_or_id: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        language: str = "",
        download_directory: str = "downloads",
        synthesis_directory: str = "synthesis",
        extract: bool = False, 
        reference_wav: str = "reference.wav", 
        output_video: str = "final_cut.mp4"):
    """
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

    print("Downloading video...")
    _, audio_file, video_file_muted = fetch_youtube(url_or_id, extract=extract, directory=download_directory)

    print("Transcribing audio...")
    segments, info  = transcribe(audio_file)
    detected_input_language = info.language
    synthesis_language = language if len(language) > 0 else detected_input_language

    print("Extracting words...")
    words = extract_words(segments)

    print("Creating synthesizable fragments...")
    sentences = create_synthesizable_fragments(words)

    if len(language) > 0 and detected_input_language != language:
        print ("Translating from " + detected_input_language + " to " + language)

        translated_sentences = []
        for sentence in sentences:
            translated_sentence = translate(sentence["text"], source=detected_input_language, target=language)
            sentence["text"] = translated_sentence
            translated_sentences.append(sentence)

        sentences = translated_sentences

    print(f"Starting synthesis for {len(sentences)} sentences...")
    synthesis = Synthesis(language=synthesis_language, reference_wav=reference_wav)
    synthesize_sentences(sentences, synthesis, synthesis_directory)

    print("Creating composite audio...")
    duration = AudioFileClip(audio_file).duration
    create_composite_audio(sentences, synthesis_directory, duration)

    print("Rendering final video...")
    overlay_audio_on_video(video_file_muted, output_video)

    synthesis.close()


def synthesize_sentences(sentences, synthesis, synthesis_dir):
    """
    Synthesizes audio for each sentence fragment.

    Parameters:
    sentences (list): List of sentence fragments with timing information.
    synthesis (Synthesis): Synthesis object to generate audio.
    synthesis_dir (str): Directory to save synthesized audio files.
    """
    for index, sentence in enumerate(sentences):
        print_sentence_info(sentence, index, len(sentences))

        filename = f"sentence{index}.wav"
        filename = os.path.join(synthesis_dir, filename) if synthesis_dir else filename

        synthesis.synthesize_duration(
            text=sentence['text'],
            base_filename=filename,
            desired_duration=sentence["end"] - sentence["start"]
        )

        if not os.path.exists(filename):
            print(f"Synthesized file {filename} does not exist.")
            exit(0)


def print_sentence_info(sentence, index, total_sentences):
    """
    Prints information about the sentence being processed.

    Parameters:
    sentence (dict): Sentence fragment with timing information.
    index (int): Index of the sentence in the list.
    total_sentences (int): Total number of sentences to process.
    """
    start, end = sentence["start"], sentence["end"]
    duration = end - start
    text = sentence["text"]
    print(f"[{start:.2f}s -> {end:.2f}s] ({duration:.2f}s) {text}")
    print(f"Resynthesizing sentence {index}/{total_sentences}: {text}")


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
    parser.add_argument('-e', '--extract', action='store_true', help='Extract audio from the video file.')
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
        extract=args.extract,
        reference_wav=args.reference_wav,
        output_video=args.output_video
    )

if __name__ == "__main__":
    main()