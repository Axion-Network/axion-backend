from .models import HexUser
from holder_parsing import get_hex_balance_for_address, get_hex_balance_for_multiple_address
from .signing import get_user_signature
from .web3int import W3int
from holder_parsing import load_hex_contract


def regenerate_db_amount_signatures():
    all_users = HexUser.objects.all().order_by('id')

    w3 = W3int('parity')
    hex_contract = load_hex_contract(w3.interface)

    for hex_user in all_users:
        try:
            print('Progress: {curr}/{total}'.format(curr=hex_user.id, total=len(all_users)), flush=True)
            #hex_user.hex_amount = get_hex_balance_for_multiple_address(w3.interface, hex_contract, hex_user.user_address)
            hex_user.hex_amount = get_hex_balance_for_address(hex_user.user_address)
            sign_info = get_user_signature('mainnet', hex_user.user_address, int(hex_user.hex_amount))
            hex_user.user_hash = sign_info['msg_hash'].hex()
            hex_user.hash_signature = sign_info['signature']
            hex_user.save()
        except Exception as e:
            print('error in parsing', hex_user.id, hex_user.user_address)
            print(e)


def regenerate_db_amount_signatures_from(count_start, count_stop=None):
    if not count_stop:
        count_stop=HexUser.objects.all().last().id

    all_users = HexUser.objects.filter(id__in=list(range(count_start, count_stop)))

    w3 = W3int('parity')
    hex_contract = load_hex_contract(w3.interface)

    for hex_user in all_users:
        print('Progress: {curr}/{total}'.format(curr=hex_user.id, total=len(all_users)), flush=True)
        hex_user.hex_amount = get_hex_balance_for_multiple_address(w3.interface, hex_contract, hex_user.user_address)
        sign_info = get_user_signature('mainnet', hex_user.user_address, int(hex_user.hex_amount))
        hex_user.user_hash = sign_info['msg_hash'].hex()
        hex_user.hash_signature = sign_info['signature']
        hex_user.save()


def generate_and_save_signature(hex_user):
    sign_info = get_user_signature('mainnet', hex_user.user_address, int(hex_user.hex_amount))
    hex_user.user_hash = sign_info['msg_hash'].hex()
    hex_user.hash_signature = sign_info['signature']
    hex_user.save()
    print('user:', hex_user.user_address, 'hash:', hex_user.user_hash, 'signature:', hex_user.hash_signature)
