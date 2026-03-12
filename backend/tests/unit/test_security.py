import uuid
import pytest
from app.shared import security


class TestPasswordHashing:
    def test_hash_and_verify(self):
        h = security.hash_password("mysecretpassword")
        assert security.verify_password("mysecretpassword", h)

    def test_wrong_password_fails(self):
        h = security.hash_password("correct")
        assert not security.verify_password("wrong", h)

    def test_different_hashes_same_input(self):
        h1 = security.hash_password("password")
        h2 = security.hash_password("password")
        assert h1 != h2  # argon2id uses random salt


class TestJWT:
    def test_access_token_roundtrip(self):
        uid = uuid.uuid4()
        token = security.create_access_token(uid)
        assert security.decode_access_token(token) == uid

    def test_refresh_token_roundtrip(self):
        uid = uuid.uuid4()
        token = security.create_refresh_token(uid)
        assert security.decode_refresh_token(token) == uid

    def test_access_token_rejected_as_refresh(self):
        uid = uuid.uuid4()
        token = security.create_access_token(uid)
        with pytest.raises(ValueError):
            security.decode_refresh_token(token)

    def test_refresh_token_rejected_as_access(self):
        uid = uuid.uuid4()
        token = security.create_refresh_token(uid)
        with pytest.raises(ValueError):
            security.decode_access_token(token)

    def test_tampered_token_raises(self):
        uid = uuid.uuid4()
        token = security.create_access_token(uid)
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(ValueError):
            security.decode_access_token(tampered)

    def test_garbage_token_raises(self):
        with pytest.raises(ValueError):
            security.decode_access_token("not.a.jwt")
