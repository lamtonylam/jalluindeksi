from flask import Flask
from flask import Response
from flask import render_template
import requests
import requests_cache
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import io

# matplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import database

from flask_apscheduler import APScheduler

app = Flask(__name__)
scheduler = APScheduler()

load_dotenv()

# Get the API key from the environment variable
api_key = os.getenv("api_key")

# Set the proxy parameters
proxy_params = {
    "api_key": api_key,
    "url": "https://www.alko.fi/tuotteet/000706/Jaloviina-/",
}

# request cache to not call api all the time, expires after 1 hour
requests_cache.install_cache("cache_name", expire_after=43200)

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


# run price check every 12 hours
@scheduler.task("interval", id="do_job_1", seconds=43200, misfire_grace_time=900)
# function to check price daily and insert into database if changed
def price_check_daily():
    database.insert_price(hinta)
    print("checked price")


scheduler.start()


@app.route("/")
def hello_world():
    prices = database.get_all_clean()
    return render_template("index.html", hinta=hinta, prices=prices)


def create_figure():
    fig = Figure()
    ax = fig.subplots()
    prices_data = database.get_all_clean()
    prices = [item["hinta"] for item in prices_data]
    dates = [item["kirjattu tietokantaan"][0:11] for item in prices_data]
    ax.plot(dates, prices)
    return fig


@app.route("/graph")
def graph():
    fig = create_figure()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/jpeg")


if __name__ == "__main__":
    app.run()
