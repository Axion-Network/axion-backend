import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django

django.setup()

from hex2x_backend.tokenholders.stakings import iterate_dump_stake_all


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise Exception('event type must be specified')

    param = sys.argv[1]

    if param not in ['stake_start', 'stake_end']:
        raise Exception('argument must be stake_start or stake_end')

    iterate_dump_stake_all(param)
