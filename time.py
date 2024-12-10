import sys
import os
import time
from datetime import datetime
import subprocess
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd2in13_V3
import yaml
import argparse

def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)
      
def update_config(key, value):
    config = load_config()
    keys = key.split(".")
    target = config
    for k in keys[:-1]:
        target = target[k]
    target[keys[-1]] = value

    # Write updated config back to the file
    with open("config.yaml", "w") as file:
        yaml.dump(config, file, default_flow_style=False)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Display time on e-ink display with customization options.")
    parser.add_argument("--time_format", type=str, choices=["12", "24"], help="Time format: '12' for 12-hour or '24' for 24-hour format.")
    parser.add_argument("--show_seconds", type=str, choices=["true", "false"], help="Include seconds in the time display.")
    parser.add_argument("--text_style", type=int, choices=range(1, 8), help="Text style: Choose a style from 1 to 7.")
    parser.add_argument("--text_height", type=int, help="Text height in pixels.")
    parser.add_argument("--dark_mode", type=str, choices=["true", "false"], help="Enable or disable dark mode.")
    parser.add_argument("--screen_rotate", type=str, choices=["true", "false"], help="Rotate screen 180 degrees if true; otherwise, no rotation.")
    return parser.parse_args()

# Load configuration and parse arguments
config = load_config()
args = parse_arguments()

# Apply arguments or fallback to configuration
time_format = args.time_format or config["Time Settings"].get("time_format", "12h").lower()
show_seconds = (args.show_seconds.lower() == "true" if args.show_seconds else config["Time Settings"].get("show_seconds", False))
text_style = args.text_style or config["Time Settings"]["text_style"]
text_height = args.text_height or config["Time Settings"]["text_height"]
dark_mode = (args.dark_mode.lower() == "true" if args.dark_mode else config["Time Settings"].get("dark_mode", False))
screen_rotate = (180 if (args.screen_rotate and args.screen_rotate.lower() == "true") else 0)

bg_color = 0 if dark_mode else 255
text_color = 255 if dark_mode else 0

# Initialize the e-ink display
epd = epd2in13_V3.EPD()
epd.init()
epd.Clear(bg_color)

# Define width, height, and drawing canvas
width = epd.height
height = epd.width
image = Image.new('1', (width, height), bg_color)  # 255: White background
draw = ImageDraw.Draw(image)

font_paths = {
    1: 'static/Fonts/Font.ttc',
    2: 'static/Fonts/DejaVuSansMono.ttf',
    3: 'static/Fonts/FrederickatheGreat-Regular.ttf',
    4: 'static/Fonts/RubikDoodleShadow-Regular.ttf',
    5: 'static/Fonts/GravitasOne-Regular.ttf',
    6: 'static/Fonts/SpecialElite-Regular.ttf',
    7: 'static/Fonts/Gluten-Light.ttf'
}

def get_font(text_style, text_height):
    font_path = font_paths.get(text_style, font_paths[1])
    return ImageFont.truetype(font_path, text_height)

selected_font = get_font(text_style, text_height)

def wrap_text(text, font, max_width):
    wrapped_lines = []
    words = text.split()
    current_line = ""

    for i, word in enumerate(words):
        # If "A:" or "--" is found, force it onto a new line
        if word == "A:" or word == "--":
            if current_line.strip():  # Add the current line if not empty
                wrapped_lines.append(current_line.strip())
            current_line = f"{word} "  # Start a new line with "A:" or "--"
            continue

        test_line = f"{current_line}{word} "
        text_width, _ = draw.textsize(test_line, font=font)

        # Check if the test line fits within the screen width
        if text_width <= max_width:
            current_line = test_line  # Add the word to the current line
        else:
            wrapped_lines.append(current_line.strip())  # Add the current line
            current_line = f"{word} "  # Start a new line with the current word

    if current_line.strip():
        wrapped_lines.append(current_line.strip())

    return wrapped_lines[:6] 

def get_current_time():
    if time_format == "12":
        # Format the time based on the "show_seconds" setting
        time_format_string = "%-I:%M:%S %p" if show_seconds else "%-I:%M %p"
    else:
        time_format_string = "%H:%M:%S" if show_seconds else "%H:%M"

    # Format the current time
    current_time = datetime.now().strftime(time_format_string)
    return [current_time]


def display_time():
    global draw, image
    image = Image.new('1', (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # Get the current time
    time_text = get_current_time()[0]

    # Wrap the time text
    wrapped_lines = wrap_text(time_text, selected_font, width)

    # Calculate the total height of the wrapped text block
    ascent, descent = selected_font.getmetrics()
    line_height = ascent + descent
    total_height = len(wrapped_lines) * line_height

    # Determine vertical alignment
    y_offset = (height - total_height) // 2  # Center vertically

    # Draw each wrapped line of text
    for line in wrapped_lines:
        text_width, _ = draw.textsize(line, font=selected_font)

        # Center horizontally
        x_offset = (width - text_width) // 2
        draw.text((x_offset, y_offset), line, font=selected_font, fill=text_color)
        y_offset += line_height  # Move to the next line

    # Rotate and display the image
    image = image.rotate(screen_rotate)
    epd.displayPartial(epd.getbuffer(image))


def main():
    try:
        while True:
            display_time()
            time.sleep(3)
    except KeyboardInterrupt:
        print("Exiting. Putting e-ink display to sleep.")
        epd.sleep()

if __name__ == "__main__":
    main()
