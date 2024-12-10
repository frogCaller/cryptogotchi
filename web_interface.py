from flask import Flask, render_template, request, jsonify, redirect, url_for, stream_with_context, Response
import json
import os
import socket
import psutil
import random
import subprocess
import time
import yaml
import base64
import threading

app = Flask(__name__)

# File to save coin settings
coins_file = os.path.join(os.path.dirname(__file__), "templates", "coins.json")
last_update_time = 0

CONFIG_FILE = "config.yaml"
DATA_DIR = os.path.join(os.getcwd(), "Data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_config():
    with open(CONFIG_FILE, "r") as file:
        config = yaml.safe_load(file)
        return config

def update_config(new_data):
    config = load_config()

    # Ensure top-level groups exist
    if "Cryptogotchi Settings" not in config:
        config["Cryptogotchi Settings"] = {}

    if "Text Settings" not in config:
        config["Text Settings"] = {}

    # Update Cryptogotchi Settings
    if "Cryptogotchi Settings" in new_data:
        config["Cryptogotchi Settings"].update(new_data["Cryptogotchi Settings"])

    # Update Text Settings
    if "Text Settings" in new_data:
        config["Text Settings"].update(new_data["Text Settings"])

    # Create ordered_config for consistent structure
    ordered_config = {
        "Cryptogotchi Settings": {
            "username": config["Cryptogotchi Settings"].get("username", ""),
            "dark_mode": config["Cryptogotchi Settings"].get("dark_mode", False),
            "screen_rotation": config["Cryptogotchi Settings"].get("screen_rotation", 0),
            "refresh_rate": config["Cryptogotchi Settings"].get("refresh_rate", 3),
            "show_faces": config["Cryptogotchi Settings"].get("show_faces", True),
            "graph_history": config["Cryptogotchi Settings"].get("graph_history", 1),
        },
        "Text Settings": {
            "text_style": config["Text Settings"].get("text_font", 1),
            "text_height": config["Text Settings"].get("text_height", 18),
            "text_alignment": config["Text Settings"].get("text_alignment", center),
            "text_justify": config["Text Settings"].get("text_justify", center),
            "dark_mode": config["Text Settings"].get("dark_mode", False),
            "screen_rotation": config["Text Settings"].get("screen_rotation", 180),
            "quote_display_duration": config["Text Settings"].get("quote_display_duration", 20),
        },
    }

    # Write updated config back to the file
    with open(CONFIG_FILE, "w") as file:
        yaml.dump(ordered_config, file, default_flow_style=False, sort_keys=False)



@app.route("/get-config", methods=["GET"])
def get_config():
    try:
        config = load_config()
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/update-config", methods=["POST"])
def update_config_route():
    try:
        new_data = request.json  # Expect a nested structure
        config = load_config()

        # Update Cryptogotchi Settings
        if "Cryptogotchi Settings" in new_data:
            config["Cryptogotchi Settings"].update(new_data["Cryptogotchi Settings"])

        # Update Text Settings
        if "Text Settings" in new_data:
            config["Text Settings"].update(new_data["Text Settings"])

        # Write back the updated config
        with open(CONFIG_FILE, "w") as file:
            yaml.dump(config, file, default_flow_style=False, sort_keys=False)

        return jsonify({"message": "Config updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Default coins list with all fields
default_coins = [
    {"id": "bitcoin", "name": "Bitcoin", "display": "BTC", "format": 0, "show": True},
    {"id": "dogecoin", "name": "Dogecoin", "display": "DOGE", "format": 3, "show": True},
    {"id": "litecoin", "name": "Litecoin", "display": "LTC", "format": 2, "show": True},
    {"id": "verus-coin", "name": "Verus Coin", "display": "VRSC", "format": 2, "show": True},
    {"id": "shiba-inu", "name": "Shiba Inu", "display": "SHIB", "format": 6, "show": True},
    {"id": "ethereum", "name": "Ethereum", "display": "ETH", "format": 2, "show": True}
]

# Load coins from JSON and merge with default values
def load_coins():
    if os.path.exists(coins_file):
        with open(coins_file, "r") as f:
            saved_coins = json.load(f)

        # Merge saved coins with default coins to ensure all fields exist
        merged_coins = []
        default_ids = {coin["id"] for coin in default_coins}

        for saved_coin in saved_coins:
            # Merge with default coin structure, prioritizing saved fields
            default_coin = next((coin for coin in default_coins if coin["id"] == saved_coin["id"]), {})
            merged_coin = {**default_coin, **saved_coin}
            merged_coins.append(merged_coin)

        # Add any missing default coins
        saved_ids = {coin["id"] for coin in saved_coins}
        for default_coin in default_coins:
            if default_coin["id"] not in saved_ids:
                merged_coins.append(default_coin)

        return merged_coins
    return default_coins

# Save coins to JSON file
def save_coins(coins):
    with open(coins_file, "w") as f:
        json.dump(coins, f, indent=4)

def update_coin_list():
    global last_update_time

    # Only update if 300 seconds have passed since the last update
    current_time = time.time()
    if current_time - last_update_time >= 360:
        subprocess.run(["python3", "updateList.py"])  # Adjust the command if needed
        last_update_time = current_time

# Function to run update_coin_list in a separate thread
def run_update_coin_list():
    update_thread = threading.Thread(target=update_coin_list)
    update_thread.daemon = True  # Daemon thread will exit when the main program exits
    update_thread.start()


@app.route("/get-coins", methods=["GET"])
def get_coins():
    if os.path.exists(coins_file):
        with open(coins_file, "r") as f:
            coins = json.load(f)
        return jsonify({"coins": coins})
    return jsonify({"coins": []}), 404


@app.route("/toggle-coin", methods=["POST"])
def toggle_coin():
    data = request.json
    coin_id = data.get("coinId")
    show = data.get("show")

    if coin_id is not None and show is not None:
        coins = load_coins()
        for coin in coins:
            if coin["id"] == coin_id:
                coin["show"] = show  # Update the "show" field
                break

        # Save updated coins back to the JSON file
        save_coins(coins)
        return jsonify({"status": "success", "message": f"Coin {coin_id} updated to {'visible' if show else 'hidden'}."})

    return jsonify({"status": "error", "message": "Invalid data"}), 400


def get_system_info():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent

        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = float(f.read()) / 1000.0
            cpu_temp = f"{temp:.1f}°C"
        except FileNotFoundError:
            cpu_temp = "N/A"

        # Storage Information
        storage_info = psutil.disk_usage('/')
        storage_total = storage_info.total / (1024 ** 3)  # Convert to GB
        storage_used = storage_info.used / (1024 ** 3)    # Convert to GB
        storage_percent = storage_info.percent

        return {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "cpu_temp": cpu_temp,
            "storage_total": f"{storage_total:.2f} GB",
            "storage_used": f"{storage_used:.2f} GB",
            "storage_percent": storage_percent
        }

    except Exception as e:
        print(f"Error fetching system info: {e}")
        return {
            "cpu_usage": "Error",
            "memory_usage": "Error",
            "cpu_temp": "Error",
            "storage_total": "Error",
            "storage_used": "Error",
            "storage_percent": "Error"
        }

@app.route('/get_server_ip', methods=['GET'])
def get_server_ip():
    import socket
    server_ip = socket.gethostbyname(socket.gethostname())
    return jsonify({"server_ip": server_ip})

@app.route("/system-info", methods=["GET"])
def system_info():
    info = get_system_info()
    return jsonify(info)

def get_wifi_status():
    try:
        # Check for network connectivity (ping Google's DNS)
        response = os.system("ping -c 1 8.8.8.8 > /dev/null 2>&1")
        if response == 0:
            return "connected"  # Wi-Fi is available
        else:
            return "disconnected"  # No Wi-Fi connection
    except:
        return "disconnected"

def load_quotes():
    with open("templates/quotes.txt", "r") as file:
        quotes = file.readlines()
    return [quote.strip() for quote in quotes if quote.strip()]


@app.route("/")
def index():
    wifi_status = get_wifi_status()
    return render_template("index.html", wifi_status=wifi_status)

@app.route("/crypto")
def crypto():
    run_update_coin_list()
    coins = load_coins()

    # If this is an AJAX request, return JSON
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"coins": coins})

    quotes = load_quotes()
    random_quote = random.choice(quotes) if quotes else "Stay positive!"
    return render_template("crypto.html", coins=coins, random_quote=random_quote)

@app.route("/draw")
def draw():
    return render_template("draw.html")

@app.route('/save_image', methods=['POST'])
def save_image():
    data = request.get_json()
    image_data = data.get("image")
    file_name = data.get("file_name", "drawing.png")  # Default to drawing.png if no name provided

    try:
        # Decode the image data and save it with the specified file name
        image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)

        save_path = os.path.join("Data", file_name)
        with open(save_path, "wb") as image_file:
            image_file.write(image_bytes)

        return jsonify({"success": True, "message": f"Image saved as {file_name}."})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error saving image: {str(e)}"})


