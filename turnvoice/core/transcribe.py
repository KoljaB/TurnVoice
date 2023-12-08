from .word import Word
import torch
import gc

stable_model = None
faster_model = None
stable_model_size = None
faster_model_size = None

LANGUAGES = {
    "en": "english",
    "zh": "chinese",
    "de": "german",
    "es": "spanish",
    "ru": "russian",
    "ko": "korean",
    "fr": "french",
    "ja": "japanese",
    "pt": "portuguese",
    "tr": "turkish",
    "pl": "polish",
    "ca": "catalan",
    "nl": "dutch",
    "ar": "arabic",
    "sv": "swedish",
    "it": "italian",
    "id": "indonesian",
    "hi": "hindi",
    "fi": "finnish",
    "vi": "vietnamese",
    "he": "hebrew",
    "uk": "ukrainian",
    "el": "greek",
    "ms": "malay",
    "cs": "czech",
    "ro": "romanian",
    "da": "danish",
    "hu": "hungarian",
    "ta": "tamil",
    "no": "norwegian",
    "th": "thai",
    "ur": "urdu",
    "hr": "croatian",
    "bg": "bulgarian",
    "lt": "lithuanian",
    "la": "latin",
    "mi": "maori",
    "ml": "malayalam",
    "cy": "welsh",
    "sk": "slovak",
    "te": "telugu",
    "fa": "persian",
    "lv": "latvian",
    "bn": "bengali",
    "sr": "serbian",
    "az": "azerbaijani",
    "sl": "slovenian",
    "kn": "kannada",
    "et": "estonian",
    "mk": "macedonian",
    "br": "breton",
    "eu": "basque",
    "is": "icelandic",
    "hy": "armenian",
    "ne": "nepali",
    "mn": "mongolian",
    "bs": "bosnian",
    "kk": "kazakh",
    "sq": "albanian",
    "sw": "swahili",
    "gl": "galician",
    "mr": "marathi",
    "pa": "punjabi",
    "si": "sinhala",
    "km": "khmer",
    "sn": "shona",
    "yo": "yoruba",
    "so": "somali",
    "af": "afrikaans",
    "oc": "occitan",
    "ka": "georgian",
    "be": "belarusian",
    "tg": "tajik",
    "sd": "sindhi",
    "gu": "gujarati",
    "am": "amharic",
    "yi": "yiddish",
    "lo": "lao",
    "uz": "uzbek",
    "fo": "faroese",
    "ht": "haitian creole",
    "ps": "pashto",
    "tk": "turkmen",
    "nn": "nynorsk",
    "mt": "maltese",
    "sa": "sanskrit",
    "lb": "luxembourgish",
    "my": "myanmar",
    "bo": "tibetan",
    "tl": "tagalog",
    "mg": "malagasy",
    "as": "assamese",
    "tt": "tatar",
    "haw": "hawaiian",
    "ln": "lingala",
    "ha": "hausa",
    "ba": "bashkir",
    "jw": "javanese",
    "su": "sundanese",
    "yue": "cantonese",
}

class TranscriptionInfo:
    def __init__(self, language):
        self.language = language

def stable_transcribe(file_name, language=None, model="large-v2"):
    """
    Transcribes a audio file, returns transcript and word timestamps.
    """
    global stable_model, stable_model_size

    if stable_model_size and stable_model_size != model:
        unload_stable_model()

    if stable_model is None:
        import stable_whisper
        stable_model = stable_whisper.load_faster_whisper(model)
        stable_model_size = model

    result = stable_model.transcribe_stable(file_name, word_timestamps=True, vad=True)
    language = result.language
    language_shortcut = ""
    for key, value in LANGUAGES.items():
        if value == language:
            language_shortcut = key
            break
    info = TranscriptionInfo(language_shortcut)
    print (f"Detected language: {language} ({language_shortcut})")
    return result, info

def faster_transcribe(file_name, language=None, model="large-v2"):
    global faster_model, faster_model_size

    if faster_model_size and faster_model_size != model:
        unload_stable_model()

    if faster_model is None:
        import faster_whisper
        faster_model = faster_whisper.WhisperModel(model, device="cuda", compute_type="float16")
        faster_model_size = model

    return faster_model.transcribe(
        file_name, 
        language=language, 
        beam_size=5, 
        word_timestamps=True, 
        vad_filter=True)

def unload_stable_model():
    global stable_model
    if stable_model:
        del stable_model
        torch.cuda.empty_cache()
        gc.collect()
        from numba import cuda
        device = cuda.get_current_device()
        device.reset()
        stable_model = None
        print("Stable model unloaded successfully.")
    else:
        print("Stable is not loaded.")        

def unload_faster_model():
    global faster_model
    if faster_model:
        del faster_model
        torch.cuda.empty_cache()
        gc.collect()
        from numba import cuda
        device = cuda.get_current_device()
        device.reset()
        faster_model = None
        print("Faster model unloaded successfully.")
    else:
        print("Faster is not loaded.")          

def extract_words(segments):
    """
    Extracts words from segments.
    """
    words = []
    for segment in segments:
        for segword in segment.words:
            print ("." , end="", flush=True)
            word = Word(
                text=segword.word, 
                start=segword.start, 
                end=segword.end, 
                probability=segword.probability)
            words.append(word)

    print ()
    return words