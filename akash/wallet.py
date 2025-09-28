import bech32
import hashlib
import hmac
import logging
import struct
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecdsa.util import sigencode_string_canonize
from mnemonic import Mnemonic
from typing import Dict, List, Optional, Tuple, Any

from akash.modules.auth.utils import validate_address

logger = logging.getLogger(__name__)


class AkashWallet:
    """
    Wallet for Akash Network supporting BIP39/BIP44 key derivation and transaction signing.

    This wallet implementation provides:
    - Mnemonic-based wallet creation and restoration
    - secp256k1 key pair generation
    - Akash address derivation (bech32 with 'akash' prefix)
    - Transaction signing for Cosmos SDK transactions

    Example:
        ```python
        # Create from mnemonic
        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        wallet = AkashWallet.from_mnemonic(mnemonic)
        print(f"Address: {wallet.address}")

        # Generate new wallet
        new_wallet = AkashWallet.generate()
        print(f"New wallet address: {new_wallet.address}")
        print(f"Mnemonic: {new_wallet.mnemonic}")

        # Sign transaction data
        tx_data = {"msg": "test"}
        signature = wallet.sign_transaction(tx_data)
        ```
    """

    # BIP44 derivation path for Cosmos chains: m/44'/118'/0'/0/0
    COSMOS_DERIVATION_PATH = [44 + 0x80000000, 118 + 0x80000000, 0x80000000, 0, 0]

    def __init__(self, private_key: SigningKey, mnemonic: Optional[str] = None):
        """
        Initialize wallet with a private key.

        Args:
            private_key (SigningKey): The secp256k1 private key
            mnemonic (Optional[str]): The mnemonic phrase (if created from mnemonic)
        """
        self._private_key = private_key
        self._public_key = private_key.verifying_key
        self._mnemonic = mnemonic
        self._address = self._derive_address()

        logger.info(f"Initialized wallet with address: {self._address}")

    @classmethod
    def generate(
        cls, strength: int = 128, passphrase: str = "", derivation_path: str = None
    ) -> "AkashWallet":
        """
        Generate a new random wallet with proper BIP39 mnemonic.

        Args:
            strength (int): Entropy strength in bits (128, 160, 192, 224, 256)
                          Maps to 12, 15, 18, 21, 24 word mnemonics respectively
            passphrase (str): Optional BIP39 passphrase for additional security
            derivation_path (str): Optional custom derivation path (e.g., "m/44'/118'/0'/0/1")
                                 Defaults to "m/44'/118'/0'/0/0" (Cosmos standard)

        Returns:
            AkashWallet: New wallet instance

        Example:
            ```python
            # Generate 12-word mnemonic with default path
            wallet = AkashWallet.generate()
            print(f"Address: {wallet.address}")
            print(f"Mnemonic: {wallet.mnemonic}")

            # Generate 24-word mnemonic (256 bits entropy)
            secure_wallet = AkashWallet.generate(256)
            print(f"Secure mnemonic: {secure_wallet.mnemonic}")

            # Generate with custom derivation path for multiple accounts
            account1 = AkashWallet.generate(derivation_path="m/44'/118'/0'/0/0")
            account2 = AkashWallet.generate(derivation_path="m/44'/118'/0'/0/1")
            print(f"Account 1: {account1.address}")
            print(f"Account 2: {account2.address}")
            # Same mnemonic would generate both addresses with different paths

            # Generate with passphrase for extra security
            protected = AkashWallet.generate(passphrase="my-secret-passphrase")
            print(f"Protected wallet: {protected.address}")
            ```
        """
        mnemo = Mnemonic("english")
        mnemonic = mnemo.generate(strength=strength)

        logger.info(f"Generated new wallet with {len(mnemonic.split())} word mnemonic")
        return cls.from_mnemonic(
            mnemonic, passphrase=passphrase, derivation_path=derivation_path
        )

    @classmethod
    def from_mnemonic(
        cls, mnemonic: str, passphrase: str = "", derivation_path: str = None
    ) -> "AkashWallet":
        """
        Create wallet from BIP39 mnemonic phrase using proper BIP44 derivation.

        Args:
            mnemonic (str): BIP39 mnemonic phrase (12, 15, 18, 21, or 24 words)
            passphrase (str): Optional BIP39 passphrase for additional security
            derivation_path (str): Optional custom derivation path (e.g., "m/44'/118'/0'/0/1")
                                 Defaults to "m/44'/118'/0'/0/0" (Cosmos standard)

        Returns:
            AkashWallet: Wallet instance derived from mnemonic

        Example:
            ```python
            # Using the test mnemonic with default derivation path
            mnemonic = ("poverty torch street hybrid estate message increase play negative "
                       "vibrant transfer six police tiny garment congress survey tired used "
                       "audit dolphin focus abstract appear")

            wallet = AkashWallet.from_mnemonic(mnemonic)
            print(f"Default path address: {wallet.address}")
            # Should match: akash1qnnhhgzxj24f2kld5yhy4v4h4s9r295ak5gjw4

            # Using custom derivation path for different address
            wallet2 = AkashWallet.from_mnemonic(mnemonic, derivation_path="m/44'/118'/0'/0/1")
            print(f"Custom path address: {wallet2.address}")
            ```
        """
        # Validate mnemonic
        mnemo = Mnemonic("english")
        if not mnemo.check(mnemonic):
            raise ValueError("Invalid mnemonic phrase")

        private_key = cls._derive_private_key_from_mnemonic(
            mnemonic, passphrase, derivation_path
        )

        logger.info(
            f"Created wallet from mnemonic with derivation path: {derivation_path or 'default'}"
        )
        return cls(private_key, mnemonic)

    @classmethod
    def from_private_key(cls, private_key_bytes: bytes) -> "AkashWallet":
        """
        Create wallet from raw private key bytes.

        Args:
            private_key_bytes (bytes): 32-byte private key

        Returns:
            AkashWallet: Wallet instance
        """
        private_key = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
        logger.info("Created wallet from private key")
        return cls(private_key)

    @property
    def address(self) -> str:
        """Get the Akash address (bech32 format)."""
        return self._address

    @property
    def mnemonic(self) -> Optional[str]:
        """Get the mnemonic phrase (if available)."""
        return self._mnemonic

    @property
    def public_key(self) -> VerifyingKey:
        """Get the public key."""
        return self._public_key

    @property
    def public_key_bytes(self) -> bytes:
        """Get compressed public key bytes."""
        return self._public_key.to_string("compressed")

    def _derive_address(self) -> str:
        """
        Derive Akash address from public key.

        Returns:
            str: Bech32 address with 'akash' prefix
        """
        pub_key_compressed = self.public_key_bytes
        sha256_hash = hashlib.sha256(pub_key_compressed).digest()

        try:
            from Crypto.Hash import RIPEMD160

            ripemd160_hash = RIPEMD160.new(sha256_hash).digest()
        except ImportError:
            try:
                ripemd160_hash = hashlib.new("ripemd160", sha256_hash).digest()
            except ValueError:
                raise ImportError(
                    "RIPEMD160 is required for correct Akash address derivation. "
                    "Install pycryptodome: pip install pycryptodome"
                )

        converted_bits = bech32.convertbits(ripemd160_hash, 8, 5)
        address = bech32.bech32_encode("akash", converted_bits)

        return address

    def sign_transaction(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign transaction data for Akash blockchain.

        Args:
            tx_data (Dict[str, Any]): Transaction data to sign

        Returns:
            Dict[str, Any]: Signed transaction with signature

        Example:
            ```python
            wallet = AkashWallet.from_mnemonic("your mnemonic here")

            # Example transaction data (simplified)
            tx_data = {
                "chain_id": "akashnet-2",
                "account_number": "123",
                "sequence": "1",
                "fee": {"amount": [{"denom": "uakt", "amount": "5000"}], "gas": "200000"},
                "msgs": [{"type": "akash/deployment-create", "value": {...}}],
                "memo": ""
            }

            signed_tx = wallet.sign_transaction(tx_data)
            print(f"Signature: {signed_tx['signature']}")
            ```
        """
        try:
            tx_bytes = self._serialize_tx_for_signing(tx_data)
            tx_hash = hashlib.sha256(tx_bytes).digest()
            signature = self._private_key.sign(tx_hash)

            signed_tx = {
                "tx": tx_data,
                "signature": {
                    "signature": signature.hex(),
                    "pub_key": {
                        "type": "tendermint/PubKeySecp256k1",
                        "value": self.public_key_bytes.hex(),
                    },
                },
                "mode": "sync",
            }

            logger.info("Successfully signed transaction")
            return signed_tx

        except Exception as e:
            logger.error(f"Failed to sign transaction: {e}")
            raise

    def sign_message(self, message: str) -> str:
        """
        Sign an arbitrary message.

        Args:
            message (str): Message to sign

        Returns:
            str: Hex-encoded signature

        Example:
            ```python
            wallet = AkashWallet.from_mnemonic("your mnemonic here")

            message = "Hello Akash Network"
            signature = wallet.sign_message(message)
            print(f"Message signature: {signature}")
            ```
        """
        try:
            message_bytes = message.encode("utf-8")

            signature = self._private_key.sign(message_bytes)

            logger.info(f"Signed message: {message}")
            return signature.hex()

        except Exception as e:
            logger.error(f"Failed to sign message: {e}")
            raise

    def verify_signature(self, message: str, signature_hex: str) -> bool:
        """
        Verify a signature against a message.

        Args:
            message (str): Original message
            signature_hex (str): Hex-encoded signature

        Returns:
            bool: True if signature is valid
        """
        try:
            message_bytes = message.encode("utf-8")
            signature = bytes.fromhex(signature_hex)

            return self._public_key.verify(signature, message_bytes)

        except Exception as e:
            logger.error(f"Failed to verify signature: {e}")
            return False

    def sign_raw(self, data: bytes) -> bytes:
        """
        Sign raw bytes with this wallet's private key.

        Args:
            data (bytes): Raw data to sign

        Returns:
            bytes: Signature bytes
        """
        try:
            data_hash = hashlib.sha256(data).digest()

            signature = self._private_key.sign_deterministic(
                data_hash, hashfunc=hashlib.sha256, sigencode=sigencode_string_canonize
            )

            return signature

        except Exception as e:
            logger.error(f"Failed to sign raw data: {e}")
            raise

    @staticmethod
    def _derive_private_key_from_mnemonic(
        mnemonic: str, passphrase: str = "", derivation_path: str = None
    ) -> SigningKey:
        """
        Derive private key from mnemonic using proper BIP39/BIP44 key derivation.

        Args:
            mnemonic (str): BIP39 mnemonic phrase
            passphrase (str): Optional passphrase
            derivation_path (str): Optional custom derivation path (e.g., "m/44'/118'/0'/0/1")
                                 Defaults to "m/44'/118'/0'/0/0" (Cosmos standard)

        Returns:
            SigningKey: Derived private key
        """
        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(mnemonic, passphrase)

        master_key, master_chain_code = AkashWallet._derive_master_key(seed)

        if derivation_path:
            parsed_path = AkashWallet._parse_derivation_path(derivation_path)
            child_key = AkashWallet._derive_child_key(
                master_key, master_chain_code, parsed_path
            )
        else:
            child_key = AkashWallet._derive_child_key(
                master_key, master_chain_code, AkashWallet.COSMOS_DERIVATION_PATH
            )

        return SigningKey.from_string(child_key, curve=SECP256k1)

    @staticmethod
    def _parse_derivation_path(path: str) -> List[int]:
        """
        Parse derivation path string into integer array for BIP32 derivation.

        Args:
            path (str): Derivation path string (e.g., "m/44'/118'/0'/0/1")

        Returns:
            List[int]: Parsed path components with hardened derivation flags

        Raises:
            ValueError: If path format is invalid

        Example:
            "m/44'/118'/0'/0/1" -> [44 + 0x80000000, 118 + 0x80000000, 0x80000000, 0, 1]
        """
        if not path or not path.startswith("m/"):
            raise ValueError(f"Invalid derivation path: {path}. Must start with 'm/'")

        components = path[2:].split("/")
        parsed_path = []

        for component in components:
            if not component:
                continue

            if component.endswith("'") or component.endswith('"'):
                # Hardened derivation: add 0x80000000
                try:
                    index = int(component[:-1])
                    parsed_path.append(index + 0x80000000)
                except ValueError:
                    raise ValueError(f"Invalid path component: {component}")
            else:
                # Non-hardened derivation
                try:
                    index = int(component)
                    parsed_path.append(index)
                except ValueError:
                    raise ValueError(f"Invalid path component: {component}")

        return parsed_path

    @staticmethod
    def _derive_master_key(seed: bytes) -> Tuple[bytes, bytes]:
        """
        Derive master private key from seed using BIP32.

        Args:
            seed (bytes): BIP39 seed

        Returns:
            Tuple[bytes, bytes]: (Master private key, Master chain code)
        """
        hmac_result = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
        master_key = hmac_result[:32]
        master_chain_code = hmac_result[32:]

        return master_key, master_chain_code

    @staticmethod
    def _derive_child_key(
        parent_key: bytes, parent_chain_code: bytes, path: List[int]
    ) -> bytes:
        """
        Derive child key using BIP32 hierarchical deterministic key derivation.

        Args:
            parent_key (bytes): Parent private key
            parent_chain_code (bytes): Parent chain code
            path (List[int]): Derivation path indices

        Returns:
            bytes: Child private key
        """
        current_key = parent_key
        current_chain_code = parent_chain_code

        for index in path:
            if index >= 0x80000000:
                # Hardened derivation: use private key
                data = b"\x00" + current_key + struct.pack(">I", index)
            else:
                # Non-hardened derivation: use public key
                private_key_obj = SigningKey.from_string(current_key, curve=SECP256k1)
                public_key_compressed = private_key_obj.verifying_key.to_string(
                    "compressed"
                )
                data = public_key_compressed + struct.pack(">I", index)

            hmac_result = hmac.new(current_chain_code, data, hashlib.sha512).digest()

            key_part = hmac_result[:32]
            current_chain_code = hmac_result[32:]

            current_key_int = int.from_bytes(current_key, "big")
            key_part_int = int.from_bytes(key_part, "big")

            curve_order = SECP256k1.order
            new_key_int = (current_key_int + key_part_int) % curve_order

            if new_key_int == 0 or new_key_int >= curve_order:
                raise ValueError("Invalid derived key")

            current_key = new_key_int.to_bytes(32, "big")

        return current_key

    def _serialize_tx_for_signing(self, tx_data: Dict[str, Any]) -> bytes:
        """
        Serialize transaction data for signing (canonical JSON).

        Args:
            tx_data (Dict[str, Any]): Transaction data

        Returns:
            bytes: Canonical transaction bytes
        """
        import json

        sign_doc = {
            "chain_id": tx_data.get("chain_id", ""),
            "account_number": str(tx_data.get("account_number", "0")),
            "sequence": str(tx_data.get("sequence", "0")),
            "fee": tx_data.get("fee", {}),
            "msgs": tx_data.get("msgs", []),
            "memo": tx_data.get("memo", ""),
        }

        canonical_json = json.dumps(sign_doc, sort_keys=True, separators=(",", ":"))
        return canonical_json.encode("utf-8")

    @staticmethod
    def validate_mnemonic(mnemonic: str) -> bool:
        """
        Validate a BIP39 mnemonic phrase.

        Args:
            mnemonic (str): Mnemonic phrase to validate

        Returns:
            bool: True if mnemonic is valid
        """
        try:
            mnemo = Mnemonic("english")
            return mnemo.check(mnemonic)
        except Exception:
            return False

    @staticmethod
    def validate_address(address: str) -> bool:
        """
        Validate an Akash bech32 address.
        Delegates to auth module's validate_address for the actual validation.

        Args:
            address (str): Address to validate

        Returns:
            bool: True if address is valid
        """
        return validate_address(address)

    def __str__(self) -> str:
        """String representation of wallet."""
        return f"AkashWallet(address={self.address})"

    def __repr__(self) -> str:
        """Detailed representation of wallet."""
        return f"AkashWallet(address={self.address}, has_mnemonic={self.mnemonic is not None})"
