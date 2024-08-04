import os

from api.api_base import ApiBase


class WiseApi(ApiBase):

    def __init__(self, sell, buy):
        super().__init__()
        self._header = {
            "Authorization": f"Basic {os.environ.get('WISE_BEARER_TOKEN')}"
        }
        self._base_api_url = os.environ.get('WISE_API_URL')
        self._base_wise_url = os.environ.get('WISE_BASE_URL')
        self._sell = sell
        self._buy = buy

    def current_curs(self):
        return self.request.get(
            url=f"{self._base_api_url}?source={self._sell}&target={self._buy}",
            headers=self._header).json()

    def monthly_range(self):
        return self.request.get(
            url=f"{self._base_wise_url}?source={self._sell}&target={self._buy}&length=30&resolution=hourly&unit=day").json()

    def yearly_range(self):
        return self.request.get(
            url=f"{self._base_wise_url}?source={self._sell}&target={self._buy}&length=1&resolution=daily&unit=year").json()
