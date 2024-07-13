import os

import requests


class MonoBankApi:

    def __init__(self):
        self._base_api_url = os.environ.get('MONO_BANK_URL')

    def uah_rates(self):
        return requests.get(url=f"{self._base_api_url}").json()
