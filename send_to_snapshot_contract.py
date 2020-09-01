import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django

django.setup()

from hex2x_backend.snapshot.contracts_interaction import send_to_snapshot_all

if __name__ == '__main__':
    send_to_snapshot_all()
