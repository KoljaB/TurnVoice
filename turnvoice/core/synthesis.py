from RealtimeTTS import TextToAudioStream, CoquiEngine
from moviepy.editor import AudioFileClip #, concatenate_audioclips
from .stripsilence import strip_silence
from .verify import verify_synthesis
from .stretch import time_stretch
import shutil
import time
import os

class Synthesis:
    def __init__(self, language = "en", reference_wav="TV_Total.wav"):
        if language == "zh":
            language = "zh-cn"
        
        if len(language) == 0:
            language = "en"

        self.engine = CoquiEngine(language=language, cloning_reference_wav=reference_wav)
        self.stream = TextToAudioStream(self.engine)

    def set_language(self, language):
        if language == "zh":
            language = "zh-cn"

        self.engine.language = language

    def synthesize(self, 
                   text: str, 
                   filename: str,
                   speed:float = 1.0, 
                   ):
        
        self.engine.set_speed(speed)
        self.stream.feed(text)
        self.stream.play(output_wavfile=filename, muted=True)

    def safe_synthesize(self,
                        text: str, 
                        filename: str,
                        speed: float = 1.0, 
                        max_last_word_distance: float = 0.35,
                        max_levenshtein_distance: float = 0.9,
                        max_jaro_winkler_distance: float = 0.9, 
                        tries: int = 5,
                        use_stable: bool = True):
        """
        Performs a safe synthesis (checking the synthesis quality and retrying if needed)
        We can achieve nearly hallucination-free synthesis this way.
        """
        
        if os.path.exists(filename):
            os.remove(filename)
        
        best_attempt = None
        best_average_distance = -1
        attempts_data = []

        # retry synthesis if we are not satisfied with the result
        for attempt in range(tries):
            try:
                synthesis_attempt = f"{filename}_synthesis_{attempt}.wav"
                self.synthesize(text, synthesis_attempt, speed)
                filename_trimmed = f"{filename}_trimmed_{attempt}.wav"

                print (f"Synthesis attempt {attempt + 1}: Stripping silence from {filename_trimmed}...")
                strip_silence(synthesis_attempt, filename_trimmed)

                # calculate levenshtein distance, jaro winkler distance and last word distance (does the last word end at the end of the file?)
                _, _, _, last_word, lev, jaro = verify_synthesis(
                    filename_trimmed, text,
                    levenshtein_threshold=max_levenshtein_distance,
                    jaro_winkler_threshold=max_jaro_winkler_distance,
                    last_word_threshold=max_last_word_distance,
                    use_stable=use_stable)

                # store all attempts for later
                print(f"Synthesis attempt {attempt + 1}: Last Word: {last_word:.2f}, Lev: {lev:.2f}, Jaro: {jaro:.2f}")
                attempts_data.append((filename_trimmed, last_word, lev, jaro))

                # if the result is good enough, we can stop here
                if last_word < max_last_word_distance and lev > max_levenshtein_distance and jaro > max_jaro_winkler_distance:
                    print(f"Synthesis attempt {attempt + 1} was successful.")
                    shutil.copyfile(filename_trimmed, filename)                    
                    return filename
                
                fail_reasons = []
                if last_word >= max_last_word_distance:
                    fail_reasons.append(f"last word distance was {last_word:.2f} (max {max_last_word_distance:.2f})")
                if lev <= max_levenshtein_distance:
                    fail_reasons.append(f"levenshtein distance was {lev:.2f} (min {max_levenshtein_distance:.2f})")
                if jaro <= max_jaro_winkler_distance:
                    fail_reasons.append(f"jaro winkler distance was {jaro:.2f} (min {max_jaro_winkler_distance:.2f})")
                failreason_str = ", ".join(fail_reasons)
                print(f"Synthesis attempt {attempt + 1} failed because {failreason_str}. Retrying...")

                max_last_word_distance += 0.02
                max_levenshtein_distance -= 0.01
                max_jaro_winkler_distance -= 0.01

            except PermissionError as e:
                print(f"Synthesis attempt {attempt + 1} failed due to a permission error. Retrying...")

        # if we did not find a satisfying synthesis, we first kick off the attempt with the worst last_word distance (no hallucinations)
        if attempts_data:
            attempts_data.sort(key=lambda x: x[1], reverse=True) 
            attempts_data.pop(0)  

        # then we just select the attempt with the best average text distance (least difference between feeded and detected text)
        for data in attempts_data:
            filename_attempt, last_word, lev, jaro = data
            average_distance = (lev + jaro) / 2
            if average_distance > best_average_distance:
                best_average_distance = average_distance
                best_attempt = data

        if best_attempt:
            filename_attempt, last_word, lev, jaro = best_attempt
            print(f"Selected best attempt with word distance {last_word}, levensthein distance {lev} and jaro winkler distance {jaro} based on average distance: {best_average_distance}")
            shutil.copyfile(filename_attempt, filename)                    
            return filename

        return None           

    def safe_synthesize2(self,
                        text: str, 
                        filename: str,
                        speed: float = 1.0, 
                        max_last_word_distance: float = 0.35,
                        max_levenshtein_distance: float = 0.9,
                        max_jaro_winkler_distance: float = 0.9, 
                        tries: int = 3):
        
        if os.path.exists(filename):
            os.remove(filename)
        
        best_attempt = None
        best_average_distance = -1
        attempts_data = []

        for attempt in range(tries):
            try:
                self.synthesize(text, filename, speed)
                filename_trimmed = f"{filename}_trimmed.wav"
                strip_silence(filename, filename_trimmed)

                _, _, _, last_word, lev, jaro = verify_synthesis(
                    filename_trimmed, text,
                    levenshtein_threshold=max_levenshtein_distance,
                    jaro_winkler_threshold=max_jaro_winkler_distance,
                    last_word_threshold=max_last_word_distance)

                print(f"Attempt {attempt + 1}: Last Word: {last_word:.2f}, Lev: {lev:.2f}, Jaro: {jaro:.2f}")
                attempts_data.append((filename_trimmed, lev, jaro))

                if last_word < max_last_word_distance and lev > max_levenshtein_distance and jaro > max_jaro_winkler_distance:
                    return filename_trimmed

            except PermissionError as e:
                print(f"Synthesis attempt {attempt + 1} failed due to a permission error. Retrying...")

            time.sleep(0.5)

        # Selecting the best attempt based on average distance
        for data in attempts_data:
            filename_attempt, lev, jaro = data
            average_distance = (lev + jaro) / 2
            if average_distance > best_average_distance:
                best_average_distance = average_distance
                best_attempt = filename_attempt

        if best_attempt:
            print(f"Selected best attempt based on average distance: {best_attempt}")
            return best_attempt

        return None        
        
    def synthesize_duration(self, text, base_filename, desired_duration, desired_accuracy=0.05, tries=5, use_stable=True):
        """
        Perform a safe synthesis with a desired duration and accuracy.

        Accuracy is the maximum difference between the desired duration and the actual duration.
        We can synthesize with a 50ms accuracy this way.
        """

        def generate_filename(base, suffix):
            return f"{base}_{suffix}.wav"
        
        synthesis_file = generate_filename(base_filename, "synthesis")
        if os.path.exists(base_filename):
            os.remove(base_filename)

        # Synthesize and process the audio
        self.safe_synthesize(text, synthesis_file, speed=1.0, max_last_word_distance=0.25, max_levenshtein_distance=0.9, max_jaro_winkler_distance=0.9, use_stable=use_stable)
        
        # we start with speed 1.0
        optimal_speed = 1.0

        processing_file = synthesis_file
        for attempt in range(tries):
            with AudioFileClip(processing_file) as sentence_clip:
                sentence_clip_duration = sentence_clip.duration
            
            print (f"Stretching attempt {attempt + 1}: Duration: {sentence_clip_duration:.2f}s, Desired Duration: {desired_duration:.2f}s, Optimal Speed: {optimal_speed:.2f}")

            # now we calculate the optimal speed to reach the desired duration (recursive to refine the speed with each step)
            optimal_speed = optimal_speed * (sentence_clip_duration / desired_duration)

            stretched_file = generate_filename(base_filename, f"stretched_{attempt + 1}")
            print (f"Stretching audio to {optimal_speed:.2f}x speed...")

            # with this optimal speed we stretch the audio to fit into the desired duration
            time_stretch(synthesis_file, stretched_file, optimal_speed)

            processing_file = generate_filename(base_filename, f"trimmed_stretched_{attempt + 1}")

            # since rubberbands time_stretch often introduces silence at the end of the file, we strip it
            strip_silence(stretched_file, processing_file)

            with AudioFileClip(processing_file) as final_clip:
                final_clip_duration = final_clip.duration
        
            duration_difference = final_clip_duration - desired_duration
            if abs(duration_difference) <= desired_accuracy:
                break  # Desired accuracy reached

            print(f"Attempt {attempt + 1}: Duration difference is {duration_difference:.2f} seconds")

        with AudioFileClip(processing_file) as final_clip:
            # apply fade effects to prevent clipping
            final_clip = final_clip.audio_fadein(0.05)
            final_clip = final_clip.audio_fadeout(0.05)
            
            final_clip.write_audiofile(base_filename)

        print(f"Final synthesized audio duration: {final_clip.duration:.2f}s for text '{text}' in {base_filename}")
        return base_filename   

    def close(self):
        self.engine.shutdown()


    def synthesize_sentences(self, sentences, synthesis, synthesis_dir, start_time, use_stable=True):
        """
        Synthesizes audio for each sentence fragment.

        Parameters:
        sentences (list): List of sentence fragments with timing information.
        synthesis (Synthesis): Synthesis object to generate audio.
        synthesis_dir (str): Directory to save synthesized audio files.
        """
        for index, sentence in enumerate(sentences):
            self.print_sentence_info(sentence, index, len(sentences), start_time)

            filename = f"sentence{index}.wav"
            filename = os.path.join(synthesis_dir, filename) if synthesis_dir else filename

            self.synthesize_duration(
                text=sentence['text'],
                base_filename=filename,
                desired_duration=sentence["end"] - sentence["start"],
                use_stable=use_stable
            )

            if not os.path.exists(filename):
                print(f"Synthesized file {filename} does not exist.")
                exit(0)

    def print_sentence_info(self, sentence, index, total_sentences, start_time):
        """
        Prints information about the sentence being processed.

        Parameters:
        sentence (dict): Sentence fragment with timing information.
        index (int): Index of the sentence in the list.
        total_sentences (int): Total number of sentences to process.
        """
        start, end = sentence["start"], sentence["end"]
        duration = end - start
        text = sentence["text"]
        print(f"[{start:.2f}s -> {end:.2f}s] ({duration:.2f}s) {text}")
        print(f"[{(time.time() - start_time):.1f}s] Synthesizing sentence {index}/{total_sentences}: {text}")

    def close(self):
        self.engine.shutdown()