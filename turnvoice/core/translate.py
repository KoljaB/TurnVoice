from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import torch

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

def translate(text: str, source: str = "en", target: str = "de") -> str:
    # Get the source and target language tokens
    src_token = find_language_token(source)
    tgt_token = find_language_token(target)

    if not src_token or not tgt_token:
        raise ValueError("Invalid source or target language shortcut.")

    # Load the tokenizer with source and target language tokens
    tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang=src_token, tgt_lang=tgt_token)

    # Create the translation pipeline
    translator = pipeline('translation', model=model, tokenizer=tokenizer, src_lang=src_token, tgt_lang=tgt_token, device=device)

    # Translate the text
    translated_text = translator(text, max_length=128)
    translated_text = translated_text[0]['translation_text']

    #print (f"Translated from language {source} to {target}: text \"{text}\" to \"{translated_text}\"")
    print (f"Translated \"{text}\" to \"{translated_text}\"")
    return translated_text

def shortcut_to_name(shortcut: str) -> str:
    for language in languages:
        if language['shortcut'] == shortcut:
            return language['name']

    return 'Unknown'

# # Example usage
#print(shortcut_to_name('en'))  # Should return 'English'
# print(shortcut_to_name('xyz'))  # Should return 'Unknown'


# # Example usage
text = "Hello, how are you?"
translated_text = translate(text, source="en", target="de")
print(translated_text)

# def shortcut_to_name(shortcut: str) -> str:
    

#     languages = [
#         {'name': 'English', 'shortcut': 'en', 'token': 'eng_Latn'},
#         {'name': 'Spanish', 'shortcut': 'es', 'token': 'spa_Latn'},
#         {'name': 'French', 'shortcut': 'fr', 'token': 'fra_Latn'},
#         {'name': 'German', 'shortcut': 'de', 'token': 'deu_Latn'},
#         {'name': 'Italian', 'shortcut': 'it', 'token': 'ita_Latn'},
#         {'name': 'Portuguese', 'shortcut': 'pt', 'token': 'por_Latn'},
#         {'name': 'Polish', 'shortcut': 'pl', 'token': 'pol_Latn'},
#         {'name': 'Turkish', 'shortcut': 'tr', 'token': 'tur_Latn'},
#         {'name': 'Russian', 'shortcut': 'ru', 'token': 'rus_Cyrl'},
#         {'name': 'Dutch', 'shortcut': 'nl', 'token': 'nld_Latn'},
#         {'name': 'Czech', 'shortcut': 'cs', 'token': 'ces_Latn'},
#         {'name': 'Arabic', 'shortcut': 'ar', 'token': 'arb_Arab'},
#         {'name': 'Chinese', 'shortcut': 'zh-cn', 'token': 'zho_Hans'},
#         {'name': 'Japanese', 'shortcut': 'ja', 'token': 'jpn_Jpan'},
#         {'name': 'Hungarian', 'shortcut': 'hu', 'token': 'hun_Latn'},
#         {'name': 'Korean', 'shortcut': 'ko', 'token': 'kor_Hang'},
#         {'name': 'Hindi', 'shortcut': 'hi', 'token': 'hin_Deva'}
#     ]



# from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
# import torch

# def translate(text: str, source: str = "en", target: str = "de") -> str:



# #set the device
# device = torch.cuda.current_device() if torch.cuda.is_available() else -1

# #load the model
# model_name = 'facebook/nllb-200-distilled-600M'
# model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# #load the tokenizer
# tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang="deu_Latn", tgt_lang="eng_Latn")

# #create the pipeline object
# translator = pipeline('translation', model=model, tokenizer=tokenizer, src_lang="deu_Latn", tgt_lang="eng_Latn",device=device)  

# #text = "Na, alles klar? Hoffe, das wird hier jetzt mal so richtig anständig übersetzt. Sonst gibt es aber Haue."
# text = "Na, alles klar?"

# #get the target sentence
# target_seq = translator(text, max_length=128)

# #display the target sentence
# print(target_seq [0]['translation_text'])
# #output : Rahul was awarded Man of the Match for his outstanding batting and fielding.

# languages = [
#     {'name': 'English', 'shortcut': 'en', 'token': 'eng_Latn'},
#     {'name': 'Spanish', 'shortcut': 'es', 'token': 'spa_Latn'},
#     {'name': 'French', 'shortcut': 'fr', 'token': 'fra_Latn'},
#     {'name': 'German', 'shortcut': 'de', 'token': 'deu_Latn'},
#     {'name': 'Italian', 'shortcut': 'it', 'token': 'ita_Latn'},
#     {'name': 'Portuguese', 'shortcut': 'pt', 'token': 'por_Latn'},
#     {'name': 'Polish', 'shortcut': 'pl', 'token': 'pol_Latn'},
#     {'name': 'Turkish', 'shortcut': 'tr', 'token': 'tur_Latn'},
#     {'name': 'Russian', 'shortcut': 'ru', 'token': 'rus_Cyrl'},
#     {'name': 'Dutch', 'shortcut': 'nl', 'token': 'nld_Latn'},
#     {'name': 'Czech', 'shortcut': 'cs', 'token': 'ces_Latn'},
#     {'name': 'Arabic', 'shortcut': 'ar', 'token': 'arb_Arab'},
#     {'name': 'Chinese', 'shortcut': 'zh-cn', 'token': 'zho_Hans'},
#     {'name': 'Japanese', 'shortcut': 'ja', 'token': 'jpn_Jpan'},
#     {'name': 'Hungarian', 'shortcut': 'hu', 'token': 'hun_Latn'},
#     {'name': 'Korean', 'shortcut': 'ko', 'token': 'kor_Hang'},
#     {'name': 'Hindi', 'shortcut': 'hi', 'token': 'hin_Deva'}
# ]

