import asyncio

import aiohttp

from push_notification.firebase_base import FirebaseBase


class UpdateCurrency(FirebaseBase):

    async def fetch_data(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.server_url}/api/available-currencies", ssl=False) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Failed to fetch data: {response.status}")
                    return None

    async def update_currency_data(self, currency, max_retries=5):
        retries = 0
        while retries < max_retries:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/api/rates/{currency}", ssl=False) as response:
                    if response.status == 200:
                        first_result = await response.json()

                        for result in first_result:
                            async with session.get(
                                    f"{self.server_url}/api/rates/yearly?buy={currency}&sell={result['target']}",
                                    ssl=False) as response2:
                                if response2.status == 200:
                                    first_result["yearly"] = await response2.json()

                        print(currency)
                        return
                    else:
                        retries += 1
                        print(
                            f"Server error ({response.status}) for currency {currency}, retrying {retries}/{max_retries}...")
                        await asyncio.sleep(1)  # Optional: wait for a second before retrying
        print(f"Exceeded maximum retries for currency {currency}")
        return None

    async def main(self):
        try:
            response = await self.fetch_data()
            if response is not None:
                previous_doc = self.database.collection("api_data").document("previous")
                current_doc = self.database.collection("api_data").document("current")

                previous_exists = previous_doc.get()
                if previous_exists.exists:
                    previous_doc.set(current_doc.get().to_dict())
                else:
                    all_curs = {currency: currency for currency in response["available_currencies"]}
                    previous_doc.create(all_curs)
                    current_doc.create(all_curs)

                tasks = []
                for currency in response["available_currencies"]:
                    tasks.append(asyncio.ensure_future(self.update_currency_data(currency)))

                results = await asyncio.gather(*tasks)

                updates = {currency: result for currency, result in zip(response["available_currencies"], results) if
                           result is not None}
                current_doc.update(updates)
            else:
                print("No data to process")
        except Exception as e:
            print(f"Error during API call: {e}")
