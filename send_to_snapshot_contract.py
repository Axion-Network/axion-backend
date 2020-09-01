import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django

django.setup()

from hex2x_backend.snapshot.contracts_interaction import send_to_snapshot_all

if __name__ == '__main__':
    portion = 350
    gas_price = 30
    sleep_time = 15

    send_to_snapshot_all(portion, gas_price, sleep_time)
