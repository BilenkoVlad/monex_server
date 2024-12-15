import asyncio

from google.cloud.firestore_v1 import DocumentSnapshot

from currency.currency import Currency
from push_notification.firebase_base import FirebaseBase
from push_notification.push_funcs import full_flow


class SendPush(FirebaseBase):
    async def update_user_info_rates(self, source_cur, targets, rate_data, user_info):
        for current in self.database.collection(self.api_data).document(rate_data).get().to_dict().keys():
            if current == source_cur:
                for val in self.database.collection(self.api_data).document(rate_data).get().to_dict()[current]:
                    for target in targets:
                        if val["target"] == target:
                            user_info[source_cur][target][rate_data] = val["rate"]

    async def process_token(self, token: DocumentSnapshot, test_push: bool = False):
        if "test" in token.to_dict()["platform"]:
            self.delete_user(token=token)
        else:
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

            await self.update_user_info_rates(source_cur=source,
                                              targets=targets,
                                              rate_data="current",
                                              user_info=user_info)
            await self.update_user_info_rates(source_cur=source,
                                              targets=targets,
                                              rate_data="previous",
                                              user_info=user_info)

            for target in targets:
                full_flow(fb_base=self,
                          token=token,
                          source=source,
                          target=target,
                          previous_data=user_info[source][target]["previous"],
                          current_data=user_info[source][target]["current"],
                          test_push=test_push)



    async def main(self):
        user_tokens = self.database.collection(self.users).list_documents()
        for token in user_tokens:
            self.delete_broken_collection(token=token)

        user_tokens = self.database.collection(self.users).get()
        tasks = [self.process_token(token) for token in user_tokens]
        await asyncio.gather(*tasks)

    async def test_notifications_main(self):
        user_tokens = self.database.collection(self.users).get()
        tasks = [self.process_token(token, True) for token in user_tokens]
        await asyncio.gather(*tasks)
