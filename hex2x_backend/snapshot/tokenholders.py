from datetime import datetime
from decimal import Decimal
from collections import defaultdict
import json
import os

try:
    from web3.utils.abi import get_constructor_abi, merge_args_and_kwargs
    from web3.utils.events import get_event_data
    from web3.utils.filters import construct_event_filter_params
    from web3.utils.contracts import encode_abi
except ImportError:
    from web3._utils.abi import get_constructor_abi, merge_args_and_kwargs
    from web3._utils.events import get_event_data
    from web3._utils.filters import construct_event_filter_params
    from web3._utils.contracts import encode_abi


from hex2x_backend.snapshot.web3int import W3int
from hex2x_backend.snapshot.models import HexUser, TokenTransfer


HEX_WIN_TOKEN_ADDRESS = '0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39'
CONTRACT_CREATION_BLOCK = 9041184
TRANSFERS_STARTED_BLOCK = 9046420
MAINNET_STOP_BLOCK = 10684948


def load_hex_contract(web3_interface):
    with open('./HEX_abi.json', 'r') as f:
        erc20_abi = json.loads(f.read())

    hex_contract = web3_interface.eth.contract(address=HEX_WIN_TOKEN_ADDRESS, abi=erc20_abi)
    return hex_contract


def get_contract_transfers(w3, address, from_block, to_block, decimals=8):
    """Get logs of Transfer events of a contract"""
    from_block = from_block or "0x0"
    transfer_hash = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    params = [{"address": address, "fromBlock": hex(from_block), "toBlock": hex(to_block), "topics": [transfer_hash]}]
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


def get_transfer_logs(contract, from_block, to_block):
    # event_filter = myContract.events. < event_name >.createFilter(fromBlock="latest", argument_filters={'arg1': 10})
    # event_filter.get_new_entries()

    transfer = contract.events.Transfer("from", "to", "value")
    event_filter = transfer.createFilter(fromBlock=from_block, toBlock=to_block, address=contract.address)
    events = event_filter.get_all_entries()
    return events


def get_stakes_logs(contract, from_block, to_block):
    # event_filter = myContract.events. < event_name >.createFilter(fromBlock="latest", argument_filters={'arg1': 10})
    # event_filter.get_new_entries()

    transfer = contract.events.StakeStart("data0", "stakerAddr", "stakeId")
    event_filter = transfer.createFilter(fromBlock=from_block, toBlock=to_block, address=contract.address)
    events = event_filter.get_all_entries()
    return events





def scan_stakes(blocks):
    w3 = W3int('parity')
    token = load_hex_contract(w3.interface_http)

    start = TRANSFERS_STARTED_BLOCK
    stop = TRANSFERS_STARTED_BLOCK + blocks

    events = get_stakes_logs(token, start, stop)
    return events


def get_raw_transfer_logs(w3, address, from_block, to_block):
    """Get logs of Transfer events of a contract"""
    from_block = from_block or hex(TRANSFERS_STARTED_BLOCK)
    transfer_hash = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    params = [{"address": address, "fromBlock": hex(from_block), "toBlock": hex(to_block), "topics": [transfer_hash]}]
    req = w3.get_http_rpc_response("eth_getLogs", params)

    if 'result' in req:
        logs = req['result']
    else:
        logs = []
        print(req)

    return logs


def get_raw_stakes_logs(w3, address, from_block, to_block):
    """Get logs of Transfer events of a contract"""
    from_block = from_block or hex(TRANSFERS_STARTED_BLOCK)
    transfer_hash = "0x14872dc760f33532684e68e1b6d5fd3f71ba7b07dee76bdb2b084f28b74233ef"
    params = [{"address": address, "fromBlock": hex(from_block), "toBlock": hex(to_block), "topics": [transfer_hash]}]
    req = w3.get_http_rpc_response("eth_getLogs", params)

    if 'result' in req:
        logs = req['result']
    else:
        logs = []
        print(req)

    return logs


def scan_raw_stakes_logs(blocks):
    w3 = W3int('parity')
    token = load_hex_contract(w3.interface_http)

    start = TRANSFERS_STARTED_BLOCK
    stop = TRANSFERS_STARTED_BLOCK + blocks
    events = get_raw_stakes_logs(w3, token.address, start, stop)
    return events



