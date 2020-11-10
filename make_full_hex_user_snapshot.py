import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django

django.setup()

from hex2x_backend.snapshot.api import make_full_hex_user_snapshot

if __name__ == '__main__':
    make_full_hex_user_snapshot(testnet=False)
