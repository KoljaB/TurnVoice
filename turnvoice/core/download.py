from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip, AudioFileClip
import os

def fetch_youtube(
        url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 
        extract = True,
        directory: str = "downloaded_files"): 
    """
    Downloads a video from the provided YouTube URL.
    
    Optionally either extracts audio and muted video from the original video or downloads the video and audio separately.

    Args:
        url (str): The URL of the YouTube video to be downloaded.
        extract (bool): If set to True, only one video file is downloaded. 
                        If False, muted video and audio are downloaded separately.
                        Can potentially lead to better quality but may increase the likelihood of errors.
        directory (str): The directory to download the video to. Set to None if you like cluttered main directories.
    """

    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    outtmpl = os.path.join(directory, '%(title)s.%(ext)s') if directory else '%(title)s.%(ext)s'
    
    # download video with audio
    ydl_opts = {
        'format': 'best',
        'outtmpl': outtmpl,
        'noplaylist': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_file = ydl.prepare_filename(info)

    video_extension = os.path.splitext(video_file)[1]
    audio_file = video_file.replace(video_extension, ".mp3") 
    video_file_muted = video_file.replace(video_extension, f"_muted{video_extension}") 

    if extract:
        # extract audio from video
        video_clip = VideoFileClip(video_file)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(audio_file)

        # create muted video file
        muted_video_clip = video_clip.set_audio(None)
        muted_video_clip.write_videofile(video_file_muted, codec="libx264", audio_codec=None)
    else:
        # download audio
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s_audio.%(ext)s',
            'noplaylist': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_file_download = ydl.prepare_filename(info)

            if os.path.exists(audio_file):
                print(f"File '{audio_file}' already exists, removing")
                os.remove(audio_file)

            os.rename(audio_file_download, audio_file)

        # download muted video
        ydl_opts = {
            'format': 'bestvideo',
            'outtmpl': '%(title)s_video.%(ext)s',
            'noplaylist': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_file_muted_download = ydl.prepare_filename(info)

            if os.path.exists(video_file_muted):
                print(f"File '{video_file_muted}' already exists, removing")
                os.remove(video_file_muted)

            os.rename(video_file_muted_download, video_file_muted)

    return video_file, audio_file, video_file_muted