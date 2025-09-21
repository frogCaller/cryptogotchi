import sys
import os
import json
import time
import requests
import subprocess
import threading
import feedparser
import socket
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from waveshare_epd import epd2in13_V3
from PIL import Image, ImageDraw, ImageFont, ImageOps
import psutil
import yaml

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

    with open("config.yaml", "w") as file:
        yaml.dump(config, file, default_flow_style=False)

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
HOT = "('⚆_⚆)"
HOT2 = "(☉_☉')"
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
    {"id": "ethereum", "name": "Ethereum", "display": "ETH", "format": 2, "show": True},
    {"id": "dogecoin", "name": "Dogecoin", "display": "DOGE", "format": 3, "show": True},
    {"id": "litecoin", "name": "Litecoin", "display": "LTC", "format": 2, "show": True},
    {"id": "verus-coin", "name": "Verus coin", "display": "VRSC", "format": 2, "show": True}
]

last_coins_update_time = 0

# Data directory
data_directory = "Data"
if not os.path.exists(data_directory):
    os.makedirs(data_directory)

# Historical data file
historical_prices_file = os.path.join(data_directory, "f{coin_id}_historical_prices.json")

myface = []
quote_index = 0
quotes_list = ["In crypto, we trust.", "Crypto never sleeps", "TO THE MOON!", "Stay calm and HODL", "Buy the dip!"]
hot_quotes = ["It's getting kinda hot!",  "Is it hot in here?",  "I'm sweating a bit",  "I am HOT!"]
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
face32 = ImageFont.truetype('Fonts/DejaVuSansMono.ttf', 32)
BOLD_FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
NewsFont = ImageFont.truetype(('Fonts/GravitasOne-Regular.ttf'), 10)


news_titles = []
last_news_fetch_time = 0
NEWS_FETCH_INTERVAL = 600

RSS_CATEGORIES = {
    "Crypto": {
        "CoinDesk": "https://feeds.feedburner.com/CoinDesk",
        "Decrypt": "https://decrypt.co/feed",
        "CryptoSlate": "https://cryptoslate.com/feed/",
        "NewsBTC": "https://www.newsbtc.com/feed/",
    }
}

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
  

def get_coin_data(coin_id):
    try:
        coin_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/"
        response = requests.get(coin_url)
        response.raise_for_status()
        data = response.json()

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
        return ath_date.strftime("%Y-%m-%d")
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
      
# --- Function to pick a random news feed ---
def pick_random_news_feed():
    category = random.choice(list(RSS_CATEGORIES.keys()))
    feed_name, feed_url = random.choice(list(RSS_CATEGORIES[category].items()))
    return feed_url
  
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
        return
      
    if cpu_temp_value and cpu_temp_value >= 72:
        current_time = int(time.time())
        if current_time % 2 == 0:
            myface.append(HOT)
        else:
            myface.append(HOT2)
        return

    if first_run:
        myface.append(AWAKE)
        return

    current_time = int(time.time())
    state = current_time // 3 % 2
    sentiment_up = float(coin_data.get("sentiment_votes_up_percentage", "0"))

    if sentiment_up > 75:
        if look_counter < 4:  
            if look_counter % 2 == 0:
                myface.append(LOOK_R_HAPPY)
            else:
                myface.append(LOOK_L_HAPPY)
            look_counter += 1
        else:
            myface.append(COOL)
            look_counter = 0 
    elif sentiment_up > 50:
        if state == 0: 
            myface.append(LOOK_R_HAPPY)
        else:
            myface.append(LOOK_L_HAPPY)
    else:
        if state == 0:
            myface.append(LOOK_R)
        else:
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
    
    if dark_mode:
        plt.style.use('dark_background')
        line_color = 'white'
    else:
        plt.style.use('default')
        line_color = 'black'    
    
    ax = plt.gca()
    ax.plot(prices, color=line_color)
    ax.set_ylim([min(prices), max(prices)])

    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    plot_path = os.path.join(data_directory, f"{coin_id}_plot.png")
    plt.savefig(plot_path, dpi=dpi, bbox_inches='tight', pad_inches=0)
    plt.close()
    return plot_path
  

