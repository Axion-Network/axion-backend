import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django

django.setup()

from hex2x_backend.snapshot.api import make_balance_snapshot

if __name__ == '__main__':
    make_balance_snapshot()
