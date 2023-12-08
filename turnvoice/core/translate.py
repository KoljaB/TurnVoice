from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import torch
import gc

# Set the device
device = torch.cuda.current_device() if torch.cuda.is_available() else -1

# Load the model
model_name = 'facebook/nllb-200-distilled-600M'
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

languages = [
    {'name': 'English', 'shortcut': 'en', 'token': 'eng_Latn'},
    {'name': 'Spanish', 'shortcut': 'es', 'token': 'spa_Latn'},
    {'name': 'French', 'shortcut': 'fr', 'token': 'fra_Latn'},
    {'name': 'German', 'shortcut': 'de', 'token': 'deu_Latn'},
    {'name': 'Italian', 'shortcut': 'it', 'token': 'ita_Latn'},
    {'name': 'Portuguese', 'shortcut': 'pt', 'token': 'por_Latn'},
    {'name': 'Polish', 'shortcut': 'pl', 'token': 'pol_Latn'},
    {'name': 'Turkish', 'shortcut': 'tr', 'token': 'tur_Latn'},
    {'name': 'Russian', 'shortcut': 'ru', 'token': 'rus_Cyrl'},
    {'name': 'Dutch', 'shortcut': 'nl', 'token': 'nld_Latn'},
    {'name': 'Czech', 'shortcut': 'cs', 'token': 'ces_Latn'},
    {'name': 'Arabic', 'shortcut': 'ar', 'token': 'arb_Arab'},
    {'name': 'Chinese', 'shortcut': 'zh-cn', 'token': 'zho_Hans'},
    {'name': 'Japanese', 'shortcut': 'ja', 'token': 'jpn_Jpan'},
    {'name': 'Hungarian', 'shortcut': 'hu', 'token': 'hun_Latn'},
    {'name': 'Korean', 'shortcut': 'ko', 'token': 'kor_Hang'},
    {'name': 'Hindi', 'shortcut': 'hi', 'token': 'hin_Deva'}
]

def find_language_token(shortcut: str) -> str:
    for language in languages:
        if language['shortcut'] == shortcut:
            return language['token']
    return None

pipelines = {}

def get_pipeline(source: str, target: str):
    global pipelines
    pipeline_key = f"{source}->{target}"

    if pipeline_key not in pipelines:
        src_token = find_language_token(source)
        tgt_token = find_language_token(target)

        if not src_token or not tgt_token:
            raise ValueError("Invalid source or target language shortcut.")

        # Load the tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang=src_token, tgt_lang=tgt_token)

        # Create the translation pipeline
        device = torch.cuda.current_device() if torch.cuda.is_available() else -1
        translator = pipeline('translation', model=model, tokenizer=tokenizer, src_lang=src_token, tgt_lang=tgt_token, device=device)

        pipelines[pipeline_key] = translator

    return pipelines[pipeline_key]

def translate(text: str, source: str = "en", target: str = "de") -> str:
    translator = get_pipeline(source, target)

    # Perform translation
    translated_text = translator(text, max_length=128)
    translated_text = translated_text[0]['translation_text']
    print (f"Translated \"{text}\" to \"{translated_text}\"")

    return translated_text

def shortcut_to_name(shortcut: str) -> str:
    for language in languages:
        if language['shortcut'] == shortcut:
            return language['name']

    return 'Unknown'

def translate_model_unload():
    global model, pipelines
    if model:
        del model
        torch.cuda.empty_cache()
        gc.collect()
        from numba import cuda
        device = cuda.get_current_device()
        device.reset()
        model = None
        pipelines = {}
        print("Translation model unloaded successfully.")
    else:
        print("Translation model is not loaded.")