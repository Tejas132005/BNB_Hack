"""
BNB Chain Testnet Real Transaction Executor
============================================
Handles real BNB Testnet transactions using web3.py.
- Validates wallet private key
- Connects to BNB Testnet RPC
- Signs and sends transactions server-side
- Returns real transaction hashes
- Full error handling for all edge cases

SECURITY: Private key NEVER leaves the server.
"""
import os
import re
import logging
from decimal import Decimal
from datetime import datetime
from dotenv import load_dotenv

from web3 import Web3
from web3.exceptions import (
    TransactionNotFound,
)

load_dotenv()

logger = logging.getLogger(__name__)

# ──────────────────────────────────
# Constants
# ──────────────────────────────────
BNB_TESTNET_CHAIN_ID = 97
EXPLORER_BASE_URL = "https://testnet.bscscan.com/tx/"
DEFAULT_RPC_URL = "https://data-seed-prebsc-1-s1.binance.org:8545/"

# Fallback RPC URLs in case the primary fails
FALLBACK_RPC_URLS = [
    "https://data-seed-prebsc-2-s1.binance.org:8545/",
    "https://data-seed-prebsc-1-s2.binance.org:8545/",
    "https://data-seed-prebsc-2-s2.binance.org:8545/",
]

# Minimum transaction value in Wei (0.0001 BNB)
MIN_TX_VALUE_WEI = Web3.to_wei(0.0001, 'ether')

# Data payload prefixes to mark trade type in the transaction's input data
TRADE_DATA_PREFIXES = {
    'BUY':   '0x4255590000',   # "BUY\x00\x00"
    'SELL':  '0x53454c4c00',   # "SELL\x00"
    'STOP':  '0x53544f5000',   # "STOP\x00"
    'LIMIT': '0x4c494d4954',   # "LIMIT"
}


class BNBChainError(Exception):
    """Base exception for BNB Chain operations."""
    pass


class InvalidPrivateKeyError(BNBChainError):
    """Raised when the wallet private key is invalid or missing."""
    pass


class InsufficientFundsError(BNBChainError):
    """Raised when the wallet has insufficient tBNB."""
    pass


class RPCConnectionError(BNBChainError):
    """Raised when the RPC endpoint is unreachable."""
    pass


class TransactionFailedError(BNBChainError):
    """Raised when a transaction fails on-chain."""
    pass


def validate_private_key(private_key: str) -> str:
    """
    Validate the format of a private key.
    Must be exactly 64 hex characters (with optional 0x prefix).
    
    Returns: cleaned key (without 0x prefix)
    Raises: InvalidPrivateKeyError
    """
    if not private_key:
        raise InvalidPrivateKeyError("WALLET_PRIVATE_KEY is not set in .env file.")

    # Strip whitespace and quotes
    key = private_key.strip().strip('"').strip("'")

    # Remove 0x prefix if present
    if key.startswith('0x') or key.startswith('0X'):
        key = key[2:]

    # Validate hex format and length
    if not re.match(r'^[0-9a-fA-F]{64}$', key):
        raise InvalidPrivateKeyError(
            "WALLET_PRIVATE_KEY format invalid. Must be exactly 64 hex characters."
        )

    return key


def get_web3_connection(rpc_url: str = None) -> Web3:
    """
    Establish a Web3 connection to BNB Testnet.
    Tries primary and fallback RPCs.
    
    Returns: Web3 instance
    Raises: RPCConnectionError
    """
    urls_to_try = []

    if rpc_url:
        urls_to_try.append(rpc_url)

    env_rpc = os.getenv('BNB_TESTNET_RPC', '').strip().strip('"').strip("'")
    if env_rpc and env_rpc not in urls_to_try:
        urls_to_try.append(env_rpc)

    urls_to_try.append(DEFAULT_RPC_URL)
    urls_to_try.extend(FALLBACK_RPC_URLS)

    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for u in urls_to_try:
        if u and u not in seen:
            seen.add(u)
            unique_urls.append(u)

    for url in unique_urls:
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
            if w3.is_connected():
                # Verify we're on the right chain
                chain_id = w3.eth.chain_id
                if chain_id != BNB_TESTNET_CHAIN_ID:
                    logger.warning(
                        f"RPC {url} returned chain_id={chain_id}, expected {BNB_TESTNET_CHAIN_ID}. "
                        f"Proceeding anyway (may be a different network)."
                    )
                return w3
        except Exception as e:
            logger.warning(f"Failed to connect to RPC {url}: {e}")
            continue

    raise RPCConnectionError(
        "Could not connect to BNB Testnet. All RPC endpoints failed. "
        "Please check your internet connection and BNB_TESTNET_RPC in .env."
    )


