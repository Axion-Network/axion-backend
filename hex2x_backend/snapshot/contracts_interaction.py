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

from web3.exceptions import TransactionNotFound

from django.core.paginator import Paginator

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


def check_snapshot_contract_amounts(all_users):
    load_contracts_dotenv()

    snapshot_contract_address = os.getenv('SNAPSHOT_CONTRACT_ADDRESS')
    w3, snapshot_contract = load_snapshot_contract(snapshot_contract_address, 'ropsten')

    total_users = all_users.count()

    non_matching_user_ids = []
    for user in all_users:
        snapshot_balance = user.hex_amount
        real_balance = snapshot_contract.functions.balanceOf(user.user_address).call()

        if snapshot_balance == real_balance:
            user.tx_possible_fail = True
            user.save()

        print(user.id, '/', total_users, 'address', user.user_address, 'have valid amount:', user.tx_possible_fail, flush=True)

    print('Done',  flush=True)

    with open('non_matched.txt', 'w') as f:
        writer = csv.writer(f,  delimiter=',', quoting=csv.QUOTE_MINIMAL)
        for id in non_matching_user_ids:
            writer.writerow([id])


def send_next_addresses(max_addresses, gas_price, retry_seconds,):
    addresses = HexUser.objects.filter(snapshot_tx=None).order_by('id')
    addresses_count = addresses.count()
    print('Starting migration of ', addresses_count, 'addresses with page size', max_addresses,
          'gas price', gas_price, 'retry wait', retry_seconds, flush=True
          )
    load_contracts_dotenv()

    snapshot_contract_address = os.getenv('SNAPSHOT_CONTRACT_ADDRESS')
    w3, snapshot_contract = load_snapshot_contract(snapshot_contract_address, 'ropsten')
    print('snapshot contract address', snapshot_contract.address, flush=True)

    # gas_limit = w3.interface.eth.getBlock('latest')['gasLimit']
    gas_limit = 7900000
    chain_id = w3.interface.eth.chainId

    # addresses = HexUser.objects.filter(id__gte=start, id__lte=stop, snapshot_tx=None).order_by('id')

    paginator = Paginator(addresses, max_addresses)
    print('Total pages', paginator.num_pages, flush=True)

    page = paginator.page(1)

    while page.has_next():
        user_list = page.object_list

        print('users:', len(user_list), flush=True)

        if len(user_list) == 0:
            return {'reason': 'exited'}
        user_id_start = user_list[0].id
        user_id_end = user_list[len(user_list) - 1].id

        try:
            sender_balance = w3.interface.eth.getBalance(SNAPSHOT_CONTRACT_SENDER_ADDR)
            if sender_balance < w3.interface.toWei('1', 'ether'):
                print('not enough balance', sender_balance, ', stopping', flush=True)
                return {'reason': 'balance'}
            print(str(datetime.now()), 'sending', user_id_start, '-', user_id_end, 'total :', addresses_count, flush=True)

            address_list = []
            amount_list = []
            for user in user_list:
                address_list.append(w3.interface.toChecksumAddress(user.user_address.lower()))
                amount_list.append(int(user.hex_amount))

            tx = snapshot_contract.functions.addToSnapshotMultiple(address_list, amount_list)

            tx_hash = sign_send_tx(w3.interface, chain_id, gas_limit, tx,
                                   SNAPSHOT_CONTRACT_SENDER_ADDR, SNAPSHOT_CONTRACT_SENDER_PRIV, str(gas_price),
                                   )
            tx_hash_hex = tx_hash.hex()
            print('page', page.number, 'tx:', tx_hash_hex, 'waiting receipt',  flush=True)
            # w3.interface.eth.waitForTransactionReceipt(tx_hash_hex, wait)

            tx_confirmed = False
            for retry in range(retry_seconds):
                try:
                    tx_receipt = w3.interface.eth.getTransactionReceipt(tx_hash_hex)
                    if tx_receipt:
                        if tx_receipt['status'] == 1:
                            tx_confirmed = True
                            print('tx confirmed', flush=True)
                            break
                        elif tx_receipt['status'] == 0:
                            print('tx reverted', flush=True)
                            break
                        else:
                            print('tx may failed, receipt found without status', flush=True)
                            break
                except TransactionNotFound:
                    time.sleep(1)
                    continue

            if not tx_confirmed:
                for user in user_list:
                    user.snapshot_tx = tx_hash_hex
                    user.tx_possible_fail = True
                    user.save()
                raise Exception('transaction failed or not appeared in %s seconds' % retry_seconds)
            # tx_receipt = w3.interface.eth.getTransactionReceipt(tx_hash_hex)
            sender_balance = w3.interface.eth.getBalance(SNAPSHOT_CONTRACT_SENDER_ADDR)

            for user in user_list:
                user.snapshot_tx = tx_hash_hex
                user.save()

            print(user_id_start, '/', user_id_end, 'of', addresses_count, ': sent, balance:', sender_balance,
                  flush=True)
        except Exception as e:
            print(user_id_start, '/', user_id_end, 'of', addresses_count, ': FAILED to send, because:', e,
                  flush=True)

        next_page_number = page.next_page_number()
        page = paginator.page(next_page_number)

    return {'reason': 'finished'}

def get_sent_addresses_paginator():
    start = 1
    stop = HexUser.objects.count()
    max_addresses = 150

    addresses = HexUser.objects.filter(id__gte=start, id__lte=stop).order_by('id')
    paginator = Paginator(addresses, max_addresses)
    return paginator


def check_failed_txs():
    failed_addresses = HexUser.objects.filter(tx_possible_fail=True).values('snapshot_tx').distinct()
    failed_tx_list = [tx['snapshot_tx'] for tx in failed_addresses]
    w3 = W3int('infura', 'ropsten')

    checked_txs = {}
    for tx in failed_tx_list:
        try:
            receipt = w3.interface.eth.getTransactionReceipt(tx)
            if receipt['status'] == 1:
                checked_txs[tx] = receipt
            else:
                checked_txs[tx] = None
        except TransactionNotFound:
            ckecked_txs[tx] = None

    return checked_txs


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



