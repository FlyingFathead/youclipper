# yousubtitler.py
# yousubtitler v0.08

import os
import sys
import logging
import platform
import subprocess
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import whisper
from moviepy.config import change_settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_imagemagick():
    try:
        subprocess.run(["magick", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("ImageMagick is installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("ImageMagick is not installed or not found in PATH.")
        print("\nImageMagick is required but not found.")
        if platform.system() == "Windows":
            print("Please install it from: https://imagemagick.org/script/download.php")
            print("Make sure to add ImageMagick to your system PATH during installation.")
            print("Note: if you have Chocolatey installed on Windows, you can also install ImageMagick with: choco install imagemagick")
        elif platform.system() == "Linux":
            print("You can install ImageMagick using your package manager.")
            print("For example, on Ubuntu or Debian: sudo apt update && sudo apt install imagemagick")
            print("(You can also download the latest ImageMagick version from: https://imagemagick.org/script/download.php)")
        elif platform.system() == "Darwin":  # macOS
            print("You can install ImageMagick using Homebrew.")
            print("Install Homebrew from https://brew.sh/ if you haven't already, then run: brew install imagemagick")
            print("(You can also download the latest ImageMagick version from: https://imagemagick.org/script/download.php)")            
        sys.exit(1)

def configure_imagemagick():
    if platform.system() == "Windows":
        logging.info("Configuring ImageMagick for Windows.")
        check_imagemagick()
        change_settings({"IMAGEMAGICK_BINARY": "magick"})
    else:
        logging.info("Configuring ImageMagick for Linux/macOS.")
        check_imagemagick()
        change_settings({"IMAGEMAGICK_BINARY": "convert"})  # Typical binary name for ImageMagick on Unix-like systems

def transcribe_video(video_path):
    logging.info("Loading Whisper model...")
    model = whisper.load_model("medium.en")
    logging.info(f"Transcribing video: {video_path}")
    result = model.transcribe(video_path)
    logging.info("Transcription completed.")
    return result["segments"]

def create_highlighted_text(text, start_time, duration, font_size=40, highlight_color='yellow', text_color='black'):
    txt_clip = TextClip(text, fontsize=font_size, color=text_color, font='Arial-Bold', bg_color=highlight_color)
    txt_clip = txt_clip.set_start(start_time).set_duration(duration).set_pos(('center', 'bottom'))
    txt_clip = txt_clip.crossfadein(0.5).crossfadeout(0.5)
    return txt_clip

# def create_highlighted_text(text, start_time, duration, font_size=40, highlight_color='yellow', text_color='black'):
#     txt_clip = TextClip(text, fontsize=font_size, color=text_color, font='Arial-Bold')
#     txt_clip = txt_clip.on_color(size=(txt_clip.w + 20, txt_clip.h + 20), color=highlight_color, pos=(10, 10))
#     txt_clip = txt_clip.set_start(start_time).set_duration(duration).set_pos(('center', 'bottom'))
#     txt_clip = txt_clip.crossfadein(0.5).crossfadeout(0.5)
#     return txt_clip

def create_subtitled_video(input_file, segments):
    logging.info(f"Loading video file: {input_file}")
    video = VideoFileClip(input_file)
    subtitles = []
    
    for segment in segments:
        text = segment["text"]
        start_time = segment["start"]
        end_time = segment["end"]
        duration = end_time - start_time
        logging.info(f"Creating subtitle for text: '{text}' from {start_time} to {end_time}")
        subtitle_clip = create_highlighted_text(text, start_time, duration)
        subtitles.append(subtitle_clip)
    
    logging.info("Combining video and subtitles...")
    result = CompositeVideoClip([video, *subtitles])
    output_file = f"{os.path.splitext(input_file)[0]}_subtitled.mp4"
    logging.info(f"Writing subtitled video to: {output_file}")
    result.write_videofile(output_file, fps=video.fps)
    logging.info("Subtitled video created successfully.")

def main():
    if len(sys.argv) != 2:
        print("Usage: python yousubtitler.py <input_video_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    configure_imagemagick()
    
    logging.info("Starting transcription and subtitling process...")
    segments = transcribe_video(input_file)
    
    logging.info("Starting video creation with subtitles...")
    create_subtitled_video(input_file, segments)
    
    logging.info("Process completed successfully.")

if __name__ == "__main__":
    main()
