import requests
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
from time import sleep
import json
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django
django.setup()

from hex2x_snapshot.web3int import W3int
from hex2x_snapshot.models import HexUser

HEX_WIN_TOKEN_ADDRESS = '0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39'
CONTRACT_CREATION_BLOCK = 9041184
MAINNET_STOP_BLOCK = 10425137


def get_contract_transfers(address, from_block, to_block, decimals=8):
    """Get logs of Transfer events of a contract"""
    from_block = from_block or "0x0"
    transfer_hash = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    params = [{"address": address, "fromBlock": from_block, "toBlock": to_block, "topics": [transfer_hash]}]
    w3 = W3int('parity')
    req = w3.get_http_rpc_response("eth_getLogs", params)
    #print(req)
    logs = req['result']

    addresses = []

    if logs:
        # decimals_factor = Decimal("10") ** Decimal("-{}".format(decimals))
        for log in logs:
            # log["amount"] = Decimal(str(int(log["data"], 16))) * decimals_factor
            # log["from"] = log["topics"][1][0:2] + log["topics"][1][26:]
            # log["to"] = log["topics"][2][0:2] + log["topics"][2][26:]

            from_addr = log["topics"][1][0:2] + log["topics"][1][26:]
            to_addr = log["topics"][2][0:2] + log["topics"][2][26:]

            if from_addr not in addresses:
                addresses.append(from_addr)

            if to_addr not in addresses:
                addresses.append(to_addr)

    return addresses


def get_balances(transfers):
    balances = defaultdict(Decimal)
    for t in transfers:
        balances[t["from"]] -= t["amount"]
        balances[t["to"]] += t["amount"]
    bottom_limit = Decimal("0.00000000001")
    balances = {k: balances[k] for k in balances if balances[k] > bottom_limit}
    return balances


def start_stop_to_hex(from_block, to_block):
    return hex(from_block), hex(to_block)


def log_time():
    print(str(datetime.now()), flush=True)


def iterate_from(start_block):
    step_block = start_block + 1000

    while step_block <= MAINNET_STOP_BLOCK:

        from_block, to_block = start_stop_to_hex(start_block, step_block)
        addresses = get_contract_transfers(HEX_WIN_TOKEN_ADDRESS, from_block, to_block)

        log_time()
        print('Addresses in batch', len(addresses), flush=True)
        print('Current block part', start_block, 'to', step_block, flush=True)

        start_block += 1000
        step_block = start_block + 1000

        if addresses:
            i = 1
            for addr in addresses:
                print('{curr}/{total} Address: {addr}'.format(curr=i, total=len(addresses), addr=addr))
                if HexUser.objects.filter(user_address=addr).first() is None:
                    user = HexUser(user_address=addr)
                    user.save()

                i += 1


def iterate_from_beginning():
    start_block = CONTRACT_CREATION_BLOCK
    iterate_from(start_block)


def load_hex_contract(web3_interface):
    with open('./HEX_abi.json', 'r') as f:
        erc20_abi = json.loads(f.read())

    hex_contract = web3_interface.eth.contract(address=HEX_WIN_TOKEN_ADDRESS, abi=erc20_abi)
    return hex_contract


def get_hex_balance_for_multiple_address(w3_int, hex_contract, address):
    conv_address = w3_int.toChecksumAddress(address.lower())
    balance = hex_contract.functions.balanceOf(conv_address).call()
    return balance


def get_hex_balance_for_address(address):
    w3 = W3int('parity')

    hex_contract = load_hex_contract(w3.interface)

    balance = get_hex_balance_for_multiple_address(w3.interface, hex_contract)
    return balance


def stake_response_to_dict(stake):
    return {
        'stake_id': stake[0],
        'staked_hearts': stake[1],
        'stake_shares': stake[2],
        'locked_day': stake[3],
        'staked_days': stake[4],
        'unlocked_day': stake[5],
        'is_auto_stake': stake[6]
    }


def get_stakes_for_address(address):
    w3 = W3int('parity')

    hex_contract = load_hex_contract(w3.interface)
    conv_address = w3.interface.toChecksumAddress(address.lower())
    stake_count = hex_contract.functions.stakeCount(conv_address).call()
    stake_list = []
    for i in range(stake_count):
        stake = hex_contract.functions.stakeLists(conv_address, i).call()
        stake_list.append(stake_response_to_dict(stake))

    return {'total': stake_count, 'stakes': stake_list}


if __name__ == '__main__':
    log_time()
    print('Starting full db sync in 30s', flush=True)
    iterate_from_beginning()