import sys
import os
import json
import time
import requests
import subprocess
import threading
import socket
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from waveshare_epd import epd2in13_V3
from PIL import Image, ImageDraw, ImageFont, ImageOps
import psutil
import yaml


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception as e:
        return "127.0.0.1"

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

host_ip = get_local_ip()
config = load_config()
username = config["Cryptogotchi Settings"]["username"]
dark_mode = config["Cryptogotchi Settings"]["dark_mode"]
screen_rotate = config["Cryptogotchi Settings"]["screen_rotation"]
hide_faces = not config["Cryptogotchi Settings"]["show_faces"]
graph_history = config["Cryptogotchi Settings"]["graph_history"]
refresh_rate = config["Cryptogotchi Settings"]["refresh_rate"]

bg_color = 0 if dark_mode else 255
text_color = 255 if dark_mode else 0


LOOK_R = '( ⚆_⚆)'
LOOK_L = '(☉_☉ )'
LOOK_R_HAPPY = '( ◕‿◕)'
LOOK_L_HAPPY = '(◕‿◕ )'
SLEEP = '(⇀‿‿↼)'
SLEEP2 = '(≖‿‿≖)'
AWAKE = '(◕‿‿◕)'
BORED = '(-__-)'
INTENSE = '(°▃▃°)'
COOL = '(⌐■_■)'
HOT = "( '⚆_⚆)"
HOT2 = "(☉_☉' )"
HAPPY = '(•‿‿•)'
GRATEFUL = '(^‿‿^)'
EXCITED = '(ᵔ◡◡ᵔ)'
MOTIVATED = '(☼‿‿☼)'
DEMOTIVATED = '(≖__≖)'
SMART = '(✜‿‿✜)'
LONELY = '(ب__ب)'
SAD = '(╥☁╥ )'
ANGRY = "(-_-')"
FRIEND = '(♥‿‿♥)'
BROKEN = '(☓‿‿☓)'
DEBUG = '(#__#)'
UPLOAD = '(1__0)'
UPLOAD1 = '(1__1)'
UPLOAD2 = '(0__1)'

coin_index = 0
fallback_coins = [
    {"id": "bitcoin", "name": "Bitcoin", "display": "BTC", "format": 0, "show": True},
    {"id": "dogecoin", "name": "Dogecoin", "display": "DOGE", "format": 3, "show": True},
    {"id": "litecoin", "name": "Litecoin", "display": "LTC", "format": 2, "show": True},
    {"id": "verus-coin", "name": "Verus coin", "display": "VRSC", "format": 2, "show": True},
    {"id": "shiba-inu", "name": "Shiba Inu", "display": "SHIB", "format": 6, "show": True},
    {"id": "ethereum", "name": "Ethereum", "display": "ETH", "format": 2, "show": True}
]

last_coins_update_time = 0

def validate_coins(coins_list):
    default_structure = {
        "id": "",
        "name": "",
        "display": "",
        "format": 0,
        "show": True
    }
    for coin in coins_list:
        for key, default_value in default_structure.items():
            if key not in coin:
                coin[key] = default_value
    return coins_list

def refresh_reload_coins():    
    global coins, last_coins_update_time, coin_index
    coins_file = os.path.join(os.path.dirname(__file__), "templates", "coins.json")
    if os.path.exists(coins_file):
        file_mod_time = os.path.getmtime(coins_file)
        if file_mod_time != last_coins_update_time:
            try:
                with open(coins_file, "r") as f:
                    coins = json.load(f)
                coins = validate_coins(coins)
                last_coins_update_time = file_mod_time
                visible_coins = [coin for coin in coins if coin.get("show", True)]
                
                if not visible_coins:
                    coin_index = 0
                    print("No visible coins. Please check your configuration.")
                elif coin_index >= len(visible_coins): 
                    coin_index = 0
            except Exception as e:
                print(f"Error reloading coins.json: {e}")
          
# Data directory
data_directory = "Data"
if not os.path.exists(data_directory):
    os.makedirs(data_directory)

# Historical data file
historical_prices_file = os.path.join(data_directory, "f{coin_id}_historical_prices.json")


myface = []
quote_index = 0
#up_quotes = ["TO THE MOON!", "Bulls are running!", "Next stop: the moon!", "Keep climbing!", "Green all the way!"]
#down_quotes = ["Buy the dip!", "Opportunities in red", "Patience is key.", "Down but not out.", "Stay calm and HODL"]
quotes_list = ["In crypto, we trust.", "Crypto never sleeps", "TO THE MOON!", "Stay calm and HODL", "Buy the dip!"]
timestamps = []

last_quote_update_time = 0
current_quote = ""
first_run = True
last_price_fetch_time = 0
last_graph_display_time = time.time() - 120


