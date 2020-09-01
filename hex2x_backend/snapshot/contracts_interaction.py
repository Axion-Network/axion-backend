from .web3int import W3int
from .signing import sign_send_tx
from .models import HexUser

import os
import json
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


def send_to_snapshot_batch(w3, snapshot_contract, count_start, count_end):
    gas_limit = w3.interface.eth.getBlock('latest')['gasLimit']
    chain_id = w3.interface.eth.chainId

    user_list = HexUser.objects.filter(id__in=list(range(count_start, count_end)), blockchain_saved=False)

    if user_list:
        address_list = []
        amount_list = []
        for user in user_list:
            address_list.append(w3.interface.toChecksumAddress(user.user_address.lower()))
            amount_list.append(int(user.hex_amount))

        print(address_list, flush=True)
        print(amount_list, flush=True)
        tx = snapshot_contract.functions.addToSnapshotMultiple(address_list, amount_list)

        tx_hash = sign_send_tx(w3.interface, chain_id, gas_limit, snapshot_contract.address, tx,
                               SNAPSHOT_CONTRACT_SENDER_ADDR, SNAPSHOT_CONTRACT_SENDER_PRIV, '10',
                               )

        print('tx_hash', tx_hash.hex(), flush=True)

        for user in user_list:
            user.blockchain_saved = True
            user.save()

        return tx_hash
    else:
        print('skipped because already saved', flush=True)


def send_to_snapshot_portions(start, stop):
    step_part = start + 350

    snapshot_contract_address = os.getenv('SNAPSHOT_CONTRACT_ADDRESS')

    w3, contract = load_snapshot_contract(snapshot_contract_address)
    sender_balance = w3.interface.eth.getBalance(BACKEND_ADDR)
    while step_part <= stop and sender_balance > 10 ** 18:
        print(str(datetime.now()), 'Current part', start, 'to', step_part, 'account balance', sender_balance / 10 ** 18,
              flush=True)

        start += 350
        step_part = start + 350

        try:
            send_to_snapshot_batch(w3, contract, start, step_part)
            sender_balance = w3.interface.eth.getBalance(BACKEND_ADDR)
        except Exception as e:
            print('cannot send batch', start, stop)
            print(e)


def send_to_snapshot_all():
    first_id = HexUser.objects.first().id
    last_id = HexUser.objects.last().id

    send_to_snapshot_portions(first_id, last_id)


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

        tx_hash = sign_send_tx(w3.interface, chain_id, contract.address, gas_limit, tx)
        return tx_hash

    except Exception as e:
        print('Transaction failed to send, reason:', e)



