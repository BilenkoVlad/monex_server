import asyncio

from currency.currency import Currency
from push_notification.firebase_base import FirebaseBase
from push_notification.push_funcs import full_flow


class SendPush(FirebaseBase):
    async def update_user_info_rates(self, source_cur, targets, rate_data, user_info):
        for current in self.api_data_collection_local[rate_data]:
            if current == source_cur:
                for val in self.api_data_collection_local[rate_data][current]:
                    for target in targets:
                        if val["target"] == target:
                            user_info[source_cur][target][rate_data] = val["rate"]

    async def process_token(self, token: str, user_data: dict, test_push: bool = False):
        self.set_user_doc(token=token)

        user_info = {}

        source = [cur for cur in Currency.currency_dict if cur in user_data][0]
        targets = user_data[source]
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
        self.read_collections()

        tasks = [self.process_token(token, user_data) for token, user_data in self.users_collection_local.items()]
        await asyncio.gather(*tasks)

    def cleanup(self):
        user_tokens = self.users_collection_local.copy()
        for token, user_data in user_tokens.items():
            if "test" in user_data["platform"]:
                self.delete_user(token=token)
            self.delete_broken_collection(token=token)
            del self.users_collection_local[token]

    async def test_notifications_main(self):
        user_tokens = self.database.collection(self.users).get()
        # tasks = [self.process_token(token, True) for token in user_tokens]
        # await asyncio.gather(*tasks)
