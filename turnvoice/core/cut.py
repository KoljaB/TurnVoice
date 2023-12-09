from moviepy.editor import concatenate_audioclips, VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip
from os.path import basename, exists, join, splitext
import subprocess
import os

def get_silent_clip_from_path(duration, silent_audio_path):
    # Calculate the number of repetitions needed for the silent clip
    repetitions = int(duration / 60)
    remainder = duration % 60

    silent_clips = [AudioFileClip(silent_audio_path).subclip(0, 60) for _ in range(repetitions)]

    # Add the remainder of the silence if needed
    if remainder > 0:
        silent_clips.append(AudioFileClip(silent_audio_path).subclip(0, remainder))

    # Concatenate and return the silent clip
    return concatenate_audioclips(silent_clips)

def get_silent_clip(duration):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    silent_audio_path = os.path.join(script_dir, "silent_audio.wav")

    return get_silent_clip_from_path(duration, silent_audio_path)

def create_composite_audio(sentences, synthesis_directory, video_duration, output_filename="final_audio.wav"):

    # create an empty list to store audio clips
    clips = []
    current_duration = 0

    print ("creating composite audio")

    # add silence for the initial part if needed
    if sentences[0]["start"] > 0:

        initial_silence_duration = sentences[0]["start"]
        print ("adding silence at start: ", initial_silence_duration)

        clips.append(get_silent_clip(initial_silence_duration))
        current_duration += initial_silence_duration        

    for index, sentence in enumerate(sentences):

        # calculate the required silence before the sentence
        silence_duration_before_sentence = sentence["start"] - current_duration
        if silence_duration_before_sentence > 0:
            clips.append(get_silent_clip(silence_duration_before_sentence))
            current_duration += silence_duration_before_sentence            

        # add the sentence audio
        filename = f"sentence{index}.wav"
        if synthesis_directory is not None:
            filename = os.path.join(synthesis_directory, filename)
        sentence_clip = AudioFileClip(filename)
        clips.append(sentence_clip)
        current_duration += sentence_clip.duration            

    # add final silence if needed
    final_silence_duration = video_duration - current_duration
    if final_silence_duration > 0:
        clips.append(get_silent_clip(final_silence_duration))

    # concatenate all clips
    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile(output_filename)
    final_audio.close()

def overlay_audio_on_video(audio_filename, video_filename, output_filename):

    try:
        with VideoFileClip(video_filename) as video_clip, AudioFileClip(audio_filename) as audio_clip:
            final_clip = video_clip.set_audio(audio_clip)
            final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')
            return final_clip.duration

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def merge_video_audio(video_filename, audio1_filename, audio2_filename, output_filename):
    try:
        # Load the video clip
        video_clip = VideoFileClip(video_filename)

        # Load the audio clips
        audio_clip1 = AudioFileClip(audio1_filename)
        audio_clip2 = AudioFileClip(audio2_filename)

        # Ensure audio clips are the same duration as the video
        audio_clip1 = audio_clip1.set_duration(video_clip.duration)
        audio_clip2 = audio_clip2.set_duration(video_clip.duration)

        # Combine the audio clips
        combined_audio = CompositeAudioClip([audio_clip1, audio_clip2])

        # Set the combined audio to the video clip
        final_clip = video_clip.set_audio(combined_audio)

        # Write the final video with merged audio
        final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')

        return final_clip.duration

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    

def split_audio(file_path, output_path):
    # Check if the file is not mp3, convert it to mp3
    name, ext = splitext(basename(file_path))
    file_path_temp = file_path

    if ext.lower() != '.mp3':
        print (f"Converting downloaded audio from format {ext} to mp3")
        file_path_temp = join(output_path, "{}.mp3".format(name))
        subprocess.run(['ffmpeg', '-i', file_path, '-codec:a', 'libmp3lame', '-b:a', '320k', file_path_temp], check=True)

    # Use spleeter CLI for separation
    subprocess.run(['spleeter', 'separate', '-o', output_path, '-p', 'spleeter:2stems', '-c', 'wav', file_path_temp], check=True)

    vocals_path = join(output_path, "{}/vocals.wav".format(name))
    accompaniment_path = join(output_path, "{}/accompaniment.wav".format(name))

    return (vocals_path, accompaniment_path) if exists(vocals_path) and exists(accompaniment_path) else (None, None)

def cut_video_to_duration(video_filename, output_filename, duration):
    try:
        # Load the video clip
        video_clip = VideoFileClip(video_filename)

        # Set the duration of the video clip
        final_clip = video_clip.subclip(0, duration)

        # Write the final video
        final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')

        return final_clip.duration

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def merge_audios(audio1_filename, audio2_filename, timestamps, output_filename):
    try:
        # Load the audio files
        audio_clip1 = AudioFileClip(audio1_filename)
        audio_clip2 = AudioFileClip(audio2_filename)

        # Initialize an empty list for audio segments
        segments = []

        # Start of the next segment
        next_start = 0

        # Iterate over the timestamps
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

        return "Audio merged successfully."

    except Exception as e:
        print(f"An error occurred: {e}")
        return None