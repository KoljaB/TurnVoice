# TurnVoice

A command-line tool (currently in pre-alpha) to **transform voices** in YouTube videos with additional **translation** capabilities.  

## New Features

- **Voice replacement**: Strips out vocal track and recomposes to preserve original background audio
- **Speaker diarization**: Replace specific speaker voice from a video 

## Prerequisites

- [Rubberband](https://breakfastquay.com/rubberband/) command-line utility installed (needed to pitchpreserve timestretch audios)

- [Deezer's Spleeter](https://github.com/deezer/spleeter) command-line utility installed (needed for audio preservation to split vocals, install python 3.8 and then run 'pipx install spleeter --python /path/to/python3.8')

- huggingface access token in env variable HF_ACCESS_TOKEN (needed for identifying speakers to download the pyannote.audio speaker diarization model, see diarize.py)

## Installation 

```
pip install turnvoice
```

For faster rendering prepare your [CUDA](https://pytorch.org/get-started/locally/) environment:

**CUDA 11.8:**
```
pip install torch==2.1.1+cu118 torchaudio==2.1.1+cu118 --index-url https://download.pytorch.org/whl/cu118
```

**CUDA v12.1:**
```
pip install torch==2.1.1+cu118 torchaudio==2.1.1+cu211 --index-url https://download.pytorch.org/whl/cu211
```

Installation in a virtual environment is recommended.

## Usage

```bash
turnvoice [-u] <YouTube Video URL|ID> [-l] <Translation Language> -r <Reference WAV File> -o <Output Video Filename>
```

For example, this is musk's voice replaced with the male default voice:
```bash
turnvoice RK91Ji6GCZ8
```

Same translated to spanish:
```bash
turnvoice RK91Ji6GCZ8 es
```

### Parameters Explained:

- `-i`, `--in`: (required) The YouTube video ID or URL you want to transform
- `-l`, `--language`: Language to translate to (supported: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh, ja, hu, ko)
   *leaving this out keeps the source video language*
- `-v`, `--voice`: Your chosen voice in wav format (24kHz, 16 bit, mono, ~10-30s)
- `-o`, `--output_video`: The grand finale video file name (default: 'final_cut.mp4')
- `-a`, `--analysis`: Enable analysis mode. Only generates the transcription and speaker diarization, doesn't render the video
- `-s`, `--speaker`: Speaker number to be turned. Speakers are sorted by amount of speech. Perform --analysis before.
- `-from`, `--from`: Time to start processing the video from
- `-to`, `--to`: Time to stop processing the video at
- `-dd`, `--download_directory`: Where to save the video downloads (default: 'downloads')
- `-sd`, `--synthesis_directory`: Where to save the text to speech audio files (default: 'synthesis')
- `-e`, `--extractoff`: Use with -e to disable extract audio directly from the video (may lead to higher quality while also increasing likelihood of errors)
- `-c`, `--clean_audio`: No preserve of original audio in the final video. Returns clean synthesis

You can leave out -i and -l as first parameters.

### Example Command:

Arthur Morgan narrating a cooking tutorial:

```bash
turnvoice AmC9SmCBUj4 -v arthur.wav -o cooking_with_arthur.mp4
```

*This example needs a arthur.wav (or.json) file in the same directory. Works when executed from the tests directory.*

## What to expect

- might not always achieve perfect lip synchronization, especially when translating to a different language
- translation feature is currently in experimental prototype state (powered by Meta's nllb-200-distilled-600m) and still produces very imperfect results
- occasionally, the synthesis might introduce unexpected noises or distortions in the audio (we got WAY better reducing artifacts with the new v0.0.30 algo)

## Source Quality

- delivers best results with YouTube videos featuring **clear spoken** content (podcasts, educational videos)
- requires a high-quality, **clean** source WAV file for effective voice cloning 

## Pro Tips

### The Art of Choosing a Reference Wav
- A 24000, 44100 or 22050 Hz 16-bit mono wav file of 10-30 seconds is your golden ticket. 
- 24k mono 16 is my default, but I also had voices where I found 44100 32-bit to yield best results
- I test voices [with this tool](https://github.com/KoljaB/RealtimeTTS/blob/master/tests/coqui_test.py) before rendering
- Audacity is your friend for adjusting sample rates. Experiment with frame rates for best results!

### Fixed TTS Model Download Folder
Keep your models organized! Set `COQUI_MODEL_PATH` to your preferred folder.

Windows example:
```bash
setx COQUI_MODEL_PATH "C:\Downloads\CoquiModels"
```

## Future Improvements

- **TTS Voice variety**: Add OpenAI TTS, Azure and Elevenlabs as voice sources.
- **Tranlation quality**: Add option to translate with OpenAI, DeepL API, other models. Better logic than simply transcribe the frags.
- **Voice Cloning from YouTube**: Cloning voices directly from other videos.
- **Speed up to realtiem**: Feed streams and get a "realtime" (translated) stream with voice of choice
- **Open up the CLI**: Allow local Videos, Audios and even Textfiles as Input until down to turnvoice "Hello World"

## License

TurnVoice is proudly under the [Coqui Public Model License 1.0.0](https://coqui.ai/cpml) and [NLLB-200 CC-BY-NC License](https://huggingface.co/facebook/nllb-200-distilled-600M) (these are OpenSource NonCommercial licenses). 

## Let's Make It Fun! 🎉

[Share](https://github.com/KoljaB/TurnVoice/discussions) your funniest or most creative TurnVoice creations with me! 

And if you've got a cool feature idea or just want to say hi, drop me a line on

- [Twitter](https://twitter.com/LonLigrin)  
- [Reddit](https://www.reddit.com/user/Lonligrin)  
- [EMail](mailto:kolja.beigel@web.de)  

If you like the repo please leave a star ✨ 🌟 ✨