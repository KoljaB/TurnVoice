# TurnVoice 🎬

A command-line tool to replace voices in youtube videos.

## Installation 

```
pip install turnvoice
```

For a speedier experience, prepare your [CUDA](https://pytorch.org/get-started/locally/) environment:

**CUDA 11.8:**
```
pip install torch==2.1.1+cu118 torchaudio==2.1.1+cu118 --index-url https://download.pytorch.org/whl/cu118
```

**CUDA v12.1:**
```
pip install torch==2.1.1+cu118 torchaudio==2.1.1+cu211 --index-url https://download.pytorch.org/whl/cu211
```

## Usage 🎮

```bash
turnvoice -u <YouTube Video URL> -rw <Reference WAV File> -ov <Output Video Filename>
```

### Parameters Explained:

- `-u`, `--url`: (required) The YouTube video URL you want to transform.
- `-l`, `--language`: The language for transcription and synthesis (default: 'en').
- `-dd`, `--download_directory`: Where to save the video downloads (default: 'downloads').
- `-sd`, `--synthesis_directory`: Secret lab for tts synthesis audio files (default: 'synthesis').
- `-e`, `--extract`: To extract or not to extract audio directly from the video? That is the question. False can lead to better quality but also increase likelihood of errors.
- `-rw`, `--reference_wav`: Your chosen voice in wav format (24000 Hz, 16 bit)
- `-ov`, `--output_video`: The grand finale video file name (default: 'final_cut.mp4').

### Example Command:

Ever wanted Arthur Morgan to narrate a cooking tutorial? Here's how:

```bash
turnvoice -u https://www.youtube.com/watch?v=AmC9SmCBUj4 -rw arthur.wav -ov cooking_with_arthur.mp4
```

*This example needs a arthur.wav clone wav file in the same directory. May magically work when executed from the test directory though.*

## Pro Tips 🧙‍♂️

### The Art of Choosing a Reference Wav:
- A 24000, 44100 or 22050 Hz 16-bit, mono wav file of 10-30 seconds is your golden ticket.
- Audacity is your friend for adjusting sample rates. Experiment with frame rates for best results!

### Fixed TTS Model Download Folder:
Keep your models organized! Set `COQUI_MODEL_PATH` to your preferred folder.

Windows example:
```bash
setx COQUI_MODEL_PATH "C:\Downloads\CoquiModels"
```

## Future Improvements 🚀

- **Optional Translation**: Polyglot? Coming soon!
- **Optimized Synthesis**: Reducing the synthesis tries for faster results.
- **Voice Cloning from YouTube**: Imagine cloning voices directly from other videos!

## License 📜

TurnVoice is proudly under the [Coqui Public Model License 1.0.0](https://coqui.ai/cpml). 

## Let's Make It Fun! 🎉

[Share](https://github.com/KoljaB/TurnVoice/discussions) your funniest or most creative TurnVoice creations with me! 

And if you've got a cool feature idea or just want to say hi, drop me a line on

- [Twitter](https://twitter.com/LonLigrin)  
- [Reddit](https://www.reddit.com/user/Lonligrin)  
- [EMail](mailto:kolja.beigel@web.de)  

Don't forget to leave a star.