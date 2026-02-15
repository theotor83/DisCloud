import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding


class EncryptionService:
    """
    Handles encryption and decryption of file chunks using AES-256-CBC.
    Each instance is bound to a specific encryption key to prevent 
    accidental key mix-ups.
    
    Each encrypted chunk is self-contained with its own IV prepended,
    allowing for stateless decryption and resumable downloads.
    """
    
    # AES-256 requires 32-byte keys
    KEY_SIZE = 32
    # AES block size is always 16 bytes
    BLOCK_SIZE = 16

    @classmethod
    def create_with_new_key(cls):
        """
        Factory method to create a service with a new random key.
        
        Returns:
            EncryptionService: A new instance with a generated key.
        """
        return cls(key=None)

    @classmethod
    def create_from_key(cls, key):
        """
        Factory method to create a service with an existing key.
        
        Args:
            key (bytes): The 32-byte encryption key to use.
            
        Returns:
            EncryptionService: A new instance bound to the provided key.
        """
        return cls(key=key)

    def __init__(self, key=None):
        """
        Initialize the encryption service with a specific key.
        
        Args:
            key (bytes, optional): A 32-byte encryption key. If None, generates a new key.
        
        Raises:
            ValueError: If the provided key is not 32 bytes.
        """
        if key is not None:
            if len(key) != self.KEY_SIZE:
                raise ValueError(f"Encryption key must be {self.KEY_SIZE} bytes, got {len(key)}")
            self.key = key
        else:
            self.key = self.generate_key()

    def generate_key(self):
        """
        Generates a new encryption key.
        
        Returns:
            bytes: A 32-byte random key suitable for AES-256.
        """
        return os.urandom(self.KEY_SIZE)

    def encrypt_chunk(self, chunk):
        """
        Encrypts a single chunk of data using AES-256-CBC with PKCS7 padding.
        
        The encrypted output includes the IV prepended to the ciphertext:
        [16 bytes IV][encrypted data]
        
        This makes each chunk self-contained and independently decryptable.
        
        Args:
            chunk (bytes): The plaintext data to encrypt.
        
        Returns:
            bytes: IV + encrypted data.
        
        Raises:
            TypeError: If chunk is not bytes.
        """
        if not isinstance(chunk, bytes):
            raise TypeError("Chunk must be bytes")
        
        # Generate a random IV for this chunk
        iv = os.urandom(self.BLOCK_SIZE)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Apply PKCS7 padding to ensure data is multiple of block size
        padder = padding.PKCS7(self.BLOCK_SIZE * 8).padder()
        padded_data = padder.update(chunk) + padder.finalize()
        
        # Encrypt the padded data
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Prepend IV to ciphertext for self-contained chunk
        return iv + ciphertext

    def decrypt_chunk(self, encrypted_chunk):
        """
        Decrypts a single chunk of data that was encrypted with encrypt_chunk().
        
        Expects the encrypted chunk to have the IV prepended:
        [16 bytes IV][encrypted data]
        
        Args:
            encrypted_chunk (bytes): The IV + encrypted data.
        
        Returns:
            bytes: The original plaintext data.
        
        Raises:
            TypeError: If encrypted_chunk is not bytes.
            ValueError: If encrypted_chunk is too short to contain an IV.
        """
        if not isinstance(encrypted_chunk, bytes):
            raise TypeError("Encrypted chunk must be bytes")
        
        if len(encrypted_chunk) < self.BLOCK_SIZE:
            raise ValueError(f"Encrypted chunk too short, must be at least {self.BLOCK_SIZE} bytes")
        
        # Extract IV from the beginning
        iv = encrypted_chunk[:self.BLOCK_SIZE]
        ciphertext = encrypted_chunk[self.BLOCK_SIZE:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt the data
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove PKCS7 padding
        unpadder = padding.PKCS7(self.BLOCK_SIZE * 8).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext