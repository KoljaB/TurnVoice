DEMUX_INSTRUCTIONS = """
Demux CLI not installed. It's required for audio splitting.
Installation:
1. Run 'python3 -m pip install -U demucs'
2. Visit https://github.com/facebookresearch/demucs for more
   information.
"""

RUBBERBAND_INSTRUCTIONS = """
Rubber Band utility is not installed. It's required for audio stretching.
Installation steps:
1. Visit https://breakfastquay.com/rubberband/ and download the appropriate
   archive for your system.
2. Unpack the downloaded archive into a desired folder.
3. For Windows users:
   - Place the executable in a specific folder, such as C:\\RubberBand\\.
   - Add that folder to your system PATH. This can be done via System
     Properties > Advanced > Environment Variables.
   For macOS users:
   - Use the 'mv' command in Terminal to move the executable to a directory
     in your PATH, like /usr/local/bin/.
   - Example: mv /path/to/rubberband /usr/local/bin/
"""


def is_installed(lib: str) -> bool:
    """
    Check if Deezer's Spleeter CLI is installed on the system.

    Returns:
    bool: True if Spleeter is installed, False otherwise.
    """
    import subprocess
    try:
        subprocess.run(
            [lib, "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def verify_install(*libraries):
    """
    Check if all required libraries are installed on the system.

    Args:
    libraries (str): List of libraries to check.

    Returns:
    bool: True if all libraries are installed, False otherwise.
    """
    missing_libraries = []

    for lib in libraries:
        if not is_installed(lib):
            missing_libraries.append(lib)

    if missing_libraries:
        for lib in missing_libraries:
            if lib == "demux":
                print(DEMUX_INSTRUCTIONS)
            elif lib == "rubberband":
                print(RUBBERBAND_INSTRUCTIONS)

        return False

    return True
