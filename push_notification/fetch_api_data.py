import asyncio
import os
from datetime import datetime

import aiohttp
import firebase_admin
from firebase_admin import credentials, firestore


async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, ssl=False) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to fetch data: {response.status}")
                return None


async def update_currency_data(currency):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{os.environ.get('SERVER_URL')}/api/rates/{currency}", ssl=False) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to fetch data for currency {currency}: {response.status}")
                return None


async def main():
    service_account_file = 'push_notification/secret.json' if os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_MONEX_APP_F86C7") is None else os.getenv("FIREBASE_SERVICE_ACCOUNT_MONEX_APP_F86C7")

    cred = credentials.Certificate(service_account_file)
    firebase_admin.initialize_app(cred)

    db = firestore.client()

    url = f"{os.environ.get('SERVER_URL')}/api/available-currencies"
    try:
        response = await fetch_data(url)
        if response is not None:
            previous_doc = db.collection("api_data").document("previous")
            current_doc = db.collection("api_data").document("current")

            previous_exists = previous_doc.get()
            if previous_exists.exists:
                previous_doc.set(current_doc.get().to_dict())
            else:
                all_curs = {currency: currency for currency in response["available_currencies"]}
                previous_doc.create(all_curs)
                current_doc.create(all_curs)

            tasks = []
            for currency in response["available_currencies"]:
                tasks.append(asyncio.ensure_future(update_currency_data(currency)))

            results = await asyncio.gather(*tasks)

            updates = {currency: result for currency, result in zip(response["available_currencies"], results) if
                       result is not None}
            current_doc.update(updates)
        else:
            print("No data to process")
    except Exception as e:
        print(f"Error during API call: {e}")


start = datetime.now()
asyncio.run(main())
finish = datetime.now()
print(finish - start)