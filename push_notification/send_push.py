from push_notification.firebase_base import FirebaseBase


class SendPush(FirebaseBase):
    a = {
        "source": {
            "target1": {
                "previous": 0,
                "current": 1
            },
            "target2": {
                "previous": 0,
                "current": 1
            }
        }
    }

    b = {}

    async def main(self):
        user_tokens = self.database.collection("qwe").get()
        for token in user_tokens:
            follow_list = token.to_dict()
            follow_list.pop("platform")

            source = list(follow_list.keys())[0]
            targets = follow_list[source]
            self.b[source] = {}

            for target in targets:
                add_target = {target: {
                    "previous": 0,
                    "current": 0
                }}
                self.b[source].update(add_target)

            print(self.b)

            for current in self.database.collection("api_data").document("current").get().to_dict().keys():
                if current == source:
                    for val in self.database.collection("api_data").document("current").get().to_dict()[current]:
                        for target in targets:
                            if val["target"] == target:
                                self.b[source][target]["current"] = val["rate"]

            for previous in self.database.collection("api_data").document("previous").get().to_dict().keys():
                if previous == source:
                    for val in self.database.collection("api_data").document("current").get().to_dict()[previous]:
                        for target in targets:
                            if val["target"] == target:
                                self.b[source][target]["previous"] = val["rate"]

            print(self.b)

            #
            #
            # for key in user.to_dict().keys():
            #     if key != "platform":
            #         for currency in user.to_dict()[key]:
            #             if currency["follow"]:
            #                 print(f"source = {key}, target = {currency}")
            #
            #                 target = currency["target"]
            #                 source = currency["source"]
            #                 current_rate = 0
            #                 previous_rate = 0
            #
            # for current in db.collection("api_data").document("current").get().to_dict().keys():
            #     if current == source:
            #         for val in db.collection("api_data").document("current").get().to_dict()[
            #             current]:
            #             if val["target"] == target:
            #                 current_rate = val["rate"]
            #
            # for previous in db.collection("api_data").document("previous").get().to_dict().keys():
            #     if previous == source:
            #         for val in db.collection("api_data").document("current").get().to_dict()[
            #             previous]:
            #             if val["target"] == target:
            #                 previous_rate = val["rate"]
            #
            #                 if current_rate != previous_rate:
            #                     a = messaging.Message(
            #                         notification=messaging.Notification(
            #                             title="Python",
            #                             body=f"{target} currency to {source}"
            #                         ),
            #                         token="foaANwfD80NbjGAzOozhcv:APA91bEVR-XgFCDJiq2apFX2HIGPO3R_bZMxJU-GdKOg9pSHeg-IjoVVIm06d5tCy_cgjhfLH3VBDrcgYYMAl8Ew5dlPrLUl0egFikMHorvrbbXOBYyaN5fQeFdXmro7pivHqPUIZ3DH"
            #                     )
            #                     messaging.send(a)
            #                 print(current_rate)
            #                 print(previous_rate)
