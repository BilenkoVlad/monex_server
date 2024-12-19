import uuid
from dataclasses import asdict

from firebase_admin import messaging
from google.cloud.firestore_v1 import CollectionReference

from api.logg import setup_server_logger
from db_dataclasses.push_notification_dc import PushNotification, GeneralPushNotification
from push_notification.firebase_base import FirebaseBase

logger = setup_server_logger()


def full_flow(fb_base: FirebaseBase,
              token: str,
              source: str,
              target: str,
              previous_data: float,
              current_data: float,
              test_push: bool):
    msg = check_if_changed(token=token,
                           source=source,
                           target=target,
                           previous_data=previous_data,
                           current_data=current_data,
                           test_push=test_push)
    if msg is not None:
        general_push = GeneralPushNotification(push_notification=asdict(msg), user_token=token)

        add_msg_to_user(fb_base=fb_base, token=token, msg=msg)

        general_push_id = add_msg_to_general_db(fb_base=fb_base, general_push=general_push)

        send_notification(fb_base=fb_base, token=token, msg=msg, general_push_id=general_push_id)


def check_if_changed(token: str,
                     source: str,
                     target: str,
                     previous_data: float,
                     current_data: float,
                     test_push: bool):
    logger.info(f"Check if rate '{source}' to '{target}' is changed. User: '{token}'")
    if test_push:
        return PushNotification(
            text=f"{source} to {target} is up! 🚀 New rate: {current_data}",
            up=True,
            target=target,
            source=source,
            value=current_data,
            notification_title="Rate up ↗️",
            notification_body=f"{source} to {target} is up! 🚀 New rate: {current_data}"
        )
    if previous_data < current_data:
        return PushNotification(
            text=f"{source} to {target} is up! 🚀 New rate: {current_data}",
            up=True,
            target=target,
            source=source,
            value=current_data,
            notification_title="Rate up ↗️",
            notification_body=f"{source} to {target} is up! 🚀 New rate: {current_data}"
        )
    elif previous_data > current_data:
        return PushNotification(
            text=f"{source} to {target} dropped! 📉 New rate: {current_data}",
            up=False,
            target=target,
            source=source,
            value=current_data,
            notification_title="Rate down ↘️",
            notification_body=f"{source} to {target} dropped! 📉 New rate: {current_data}"
        )
    else:
        logger.info(f"Rate '{source}' to '{target}' is the same")
        return None


def add_msg_to_user(fb_base: FirebaseBase, token: str, msg: PushNotification):
    user_nots: CollectionReference = fb_base.user_doc.collection(fb_base.notifications)
    user_nots.add(asdict(msg))
    logger.info(f"Notification '{asdict(msg)}' was added to user with token '{token}'")


def add_msg_to_general_db(fb_base: FirebaseBase, general_push: GeneralPushNotification):
    msg_id = str(uuid.uuid4())
    fb_base.notifications_collection.add(document_data=asdict(general_push), document_id=msg_id)

    logger.info(
        f"General push '{asdict(general_push)}' was added to '{fb_base.notifications}' collection with id '{msg_id}'")
    return msg_id


def send_notification(fb_base: FirebaseBase,
                      token: str,
                      msg: PushNotification,
                      general_push_id: str):
    try:
        logger.info(f"Sending push notification for '{token}'")

        user_nots: CollectionReference = fb_base.user_doc.collection(fb_base.notifications)

        badge_count = sum(1 for collection in user_nots.get() if not collection.to_dict()["read"])

        message = messaging.Message(
            notification=messaging.Notification(
                title=msg.notification_title,
                body=msg.notification_body
            ),
            token=token,
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        badge=badge_count
                    )
                )
            )
        )
        logger.info(f"Push notification data: '{asdict(msg)}'. Badge count is '{badge_count}'")

        messaging.send(message)

        fb_base.notifications_collection.document(general_push_id).delete()
    except Exception as ex:
        logger.error(ex)
        logger.error(f"Push notification for '{token}' was not sent")
        if str(ex) == "Requested entity was not found.":
            fb_base.delete_user(token=token)