def draw_header(draw, coin, coin_data, font, screen_width=250):

    space = 3
    coin_text = f"{coin['name']}".upper()
    coin_acr = f"{coin['display']}"
    rank_text = f"RANK: {coin_data['market_cap_rank']}"
    time_text = datetime.now().strftime("%-I:%M %p")

    coin_acr_width = draw.textbbox((0, 0), coin_acr, font=font)[2]
    rank_text_width = draw.textbbox((0, 0), rank_text, font=font)[2]
    time_text_width = draw.textbbox((0, 0), time_text, font=font)[2]
    
    if len(coin['name']) <= 12:
        coin_text_width = draw.textbbox((0, 0), coin_text, font=font)[2]
        total_text_width = coin_text_width + coin_acr_width + rank_text_width + time_text_width
    else:
        space = 2
        coin_text = ""
        coin_text_width = 0
        total_text_width = coin_acr_width + rank_text_width + time_text_width

    total_text_width = coin_text_width + coin_acr_width + rank_text_width + time_text_width
    remaining_space = screen_width - total_text_width
    gap_between_texts = remaining_space // space

    x_position = 2
    
    if coin_text:
        draw.text((x_position, 0), coin_text, font=font, fill=text_color)
        x_position += coin_text_width + gap_between_texts

    # Draw the coin acronym
    draw.text((x_position, 0), coin_acr, font=font, fill=text_color)
    x_position += coin_acr_width + gap_between_texts

    # Draw the rank text
    draw.text((x_position, 0), rank_text, font=font, fill=text_color)
    x_position += rank_text_width + gap_between_texts

    draw.text((x_position, 0), time_text, font=font, fill=text_color)
    
    
def draw_footer(draw, coin, coin_data, ath, ath_date, font, screen_width=250):
    space = 2
    # Format the ATH date
    formatted_ath_date = format_ath_date(ath_date)
    
    ath_text = f"ATH:   ${ath:,.{coin['format']}f}"
    percentage_text = f"{coin_data['percentage_change_from_ath']:.2f} %"
    
    ath_text_width = draw.textbbox((0, 0), ath_text, font=font)[2]
    percentage_text_width = draw.textbbox((0, 0), percentage_text, font=font)[2]
    
    if coin['format'] <= 9:
        date_text = formatted_ath_date
        date_text_width = draw.textbbox((0, 0), date_text, font=font)[2]
    else:
        space = 1
        date_text = "" 
        date_text_width = 0

    x_ath = 5
    x_percentage = screen_width - percentage_text_width - 5
    
    if date_text:
        x_date = (x_ath + ath_text_width + x_percentage - date_text_width) // space
    else:
        x_date = 0

    draw.text((x_ath, 109), ath_text, font=font, fill=text_color)
    if date_text:
        draw.text((x_date, 109), date_text, font=font, fill=text_color)
    draw.text((x_percentage, 109), percentage_text, font=font, fill=text_color)

  
  
