import os
import sys

# Ensure Django is set up
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bnb_hack.settings')
import django
django.setup()

from dotenv import load_dotenv
load_dotenv()

from core.engines.bnb_chain import BNBChainExecutor, validate_private_key

# Test 1: Validate private key
key = os.getenv('WALLET_PRIVATE_KEY', '')
print(f"Private key length: {len(key.strip())} chars")
try:
    clean_key = validate_private_key(key)
    print("Key validation: PASSED")
except Exception as e:
    print(f"Key validation: FAILED - {e}")
    sys.exit(1)

# Test 2: Try to connect and check balance
try:
    executor = BNBChainExecutor()
    print(f"Wallet address: {executor.wallet_address}")
    balance = executor.get_balance()
    bnb_val = balance["balance_bnb"]
    print(f"tBNB Balance: {bnb_val} BNB")
    if bnb_val < 0.001:
        print("WARNING: Low balance! Get tBNB from https://testnet.bnbchain.org/faucet-smart")
    else:
        print("Balance sufficient for trades!")
except Exception as e:
    print(f"Connection/balance error: {e}")
