def get_video_duration(data):
  # Extract duration
    duration = float(data['format']['duration'])

    # Extract framerate from first video stream
    for stream in data['streams']:
        if stream['codec_type'] == 'video':
            fps_fraction = stream['avg_frame_rate']
            num, den = map(int, fps_fraction.split('/'))
            fps = num / den
            break
            
    return duration, fps  