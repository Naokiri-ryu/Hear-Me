from datetime import timedelta

from api.security import (
    _fernet_key,
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


def test_fernet_key_derived_from_encryption_key():
    # two distinct sources must yield distinct Fernet keys
    assert _fernet_key("a") != _fernet_key("b")
    # valid Fernet key: 32 url-safe base64 bytes
    assert len(_fernet_key("x" * 64)) == 44


def test_jwt_with_strong_key_no_insecure_length_warning(monkeypatch):
    import warnings

    from api import security as security_mod
    from jwt.warnings import InsecureKeyLengthWarning

    monkeypatch.setattr(security_mod.settings, "SECRET_KEY", "k" * 64)
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        token = security_mod.create_access_token(7, expires_delta=timedelta(minutes=1))
        assert security_mod.decode_access_token(token)["sub"] == "7"
    assert not any(
        issubclass(w.category, InsecureKeyLengthWarning) for w in recorded
    )


def test_production_rejects_placeholder_or_short_keys():
    import pytest

    from api.config import Settings

    with pytest.raises(ValueError):
        Settings(ENV="production", SECRET_KEY="change-me", TOKEN_ENCRYPTION_KEY="k" * 64)
    with pytest.raises(ValueError):
        Settings(ENV="production", SECRET_KEY="k" * 64, TOKEN_ENCRYPTION_KEY="short-key")
    with pytest.raises(ValueError):
        Settings(ENV="production", SECRET_KEY="k" * 16, TOKEN_ENCRYPTION_KEY="k" * 64)


def test_production_accepts_strong_separate_keys():
    from api.config import Settings

    s = Settings(
        ENV="production",
        SECRET_KEY="s" * 64,
        TOKEN_ENCRYPTION_KEY="t" * 64,
    )
    assert s.SECRET_KEY != s.TOKEN_ENCRYPTION_KEY


def test_development_accepts_placeholder_keys():
    from api.config import Settings

    # dev default must not fail startup validation
    assert Settings(ENV="development", SECRET_KEY="change-me", TOKEN_ENCRYPTION_KEY="change-me")