from deep_translator import GoogleTranslator

def translate(text: str, source: str = "en", target: str = "de") -> str:
    translated_text = GoogleTranslator(source=source, target=target).translate(text)  # output -> Weiter so, du bist großartig
    print (f"Translated \"{text}\" to \"{translated_text}\"")

    return translated_text

def translate_model_unload():
    pass