from moviepy.editor import concatenate_audioclips, VideoFileClip, AudioFileClip
import os

def merge_audio_video(audio_filename, video_filename, output_filename):

    try:
        video_clip = VideoFileClip(video_filename)
        audio_clip = AudioFileClip(audio_filename)
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    return output_filename    


def create_composite_audio(sentences, synthesis_directory, video_duration):

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
        clips.append(AudioFileClip(silent_audio_path).subclip(0, initial_silence_duration))
        current_duration += initial_silence_duration

    for index, sentence in enumerate(sentences):

        # calculate the required silence before the sentence
        silence_duration_before_sentence = sentence["start"] - current_duration
        if silence_duration_before_sentence > 0:
            clips.append(AudioFileClip(silent_audio_path).subclip(0, silence_duration_before_sentence))
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
        clips.append(AudioFileClip(silent_audio_path).subclip(0, final_silence_duration))

    # concatenate all clips
    final_audio = concatenate_audioclips(clips)
    final_audio.write_audiofile("final_audio.wav")   


def overlay_audio_on_video(video_filename, output_filename):

    try:
        video_clip = VideoFileClip(video_filename)
        new_audio_clip = AudioFileClip("final_audio.wav")
        final_clip = video_clip.set_audio(new_audio_clip)
        final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    return output_filename          
