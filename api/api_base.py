import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


class ApiBase:
    def __init__(self):
        session = requests.Session()

        retries = Retry(
            total=5,
            backoff_factor=3,
            status_forcelist=[400, 401, 402, 403, 404, 500, 501, 502],
        )

        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        self.request = session
