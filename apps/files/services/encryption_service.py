class EncryptionService:
    """
    Handles encryption and decryption of file chunks.
    This should be able to handle streams of data to avoid high memory usage.
    """

    def generate_key(self):
        """
        Generates a new encryption key.
        """
        pass

    def encrypt_chunk(self, chunk, key):
        """
        Encrypts a single chunk of data.
        """
        pass

    def decrypt_chunk(self, encrypted_chunk, key):
        """
        Decrypts a single chunk of data.
        """
        pass