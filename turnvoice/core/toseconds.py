import re

def time_to_seconds(time_str):
    """
    Converts a time string in various formats to seconds, now including hours and plain numbers.
    
    Supported formats:
    - 'XhYmZs': X hours, Y minutes and Z seconds (e.g., '1h2m3s')
    - 'XmYs': X minutes and Y seconds (e.g., '3m23s')
    - 'Xs': X seconds (e.g., '34s')
    - 'X:Y:Z': X hours, Y minutes and Z seconds (e.g., '1:02:03')
    - 'X:Y': X minutes and Y seconds (e.g., '3:00')
    - 'X': X seconds (e.g., '45')
    
    Parameters:
    - time_str (str): The time string to convert.
    
    Returns:
    - int: The number of seconds.
    """
    
    # Regex patterns for different time formats
    pattern_hours_minutes_seconds = r'(\d+)h(\d+)m(\d+)s'
    pattern_minutes_seconds = r'(\d+)m(\d+)s'
    pattern_seconds = r'(\d+)s'
    pattern_hours_colon = r'(\d+):(\d+):(\d+)'
    pattern_minutes_colon = r'(\d+):(\d+)'
    pattern_plain_number = r'^\d+$'

    # Match the time string against different patterns
    if re.match(pattern_hours_minutes_seconds, time_str):
        hours, minutes, seconds = map(int, re.findall(pattern_hours_minutes_seconds, time_str)[0])
    elif re.match(pattern_minutes_seconds, time_str):
        hours = 0
        minutes, seconds = map(int, re.findall(pattern_minutes_seconds, time_str)[0])
    elif re.match(pattern_seconds, time_str):
        hours = minutes = 0
        seconds = int(re.findall(pattern_seconds, time_str)[0])
    elif re.match(pattern_hours_colon, time_str):
        hours, minutes, seconds = map(int, re.findall(pattern_hours_colon, time_str)[0])
    elif re.match(pattern_minutes_colon, time_str):
        hours = 0
        minutes, seconds = map(int, re.findall(pattern_minutes_colon, time_str)[0])
    elif re.match(pattern_plain_number, time_str):
        hours = minutes = 0
        seconds = int(time_str)
    else:
        raise ValueError("Unsupported time format")

    return hours * 3600 + minutes * 60 + seconds