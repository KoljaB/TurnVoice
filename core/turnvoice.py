import os
import argparse
from moviepy.editor import AudioFileClip

from .download import fetch_youtube
from .transcribe import transcribe, extract_words
from .tokenize import create_synthesizable_fragments
from .videocut import create_composite_audio, overlay_audio_on_video
from .synthesis import Synthesis


def process_video(
        url = "https://www.youtube.com/watch?v=FJ3N_2r6R-o",
        language = "en",
        download_directory = "downloads",
        synthesis_directory = "synthesis",
        extract = False, 
        reference_wav = "reference.wav", 
        output_video = "final_cut.mp4"):
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
    if synthesis_directory and not os.path.exists(synthesis_directory):
        os.makedirs(synthesis_directory)

    print("Downloading video...")
    _, audio_file, video_file_muted = fetch_youtube(url, extract=extract, directory=download_directory)

    print("Transcribing audio...")
    segments, _ = transcribe(audio_file, language=language)

    print("Extracting words...")
    words = extract_words(segments)

    print("Creating synthesizable fragments...")
    sentences = create_synthesizable_fragments(words)

    print(f"Starting synthesis for {len(sentences)} sentences...")
    synthesis = Synthesis(language=language, reference_wav=reference_wav)
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
    parser = argparse.ArgumentParser(description="Replaces original voices in Youtube videos.")

    # Adding arguments
    parser.add_argument('-u', '--url', type=str, required=True, help='URL of the YouTube video.')
    parser.add_argument('-l', '--language', type=str, default='en', help='Language code for transcription. Default is "en".')
    parser.add_argument('-dd', '--download_directory', type=str, default='downloads', help='Directory to save downloaded files.')
    parser.add_argument('-sd', '--synthesis_directory', type=str, default='synthesis', help='Directory to save synthesized audio files.')
    parser.add_argument('-e', '--extract', action='store_true', help='Extract audio from the video file.')
    parser.add_argument('-rw', '--reference_wav', type=str, default='reference.wav', help='Reference audio file for voice synthesis.')
    parser.add_argument('-ov', '--output_video', type=str, default='final_cut.mp4', help='Filename for the output video with synthetic voice.')

    args = parser.parse_args()

    # Ensure directories exist
    if not os.path.exists(args.download_directory):
        os.makedirs(args.download_directory)
    
    if not os.path.exists(args.synthesis_directory):
        os.makedirs(args.synthesis_directory)

    # Call the main processing function
    process_video(
        url=args.url,
        language=args.language,
        download_directory=args.download_directory,
        synthesis_directory=args.synthesis_directory,
        extract=args.extract,
        reference_wav=args.reference_wav,
        output_video=args.output_video
    )

if __name__ == "__main__":
    main()