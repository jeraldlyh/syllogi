from lib.crypto import encrypt, decrypt


class TestCrypto:
    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "my-super-secret-password"
        ciphertext = encrypt(plaintext)

        assert ciphertext != plaintext
        assert decrypt(ciphertext) == plaintext

    def test_different_plaintexts_produce_different_ciphertexts(self):
        a = encrypt("password-one")
        b = encrypt("password-two")

        assert a != b

    def test_empty_string(self):
        ciphertext = encrypt("")

        assert decrypt(ciphertext) == ""

    def test_unicode_plaintext(self):
        plaintext = "café résumé 日本語"
        ciphertext = encrypt(plaintext)

        assert decrypt(ciphertext) == plaintext
