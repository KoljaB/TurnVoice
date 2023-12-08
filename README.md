# TurnVoice

A command-line tool in beta state to **transform voices** in YouTube videos with additional **translation** capabilities.  

## What to expect

This is hypefree zone and while I think it is possible to do some amazing stuff with this tool expectations should be kept realistic. So first here is what it can not do: It replaces the entire audio track of the video with a newly generated voice. As a result, all original sounds, including music and ambient noises, are **replaced by silence**, leaving only the new voice track. This approach ensures **clarity** in the newly generated voice but means that other audio elements from the original video will be absent in the output.  

- might not always achieve perfect lip synchronization, especially when translating to a different language
- translation feature is currently in very alpha state (powered by Meta's nllb-200-distilled-600m) and still produces very imperfect results
- occasionally, the synthesis might introduce unexpected noises or distortions in the audio (we got WAY better reducing artifacts with the new v0.0.30 algo)

## Source Quality

- delivers best results with YouTube videos featuring **clear spoken** content (podcasts, educational videos)
- requires a high-quality, **clean** source WAV file for effective voice cloning 

## Prerequisites

You need to have [Rubberband](https://breakfastquay.com/rubberband/) command-line utility installed (needed for pitchpreserve timestretching audios)

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

## Usage

```bash
turnvoice [-u] <YouTube Video URL|ID> [-l] <Translation Language> -r <Reference WAV File> -o <Output Video Filename>
```

For example, this is musk with female (default) voice:
```bash
turnvoice RK91Ji6GCZ8
```

Same translated to spanish:
```bash
turnvoice RK91Ji6GCZ8 es
```

### Parameters Explained:

- `-u`, `--url`: (required) The YouTube video ID or URL you want to transform
- `-l`, `--language`: Language to translate to (supported: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh, ja, hu, ko)
   *leaving this out keeps the source video language*
- `-d`, `--download_directory`: Where to save the video downloads (default: 'downloads')
- `-s`, `--synthesis_directory`: Where to save the text to speech audio files (default: 'synthesis')
- `-e`, `--extractoff`: Use with -e to disable extract audio directly from the video (may lead to higher quality while also increasing likelihood of errors)
- `-r`, `--reference_wav`: Your chosen voice in wav format (24kHz, 16 bit, mono, ~10-30s)
- `-o`, `--output_video`: The grand finale video file name (default: 'final_cut.mp4')

You can leave out -u and -l as first parameters.

### Example Command:

Ever wanted Arthur Morgan to narrate a cooking tutorial? Here's how:

turnvoice AmC9SmCBUj4 -r arthur.wav -o cooking_with_arthur.mp4


*This example needs a arthur.wav (or.json) file in the same directory. Works when executed from the tests directory.*

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

- **Diarization**: Replace voices of multiple speakers.
- **TTS Voice variety**: Add OpenAI TTS, Azure and Elevenlabs as voice sources.
- **Tranlation quality**: Add option to translate with OpenAI, DeepL API, other models. 
- **Optimized Synthesis**: Reducing the synthesis tries for faster results.
- **Voice Cloning from YouTube**: Cloning voices directly from other videos!
- **Speed that thing up**: Imagine feeding a youtube stream and getting a "realtime" translation stream (with strong GPU we can aim at ~10-20s latency)

## License

TurnVoice is proudly under the [Coqui Public Model License 1.0.0](https://coqui.ai/cpml) and [NLLB-200 CC-BY-NC License](https://huggingface.co/facebook/nllb-200-distilled-600M) (these are OpenSource NonCommercial licenses). 

## Let's Make It Fun! 🎉

[Share](https://github.com/KoljaB/TurnVoice/discussions) your funniest or most creative TurnVoice creations with me! 

And if you've got a cool feature idea or just want to say hi, drop me a line on

- [Twitter](https://twitter.com/LonLigrin)  
- [Reddit](https://www.reddit.com/user/Lonligrin)  
- [EMail](mailto:kolja.beigel@web.de)  

Don't forget to leave a star.