import os

import requests
import requests_cache


class MonoBankApi:

    def __init__(self):
        self._base_api_url = os.environ.get('MONO_BANK_URL')

    def uah_rates(self):
        requests_cache.install_cache('mono_cache', expire_after=300)
        return requests.get(url=f"{self._base_api_url}").json()
