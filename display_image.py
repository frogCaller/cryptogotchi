import os
import time
from PIL import Image
from waveshare_epd import epd2in13_V3
import yaml

def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)
      
config = load_config()
screen_rotate = config["Drawing Settings"]["screen_rotation"]
dark_mode = config["Drawing Settings"]["dark_mode"]

epd = epd2in13_V3.EPD()
epd.init()

width = epd.height
height = epd.width

def display_image():
    try:
        file_path = os.path.join("Data", "drawing.png")
        if not os.path.exists(file_path):
            print(f"Error: {file_path} not found!")
            return
        
        image = Image.open(file_path).convert("RGBA")

        if dark_mode:
            background = Image.new("RGBA", image.size, "BLACK")
            composite = Image.alpha_composite(background, image)
            composite = composite.convert("L").point(lambda x: 255 - x)
        else:
            background = Image.new("RGBA", image.size, "WHITE")
            composite = Image.alpha_composite(background, image)

        composite = composite.convert("1")

        composite = composite.resize((width, height), Image.ANTIALIAS).rotate(screen_rotate)

        epd.display(epd.getbuffer(composite))

        print("Image displayed on e-ink screen.")
    except Exception as e:
        print(f"Error displaying image: {e}")

def main():
    try:
        display_image()
    except KeyboardInterrupt:
        print("Exiting. Putting e-ink display to sleep.")
        time.sleep(10)

if __name__ == "__main__":
    main()
