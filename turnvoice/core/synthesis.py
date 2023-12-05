from RealtimeTTS import TextToAudioStream, CoquiEngine
from moviepy.editor import AudioFileClip
from .stripsilence import strip_silence
import shutil
import time
import os

class Synthesis:
    def __init__(self, language = "en", reference_wav="TV_Total.wav"):
        self.engine = CoquiEngine(language=language, cloning_reference_wav=reference_wav)
        self.stream = TextToAudioStream(self.engine)

    def synthesize(self, 
                   text: str, 
                   filename: str,
                   speed:float = 1.0, 
                   ):
        
        self.engine.set_speed(speed)
        self.stream.feed(text)
        self.stream.play(output_wavfile=filename, muted=True)

    def synthesize_duration(self, 
                            text: str, 
                            base_filename: str,
                            desired_duration: float,
                            tries: int = 5,
                            speed_change_per_try: float = 0.1):
        
        if os.path.exists(base_filename):
            os.remove(base_filename )

        current_speed = 1.0
        duration_differences = {}

        for i in range(tries):
            # Generate a unique filename for each try
            filename = f"{base_filename}_{i}.wav"
            filename_synthesis_untrimmed = f"{base_filename}_{i}_raw.wav"

            if i == 0:
                print(f"Try {i+1}: Speed: {current_speed} for text {text}")
            else:
                print(f"try {i+1}: Speed: {current_speed}")

            self.synthesize(text, filename_synthesis_untrimmed, speed=current_speed)

            # strip silence from the synthesized audio
            strip_silence(filename_synthesis_untrimmed, filename)

            sentence_clip = AudioFileClip(filename)

            # Calculate and store the duration difference
            duration_difference = abs(sentence_clip.duration - desired_duration)
            duration_differences[filename] = duration_difference

            # Break the loop if the duration is close enough
            if duration_difference < 0.15:
                break

            # Adjust the speed for the next try
            if i == 0:
                current_speed = sentence_clip.duration / desired_duration
            elif sentence_clip.duration > desired_duration:
                current_speed += speed_change_per_try
            else:
                current_speed -= speed_change_per_try

        # Find the file with the smallest duration difference
        best_file = min(duration_differences, key=duration_differences.get)
        print(f"Best file: {best_file} with duration difference: {duration_differences[best_file]}")

        retry_attempts = 10
        for attempt in range(retry_attempts):
            try:
                shutil.copyfile(best_file, base_filename)
                return base_filename 
            except PermissionError as e:
                print (f"Rename attempt {attempt + 1} failed. Retrying...")
                time.sleep(1)  

        return best_file        

    def close(self):
        self.engine.shutdown()