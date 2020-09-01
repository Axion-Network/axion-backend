import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django

django.setup()

from hex2x_backend.snapshot.contracts_interaction import check_snapshot_contract_amounts

if __name__ == '__main__':
    check_snapshot_contract_amounts()
