from deep_translator import GoogleTranslator


def translate(text: str, source: str = "en", target: str = "de") -> str:
    """
    Translate a given text from the source language to the target language
    using GoogleTranslator.

    Args:
    text (str): The text to be translated.
    source (str): The source language code (default is English 'en').
    target (str): The target language code (default is German 'de').

    Returns:
    str: The translated text.
    """
    # Create an instance of GoogleTranslator with specified source
    # and target languages
    if source == "zh":
        source = "zh-CN"
    if target == "zh":
        target = "zh-CN"

    print(f"Translating with deep_translator from {source} to {target}...")
    translator = GoogleTranslator(source=source, target=target)

    # Perform the translation
    translated_text = translator.translate(text)

    # Print the original and translated texts for verification
    print(f"Translated \"{text}\" to \"{translated_text}\"")

    return translated_text


def perform_translation(sentence_fragments, source_language, target_language):
    """
    Perform translation of multiple sentence fragments from the source
    language to the target language.

    Args:
    sentence_fragments (list of dict): A list of dictionaries where each
      dictionary contains the 'text' key with sentence to translate.
    source_language (str): The source language code.
    target_language (str): The target language code.

    The function modifies the 'text' key in each dictionary in the list to the
    translated text.
    """
    # Check if translation is needed (different source and target languages)
    if len(target_language) > 0 and source_language != target_language:
        print(f"Translating from {source_language} to {target_language}...")

        for sentence in sentence_fragments:
            # Log the sentence being translated
            print(f"Translating \"{sentence['text']}\" from "
                  f"{source_language} to {target_language}...")

            # Perform the translation and update the sentence in the list
            translated_sentence = translate(
                sentence["text"],
                source=source_language,
                target=target_language
            )
            sentence["text"] = translated_sentence
