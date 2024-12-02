import sys
import os
import json
import time
import requests
import subprocess
import socket
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from waveshare_epd import epd2in13_V3
from PIL import Image, ImageDraw, ImageFont
import psutil

#################################
##  ADD NAME FOR YOUR GOTCHI!  ##
#################################
username = "frogCaller"
# Screen rotation
screen_rotate = 180

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

coins = [
    {"id": "bitcoin", "name": "bitcoin", "display": "BTC", "format": 0},
    {"id": "ethereum", "name": "ethereum", "display": "ETH", "format": 2},
    {"id": "dogecoin", "name": "dogecoin", "display": "DOGE", "format": 3},
    {"id": "litecoin", "name": "litecoin", "display": "LTC", "format": 2},
    {"id": "verus-coin", "name": "verus-coin", "display": "VRSC", "format": 2}
]

data_directory = "Data"
if not os.path.exists(data_directory):
    os.makedirs(data_directory)

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
font20 = ImageFont.truetype('Fonts/Font.ttc', 20)
font22 = ImageFont.truetype('Fonts/Font.ttc', 22)
font25 = ImageFont.truetype('Fonts/Font.ttc', 25)
font30 = ImageFont.truetype('Fonts/Font.ttc', 30)
face32 = ImageFont.truetype(('Fonts/DejaVuSansMono.ttf'), 32)


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
    num = float(num)
    if num >= 1_000_000_000_000_000:
        return f"{num / 1_000_000_000_000_000:.1f} Qd"
    if num >= 1_000_000_000_000:
        return f"{num / 1_000_000_000_000:.1f} T"
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f} B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f} M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f} K"
    else:
        return f"{num:.1f}"
      

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
    coin_graph = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={7}"
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

def plot_prices(coin_id, prices):
    top_left_x, top_left_y = 5, 30
    bottom_right_x, bottom_right_y = 145, 75

    width_pixels = bottom_right_x - top_left_x
    height_pixels = bottom_right_y - top_left_y

    dpi = 100
    width_inches = width_pixels / dpi
    height_inches = height_pixels / dpi

    plt.figure(figsize=(width_inches, height_inches))
    ax = plt.gca()
    ax.plot(prices, color='black')
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
    coin_text = f"{coin['display']}"
    rank_text = f"RANK: {coin_data['market_cap_rank']}"
    time_text = datetime.now().strftime("%-I:%M %p")

    coin_text_width = draw.textbbox((0, 0), coin_text, font=font)[2]
    rank_text_width = draw.textbbox((0, 0), rank_text, font=font)[2]
    time_text_width = draw.textbbox((0, 0), time_text, font=font)[2]

    total_text_width = coin_text_width + rank_text_width + time_text_width
    remaining_space = screen_width - total_text_width
    gap_between_texts = remaining_space // 2

    draw.text((2, 0), coin_text, font=font, fill=0)

    rank_x_position = 2 + coin_text_width + gap_between_texts
    draw.text((rank_x_position, 0), rank_text, font=font, fill=0)

    time_x_position = rank_x_position + rank_text_width + gap_between_texts
    draw.text((time_x_position, 0), time_text, font=font, fill=0)
    
    
def draw_footer(draw, coin, coin_data, ath, ath_date, font, screen_width=250):
    formatted_ath_date = format_ath_date(ath_date)
    
    ath_text = f"ATH:   ${ath:,.{coin['format']}f}"
    date_text = formatted_ath_date
    percentage_text = f"{coin_data['percentage_change_from_ath']:.2f} %"

    ath_text_width = draw.textbbox((0, 0), ath_text, font=font)[2]
    date_text_width = draw.textbbox((0, 0), date_text, font=font)[2]
    percentage_text_width = draw.textbbox((0, 0), percentage_text, font=font)[2]

    x_ath = 5

    x_percentage = screen_width - percentage_text_width - 5

    x_date = (x_ath + ath_text_width + x_percentage - date_text_width) // 2

    draw.text((x_ath, 110), ath_text, font=font, fill=0)
    draw.text((x_date, 110), date_text, font=font, fill=0)
    draw.text((x_percentage, 110), percentage_text, font=font, fill=0)
  
