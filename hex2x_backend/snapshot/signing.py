import binascii
import secp256k1
import datetime
import time

from eth_abi import encode_single
from web3.exceptions import TransactionNotFound

from hex2x_backend.settings import WEB3_INFURA_PROJECT_ID, BACKEND_ADDR, BACKEND_PRIV, SNAPSHOT_SIGNING_PRIV, \
    SNAPSHOT_CONTRACT_SENDER_ADDR, SNAPSHOT_CONTRACT_SENDER_PRIV
from .web3int import W3int


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


def sign_send_tx(w3, chain_id, gas, contract_tx, address=BACKEND_ADDR, priv=BACKEND_PRIV, gas_price='30'):
    nonce = w3.eth.getTransactionCount(address, 'pending')
    tx_fields = {'chainId': chain_id, 'gas': gas, 'gasPrice': w3.toWei(gas_price, 'gwei'), 'nonce': nonce}
    tx = contract_tx.buildTransaction(tx_fields)
    signed = w3.eth.account.sign_transaction(tx, priv)
    raw_tx = signed.rawTransaction
    return w3.eth.sendRawTransaction(raw_tx)


def check_wait_tx():
    w3 = W3int('infura', 'ropsten')

    nonce = w3.interface.eth.getTransactionCount(SNAPSHOT_CONTRACT_SENDER_ADDR, 'pending')
    gas_limit = w3.interface.eth.getBlock('latest')['gasLimit']
    chain_id = w3.interface.eth.chainId
    to = w3.interface.toChecksumAddress('0x849d89ffa8f91ff433a3a1d23865d15c8495cc7b')
    value = w3.interface.toWei('0.00001', 'ether')
    tx_fields = {'chainId': chain_id, 'gas': gas_limit, 'gasPrice': w3.interface.toWei('30', 'gwei'), 'nonce': nonce,
                 'to': to, 'value': value}
    signed = w3.interface.eth.account.sign_transaction(tx_fields, SNAPSHOT_CONTRACT_SENDER_PRIV)
    raw_tx = signed.rawTransaction
    tx = w3.interface.eth.sendRawTransaction(raw_tx)
    tx_hex = tx.hex()
    print(tx_hex)
    print(datetime.datetime.now())
    # w3.interface.eth.waitForTransactionReceipt(tx_hex, 240)
    retry_seconds = 240
    print('waiting receipt', flush=True)
    tx_receipt = None
    tx_confirmed = False
    for retry in range(retry_seconds):
        print(retry)
        try:
            tx_receipt = w3.interface.eth.getTransactionReceipt(tx_hex)
            if tx_receipt['blockNumber']:
                tx_confirmed = True
                break
        except TransactionNotFound:
            time.sleep(1)
            continue


    # tx_receipt = w3.interface.eth.getTransactionReceipt(tx_hex)
    print(datetime.datetime.now())
    if tx_confirmed:
        return tx_receipt
    else:
        return 'not confirmed'


# 0x4B346C42D212bBD0Bf85A01B1da80C2841149EA2
# 5

# 0x09c8CB55EfD34f89B21C43cE7d4D4c4dAB87D45b
# 10
