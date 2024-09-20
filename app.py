from flask import Flask
from flask import render_template
import requests
import requests_cache
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

import database

app = Flask(__name__)

load_dotenv()

# Get the API key from the environment variable
api_key = os.getenv("api_key")

# Set the proxy parameters
proxy_params = {
    "api_key": api_key,
    "url": "https://www.alko.fi/tuotteet/000706/Jaloviina-/",
}

# request cache to not call api all the time, expires after 1 hour
requests_cache.install_cache("cache_name", expire_after=3600)

# get request
response = requests.get(
    url="https://proxy.scrapeops.io/v1/",
    params=urlencode(proxy_params),
    timeout=120,
)

# use beautifulsoup to parse raw html
soup = BeautifulSoup(response.content, "html.parser")
# find class that houses the price
price_container = soup.find(
    class_="js-price-container price-wrapper price module-price"
)
# get aria label using slice
hinta = str(price_container)[18:23]
hinta = float(hinta)

@app.route("/")
def hello_world():
    database.insert_price(hinta)
    prices = database.get_all_clean()
    return render_template("index.html", hinta=hinta, prices=prices)
