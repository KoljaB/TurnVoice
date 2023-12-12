from RealtimeTTS import TextToAudioStream, SystemEngine, AzureEngine, ElevenlabsEngine, CoquiEngine, OpenAIEngine
from moviepy.editor import AudioFileClip 
from os.path import basename, exists, join, splitext   
from .verify import verify_synthesis
from .silence import strip_silence
from .stretch import time_stretch
import subprocess
import shutil
import time
import os

class Synthesis:
    def __init__(self, language = "en", voices=["male.wav"], engine_name="coqui"):
        if language == "zh":
            language = "zh-cn"
        
        if len(language) == 0:
            language = "en"

        self.language = language

        # self.engine_system = SystemEngine()
        # self.engine_azure = AzureEngine(os.environ.get("AZURE_SPEECH_KEY"), os.environ.get("AZURE_SPEECH_REGION"))
        # self.engine_elevenlabs = ElevenlabsEngine(os.environ.get("ELEVENLABS_API_KEY"))
        # self.engine_coqui = CoquiEngine(language=language, cloning_reference_wav=voices[self.current_voice] if voices else None)
        # self.engine_openai = OpenAIEngine()

        # self.engines = {
        #     "System Engine": self.engine_system,
        #     "Azure Engine": self.engine_azure,
        #     "Elevenlabs Engine": self.engine_elevenlabs,
        #     "Coqui Engine": self.engine_coqui
        # }        


        self.current_voice = 0
        self.voices = voices
        self.engine_name = engine_name
        self.create_engine(self.engine_name)
        self.stream = TextToAudioStream(self.engine)

    def create_engine(self, engine_name):
        self.engine_name = engine_name

        if engine_name == "system":
            self.engine = SystemEngine()
        elif engine_name == "azure":
            self.engine = AzureEngine(os.environ.get("AZURE_SPEECH_KEY"), os.environ.get("AZURE_SPEECH_REGION"))
        elif engine_name == "elevenlabs":
            self.engine = ElevenlabsEngine(os.environ.get("ELEVENLABS_API_KEY"))
        elif engine_name == "coqui":
            self.engine = CoquiEngine(language=self.language)
        elif engine_name == "openai":
            self.engine = OpenAIEngine()
        else:
            raise Exception(f"Unknown engine name {engine_name}")

        if self.voices:
            self.engine.set_voice(self.voices[self.current_voice])

    def set_language(self, language):
        if language == "zh":
            language = "zh-cn"

        self.engine.language = language

    def synthesize(self, 
                   text: str, 
                   filename: str,
                   speed:float = 1.0, 
                   speaker_index = 0,
                   ):
        
        if speaker_index != self.current_voice:
            print (f"Switching speaker to {speaker_index} with voice {self.voices[speaker_index]}")
            self.current_voice = speaker_index
            self.engine.set_voice(self.voices[speaker_index])

        print (f"Synthesizing '{text}' with voice {self.voices[self.current_voice] if self.voices else 'default'} and speed {speed} to {filename}...")
        #self.engine.set_speed(speed)
        self.stream.feed(text)

        if self.engine_name == "elevenlabs":
            audio_file_name, extension = splitext(filename)
            mp3_file_name = audio_file_name + ".mp3"
            self.stream.play(output_wavfile=mp3_file_name, muted=True)

            # convert to wav
            command = ["ffmpeg", "-y", "-i", mp3_file_name, filename]
            subprocess.run(command, check=True)
        else:
            self.stream.play(output_wavfile=filename, muted=True)

    def hallucination_free_synthesis(self,
                        text: str, 
                        filename: str,
                        speed: float = 1.0, 
                        max_last_word_distance: float = 0.35,
                        max_levenshtein_distance: float = 0.9,
                        max_jaro_winkler_distance: float = 0.9, 
                        tries: int = 5,
                        speaker_index = 0):
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
                self.synthesize(text, synthesis_attempt, speed, speaker_index)
                filename_trimmed = f"{filename}_trimmed_{attempt}.wav"

                print (f"Synthesis attempt {attempt + 1}: Stripping silence from {filename_trimmed}...")
                strip_silence(synthesis_attempt, filename_trimmed)

                # calculate levenshtein distance, jaro winkler distance and last word distance (does the last word end at the end of the file?)
                _, _, _, last_word, lev, jaro = verify_synthesis(
                    filename_trimmed, text,
                    levenshtein_threshold=max_levenshtein_distance,
                    jaro_winkler_threshold=max_jaro_winkler_distance,
                    last_word_threshold=max_last_word_distance)

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

    def synthesize_duration(self, text, base_filename, desired_duration, desired_accuracy=0.05, tries=5, speaker_index = 0):
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

        # basically ~0.3 is last the error rate that we have with the transcription word stamps currently
        # not much we can do, maybe we should just substract like 0.3 from the desired duration
        max_last_word_distance = 0.40

        # Synthesize and process the audio
        self.hallucination_free_synthesis(text, synthesis_file, speed=1.0, max_last_word_distance=max_last_word_distance, max_levenshtein_distance=0.9, max_jaro_winkler_distance=0.9, speaker_index=speaker_index)
        
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


    def synthesize_sentences(self, sentences, synthesis_dir, start_time):
        """
        Synthesizes audio for each sentence fragment.

        Parameters:
        sentences (list): List of sentence fragments with timing information.
        synthesis_dir (str): Directory to save synthesized audio files.
        start_time (float): Time when the synthesis started.
        use_stable (bool): Whether to use the stable_whisper model for verification.
        """
        successful_synthesis = 0
        for index, sentence in enumerate(sentences):
            self.print_sentence_info(sentence, index, len(sentences), start_time)

            filename = f"sentence{successful_synthesis}.wav"
            filename = os.path.join(synthesis_dir, filename) if synthesis_dir else filename

            sentence["synthesis_result"] = False
            number_of_voices = len(self.voices) if self.voices else 1

            if "speaker_index" not in sentence or number_of_voices == 1:
                print (f"no speaker index defined found for sentence {sentence['text']}, assuming 0")
                sentence["speaker_index"] = 0

            if sentence["speaker_index"] >= number_of_voices:
                print (f"Skipping synthesis for sentence {index}, no voice for speaker {sentence['speaker_index']} defined")
                continue
            
            self.synthesize_duration(
                text=sentence['text'],
                base_filename=filename,
                desired_duration=sentence["end"] - sentence["start"],
                speaker_index=sentence["speaker_index"]
            )

            if not os.path.exists(filename):
                continue

            sentence["synthesis_result"] = True
            successful_synthesis += 1

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