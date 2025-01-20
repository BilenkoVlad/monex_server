import json
import os

import dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage
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
            firebase_admin.initialize_app(creds, {'storageBucket': 'monex2.firebasestorage.app'})
        return cls._instance

    def __init__(self):
        self.logger = setup_server_logger()
        self.database = firestore.client()
        self.bucket = storage.bucket()
        self.server_url = os.environ.get('SERVER_URL')

        self.api_data = "api_data"
        self.api_data_collection: CollectionReference = self.database.collection(self.api_data)

        self.users = "users"
        self.users_collection: CollectionReference = self.database.collection(self.users)

        self.notifications = "notifications"

        self.users_to_delete = []

        self.api_local = {}
        self.users_local = {}

        self.logger.info("FirebaseBase is initiated")

    def read_local_data(self):
        with open(f"{os.getcwd()}/{self.api_data}.json", 'r') as file:
            self.api_local = json.load(file)

        with open(f"{os.getcwd()}/{self.users}.json", 'r') as file:
            self.users_local = json.load(file)

    def read_collections(self):
        self.logger.info("Read api_data collection")
        a_data_c = self.database.collection(self.api_data).get()
        api_data_collection_local = {}
        for api_data_collection in a_data_c:
            api_data_collection_local[api_data_collection.id] = api_data_collection.to_dict()

        with open(f"{os.getcwd()}/{self.api_data}.json", "w", encoding="utf-8") as file:
            json.dump(api_data_collection_local, file, indent=4)
            blob = self.bucket.blob(f"{self.api_data}.json")
            blob.upload_from_filename(f"{self.api_data}.json")
            blob.make_public()

        self.logger.info("Read users collection")
        u_c = self.database.collection(self.users).list_documents()
        users_collection_local = {}
        for user_collection in u_c:
            try:
                users_collection_local[user_collection.id] = user_collection.get().to_dict()
                if user_collection is not None:
                    users_collection_local[user_collection.id][self.notifications] = [notif.to_dict() for notif in
                                                                                      user_collection.collection(
                                                                                          self.notifications).get()]
            except TypeError:
                self.delete_broken_collection(token=user_collection.id)

        with open(f"{os.getcwd()}/{self.users}.json", "w", encoding="utf-8") as file:
            json.dump(users_collection_local, file, indent=4)
            blob = self.bucket.blob(f"{self.users}.json")
            blob.upload_from_filename(f"{self.users}.json")
            blob.make_public()

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
            notifications: list[DocumentReference] = list(user_doc.collection(self.notifications).list_documents())
            if len(notifications):
                for notif in notifications:
                    notif.delete()
                self.logger.info("Notifications are cleared")
            user_doc.delete()
            self.logger.info(f"Broken user with token '{token}' is deleted")
