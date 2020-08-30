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
    started_stake = {
        'address': event['args']['stakerAddr'],
        'stake_id': event['args']['stakeId'],
        'tx_hash': event['transactionHash'],
        'block': event['blockNumber']
    }

    data0 = event['args']['data0']
    hex_data = hex(data0)

    # normalize hex to full string
    extended_data = '0x' + hex_data[2:].zfill(64)

    bit_start_time = 40 // 4
    bit_start_hearts = 112 // 4
    bit_start_shares = 184 // 4
    bit_start_days = 200 // 4

    started_stake['data0'] = extended_data
    started_stake['from_bits'] = {
        'timestamp': int(extended_data[-bit_start_time:], 16),
        'hearts': int(extended_data[-bit_start_hearts:-bit_start_time], 16),
        'shares': int(extended_data[-bit_start_shares:-bit_start_hearts], 16),
        'days': int(extended_data[-bit_start_days:-bit_start_shares], 16),
        'is_autostake': True if int(extended_data[:-bit_start_days], 16) != 0 else False
    }

    return started_stake


def parse_stake_end(event):
    ended_stake = {
        'address': event['args']['stakerAddr'],
        'stake_id': event['args']['stakeId'],
        'tx_hash': event['transactionHash'],
        'block': event['blockNumber']
    }

    data0 = event['args']['data0']
    data1 = event['args']['data1']

    extended_data_0 = '0x' + hex(data0)[2:].zfill(64)
    extended_data_1 = '0x' + hex(data1)[2:].zfill(64)

    bit_start_time = 40 // 4
    bit_start_hearts = 112 // 4
    bit_start_shares = 184 // 4

    bit_start_penalty = 72 // 4
    bit_start_days = 88 // 4

    ended_stake['data0'] = extended_data_0
    ended_stake['data1'] = extended_data_1

    ended_stake['from_bits_0'] = {
        'timestamp': int(extended_data_0[-bit_start_time:], 16),
        'hearts': int(extended_data_0[-bit_start_hearts:-bit_start_time], 16),
        'shares': int(extended_data_0[-bit_start_shares:-bit_start_hearts], 16),
        'payout': int(extended_data_0[:-bit_start_shares], 16)
    }

    ended_stake['from_bits_1'] = {
        'penalty': int(extended_data_1[-bit_start_penalty:], 16),
        'served_days': int(extended_data_1[-bit_start_days:-bit_start_penalty], 16),
        'prev_unlocked': True if int(extended_data_1[:-bit_start_days], 16) != 0 else False
    }

    return ended_stake


def parse_and_save_stakes(event_type, from_block, to_block):
    events = scan_stakes(event_type, from_block, to_block)

    print('iterating from', from_block, 'to', to_block, flush=True)
    print('events in batch:', len(events), flush=True)

    for event in events:
        if event_type == 'stake_start':
            parsed_event = parse_stake_start(event)

            started_stake = TokenStakeStart(
                address=parsed_event['address'],
                stake_id=parsed_event['stake_id'],
                data0=parsed_event['data0'],
                timestamp=parsed_event['from_bits']['timestamp'],
                hearts=parsed_event['from_bits']['hearts'],
                shares=parsed_event['from_bits']['shares'],
                days=parsed_event['from_bits']['days'],
                is_autostake=parsed_event['from_bits']['is_autostake'],
                tx_hash=parsed_event['tx_hash'].hex(),
                block_number=parsed_event['block']
            )

            started_stake.save()

            print('Saved started stake',
                  started_stake.id, started_stake.address, started_stake.stake_id, started_stake.data0,
                  started_stake.timestamp, started_stake.hearts, started_stake.shares, started_stake.days,
                  started_stake.is_autostake, started_stake.tx_hash
                  )

        elif event_type == 'stake_end':
            parsed_event = parse_stake_end(event)

            ended_stake = TokenStakeEnd(
                address=parsed_event['address'],
                stake_id=parsed_event['stake_id'],
                data0=parsed_event['data0'],
                data1=parsed_event['data1'],
                timestamp=parsed_event['from_bits_0']['timestamp'],
                hearts=parsed_event['from_bits_0']['hearts'],
                shares=parsed_event['from_bits_0']['shares'],
                payout=parsed_event['from_bits_0']['payout'],
                penalty=parsed_event['from_bits_1']['penalty'],
                served_days=parsed_event['from_bits_1']['served_days'],
                prev_unlocked=parsed_event['from_bits_1']['prev_unlocked'],
                tx_hash=parsed_event['tx_hash'].hex(),
                block_number=parsed_event['block']
            )

            ended_stake.save()

            print('Saved ended stake',
                  ended_stake.id, ended_stake.address, ended_stake.stake_id, ended_stake.data0, ended_stake.data1,
                  ended_stake.timestamp, ended_stake.hearts, ended_stake.shares, ended_stake.payout,
                  ended_stake.penalty, ended_stake.served_days, ended_stake.prev_unlocked, ended_stake.tx_hash
                  )
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


def iterate_dump_stake_all(event_type):
    iterate_dump_stakes(event_type, TRANSFERS_STARTED_BLOCK, MAINNET_STOP_BLOCK)