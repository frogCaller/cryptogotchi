import sys
import os
import time
import json
import random
import subprocess
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd2in13_V3
import argparse


# Function to parse command-line arguments
def str_to_bool(value):
    if value.lower() in ['true', '1', 'yes']:
        return True
    elif value.lower() in ['false', '0', 'no']:
        return False
    else:
        raise argparse.ArgumentTypeError(f"Boolean value expected (got {value}).")


def parse_args():
    parser = argparse.ArgumentParser(description="Display a message, joke, or fortune on an e-ink screen.")
    parser.add_argument("--message", type=str, nargs="?", default=None, help="The message to display.")  # Make message optional
    parser.add_argument("--display_type", type=str, choices=["message", "joke", "fortune"], default="message",
                        help="What to display: a custom message, a joke, or a fortune.")
    parser.add_argument("--font", type=int, default=None, help="Font size (text height).")
    parser.add_argument("--justify", type=str, choices=["left", "center", "right"], default=None, help="Text justification.")
    parser.add_argument("--vertical_align", type=str, choices=["top", "center", "bottom"], default=None, help="Vertical alignment.")
    parser.add_argument("--font_style", type=int, choices=range(1, 8), default=None, help="Font style (1-7).")
    parser.add_argument("--dark_mode", type=str_to_bool, default=None, help="Enable dark mode (true/false).")
    parser.add_argument("--rotate", type=int, choices=[0, 90, 180, 270], default=None, help="Screen rotation angle.")
    return parser.parse_args()


# Load settings from config.yaml or command-line arguments
args = parse_args()
# Override config settings with command-line arguments if provided
text_style = args.font_style if args.font_style is not None else 1
text_height = args.font if args.font is not None else 18
text_justify = args.justify if args.justify is not None else "left"
text_align = args.vertical_align if args.vertical_align is not None else "top"
dark_mode = args.dark_mode if args.dark_mode is not None else False
screen_rotate = args.rotate if args.rotate is not None else 180

# Correctly set background and text color based on dark_mode
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
    1: 'Fonts/Font.ttc',
    2: 'Fonts/DejaVuSansMono.ttf',
    3: 'Fonts/FrederickatheGreat-Regular.ttf',
    4: 'Fonts/RubikDoodleShadow-Regular.ttf',
    5: 'Fonts/GravitasOne-Regular.ttf',
    6: 'Fonts/SpecialElite-Regular.ttf',
    7: 'Fonts/Gluten-Light.ttf'
}
jokes_file = os.path.join(os.path.dirname(__file__), "templates", "jokes.json")

def load_json_with_comments(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()
        # Remove lines starting with `//`
        json_string = "".join(line for line in lines if not line.strip().startswith("//"))
        return json.loads(json_string)

# Load jokes using the correct file path
jokes = load_json_with_comments(jokes_file)

# Function to fetch a random joke
def fetch_joke():
    try:
        # Randomly select a joke
        if jokes:
            joke = random.choice(jokes)
            return f"{joke['setup']} -- {joke['punchline']}"
        else:
            return "No jokes found in the file."
    except FileNotFoundError:
        return "Jokes file not found."
    except json.JSONDecodeError:
        return "Error decoding jokes file."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def get_fortune(selected_font, width, height):
    while True:
        try:
            ascent, descent = selected_font.getmetrics()
            line_height = ascent + descent
            max_lines = height // line_height

            avg_char_width = selected_font.getsize("W")[0]
            max_line_words = width // avg_char_width
            max_words = max_lines * max_line_words

            # Fetch a fortune
            result = subprocess.run(['fortune'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            fortune_text = result.stdout.decode('utf-8').strip()
            print(f"Retrieved fortune: {fortune_text}")  # Debugging output

            word_count = len(fortune_text.split())
            if word_count > max_words:
                print(f"Fortune too long ({word_count} words). Fetching a new one...")
                continue  # Fetch a new fortune

            wrapped_text = wrap_text(fortune_text, selected_font, width)

            if len(wrapped_text) <= max_lines:
                return wrapped_text

            print(f"Fortune too long ({len(wrapped_text)} lines). Fetching a new one...")

        except Exception as e:
            print(f"Error running fortune: {e}")
            return ["Error fetching", "fortune."]


def get_font(text_style, text_height):
    font_path = font_paths.get(text_style, font_paths[1])
    return ImageFont.truetype(font_path, text_height)


selected_font = get_font(text_style, text_height)


def wrap_text(text, font, max_width):
    wrapped_lines = []
    words = text.split()
    lines = text.split("\n")
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

        if text_width <= max_width:
            current_line = test_line  # Add the word to the current line
        else:
            wrapped_lines.append(current_line.strip())  # Add the current line
            current_line = f"{word} "  # Start a new line with the current word

    if current_line.strip():
        wrapped_lines.append(current_line.strip())

    return wrapped_lines[:6]


def display_message(message):
    global draw, image
    image = Image.new('1', (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # Wrap the text
    wrapped_message = wrap_text(message, selected_font, width)

    # Calculate the total height of the text block
    ascent, descent = selected_font.getmetrics()
    line_height = ascent + descent
    total_height = len(wrapped_message) * line_height

    # Determine vertical alignment
    if text_align == "top":
        y_offset = 0  # Start at the top
    elif text_align == "center":
        y_offset = (height - total_height) // 2  # Center vertically
    elif text_align == "bottom":
        y_offset = height - total_height  # Start at the bottom
    else:
        raise ValueError(f"Invalid text alignment: {text_align}")

    # Draw each line of text with justification
    for line in wrapped_message:
        text_width, _ = draw.textsize(line, font=selected_font)

        if text_justify == "center":
            x_offset = (width - text_width) // 2  # Center horizontally
        elif text_justify == "right":
            x_offset = width - text_width - 5  # Right-align with padding
        elif text_justify == "left":
            x_offset = 5  # Left-align with padding
        else:
            raise ValueError(f"Invalid text justification: {text_justify}")

        draw.text((x_offset, y_offset), line, font=selected_font, fill=text_color)
        y_offset += line_height  # Move to the next line

    # Rotate and save the image
    image = image.rotate(screen_rotate)
    image.save("Data/message.png")
    epd.displayPartial(epd.getbuffer(image))


def main():
    if args.display_type == "message":
        if not args.message:
            print("Error: No message provided for display_type='message'.")
        else:
            display_message(args.message)

    elif args.display_type == "joke":
        print("Displaying a joke...")
        joke = fetch_joke()
        if joke:
            display_message(joke)
        else:
            print("No joke available.")

    elif args.display_type == "fortune":
        print("Displaying a fortune...")
        fortune_lines = get_fortune(selected_font, width, height)
        if fortune_lines:
            display_message("\n".join(fortune_lines))  # Join lines into a single string
        else:
            print("No fortune available.")

    print("Message displayed on the e-ink screen!")

if __name__ == "__main__":
    main()

#python3 write.py --display_type=joke
#python3 write.py --display_type=fortune
#python3 write.py helloworld
