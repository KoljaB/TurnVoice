from moviepy.editor import AudioFileClip
from turnvoice.core.fragtokenizer import create_synthesizable_fragments
from turnvoice.core.transcribe import transcribe, extract_words
from turnvoice.core.stripsilence import strip_silence
from turnvoice.core.download import fetch_youtube
from turnvoice.core.synthesis import Synthesis
from turnvoice.core.word import Word
from pydub import AudioSegment
import unittest
import shutil
import json
import os

class TestDownloadVideo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dir_with_extraction = 'test_download_with_extraction'
        cls.dir_without_extraction = 'test_download_without_extraction'

        # List of directories to be cleaned up
        directories_to_cleanup = [cls.dir_with_extraction, cls.dir_without_extraction]

        # Iterate over the list and delete each directory if it exists
        for directory in directories_to_cleanup:
            if os.path.exists(directory):
                shutil.rmtree(directory)  

    def test_video_download_with_extraction(self):
        test_url = 'https://www.youtube.com/watch?v=oeb5LdAyLC8'
        download_directory = self.dir_with_extraction

        # Test with extract=True
        video_file, audio_file, video_file_muted = fetch_youtube(test_url, extract=True, directory=download_directory)

        print(f"video_file: {video_file}, audio_file: {audio_file}, video_file_muted: {video_file_muted}")
        self.assertTrue(video_file)
        self.assertTrue(audio_file)
        self.assertTrue(video_file_muted)

    def test_video_download_without_extraction(self):
        test_url = 'https://www.youtube.com/watch?v=VV5JOQyUYNg'
        download_directory = self.dir_without_extraction

        # Test with extract=False
        video_file, audio_file, video_file_muted = fetch_youtube(test_url, extract=False, directory=download_directory)

        print(f"video_file: {video_file}, audio_file: {audio_file}, video_file_muted: {video_file_muted}")
        self.assertTrue(video_file)
        self.assertTrue(audio_file)
        self.assertTrue(video_file_muted)



class TestTranscript(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.transcribe_test_audio_file = "turnvoice/tests/audio/testaudio.wav"

        result_directory = "turnvoice/tests/results"
        if not os.path.exists(result_directory):
            os.makedirs(result_directory)

        cls.transcribe_test_transcription_file = os.path.join(result_directory, "transcription_output.txt")

    def test_transcription(self):
        # Test the accuracy of transcription
        segments, info = transcribe(self.transcribe_test_audio_file)
        self.assertIsNotNone(segments)
        self.assertIsNotNone(info)

        words = extract_words(segments)
        self.assertIsNotNone(words)

        words_dict = [word.to_dict() for word in words]

        # Serialization
        if not os.path.exists(self.transcribe_test_transcription_file):
            with open(self.transcribe_test_transcription_file, 'w') as f:
                json.dump(words_dict, f)
 
        # Deserialization
        with open(self.transcribe_test_transcription_file, 'r') as f:
            words_from_file = json.load(f)

        # Compare the original words list with the one read from file
        self.assertEqual(words_dict, words_from_file)



class TestFrag(unittest.TestCase):

    def test_fragmentation(self):
        # Setup: Create a list of Word objects
        words = [
            Word(" Hello", 0.0, 0.5), Word(" world!", 0.6, 1.1), Word(" This", 1.5, 2.0),
            Word(" is", 2.1, 2.5), Word(" a", 2.6, 3.0), Word(" test.", 3.1, 3.5)
        ]

        # Execution: Call create_synthesizable_fragments
        sentences = create_synthesizable_fragments(words)

        # Verification: Check if the sentences are correctly formed
        expected_sentences = [
            {"text": "Hello world!", "start": 0.0, "end": 1.1},
            {"text": "This is a test.", "start": 1.5, "end": 3.5}
        ]
        self.assertEqual(sentences, expected_sentences)



class TestSynthesis(unittest.TestCase):

    def test_synthesize_duration(self):
      # Setup: Create an instance of the Synthesis class
        synthesis = Synthesis(language="en")

        # Define test parameters
        text = "This is a test sentence for synthesis. We will see if the synthesized audio is of the desired duration."
        base_filename = "test_synthesis"
        desired_duration = 6.0  # In seconds

        # Execution: Call synthesize_duration
        synthesized_file = synthesis.synthesize_duration(
            text=text,
            base_filename=base_filename,
            desired_duration=desired_duration
        )

        # Verification: Check if the synthesized audio duration is close to the desired duration
        synthesized_clip = AudioFileClip(synthesized_file)
        duration_difference = abs(synthesized_clip.duration - desired_duration)
        self.assertTrue(duration_difference < 0.5)  # Tolerance of 0.5 seconds

        # # Cleanup: Remove the synthesized file
        # if os.path.exists(synthesized_file):
        #     os.remove(synthesized_file)

        # Shutdown the synthesis engine
        synthesis.close()        



class TestStripSilence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Setup paths for input and output audio files
        cls.input_audio_file = "turnvoice/tests/audio/stripsilence_test1.wav"
        cls.output_audio_file = "turnvoice/tests/audio/stripsilence_test1_out.wav"

    def test_strip_silence(self):
        # Call the strip_silence function
        strip_silence(self.input_audio_file, self.output_audio_file)

        # Load the original and stripped audio files
        original_audio = AudioSegment.from_wav(self.input_audio_file)
        stripped_audio = AudioSegment.from_wav(self.output_audio_file)

        # Check that the stripped audio is shorter than the original
        self.assertLessEqual(len(stripped_audio), len(original_audio))

    def test_no_silence(self):
        # Call the strip_silence function with an audio file that has no silence
        # You will need to create or use an audio file with no silence for this test
        no_silence_audio_file = "turnvoice/tests/audio/stripsilence_test2.wav"
        output_no_silence_file = "turnvoice/tests/audio/stripsilence_test2_out.wav"

        strip_silence(no_silence_audio_file, output_no_silence_file)

        # Check if the output file duration is the same as the input file
        input_audio = AudioSegment.from_wav(no_silence_audio_file)
        output_audio = AudioSegment.from_wav(output_no_silence_file)

        self.assertEqual(len(input_audio), len(output_audio))

    @classmethod
    def tearDownClass(cls):
        # Cleanup: Remove the output audio files
        import os
        # if os.path.exists(cls.output_audio_file):
        #     os.remove(cls.output_audio_file)
        # if os.path.exists("turnvoice/tests/audio/stripsilence_test2_out.wav"):
        #     os.remove("turnvoice/tests/audio/stripsilence_test2_out.wav")