@app.route('/display', methods=['POST'])
def display():
    try:
        # Run the Python script to display the image
        subprocess.run(["python3", "display_image.py"], check=True)
        return jsonify({"success": True, "message": "Image displayed on e-ink screen."})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "message": f"Failed to display image: {str(e)}"})

@app.route('/display-message', methods=['POST'])
def display_message():
    data = request.json
    display_type = data.get("display_type", "message")  # Default to 'message'
    font = data.get("font", 16)
    justify = data.get("justify", "left")
    vertical_align = data.get("vertical_align", "top")
    font_style = data.get("font_style", 1)
    dark_mode = data.get("dark_mode", False)
    rotate = data.get("rotate", 180)

    command = [
        "python3", "write.py",
        f"--display_type={display_type}",
        f"--font={font}",
        f"--justify={justify}",
        f"--vertical_align={vertical_align}",
        f"--font_style={font_style}",
        f"--dark_mode={dark_mode}",
        f"--rotate={rotate}"
    ]

    if display_type == "message":
        message = data.get("message", "")
        if not message:
            return jsonify({"success": False, "message": "No message provided for display_type='message'."})
        command.append(message)

    print("Running command:", " ".join(command))

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Subprocess stdout:", result.stdout)
        print("Subprocess stderr:", result.stderr)
        return jsonify({"success": True, "output": result.stdout})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/message")
