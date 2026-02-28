from dome_api_sdk import DomeClient
from dotenv import load_dotenv
import os

load_dotenv()

dome = DomeClient({"api_key": os.getenv("DOME_API_KEY")})

market_price = dome.polymarket.markets.get_market_price({
    "token_id": "98250445447699368679516529207365255018790721464590833209064266254238063117329"
})      
print(f"Market Price: {market_price.price}")

print("\n\n"+"*"*100+"\n\n")

import requests

url = "https://api.domeapi.io/v1/polymarket/markets?limit=10"

# Added headers with API key for authentication
headers = {
    "x-api-key": os.getenv("DOME_API_KEY")
}

response = requests.get(url, headers=headers)
print(response.text)
print("\n\n"+"*"*100+"\n\n")

import requests

url = "https://api.domeapi.io/v1/polymarket/events?include_markets=false&limit=10"
response = requests.get(url, headers=headers)
print(response.text)