class BNBChainExecutor:
    """
    Real transaction executor for BNB Chain Testnet.
    
    Usage:
        executor = BNBChainExecutor()
        result = executor.execute_trade('BUY', value_bnb=0.0001)
    """

    def __init__(self):
        """
        Initialize the executor.
        Validates the private key and connects to the RPC.
        Does NOT log the private key.
        """
        # Get and validate private key
        raw_key = os.getenv('WALLET_PRIVATE_KEY', '')
        self._private_key_hex = validate_private_key(raw_key)
        self._private_key = '0x' + self._private_key_hex

        # Connect to BNB Testnet
        self.w3 = get_web3_connection()

        # Derive wallet address from private key
        try:
            account = self.w3.eth.account.from_key(self._private_key)
            self.wallet_address = account.address
        except Exception as e:
            raise InvalidPrivateKeyError(
                f"Could not derive wallet from WALLET_PRIVATE_KEY: {str(e)}"
            )

        logger.info(f"BNBChainExecutor initialized. Wallet: {self.wallet_address}")

    def get_balance(self) -> dict:
        """Get the wallet's tBNB balance."""
        try:
            balance_wei = self.w3.eth.get_balance(self.wallet_address)
            balance_bnb = self.w3.from_wei(balance_wei, 'ether')
            return {
                'address': self.wallet_address,
                'balance_wei': balance_wei,
                'balance_bnb': float(balance_bnb),
            }
        except Exception as e:
            raise RPCConnectionError(f"Failed to get balance: {str(e)}")

    def execute_trade(self, action: str, value_bnb: float = 0.0001) -> dict:
        """
        Execute a real transaction on BNB Testnet.
        
        The transaction sends a small amount of tBNB to the wallet's own address
        (self-transfer) with trade type encoded in the input data field.
        This creates a real on-chain record of the trade action.

        Args:
            action: One of 'BUY', 'SELL', 'STOP', 'LIMIT'
            value_bnb: Amount of tBNB to send (default: 0.0001 BNB)

        Returns:
            dict with success status, tx_hash, explorer_url, etc.

        Raises:
            InvalidPrivateKeyError, InsufficientFundsError,
            RPCConnectionError, TransactionFailedError
        """
        if action not in TRADE_DATA_PREFIXES:
            raise ValueError(f"Invalid action: {action}. Must be BUY, SELL, STOP, or LIMIT.")

        # Convert to Wei
        value_wei = self.w3.to_wei(value_bnb, 'ether')

        # ── 1. Check balance ──
        try:
            balance_wei = self.w3.eth.get_balance(self.wallet_address)
        except Exception as e:
            raise RPCConnectionError(f"Failed to query balance: {str(e)}")

        balance_bnb = float(self.w3.from_wei(balance_wei, 'ether'))

        # Estimate gas cost (gas_limit * gas_price) + value
        try:
            gas_price = self.w3.eth.gas_price
        except Exception as e:
            raise RPCConnectionError(f"Failed to get gas price: {str(e)}")

        estimated_gas = 30000  # Self-transfer with data ~25k-30k gas
        estimated_total_cost = value_wei + (estimated_gas * gas_price)

        if balance_wei < estimated_total_cost:
            raise InsufficientFundsError(
                f"Insufficient tBNB. Balance: {balance_bnb:.6f} BNB. "
                f"Required: ~{float(self.w3.from_wei(estimated_total_cost, 'ether')):.6f} BNB. "
                f"Get testnet BNB from https://testnet.bnbchain.org/faucet-smart"
            )

        # ── 2. Build data payload ──
        # Encode: trade type prefix + action name + timestamp
        data_str = f"{action}|NeutraYield|{datetime.now().isoformat()}"
        data_hex = '0x' + data_str.encode('utf-8').hex()

        # ── 3. Get nonce ──
        try:
            nonce = self.w3.eth.get_transaction_count(self.wallet_address, 'pending')
        except Exception as e:
            raise RPCConnectionError(f"Failed to get nonce: {str(e)}")

        # ── 4. Build transaction ──
        tx = {
            'nonce': nonce,
            'to': self.wallet_address,  # Self-transfer
            'value': value_wei,
            'gas': estimated_gas,
            'gasPrice': gas_price,
            'chainId': BNB_TESTNET_CHAIN_ID,
            'data': data_hex,
        }

        # ── 5. Estimate gas (more accurate) ──
        try:
            estimated_gas_precise = self.w3.eth.estimate_gas(tx)
            # Add 20% buffer
            tx['gas'] = int(estimated_gas_precise * 1.2)
        except Exception as e:
            logger.warning(f"Gas estimation failed, using default: {e}")
            tx['gas'] = 35000  # Use higher default

        # ── 6. Sign transaction ──
        try:
            signed_tx = self.w3.eth.account.sign_transaction(tx, self._private_key)
        except Exception as e:
            raise InvalidPrivateKeyError(
                f"Transaction signing failed: {str(e)}"
            )

        # ── 7. Send transaction ──
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            if not tx_hash_hex.startswith('0x'):
                tx_hash_hex = '0x' + tx_hash_hex
        except Exception as e:
            error_msg = str(e).lower()
            if 'insufficient funds' in error_msg or 'insufficient balance' in error_msg:
                raise InsufficientFundsError(
                    f"Transaction rejected: Insufficient tBNB for gas. "
                    f"Get testnet BNB from https://testnet.bnbchain.org/faucet-smart"
                )
            elif 'nonce' in error_msg:
                raise TransactionFailedError(
                    f"Nonce conflict. A pending transaction may exist. Details: {str(e)}"
                )
            elif 'chain' in error_msg or 'chainid' in error_msg:
                raise TransactionFailedError(
                    f"Chain ID mismatch. Ensure you're on BNB Testnet (chainId=97). Details: {str(e)}"
                )
            else:
                raise TransactionFailedError(f"Transaction send failed: {str(e)}")

        # ── 8. Wait for receipt (with timeout) ──
        block_number = None
        gas_used = None
        status_str = 'Pending'
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
            block_number = receipt.get('blockNumber')
            gas_used = receipt.get('gasUsed')
            tx_status = receipt.get('status', 0)
            status_str = 'Confirmed' if tx_status == 1 else 'Failed'

            if tx_status != 1:
                raise TransactionFailedError(
                    f"Transaction mined but reverted (status=0). TX: {tx_hash_hex}"
                )
        except TransactionFailedError:
            raise
        except Exception as e:
            # Transaction was sent but receipt wait timed out - still valid
            logger.warning(f"Receipt wait timeout for {tx_hash_hex}: {e}")
            status_str = 'Pending'

        # ── 9. Calculate gas fee ──
        gas_fee_bnb = None
        if gas_used and gas_price:
            gas_fee_wei = gas_used * gas_price
            gas_fee_bnb = float(self.w3.from_wei(gas_fee_wei, 'ether'))

        explorer_url = f"{EXPLORER_BASE_URL}{tx_hash_hex}"

        return {
            'success': True,
            'action': action,
            'chain': 'BNB Chain',
            'network': 'BSC Testnet',
            'tx_hash': tx_hash_hex,
            'explorer_url': explorer_url,
            'block_number': block_number,
            'gas_used': gas_used,
            'gas_price_gwei': float(self.w3.from_wei(gas_price, 'gwei')),
            'gas_fee_bnb': gas_fee_bnb,
            'value_bnb': value_bnb,
            'wallet_address': self.wallet_address,
            'nonce': nonce,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': status_str,
        }


def execute_real_trade(action: str, value_bnb: float = 0.0001) -> dict:
    """
    Convenience function to execute a real trade.
    Handles all error types and returns a uniform response.
    
    Returns:
        dict: Always has 'success' key. On failure, includes 'error' key.
    """
    try:
        executor = BNBChainExecutor()
        return executor.execute_trade(action, value_bnb)
    except InvalidPrivateKeyError as e:
        logger.error(f"Private key error: {e}")
        return {
            'success': False,
            'error': str(e),
            'error_type': 'INVALID_PRIVATE_KEY',
        }
    except InsufficientFundsError as e:
        logger.error(f"Insufficient funds: {e}")
        return {
            'success': False,
            'error': str(e),
            'error_type': 'INSUFFICIENT_FUNDS',
        }
    except RPCConnectionError as e:
        logger.error(f"RPC connection error: {e}")
        return {
            'success': False,
            'error': str(e),
            'error_type': 'RPC_ERROR',
        }
    except TransactionFailedError as e:
        logger.error(f"Transaction failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'error_type': 'TX_FAILED',
        }
    except Exception as e:
        logger.exception(f"Unexpected error in trade execution: {e}")
        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}",
            'error_type': 'UNKNOWN',
        }
