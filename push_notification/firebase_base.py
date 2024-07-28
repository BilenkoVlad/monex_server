import json
import os

import dotenv
import firebase_admin
from firebase_admin import credentials, firestore

dotenv.load_dotenv()


class FirebaseBase:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        remote = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        service_account_file = f'{os.path.dirname(os.path.abspath(__file__))}/secret.json'

        if remote is not None:
            with open(service_account_file, 'w') as json_file:
                json.dump(json.loads(remote), json_file, indent=4)

        self.creds = credentials.Certificate(service_account_file)
        firebase_admin.initialize_app(self.creds)

        self.database = firestore.client()
        self.server_url = os.environ.get('SERVER_URL')
        self.api_data = "api_data"
        self.users = "users"
        self.notifications = "notifications"
