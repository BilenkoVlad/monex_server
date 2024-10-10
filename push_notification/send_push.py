import asyncio
import datetime

from firebase_admin import messaging
from google.cloud.firestore_v1 import DocumentSnapshot

from currency.currency import Currency
from push_notification.firebase_base import FirebaseBase


class SendPush(FirebaseBase):
    async def update_user_info_rates(self, source_cur, targets, rate_data, user_info):
        for current in self.database.collection(self.api_data).document(rate_data).get().to_dict().keys():
            if current == source_cur:
                for val in self.database.collection(self.api_data).document(rate_data).get().to_dict()[current]:
                    for target in targets:
                        if val["target"] == target:
                            user_info[source_cur][target][rate_data] = val["rate"]

    async def process_token(self, token: DocumentSnapshot, test_push: bool = False):
        user_info = {}
        follow_list = token.to_dict()

        source = [cur for cur in Currency.currency_dict if cur in follow_list][0]
        targets = follow_list[source]
        user_info[source] = {}

        for target in targets:
            add_target = {target: {
                "previous": 0,
                "current": 0
            }}
            user_info[source].update(add_target)

        await self.update_user_info_rates(source_cur=source, targets=targets, rate_data="current", user_info=user_info)
        await self.update_user_info_rates(source_cur=source, targets=targets, rate_data="previous", user_info=user_info)

        for target in targets:
            message = None
            if not test_push:
                if user_info[source][target]["previous"] < user_info[source][target]["current"]:
                    self.database.collection(self.users).document(token.id).collection(self.notifications).add(
                        {"text": f"{source} to {target} is up! 🚀 New rate: {user_info[source][target]['current']}",
                         "date": datetime.datetime.now().strftime("%d-%m-%y %H:%M"),
                         "up": True,
                         "target": target,
                         "source": source,
                         "value": user_info[source][target]['current'],
                         "read": False
                         })

                    notification_collection: DocumentSnapshot = self.database.collection(self.users).document(
                        token.id).collection(self.notifications).get()

                    badge_count = sum(1 for collection in notification_collection if not collection.to_dict()["read"])

                    message = messaging.Message(
                        notification=messaging.Notification(
                            title="Rate up ↗️",
                            body=f"{source} to {target} is up! 🚀 New rate: {user_info[source][target]['current']}"
                        ),
                        token=token.id,
                        apns=messaging.APNSConfig(
                            payload=messaging.APNSPayload(
                                aps=messaging.Aps(
                                    badge=badge_count
                                )
                            )
                        )
                    )

                if user_info[source][target]["previous"] > user_info[source][target]["current"]:
                    self.database.collection(self.users).document(token.id).collection(self.notifications).add(
                        {"text": f"{source} to {target} dropped! 📉 New rate: {user_info[source][target]['current']}",
                         "date": datetime.datetime.now().strftime("%d-%m-%y %H:%M"),
                         "up": False,
                         "target": target,
                         "source": source,
                         "value": user_info[source][target]['current'],
                         "read": False
                         })

                    notification_collection: DocumentSnapshot = self.database.collection(self.users).document(
                        token.id).collection(self.notifications).get()

                    badge_count = sum(1 for collection in notification_collection if not collection.to_dict()["read"])

                    message = messaging.Message(
                        notification=messaging.Notification(
                            title="Rate down ↘️",
                            body=f"{source} to {target} dropped! 📉 New rate: {user_info[source][target]['current']}"
                        ),
                        token=token.id,
                        apns=messaging.APNSConfig(
                            payload=messaging.APNSPayload(
                                aps=messaging.Aps(
                                    badge=badge_count
                                )
                            )
                        )
                    )

                if message is not None:
                    try:
                        messaging.send(message)
                    except Exception as ex:
                        print(str(ex))
            else:
                self.database.collection(self.users).document(token.id).collection(self.notifications).add(
                    {"text": "USD to UAH is up! 🚀 New rate: 1.0",
                     "date": datetime.datetime.now().strftime("%d-%m-%y %H:%M"),
                     "up": True,
                     "target": "UAH",
                     "source": "USD",
                     "value": 1.0,
                     "read": False
                     })

                notification_collection: DocumentSnapshot = self.database.collection(self.users).document(
                    token.id).collection(self.notifications).get()

                badge_count = sum(1 for collection in notification_collection if not collection.to_dict()["read"])

                message = messaging.Message(
                    notification=messaging.Notification(
                        title="Rate up ↗️",
                        body="USD to UAH is up! 🚀 New rate: 1.0",
                    ),
                    token=token.id,
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                badge=badge_count
                            )
                        )
                    )
                )

                try:
                    messaging.send(message)
                except Exception as ex:
                    self.database.collection(self.users).document(token.id).delete()

    async def main(self):
        user_tokens = self.database.collection(self.users).get()
        tasks = [self.process_token(token) for token in user_tokens]
        await asyncio.gather(*tasks)

    async def test_notifications_main(self):
        user_tokens = self.database.collection(self.users).get()
        tasks = [self.process_token(token, True) for token in user_tokens]
        await asyncio.gather(*tasks)
