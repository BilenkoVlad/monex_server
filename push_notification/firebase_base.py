import json
import os

import dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import CollectionReference, DocumentReference, DocumentSnapshot

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
        self.logger = setup_server_logger()
        self.database = firestore.client()
        self.server_url = os.environ.get('SERVER_URL')
        self.api_data = "api_data"
        self.users = "users"
        self.notifications = "notifications"

    def delete_user(self, token: DocumentSnapshot):
        users_col: CollectionReference = self.database.collection(self.users)
        user_doc: DocumentReference = users_col.document(token.id)
        user_doc.delete()
        self.logger.info(f"Deleting user with token '{token.id}'")
        if user_doc.get().exists:
            self.logger.warning(f"User with token '{token.id}' was not deleted")

    def delete_broken_collection(self, token: DocumentSnapshot):
        users_col: CollectionReference = self.database.collection(self.users)
        user_doc: DocumentReference = users_col.document(token.id)
        if not user_doc.get().exists:
            self.logger.info("Deleting broken user")
            user_nots: CollectionReference = user_doc.collection(self.notifications)
            notifications: list[DocumentReference] = list(user_nots.list_documents())
            if len(notifications):
                for notif in notifications:
                    notif.delete()
                self.logger.info("Notifications are cleared")
            user_doc.delete()
            self.logger.info(f"Broken user with token '{token.id}' is deleted")
