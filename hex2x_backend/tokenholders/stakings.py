from hex2x_backend.snapshot.web3int import W3int
from .models import TokenStakeStart, TokenStakeEnd
from .common import *


def get_stakes_logs(contract, event_type, from_block, to_block):
    # event_filter = myContract.events. < event_name >.createFilter(fromBlock="latest", argument_filters={'arg1': 10})
    # event_filter.get_new_entries()

    if event_type == 'stake_start':
        stake_event = contract.events.StakeStart("data0", "stakerAddr", "stakeId")
    elif event_type == 'stake_end':
        stake_event = contract.events.StakeEnd("data0", "stakerAddr", "stakeId")
    else:
        raise Exception('no event type supplied')

    event_filter = stake_event.createFilter(fromBlock=from_block, toBlock=to_block, address=contract.address)
    events = event_filter.get_all_entries()
    return events


def scan_stakes(event_type, from_block, to_block):
    w3 = W3int('parity')
    token = load_hex_contract(w3.interface_http)

    events = get_stakes_logs(token, event_type, from_block, to_block)
    return events


def parse_stake_start(event):
    return


def parse_stake_end(event):
    return


def parse_and_save_stakes(event_type, from_block, to_block):
    events = scan_stakes(event_type, from_block, to_block)

    print('iterating from', from_block, 'to', to_block, flush=True)
    print('events in batch:', len(events), flush=True)

    for event in events:
        if event_type == 'stake_start':
            parsed_event = parse_stake_start(event)

            started_stake = TokenStakeStart()

        elif event_type == 'stake_end':
            parsed_event = parse_stake_end(event)

            ended_stake = TokenStakeEnd()
        else:
            raise Exception('invalid event type')


def iterate_dump_stakes(event_type, start_block, stop_block):
    step_block = start_block + 1000

    while step_block <= stop_block:
        print('Saving events from', start_block, 'to', step_block, 'blocks', flush=True)
        parse_and_save_stakes(event_type, start_block, step_block)
        print('Batch saved', flush=True)
        start_block += 1000
        step_block = start_block + 1000


def iterate_dump_stake_start_all():
    iterate_dump_stakes('stake_start', TRANSFERS_STARTED_BLOCK, MAINNET_STOP_BLOCK)


def iterate_dump_stake_end_all():
    iterate_dump_stakes('stake_end', TRANSFERS_STARTED_BLOCK, MAINNET_STOP_BLOCK)
