import json

from hex2x_backend.snapshot.web3int import W3int
from .models import TokenTransferHex2t
from .transfers import get_transfer_logs

HEX2T_TOKEN_ADDRESS = '0xEd1199093b1aBd07a368Dd1C0Cdc77D8517BA2A0'
# CONTRACT_CREATION_BLOCK = 10164763
CONTRACT_CREATION_BLOCK = 11174763
NATIVE_SWAP_LAUNCHED_BLOCK = 11176348


def load_hex2t_contract(web3_interface):
    with open('./HEX2T_abi.json', 'r') as f:
        erc20_abi = json.loads(f.read())

    hex_contract = web3_interface.eth.contract(address=HEX2T_TOKEN_ADDRESS, abi=erc20_abi)
    return hex_contract


def scan_token_hex2t(from_block, to_block):
    w3 = W3int('parity')
    token = load_hex2t_contract(w3.interface_http)

    events = get_transfer_logs(token, from_block, to_block)
    return events


def parse_and_save_transfers(from_block, to_block):
    events = scan_token_hex2t(from_block, to_block)

    print('iterating from', from_block, 'to', to_block, flush=True)
    print('events in batch:', len(events), flush=True)
    for event in events:
        from_addr = event['args']['from']
        to_addr = event['args']['to']
        amount = event['args']['value']
        tx_hash = event['transactionHash']
        block = event['blockNumber']

        # exist_transfer = TokenTransferHex2t.objects.filter(tx_hash=tx_hash.hex())
        # exist_transfer = TokenTransferHex2t.

        (transfer, created) = TokenTransferHex2t.objects.get_or_create(
            from_address=from_addr,
            to_address=to_addr,
            amount=amount,
            tx_hash=tx_hash.hex(),
            block_number=block
        )

        if not created:
            print(
                'hash %s skipped due: already saved (id: %s), from blockNo: %s' %
                (tx_hash.hex(), transfer.id, block
                 ), flush=True)
        else:
            transfer.save()
            print('Saved transfer',
                  transfer.id, transfer.block_number, transfer.from_address, transfer.to_address, transfer.amount,
                  transfer.tx_hash
                  )


def iterate_dump_transfers(start_block, stop_block):
    step_block = start_block + 1000

    while step_block <= stop_block:
        print('Saving events from', start_block, 'to', step_block, 'blocks', flush=True)
        parse_and_save_transfers(start_block, step_block)
        print('Batch saved', flush=True)
        start_block += 1000

        block_diff = stop_block - start_block
        print('block diff', block_diff, flush=True)

        if (block_diff <= 1000) and (block_diff > 0):
            step_block = start_block + block_diff
        else:
            step_block = start_block + 1000



def iterate_dump_transfers_all():
    iterate_dump_transfers(CONTRACT_CREATION_BLOCK, NATIVE_SWAP_LAUNCHED_BLOCK)
