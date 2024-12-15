import asyncio

import aiohttp

from api.logg import setup_server_logger
from push_notification.firebase_base import FirebaseBase


class UpdateCurrency(FirebaseBase):
    logger = setup_server_logger()

    async def fetch_data(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.server_url}/api/available-currencies", ssl=False) as response:
                self.logger.info(f"GET currencies '{response.url}' with status '{response.status}'")
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"Failed to fetch data: {response.status}")

    async def update_currency_data(self, currency, max_retries=5):
        retries = 0
        while retries < max_retries:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/api/rates/{currency}", ssl=False) as response:
                    if response.status == 200:
                        self.logger.info(currency)
                        return await response.json()
                    else:
                        retries += 1
                        self.logger.info(
                            f"Server error ({response.status}) for currency {currency}, retrying {retries}/{max_retries}...")
                        await asyncio.sleep(1)  # Optional: wait for a second before retrying
        self.logger.info(f"Exceeded maximum retries for currency {currency}")

    async def main(self):
        try:
            response = await self.fetch_data()
            if response is not None:
                previous_doc = self.database.collection("api_data").document("previous")
                self.logger.info(f"previous document: '{previous_doc.get()}'")

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
                self.logger.info(f"updated current document: '{current_doc.get()}'")
            else:
                print("No data to process")
        except Exception as e:
            print(f"Error during API call: {e}")
