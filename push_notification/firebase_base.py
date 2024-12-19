import json
import os

import dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import CollectionReference, DocumentReference

from api.logg import setup_server_logger

dotenv.load_dotenv()


class FirebaseBase:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FirebaseBase, cls).__new__(cls, *args, **kwargs)
            remote = os.getenv("FIREBASE_SERVICE_ACCOUNT")
            service_account_file = f'{os.path.dirname(os.path.abspath(__file__))}/secret.json'

            if remote is not None:
                with open(service_account_file, 'w') as json_file:
                    json.dump(json.loads(remote), json_file, indent=4)

            creds = credentials.Certificate(service_account_file)
            firebase_admin.initialize_app(creds)
        return cls._instance

    def __init__(self):
        self.user_doc = None
        self.logger = setup_server_logger()
        self.database = firestore.client()
        self.server_url = os.environ.get('SERVER_URL')

        self.api_data = "api_data"
        self.api_data_collection: CollectionReference = self.database.collection(self.api_data)

        self.users = "users"
        self.users_collection: CollectionReference = self.database.collection(self.users)

        self.notifications = "notifications"
        self.notifications_collection: CollectionReference = self.database.collection(self.notifications)

        self.api_data_collection_local = {}
        self.users_collection_local = {}
        self.users_to_delete = []

        self.logger.info("FirebaseBase is initiated")

    def read_collections(self):
        self.logger.info("Read api_data collection")
        a_data_c = self.database.collection(self.api_data).get()
        for api_data_collection in a_data_c:
            self.api_data_collection_local[api_data_collection.id] = api_data_collection.to_dict()

        self.logger.info("Read users collection")
        u_c = self.database.collection(self.users).list_documents()
        for user_collection in u_c:
            self.users_collection_local[user_collection.id] = user_collection.get().to_dict()

    def set_user_doc(self, token: str):
        self.user_doc: DocumentReference = self.users_collection.document(token)

    def delete_user(self, token: str):
        user_doc: DocumentReference = self.users_collection.document(token)
        user_doc.delete()
        self.logger.info(f"Deleting user with token '{token}'")
        if user_doc.get().exists:
            self.logger.warning(f"User with token '{token}' was not deleted")

    def delete_broken_collection(self, token: str):
        user_doc: DocumentReference = self.users_collection.document(token)
        if not user_doc.get().exists:
            self.logger.info("Deleting broken user")
            notifications: list[DocumentReference] = list(self.notifications_collection.list_documents())
            if len(notifications):
                for notif in notifications:
                    notif.delete()
                self.logger.info("Notifications are cleared")
            user_doc.delete()
            self.logger.info(f"Broken user with token '{token}' is deleted")
