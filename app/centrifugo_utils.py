import time
import jwt
from cent import Client, PublishRequest
from django.conf import settings

def generate_centrifuge_token(user_id):
    """Генерирует JWT токен для Centrifugo"""
    token = jwt.encode({
        "sub": str(user_id),
        "exp": int(time.time()) + 10 * 60,  # 10 минут
    }, settings.CENTRIFUGO_HMAC_SECRET, algorithm="HS256")
    return token

def publish_to_centrifuge(channel, data):
    """Публикует сообщение в Centrifugo"""
    api_url = f"{settings.CENTRIFUGO_URL}/api"
    client = Client(api_url, settings.CENTRIFUGO_API_KEY)
    request = PublishRequest(channel=channel, data=data)
    client.publish(request)