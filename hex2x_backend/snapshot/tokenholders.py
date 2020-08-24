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


def get_contract_transfers(address, from_block, to_block, decimals=8):
    """Get logs of Transfer events of a contract"""
    from_block = from_block or "0x0"
    transfer_hash = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    params = [{"address": address, "fromBlock": hex(from_block), "toBlock": hex(to_block), "topics": [transfer_hash]}]
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


def get_logs(contract, from_block, to_block):
    # event_filter = myContract.events. < event_name >.createFilter(fromBlock="latest", argument_filters={'arg1': 10})
    # event_filter.get_new_entries()

    transfer = contract.events.Transfer("from", "to", "value")
    event_filter = transfer.createFilter(fromBlock=from_block, toBlock=to_block, address=contract.address)
    events = event_filter.get_all_entries()
    return events


def scan_token(blocks):
    w3 = W3int('parity')
    token = load_hex_contract(w3.interface_http)

    start = TRANSFERS_STARTED_BLOCK
    stop = TRANSFERS_STARTED_BLOCK + blocks

    events = get_logs(token, start, stop)
    return events


def parse_and_save_transfers(blocks):
    events = scan_token(blocks)

    for event in events:
        from_addr = event['args']['from']
        to_addr = event['args']['to']
        amount = event['args']['value']
        tx_hash = event['transactionHash']
        block = event['blockNumber']

        transfer = TokenTransfer(
            from_address=from_addr,
            to_address=to_addr,
            amount=amount,
            tx_hash=tx_hash,
            block_number=block
        )
        transfer.save()
        print(transfer.id, 'saved, current block number:', block)



def get_logs_old(w3=None, contract=None, from_block=None, to_block=None, topics=None):

    if from_block is None:
        raise TypeError("Missing mandatory keyword argument to getLogs: fromBlock")

    transfer_abi = contract.events.Transfer("from", "to", "value")

    argument_filters = dict()

    _filters = dict(**argument_filters)

    # Construct JSON-RPC raw filter presentation based on human readable Python descriptions
    # Namely, convert event names to their keccak signatures
    data_filter_set, event_filter_params = construct_event_filter_params(
        transfer_abi,
        abi_codec=w3.codec,
        contract_address=contract.address,
        argument_filters=_filters,
        fromBlock=from_block,
        toBlock=to_block,
        address=contract.address,
        topics=topics,
    )

    # Call JSON-RPC API
    logs = w3.eth.getLogs(event_filter_params)

    # Convert raw binary data to Python proxy objects as described by ABI
    for entry in logs:
        yield get_event_data(transfer_abi, entry)


def scan_chunk(w3, token, start_block, end_block):
    """Populate TokenHolderStatus for certain blocks.
    :return: Set of addresses where balance changes between scans.
    """

    mutated_addresses = set()

    # Discriminate between ERC-20 transfer and ERC-667
    # The latter is not used anywhere yet AFAIK
    Transfer = token.events.Transfer("from", "to", "value")
    Issued = token.events.Issued("to", "value")

    for event_type in [Issued, Transfer]:

        # events = event_type.createFilter(fromBlock=start_block, toBlock=end_block).get_all_entries()

        events = get_logs(event_type, w3, token, from_block=start_block, to_block=end_block)

        # AttributeDict({'args': AttributeDict({'from': '0xDE5bC059aA433D72F25846bdFfe96434b406FA85', 'to': '0x0bdcc26C4B8077374ba9DB82164B77d6885b92a6', 'value': 300000000000000000000}), 'event': 'Transfer', 'logIndex': 0, 'transactionIndex': 0, 'transactionHash': HexBytes('0x973eb270e311c23dd6173a9092c9ad4ee8f3fe24627b43c7ad75dc2dadfcbdf9'), 'address': '0x890042E3d93aC10A426c7ac9e96ED6416B0cC616', 'blockHash': HexBytes('0x779f55173414a7c0df0d9fc0ab3fec461a66ceeee0b4058e495d98830c92abf8'), 'blockNumber': 7})
        for e in events:
            idx = e["logIndex"]  # nteger of the log index position in the block. null when its pending log.
            if idx is None:
                raise RuntimeError("Somehow tried to scan a pending block")

            if e["event"] == "Issued":
                # New issuances pop up from empty air - mark this specially in the database.
                # Also some ERC-20 tokens use Transfer from null address to symbolise issuance.
                from_ = self.TokenScanStatus.NULL_ADDRESS
            else:
                from_ = e["args"]["from"]
                mutated_addresses.add(e["args"]["from"])

            block_when = get_block_when(e["blockNumber"])

            self.create_deltas(e["blockNumber"], block_when, e["transactionHash"].hex(), idx, from_, e["args"]["to"], e["args"]["value"])
            self.logger.debug("Imported %s, token:%s block:%d from:%s to:%s value:%s", e["event"], self.address, e["blockNumber"], from_, e["args"]["to"], e["args"]["value"])

            mutated_addresses.add(e["args"]["to"])

    return mutated_addresses