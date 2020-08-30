import json

from hex2x_backend.snapshot.web3int import W3int
from .models import TokenTransfer


HEX_WIN_TOKEN_ADDRESS = '0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39'
CONTRACT_CREATION_BLOCK = 9041184
TRANSFERS_STARTED_BLOCK = 9046420
MAINNET_STOP_BLOCK = 10150928


def load_hex_contract(web3_interface):
    with open('./HEX_abi.json', 'r') as f:
        erc20_abi = json.loads(f.read())

    hex_contract = web3_interface.eth.contract(address=HEX_WIN_TOKEN_ADDRESS, abi=erc20_abi)
    return hex_contract


def get_transfer_logs(contract, from_block, to_block):
    # event_filter = myContract.events. < event_name >.createFilter(fromBlock="latest", argument_filters={'arg1': 10})
    # event_filter.get_new_entries()

    transfer = contract.events.Transfer("from", "to", "value")
    event_filter = transfer.createFilter(fromBlock=from_block, toBlock=to_block, address=contract.address)
    events = event_filter.get_all_entries()
    return events


def scan_token_to(blocks):
    w3 = W3int('parity')
    token = load_hex_contract(w3.interface_http)

    start = TRANSFERS_STARTED_BLOCK
    stop = TRANSFERS_STARTED_BLOCK + blocks

    events = get_transfer_logs(token, start, stop)
    return events


def scan_token(from_block, to_block):
    w3 = W3int('parity')
    token = load_hex_contract(w3.interface_http)

    events = get_transfer_logs(token, from_block, to_block)
    return events


def parse_and_save_transfers(from_block, to_block):
    events = scan_token(from_block, to_block)

    print('iterating from', from_block, 'to', to_block, flush=True)
    print('events in batch:',len(events), flush=True)
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
            tx_hash=tx_hash.hex(),
            block_number=block
        )
        transfer.save()
        print('Saved transfer',
              transfer.id, transfer.from_address, transfer.to_address, transfer.amount, transfer.tx_hash
        )


def iterate_dump_transfers(start_block, stop_block):
    step_block = start_block + 1000

    while step_block <= stop_block:
        print('Saving events from', start_block, 'to', step_block, 'blocks', flush=True)
        parse_and_save_transfers(start_block, step_block)
        print('Batch saved', flush=True)
        start_block += 1000
        step_block = start_block + 1000


def iterate_dump_transfers_all():
    iterate_dump_transfers(TRANSFERS_STARTED_BLOCK, MAINNET_STOP_BLOCK)

# def iterate_from(start_block):
#     step_block = start_block + 1000
#
#     while step_block <= MAINNET_STOP_BLOCK:
#
#         parse_and_save_transfers(start_block, step_block)
#
#         from_block, to_block = start_stop_to_hex(start_block, step_block)
#         addresses = get_contract_transfers(HEX_WIN_TOKEN_ADDRESS, from_block, to_block)
#
#         print('Current block part', start_block, 'to', step_block, flush=True)
#
#         start_block += 1000
#         step_block = start_block + 1000
#
#         if addresses:
#             i = 1
#             for addr in addresses:
#                 msg = '{curr}/{total} Address: {addr}'.format(curr=i, total=len(addresses), addr=addr)
#                 if HexUser.objects.filter(user_address=addr).first() is None:
#                     user = HexUser(user_address=addr)
#                     user.save()
#                     print(msg)
#                 else:
#                     print(msg + ' (skipped)')
#
#                 i += 1


# def iterate_from_beginning():
#     start_block = TRANSFERS_STARTED_BLOCK
#     iterate_from(start_block)

