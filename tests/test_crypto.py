from app.core.crypto import decrypt, encrypt


def test_encrypt_decrypt_round_trip():
    original = "super-secret-password"
    encrypted = encrypt(original)

    assert encrypted != original
    assert decrypt(encrypted) == original