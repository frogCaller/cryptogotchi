from flask import Flask, render_template, request, jsonify, redirect, url_for, stream_with_context, Response
import json
import os
import socket
import psutil
import random
import subprocess
import time
import signal
import sys
import yaml
import base64
import threading

app = Flask(__name__)

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

    if "Cryptogotchi Settings" not in config:
        config["Cryptogotchi Settings"] = {}

    if "Cryptogotchi Settings" in new_data:
        config["Cryptogotchi Settings"].update(new_data["Cryptogotchi Settings"])


    ordered_config = {
        "Cryptogotchi Settings": {
            "username": config["Cryptogotchi Settings"].get("username", ""),
            "dark_mode": config["Cryptogotchi Settings"].get("dark_mode", False),
            "screen_rotation": config["Cryptogotchi Settings"].get("screen_rotation", 0),
            "refresh_rate": config["Cryptogotchi Settings"].get("refresh_rate", 3),
            "show_faces": config["Cryptogotchi Settings"].get("show_faces", True),
            "graph_history": config["Cryptogotchi Settings"].get("graph_history", 1),
        },
    }

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
        new_data = request.json
        config = load_config()

        if "Cryptogotchi Settings" in new_data:
            config["Cryptogotchi Settings"].update(new_data["Cryptogotchi Settings"])

        with open(CONFIG_FILE, "w") as file:
            yaml.dump(config, file, default_flow_style=False, sort_keys=False)

        return jsonify({"message": "Config updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


default_coins = [
    {"id": "bitcoin", "name": "Bitcoin", "display": "BTC", "format": 0, "show": True},
    {"id": "dogecoin", "name": "Dogecoin", "display": "DOGE", "format": 3, "show": True},
    {"id": "verus-coin", "name": "Verus Coin", "display": "VRSC", "format": 2, "show": True},
    {"id": "ethereum", "name": "Ethereum", "display": "ETH", "format": 2, "show": True}
]


def load_coins():
    if os.path.exists(coins_file):
        with open(coins_file, "r") as f:
            saved_coins = json.load(f)

        merged_coins = []
        default_ids = {coin["id"] for coin in default_coins}

        for saved_coin in saved_coins:
            default_coin = next((coin for coin in default_coins if coin["id"] == saved_coin["id"]), {})
            merged_coin = {**default_coin, **saved_coin}
            merged_coins.append(merged_coin)

        saved_ids = {coin["id"] for coin in saved_coins}
        for default_coin in default_coins:
            if default_coin["id"] not in saved_ids:
                merged_coins.append(default_coin)

        return merged_coins
    return default_coins

def save_coins(coins):
    with open(coins_file, "w") as f:
        json.dump(coins, f, indent=4)

def update_coin_list():
    global last_update_time

    current_time = time.time()
    if current_time - last_update_time >= 300:
        print("Updating coin list...")
        subprocess.run(["python3", "updateList.py"])
        last_update_time = current_time
    else:
        print(f"Skipping update. {int(300 - (current_time - last_update_time))} seconds remaining until next update.")


def run_update_coin_list():
    update_thread = threading.Thread(target=update_coin_list)
    update_thread.daemon = True
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
                coin["show"] = show
                break

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


@app.route("/system-info", methods=["GET"])
def system_info():
    info = get_system_info()
    return jsonify(info)



@app.route("/")
def crypto():
    get_system_info()
    coins = load_coins()
    
    run_update_coin_list()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"coins": coins})

    return render_template("crypto.html", coins=coins)


@app.route("/start-script", methods=["POST"])
def start_script():
    data = request.json
    script = data.get("script")
    if script and os.path.exists(script):
        subprocess.Popen(["python3", script])
        return jsonify({"status": "success", "message": f"Switched to script: {script}"})
    return jsonify({"status": "error", "message": "Script not found"}), 400
  

def kill_cryptogotchi_on_exit():
    for proc in psutil.process_iter(['pid', 'cmdline']):
        if proc.info['cmdline'] and "cryptogotchi.py" in " ".join(proc.info['cmdline']):
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception as e:
                print(f"Failed to stop cryptogotchi.py: {e}")
                
def signal_handler(sig, frame):
    kill_cryptogotchi_on_exit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)   # Handle Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Handle kill command


def manage_scripts(kill_scripts=None, start_script=None, script_args={}):
    kill_scripts = kill_scripts or []
    response = {"killed_scripts": [], "not_running": [], "started_script": None}

    # Kill scripts
    for script in kill_scripts:
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

    time.sleep(1)

    if start_script:
        try:
            args = [f"--{key}={value}" for key, value in script_args.items()]
            subprocess.Popen(["python3", start_script] + args, start_new_session=True)
            response["started_script"] = start_script
        except Exception as e:
            response["started_script"] = f"Failed to start: {e}"

    return response
  
@app.route("/manage-script", methods=["POST"])
def manage_script_route():
    data = request.json
    result = manage_scripts(
        kill_scripts=data.get("kill_scripts", []),
        start_script=data.get("start_script"),
        script_args=data.get("script_args", {})
    )
    return jsonify({"success": True, "details": result})


if __name__ == "__main__":
    if not os.path.exists(coins_file):
        save_coins(default_coins)
        print("Created coins.json with default coins.")
    manage_scripts(kill_scripts=["cryptogotchi.py"], start_script="cryptogotchi.py")
    app.run(host="0.0.0.0", port=5000)
