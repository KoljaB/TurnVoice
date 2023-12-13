from .transcribe import faster_transcribe, extract_words
from moviepy.editor import AudioFileClip
import textdistance
import re


def normalize_text(text):
    text = text.strip()
    text = text.lower()

    # Remove punctuation and special characters
    text = re.sub(r'[^\w\s]', '', text)

    # Standardize whitespace (convert multiple spaces to a single space)
    text = re.sub(r'\s+', ' ', text)

    return text


def verify_synthesis(
    input_file,
    expected_text,
    levenshtein_threshold=0.85,
    jaro_winkler_threshold=0.85,
    last_word_threshold=0.5
):
    """
    Verify that the input text was synthesized correctly.

    Args:
    input_file (str): Path to the input WAV file.
    expected_text (str): The expected text that was synthesized.
    """

    # transcribe text
    print(f"Using faster transcribe for verification of {input_file}")
    segs, _ = faster_transcribe(input_file, language=None, model="large-v2")

    words = extract_words(segs)
    if len(words) == 0:
        return False, False, False, 0, 0, 0

    detected_text = "".join([word.text for word in words])

    # normalize (normalized texts can be compared better)
    detected_text_norm = normalize_text(detected_text)
    expected_text_norm = normalize_text(expected_text)

    # compare
    levenshtein_sim = textdistance.levenshtein.normalized_similarity(
        detected_text_norm, expected_text_norm
    )
    jaro_winkler_sim = textdistance.jaro_winkler(
        detected_text_norm, expected_text_norm
    )

    # evaluate comparison
    levenshtein_is_fine = levenshtein_sim >= levenshtein_threshold
    jaro_winkler_is_fine = jaro_winkler_sim >= jaro_winkler_threshold

    # check if last detected word ends not too far from end of input file
    first_word = words[0]
    first_word_start = first_word.start
    last_word = words[-1]
    last_word_end = last_word.end

    print(f"file {input_file}, first_word_start: {first_word_start}, "
          f"last_word_end: {last_word_end}"
          )

    with AudioFileClip(input_file) as audio_clip:
        duration = audio_clip.duration

    print(f"audio_clip.duration: {duration}")

    last_word_distance = duration - last_word_end

    print(f"Expected text: {expected_text}, detected text: {detected_text}"
          f"Levenshtein similarity: {levenshtein_sim:.2f}, "
          f"Jaro-Winkler similarity: {jaro_winkler_sim:.2f}, "
          f"Last word distance: {last_word_distance:.2f}"
          )

    last_word_is_fine = last_word_distance < last_word_threshold

    return (
        last_word_is_fine,
        levenshtein_is_fine,
        jaro_winkler_is_fine,
        last_word_distance,
        levenshtein_sim,
        jaro_winkler_sim
    )
