from os.path import exists, join, splitext
from moviepy.editor import VideoFileClip
from yt_dlp import YoutubeDL
import os
import re


def fetch_youtube(
    url: str,
    filetype: str,
    directory: str = "downloaded_files"
):

    """
    Downloads a specific type of file (video, audio, or muted video)
    from the provided YouTube URL.

    Args:
        url (str): The URL of the YouTube video to be downloaded.
        filetype (str): Type of file to download - 'video', 'audio',
            or 'muted_video'.
        directory (str): The directory to download the file to.

    Returns:
        str: The filename of the downloaded file.
    """
    if directory and not exists(directory):
        os.makedirs(directory)

    if filetype == 'video':
        # Download video with audio
        outtmpl = join(directory, '%(title)s.%(ext)s')
        ydl_opts = {
            'format': 'best',
            'outtmpl': outtmpl,
            'noplaylist': True,
        }
    elif filetype == 'audio':
        # Download audio only
        outtmpl = join(directory, '%(title)s_audio.%(ext)s')
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'noplaylist': True,
        }
    elif filetype == 'muted_video':
        # Download video without audio
        outtmpl = join(directory, '%(title)s_mutedvideo.%(ext)s')
        ydl_opts = {
            'format': 'bestvideo',
            'outtmpl': outtmpl,
            'noplaylist': True,
        }
    else:
        raise ValueError(
            "Invalid filetype. Choose 'video', 'audio', or 'muted_video'."
        )

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        downloaded_file = ydl.prepare_filename(info)

    return downloaded_file


def is_valid_youtube_id(yt_id: str) -> bool:
    """
    Checks if the given string is a valid YouTube video ID.

    Args:
        yt_id (str): The YouTube video ID to be checked.

    Returns:
        bool: True if it's a valid YouTube ID, False otherwise.
    """
    # YouTube video ID pattern (11 characters, can include '-' and '_')
    yt_id_pattern = re.compile(r'^[a-zA-Z0-9_-]{11}$')
    return bool(yt_id_pattern.match(yt_id))


def check_youtube(url_or_id: str):
    """
    Checks if given url is a valid YouTube video or a YouTube ID.

    Args:
        url_or_id (str): The URL of the YouTube video to be checked
          or the video ID.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    # Check if it's a valid YouTube ID
    if is_valid_youtube_id(url_or_id):
        print(f"{url_or_id} matches YouTube video ID pattern.")
        return True

    # Check if it's a valid YouTube URL
    if "youtube.com/watch?v=" in url_or_id or "youtu.be/" in url_or_id:
        print(f"{url_or_id} contains a valid YouTube URL pattern.")
        return True

    # Not a valid YouTube video ID or URL
    return False


def ensure_youtube_url(url_or_id: str) -> str:
    """
    Converts a YouTube video ID to a full URL if necessary,
    or returns the original URL.

    This function assumes the input is a YouTube video ID
    if it is an 11-character alphanumeric string.
    In this case, it constructs and returns the full YouTube
    video URL. Otherwise, it returns the input as is.

    Args:
    url_or_id (str): The YouTube video ID or URL.

    Returns:
    str: The full YouTube video URL if a video ID was provided,
      otherwise the original URL.
    """
    if is_valid_youtube_id(url_or_id):
        return "https://www.youtube.com/watch?v=" + url_or_id
    return url_or_id


def extract_audio_and_muted_video(video_file: str):
    """
    Helper function to extract audio
    and create a muted video from a video file.

    Args:
        video_file (str): The path to the video file.

    Returns:
        Tuple[str, str]: A tuple containing paths
        to the extracted audio file and muted video file.
    """

    video_extension = splitext(video_file)[1]
    audio_file = video_file.replace(video_extension, ".wav")
    video_file_muted = video_file.replace(
        video_extension,
        f"_muted{video_extension}"
    )

    if exists(audio_file) and exists(video_file_muted):

        print(f"Files '{audio_file}' and '{video_file_muted}' "
              "already exist, skipping extraction")
    else:
        video_clip = VideoFileClip(video_file)

        if not exists(audio_file):
            audio_clip = video_clip.audio

            audio_clip.write_audiofile(
                audio_file,
                codec="pcm_s16le"
            )

        if not exists(video_file_muted):
            # TBD: don't write video, just return the clip
            muted_video_clip = video_clip.set_audio(None)
            muted_video_clip.write_videofile(
                video_file_muted,
                codec="libx264",
                audio_codec=None
            )

    return audio_file, video_file_muted


def fetch_youtube_extract(
        url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        extract=False,
        directory: str = "downloaded_files"):
    """
    Downloads a video from the provided YouTube URL.

    Optionally either extracts audio and muted video
    from the original video or downloads the video and audio separately.

    Args:
        url (str): The URL of the YouTube video to be downloaded.
        extract (bool): If set to True, only one video file is downloaded.
            If False, muted video and audio are downloaded separately.
            Can potentially lead to better quality
            but may increase the likelihood of errors.
        directory (str): The directory to download the video to.
            Set to None if you like cluttered main directories.
    """
    if directory and not exists(directory):
        os.makedirs(directory)

    video_file = fetch_youtube(url, 'video', directory)

    if extract:
        return extract_audio_and_muted_video(video_file)
    else:
        audio_file = fetch_youtube(url, 'audio', directory)
        video_file_muted = fetch_youtube(url, 'muted_video', directory)
        return audio_file, video_file_muted


def local_file_extract(filename: str, directory: str = "downloaded_files"):
    """
    Extracts audio and muted video from a local video file.

    Args:
        filename (str): The name of the video file.
        directory (str): The directory for extracted files.

    Returns:
        Tuple[str, str]: Paths to the extracted audio file
            and muted video file.
    """
    if directory and not exists(directory):
        os.makedirs(directory)

    return extract_audio_and_muted_video(filename)
