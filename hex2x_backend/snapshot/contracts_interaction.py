from .web3int import W3int
from .signing import sign_send_tx
from .models import HexUser

import os
import json
import csv
import time
from datetime import datetime

from dotenv import load_dotenv
from eth_abi import encode_single

from hex2x_backend.settings import BASE_DIR, SNAPSHOT_SIGNING_ADDR, BACKEND_ADDR, \
    SNAPSHOT_CONTRACT_SENDER_ADDR, SNAPSHOT_CONTRACT_SENDER_PRIV


def load_contracts_dotenv():
    path = os.path.join(BASE_DIR, '.env')
    load_dotenv(dotenv_path=path)


def load_contract(contract_address, abi_path, network):
    w3 = W3int('infura', network)

    with open(abi_path, 'r') as f:
        snapshot_contract_abi = json.loads(f.read())

    snapshot_contract = w3.interface.eth.contract(address=contract_address, abi=snapshot_contract_abi)
    return w3, snapshot_contract


def load_snapshot_contract(contract_ddress, network='rinkeby'):
    abi_path = os.path.join(BASE_DIR, 'ERC20Snapshot_abi.json')
    w3, contract = load_contract(contract_ddress, abi_path, network)
    return w3, contract


def load_swap_contract(contract_address, network='rinkeby'):
    abi_path = os.path.join(BASE_DIR, 'foreignswap.json')
    w3, contract = load_contract(contract_address, abi_path, network)
    return w3, contract


def send_to_snapshot(w3, snapshot_contract, hex_user):
    gas_limit = w3.interface.eth.getBlock('latest')['gasLimit']
    chain_id = w3.interface.eth.chainId

    tx = snapshot_contract.functions.addToSnapshot(hex_user.user_address, hex_user.hex_amount)
    tx_hash = sign_send_tx(w3, chain_id, gas_limit, tx)
    return tx_hash


def send_to_snapshot_batch(w3, snapshot_contract, count_start, count_end, gas_price, sleep_time):
    gas_limit = w3.interface.eth.getBlock('latest')['gasLimit']
    chain_id = w3.interface.eth.chainId

    user_list = HexUser.objects.filter(id__in=list(range(count_start, count_end)), blockchain_saved=False)

    if user_list:
        address_list = []
        amount_list = []
        for user in user_list:
            address_list.append(w3.interface.toChecksumAddress(user.user_address.lower()))
            amount_list.append(int(user.hex_amount))

        # print(address_list, flush=True)
        # print(amount_list, flush=True)
        tx = snapshot_contract.functions.addToSnapshotMultiple(address_list, amount_list)

        tx_hash = sign_send_tx(w3.interface, chain_id, gas_limit, tx,
                               SNAPSHOT_CONTRACT_SENDER_ADDR, SNAPSHOT_CONTRACT_SENDER_PRIV, str(gas_price),
                               )

        print('tx_hash', tx_hash.hex(), flush=True)

        for user in user_list:
            user.blockchain_saved = True
            user.save()

        time.sleep(sleep_time)
        return tx_hash
    else:
        print('skipped because already saved', flush=True)


def send_to_snapshot_portions(start, stop, portion, gas_price, sleep_time):
    load_contracts_dotenv()
    step_part = start + portion

    snapshot_contract_address = os.getenv('SNAPSHOT_CONTRACT_ADDRESS')

    w3, contract = load_snapshot_contract(snapshot_contract_address)
    sender_balance = w3.interface.eth.getBalance(SNAPSHOT_CONTRACT_SENDER_ADDR)
    while step_part <= stop and sender_balance > 10 ** 18:
        print(str(datetime.now()), 'Current part', start, 'to', step_part, 'account balance', sender_balance / 10 ** 18,
              flush=True)

        try:
            send_to_snapshot_batch(w3, contract, start, step_part, gas_price, sleep_time)
            sender_balance = w3.interface.eth.getBalance(SNAPSHOT_CONTRACT_SENDER_ADDR)
        except Exception as e:
            print('cannot send batch', start, stop)
            print(e)

        start += portion
        step_part = start + portion


