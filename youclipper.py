# youclipper v0.07
# https://github.com/FlyingFathead/youclipper/
# FlyingFathead 2024 ~*~ w/ ghostcode by ChaosWhisperer

import argparse
import subprocess
import os
import glob
import re

def fetch_video_duration(url):
    result = subprocess.run(['yt-dlp', '--get-duration', url], stdout=subprocess.PIPE, text=True)
    duration_str = result.stdout.strip()
    return parse_time(duration_str)

def parse_time(time_str):
    # Validates and converts a time string into milliseconds.
    parts = time_str.split(':')
    if '.' in parts[-1]:
        seconds, milliseconds = parts[-1].split('.')
        parts[-1] = seconds
        milliseconds = int(milliseconds.ljust(3, '0'))
    else:
        milliseconds = 0

    parts = [int(part) for part in parts]
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    else:
        raise ValueError("Invalid time format: " + time_str)

    total_milliseconds = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds
    return total_milliseconds

def download_video(url, start_ms, end_ms, output):
    temp_file = 'temp_video'
    subprocess.call(['yt-dlp', url, '-o', f'{temp_file}.%(ext)s'])
    
    downloaded_files = glob.glob(f'{temp_file}.*')
    if not downloaded_files:
        raise Exception("No files downloaded.")
    downloaded_file = downloaded_files[0]
    
    ffmpeg_command = [
        'ffmpeg', '-i', downloaded_file, '-ss', str(start_ms / 1000), '-to', str(end_ms / 1000),
        '-c:v', 'libx264', '-c:a', 'aac', output
    ]
    subprocess.call(ffmpeg_command)

    os.remove(downloaded_file)

# (old method, copies without re-encoding, better quality but usually causes video/audio desync issues)
# def download_video(url, start_ms, end_ms, output):
#     temp_file = 'temp_video'
#     subprocess.call(['yt-dlp', url, '-o', f'{temp_file}.%(ext)s'])
    
#     downloaded_files = glob.glob(f'{temp_file}.*')
#     if not downloaded_files:
#         raise Exception("No files downloaded.")
#     downloaded_file = downloaded_files[0]
    
#     ffmpeg_command = [
#         'ffmpeg', '-i', downloaded_file, '-ss', str(start_ms / 1000), '-to', str(end_ms / 1000),
#         '-c', 'copy', output
#     ]
#     subprocess.call(ffmpeg_command)

#     os.remove(downloaded_file)

def main():
    parser = argparse.ArgumentParser(description='YouClipper: Download and clip YouTube videos easily.')
    parser.add_argument('--url', type=str, help='The URL of the YouTube video you want to download and clip.')
    parser.add_argument('--start', type=str, help='The start time of the clip in hh:mm:ss[.xxx] or mm:ss[.xxx] format.')
    parser.add_argument('--end', '--stop', type=str, dest='end', help='The end time of the clip in hh:mm:ss[.xxx] or mm:ss[.xxx] format.')
    parser.add_argument('--output', '--out', type=str, dest='output', help='The desired output filename without extension. Defaults to "output_clip" if not specified.')
    args = parser.parse_args()

    if not args.url:
        args.url = input('Enter video URL: ')
    if not args.start:
        args.start = input('Enter start time (hh:mm:ss[.xxx] or mm:ss[.xxx]): ')
    if not args.end:  # This line ensures that end time is always asked for user input if it's not provided via command-line arguments.
        args.end = input('Enter end time (hh:mm:ss[.xxx] or mm:ss[.xxx]): ')
    if not args.output:
        args.output = input('Enter output filename without extension (default: output_clip): ').strip()
        if not args.output:
            args.output = 'output_clip'
    if not args.output.endswith('.mp4'):
        args.output += '.mp4'

    try:
        start_ms = parse_time(args.start)
        end_ms = parse_time(args.end)
        duration_ms = fetch_video_duration(args.url)
        
        if start_ms >= end_ms or end_ms > duration_ms:
            raise ValueError("Invalid start or end time.")

        download_video(args.url, start_ms, end_ms, args.output)
        print(f'Video clipped successfully: {args.output}')
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
