import requests


class WiseApi:
    def __init__(self, sell, buy):
        self._header = {
            "Authorization": "Basic OGNhN2FlMjUtOTNjNS00MmFlLThhYjQtMzlkZTFlOTQzZDEwOjliN2UzNmZkLWRjYjgtNDEwZS1hYzc3LTQ5NGRmYmEyZGJjZA=="
        }
        self._base_api_url = "https://api.wise.com/v1/rates"
        self._base_wise_url = "https://wise.com/rates/history+live"
        self._sell = sell
        self._buy = buy

    def current_curs(self):
        return requests.get(
            url=f"{self._base_api_url}?source={self._sell}&target={self._buy}",
            headers=self._header).json()

    def monthly_range(self):
        return requests.get(
            url=f"{self._base_wise_url}?source={self._sell}&target={self._buy}&length=30&resolution=hourly&unit=day").json()
