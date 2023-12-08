import soundfile as sf
import subprocess

def is_rubberband_installed() -> bool:
    """
    Check if Rubberband CLI is installed on the system.

    Returns:
    bool: True if Rubberband is installed, False otherwise.
    """
    try:
        subprocess.run(["rubberband", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

if is_rubberband_installed():
    import pyrubberband as pyrb
    print ("rubberband found")
else:
    print ("rubberband not installed")


def time_stretch(input_file: str, output_file: str, stretch_factor: float) -> str:
    """
    Time-stretch a WAV file while preserving pitch.

    Args:
    input_file (str): Path to the input WAV file.
    output_file (str): Path where the time-stretched WAV file will be saved.
    stretch_factor (float): The factor by which the audio will be time-stretched.
                             A factor greater than 1.0 increases the duration (slows down),
                             and less than 1.0 decreases it (speeds up).

    Returns:
    str: Path to the output time-stretched WAV file.
    """
    print (f"time_stretch: {input_file} -> {output_file} with stretch_factor {stretch_factor}")

    # Read the WAV file
    y, sr = sf.read(input_file)
    
    # Apply time-stretching
    y_stretch = pyrb.time_stretch(y, sr, stretch_factor)

    # Write the stretched audio to a new WAV file
    sf.write(output_file, y_stretch, sr)

    return output_file