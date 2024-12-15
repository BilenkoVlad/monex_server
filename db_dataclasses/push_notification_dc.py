import datetime
from dataclasses import dataclass


@dataclass
class PushNotification:
    text: str
    up: bool
    target: str
    source: str
    value: float
    notification_title: str
    notification_body: str
    date: str = datetime.datetime.now().strftime("%d-%m-%y %H:%M")
    read: bool = False


@dataclass
class GeneralPushNotification:
    push_notification: dict
    user_token: str
