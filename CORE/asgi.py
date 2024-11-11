import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from channels.auth import AuthMiddlewareStack
from LocalGov.consumers import NotificationConsumer

# Set the default settings module for the 'asgi' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CORE.settings')

# Application definition for HTTP and WebSocket
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  
    "websocket": AuthMiddlewareStack( 
        URLRouter([
            path("ws/notifications/", NotificationConsumer.as_asgi()),  
        ])
    ),
})
