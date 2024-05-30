# youclipper

`youclipper` is a Python-based command-line tool that leverages `yt-dlp` and `ffmpeg` to download and clip sections from online videos, such as those available on YouTube. It allows you to specify the exact start and end times, even down to milliseconds, to get the precise clip you need.

## Features

- Download videos from YouTube and other platforms supported by `yt-dlp`.
- Clip videos to your specified start and end times with support for millisecond precision.
- Output your clip directly to a specified filename.

## Installation

Before you use `youclipper`, ensure you have the following dependencies installed:

- Python 3
- `yt-dlp`
- `ffmpeg`

You can install `yt-dlp` and `ffmpeg` using your operating system's package manager or download them directly from their official websites.

## Usage

To view all available commands and their descriptions, you can use the `--help` flag:

```bash
python youclipper.py --help
```

### Basic Clipping

To clip a video without specifying milliseconds:

```bash
python youclipper.py --url <video-url> --start mm:ss --end mm:ss --output <output-filename>
```

### Clipping with Millisecond Precision

To clip a video and specify times down to the millisecond:

```bash
python youclipper.py --url <video-url> --start mm:ss.xxx --end mm:ss.xxx --output <output-filename>
```

Note: Replace <video-url> with the actual URL of the video you wish to clip, mm:ss with the start and end times in minutes and seconds, xxx with milliseconds, and <output-filename> with the desired name of your output file (without adding the .mp4 extension, as it is appended automatically).

## Changelog
- v0.07 - recode instead of copying when clipping to avoid video/audio desync issues
- v0.06 - first public release

## Contributing

Contributions to youclipper are welcome! If you have suggestions for improvements or encounter any issues, please open an issue or submit a pull request.

## About

Developed by FlyingFathead, with ghostcode by ChaosWhisperer.

[FlyingFathead on GitHub](https://github.com/FlyingFathead/)

[youclipper on GitHub](https://github.com/FlyingFathead/youclipper)