def send_to_snapshot_all(portion, gas_price, sleep_time):
    first_id = HexUser.objects.filter(blockchain_saved=False).first().id
    last_id = HexUser.objects.filter(blockchain_saved=False).last().id

    send_to_snapshot_portions(first_id, last_id, portion, gas_price, sleep_time)


def check_snapshot_contract_amounts():
    load_contracts_dotenv()

    snapshot_contract_address = os.getenv('SNAPSHOT_CONTRACT_ADDRESS')
    w3, snapshot_contract = load_snapshot_contract(snapshot_contract_address)

    all_users = HexUser.objects.all().order_by('id')
    total_users = HexUser.objects.count()

    non_matching_user_ids = []
    for user in all_users:
        snapshot_balance = user.hex_amount
        real_balance = snapshot_contract.functions.balanceOf(user.user_address).call()

        if snapshot_balance == real_balance:
            user.rechecked = True
            user.save()

        print(user.id, '/', total_users, 'address', user.user_address, 'have hvalid amount:', user.rechecked, flush=True)

    print('Done',  flush=True)

    with open('non_matched.txt', 'w') as f:
        f.write(non_matching_user_ids)


def check_snapshot_contract_from_csv():
    load_contracts_dotenv()

    snapshot_contract_address = os.getenv('SNAPSHOT_CONTRACT_ADDRESS')
    w3, snapshot_contract = load_snapshot_contract(snapshot_contract_address)

    csv_file = open('export-tokenholders-for-contract-0x09088dd603f48d70105850718f1aec8b7aa6f8e2.csv', 'r')
    csv_dump = csv.reader(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    csv_addresses = [row for row in csv_dump]
    csv_addresses.pop(0)
    csv_addr_list = [w3.interface.toChecksumAddress(csv_addr[0]) for csv_addr in csv_addresses]

    not_in_csv = HexUser.objects.exclude(user_address__in=csv_addr_list)

    count = 0
    print('Started', flush=True)
    for user in not_in_csv:
        snapshot_balance = user.hex_amount
        real_balance = snapshot_contract.functions.balanceOf(user.user_address).call()

        if snapshot_balance != real_balance:
            user.blockchain_saved = False
        else:
            user.blockchain_saved = True

        user.save()
        count += 1
        print(count, '|', user.id, 'matched:', user.blockchain_saved, flush=True)

    print('Done', flush=True)


def check_snapshot_contract_from_etherscan():
    load_contracts_dotenv()

    snapshot_contract_address = os.getenv('SNAPSHOT_CONTRACT_ADDRESS')
    w3, snapshot_contract = load_snapshot_contract(snapshot_contract_address)

    transferred_users = HexUser.objects.all().order_by('id')

    csv_file = open('export-tokenholders-for-contract-0x09088dd603f48d70105850718f1aec8b7aa6f8e2.csv', 'r')

    csv_dump = csv.reader(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    csv_addresses = [row for row in csv_dump]
    csv_addresses.pop(0)
    total_users = len(csv_addresses)

    non_matching_user_ids = []
    non_matching_list = []
    counter = 0
    for row in csv_addresses:

        address = row[0]
        amount = row[1]

        checksum_address = w3.interface.toChecksumAddress(str(address))
        decimal_amount = w3.interface.toWei(amount, 'ether')

        user = HexUser.objects.get(user_address=checksum_address)

        appended = False
        if user.hex_amount != decimal_amount:
            non_matching_user_ids.append(user.id)
            non_matching_list.append(user)
            appended = True

        counter += 1
        print(counter, user.id, '/', total_users, 'not matched:', appended)

    print('Done', len(non_matching_user_ids), 'addresses', flush=True)
    with open('non_matched.txt', 'w') as f:
        f.write(str(non_matching_user_ids))

    return non_matching_list


def send_to_snapshot_unset(w3, snapshot_contract, user_list, gas_price, sleep_time):
    gas_limit = w3.interface.eth.getBlock('latest')['gasLimit']
    chain_id = w3.interface.eth.chainId

    if user_list:
        address_list = []
        amount_list = []
        for user in user_list:
            address_list.append(w3.interface.toChecksumAddress(user.user_address.lower()))
            amount_list.append(int(user.hex_amount))

        # print(address_list, flush=True)
        # print(amount_list, flush=True)
        tx = snapshot_contract.functions.addToSnapshotMultiple(address_list, amount_list)

        tx_hash = sign_send_tx(w3.interface, chain_id, gas_limit, tx,
                               SNAPSHOT_CONTRACT_SENDER_ADDR, SNAPSHOT_CONTRACT_SENDER_PRIV, str(gas_price),
                               )

        print('tx_hash', tx_hash.hex(), flush=True)

        for user in user_list:
            user.blockchain_saved = True
            user.save()

        time.sleep(sleep_time)
        return tx_hash
    else:
        print('skipped because already saved', flush=True)


def send_next_addresses():
    load_contracts_dotenv()

    snapshot_contract_address = os.getenv('SNAPSHOT_CONTRACT_ADDRESS')
    w3, snapshot_contract = load_snapshot_contract(snapshot_contract_address)
    not_sent_addresses = HexUser.objects.filter(blockchain_saved=False).order_by('id')
    not_sent_addresses_count = not_sent_addresses.count()
    max_addresses = 300

    while not_sent_addresses_count != 0:

        current_addr_part = not_sent_addresses[:max_addresses]
        send_to_snapshot_unset(w3, snapshot_contract, current_addr_part, gas_price=30, sleep_time=20)

        not_sent_addresses = HexUser.objects.filter(blockchain_saved=True).order_by('id')
        not_sent_addresses_count = not_sent_addresses.count()




def init_foreign_swap_contract(network='rinkeby'):
    load_contracts_dotenv()

    foreign_swap_address = os.getenv('FOREIGN_SWAP_ADDRESS')

    w3, contract = load_swap_contract(foreign_swap_address, network)

    gas_limit = w3.interface.eth.getBlock('latest')['gasLimit']
    chain_id = w3.interface.eth.chainId

    try:
        signer_address = SNAPSHOT_SIGNING_ADDR
        day_seconds = os.getenv('DAY_SECONDS')
        max_claim_amount = os.getenv('MAX_CLAIM_AMOUNT')
        token_address = os.getenv('TOKEN_ADDRESS')
        daily_auction_address = os.getenv('DAILY_AUCTION_ADDRESS')
        weekly_auction_address = os.getenv('WEEKLY_AUCTION_ADDRESS')
        staking_adrress = os.getenv('STAKING_ADDRESS')
        bpd_address = os.getenv('BPD_ADDRESS')
        total_snapshot_amount = os.getenv('TOTAL_SNAPSHOT_AMOUNT')
        total_snapshot_addresses = os.getenv('TOTAL_SNAPSHOT_ADDRESSES')

        # init_signature = '(address,uint256,uint256,address,address,address,address,address,uint256,uint256)'
        # init_args = [
        #     signer_address,
        #     int(day_seconds),
        #     int(max_claim_amount),
        #     token_address,
        #     daily_auction_address,
        #     weekly_auction_address,
        #     staking_adrress,
        #     bpd_address,
        #     int(total_snapshot_addresses),
        #     int(total_snapshot_amount)
        # ]
        #
        # encoded_params = encode_single(init_signature, init_args)
        # #print(encoded_params, flush=True)
        #
        # tx_data = contract.encodeABI('init', args=init_args)
        #
        # print(tx_data)

        tx = contract.functions.init(
            signer_address,
            int(day_seconds),
            int(max_claim_amount),
            token_address,
            daily_auction_address,
            weekly_auction_address,
            staking_adrress,
            bpd_address,
            int(total_snapshot_amount),
            int(total_snapshot_addresses)
        )
        print('tx', tx.__dict__, flush=True)

        tx_hash = sign_send_tx(w3.interface, chain_id, gas_limit, tx)
        return tx_hash

    except Exception as e:
        print('Transaction failed to send, reason:', e)



