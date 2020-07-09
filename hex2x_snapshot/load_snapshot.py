from .web3int import W3int
from .signing import sign_send_tx
from .models import HexUser
import json

from hex2x_backend.settings import BACKEND_ADDR, BACKEND_PRIV


def load_contract(contract_address):
    w3 = W3int('infura', 'ropsten')

    with open('../snapshot_contract_abi.json', 'r') as f:
        snapshot_contract_abi = json.loads(f.read())

    snapshot_contract = w3.interface.eth.contract(address=contract_address, abi=snapshot_contract_abi)
    return w3, snapshot_contract


def send_to_contract(w3, snapshot_contract, hex_user):
    gas_limit = w3.interface.eth.getBlock('latest')['gasLimit']

    tx = snapshot_contract.functions.addToList(hex_user.user_address, hex_user.hex_amount)
    tx_hash = sign_send_tx(w3, 3, gas_limit, tx)
    return tx_hash


def send_to_contract_batch(w3, snapshot_contract, count_start, count_end):
    gas_limit = w3.interface.eth.getBlock('latest')['gasLimit']

    user_list = HexUser.objects.filter(id__in=list(range(count_start, count_end)))
    address_list = []
    amount_list = []
    for user in user_list:
        address_list.append(user.user_address)
        amount_list.append(user.hex_amount)
    tx = snapshot_contract.functions.addToListMultiple(address_list, amount_list)
    tx_hash = sign_send_tx(w3, 3, gas_limit, tx)
    return tx_hash
