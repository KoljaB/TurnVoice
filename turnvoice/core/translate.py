from deep_translator import GoogleTranslator


def translate(text: str, source: str = "en", target: str = "de") -> str:

    translator = GoogleTranslator(
        source=source, target=target
    )

    translated_text = translator.translate(text)

    print(f"Translated \"{text}\" to \"{translated_text}\"")

    return translated_text


def translate_model_unload():
    pass
