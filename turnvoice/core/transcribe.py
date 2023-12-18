from .word import Word
import torch
import gc
import os

faster_model = None
faster_model_size = None
stable_model = None
stable_model_size = None

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
    """
    Unloads the 'faster_model' from memory. It clears the model,
    empties the CUDA cache, and resets the GPU device.
    """
    global faster_model
    if faster_model:
        del faster_model
        torch.cuda.empty_cache()
        gc.collect()
        from numba import cuda
        device = cuda.get_current_device()
        device.reset()
        faster_model = None
        print("faster_whisper model unloaded successfully.")
    else:
        print("faster_whisper is not loaded.")


def unload_stable_model():
    """
    Unloads the 'stable_model' from memory. It clears the model,
    empties the CUDA cache, and resets the GPU device.
    """
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


def faster_transcribe(file_name, language=None, model="large-v2", vad=True):
    """
    Transcribes a audio file with faster_whisper,
    returns transcript and word timestamps.
    """

    global faster_model, faster_model_size

    if faster_model_size and faster_model_size != model:
        unload_faster_model()

    if faster_model is None:
        import faster_whisper

        faster_model = faster_whisper.WhisperModel(
            model,
            device="cuda",
            compute_type="float16"
            )

        faster_model_size = model

    if language is not None and language == "":
        language = None

    return faster_model.transcribe(
        file_name,
        language=language,
        beam_size=5,
        word_timestamps=True,
        vad_filter=vad
        )


def stable_transcribe(file_name, language=None, model="large-v3", vad=True):
    """
    Transcribes a audio file with stable_whisper,
    returns transcript and word timestamps.
    """
    global stable_model, stable_model_size

    if stable_model_size and stable_model_size != model:
        unload_stable_model()

    if stable_model is None:
        import stable_whisper

        stable_model = stable_whisper.load_model(model)
        stable_model_size = model

    if language is not None and language == "":
        language = None

    # result = stable_model.transcribe(
    #     file_name,
    #     word_timestamps=True,
    #     vad=vad,
    #     language=language,
    #     regroup=False  # disable default regrouping logic
    #     )

    result = stable_model.transcribe(
        file_name,
        word_timestamps=True,
        vad=vad,
        language=language,
        suppress_silence=True,
        ts_num=16,
        regroup=False  # disable default regrouping logic
        )

    result = stable_model.refine(
        file_name,
        result,
        precision=0.05,
    )

    # apply our own regrouping logic (currently same as default)
    result = (
        result.clamp_max()
        .split_by_punctuation([('.', ' '), '。', '?', '？', (',', ' '), '，'])
        .split_by_gap(.5)
        .merge_by_gap(.3, max_words=3)
        .split_by_punctuation([('.', ' '), '。', '?', '？'])
    )

    file_name_base, _ = os.path.splitext(file_name)
    result.save_as_json(file_name_base + "_transcript.json")

    # for faster_whisper models
    language = result.language
    language_shortcut = ""
    for key, value in LANGUAGES.items():
        if value == language:
            language_shortcut = key
            break

    # for non faster_whisper models
    if language_shortcut == "":
        language_shortcut = language
    info = TranscriptionInfo(language_shortcut)
    print(f"Detected language: {language} ({language_shortcut})")
    return result, info


def extract_words(segments):
    """
    Extracts words from segments.
    """
    words = []
    for segment in segments:
        for segword in segment.words:
            print(".", end="", flush=True)
            word = Word(
                text=segword.word,
                start=segword.start,
                end=segword.end,
                probability=segword.probability
                )
            words.append(word)

    print()
    return words


def transcribe(file_name, language=None, model="large-v3", use_stable=False):
    """
    Transcribes the given audio file using the specified model.
    Chooses between stable and faster transcription models based
    on 'use_stable' flag.
    :param file_name: Name of the audio file to transcribe.
    :param language: Language of the audio content (optional).
    :param model: Model version to use for transcription (default
      is 'large-v3').
    :param use_stable: Boolean flag to choose between stable or faster model.
    :return: Transcription result.
    """
    if use_stable:
        return stable_transcribe(file_name, language, model)
    else:
        return faster_transcribe(file_name, language, model)


def unload_model(use_stable=False):
    """
    Unloads the transcription model from memory.
    Chooses between unloading the stable or faster model based on 'use_stable'
    flag.
    :param use_stable: Boolean flag to choose between unloading stable or
      faster model.
    """
    if use_stable:
        unload_stable_model()
    else:
        unload_faster_model()
