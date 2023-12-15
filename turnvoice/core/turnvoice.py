def main():
    print("Welcome to TurnVoice!")

    import argparse
    parser = argparse.ArgumentParser(
        description="Replaces voices in Youtube videos. Can translate."
    )

    parser.add_argument(
        'inputvideo', nargs='?', type=str,
        help='Input video. URL or ID of a YouTube video or '
             'path to a local video. (Positional)'
    )
    parser.add_argument(
        '-i', '--in', dest='source', type=str,
        help='Input video. URL or ID of a YouTube video or '
             'path to a local video. (Optional)'
    )
    parser.add_argument(
        'language', nargs='?', type=str, default='',
        help='Language code for translation. (Positional)'
    )
    parser.add_argument(
        '-l', '--language', dest='language_optional', type=str,
        help='Language code for translation. (Optional)'
    )
    parser.add_argument(
        '-il', '--input_language', type=str, default='',
        help='Language code for transcription. Can be set in case '
             'automatical detection goes wrong. (Optional)'
    )
    parser.add_argument(
        '-v', '--voice', nargs='+',
        help='Reference voice(s) for synthesis. Accepts multiple values '
             'to replace more than one speaker. (Optional)'
    )
    parser.add_argument(
        '-o', '--output_video', '-out', type=str, default='final_cut.mp4',
        help='Filename for the final cut output video. (Optional)'
    )
    parser.add_argument(
        '-a', '--analysis', action='store_true',
        help='Prints transcription and speaker analysis, then aborts '
             'without synthesizing and rendering. (Optional)'
    )
    parser.add_argument(
        '-from', '--from', dest='_from', type=str,
        help='Time to start processing the video from. (Optional)'
    )
    parser.add_argument(
        '-to', '--to', type=str,
        help='Time to stop processing the video at. (Optional)'
    )
    parser.add_argument(
        '-e', '--engine', nargs='+', default=['coqui'],
        help='Engine(s) to synthesize with. Can be coqui, elevenlabs, azure, '
             'openai or system. Accepts multiple values, linked to the '
             'the submitted voices. (Optional, uses coqui as default)'
    )
    parser.add_argument(
        '-s', '--speaker', type=str, default='',
        help='Speaker number to be turned. (Optional)'
    )
    parser.add_argument(
        '-snum', '--num_speakers', type=int, default='0',
        help='Helps diarization. Specify the exact number of speakers in '
             'the video if you know it in advance. (Optional)'
    )
    parser.add_argument(
        '-smin', '--min_speakers', type=int, default='0',
        help='Helps diarization. Specify the minimum number of speakers in '
             'the video if you know it in advance. (Optional)'
    )
    parser.add_argument(
        '-smax', '--max_speakers', type=int, default='0',
        help='Helps diarization. Specify the maximum number of speakers in '
             'the video if you know it in advance. (Optional)'
    )
    parser.add_argument(
        '-dd', '--download_directory', type=str, default='downloads',
        help='Directory to save downloaded files. (Optional)'
    )
    parser.add_argument(
        '-sd', '--synthesis_directory', type=str, default='synthesis',
        help='Directory to save synthesized audio files. (Optional)'
    )
    parser.add_argument(
        '-exoff', '--extractoff', action='store_true',
        help='Disables extraction of audio from the video file. Downloads '
             'audio and video files from the internet. (Optional)'
    )
    parser.add_argument(
        '-c', '--clean_audio', action='store_true',
        help='No preserve of original audio in the final video. '
             'Returns clean synthesis. (Optional)'
    )
    parser.add_argument(
        '-tf', '--timefile', nargs='?',
        help='Define timestamp file(s) for processing '
             '(basically performs multiple --from/--to) (Optional)'
    )
    parser.add_argument(
        '-p', '--prompt', type=str,
        help='Style change prompt for sentences. For example, '
             '"speaking style of captain jack sparrow". (Optional)'
    )
    parser.add_argument(
        '-prep', '--prepare', action='store_true',
        help='Generates full script with speaker analysis, sentence prompt '
             'transformation and translation. Can be continued. (Optional)'
    )
    parser.add_argument(
        '-r', '--render', type=str,
        help='Renders a prepared full script. (Optional)'
    )
    parser.add_argument(
        '-dbg', '--debug', action='store_true',
        help='Prints extended debugging output. (Optional)'
    )

    args = parser.parse_args()

    input_video = args.source if args.source is not None else args.inputvideo

    language = (
        args.language_optional
        if args.language_optional is not None
        else args.language
    )

    # Call the main processing function
    from .render import prepare_and_start_rendering
    prepare_and_start_rendering(
        p_input_video=input_video,
        p_target_language=language,
        p_source_language=args.input_language,
        p_download_directory=args.download_directory,
        p_synthesis_directory=args.synthesis_directory,
        p_extract_disabled=args.extractoff,
        p_voices=args.voice,
        p_engines=args.engine,
        p_output_video=args.output_video,
        p_clean_audio=args.clean_audio,
        p_limit_start_time=args._from,
        p_limit_end_time=args.to,
        p_analysis=args.analysis,
        p_speaker_number=args.speaker,
        p_num_speakers=args.num_speakers,
        p_min_speakers=args.min_speakers,
        p_max_speakers=args.max_speakers,
        p_time_files=args.timefile,
        p_prompt=args.prompt,
        p_debug=args.debug,
        p_prepare=args.prepare,
        p_render=args.render
    )


if __name__ == "__main__":
    main()
