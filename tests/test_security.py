from datetime import timedelta

from api.security import (
    create_access_token,
    decode_access_token,
    decrypt_token,
    encrypt_token,
    hash_password,
    verify_password,
)


def test_encrypt_decrypt_roundtrip():
    plaintext = "spotify-token-abc123"
    ciphertext = encrypt_token(plaintext)
    assert ciphertext != plaintext
    assert decrypt_token(ciphertext) == plaintext


def test_decrypt_with_wrong_key():
    from api.security import decrypt_token, encrypt_token
    from api.security import _fernet_key  # noqa: F401

    ciphertext = "/corrupted-value/"
    try:
        decrypt_token(ciphertext)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_password_hash_and_verify():
    hashed = hash_password("s3cret-pass")
    assert hashed != "s3cret-pass"
    assert verify_password("s3cret-pass", hashed)
    assert not verify_password("wrong-pass", hashed)


def test_jwt_roundtrip():
    token = create_access_token(42, expires_delta=timedelta(minutes=5))
    payload = decode_access_token(token)
    assert payload["sub"] == "42"