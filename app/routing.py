# chat/routing.py
from django.urls import re_path
from django.conf.urls import url
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from .consumers import *

websocket_urlpatterns = [
    url(r'^message/(?P<sender>[0-9]+)/(?P<receiver>[0-9]+)$', ChatConsumer),
]

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})