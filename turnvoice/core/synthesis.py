from RealtimeTTS import (
    TextToAudioStream,
    SystemEngine,
    AzureEngine,
    ElevenlabsEngine,
    CoquiEngine,
    OpenAIEngine
)
from moviepy.editor import AudioFileClip
from os.path import splitext
from .verify import verify_synthesis
from .silence import strip_silence
from .stretch import time_stretch
import subprocess
import shutil
import time
import os


class Synthesis:
    def __init__(self,
                 language="en",
                 voices=None,
                 engine_names=["coqui"]
                 ):
        """
        Initializes the Synthesis class with language, voices, and TTS engines.

        :param language: Language code, defaults to 'en'.
        :param voices: List of voices, defaults to ['male.wav'].
        :param engine_names: List of engine names, defaults to ['coqui'].
        """

        self.language = "zh-cn" if language == "zh" else language
        self.language = "en" if language == "" else language

        self.voices = voices or ["male.wav"]
        self.current_voice = 0
        self.engines = {}
        self.engine_names = engine_names
        self.engine = self.set_engine_by_index(0)
        if self.voices:
            self.engine.set_voice(self.voices[self.current_voice])

        self.stream = TextToAudioStream(self.engine)

    def create_engine(self, engine_name):
        """
        Creates a TTS engine based on the specified name.

        :param engine_name: Name of the engine ('system', 'azure',
          'elevenlabs', 'coqui', 'openai').
        :return: Engine instance.
        """

        if engine_name == "system":
            return SystemEngine()
        if engine_name == "azure":
            return AzureEngine(
                os.environ.get("AZURE_SPEECH_KEY"),
                os.environ.get("AZURE_SPEECH_REGION")
                )
        if engine_name == "elevenlabs":
            return ElevenlabsEngine(
                os.environ.get("ELEVENLABS_API_KEY"),
                model="eleven_multilingual_v2"
                )
        if engine_name == "coqui":
            print(f"Language: {self.language}")
            return CoquiEngine(language=self.language)
        if engine_name == "openai":
            return OpenAIEngine()

        raise Exception(f"Unknown engine name {engine_name}")

    def set_engine(self, engine_name):
        """
        Sets the current TTS engine.
        :param engine_name: Name of the engine to set.
        :return: Engine instance.
        """

        if engine_name not in self.engines:
            self.engines[engine_name] = self.create_engine(engine_name)

        self.engine_name = engine_name

        return self.engines[engine_name]

    def set_engine_by_index(self, engine_index):
        """
        Sets the TTS engine based on the provided index.
        :param engine_index: Index of the engine in the engine list.
        """

        if engine_index >= len(self.engines):
            print(f"No engine specified for voice {engine_index + 1}. "
                  f"Using first/default engine {self.engine_names[0]}")
            engine_index = 0

        engine_name = self.engine_names[engine_index]
        self.current_engine_index = engine_index

        print(f"Switching engine to {engine_name}, "
              f"voice {self.voices[engine_index]}")

        return self.set_engine(engine_name)

    def set_language(self, language):
        """
        Sets the language for TTS synthesis.
        :param language: Language code to set.
        """
        language = "zh-cn" if language == "zh" else language
        self.engine.language = language

    def synthesize(self,
                   text: str,
                   filename: str,
                   speed: float = 1.0,
                   speaker_index=0,
                   ):
        """
        Synthesizes text into audio.
        :param text: Text to synthesize.
        :param filename: Output file name for the audio.
        :param speed: Speed of the speech (default is 1.0).
        :param speaker_index: Index of the speaker voice to use.
        """

        if speaker_index != self.current_engine_index:
            self.set_engine_by_index(speaker_index)

        if speaker_index != self.current_voice:
            print(f"Switching speaker to {speaker_index} with "
                  f"voice {self.voices[speaker_index]}"
                  )
            self.current_voice = speaker_index
            self.engine.set_voice(self.voices[speaker_index])

        voice = {self.voices[self.current_voice] if self.voices else 'default'}
        print(f"Synthesizing '{text}' with voice {voice} "
              f"and speed {speed} to {filename}...")

        self.stream.feed(text)

        if self.engine_name == "elevenlabs":
            audio_file_name, _ = splitext(filename)
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
                                     speaker_index=0):
        """
        Performs a safe synthesis (checking the synthesis quality and
        retrying if needed)
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

                print(f"Synthesis attempt {attempt + 1}: "
                      f"Stripping silence from {filename_trimmed}..."
                      )
                strip_silence(synthesis_attempt, filename_trimmed)

                # calculate levenshtein distance, jaro winkler
                # distance and last word distance (does the last word
                # end at the end of the file?)
                _, _, _, last_word, lev, jaro = verify_synthesis(
                    filename_trimmed, text,
                    levenshtein_threshold=max_levenshtein_distance,
                    jaro_winkler_threshold=max_jaro_winkler_distance,
                    last_word_threshold=max_last_word_distance)

                # store all attempts for later
                print(f"Synthesis attempt {attempt + 1}: "
                      f"Last Word: {last_word:.2f}, Lev: {lev:.2f}, "
                      f"Jaro: {jaro:.2f}"
                      )
                attempts_data.append((filename_trimmed, last_word, lev, jaro))

                # if the result is good enough, we can stop here
                if (last_word < max_last_word_distance and
                        lev > max_levenshtein_distance and
                        jaro > max_jaro_winkler_distance):

                    print(f"Synthesis attempt {attempt + 1} was successful.")
                    shutil.copyfile(filename_trimmed, filename)
                    return filename

                fail_reasons = []
                if last_word > max_last_word_distance:
                    fail_reasons.append(
                        f"last word distance was {last_word:.2f} "
                        f"(max {max_last_word_distance:.2f})"
                        )
                if lev < max_levenshtein_distance:
                    fail_reasons.append(
                        f"levenshtein distance was {lev:.2f} "
                        f"(min {max_levenshtein_distance:.2f})"
                        )
                if jaro < max_jaro_winkler_distance:
                    fail_reasons.append(
                        f"jaro winkler distance was {jaro:.2f} "
                        f"(min {max_jaro_winkler_distance:.2f})"
                        )
                failreason_str = ", ".join(fail_reasons)
                print(f"Synthesis attempt {attempt + 1} failed "
                      f"because {failreason_str}. Retrying..."
                      )

                max_last_word_distance += 0.02
                max_levenshtein_distance -= 0.01
                max_jaro_winkler_distance -= 0.01

            except PermissionError:
                print(f"Synthesis attempt {attempt + 1} failed "
                      "due to a permission error. Retrying..."
                      )

        # if we did not find a satisfying synthesis, we first kick off
        # the attempt with the worst last_word distance (no hallucinations)
        if attempts_data:
            attempts_data.sort(key=lambda x: x[1], reverse=True)
            attempts_data.pop(0)

        # then we just select the attempt with the best average text
        # distance (least difference between feeded and detected text)
        for data in attempts_data:
            filename_attempt, last_word, lev, jaro = data
            average_distance = (lev + jaro) / 2
            if average_distance > best_average_distance:
                best_average_distance = average_distance
                best_attempt = data

        if best_attempt:
            filename_attempt, last_word, lev, jaro = best_attempt
            print(f"Selected best attempt with word distance {last_word}, "
                  f"levensthein distance {lev} and jaro winkler distance "
                  f"{jaro} based on average distance: {best_average_distance}"
                  )
            shutil.copyfile(filename_attempt, filename)
            return filename

        return None

    def synthesize_duration(
        self,
        text,
        base_filename,
        desired_duration,
        desired_accuracy=0.05,
        tries=5,
        speaker_index=0
    ):
        """
        Perform a safe synthesis with a desired duration and accuracy.

        Accuracy is the maximum difference between the
        desired duration and the actual duration.
        We can synthesize with a 50ms accuracy this way.
        """

        def generate_filename(base, suffix):
            return f"{base}_{suffix}.wav"

        synthesis_file = generate_filename(base_filename, "synthesis")
        if os.path.exists(base_filename):
            os.remove(base_filename)

        # basically ~0.3 is last the error rate that we have with the
        # transcription word stamps currently not much we can do, maybe we
        # should just substract like 0.3 from the desired duration
        max_last_word_distance = 0.40

        # Synthesize and process the audio
        self.hallucination_free_synthesis(
            text,
            synthesis_file,
            speed=1.0,
            max_last_word_distance=max_last_word_distance,
            max_levenshtein_distance=0.9,
            max_jaro_winkler_distance=0.9,
            speaker_index=speaker_index
        )

        # we start with speed 1.0
        optimal_speed = 1.0

        processing_file = synthesis_file
        for attempt in range(tries):
            with AudioFileClip(processing_file) as sentence_clip:
                sentence_clip_duration = sentence_clip.duration

            print(f"Stretching attempt {attempt + 1}: "
                  f"Duration: {sentence_clip_duration:.2f}s, "
                  f"Desired Duration: {desired_duration:.2f}s, "
                  f"Optimal Speed: {optimal_speed:.2f}"
                  )

            # now we calculate the optimal speed to reach the desired duration
            # (recursive to refine the speed with each step)
            optimal_speed = (
                optimal_speed * (sentence_clip_duration / desired_duration)
            )

            stretched_file = generate_filename(
                base_filename,
                f"stretched_{attempt + 1}"
                )
            print(f"Stretching audio to {optimal_speed:.2f}x speed...")

            # with this optimal speed we stretch the audio
            # to fit into the desired duration
            if optimal_speed < 0.3:
                optimal_speed = 0.3
            if optimal_speed > 2.5:
                optimal_speed = 2.5
            time_stretch(synthesis_file, stretched_file, optimal_speed)

            processing_file = generate_filename(
                base_filename,
                f"trimmed_stretched_{attempt + 1}"
                )

            # since rubberbands time_stretch often introduces silence
            # at the end of the file, we strip it
            strip_silence(stretched_file, processing_file)

            with AudioFileClip(processing_file) as final_clip:
                final_clip_duration = final_clip.duration

            duration_difference = final_clip_duration - desired_duration
            if abs(duration_difference) <= desired_accuracy:
                break  # Desired accuracy reached

            print(f"Attempt {attempt + 1}: Duration difference "
                  f"is {duration_difference:.2f} seconds")

        with AudioFileClip(processing_file) as final_clip:
            # apply fade effects to prevent clipping
            final_clip = final_clip.audio_fadein(0.05)
            final_clip = final_clip.audio_fadeout(0.05)

            final_clip.write_audiofile(base_filename)

        print(f"Final synthesized audio duration: {final_clip.duration:.2f}s "
              f"for text '{text}' in {base_filename}")

        return base_filename

    def synthesize_sentences(self, sentences, synthesis_dir, start_time):
        """
        Synthesizes audio for each sentence fragment.

        Parameters:
        sentences (list): List of sentence fragments with timing information.
        synthesis_dir (str): Directory to save synthesized audio files.
        start_time (float): Time when the synthesis started.
        use_stable (bool): Whether to use the stable_whisper
            model for verification.
        """

        # Sort sentences by start time
        successful_synthesis = 0
        for index, sentence in enumerate(sentences):
            self.print_sentence_info(
                sentence, index, len(sentences), start_time
            )

            filename = f"sentence{successful_synthesis}.wav"
            if synthesis_dir:
                filename = os.path.join(synthesis_dir, filename)

            sentence["synthesis_result"] = False
            number_of_voices = len(self.voices) if self.voices else 1

            if "speaker_index" not in sentence or number_of_voices == 1:
                print("no speaker index defined found for sentence "
                      f"{sentence['text']}, assuming 0"
                      )
                sentence["speaker_index"] = 0

            sentence["speaker_index"] = int(sentence["speaker_index"])

            if sentence["speaker_index"] >= number_of_voices:
                print(f"Skipping synthesis for sentence {index}, "
                      f"no voice for speaker {sentence['speaker_index']} "
                      "defined"
                      )
                continue

            self.synthesize_duration(
                text=sentence["text"],
                base_filename=filename,
                desired_duration=sentence["end"] - sentence["start"],
                speaker_index=sentence["speaker_index"]
            )

            if not os.path.exists(filename):
                continue

            sentence["synthesis_result"] = True
            successful_synthesis += 1

    def print_sentence_info(self,
                            sentence,
                            index,
                            total_sentences,
                            start_time
                            ):
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
        print(f"[{(time.time() - start_time):.1f}s] "
              f"Synthesizing sentence {index}/{total_sentences}: {text}"
              )

    def close(self):
        self.engine.shutdown()
