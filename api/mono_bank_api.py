import os

import requests

from api.api_base import ApiBase


class MonoBankApi(ApiBase):

    def __init__(self):
        super().__init__()
        self._base_api_url = os.environ.get('MONO_BANK_URL')

    def uah_rates(self):
        return self.request.get(url=f"{self._base_api_url}").json()
