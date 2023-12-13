import subprocess


def time_stretch(
    input_file: str,
    output_file: str,
    stretch_factor: float
) -> str:
    """
    Time-stretch a WAV file while preserving pitch.

    Args:
    input_file (str): Path to the input WAV file.
    output_file (str): Path where the time-stretched WAV file will be saved.
    stretch_factor (float): The factor by which the audio will be
        time-stretched. A factor greater than 1.0 increases the
        duration (slows down), and less than 1.0 decreases it (speeds up).

    Returns:
    str: Path to the output time-stretched WAV file.
    """
    print(f"time_stretch: {input_file} -> {output_file} "
          f"with stretch_factor {stretch_factor}"
          )

    # Construct the command as a list of arguments
    cmd = [
        'rubberband',
        '--fine',  # Use the R3 (finer) engine
        '--formant',  # Enable formant preservation
        '--crisp', '6',  # Set the highest level of crispness
        '--tempo', str(stretch_factor),
        input_file,
        output_file
    ]

    # Execute the command
    subprocess.check_call(cmd)

    return output_file
