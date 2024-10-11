from flask import Flask, Response, render_template
import requests
import requests_cache
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import io
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib import rcParams
import database
from flask_apscheduler import APScheduler
from datetime import datetime

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


def fetch_price():
    # request cache to not call api all the time, expires after 3 hours
    requests_cache.install_cache("cache_name", expire_after=10800)

    # get request
    response = requests.get(
        url="https://proxy.scrapeops.io/v1/",
        params=urlencode(proxy_params),
        timeout=120,
    )

    # Check if the response was served from the cache
    if response.from_cache:
        print("Response served from cache")
    else:
        print("Real request made")

    # use beautifulsoup to parse raw html
    soup = BeautifulSoup(response.content, "html.parser")
    # find class that houses the price
    price_container = soup.find(
        class_="js-price-container price-wrapper price module-price"
    )
    # get aria label using slice
    hinta = str(price_container)[18:23]
    hinta = float(hinta)
    return hinta


@scheduler.task("interval", id="do_job_1", seconds=60, misfire_grace_time=900)
def price_check_daily():
    hinta = fetch_price()
    database.insert_price(hinta)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Checked price at {current_time}")


scheduler.start()


@app.route("/")
def hello_world():
    prices = database.get_all_clean(eurosign=True)
    hinta = fetch_price()
    return render_template("index.html", hinta=hinta, prices=prices)


def create_figure():
    fig = Figure()
    ax = fig.subplots()
    prices_data = database.get_all_clean()
    prices = [item["hinta"] for item in prices_data]
    prices = [float(item) for item in prices]
    dates = [item["kirjattu tietokantaan"][0:11] for item in prices_data]
    ax.plot(dates, prices)

    ax.yaxis.set_major_formatter("{x:1.2f} €")
    
    ax.scatter(dates, prices, color='red', marker='x')

    rcParams["axes.autolimit_mode"] = "round_numbers"

    return fig


@app.route("/graph")
def graph():
    fig = create_figure()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/jpeg")


if __name__ == "__main__":
    app.run()