# English (en)
# eng_Latn
# Spanish (es)
# spa_Latn
# French (fr)
# fra_Latn
# German (de)
# deu_Latn
# Italian (it)
# ita_Latn
# Portuguese (pt)
# por_Latn
# Polish (pl)
# pol_Latn
# Turkish (tr)
# tur_Latn
# Russian (ru)
# rus_Cyrl
# Dutch (nl)
# nld_Latn
# Czech (cs)
# ces_Latn
# Arabic (ar)
# arb_Arab
# Chinese (zh-cn)
# zho_Hans
# Japanese (ja)
# jpn_Jpan
# Hungarian (hu)
# hun_Latn
# Korean (ko)
# kor_Hang
# Hindi (hi)
# hin_Deva

# ... Hindi (hi)  mit 2.0.3

# List of Languages supported by Coqui XTTS 2.0.2
# https://huggingface.co/coqui/XTTS-v2

# English (en)
# Spanish (es)
# French (fr)
# German (de)
# Italian (it)
# Portuguese (pt)
# Polish (pl)
# Turkish (tr)
# Russian (ru)
# Dutch (nl)
# Czech (cs)
# Arabic (ar)
# Chinese (zh-cn)
# Japanese (ja)
# Hungarian (hu)
# Korean (ko)

# ... Hindi (hi)  mit 2.0.3


# List of Languages supported by NLLB-200 translate:
# https://ai.meta.com/research/no-language-left-behind/#200-languages-accordion

# Acehnese (Latin script)
# Arabic (Iraqi/Mesopotamian)
# Arabic (Yemen)
# Arabic (Tunisia)
# Afrikaans
# Arabic (Jordan)
# Akan
# Amharic
# Arabic (Lebanon)
# Arabic (MSA)
# Arabic (Modern Standard Arabic)
# Arabic (Saudi Arabia)
# Arabic (Morocco)
# Arabic (Egypt)
# Assamese
# Asturian
# Awadhi
# Aymara
# Crimean Tatar
# Welsh
# Danish
# German
# French
# Friulian
# Fulfulde
# Dinka(Rek)
# Dyula
# Dzongkha
# Greek
# English
# Esperanto
# Estonian
# Basque
# Ewe
# Faroese
# Iranian Persian
# Icelandic
# Italian
# Javanese
# Japanese
# Kabyle
# Kachin | Jinghpo
# Kamba
# Kannada
# Kashmiri (Arabic script)
# Kashmiri (Devanagari script)
# Georgian
# Kanuri (Arabic script)
# Kanuri (Latin script)
# Kazakh
# Kabiye
# Thai
# Khmer
# Kikuyu
# South Azerbaijani
# North Azerbaijani
# Bashkir
# Bambara
# Balinese
# Belarusian
# Bemba
# Bengali
# Bhojpuri
# Banjar (Latin script)
# Tibetan
# Bosnian
# Buginese
# Bulgarian
# Catalan
# Cebuano
# Czech
# Chokwe
# Central Kurdish
# Fijian
# Finnish
# Fon
# Scottish Gaelic
# Irish
# Galician
# Guarani
# Gujarati
# Haitian Creole
# Hausa
# Hebrew
# Hindi
# Chhattisgarhi
# Croatian
# Hugarian
# Armenian
# Igobo
# IIocano
# Indonesian
# Kinyarwanda
# Kyrgyz
# Kimbundu
# Konga
# Korean
# Kurdish (Kurmanji)
# Lao
# Latvian (Standard)
# Ligurian
# Limburgish
# Lingala
# Lithuanian
# Lombard
# Latgalian
# Luxembourgish
# Luba-Kasai
# Ganda
# Dholuo
# Mizo


# List of Language tokens supported by NLLB-200 translate:
# https://huggingface.co/facebook/nllb-200-3.3B/blob/main/special_tokens_map.json

