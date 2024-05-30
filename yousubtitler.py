# yousubtitler.py
# yousubtitler v0.09

import os
import sys
import logging
import platform
import subprocess
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings

# Configuration flags
USE_WHISPERX = True  # Set to False to use OpenAI's Whisper

if USE_WHISPERX:
    import whisperx
else:
    import whisper

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

def transcribe_video_whisperx(video_path):
    logging.info("Loading WhisperX model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisperx.load_model("large-v2", device)
    audio = whisperx.load_audio(video_path)
    result = model.transcribe(audio)
    
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device)
    
    return result["segments"]

def transcribe_video_whisper(video_path):
    logging.info("Loading Whisper model...")
    model = whisper.load_model("medium.en")
    result = model.transcribe(video_path)
    return result["segments"]

def create_highlighted_text(text, start_time, duration, video_width, font_size=40, highlight_color='yellow', text_color='black'):
    words = text.split()
    text_clips = []
    word_start_time = start_time
    
    for word in words:
        txt_clip = TextClip(word, fontsize=font_size, color=text_color, font='Arial-Bold', bg_color=highlight_color, size=(video_width, None), method='caption')
        txt_clip = txt_clip.set_start(word_start_time).set_duration(duration / len(words))
        txt_clip = txt_clip.set_pos(('center', 'bottom'))
        
        text_clips.append(txt_clip)
        word_start_time += duration / len(words)
    
    return text_clips

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
        subtitle_clips = create_highlighted_text(text, start_time, duration, video.size[0])
        subtitles.extend(subtitle_clips)
    
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
    if USE_WHISPERX:
        segments = transcribe_video_whisperx(input_file)
    else:
        segments = transcribe_video_whisper(input_file)
    
    logging.info("Starting video creation with subtitles...")
    create_subtitled_video(input_file, segments)
    
    logging.info("Process completed successfully.")

if __name__ == "__main__":
    main()