import os

import requests


class XChangeApi:

    def __init__(self):
        self._base_api_url = os.environ.get('X_CHANGE_URL')

    def czk_rates(self):
        return requests.get(url=f"{self._base_api_url}").json()
