import torch
device = torch.cuda.current_device() if torch.cuda.is_available() else -1

translator = pipeline('translation', model=model, tokenizer=tokenizer,src_lang="hi", tgt_lang="en",device=device)



input = tokenizer(src_seq)
tgt_seq_ids = model.generate(**input)
tgt_seq = tokenizer.decode(tgt_seq_ids)




translate = pipeline('translation')
tgt_seq = translate(src_seq)

# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
# tokenizer = AutoTokenizer.from_pretrained(“facebook/nllb-200-distilled-600M”)
# model = AutoModelForSeq2SeqLM.from_pretrained(“facebook/nllb-200-distilled-600M”) 
                                              
# translator = pipeline(‘translation’, model=model, tokenizer=tokenizer, src_lang=’kin_Latn’, tgt_lang=’eng_Latn’, max_length = 200)
# text=[“Niitwa Deo”, “Amakuru yawe”]
# translator(text)

# #Get the code of your target langauge. After getting the language code; get the id
# tgt_lang_id = tokenizer.lang_code_to_id[“eng_Latn”]
# #tokenize your input
# model_inputs = tokenizer(text, return_tensors=”pt”, padding=’longest’)
# #generate output
# gen_tokens = model.generate(**model_inputs , forced_bos_token_id=tgt_lang_id)
# #decode output — convert to text
# translated_text = tokenizer.batch_decode(gen_tokens, skip_special_tokens=True)
# #print
# print(translated_text)