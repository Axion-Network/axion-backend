import binascii
import secp256k1

from web3 import Web3, HTTPProvider
from eth_abi import encode_single
from eth_account.messages import encode_defunct

from hex2x_backend.settings import WEB3_INFURA_PROJECT_ID, WEB3_INFURA_PROJECT_SECRET, BACKEND_ADDR, BACKEND_PRIV


def initiate_web3(network):
    infura_url = 'https://{subdomain}.infura.io/v3/{proj_id}'\
            .format(subdomain=network, proj_id=WEB3_INFURA_PROJECT_ID)
    return Web3(HTTPProvider(infura_url))


def convert_message_to_hash(w3, hex_amount, hex_user_address):
    # w3 = initiate_web3('ropsten')
    # types_params = '(uint256,address)'
    types_params = ['uint256', 'address']
    encoded_params = encode_single('(uint256,address)', [hex_amount, hex_user_address])
    return w3.solidityKeccak(['bytes'], [encoded_params])


def bytearray_to_bytestr(value):
    #return bytes(''.join(chr(c) for c in value))
    return bytes(value)


def sign_message(message):
    priv = secp256k1.PrivateKey(binascii.unhexlify(BACKEND_PRIV))
    signature = priv.ecdsa_recoverable_serialize(priv.ecdsa_sign_recoverable(message, raw=True))
    signature = signature[0] + bytearray_to_bytestr([signature[1]])
    return '0x' + binascii.hexlify(signature)


def get_user_signature(network, hex_address, hex_amount):
    w3 = initiate_web3(network)
    converted_message = convert_message_to_hash(w3, hex_amount, hex_address)
    print(converted_message)
    signed_message = sign_message(w3, converted_message)
    print(signed_message)
    return signed_message


def sign_send_tx(w3, chain_id, contract_tx):
    nonce = w3.eth.getTransactionCoint(BACKEND_ADDR)
    tx_fields = {'chainId': chain_id, 'gas': 1000000, 'gasPrice': w3.toWei('30', 'gwei'), 'nonce': nonce}
    tx = contract_tx.buildTransaction(tx_fields)
    signed = w3.eth.account.sign_transaction(tx, BACKEND_PRIV)
    raw_tx = signed.rawTransaction
    return w3.eth.sendRawTransaction(raw_tx)


# 0x4B346C42D212bBD0Bf85A01B1da80C2841149EA2
# 5
