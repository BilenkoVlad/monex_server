import os

from api.api_base import ApiBase


class XChangeApi(ApiBase):

    def __init__(self):
        super().__init__()
        self._base_api_url = os.environ.get('X_CHANGE_URL')

    def czk_rates(self):
        return self.request.get(url=f"{self._base_api_url}").json()
