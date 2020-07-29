from .web3int import W3int
from .signing import sign_send_tx
from .models import HexUser
import json

from hex2x_backend.settings import SNAPSHOT_CONTRACT_ADDRESS


def load_contract(contract_address, abi_path):
    w3 = W3int('infura', 'ropsten')

    with open(abi_path, 'r') as f:
        snapshot_contract_abi = json.loads(f.read())

    snapshot_contract = w3.interface.eth.contract(address=contract_address, abi=snapshot_contract_abi)
    return w3, snapshot_contract


def load_snapshot_contract(contract_ddress):
    abi_path = './ERC20Snapshot_abi.json'
    w3, contract = load_contract(contract_ddress, abi_path)
    return w3, contract


def load_swap_contract(contract_address):
    abi_path = './ForeignSwap_abi.json'
    w3, contract = load_contract(contract_address, abi_path)
    return w3, contract


def send_to_snapshot(w3, snapshot_contract, hex_user):
    gas_limit = w3.interface.eth.getBlock('latest')['gasLimit']
    chain_id = w3.interface.eth.chainId

    tx = snapshot_contract.functions.addToSnapshot(hex_user.user_address, hex_user.hex_amount)
    tx_hash = sign_send_tx(w3, chain_id, gas_limit, tx)
    return tx_hash


def send_to_snapshot_batch(w3, snapshot_contract, count_start, count_end):
    gas_limit = w3.interface.eth.getBlock('latest')['gasLimit']
    chain_id = w3.interface.eth.chainId

    user_list = HexUser.objects.filter(id__in=list(range(count_start, count_end)))
    address_list = []
    amount_list = []
    for user in user_list:
        address_list.append(w3.interface.toChecksumAddress(user.user_address.lower()))
        amount_list.append(int(user.hex_amount))
    tx = snapshot_contract.functions.addToSnapshotMultiple(address_list, amount_list)
    tx_hash = sign_send_tx(w3.interface, chain_id, gas_limit, tx)
    return tx_hash

