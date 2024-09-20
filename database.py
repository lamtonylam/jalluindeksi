import os
from supabase import create_client, Client
import datetime
from datetime import timedelta

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def get_all():
    response = supabase.table("jalluindex").select("hinta, created_at").execute()
    return list(response.data)


def get_all_clean():
    response = (
        supabase.table("jalluindex").select("hinta, created_at").limit(20).execute()
    )

    list_of_prices = []

    for i in response.data:

        date = datetime.datetime.strptime(i["created_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
        price_dict = {
            "hinta": f'{i["hinta"]} €',
            "kirjattu tietokantaan": date.strftime("%Y/%m/%d, %H:%M"),
        }
        list_of_prices.append(price_dict)

    return list_of_prices


def insert_price(price):
    # get all entries
    all_entries = get_all()
    # if true, that means that there are entries, check if entry to be added is same as last
    if all_entries:
        last_entry = all_entries[-1]
        last_price = last_entry["hinta"]
        # if the price is the same as the last one, do not add it to the database
        if price == last_price:
            return
        # if the price is different, add it to the database
        else:
            response = supabase.table("jalluindex").insert({"hinta": price}).execute()
    # if it is false, it means that the database is empty, so put a new entry in.
    else:
        response = supabase.table("jalluindex").insert({"hinta": price}).execute()