def message():
    return render_template("message.html")

@app.route('/start-clock', methods=['POST'])
def start_clock():
    data = request.json
    time_format = data.get("time_format", "12")  # Default to 12-hour format
    text_height = data.get("text_height", 32)
    text_style = data.get("text_style", 1)
    dark_mode = data.get("dark_mode", False)
    screen_rotate = data.get("screen_rotate", False)
    show_seconds = data.get("show_seconds", True)

    # Construct the command
    command = [
        "python3", "time.py",
        f"--time_format={time_format}",
        f"--text_height={text_height}",
        f"--text_style={text_style}",
        f"--dark_mode={'true' if dark_mode else 'false'}",
        f"--screen_rotate={'true' if screen_rotate else 'false'}",
        f"--show_seconds={'true' if show_seconds else 'false'}"
    ]

    print("Running command:", " ".join(command))

    try:
        # Run the subprocess and capture stdout and stderr
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Subprocess stdout:", result.stdout)
        print("Subprocess stderr:", result.stderr)

        if result.returncode == 0:
            return jsonify({"success": True, "output": result.stdout})
        else:
            return jsonify({"success": False, "message": result.stderr})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/get-quote", methods=["GET"])
def get_quote():
    quotes = load_quotes()
    random_quote = random.choice(quotes)
    return jsonify({"quote": random_quote})

@app.route('/check-script-status', methods=['GET'])
def check_script_status():
    script_name = request.args.get('script', '')  # Get the script name from the query parameter
    if not script_name:
        return jsonify({'error': 'Script name not provided'}), 400

    for proc in psutil.process_iter(['name', 'cmdline']):
        if 'python' in proc.info['name'] and script_name in (proc.info['cmdline'] or []):
            return jsonify({'running': True})
    return jsonify({'running': False})

@app.route("/start-script", methods=["POST"])
def start_script():
    data = request.json
    script = data.get("script")
    if script and os.path.exists(script):
        subprocess.Popen(["python3", script])
        return jsonify({"status": "success", "message": f"Switched to script: {script}"})
    return jsonify({"status": "error", "message": "Script not found"}), 400

@app.route("/manage-script", methods=["POST"])
def manage_script():
    data = request.json
    scripts_to_kill = data.get("kill_scripts", [])  # List of scripts to kill
    start_script = data.get("start_script")  # Script to start
    script_args = data.get("script_args", {})  # Arguments for the script

    # Response messages
    response = {"killed_scripts": [], "not_running": [], "started_script": None}

    # Kill specified scripts
    for script in scripts_to_kill:
        try:
            for proc in psutil.process_iter(['pid', 'cmdline']):
                if script in " ".join(proc.info['cmdline']):
                    proc.terminate()
                    proc.wait(timeout=5)
                    response["killed_scripts"].append(script)
                    break
            else:
                response["not_running"].append(script)
        except Exception as e:
            response["not_running"].append(script)
            print(f"Error stopping {script}: {e}")

    # Ensure a small delay to avoid overlapping termination and startup
    time.sleep(1)

    # Start the specified script if provided
    if start_script:
        try:
            # Convert script arguments to command-line arguments
            args = [f"--{key}={value}" for key, value in script_args.items()]
            subprocess.Popen(["python3", start_script] + args, start_new_session=True)
            response["started_script"] = start_script
        except Exception as e:
            response["started_script"] = f"Failed to start: {str(e)}"

    return jsonify({"success": True, "details": response})




