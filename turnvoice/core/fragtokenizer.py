from .word import Word

# define characters that indicate the end of a sentence.
start_break_characters = ('.', '!', '?', ',')

# list of abbreviations and acronyms that shouldn't be treated as sentence breaks.
start_no_break_words = [
    "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "St.", "Ave.", "Rd.", "Jan.", "Feb.", "Mar.", 
    "Apr.", "Jun.", "Jul.", "Aug.", "Sep.", "Sept.", "Oct.", "Nov.", "Dec.", "vs.", "etc.",
    "e.g.", "i.e.", "U.S.", "U.K.", "U.N.", "N.A.S.A.", "F.B.I.", "C.I.A.", "D.C.", "U.S.A.", 
    "U.S.S.R.", "U.S.S.", "U.S.C.", "U.S.M.C.", "U.S.N.", "U.S.P.S.", "U.S.S.", "U.S"
]

def create_synthesizable_fragments(
        words,
        gap_duration: float = 1.0,
        break_characters = start_break_characters,
        no_break_words = start_no_break_words):
    """
    Analyze a list of Word objects and create synthesizable fragments (sentences) based on certain rules.

    Args:
    words (list of Word): List of Word objects to analyze.
    gap_duration (float): The minimum duration of a gap between words to consider it as a sentence break. Default is 1.0 seconds.
    break_characters (tuple): Characters that typically indicate the end of a sentence.
    no_break_words (list of str): Abbreviations or acronyms that should not be treated as sentence breaks.

    Returns:
    list: A list of dictionaries, each containing the 'text', 'start', and 'end' keys representing each sentence fragment.
    """

    sentences = []  # holds sentence frags
    current_sentence = ""  # accumulates words
    sentence_start_time = 0.0  # start time of a sentence

    for index, word in enumerate(words):

        # if starting a new sentence, record the start time
        if current_sentence == "":
            sentence_start_time = word.start

        # add the current word's text to the sentence
        current_sentence += word.text

        # initialize a flag for a big gap before the next word
        big_gap_to_next_word = False  

        if index + 1 < len(words):

            # calculate the gap to the next word
            gap_to_next_word = words[index + 1].start - word.end  

            if gap_to_next_word > gap_duration:
                big_gap_to_next_word = True 

        # check if the current word is the last in the list
        is_last_word = index + 1 == len(words)  

        # check conditions to finalize the current sentence
        if big_gap_to_next_word or is_last_word or (word.text.endswith(break_characters) and not word.text in no_break_words):
            sentence_duration = word.end - sentence_start_time  # Calculate the sentence duration.
            
            # check if it's time to end the sentence.
            if is_last_word or big_gap_to_next_word or sentence_duration > gap_duration:

                sentence_end_time = word.end                 
                sentences.append({"text": current_sentence.strip(), "start": sentence_start_time, "end": sentence_end_time})

                # reset the current sentence
                current_sentence = ""  

    return sentences