from moviepy.editor import concatenate_audioclips, AudioFileClip
from pydub.silence import detect_nonsilent
from pydub import AudioSegment
import os


def strip_silence(
    input_wav_file: str,
    output_wav_file: str,
    silence_threshold: int = -50,
    min_silence_length: int = 10,
    seek_step: int = 1
):
    """
    Removes silence from the beginning and end of a WAV file.

    :param input_wav_file: Path to the input WAV file.
    :param output_wav_file: Path to the output WAV file.
    :param silence_threshold: The upper bound for how quiet is silent in dBFS.
        Default is -50 dBFS.
    :param min_silence_length: The minimum length for any silent section
        in milliseconds.
    :param seek_step: Step size for iterating over the segment in milliseconds.
    :return: None, saves the trimmed audio to a new file.
    """
    # Load the audio file
    audio = AudioSegment.from_wav(input_wav_file)

    # Detect non-silent parts
    nonsilent_parts = detect_nonsilent(audio,
                                       min_silence_len=min_silence_length,
                                       silence_thresh=silence_threshold,
                                       seek_step=seek_step)

    # Check if nonsilent parts were detected
    if nonsilent_parts:
        # Get start and end of first and last chunks
        start = nonsilent_parts[0][0]
        end = nonsilent_parts[-1][1]

        # Trim the audio
        trimmed_audio = audio[start:end]
    else:
        print("No nonsilent parts detected. Copying original file.")
        trimmed_audio = audio

    # Save the audio (trimmed or original) to the output file
    trimmed_audio.export(output_wav_file, format="wav")


def create_silence_from_file(
    duration: float, silence_file: str
) -> AudioFileClip:
    """
    Creates a silent audio clip of a specified duration
    from an existing silent audio file.

    :param duration: Duration of the silent audio needed in seconds.
    :param silence_file: Path to the audio file which contains silence.
    :return: An AudioFileClip object representing the silent audio clip.
    """
    # Calculate the number of full minute repetitions needed
    repetitions = int(duration / 60)
    remainder = duration % 60

    # Generate silent clips for each full minute
    silent_clips = [
        AudioFileClip(silence_file).subclip(0, 60) for _ in range(repetitions)
    ]

    # Add a clip for the remaining seconds, if any
    if remainder > 0:
        silent_clips.append(AudioFileClip(silence_file).subclip(0, remainder))

    # Concatenate all silent clips into one and return
    return concatenate_audioclips(silent_clips)


def create_silence(duration: float) -> AudioFileClip:
    """
    Creates a silent audio clip of a specified duration using
    a pre-existing silent audio file.

    :param duration: Duration of the silent audio needed in seconds.
    :return: An AudioFileClip object representing the silent audio clip.
    """
    # Determine the path to the silent audio file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    silent_audio_path = os.path.join(script_dir, "silent_audio.wav")

    # Create and return the silent audio clip using the silent audio file
    return create_silence_from_file(duration, silent_audio_path)
