import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django

django.setup()

from hex2x_backend.snapshot.contracts_interaction import send_next_addresses

if __name__ == '__main__':
    # start = 1
    # stop = 2000

    portion = 300

    gas_price = 30
    retry_seconds = 600

    while True:
        res = send_next_addresses(portion, gas_price, retry_seconds)
        # print(res, flush=True)
        if res['reason'] == 'balance':
            print('please replenish balance', flush=True)
            break
        elif res['reason'] == 'finished':
            print('script finished', flush=True)
            break
        elif res['reason'] == 'exited':
            print('starting over', flush=True)
            continue
        else:
            print('script finished', flush=True)
            break