def draw_line_graph(draw, image, coin_data, line_y, line_width, time_period_label, low_key, high_key, current_key, coin, font, total_width=252):
    line_x = (total_width - line_width) // 2


    draw.line([(line_x, line_y), (line_x + line_width, line_y)], fill=text_color, width=2)


    for i in range(1, 4):
        tick_x = line_x + (i * (line_width // 4))
        draw.line([(tick_x, line_y - 5), (tick_x, line_y + 5)], fill=text_color, width=1)


    low_value = float(coin_data.get(low_key, 0))
    high_value = float(coin_data.get(high_key, 0))
    current_value = float(coin_data.get(current_key, 0))

    if high_value > low_value:
       
        price_position = (current_value - low_value) / (high_value - low_value)
        circle_x = line_x + int(line_width * price_position)
        circle_radius = 5

        draw.ellipse([(circle_x - circle_radius, line_y - circle_radius), 
                      (circle_x + circle_radius, line_y + circle_radius)], outline=0, fill=text_color)

        current_price_text = f"${current_value:,.{coin['format']}f}"
        text_width = draw.textbbox((0, 0), current_price_text, font=font)[2]
        text_x = circle_x - text_width // 2
        draw.text((text_x, line_y - 21), current_price_text, font=font, fill=text_color)

    low_price_text = "24L"
    high_price_text = "24H"

    draw.text((line_x - 27, line_y - 9), low_price_text, font=font, fill=text_color)

    draw.text((line_x + line_width + 5, line_y - 10), high_price_text, font=font, fill=text_color)

  

def toggle_display(draw, image, coin, coin_data, current_quote, switch_interval=10):
    current_time = time.time()
    total_quotes = len(quotes_list)
    cycle_time = switch_interval * (total_quotes + 4)
    cycle_position = current_time % cycle_time

    text_box = (125, 45, 400, 80)
    draw.rectangle(text_box, fill=bg_color)

    if cycle_position < switch_interval:
        formatted_market_cap = format_large_number(coin_data['market_cap'])
        current_quote = f"Market Cap: ${formatted_market_cap}"
    elif cycle_position < switch_interval * 2:
        formatted_circulation = format_large_number(coin_data['circulating_supply'])
        current_quote = f"Circulation: {formatted_circulation}"
    elif cycle_position < switch_interval * 3:
        formatted_total_supply = format_large_number(coin_data['total_supply'])
        current_quote = f"Total Supply: {formatted_total_supply}"
    elif cycle_position < switch_interval * 4:
        current_quote = f"High: ${coin_data['high_24h']:,.{coin['format']}f}\nLow: ${coin_data['low_24h']:,.{coin['format']}f}"
    else:
        quote_index = int((cycle_position - switch_interval * 4) // switch_interval)
        current_quote = quotes_list[quote_index % total_quotes]

    # Override quote if HOT face
    if myface and myface[0] == HOT:
        hot_index = int(time.time() // switch_interval) % len(hot_quotes)  # cycle every switch_interval seconds
        current_quote = hot_quotes[hot_index]
    
    draw.text((125, 45), current_quote, font=font12, fill=text_color)


        
        
def toggle_bottom_display(draw, image, coin, coin_data, epd, switch_interval=30):
    current_time = time.time()

    cycle_position = current_time % (4 * switch_interval)

    if cycle_position < switch_interval:
        line_y = 95
        line_width = 196
        total_width = 252
        line_x = (total_width - line_width) // 2

        draw.line([(line_x, line_y), (line_x + line_width, line_y)], fill=text_color, width=2)

        for i in range(1, 4):
            tick_x = line_x + (i * (line_width // 4))
            draw.line([(tick_x, line_y - 5), (tick_x, line_y + 5)], fill=text_color, width=1)

        up_percentage = coin_data.get('sentiment_votes_up_percentage', "N/A")

        if up_percentage != "N/A":
            up_percentage = float(up_percentage)
            circle_x = line_x + int(line_width * (up_percentage / 100))
            circle_radius = 5

            draw.ellipse([(circle_x - circle_radius, line_y - circle_radius), 
                          (circle_x + circle_radius, line_y + circle_radius)], outline=0, fill=text_color)

        if up_percentage != "N/A":
            up_percentage_text = f"{up_percentage:.1f} %"
            text_width = draw.textbbox((0, 0), up_percentage_text, font=font12)[2]
            text_x = circle_x - text_width // 2
            draw.text((text_x, line_y - 20), up_percentage_text, font=font12, fill=text_color)

        happy_icon = Image.open("images/happy_face.png").convert('L')
        sad_icon = Image.open("images/sad_face.png").convert('L')
        
        if dark_mode:
            happy_icon = ImageOps.invert(happy_icon)
            sad_icon = ImageOps.invert(sad_icon)

        happy_icon = happy_icon.resize((18, 18)).convert('1')
        sad_icon = sad_icon.resize((18, 18)).convert('1')

        sad_x = line_x - 23
        happy_x = line_x + line_width + 7

        image.paste(happy_icon, (happy_x, line_y - 10))
        image.paste(sad_icon, (sad_x, line_y - 10))

    elif cycle_position < 2 * switch_interval:
        draw_line_graph(draw, image, coin_data, line_y=95, line_width=196, time_period_label="24H", low_key="low_24h", high_key="high_24h", current_key="current_price", coin=coin, font=font12)

    elif cycle_position < 3 * switch_interval:

        label_y = 76
        value_y = 90
        total_width = epd.width

        price_change_24h = float(coin_data.get('price_change_24h', 0))
        price_change_7d = float(coin_data.get('price_change_7d', 0))
        price_change_30d = float(coin_data.get('price_change_30d', 0))
        price_change_200d = float(coin_data.get('price_change_200d', 0))
        price_change_1y = float(coin_data.get('price_change_1y', 0))

        labels = ["24H", "7D", "30D", "6M", "1Y"]
        values = [f"{price_change_24h:.2f}%", f"{price_change_7d:.2f}%", f"{price_change_30d:.2f}%", f"{price_change_200d:.2f}%", f"{price_change_1y:.2f}%"]
        separator = "  |  "

        label_value_pairs = []
        separator_width = draw.textbbox((0, 0), separator, font=font12)[2]
        for label, value in zip(labels, values):
            label_width = draw.textbbox((0, 0), label, font=font12)[2]
            value_width = draw.textbbox((0, 0), value, font=font12)[2]
            total_pair_width = max(label_width, value_width)
            label_value_pairs.append((label, value, total_pair_width))

        total_pairs_width = sum(pair[2] for pair in label_value_pairs) + separator_width * (len(labels) - 1)
        spacing = ((total_width - total_pairs_width) // len(labels)) + 24

        current_x = 0

        for i, (label, value, pair_width) in enumerate(label_value_pairs):
            label_x = current_x + (pair_width - draw.textbbox((0, 0), label, font=font12)[2]) // 2
            value_x = current_x + (pair_width - draw.textbbox((0, 0), value, font=font12)[2]) // 2

            draw.text((label_x, label_y), label, font=BOLD_FONT, fill=text_color)
            draw.text((value_x, value_y), value, font=font12, fill=text_color)

            current_x += pair_width

            if i < len(label_value_pairs) - 1:
                separator_x = current_x + spacing // 2
                draw.text((separator_x, label_y), separator, font=font15, fill=text_color)
                draw.text((separator_x, value_y), separator, font=font15, fill=text_color)
                current_x += separator_width + spacing

    else:
        global news_titles, last_news_fetch_time

        current_time = time.time()
        if not news_titles or (current_time - last_news_fetch_time) > NEWS_FETCH_INTERVAL:
            RSS_URL = pick_random_news_feed()
            feed = feedparser.parse(RSS_URL)
            news_titles = [entry.get("title", "No Title").upper() for entry in feed.entries][:5]
            if not news_titles:
                news_titles = ["No news available"]
            last_news_fetch_time = current_time
    
        if news_titles:
            index = int(current_time / 10) % len(news_titles)
            title = news_titles[index]
        else:
            title = "No news available"
    
        news_y_start = 76
        x_start = 60
        max_width = 190
        max_lines = 2
    
        words = title.split()
        lines = []
        line = ""
        for w in words:
            test_line = line + " " + w if line else w
            bbox = draw.textbbox((0, 0), test_line, font=NewsFont)
            line_width = bbox[2] - bbox[0]
            if line_width > max_width:
                lines.append(line)
                line = w
                if len(lines) == max_lines:
                    line = line.rstrip() + "…"
                    break
            else:
                line = test_line
        if line and len(lines) < max_lines:
            lines.append(line)
    
        draw.text((4, 84), "NEWS:", font=NewsFont, fill=text_color)
    
        y = news_y_start
        for l in lines:
            draw.text((x_start, y), l, font=NewsFont, fill=text_color)
            y += 14
    
            
            
        
def display_coin_data(epd, coin, coin_data, coin_price, price_change_24h, price_change_7d, price_change_30d, price_change_60d, price_change_200d, price_change_1y, cpu_temp, cpu_usage, memory_usage, show_graph=False, now=None, ath="N/A", ath_date="N/A", showing_sentiment=False):

    global current_quote

    image = Image.new('1', (epd.height, epd.width), bg_color)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, epd.height, epd.width), fill=bg_color)

    draw_header(draw, coin, coin_data, font12, screen_width=(epd.height-2))

    draw.line([(0, 14), (epd.height, 14)], fill=text_color, width=1)
    
    holdings_usd = 15_000

    if holdings_usd > 0 and holdings_usd < 1_000:
        symbols  = 1
    elif holdings_usd >= 1_000 and holdings_usd < 10_000:
        symbols  = 2
    elif holdings_usd >= 10_000 and holdings_usd < 100_000:
        symbols  = 3
    elif holdings_usd >= 100_000 and holdings_usd < 1_000_000:
        symbols  = 4
    else:
        symbols = 5    
    symbols = min(symbols, 5)  
    draw.text((5, 15), f"{username}> {'$ ' * symbols}", font=font12, fill=text_color)

    toggle_display(draw, image, coin, coin_data, current_quote)
    toggle_bottom_display(draw, image, coin, coin_data, epd)
    

    if coin['format'] > 10:
        font = font18
    elif coin['format'] > 8:
        font = font20    
    elif coin['format'] > 6:
        font = font22
    else:
        font = font25
        
    
    Price_text = f"${coin_data['current_price']:,.{coin['format']}f}"
    text_width = draw.textbbox((0, 0), Price_text, font=font)[2]
    x = 240 - text_width
    draw.text((x, 16), Price_text, font=font, fill=text_color)
    
    draw.line([(0, 108), (epd.height, 108)], fill=text_color, width=1)

    draw_footer(draw, coin, coin_data, ath, ath_date, font12, screen_width=(epd.height-2))

    if show_graph:
        historical_prices = fetch_historical_prices_with_cache(coin['id'])
        plot_path = plot_prices(coin['id'], historical_prices, dark_mode=dark_mode)
        plot_image = Image.open(plot_path).convert('1')
        image.paste(plot_image, (5, 35)) 

    else:
        if myface:
            draw.text((3, 28), myface[0], font=face32, fill=text_color)

    image = image.rotate(screen_rotate)
    epd.displayPartial(epd.getbuffer(image))

def main():
    global coins
    
    with open("templates/coins.json", "r") as f:
        coins = json.load(f)
    coins = validate_coins(coins)
    visible_coins = [coin for coin in coins if coin.get("show", True)]
    if not visible_coins:
        visible_coins = fallback_coins

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
    last_coin_update_time = time.time()
    coin_data = None
    coin_price = None
    cpu_temp = None 
    cpu_usage = None
    memory_usage = None    

    showing_sentiment = False
    sentiment_display_start = 0
    first_run = True 
    show_graph = False
    coin_cycle_complete = False
    coin_update_interval = 90

    while True:
        current_time = time.time()
        now = datetime.now()
        
        if coin_index >= len(visible_coins):
            coin_index = 0

        coin = visible_coins[coin_index]
        coin_id = coin['id'] 
        
        if current_time - last_cpu_temp_update_time >= 3:
            cpu_temp = get_cpu_temperature()
            cpu_usage, memory_usage = get_cpu_memory_usage()
            last_cpu_temp_update_time = current_time

        if current_time - last_fetch_time >= 120:
            try:
                coin_data = fetch_coin_data_with_cache(coin_id)
                ath = coin_data.get("ath", "N/A")
                ath_date = coin_data.get("ath_date", "N/A")
                last_fetch_time = current_time
            except Exception as e:
                print(f"Error in fetching coin data: {e}")

        if current_time - last_price_fetch_time >= 300:
            try:
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

        if not show_graph and (current_time - last_face_display_time >= 60):
            show_graph = True
            last_graph_display_time = current_time
            coin_cycle_complete = False

        if show_graph:
            if current_time - last_graph_display_time >= 30:
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

            if current_time - last_face_update_time >= 3:
                if coin_data:
                    update_face(coin_data, first_run)
                    first_run = False
                last_face_update_time = current_time

            if showing_sentiment:
                if current_time - sentiment_display_start >= 10:
                    showing_sentiment = False
                    last_quote_update_time = current_time
            else:
                if current_time - last_quote_update_time >= 10:
                    showing_sentiment = True
                    sentiment_display_start = current_time 
                    current_quote = get_new_quotes()

            if not show_graph and not showing_sentiment and current_time - last_quote_update_time >= 10:
                coin_cycle_complete = True

        if coin_cycle_complete or (current_time - last_coin_update_time >= coin_update_interval):
            visible_coins = [coin for coin in coins if coin.get("show", True)]    
            if not visible_coins:
                Fallback_length = len(fallback_coins)
                random_coin = random.choice(range(Fallback_length))
                visible_coins = [fallback_coins[random_coin]]
                print(f"Displaying fallback coin: {fallback_coins[random_coin]['name']} ({fallback_coins[random_coin]['display']}).")
                print(f"Visit http://{host_ip}:5000 to manage your coins.")
                
            coin_index = (coin_index + 1) % len(visible_coins)
            last_coin_update_time = current_time
            coin_cycle_complete = False

            coin = visible_coins[coin_index]
            coin_id = coin['id']
            try:
                coin_data = fetch_coin_data_with_cache(coin_id)
                ath = coin_data.get("ath", "N/A")
                ath_date = coin_data.get("ath_date", "N/A")
                last_fetch_time = current_time
            except Exception as e:
                print(f"Error in fetching coin data: {e}")

            try:
                coin_price = coin_data.get('current_price')
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

            first_run = True 

        time.sleep(refresh_rate)

if __name__ == "__main__":
    main()