# "ace_Arab",
# "ace_Latn",
# "acm_Arab",
# "acq_Arab",
# "aeb_Arab",
# "afr_Latn",
# "ajp_Arab",
# "aka_Latn",
# "amh_Ethi",
# "apc_Arab",
# "arb_Arab",
# "ars_Arab",
# "ary_Arab",
# "arz_Arab",
# "asm_Beng",
# "ast_Latn",
# "awa_Deva",
# "ayr_Latn",
# "azb_Arab",
# "azj_Latn",
# "bak_Cyrl",
# "bam_Latn",
# "ban_Latn",
# "bel_Cyrl",
# "bem_Latn",
# "ben_Beng",
# "bho_Deva",
# "bjn_Arab",
# "bjn_Latn",
# "bod_Tibt",
# "bos_Latn",
# "bug_Latn",
# "bul_Cyrl",
# "cat_Latn",
# "ceb_Latn",
# "ces_Latn",
# "cjk_Latn",
# "ckb_Arab",
# "crh_Latn",
# "cym_Latn",
# "dan_Latn",
# "deu_Latn",
# "dik_Latn",
# "dyu_Latn",
# "dzo_Tibt",
# "ell_Grek",
# "eng_Latn",
# "epo_Latn",
# "est_Latn",
# "eus_Latn",
# "ewe_Latn",
# "fao_Latn",
# "pes_Arab",
# "fij_Latn",
# "fin_Latn",
# "fon_Latn",
# "fra_Latn",
# "fur_Latn",
# "fuv_Latn",
# "gla_Latn",
# "gle_Latn",
# "glg_Latn",
# "grn_Latn",
# "guj_Gujr",
# "hat_Latn",
# "hau_Latn",
# "heb_Hebr",
# "hin_Deva",
# "hne_Deva",
# "hrv_Latn",
# "hun_Latn",
# "hye_Armn",
# "ibo_Latn",
# "ilo_Latn",
# "ind_Latn",
# "isl_Latn",
# "ita_Latn",
# "jav_Latn",
# "jpn_Jpan",
# "kab_Latn",
# "kac_Latn",
# "kam_Latn",
# "kan_Knda",
# "kas_Arab",
# "kas_Deva",
# "kat_Geor",
# "knc_Arab",
# "knc_Latn",
# "kaz_Cyrl",
# "kbp_Latn",
# "kea_Latn",
# "khm_Khmr",
# "kik_Latn",
# "kin_Latn",
# "kir_Cyrl",
# "kmb_Latn",
# "kon_Latn",
# "kor_Hang",
# "kmr_Latn",
# "lao_Laoo",
# "lvs_Latn",
# "lij_Latn",
# "lim_Latn",
# "lin_Latn",
# "lit_Latn",
# "lmo_Latn",
# "ltg_Latn",
# "ltz_Latn",
# "lua_Latn",
# "lug_Latn",
# "luo_Latn",
# "lus_Latn",
# "mag_Deva",
# "mai_Deva",
# "mal_Mlym",
# "mar_Deva",
# "min_Latn",
# "mkd_Cyrl",
# "plt_Latn",
# "mlt_Latn",
# "mni_Beng",
# "khk_Cyrl",
# "mos_Latn",
# "mri_Latn",
# "zsm_Latn",
# "mya_Mymr",
# "nld_Latn",
# "nno_Latn",
# "nob_Latn",
# "npi_Deva",
# "nso_Latn",
# "nus_Latn",
# "nya_Latn",
# "oci_Latn",
# "gaz_Latn",
# "ory_Orya",
# "pag_Latn",
# "pan_Guru",
# "pap_Latn",
# "pol_Latn",
# "por_Latn",
# "prs_Arab",
# "pbt_Arab",
# "quy_Latn",
# "ron_Latn",
# "run_Latn",
# "rus_Cyrl",
# "sag_Latn",
# "san_Deva",
# "sat_Beng",
# "scn_Latn",
# "shn_Mymr",
# "sin_Sinh",
# "slk_Latn",
# "slv_Latn",
# "smo_Latn",
# "sna_Latn",
# "snd_Arab",
# "som_Latn",
# "sot_Latn",
# "spa_Latn",
# "als_Latn",
# "srd_Latn",
# "srp_Cyrl",
# "ssw_Latn",
# "sun_Latn",
# "swe_Latn",
# "swh_Latn",
# "szl_Latn",
# "tam_Taml",
# "tat_Cyrl",
# "tel_Telu",
# "tgk_Cyrl",
# "tgl_Latn",
# "tha_Thai",
# "tir_Ethi",
# "taq_Latn",
# "taq_Tfng",
# "tpi_Latn",
# "tsn_Latn",
# "tso_Latn",
# "tuk_Latn",
# "tum_Latn",
# "tur_Latn",
# "twi_Latn",
# "tzm_Tfng",
# "uig_Arab",
# "ukr_Cyrl",
# "umb_Latn",
# "urd_Arab",
# "uzn_Latn",
# "vec_Latn",
# "vie_Latn",
# "war_Latn",
# "wol_Latn",
# "xho_Latn",
# "ydd_Hebr",
# "yor_Latn",
# "yue_Hant",
# "zho_Hans",
# "zho_Hant",
# "zul_Latn"