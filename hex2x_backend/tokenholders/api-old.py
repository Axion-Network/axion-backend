from hex2x_backend.snapshot.web3int import W3int

HEX_WIN_TOKEN_ADDRESS = '0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39'
CONTRACT_CREATION_BLOCK = 9041184
TRANSFERS_STARTED_BLOCK = 9046420
MAINNET_STOP_BLOCK = 10684948


def get_transfer_logs(address, from_block, to_block):
    """Get logs of Transfer events of a contract"""
    from_block = from_block or hex(TRANSFERS_STARTED_BLOCK)
    transfer_hash = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    params = [{"address": address, "fromBlock": hex(from_block), "toBlock": hex(to_block), "topics": [transfer_hash]}]
    w3 = W3int('parity')
    req = w3.get_http_rpc_response("eth_getLogs", params)

    if 'result' in req:
        logs = req['result']
    else:
        logs = []
        print(req)

    return logs


def get_hex_transfer_logs_to(step_block):
    return get_transfer_logs(HEX_WIN_TOKEN_ADDRESS, TRANSFERS_STARTED_BLOCK, TRANSFERS_STARTED_BLOCK + step_block)


def get_transfers_from_logs(transfer_logs):
    transfer_models = []

    for log in transfer_logs:
        # log["amount"] = Decimal(str(int(log["data"], 16))) * decimals_factor
        # log["from"] = log["topics"][1][0:2] + log["topics"][1][26:]
        # log["to"] = log["topics"][2][0:2] + log["topics"][2][26:]
        print('full log', log)

        from_addr = log["topics"][1][0:2] + log["topics"][1][26:]
        print(from_addr)
        to_addr = log["topics"][2][0:2] + log["topics"][2][26:]
        print(to_addr)

    return transfer_models