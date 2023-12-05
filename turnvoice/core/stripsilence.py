from pydub import AudioSegment
from pydub.silence import detect_nonsilent

def strip_silence(input_wav_file: str, output_wav_file: str, silence_threshold: int = -50, min_silence_length: int = 10, seek_step: int = 1):
    """
    Strip silence from the beginning and end of a WAV file.
    
    :param input_wav_file: Path to the input WAV file.
    :param output_wav_file: Path to the output WAV file.
    :param silence_threshold: The upper bound for how quiet is silent in dBFS. Default is -50 dBFS.
    :param min_silence_length: The minimum length for any silent section in milliseconds.
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