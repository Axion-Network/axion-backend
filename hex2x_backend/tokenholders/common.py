import json

HEX_WIN_TOKEN_ADDRESS = '0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39'
CONTRACT_CREATION_BLOCK = 9041184
TRANSFERS_STARTED_BLOCK = 9046420
MAINNET_STOP_BLOCK = 10150928


def load_hex_contract(web3_interface):
    with open('./HEX_abi.json', 'r') as f:
        erc20_abi = json.loads(f.read())

    hex_contract = web3_interface.eth.contract(address=HEX_WIN_TOKEN_ADDRESS, abi=erc20_abi)
    return hex_contract