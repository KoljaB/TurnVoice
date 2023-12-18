class Word:
    """
    Represents a word with start and end times and a probability score.
    """

    def __init__(self, 
                 text: str,
                 start: float,
                 end: float,
                 probability: float = 0.0):

        """
        Initializes a Word object with text,
        start time, end time, and probability.
        """
        self.text = text
        self.start = start
        self.end = end
        self.probability = probability

    def to_dict(self):
        """
        Returns a dictionary representation of the Word object.
        """
        return {
            'text': self.text,
            'start': self.start,
            'end': self.end,
            'probability': self.probability
        }

    @staticmethod
    def from_dict(data):
        """
        Creates a Word object from a dictionary.
        """
        return Word(**data)
