from deep_translator import GoogleTranslator


def translate(text: str, source: str = "en", target: str = "de") -> str:

    translator = GoogleTranslator(
        source=source, target=target
    )

    translated_text = translator.translate(text)

    print(f"Translated \"{text}\" to \"{translated_text}\"")

    return translated_text


def perform_translation(
    sentence_fragments,
    source_language,
    target_language
):
    if len(target_language) > 0 and source_language != target_language:

        print(f"translating from {source_language} to {target_language}...")

        for sentence in sentence_fragments:
            print(f"Translating \"{sentence['text']}\" from "
                  f"{source_language} to {target_language}..."
                  )
            translated_sentence = translate(
                sentence["text"],
                source=source_language,
                target=target_language
                )
            sentence["text"] = translated_sentence
