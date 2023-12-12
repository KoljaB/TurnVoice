# TurnVoice

A command-line tool to **transform voices** in YouTube videos with additional **translation** capabilities. [^1] 

https://github.com/KoljaB/TurnVoice/assets/7604638/f87759cc-0b3f-4d8f-864f-af99202d7312

<sup>(sorry for the bad video quality, it had to fit under 10MB file size because Github 🤷)</sup> [🎞️ HD version 🎞️](https://www.youtube.com/watch?v=Rl0WhIax2lM) 

## New Features

- use --prompt to apply custom style changes to the detected sentences like "speaking style of captain jack sparrow" [^6] 
- **Elevenlabs**, **OpenAI TTS**, **Azure**, **Coqui TTS** and System voices for redubbing
- replace specific speaker or multiple speaker voices (work in progress)
- process local files
- preserve original background audio  

> *more infos 👉 [release notes](https://github.com/KoljaB/TurnVoice/releases)*

## Prerequisites

- [Rubberband](https://breakfastquay.com/rubberband/) command-line utility installed [^2] 
- [Deezer's Spleeter](https://github.com/deezer/spleeter) command-line utility installed [^3]
> [!TIP]
> *For Deezer's Spleeter CLI install [Python 3.8](https://www.python.org/downloads/), then run `pipx install spleeter --python /path/to/python3.8` (pip install pipx)*  
> <sub>Pro-Tipp: don't be an idiot like me and waste hours trying to run spleeter on a somewhat modern python version, just give it it's precious dinosaur era 3.8 env and move on</sub>
- Huggingface conditions accepted for [Speaker Diarization](https://huggingface.co/pyannote/speaker-diarization-3.1) and [Segmentation](https://huggingface.co/pyannote/segmentation-3.0)
- Huggingface access token in env variable HF_ACCESS_TOKEN [^4]
> [!TIP]
> *Set your [HF token](https://huggingface.co/settings/tokens) with `setx HF_ACCESS_TOKEN "your_token_here"*

## Installation 

```
pip install turnvoice
```

> [!TIP]
> For faster rendering with GPU prepare your [CUDA](https://pytorch.org/get-started/locally/) environment after installation:
> 
> ***For CUDA 11.8***  
> `pip install torch==2.1.1+cu118 torchaudio==2.1.1+cu118 --index-url https://download.pytorch.org/whl/cu118`  
>   
> ***For CUDA 12.1***  
> `pip install torch==2.1.1+cu118 torchaudio==2.1.1+cu211 --index-url https://download.pytorch.org/whl/cu211`  

## Usage

```bash
turnvoice [-i] <YouTube URL|ID|Local Video Path> [-l] <Translation Language> -v <Voice File(s)> -o <Output File>
```

### Example Command:

Arthur Morgan narrating a cooking tutorial:

```bash
turnvoice -i AmC9SmCBUj4 -v arthur.wav -o cooking_with_arthur.mp4
```

> [!NOTE]
> *Requires a voice file (e.g., arthur.wav or .json) in the same directory (you find one in the tests directory).*

### Parameters Explained:

- `-i`, `--in`: Input video. Accepts a YouTube video URL or ID, or a path to a local video file.
- `-l`, `--language`: Language for translation. Coqui synthesis supports: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh, ja, hu, ko. Omit to retain the original video language.
- `-il`, `--input_language`: Language code for transcription, set if automatic detection fails.
- `-v`, `--voice`: Voices for synthesis. Accepts multiple values to replace more than one speaker.
- `-o`, `--output_video`: Filename for the final output video (default: 'final_cut.mp4').
- `-a`, `--analysis`: Print transcription and speaker analysis without synthesizing or rendering the video.
- `-from`: Time to start processing the video from.
- `-to`: Time to stop processing the video at.
- `-e`, `--engine`: Synthesis engine (options: coqui, elevenlabs, azure, openai, system; default: coqui).
- `-s`, `--speaker`: Speaker number to be transformed.
- `-snum`, `--num_speakers`: Exact number of speakers in the video, aids in diarization.
- `-smin`, `--min_speakers`: Minimum number of speakers in the video.
- `-smax`, `--max_speakers`: Maximum number of speakers in the video.
- `-dd`, `--download_directory`: Directory for saving downloaded files (default: 'downloads').
- `-sd`, `--synthesis_directory`: Directory for saving synthesized audio files (default: 'synthesis').
- `-exoff`, `--extractoff`: Disables extraction of audio from the video file. Downloads audio and video from the internet.
- `-c`, `--clean_audio`: Removes original audio from the final video, resulting in clean synthesis.
- `-tf`, `--timefile`: Define timestamp file(s) for processing (functions like multiple --from/--to commands).
- `-p`, `--prompt`: Define a prompt to apply a style change to sentences like "speaking style of captain jack sparrow" [^6]

> [!TIP]
> `-i` and `-l` can be used as both positional and optional arguments.

## Coqui Engine

Coqui engine is the default engine if no other engine is specified with the -e parameter.

<details>
<summary>To use voices from Coqui:</summary>

#### Voices (-v parameter)

Submit path to one or more audiofiles containing 16 bit 24kHz mono source material as reference wavs.

Example:
```
turnvoice https://www.youtube.com/watch?v=cOg4J1PxU0c -e coqui -v female.wav
```

#### The Art of Choosing a Reference Wav
- A 24000, 44100 or 22050 Hz 16-bit mono wav file of 10-30 seconds is your golden ticket. 
- 24k mono 16 is my default, but I also had voices where I found 44100 32-bit to yield best results
- I test voices [with this tool](https://github.com/KoljaB/RealtimeTTS/blob/master/tests/coqui_test.py) before rendering
- Audacity is your friend for adjusting sample rates. Experiment with frame rates for best results!

#### Fixed TTS Model Download Folder
Keep your models organized! Set `COQUI_MODEL_PATH` to your preferred folder.

Windows example:
```bash
setx COQUI_MODEL_PATH "C:\Downloads\CoquiModels"
```
</details>

## Elevenlabs Engine

> [!NOTE]
> To use Elevenlabs voices you need the [API Key](https://elevenlabs.io/docs/api-reference/text-to-speech#authentication) stored in env variable **ELEVENLABS_API_KEY**

All voices are synthesized with the multilingual-v1 model.

> [!CAUTION]
> Elevenlabs is a pricy API. Focus on short videos. Don't let a work-in-progress script like this run unattended on a pay-per-use API. Bugs could be very annoying when occurring at the end of a pricy long rendering process. 

<details>
<summary>To use voices from Elevenlabs:</summary>

#### Voices (-v parameter)

Submit name(s) of either a generated or predefined voice.

Example:
```
turnvoice https://www.youtube.com/watch?v=cOg4J1PxU0c -e elevenlabs -v Giovanni
```

</details>  

> [!TIP]
> Test rendering with a free engine like coqui first before using pricy ones.

## OpenAI Engine

> [!NOTE]
> To use OpenAI TTS voices you need the [API Key](https://platform.openai.com/api-keys) stored in env variable **OPENAI_API_KEY**

<details>
<summary>To use voices from OpenAI:</summary>

#### Voice (-v parameter)

Submit name of voice. Currently only one voice for OpenAI supported. Alloy, echo, fable, onyx, nova or shimmer.

Example:
```
turnvoice https://www.youtube.com/watch?v=cOg4J1PxU0c -e openai -v shimmer
```
</details>

## Azure Engine

> [!NOTE]
> To use Azure voices you need the [API Key](https://www.youtube.com/watch?v=HgYE2nJPaHA&t=57s) for SpeechService resource in **AZURE_SPEECH_KEY** and the [region identifier](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions) in **AZURE_SPEECH_REGION**

<details>
<summary>To use voices from Azure:</summary>

#### Voices (-v parameter)

Submit name(s) of either a generated or predefined voice.

Example:
```
turnvoice https://www.youtube.com/watch?v=BqnAeUoqFAM -e azure -v ChristopherNeural
```
</details>

## System Engine

<details>
<summary>To use system voices:</summary>

#### Voices (-v parameter)

Submit name(s) of voices as string.

Example:
```
turnvoice https://www.youtube.com/watch?v=BqnAeUoqFAM -e system -v David
```
</details>

## What to expect

- early alpha / work-in-progress, so bugs might occur (please report, need to be aware to fix)
- might not always achieve perfect lip synchronization, especially when translating to a different language
- speaker detection does not work that well, probably doing something wrong or or perhaps the tech[^5] is not yet ready to be reliable
- translation feature is currently in experimental prototype state (powered by deep-translate) and still produces very imperfect results
- occasionally, the synthesis might introduce unexpected noises or distortions in the audio (we got **way** better reducing artifacts with the new v0.0.30 algo)
- spleeter might get confused when a spoken voice and backmusic with singing are present together in the source audio

## Source Quality

- delivers best results with YouTube videos featuring **clear spoken** content (podcasts, educational videos)
- requires a high-quality, **clean** source WAV file for effective voice cloning 

## Pro Tips

### How to exchange a single speaker

First perform a speaker analysis with -a parameter:

```bash
turnvoice https://www.youtube.com/watch?v=2N3PsXPdkmM -a
```

Then select a speaker from the list with -s parameter

```bash
turnvoice https://www.youtube.com/watch?v=2N3PsXPdkmM -s 2
```

## Future Improvements

- **Translation quality**: Add option to translate with OpenAI, DeepL API, other models. Better logic than simply transcribe the frags.
- **Voice Cloning from YouTube**: Cloning voices directly from other videos.
- **Speed up to realtime**: Feed streams and get a "realtime" (translated) stream with voice of choice
- **Open up the CLI**: Allow local Videos, Audios and even Textfiles as Input until down to turnvoice "Hello World"
- match spoken volume of original voice

## License

TurnVoice is proudly under the [Coqui Public Model License 1.0.0](https://coqui.ai/cpml). 

## Let's Make It Fun! 🎉

[Share](https://github.com/KoljaB/TurnVoice/discussions) your funniest or most creative TurnVoice creations with me! 

And if you've got a cool feature idea or just want to say hi, drop me a line on

- [Twitter](https://twitter.com/LonLigrin)  
- [Reddit](https://www.reddit.com/user/Lonligrin)  
- [EMail](mailto:kolja.beigel@web.de)  

If you like the repo please leave a star ✨ 🌟 ✨

[^1]: State is work-in-progress (early pre-alpha), so please expect API changes to come and sometimes things not working properly yet. Developed on Python 3.11.4 under Win 10.  
[^2]: Rubberband is needed to pitchpreserve timestretch audios for fitting synthesis into timewindow.
[^3]: Deezer's Spleeter is needed to split vocals for original audio preservation.
[^4]: Huggingface access token is needed to download the speaker diarization model for identifying speakers with pyannote.audio.
[^5]: Speaker diarization is performed with the pyannote.audio default HF implementation on the vocals track splitted from the original audio.
[^6]: Uses GPT-4 and generates costs. Needs [OpenAI API Key](https://platform.openai.com/api-keys) stored in env variable **OPENAI_API_KEY**.