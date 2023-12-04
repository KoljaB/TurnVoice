class Word:
    def __init__(self, 
                 text: str, 
                 start: float, 
                 end: float, 
                 probability: float = 0.0):
        self.text = text
        self.start = start
        self.end = end
        self.probability = probability

    def to_dict(self):
        return {
            'text': self.text,
            'start': self.start,
            'end': self.end,
            'probability': self.probability
        }

    @staticmethod
    def from_dict(data):
        return Word(**data)