"""
ASGI config for sfcs project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()
from channels.routing import ProtocolTypeRouter, URLRouter
from .routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sfcs.settings')

# application = get_asgi_application()
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': URLRouter(
        websocket_urlpatterns
    ),
})