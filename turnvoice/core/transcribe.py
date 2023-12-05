from faster_whisper import WhisperModel
from .word import Word
model_size = "large-v2"
model = WhisperModel(model_size, device="cuda", compute_type="float16")
    
def transcribe(file_name, language="en"):
    """
    Transcribes a audio file, returns transcript and word timestamps.
    """

    return model.transcribe(
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