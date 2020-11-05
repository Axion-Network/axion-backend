import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django

django.setup()

from hex2x_backend.tokenholders.transfers_hex2t import iterate_dump_transfers_all

if __name__ == '__main__':
    iterate_dump_transfers_all()
