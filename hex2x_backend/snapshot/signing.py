import binascii
import secp256k1
import datetime
import time

from eth_abi import encode_single
from web3.exceptions import TransactionNotFound

from hex2x_backend.settings import WEB3_INFURA_PROJECT_ID, BACKEND_ADDR, BACKEND_PRIV, SNAPSHOT_SIGNING_PRIV, \
    SNAPSHOT_CONTRACT_SENDER_ADDR, SNAPSHOT_CONTRACT_SENDER_PRIV
from .web3int import W3int
from .models import HexUser, SnapshotUser, SnapshotUserTestnet


def convert_message_to_hash(w3, hex_amount, hex_user_address):
    encoded_params = encode_single('(uint256,address)', [hex_amount, hex_user_address])
    return w3.solidityKeccak(['bytes'], [encoded_params])


def sign_message(message):
    priv = secp256k1.PrivateKey(binascii.unhexlify(SNAPSHOT_SIGNING_PRIV))
    signature = priv.ecdsa_recoverable_serialize(priv.ecdsa_sign_recoverable(message, raw=True))
    rec_bytes = '1c' if signature[1] == 1 else '1b'
    return '0x' + binascii.hexlify(signature[0]).decode('utf-8') + rec_bytes


def get_user_signature(network, hex_address, hex_amount):
    w3 = W3int(network).interface
    converted_message = convert_message_to_hash(w3, hex_amount, hex_address)
    signed_message = sign_message(converted_message)
    return {'msg_hash': converted_message, 'signature': signed_message}


def create_and_generate(network, hex_address, hex_amount):
    hex_address = hex_address.lower()
    user = SnapshotUserTestnet(user_address=hex_address, hex_amount=hex_amount)
    sign_info = get_user_signature(network, hex_address, hex_amount)
    user.user_hash = sign_info['msg_hash']
    user.hash_signature = sign_info['signature']
    user.save()
    return user


def sign_send_tx(w3, chain_id, gas, contract_tx, address=BACKEND_ADDR, priv=BACKEND_PRIV, gas_price='150'):
    nonce = w3.eth.getTransactionCount(address, 'pending')
    tx_fields = {'chainId': chain_id, 'gas': gas, 'gasPrice': w3.toWei(gas_price, 'gwei'), 'nonce': nonce}
    tx = contract_tx.buildTransaction(tx_fields)
    signed = w3.eth.account.sign_transaction(tx, priv)
    raw_tx = signed.rawTransaction
    return w3.eth.sendRawTransaction(raw_tx)

