## Axion Snapshot Backend

## Install
1. Install Python >= 3.6
2. Create virtualenv: `python3 -m venv venv`
3. Activate virtualenv: `source venv/bin/activate`
4. Install requirements: `pip install -r requirements.txt`
5. Setup database

## Generating snapshot (HEX Freeclaim)

1. Get snapshot for all token transfers: `python transfer_dump_launcher.py`
2. Get snapshot for all stakings:
  - Snapshot of staking starts: `python stake_dump_launcher.py stake_start`
  - Snapshot of staking starts: `python stake_dump_launcher.py stake_end`
  - Filter out ended stakings: `python make_persisted_stake_snapshot.py`
3. Create balances for raw tokens: `python make_balance_snapshot.py`
4. Create balances for shares tokens: `python make_balance_shares_snapshot.py`
5. Combine token and shares balance to users: `python make_full_hex_user_snapshot.py`

Final addreses will be in model SnapshotUser.

## Generating snapshot (HEX2T)

1. Get snapshot for all token transfers: `python transfer_hex2t_launcher.py`
3. Create balances for raw tokens: `python make_hex2t_balance_snapshot.py` 