font10 = ImageFont.truetype('Fonts/Font.ttc', 10)
font12 = ImageFont.truetype('Fonts/Font.ttc', 12)
font15 = ImageFont.truetype('Fonts/Font.ttc', 15)
font18 = ImageFont.truetype('Fonts/Font.ttc', 18)
font20 = ImageFont.truetype('Fonts/Font.ttc', 20)
font22 = ImageFont.truetype('Fonts/Font.ttc', 22)
font25 = ImageFont.truetype('Fonts/Font.ttc', 25)
font30 = ImageFont.truetype('Fonts/Font.ttc', 30)
face32 = ImageFont.truetype(('Fonts/DejaVuSansMono.ttf'), 32)


def get_coin_data(coin_id):
    try:
        # Correctly define the CoinGecko API URL using the passed coin_id
        coin_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/"
        response = requests.get(coin_url)
        response.raise_for_status()
        data = response.json()

        # Extract relevant fields from CoinGecko API response safely
        ath = data.get("market_data", {}).get("ath", {}).get("usd", "N/A")
        ath_date = data.get("market_data", {}).get("ath_date", {}).get("usd", "N/A")
        current_price = data.get("market_data", {}).get("current_price", {}).get("usd", "N/A")
        market_cap = data.get("market_data", {}).get("market_cap", {}).get("usd", "N/A")
        market_cap_rank = data.get("market_cap_rank", "N/A")
        total_supply = data.get("market_data", {}).get("total_supply", "N/A")
        circulating_supply = data.get("market_data", {}).get("circulating_supply", "N/A")
        sentiment_up = data.get("sentiment_votes_up_percentage", "N/A")
        sentiment_down = data.get("sentiment_votes_down_percentage", "N/A")
        high_24h = data.get("market_data", {}).get("high_24h", {}).get("usd", "N/A")
        low_24h = data.get("market_data", {}).get("low_24h", {}).get("usd", "N/A")

        # Safely extract percentage changes with defaults if missing
        price_change_24h = data.get("market_data", {}).get("price_change_percentage_24h", "N/A")
        price_change_7d = data.get("market_data", {}).get("price_change_percentage_7d", "N/A")
        price_change_30d = data.get("market_data", {}).get("price_change_percentage_30d", "N/A")
        price_change_60d = data.get("market_data", {}).get("price_change_percentage_60d", "N/A")
        price_change_200d = data.get("market_data", {}).get("price_change_percentage_200d", "N/A")
        price_change_1y = data.get("market_data", {}).get("price_change_percentage_1y", "N/A")

        return {
            "ath": ath,
            "ath_date": ath_date,
            "current_price": current_price,
            "percentage_change_from_ath": ((current_price - ath) / ath) * 100 if ath != "N/A" and current_price != "N/A" else "N/A",
            "market_cap": market_cap,
            "market_cap_rank": market_cap_rank,
            "total_supply": total_supply,
            "circulating_supply": circulating_supply,
            "sentiment_votes_up_percentage": sentiment_up,
            "sentiment_votes_down_percentage": sentiment_down,
            "high_24h": high_24h,
            "low_24h": low_24h,
            "price_change_24h": price_change_24h,
            "price_change_7d": price_change_7d,
            "price_change_30d": price_change_30d,
            "price_change_60d": price_change_60d,
            "price_change_200d": price_change_200d,
            "price_change_1y": price_change_1y
        }
    except requests.RequestException as e:
        print(f"Error fetching {coin_id} data: {e}")
        return {
            "ath": "N/A",
            "ath_date": "N/A",
            "current_price": "N/A",
            "percentage_change_from_ath": "N/A",
            "market_cap": "N/A",
            "market_cap_rank": "N/A",
            "total_supply": "N/A",
            "circulating_supply": "N/A",
            "sentiment_votes_up_percentage": "N/A",
            "sentiment_votes_down_percentage": "N/A",
            "high_24h": "N/A",
            "low_24h": "N/A",
            "price_change_24h": "N/A",
            "price_change_7d": "N/A",
            "price_change_30d": "N/A",
            "price_change_60d": "N/A",
            "price_change_200d": "N/A",
            "price_change_1y": "N/A"
        }

def save_coin_data_to_file(coin_id, data):
    file_path = os.path.join(data_directory, f"{coin_id}_data.json")
    with open(file_path, "w") as file:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "data": data
        }, file)

