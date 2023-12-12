from moviepy.editor import concatenate_audioclips, VideoFileClip, AudioFileClip, CompositeAudioClip
from os.path import basename, exists, join, splitext
from .silence import create_silence
import subprocess

def create_composite_audio(sentences, synthesis_directory, video_duration, output_filename="final_audio.wav"):
    """
    Creates a composite audio file from given sentences, adding silence as needed.
    
    :param sentences: List of sentences with start times for synchronization.
    :param synthesis_directory: Directory containing synthesized sentence audio files.
    :param video_duration: Total duration of the video in seconds.
    :param output_filename: Filename for the output audio file.
    """
    clips = []
    current_duration = 0

    print("Creating composite audio")

    # Add initial silence if the first sentence doesn't start at the beginning
    initial_silence_duration = sentences[0]["start"]
    if initial_silence_duration > 0:
        print(f"Adding silence at start: {initial_silence_duration} seconds")
        clips.append(create_silence(initial_silence_duration))
        current_duration += initial_silence_duration

    for index, sentence in enumerate(sentences):
        # Calculate and add silence before the sentence
        silence_duration = sentence["start"] - current_duration
        if silence_duration > 0:
            clips.append(create_silence(silence_duration))
            current_duration += silence_duration

        # Add sentence audio
        sentence_filename = join(synthesis_directory, f"sentence{index}.wav") if synthesis_directory else f"sentence{index}.wav"
        sentence_clip = AudioFileClip(sentence_filename)
        clips.append(sentence_clip)
        current_duration += sentence_clip.duration

    # Add final silence if needed
    final_silence_duration = video_duration - current_duration
    if final_silence_duration > 0:
        clips.append(create_silence(final_silence_duration))

    # Concatenate and save the final audio
    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile(output_filename)
    final_audio.close()

def overlay_audio_on_video(audio_filename, video_filename, output_filename):
    """
    Overlays an audio file on a video file and saves the output.

    :param audio_filename: Path to the audio file.
    :param video_filename: Path to the video file.
    :param output_filename: Filename for the output video file.
    :return: Duration of the final video clip, or None if an error occurred.
    """
    try:
        final_duration = None
        video_clip = VideoFileClip(video_filename) 
        audio_clip = AudioFileClip(audio_filename)
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')
        final_duration = final_clip.duration
        return final_duration
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def merge_video_audio(video_filename, audio1_filename, audio2_filename, output_filename):
    """
    Merges two audio files with a video file.

    :param video_filename: Path to the video file.
    :param audio1_filename: Path to the first audio file.
    :param audio2_filename: Path to the second audio file.
    :param output_filename: Filename for the output video file.
    :return: Duration of the final video clip, or None if an error occurred.
    """
    try:
        video_clip = VideoFileClip(video_filename)
        audio_clip1 = AudioFileClip(audio1_filename).set_duration(video_clip.duration)
        audio_clip2 = AudioFileClip(audio2_filename).set_duration(video_clip.duration)

        combined_audio = CompositeAudioClip([audio_clip1, audio_clip2])
        final_clip = video_clip.set_audio(combined_audio)
        final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')

        return final_clip.duration
    except Exception as e:
        print(f"An error occurred: {e}")
        return None    

def split_audio(file_path, output_path, offset=0, duration=600):
    """
    Splits an audio file into vocals and accompaniment using spleeter.

    :param file_path: Path to the source audio file.
    :param output_path: Directory to save the separated audio files.
    :param offset: The offset in seconds to start separation (default is 0).
    :param duration: The duration in seconds to perform separation (default is 600).
    :return: A tuple containing paths to the separated vocals and accompaniment files.
    """    
    # Extract the base name and extension of the file
    name, ext = splitext(basename(file_path))

    # Paths for the separated audio files
    vocals_path = join(output_path, f"{name}/vocals.wav")
    accompaniment_path = join(output_path, f"{name}/accompaniment.wav")
    
    # Check if separation is already done
    if exists(vocals_path) and exists(accompaniment_path):
        print("Both vocals and accompaniment files already exist, skipping separation")
        return vocals_path, accompaniment_path
    
    # Check if the file needs to be converted to mp3
    file_path_temp = file_path
    if ext.lower() != '.mp3':
        print(f"Converting audio from format {ext} to mp3")
        file_path_temp = join(output_path, f"{name}.mp3")
        subprocess.run(['ffmpeg', '-y', '-i', file_path, '-codec', 'libmp3lame', '-b', '320k', file_path_temp], check=True)
        #subprocess.run(['ffmpeg', '-i', file_path, '-codec:a', 'libmp3lame', '-b:a', '320k', file_path_temp], check=True)

    # Separate audio into vocals and accompaniment using spleeter
    subprocess.run(['spleeter', 'separate', '-o', output_path, '-p', 'spleeter:2stems', '-c', 'wav', '-s', str(offset), '-d', str(duration), file_path_temp], check=True)

    return (vocals_path, accompaniment_path) if exists(vocals_path) and exists(accompaniment_path) else (None, None)

def cut_video_to_duration(video_filename, output_filename, duration):
    """
    Cuts a video to a specified duration.

    :param video_filename: Path to the source video file.
    :param output_filename: Filename for the output video file.
    :param duration: The duration in seconds to which the video should be cut.
    :return: Duration of the final video clip, or None if an error occurred.
    """
    try:
        # Load the video clip
        video_clip = VideoFileClip(video_filename)

        # Cut the video to the specified duration
        final_clip = video_clip.subclip(0, duration)

        # Write the cut video to the output file
        final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')

        return final_clip.duration
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def merge_audios(audio1_filename, audio2_filename, timestamps, output_filename):
    """
    Merges two audio files based on specified timestamps.

    :param audio1_filename: Path to the first audio file.
    :param audio2_filename: Path to the second audio file.
    :param timestamps: List of tuples, each containing start and end times for segments from the second audio file.
    :param output_filename: Filename for the output merged audio file.
    :return: Duration of the final audio clip.
    """
    # Load the audio files
    audio_clip1 = AudioFileClip(audio1_filename)
    audio_clip2 = AudioFileClip(audio2_filename)

    segments = []  

    # Start of the next segment
    next_start = 0 

    for start_time, end_time in timestamps:
        # Add segment from audio1 if there is a gap
        if start_time > next_start:
            segments.append(audio_clip1.subclip(next_start, start_time))


        # Add segment from audio2 for the specified duration
        segments.append(audio_clip2.subclip(start_time, end_time))

        # Update the start of the next segment
        next_start = end_time

    # Add remaining part from audio1 if any
    if next_start < audio_clip1.duration:
        segments.append(audio_clip1.subclip(next_start))

    # Combine all segments 
    final_audio = concatenate_audioclips(segments)

    # Write the final audio file
    final_audio.write_audiofile(output_filename)

    return final_audio.duration
