import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import parser_api.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pdf_parser_project.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            parser_api.routing.websocket_urlpatterns
        )
    ),
})