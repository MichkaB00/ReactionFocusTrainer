import json
import os
import uuid

import django
import paho.mqtt.client as mqtt
from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.utils import timezone
from pymongo.errors import PyMongoError

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from training.mongo import get_collection


BROKER = "test.mosquitto.org"
TOPIC = "focus/lab5/7e4af1c93b8d451f/reaction"


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe(TOPIC)
        print("Підключено до MQTT. Очікування результатів.", flush=True)
    else:
        print(f"Не вдалося підключитися до MQTT: {reason_code}", flush=True)


def on_message(client, userdata, message):
    if message.topic != TOPIC or message.retain or len(message.payload) > 256:
        print("Повідомлення відхилено.", flush=True)
        return
    try:
        data = json.loads(message.payload.decode("utf-8"))
        if not isinstance(data, dict) or set(data) != {"mode", "reaction_time_ms"}:
            raise ValueError
        reaction_time = data["reaction_time_ms"]
        if data["mode"] != "reaction" or type(reaction_time) is not int or not 1 <= reaction_time <= 60000:
            raise ValueError
    except (UnicodeDecodeError, ValueError, TypeError):
        print("Некоректний результат.", flush=True)
        return

    try:
        if not get_user_model().objects.filter(pk=userdata).exists():
            print("Користувача не знайдено. Результат не збережено.", flush=True)
            return
        get_collection().insert_one({
            "user_id": userdata,
            "mode": "reaction",
            "created_at": timezone.now(),
            "attempt_id": str(uuid.uuid4()),
            "reaction_time_ms": reaction_time,
        })
    except (PyMongoError, DatabaseError):
        print("Не вдалося зберегти результат.", flush=True)
        return
    print(f"Результат отримано та збережено: {reaction_time} мс.", flush=True)


def main():
    try:
        user_id = int(os.environ.get("FOCUS_MQTT_USER_ID", ""))
        if user_id <= 0 or not get_user_model().objects.filter(pk=user_id).exists():
            raise ValueError
    except ValueError:
        print("Вкажіть FOCUS_MQTT_USER_ID існуючого користувача.", flush=True)
        return
    except (DatabaseError, ImproperlyConfigured):
        print("Не вдалося перевірити користувача.", flush=True)
        return

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=user_id)
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect_async(BROKER, 1883, 60)
    try:
        client.loop_forever(retry_first_connection=True)
    except KeyboardInterrupt:
        print("Subscriber зупинено.", flush=True)
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