## Command line
current_working_directory = os.getcwd()

@app.route('/execute', methods=['POST'])
def execute():
    global current_working_directory
    command = request.json.get('command', '')
    if command:
        try:
            hostname = socket.gethostname()  # Get the device hostname
            username = subprocess.run('whoami', shell=True, stdout=subprocess.PIPE, text=True).stdout.strip()

            # Remove the first two directories (/home/pi)
            display_directory = "/".join(current_working_directory.split("/")[2:])

            # Handle "sudo" commands
            if command.startswith('sudo '):
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=current_working_directory,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                output = result.stdout if result.stdout else "No output."
                return jsonify({
                    "output": output,
                    "hostname": username,
                    "device": hostname,
                    "directory": current_working_directory
                })

            if command.strip() == 'ls':
                # Run the ls command in the current working directory
                result = subprocess.run(
                    'ls -F',
                    shell=True,
                    cwd=current_working_directory,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                raw_output = result.stdout if result.stdout else result.stderr
                items = []
                for item in raw_output.splitlines():
                    if item.endswith('*'):
                        items.append({'name': item.rstrip('*'), 'type': 'executable'})
                    elif item.endswith('/'):  # Folder
                        items.append({'name': item.rstrip('/'), 'type': 'folder'})
                    else:  # File
                        items.append({'name': item, 'type': 'file'})
                return jsonify({
                    "items": items,
                    "hostname": username,
                    "device": hostname,
                    "directory": display_directory
                })

            if command.startswith('cd '):
                # Handle the cd command
                target_directory = command[3:].strip()
                if target_directory == "~":  # Handle cd ~
                    target_directory = os.path.expanduser("~")
                elif target_directory == "..":  # Handle cd ..
                    target_directory = os.path.dirname(current_working_directory)
                elif not os.path.isabs(target_directory):  # Convert to absolute path if relative
                    target_directory = os.path.join(current_working_directory, target_directory)

                if os.path.isdir(target_directory):
                    current_working_directory = target_directory
                    display_directory = "/".join(current_working_directory.split("/")[2:])
                    return jsonify({
                        "output": "",
                        "hostname": username,
                        "device": hostname,
                        "directory": display_directory
                    })
                else:
                    return jsonify({
                        "output": f"cd: no such file or directory: {target_directory}",
                        "hostname": username,
                        "device": hostname,
                        "directory": display_directory
                    })

            # Handle all other commands
            result = subprocess.run(
                command,
                shell=True,
                cwd=current_working_directory,  # Execute in the updated current directory
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, #stderr=subprocess.PIPE,
                text=True
            )
            output = result.stdout if result.stdout else result.stderr
            return jsonify({
                "output": output,
                "hostname": username,
                "device": hostname,
                "directory": display_directory
            })
        except Exception as e:
            return jsonify({"output": f"Error: {str(e)}"})
    return jsonify({"output": "No command provided."})


@app.route('/autocomplete', methods=['POST'])
def autocomplete():
    global current_working_directory

    try:
        # Get the prefix from the request
        prefix = request.json.get('prefix', '')

        # List files and directories in the current working directory
        items = os.listdir(current_working_directory)

        # Filter the items based on the prefix
        matches = []
        for item in items:
            full_path = os.path.join(current_working_directory, item)
            if item.startswith(prefix):
                matches.append({
                    'name': item,
                    'type': 'folder' if os.path.isdir(full_path) else 'file'
                })

        return jsonify({"matches": matches})
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route("/clock", methods=["GET"])
def clock_page():
    return render_template("clock.html")

@app.route("/cmd", methods=["GET"])
def cmd_page():
    return render_template("cmd.html")


@app.route("/restart", methods=["POST"])
def restart():
    try:
        subprocess.run(["sudo", "reboot"], check=True)
        return jsonify({"status": "success", "message": "Restarting Raspberry Pi..."})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/shutdown", methods=["POST"])
def shutdown():
    try:
        subprocess.run(["sudo", "shutdown", "now"], check=True)
        return jsonify({"status": "success", "message": "Shutting down Raspberry Pi..."})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Initialize coins.json if it doesn't exist
    if not os.path.exists(coins_file):
        save_coins(default_coins)  # Save default coins on first run
        print("Created coins.json with default coins.")
    app.run(host="0.0.0.0", port=5000)
