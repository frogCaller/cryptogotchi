import os
import requests
import json
import math

# Base URL to fetch data from
base_url = "https://api.coingecko.com/api/v3/coins/markets"
coins_file = os.path.join(os.path.dirname(__file__), "templates", "coins.json")
def calculate_format(price):
    if price >= 10000:
        return 0
    if price >= 1:
        return 2
    elif price > 0:
        # Count number of digits after the leading zeros
        decimal_places = -math.floor(math.log10(price))
        # Add 2 more significant digits after the zeros
        return decimal_places + 2
    else:
        return 6  # Default for very small prices or edge cases

def format_price(price):
    return f"{price:,.{calculate_format(price)}f}"

def fetch_coins(page):
    try:
        # Construct the URL with the specified page
        url = f"{base_url}?vs_currency=usd&order=market_cap_desc&per_page=250&page={page}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Transform the data into the desired format
        coins = []
        for coin in data:
            coins.append({
                "id": coin["id"],
                "name": coin["name"],
                "display": coin["symbol"].upper(),
                "rank": coin["market_cap_rank"],  # Include the rank
                "price": format_price(coin["current_price"]),
                "format": calculate_format(coin["current_price"]),
                "show": False
            })
        return coins

    except requests.exceptions.RequestException as e:
        print(f"Error fetching coins: {e}")
        return []

def update_coins(local_coins, fetched_coins):
    """
    Update the local coins list with data from fetched coins.
    Preserve the 'show' and 'favorite' toggles for existing coins.
    Remove unranked coins unless they are marked as favorite.
    """
    # Convert local coins list to a dictionary for quick lookup
    local_coins_dict = {coin['id']: coin for coin in local_coins}

    # Temporary list to store updated coins
    updated_coins = []

    for fetched_coin in fetched_coins:
        if fetched_coin['id'] in local_coins_dict:
            # Update fields but keep the 'show' and 'favorite' state intact
            existing_coin = local_coins_dict[fetched_coin['id']]
            existing_coin.update({
                "rank": fetched_coin["rank"],
                "price": fetched_coin["price"],
                "format": fetched_coin["format"]
            })
            updated_coins.append(existing_coin)
        else:
            # Add new coin to the updated list
            updated_coins.append(fetched_coin)

    # Remove unranked coins unless they are favorited
    updated_coins = [
        coin for coin in updated_coins
        if coin["rank"] is not None or coin["favorite"]
    ]

    # Sort the coins by rank (place unranked coins at the end)
    updated_coins.sort(key=lambda x: x["rank"] if x["rank"] else float('inf'))

    # Resolve duplicate ranks
    resolve_duplicate_ranks(updated_coins)

    return updated_coins


def resolve_duplicate_ranks(coins):
    rank_count = {}
    for coin in coins:
        rank = coin.get("rank")
        if rank:
            rank_count[rank] = rank_count.get(rank, 0) + 1

    for coin in coins:
        rank = coin.get("rank")
        if rank and rank_count[rank] > 1:
            coin["rank"] = None  # Mark as unranked for duplicates

    return coins

# Main logic to fetch and update coins
if __name__ == "__main__":
    try:
        # Load the local coins list from a JSON file
        try:
            with open(coins_file, "r") as file:
                local_coins = json.load(file)
        except FileNotFoundError:
            local_coins = []

        # Fetch coins from API
        fetched_coins = fetch_coins(1) + fetch_coins(2)

        # Update the local coins with fetched data
        local_coins = update_coins(local_coins, fetched_coins)

        # Save the updated coins list back to the JSON file
        with open(coins_file, "w") as file:
            json.dump(local_coins, file, indent=4)

        print("Coins updated successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
