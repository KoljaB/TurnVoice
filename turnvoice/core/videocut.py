from moviepy.editor import concatenate_audioclips, VideoFileClip, AudioFileClip
import os

def add_silence(duration, silent_audio_path):
    # Calculate the number of repetitions needed for the silent clip
    repetitions = int(duration / 60)
    remainder = duration % 60

    silent_clips = [AudioFileClip(silent_audio_path).subclip(0, 60) for _ in range(repetitions)]

    # Add the remainder of the silence if needed
    if remainder > 0:
        silent_clips.append(AudioFileClip(silent_audio_path).subclip(0, remainder))

    # Concatenate and return the silent clip
    return concatenate_audioclips(silent_clips)

def create_composite_audio(sentences, synthesis_directory, video_duration, output_filename="final_audio.wav"):

    # create an empty list to store audio clips
    clips = []
    current_duration = 0

    print ("creating composite audio")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    silent_audio_path = os.path.join(script_dir, "silent_audio.wav")

    # add silence for the initial part if needed
    if sentences[0]["start"] > 0:

        initial_silence_duration = sentences[0]["start"]
        print ("adding silence at start: ", initial_silence_duration)

        clips.append(add_silence(initial_silence_duration, silent_audio_path))
        current_duration += initial_silence_duration        

    for index, sentence in enumerate(sentences):

        # calculate the required silence before the sentence
        silence_duration_before_sentence = sentence["start"] - current_duration
        if silence_duration_before_sentence > 0:
            clips.append(add_silence(silence_duration_before_sentence, silent_audio_path))
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
        clips.append(add_silence(final_silence_duration, silent_audio_path))

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