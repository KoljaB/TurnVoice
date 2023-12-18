
def render_video(
        sentence_fragments,
        synthesis_language,
        p_synthesis_directory,
        p_clean_audio,
        audio_file,
        accompaniment_path,
        video_file_muted,
        p_output_video,
        t_start,
        synthesis
        ):

    synthesis.set_language(synthesis_language)
    sentence_fragments = sorted(sentence_fragments, key=lambda s: s["start"])
    print(f"Sorted sentence fragments:\n{sentence_fragments}")
    
    word_timestamp_correction = 0.1
    crossfade_duration = 0.7

    from moviepy.editor import AudioFileClip
    with AudioFileClip(audio_file) as audio_clip:
        duration = audio_clip.duration

    # Perform synthesis of each sentence fragment
    # while respecting the original speaking duration.
    # and save the synthesized audio to disk.
    import time
    print(f"[{(time.time() - t_start):.1f}s] "
          "synthesizing audio..."
          )
    synthesis.synthesize_sentences(
        sentence_fragments,
        p_synthesis_directory,
        t_start
        )

    # Filter sentences with a successful synthesis
    # based on synthesis_result
    successful_synthesis_sentences = [
        sentence for sentence in sentence_fragments
        if sentence["synthesis_result"]
    ]

    sentence_fragments = successful_synthesis_sentences
    if len(sentence_fragments) == 0:

        print(f"[{(time.time() - t_start):.1f}s] "
              "no successful synthesis (no sentences created), aborting..."
              )
        synthesis.close()
        return

    # Combine all synthesized audio fragments into one audio file
    final_cut_audio_path = "final_cut_audio.wav"
    print(f"[{(time.time() - t_start):.1f}s] "
          "combining audio..."
          )

    from .cut import create_composite_audio
    create_composite_audio(
        sentence_fragments,
        p_synthesis_directory,
        duration,
        final_cut_audio_path
    )

    # Render the combined audio and the muted video into one video file
    if not p_clean_audio:
        #
        # Preparation of the background audiotrack.
        # We use the original audio when nothing was changed but
        # use the vocal-less audio as soon as we replaced a voice.
        # With timestamps we aim at preserving as much
        # of the original audio as possible.
        # - add little time correction to the timestamps
        #   (due to word timestamp detection errors)
        # - merge the original audio with the vocal-less audio
        #
        time_stamps = []
        max_distance = 2 * word_timestamp_correction + 2 * crossfade_duration

        # Initial timestamp adjustment
        for sentence in sentence_fragments:
            start = max(0, sentence["start"] - word_timestamp_correction)
            end = min(sentence["end"] + word_timestamp_correction, duration)
            time_stamps.append((start, end))

        merged_time_stamps = []
        for start, end in time_stamps:
            if not merged_time_stamps:
                merged_time_stamps.append((start, end))
            else:
                start_prev, end_prev = merged_time_stamps[-1]
                distance = start - end_prev
                if start < end_prev or distance < max_distance:
                    # Extend the end time of the
                    # previous segment if there is overlap
                    merged_time_stamps[-1] = (start_prev, max(end_prev, end))
                else:
                    # No overlap, add the segment as is
                    merged_time_stamps.append((start, end))

        time_stamps = merged_time_stamps

        #
        # Final merge cut of the background audio track
        #
        final_cut_audio_merged = "final_cut_audio_merged.wav"
        print(f"[{(time.time() - t_start):.1f}s] merging "
              f"original {audio_file} and vocal less audios "
              f"{accompaniment_path} into {final_cut_audio_merged}..."
              )

        from .cut import merge_audios
        merge_audios(audio_file,
                     accompaniment_path,
                     time_stamps,
                     final_cut_audio_merged,
                     crossfade_duration=crossfade_duration
                     )

        #
        # Finally render three things together:
        # - the synthesized audio track final_cut_audio_path
        # - the background audio track final_cut_audio_merged
        # - the muted video video_file_muted
        #
        print(f"[{(time.time() - t_start):.1f}s] "
              f"combining {video_file_muted} together with audios "
              f"{final_cut_audio_path} and {final_cut_audio_merged} "
              f"into video {p_output_video}..."
              )

        from .cut import merge_video_audio
        total_duration = merge_video_audio(
            video_file_muted,
            final_cut_audio_path,
            final_cut_audio_merged,
            p_output_video
            )
    else:
        #
        # If we shall deliver a clean audio track, we only need to render
        # two things together:
        # - the synthesized audio track final_cut_audio_path
        # - the muted video video_file_muted
        #
        print(f"[{(time.time() - t_start):.1f}s] "
              f"combining audio {final_cut_audio_path} with "
              f"video {video_file_muted} into {p_output_video}..."
              )

        from .cut import overlay_audio_on_video
        total_duration = overlay_audio_on_video(
            final_cut_audio_path,
            video_file_muted,
            p_output_video)

    #
    # Some cleanup and stat presenting and we're done
    #
    synthesis.close()

    print(f"[{(time.time() - t_start):.1f}s] "
          f"video processing complete: [[[ {p_output_video} ]]]"
          )
    if total_duration and total_duration > 0:
        calculation_duration = time.time() - t_start
        realtime_factor = calculation_duration / total_duration

        print(f"[{(time.time() - t_start):.1f}s] "
              f"calculation realtime factor for {total_duration:.1f}s "
              f"video: {realtime_factor:.2f}x"
              )
