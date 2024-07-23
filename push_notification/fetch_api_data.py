import asyncio
import json
import os
from datetime import datetime

import aiohttp
import dotenv
import firebase_admin
from firebase_admin import credentials, firestore, messaging

dotenv.load_dotenv()


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
    remote = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    service_account_file = f'{os.path.dirname(os.path.abspath(__file__))}/secret.json'

    if remote is not None:
        with open(service_account_file, 'w') as json_file:
            json.dump(json.loads(remote), json_file, indent=4)

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

            for user in db.collection("users").get():
                print(user.id)
                print(user.to_dict())
                for key in user.to_dict().keys():
                    if key != "platform":
                        for currency in user.to_dict()[key]:
                            if currency["follow"]:
                                print(f"source = {key}, target = {currency}")

                                target = currency["target"]
                                source = currency["source"]
                                current_rate = 0
                                previous_rate = 0

                                for current in db.collection("api_data").document("current").get().to_dict().keys():
                                    if current == source:
                                        for val in db.collection("api_data").document("current").get().to_dict()[
                                            current]:
                                            if val["target"] == target:
                                                current_rate = val["rate"]

                                for previous in db.collection("api_data").document("previous").get().to_dict().keys():
                                    if previous == source:
                                        for val in db.collection("api_data").document("current").get().to_dict()[
                                            previous]:
                                            if val["target"] == target:
                                                previous_rate = val["rate"]

                                if current_rate != previous_rate:
                                    a = messaging.Message(
                                        notification=messaging.Notification(
                                            title="Python",
                                            body=f"{target} currency to {source}"
                                        ),
                                        token="foaANwfD80NbjGAzOozhcv:APA91bEVR-XgFCDJiq2apFX2HIGPO3R_bZMxJU-GdKOg9pSHeg-IjoVVIm06d5tCy_cgjhfLH3VBDrcgYYMAl8Ew5dlPrLUl0egFikMHorvrbbXOBYyaN5fQeFdXmro7pivHqPUIZ3DH"
                                    )
                                    messaging.send(a)
                                print(current_rate)
                                print(previous_rate)

        else:
            print("No data to process")
    except Exception as e:
        print(f"Error during API call: {e}")


start = datetime.now()
asyncio.run(main())
finish = datetime.now()
print(finish - start)