import os

import firebase_admin
from firebase_admin import credentials, firestore
import requests
import json

# Path to your service account key file
SERVICE_ACCOUNT_FILE = 'secret.json' if os.getenv("FIREBASE_SERVICE_ACCOUNT_MONEX_APP_F86C7") is None else os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_MONEX_APP_F86C7")

# Initialize Firebase Admin SDK
cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()


def fetch_api_data():
    url = "https://monexserver-9c26776e6120.herokuapp.com/api/available-currencies"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()

            if db.collection("api_data").document("previous").get().exists:
                db.collection('api_data').document('previous').set(
                    db.collection('api_data').document('current').get().to_dict())
            else:
                all_curs = {}
                for currency in data["available_currencies"]:
                    all_curs[currency] = currency
                db.collection('api_data').document('previous').create(all_curs)
                db.collection('api_data').document('current').create(all_curs)

            for currency in data["available_currencies"]:
                db.collection('api_data').document('current').update({currency: requests.get(
                    f"https://monexserver-9c26776e6120.herokuapp.com/api/rates/{currency}").json()})
        else:
            print(f"Failed to fetch data: {response.status_code}")
    except Exception as e:
        print(f"Error during API call: {e}")


if __name__ == "__main__":
    fetch_api_data()
