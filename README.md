# TurnVoice

*A YouTube Video Voice Replacement Tool*  

This tool provides a convenient way to download YouTube videos, transcribe their audio, and replace the original voice with another one.  

## Features

- **YouTube Video Download:** Downloads a specific YouTube video.
- **Audio Transcription:** Transcribes the audio of the downloaded video.
- **Voice Synthesis:** Replaces the original voice in the video with a synthetic voice.

## Installation

This should make you ready:

```
pip install turnvoice
```

If you like it faster, get your [CUDA](https://pytorch.org/get-started/locally/) ready:  

For CUDA 11.8:
```
pip install torch==2.1.1+cu118 torchaudio==2.1.1+cu118 --index-url https://download.pytorch.org/whl/cu118
```

For CUDA v12.1:
```
pip install torch==2.1.1+cu118 torchaudio==2.1.1+cu211 --index-url https://download.pytorch.org/whl/cu211
```

## Usage

This tool is executed via the command line. Below are the parameters that can be configured:

- `-u`, `--url` (required): URL of the YouTube video to process.
- `-l`, `--language`: Language code for assumed transcription (default: 'en') language and synthesis language.
- `-dd`, `--download_directory`: Directory for saving downloaded files (default: 'downloads').
- `-sd`, `--synthesis_directory`: Directory for saving synthesized audio files (default: 'synthesis').
- `-e`, `--extract`: Flag to extract audio from the video file. Set to false downloads audio seperately, can lead to better quality but also increase likelihood of errors.
- `-rw`, `--reference_wav`: Reference audio file for voice synthesis. Can be wav or calculated json file.
- `-ov`, `--output_video`: Filename for the output video with synthetic voice (default: 'final_cut.mp4').

## Example Command

```bash
turnvoice -u https://www.youtube.com/watch?v=JfV6UcF18ts -rw arthur_morgan.wav -ov rdr2.mp4
```

Exchanges all voices in the given youtube vid with the voice in "arthur_morgan.wav" and writes the final cut into rdr2.mp4

## Hints

### Fixed TTS model download folder

Create a fixed folder (for example C:\Downloads\CoquiModels) for your coqui xtts model downloads and set the environment variable COQUI_MODEL_PATH to this folder.

Windows (example folder):
```
setx COQUI_MODEL_PATH "C:\Downloads\CoquiModels"
```

### Reference Wav

I recommend using a 24000 Hz, 16 bit, mono wav file of 10-30 second length. According to the config.json of the synthesis model it should be 22050Hz but it works better with 24000 in my experience. You can use Audacity to drop any input audio, set the sample rate at the down left bottom to 24000 and then export as 16 bit PCM. 

## Future Improvements

- Optional Translation: 
  coming soon
- Optimized synthesis. 
  Currently does too many synthesis tries per sentence fragment. Can be done better.
- Grab clone voice from another youtube video.

## License

The project is under [Coqui Public Model License 1.0.0](https://coqui.ai/cpml).

Make sure to comply with both YouTube's terms of service and copyright laws as well as Coqui's [Public Model License 1.0.0](https://coqui.ai/cpml) when using this tool.