def draw_line_graph(draw, image, coin_data, line_y, line_width, time_period_label, low_key, high_key, current_key, coin, font, total_width=252):
    line_x = (total_width - line_width) // 2

    draw.line([(line_x, line_y), (line_x + line_width, line_y)], fill=0, width=2)

    for i in range(1, 4):
        tick_x = line_x + (i * (line_width // 4))
        draw.line([(tick_x, line_y - 5), (tick_x, line_y + 5)], fill=0, width=1)

    low_value = float(coin_data.get(low_key, 0))
    high_value = float(coin_data.get(high_key, 0))
    current_value = float(coin_data.get(current_key, 0))

    if high_value > low_value:
        price_position = (current_value - low_value) / (high_value - low_value)
        circle_x = line_x + int(line_width * price_position)
        circle_radius = 5

        draw.ellipse([(circle_x - circle_radius, line_y - circle_radius), 
                      (circle_x + circle_radius, line_y + circle_radius)], outline=0, fill=0)

        current_price_text = f"${current_value:,.{coin['format']}f}"
        text_width = draw.textbbox((0, 0), current_price_text, font=font)[2]
        text_x = circle_x - text_width // 2
        draw.text((text_x, line_y - 21), current_price_text, font=font, fill=0)

    # Display the low and high prices at the start and end of the line (move them above the line)
    low_price_text = "24L"#f"${low_value:,.{coin['format']}f}"
    high_price_text = "24H"#f"${high_value:,.{coin['format']}f}"

    draw.text((line_x - 27, line_y - 9), low_price_text, font=font, fill=0)

    draw.text((line_x + line_width + 5, line_y - 10), high_price_text, font=font, fill=0)

    # Display the label for the time period (e.g., 24H, 7D, etc.) further above
    #draw.text((5, line_y - 20), time_period_label, font=font, fill=0)
  

def toggle_display(draw, image, coin, coin_data, current_quote, switch_interval=10):
    current_time = time.time()
    total_quotes = len(quotes_list) 
    cycle_time = switch_interval * (total_quotes + 4)

    cycle_position = current_time % cycle_time

    if cycle_position < switch_interval:
        formatted_market_cap = format_large_number(coin_data['market_cap'])
        draw.text((125, 50), f"Market Cap: ${formatted_market_cap}", font=font12, fill=0)
    elif cycle_position < switch_interval * 2:
        formatted_circulation = format_large_number(coin_data['circulating_supply'])
        draw.text((125, 50), f"Circulation: {formatted_circulation}", font=font12, fill=0)
    elif cycle_position < switch_interval * 3:
        formatted_total_supply = format_large_number(coin_data['total_supply'])
        draw.text((125, 50), f"Total Supply: {formatted_total_supply}", font=font12, fill=0)
    elif cycle_position < switch_interval * 4:
        draw.text((125, 45), f"High: ${coin_data['high_24h']:,.{coin['format']}f}", font=font12, fill=0)
        draw.text((125, 60), f"Low: ${coin_data['low_24h']:,.{coin['format']}f}", font=font12, fill=0)
    else:
        quote_index = int((cycle_position - switch_interval * 2) // switch_interval)
        current_quote = quotes_list[quote_index % total_quotes]
        draw.text((125, 50), current_quote, font=font12, fill=0)
        
        
def toggle_bottom_display(draw, image, coin, coin_data, epd, switch_interval=30):
    current_time = time.time()
    cycle_position = current_time % (3 * switch_interval)

    if cycle_position < switch_interval:
        line_y = 95
        line_width = 196
        total_width = 252  
        line_x = (total_width - line_width) // 2

        draw.line([(line_x, line_y), (line_x + line_width, line_y)], fill=0, width=2)

        for i in range(1, 4):
            tick_x = line_x + (i * (line_width // 4))
            draw.line([(tick_x, line_y - 5), (tick_x, line_y + 5)], fill=0, width=1)

        up_percentage = coin_data.get('sentiment_votes_up_percentage', "N/A")

        if up_percentage != "N/A":
            up_percentage = float(up_percentage)
            circle_x = line_x + int(line_width * (up_percentage / 100))
            circle_radius = 5
            draw.ellipse([(circle_x - circle_radius, line_y - circle_radius), 
                          (circle_x + circle_radius, line_y + circle_radius)], outline=0, fill=0)

        if up_percentage != "N/A":
            up_percentage_text = f"{up_percentage:.1f} %"
            text_width = draw.textbbox((0, 0), up_percentage_text, font=font12)[2]
            text_x = circle_x - text_width // 2
            draw.text((text_x, line_y - 20), up_percentage_text, font=font12, fill=0)

        happy_icon = Image.open("images/happy_face.png").convert('L')
        sad_icon = Image.open("images/sad_face.png").convert('L')

        happy_icon = happy_icon.resize((18, 18)).convert('1')
        sad_icon = sad_icon.resize((18, 18)).convert('1')

        sad_x = line_x - 23
        happy_x = line_x + line_width + 7

        image.paste(happy_icon, (happy_x, line_y - 10))
        image.paste(sad_icon, (sad_x, line_y - 10))

    elif cycle_position < 2 * switch_interval:
        draw_line_graph(draw, image, coin_data, line_y=95, line_width=196, time_period_label="24H", low_key="low_24h", high_key="high_24h", current_key="current_price", coin=coin, font=font12)

    else:
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

            draw.text((label_x, label_y), label, font=font12, fill=0)
            draw.text((value_x, value_y), value, font=font12, fill=0)

            current_x += pair_width

            if i < len(label_value_pairs) - 1:
                separator_x = current_x + spacing // 2
                draw.text((separator_x, label_y), separator, font=font15, fill=0)
                draw.text((separator_x, value_y), separator, font=font15, fill=0)
                current_x += separator_width + spacing


def display_coin_data(epd, coin, coin_data, coin_price, price_change_24h, price_change_7d, price_change_30d, price_change_60d, price_change_200d, price_change_1y, cpu_temp, cpu_usage, memory_usage, show_graph=False, now=None, ath="N/A", ath_date="N/A", showing_sentiment=False):

    global current_quote

    image = Image.new('1', (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, 250, 122), fill=255)

    draw_header(draw, coin, coin_data, font12, screen_width=248)

    draw.line([(0, 13), (250, 13)], fill=0, width=1)
    
    draw.text((5, 15), f"{username}>", font=font12, fill=0)

    if myface and myface[0] == HOT:
        current_quote = "It's getting hot!"
      
    toggle_bottom_display(draw, image, coin, coin_data, epd)
    toggle_display(draw, image, coin, coin_data, current_quote)

    draw.text((125, 16), f"${coin_data['current_price']:,.{coin['format']}f}", font=font25, fill=0)
    
    draw.line([(0, 108), (250, 108)], fill=0, width=1)

    draw_footer(draw, coin, coin_data, ath, ath_date, font12, screen_width=248)

    if show_graph:
        historical_prices = fetch_historical_prices_with_cache(coin['id'])
        plot_path = plot_prices(coin['id'], historical_prices)
        plot_image = Image.open(plot_path).convert('1')
        image.paste(plot_image, (5, 35)) 

    else:
        if myface:
            draw.text((3, 28), myface[0], font=face32, fill=0)
 
    image = image.rotate(screen_rotate)
    epd.displayPartial(epd.getbuffer(image))

def main():
    coin_index = 0
    global last_price_fetch_time, last_graph_display_time
    last_face_display_time = time.time()
    
    epd = epd2in13_V3.EPD()
    epd.init()
    epd.Clear(0xFF)

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

        coin = coins[coin_index]
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
                              memory_usage, show_graph=False, now=now, ath=ath, ath_date=ath_date,
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
                    showing_sentiment = True 
                    sentiment_display_start = current_time
                    current_quote = get_new_quotes()

            if not show_graph and not showing_sentiment and current_time - last_quote_update_time >= 10:
                coin_cycle_complete = True

        if coin_cycle_complete or (current_time - last_coin_update_time >= coin_update_interval):
            coin_index = (coin_index + 1) % len(coins)
            last_coin_update_time = current_time
            coin_cycle_complete = False

            coin = coins[coin_index]
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

        time.sleep(3)

if __name__ == "__main__":
    main()
    
