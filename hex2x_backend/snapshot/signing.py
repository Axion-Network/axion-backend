import binascii
import secp256k1

from eth_abi import encode_single

from hex2x_backend.settings import WEB3_INFURA_PROJECT_ID, BACKEND_ADDR, BACKEND_PRIV
from .web3int import W3int


def convert_message_to_hash(w3, hex_amount, hex_user_address):
    encoded_params = encode_single('(uint256,address)', [hex_amount, hex_user_address])
    return w3.solidityKeccak(['bytes'], [encoded_params])


def sign_message(message):
    priv = secp256k1.PrivateKey(binascii.unhexlify(BACKEND_PRIV))
    signature = priv.ecdsa_recoverable_serialize(priv.ecdsa_sign_recoverable(message, raw=True))
    rec_bytes = '1c' if signature[1] == 1 else '1b'
    return '0x' + binascii.hexlify(signature[0]).decode('utf-8') + rec_bytes


def get_user_signature(network, hex_address, hex_amount):
    w3 = W3int(network).interface
    converted_message = convert_message_to_hash(w3, hex_amount, hex_address)
    signed_message = sign_message(converted_message)
    return {'msg_hash': converted_message, 'signature': signed_message}


def sign_send_tx(w3, chain_id, gas, contract_tx):
    nonce = w3.eth.getTransactionCount(BACKEND_ADDR)
    tx_fields = {'chainId': chain_id, 'gas': gas, 'gasPrice': w3.toWei('30', 'gwei'), 'nonce': nonce}
    tx = contract_tx.buildTransaction(tx_fields)
    signed = w3.eth.account.sign_transaction(tx, BACKEND_PRIV)
    raw_tx = signed.rawTransaction
    return w3.eth.sendRawTransaction(raw_tx)


# 0x4B346C42D212bBD0Bf85A01B1da80C2841149EA2
# 5

# 0x09c8CB55EfD34f89B21C43cE7d4D4c4dAB87D45b
# 10
