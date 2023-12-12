from .word import Word
import torch
import gc

faster_model = None
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

def faster_transcribe(file_name, language=None, model="large-v2"):
    """
    Transcribes a audio file with faster_whisper, returns transcript and word timestamps.
    """
    global faster_model, faster_model_size

    if faster_model_size and faster_model_size != model:
        unload_faster_model()

    if faster_model is None:
        import faster_whisper
        faster_model = faster_whisper.WhisperModel(model, device="cuda", compute_type="float16")
        faster_model_size = model

    if not language is None and language == "":
        language = None

    return faster_model.transcribe(
        file_name, 
        language=language, 
        beam_size=5, 
        word_timestamps=True, 
        vad_filter=True)

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