def load_coin_data_from_file(coin_id):
    file_path = os.path.join(data_directory, f"{coin_id}_data.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            cached_data = json.load(file)
            return cached_data["timestamp"], cached_data["data"]
    return None, None

def should_fetch_new_coin_data(timestamp):
    if timestamp:
        last_fetch_time = datetime.fromisoformat(timestamp)
        return datetime.now() - last_fetch_time >= timedelta(minutes=5)
    return True

def fetch_coin_data_with_cache(coin_id):
    timestamp, cached_data = load_coin_data_from_file(coin_id)
    if should_fetch_new_coin_data(timestamp):
        # Fetch new data from API
        new_data = get_coin_data(coin_id)
        save_coin_data_to_file(coin_id, new_data)
        return new_data
    return cached_data

def format_ath_date(ath_date_str):
    try:
        ath_date = datetime.strptime(ath_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        return ath_date.strftime("%Y-%m-%d")  # Format the date as YYYY-MM-DD
    except ValueError:
        return ath_date_str
      
def manage_price_file(coin_id, price=None):
    file_path = os.path.join(data_directory, f"{coin_id}_price.txt")
    if price is not None:
        with open(file_path, "w") as file:
            file.write(str(price))
    else:
        try:
            with open(file_path, "r") as file:
                return float(file.read().strip())
        except (FileNotFoundError, ValueError):
            return None

def get_cpu_memory_usage():
    cpu_usage = psutil.cpu_percent()
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    return cpu_usage, memory_usage


def get_new_quotes():
    global current_quote, quote_index
    if quote_index >= len(quotes_list):
        quote_index = 0 
    current_quote = quotes_list[quote_index]
    quote_index += 1
    return current_quote

def get_current_time():
    now = datetime.now()
    day = now.strftime("%A").upper()
    date = now.strftime("%m/%d/%y")
    time_str = now.strftime("%I:%M %p")
    return f"{day}  {time_str}\n{date}"


def get_cpu_temperature():
    try:
        cpu_temp = os.popen("vcgencmd measure_temp").readline()
        return cpu_temp.replace("temp=", "").replace("'","°")
    except:
        return False
      
      
def format_large_number(num):
    try:
        num = float(num)
        if num >= 1e15:
            return f"{num / 1e12:.2f}Qd"
        elif num >= 1e12:
            return f"{num / 1e12:.2f}T"
        elif num >= 1e9:
            return f"{num / 1e9:.2f}B"
        elif num >= 1e6:
            return f"{num / 1e6:.2f}M"
        elif num >= 1e3:
            return f"{num / 1e3:.2f}K"
        else:
            return f"{num:.2f}"
    except (ValueError, TypeError):
        return num 
      

def get_wifi_status():
    try:
        subprocess.check_output(['ping', '-c', '1', '8.8.8.8'])
        return "WIFI: OK"
    except subprocess.CalledProcessError:
        return "NET ERROR"

look_counter = 0

def update_face(coin_data, first_run):
    global myface, look_counter

    myface.clear()
    wifi_status = get_wifi_status()
    cpu_temp = get_cpu_temperature()
    cpu_temp_value = float(cpu_temp.replace("°C", "")) if cpu_temp else None

    if wifi_status == "NET ERROR":
        myface.append(SAD)
    elif cpu_temp_value and cpu_temp_value >= 72:
        current_time = int(time.time())
        if current_time % 2 == 0:
            myface.append(HOT)
        else:
            myface.append(HOT2)

    if first_run:
        myface.append(AWAKE)
    else:
        current_time = int(time.time())
        state = current_time // 3 % 2

        sentiment_up = float(coin_data.get("sentiment_votes_up_percentage", "0"))

        if sentiment_up > 75:

            if look_counter < 4:  
                if look_counter % 2 == 0:
                    myface.append(LOOK_R_HAPPY)
                else:
                    myface.append(LOOK_L_HAPPY)
                look_counter += 1  # Increment the counter each time
            else:
                myface.append(COOL)
                look_counter = 0  # Reset the counter after showing COOL
        elif sentiment_up > 50:  # Positive sentiment (> 50%), show happy faces
            if state == 0:  # LOOK_R_HAPPY twice
                myface.append(LOOK_R_HAPPY)
            else:  # LOOK_L_HAPPY twice
                myface.append(LOOK_L_HAPPY)
        else:  # Negative sentiment, change to neutral/looking faces
            if state == 0:  # LOOK_L twice
                myface.append(LOOK_R)
            else:  # LOOK_R twice
                myface.append(LOOK_L)

def get_historical_prices(coin_id):
    coin_graph = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={graph_history}"
    try:
        response = requests.get(coin_graph)
        response.raise_for_status()
        data = response.json()
        prices = [price[1] for price in data["prices"]]
        return prices
    except requests.RequestException as e:
        print(f"Error fetching historical prices: {e}")
        return []

def save_historical_prices(coin_id, prices):
    historical_prices_file = os.path.join(data_directory, f"{coin_id}_historical_prices.json")
    with open(historical_prices_file, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "prices": prices}, f)

def load_historical_prices(coin_id):
    historical_prices_file = os.path.join(data_directory, f"{coin_id}_historical_prices.json")
    if os.path.exists(historical_prices_file):
        with open(historical_prices_file, "r") as f:
            data = json.load(f)
            return data["timestamp"], data["prices"]
    return None, None

def should_fetch_new_historical_data(timestamp):
    if timestamp:
        last_fetch_time = datetime.fromisoformat(timestamp)
        return datetime.now() - last_fetch_time >= timedelta(minutes=5)
    return True

def fetch_historical_prices_with_cache(coin_id):
    timestamp, cached_prices = load_historical_prices(coin_id)
    if should_fetch_new_historical_data(timestamp):
        new_prices = get_historical_prices(coin_id)
        if new_prices:
            save_historical_prices(coin_id, new_prices)
            return new_prices
        return cached_prices
    return cached_prices

def plot_prices(coin_id, prices, dark_mode=False):
    top_left_x, top_left_y = 5, 30
    bottom_right_x, bottom_right_y = 145, 75

    width_pixels = bottom_right_x - top_left_x
    height_pixels = bottom_right_y - top_left_y

    dpi = 100
    width_inches = width_pixels / dpi
    height_inches = height_pixels / dpi

    plt.figure(figsize=(width_inches, height_inches))
    
    # Apply dark mode settings
    if dark_mode:
        plt.style.use('dark_background')  # Use a dark background for the plot
        line_color = 'white'  # White line for contrast
    else:
        plt.style.use('default')  # Use default style
        line_color = 'black'  # Black line for contrast    
    
    ax = plt.gca()
    ax.plot(prices, color=line_color)
    ax.set_ylim([min(prices), max(prices)])

    # Remove axis labels and plot borders
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Save the plot to an image file in the Data folder
    plot_path = os.path.join(data_directory, f"{coin_id}_plot.png")
    plt.savefig(plot_path, dpi=dpi, bbox_inches='tight', pad_inches=0)
    plt.close()
    return plot_path
  

def draw_header(draw, coin, coin_data, font, screen_width=250):
    # Calculate text widths
    space = 3
    coin_text = f"{coin['name']}".upper()
    coin_acr = f"{coin['display']}"
    rank_text = f"RANK: {coin_data['market_cap_rank']}"
    time_text = datetime.now().strftime("%-I:%M %p")

    #coin_text_width = draw.textbbox((0, 0), coin_text, font=font)[2]
    coin_acr_width = draw.textbbox((0, 0), coin_acr, font=font)[2]
    rank_text_width = draw.textbbox((0, 0), rank_text, font=font)[2]
    time_text_width = draw.textbbox((0, 0), time_text, font=font)[2]
    
    if len(coin['name']) <= 12:
        coin_text_width = draw.textbbox((0, 0), coin_text, font=font)[2]
        total_text_width = coin_text_width + coin_acr_width + rank_text_width + time_text_width
    else:
        space = 2
        coin_text = ""  # Skip drawing coin name
        coin_text_width = 0
        total_text_width = coin_acr_width + rank_text_width + time_text_width

    # Calculate remaining space and distribute evenly
    total_text_width = coin_text_width + coin_acr_width + rank_text_width + time_text_width
    remaining_space = screen_width - total_text_width
    gap_between_texts = remaining_space // space  # Divide remaining space for gaps

    # Starting positions
    x_position = 2
    
    # Draw the coin name (if applicable)
    if coin_text:
        draw.text((x_position, 0), coin_text, font=font, fill=text_color)
        x_position += coin_text_width + gap_between_texts

    # Draw the coin acronym
    draw.text((x_position, 0), coin_acr, font=font, fill=text_color)
    x_position += coin_acr_width + gap_between_texts

    # Draw the rank text
    draw.text((x_position, 0), rank_text, font=font, fill=text_color)
    x_position += rank_text_width + gap_between_texts

    # Draw the time
    draw.text((x_position, 0), time_text, font=font, fill=text_color)
    
    
def draw_footer(draw, coin, coin_data, ath, ath_date, font, screen_width=250):
    space = 2
    # Format the ATH date
    formatted_ath_date = format_ath_date(ath_date)
    
    # Prepare the text for ATH, date, and percentage change
    ath_text = f"ATH:   ${ath:,.{coin['format']}f}"
    percentage_text = f"{coin_data['percentage_change_from_ath']:.2f} %"
    
    # Calculate text widths
    ath_text_width = draw.textbbox((0, 0), ath_text, font=font)[2]
    percentage_text_width = draw.textbbox((0, 0), percentage_text, font=font)[2]
    
    if coin['format'] <= 9:
        date_text = formatted_ath_date
        date_text_width = draw.textbbox((0, 0), date_text, font=font)[2]
    else:
        space = 1
        date_text = ""  # Skip the date
        date_text_width = 0

    x_ath = 5
    x_percentage = screen_width - percentage_text_width - 5
    
    # Center the date between ATH and percentage if it exists
    if date_text:
        x_date = (x_ath + ath_text_width + x_percentage - date_text_width) // space
    else:
        x_date = 0  # No date, so no x-coordinate needed

    draw.text((x_ath, 109), ath_text, font=font, fill=text_color)
    if date_text:
        draw.text((x_date, 109), date_text, font=font, fill=text_color)
    draw.text((x_percentage, 109), percentage_text, font=font, fill=text_color)

  
  
def draw_line_graph(draw, image, coin_data, line_y, line_width, time_period_label, low_key, high_key, current_key, coin, font, total_width=252):
    # Calculate X position of the line
    line_x = (total_width - line_width) // 2  # Center the line horizontally

    # Draw the main price line (from low to high for the specified time period)
    draw.line([(line_x, line_y), (line_x + line_width, line_y)], fill=text_color, width=2)

    # Draw tick marks at 25%, 50%, and 75%
    for i in range(1, 4):
        tick_x = line_x + (i * (line_width // 4))
        draw.line([(tick_x, line_y - 5), (tick_x, line_y + 5)], fill=text_color, width=1)

    # Get the low, high, and current price data for the specified period
    low_value = float(coin_data.get(low_key, 0))
    high_value = float(coin_data.get(high_key, 0))
    current_value = float(coin_data.get(current_key, 0))

    # Ensure the low and high prices are valid before proceeding
    if high_value > low_value:
        # Calculate the X position for the current price based on its position between the low and high
        price_position = (current_value - low_value) / (high_value - low_value)
        circle_x = line_x + int(line_width * price_position)
        circle_radius = 5

        # Draw the circle representing the current price
        draw.ellipse([(circle_x - circle_radius, line_y - circle_radius), 
                      (circle_x + circle_radius, line_y + circle_radius)], outline=0, fill=text_color)

        # Display the current price above the circle (higher up to avoid overlap with the line)
        current_price_text = f"${current_value:,.{coin['format']}f}"
        text_width = draw.textbbox((0, 0), current_price_text, font=font)[2]
        text_x = circle_x - text_width // 2
        draw.text((text_x, line_y - 21), current_price_text, font=font, fill=text_color)

    # Display the low and high prices at the start and end of the line (move them above the line)
    low_price_text = "24L" #f"${low_value:,.{coin['format']}f}"
    high_price_text = "24H" #f"${high_value:,.{coin['format']}f}"

    # Draw the low price on the left of the line (above the line)
    draw.text((line_x - 27, line_y - 9), low_price_text, font=font, fill=text_color)

    # Draw the high price on the right of the line (above the line)
    draw.text((line_x + line_width + 5, line_y - 10), high_price_text, font=font, fill=text_color)

    # Display the label for the time period (e.g., 24H, 7D, etc.) further above
    #draw.text((5, line_y - 20), time_period_label, font=font, fill=text_color)
  

def toggle_display(draw, image, coin, coin_data, current_quote, switch_interval=10):
    current_time = time.time()
    # Define the total cycle length (Sentiment + High/Low + Quotes)
    total_quotes = len(quotes_list)  # Number of quotes in the list
    cycle_time = switch_interval * (total_quotes + 4)  # Sentiment + High/Low + Quotes

    # Determine which part of the cycle we're in
    cycle_position = current_time % cycle_time

    if cycle_position < switch_interval:
        formatted_market_cap = format_large_number(coin_data['market_cap'])
        draw.text((125, 50), f"Market Cap: ${formatted_market_cap}", font=font12, fill=text_color)
    elif cycle_position < switch_interval * 2:
        formatted_circulation = format_large_number(coin_data['circulating_supply'])
        draw.text((125, 50), f"Circulation: {formatted_circulation}", font=font12, fill=text_color)
    elif cycle_position < switch_interval * 3:
        formatted_total_supply = format_large_number(coin_data['total_supply'])
        draw.text((125, 50), f"Total Supply: {formatted_total_supply}", font=font12, fill=text_color)
    elif cycle_position < switch_interval * 4:
        draw.text((125, 45), f"High: ${coin_data['high_24h']:,.{coin['format']}f}", font=font12, fill=text_color)
        draw.text((125, 60), f"Low: ${coin_data['low_24h']:,.{coin['format']}f}", font=font12, fill=text_color)
    else:
        quote_index = int((cycle_position - switch_interval * 2) // switch_interval)
        current_quote = quotes_list[quote_index % total_quotes]  # Ensure the quotes cycle correctly
        draw.text((125, 50), current_quote, font=font12, fill=text_color)
        
        
def toggle_bottom_display(draw, image, coin, coin_data, epd, switch_interval=30):
    current_time = time.time()

    # Determine which part of the cycle we're in
    cycle_position = current_time % (3 * switch_interval)

    if cycle_position < switch_interval:
        # Show the sentiment line with a circle representing sentiment vote up percentage for the first part of the cycle
        line_y = 95  # Y position for the line
        line_width = 196  # Width of the sentiment line
        total_width = 252  # Total width of the screen
        line_x = (total_width - line_width) // 2  # Center the line horizontally

        # Draw the main sentiment line
        draw.line([(line_x, line_y), (line_x + line_width, line_y)], fill=text_color, width=2)

        # Draw tick marks at 25%, 50%, and 75%
        for i in range(1, 4):
            tick_x = line_x + (i * (line_width // 4))
            draw.line([(tick_x, line_y - 5), (tick_x, line_y + 5)], fill=text_color, width=1)

        # Draw the sentiment circle
        up_percentage = coin_data.get('sentiment_votes_up_percentage', "N/A")

        if up_percentage != "N/A":
            up_percentage = float(up_percentage)
            circle_x = line_x + int(line_width * (up_percentage / 100))  # X position based on sentiment
            circle_radius = 5
            # Draw the circle representing sentiment
            draw.ellipse([(circle_x - circle_radius, line_y - circle_radius), 
                          (circle_x + circle_radius, line_y + circle_radius)], outline=0, fill=text_color)

        # Display the sentiment percentage text above the circle
        if up_percentage != "N/A":
            up_percentage_text = f"{up_percentage:.1f} %"
            text_width = draw.textbbox((0, 0), up_percentage_text, font=font12)[2]
            text_x = circle_x - text_width // 2
            draw.text((text_x, line_y - 20), up_percentage_text, font=font12, fill=text_color)

        # Load and resize the PNG images for happy and sad faces (for sentiment display)
        happy_icon = Image.open("images/happy_face.png").convert('L')  # Convert to grayscale
        sad_icon = Image.open("images/sad_face.png").convert('L')  # Convert to grayscale
        
        # Invert colors for dark mode
        if dark_mode:
            happy_icon = ImageOps.invert(happy_icon)
            sad_icon = ImageOps.invert(sad_icon)

        happy_icon = happy_icon.resize((18, 18)).convert('1')  # Convert to 1-bit (black/white)
        sad_icon = sad_icon.resize((18, 18)).convert('1')  # Convert to 1-bit (black/white)

        # X positions for happy and sad faces
        sad_x = line_x - 23  # Position happy face to the left of the line
        happy_x = line_x + line_width + 7  # Position sad face to the right of the line

        # Paste the faces at the desired positions
        image.paste(happy_icon, (happy_x, line_y - 10))
        image.paste(sad_icon, (sad_x, line_y - 10))

    elif cycle_position < 2 * switch_interval:
        # Show the 24-hour low and high price line with a circle representing the current price for the second part of the cycle
        draw_line_graph(draw, image, coin_data, line_y=95, line_width=196, time_period_label="24H", low_key="low_24h", high_key="high_24h", current_key="current_price", coin=coin, font=font12)

    else:
        # Show the 24h, 7d, 30d, 6m, 1Y info with centered labels and values for the next 15 seconds
        label_y = 76  # Starting y position for labels
        value_y = 90  # Starting y position for values
        total_width = epd.width  # The total width of the screen

        # Safely retrieve price change percentages with fallback values
        price_change_24h = float(coin_data.get('price_change_24h', 0))
        price_change_7d = float(coin_data.get('price_change_7d', 0))
        price_change_30d = float(coin_data.get('price_change_30d', 0))
        price_change_200d = float(coin_data.get('price_change_200d', 0))
        price_change_1y = float(coin_data.get('price_change_1y', 0))

        # Define the text for labels and their values
        labels = ["24H", "7D", "30D", "6M", "1Y"]
        values = [f"{price_change_24h:.2f}%", f"{price_change_7d:.2f}%", f"{price_change_30d:.2f}%", f"{price_change_200d:.2f}%", f"{price_change_1y:.2f}%"]
        separator = "  |  "

        # Get the width of each label, value, and separator and calculate the total width for each
        label_value_pairs = []
        separator_width = draw.textbbox((0, 0), separator, font=font12)[2]
        for label, value in zip(labels, values):
            label_width = draw.textbbox((0, 0), label, font=font12)[2]
            value_width = draw.textbbox((0, 0), value, font=font12)[2]
            total_pair_width = max(label_width, value_width)
            label_value_pairs.append((label, value, total_pair_width))

        # Calculate total width for all pairs combined, accounting for separators
        total_pairs_width = sum(pair[2] for pair in label_value_pairs) + separator_width * (len(labels) - 1)
        spacing = ((total_width - total_pairs_width) // len(labels)) + 24  # Spacing between pairs

        # Calculate starting x position to center the entire row of labels and values
        current_x = 0

        # Draw each label and its corresponding value centered, including the separator
        for i, (label, value, pair_width) in enumerate(label_value_pairs):
            # Calculate x positions to center each label and value
            label_x = current_x + (pair_width - draw.textbbox((0, 0), label, font=font12)[2]) // 2
            value_x = current_x + (pair_width - draw.textbbox((0, 0), value, font=font12)[2]) // 2

            # Draw the label and value
            draw.text((label_x, label_y), label, font=font12, fill=text_color)
            draw.text((value_x, value_y), value, font=font12, fill=text_color)

            # Move to the next position
            current_x += pair_width

            # Draw separator if it's not the last pair
            if i < len(label_value_pairs) - 1:
                separator_x = current_x + spacing // 2  # Center separator between pairs
                draw.text((separator_x, label_y), separator, font=font15, fill=text_color)
                draw.text((separator_x, value_y), separator, font=font15, fill=text_color)
                current_x += separator_width + spacing  # Adjust current_x for next pair


def display_coin_data(epd, coin, coin_data, coin_price, price_change_24h, price_change_7d, price_change_30d, price_change_60d, price_change_200d, price_change_1y, cpu_temp, cpu_usage, memory_usage, show_graph=False, now=None, ath="N/A", ath_date="N/A", showing_sentiment=False):

    global current_quote

    image = Image.new('1', (epd.height, epd.width), bg_color)
    draw = ImageDraw.Draw(image)

    # Drawing the template
    draw.rectangle((0, 0, 250, 122), fill=bg_color)

    draw_header(draw, coin, coin_data, font12, screen_width=248)

    draw.line([(0, 14), (250, 14)], fill=text_color, width=1)
    
    draw.text((5, 15), f"{username}>", font=font12, fill=text_color)

    # Update current_quote if CPU temperature is too high
    if myface and myface[0] == HOT:
        current_quote = "It's getting hot!"
      
    toggle_bottom_display(draw, image, coin, coin_data, epd)
    toggle_display(draw, image, coin, coin_data, current_quote)

    if coin['format'] > 10:
        font = font18
    elif coin['format'] > 8:
        font = font20    
    elif coin['format'] > 6:
        font = font22
    else:
        font = font25
        
    draw.text((125, 16), f"${coin_data['current_price']:,.{coin['format']}f}", font=font, fill=text_color)
    
    draw.line([(0, 108), (250, 108)], fill=text_color, width=1)

    draw_footer(draw, coin, coin_data, ath, ath_date, font12, screen_width=248)

    if show_graph:
        # Plot historical prices and load the plot image
        historical_prices = fetch_historical_prices_with_cache(coin['id'])
        plot_path = plot_prices(coin['id'], historical_prices, dark_mode=dark_mode)
        plot_image = Image.open(plot_path).convert('1')
        image.paste(plot_image, (5, 35)) 

    else:
        # Display current face
        if myface:
            draw.text((3, 28), myface[0], font=face32, fill=text_color)

    # Rotate and display the image    
    image = image.rotate(screen_rotate)
    epd.displayPartial(epd.getbuffer(image))

def main():
#    start_web_interface()
    global coins
    with open("coins.json", "r") as f:
        coins = json.load(f)
    coins = validate_coins(coins)
    visible_coins = [coin for coin in coins if coin.get("show", True)]
    if not visible_coins:
        visible_coins = fallback_coins  # Fallback to all coins if no favorites

    coin_index = 0
    global last_price_fetch_time, last_graph_display_time
    last_face_display_time = time.time()
    
    epd = epd2in13_V3.EPD()
    epd.init()
    epd.Clear(bg_color)

    last_fetch_time = 0
    last_face_update_time = 0
    last_quote_update_time = 0
    last_cpu_temp_update_time = 0
    last_coin_update_time = time.time()  # Initialize with current time
    coin_data = None
    coin_price = None
    cpu_temp = None 
    cpu_usage = None
    memory_usage = None    

    showing_sentiment = False
    sentiment_display_start = 0
    first_run = True 
    show_graph = False  # Variable to control graph display
    coin_cycle_complete = False  # To track when we are done with the current coin
    coin_update_interval = 90  # 1.5 minutes (90 seconds)

    while True:
        current_time = time.time()
        now = datetime.now()
        
        if coin_index >= len(visible_coins):
            coin_index = 0

        coin = visible_coins[coin_index]
        coin_id = coin['id'] 
        
        if current_time - last_cpu_temp_update_time >= 3:
            cpu_temp = get_cpu_temperature()
            cpu_usage, memory_usage = get_cpu_memory_usage()  # Get CPU and memory usage
            last_cpu_temp_update_time = current_time

        # Fetch coin data every 2 minutes, only for the current coin
        if current_time - last_fetch_time >= 120:
            try:
                coin_data = fetch_coin_data_with_cache(coin_id)  # Fetch data for current coin
                ath = coin_data.get("ath", "N/A")
                ath_date = coin_data.get("ath_date", "N/A")
                last_fetch_time = current_time
            except Exception as e:
                print(f"Error in fetching coin data: {e}")

        # Fetch coin price every 5 minutes for the current coin
        if current_time - last_price_fetch_time >= 300:
            try:
                # Fetch coin price and percentage changes
                coin_data = fetch_coin_data_with_cache(coin_id)
                coin_price = coin_data.get('current_price')
                
                manage_price_file(coin_id, coin_price)
                
                price_change_24h = coin_data.get('price_change_24h')
                price_change_7d = coin_data.get('price_change_7d')
                price_change_30d = coin_data.get('price_change_30d')
                price_change_60d = coin_data.get('price_change_60d')
                price_change_200d = coin_data.get('price_change_200d')
                price_change_1y = coin_data.get('price_change_1y')
                last_price_fetch_time = current_time
            except Exception as e:
                print(f"Error in fetching coin price: {e}")
                coin_price = manage_price_file(coin_id)

        # Check if it's time to switch between faces and graph
        if not show_graph and (current_time - last_face_display_time >= 60):
            # Time to display the graph
            show_graph = True
            last_graph_display_time = current_time
            coin_cycle_complete = False  # Reset when starting a new cycle

        if show_graph:
            if current_time - last_graph_display_time >= 30:
                # Time to switch back to faces
                show_graph = False
                last_face_display_time = current_time
            else:
                display_coin_data(epd, coin, coin_data, coin_price, price_change_24h, price_change_7d, price_change_30d,
                                  price_change_60d, price_change_200d, price_change_1y, cpu_temp, cpu_usage,
                                  memory_usage, show_graph=True, now=now, ath=ath, ath_date=ath_date,
                                  showing_sentiment=showing_sentiment)
        else:
            display_coin_data(epd, coin, coin_data, coin_price, price_change_24h, price_change_7d, price_change_30d,
                              price_change_60d, price_change_200d, price_change_1y, cpu_temp, cpu_usage,
                              memory_usage, show_graph=hide_faces, now=now, ath=ath, ath_date=ath_date,
                              showing_sentiment=showing_sentiment)

            # Update face every 3 seconds
            if current_time - last_face_update_time >= 3:
                if coin_data:
                    update_face(coin_data, first_run)
                    first_run = False
                last_face_update_time = current_time

            # Update quotes every 10 seconds
            if showing_sentiment:
                if current_time - sentiment_display_start >= 10:
                    showing_sentiment = False
                    last_quote_update_time = current_time
            else:
                if current_time - last_quote_update_time >= 10:
                    showing_sentiment = True  # Switch to showing sentiment
                    sentiment_display_start = current_time 
                    current_quote = get_new_quotes()  # Get the next quote

            # Once the cycle is done for this coin (both graph and face displayed), mark as complete
            if not show_graph and not showing_sentiment and current_time - last_quote_update_time >= 10:
                coin_cycle_complete = True

        if coin_cycle_complete or (current_time - last_coin_update_time >= coin_update_interval):
            refresh_reload_coins()
            visible_coins = [coin for coin in coins if coin.get("show", True)]    
            if not visible_coins:
                Fallback_length = len(fallback_coins)
                random_coin = random.choice(range(Fallback_length))
                visible_coins = [fallback_coins[random_coin]]
                print(f"Displaying fallback coin: {fallback_coins[random_coin]['name']} ({fallback_coins[random_coin]['display']}).")
                print(f"Visit http://{host_ip}:5000 to manage your coins.")
                
            coin_index = (coin_index + 1) % len(visible_coins)  # Move to the next coin
            last_coin_update_time = current_time  # Reset the time for the next coin change
            coin_cycle_complete = False  # Reset for the next coin

            # Fetch data immediately for the new coin
            coin = visible_coins[coin_index]
            coin_id = coin['id']
            try:
                coin_data = fetch_coin_data_with_cache(coin_id)
                ath = coin_data.get("ath", "N/A")
                ath_date = coin_data.get("ath_date", "N/A")
                last_fetch_time = current_time  # Reset fetch timer
            except Exception as e:
                print(f"Error in fetching coin data: {e}")

            try:
                # Fetch coin price and percentage changes
                coin_price = coin_data.get('current_price')
                price_change_24h = coin_data.get('price_change_24h')
                price_change_7d = coin_data.get('price_change_7d')
                price_change_30d = coin_data.get('price_change_30d')
                price_change_60d = coin_data.get('price_change_60d')
                price_change_200d = coin_data.get('price_change_200d')
                price_change_1y = coin_data.get('price_change_1y')
                last_price_fetch_time = current_time  # Reset price fetch timer
            except Exception as e:
                print(f"Error in fetching coin price: {e}")
                coin_price = manage_price_file(coin_id)

            first_run = True 

        time.sleep(refresh_rate)

if __name__ == "__main__":
    main()
    
