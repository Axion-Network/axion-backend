import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django

django.setup()

from hex2x_backend.snapshot.contracts_interaction import send_next_addresses

if __name__ == '__main__':
    start = 1
    stop = 2000

    portion = 250

    gas_price = 20
    retry_seconds = 360

    send_next_addresses(portion, gas_price, retry_seconds, start)
