import sys
import os

path = '/home/sim34/Bulk_Messenger'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sms_panel.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()