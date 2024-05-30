# yousubtitler.py
# yousubtitler v0.11
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# https://github.com/FlyingFathead/youclipper/
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import os
import sys
import logging
import platform
import subprocess
import keyboard

import torch
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings

# Configuration flags
USE_WHISPERX = False  # Set to False to use OpenAI's Whisper
WORD_TIMESTAMPS = True  # Set to True to include word-level timestamps
CONFIRM_SUBTITLES = True  # Set to True to confirm subtitles with the user
TEXT_POSITION = 'middle'  # Vertical positioning. Options: 'top', 'middle', 'bottom'

# Font options
FONT_SIZE = 40
HIGHLIGHT_COLOR = 'yellow'
TEXT_COLOR = 'black'
# FONT = 'Arial-Bold'
FONT = 'Comic-Sans-MS'

# Choose between `openai-whisper` and `whisperx`
if USE_WHISPERX:
    import whisperx
else:
    import whisper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_cuda():
    if torch.cuda.is_available():
        logging.info("CUDA is available. Using GPU.")
        return "cuda"
    else:
        logging.info("CUDA is not available. Using CPU.")
        return "cpu"
    
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
    device = check_cuda()
    model = whisperx.load_model("large-v2", device)
    audio = whisperx.load_audio(video_path)
    result = model.transcribe(audio)
    
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device)
    
    return result["segments"]

def transcribe_video_whisper(video_path):
    logging.info("Loading Whisper model...")
    model = whisper.load_model("medium.en")
    result = model.transcribe(video_path, word_timestamps=True)
    return result["segments"]

def confirm_subtitles(segments):
    confirmed_segments = []
    for segment in segments:
        old_text = segment["text"]
        print(f"\nCurrent subtitle: '{old_text}'")
        new_text = input("Enter new subtitle (or press Enter to keep current): ")
        if new_text.strip():
            while True:
                print(f"\nOld subtitle: '{old_text}'")
                print(f"New subtitle: '{new_text}'")
                print("Use the new subtitle? [Y/n] ", end='', flush=True)
                
                while True:
                    if keyboard.is_pressed('y') or keyboard.is_pressed('enter'):
                        confirm = 'y'
                        print('Y')
                        break
                    elif keyboard.is_pressed('n'):
                        confirm = 'n'
                        print('N')
                        break
                
                if confirm == 'y':
                    segment["text"] = new_text
                    print(f"Using the new subtitle: '{new_text}'")
                    confirmed_segments.append(segment)
                    break
                elif confirm == 'n':
                    new_text = input("Enter new subtitle (or press Enter to keep current): ").strip()
        else:
            confirmed_segments.append(segment)
    return confirmed_segments

def check_and_confirm_overwrite(output_file):
    if os.path.exists(output_file):
        print(f"Warning: The output file '{output_file}' already exists.")
        print("Do you want to overwrite it? [Y/n] ", end='', flush=True)
        
        while True:
            if keyboard.is_pressed('y') or keyboard.is_pressed('enter'):
                print('Y')
                return True
            elif keyboard.is_pressed('n'):
                print('N')
                return False

def create_highlighted_text(text, start_time, duration, video_width, font_size=FONT_SIZE, highlight_color=HIGHLIGHT_COLOR, text_color=TEXT_COLOR, text_position=TEXT_POSITION):
    words = text.split()
    text_clips = []
    word_start_time = start_time

    if text_position == 'top':
        position = ('center', 'top')
    elif text_position == 'middle':
        position = ('center', 'center')
    else:
        position = ('center', 'bottom')
    
    for word in words:
        txt_clip = TextClip(word, fontsize=font_size, color=text_color, font=FONT, stroke_color=highlight_color, stroke_width=3, size=(video_width, None), method='caption')
        txt_clip = txt_clip.set_start(word_start_time).set_duration(duration / len(words))
        txt_clip = txt_clip.set_pos(position)
        
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
    
    if not check_and_confirm_overwrite(output_file):
        logging.info("Operation canceled by the user.")
        return
    
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
    
    device = check_cuda()  # Check for CUDA and log the result

    logging.info("Starting transcription and subtitling process...")
    if USE_WHISPERX:
        segments = transcribe_video_whisperx(input_file)
    else:
        segments = transcribe_video_whisper(input_file)
    
    if CONFIRM_SUBTITLES:
        segments = confirm_subtitles(segments)
    
    logging.info("Starting video creation with subtitles...")
    create_subtitled_video(input_file, segments)
    
    logging.info("Process completed successfully.")

if __name__ == "__main__":
    main()