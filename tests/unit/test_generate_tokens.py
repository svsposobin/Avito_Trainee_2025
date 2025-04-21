import pytest
from unittest.mock import patch, MagicMock
from typing import Generator, Dict
from datetime import datetime, timedelta, UTC
from jose import JWTError
from src.tokens import JWTConfig, create_access_token
from src.dto import JWTTokenResponse


@pytest.fixture
def mock_getenv() -> Generator[MagicMock, None, None]:
    with patch("src.tokens.getenv") as mock:
        yield mock


@pytest.fixture
def mock_load_dotenv() -> Generator[MagicMock, None, None]:
    with patch("src.tokens.load_dotenv") as mock:
        yield mock


@pytest.fixture
def mock_jwt_encode() -> Generator[MagicMock, None, None]:
    with patch("src.tokens.jwt.encode") as mock:
        yield mock


@pytest.fixture
def mock_jwt_config() -> Generator[None, None, None]:
    with patch("src.tokens.JWTConfig.SECRET_KEY", "TEST_SECRET_KEY"), \
            patch("src.tokens.JWTConfig.ALGORITHM", "HS256"), \
            patch("src.tokens.JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES", 30.0):

        yield


@pytest.fixture
def mock_jwt_config_env_vars() -> Generator[None, None, None]:
    with patch("src.tokens.JWTConfig.SECRET_KEY", "CUSTOM_SECRET"), \
            patch("src.tokens.JWTConfig.ALGORITHM", "HS512"), \
            patch("src.tokens.JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES", 60.0):

        yield


class TestJWTConfig:
    def test_jwt_config_default_values(
            self,
            mock_getenv: MagicMock,
            mock_load_dotenv: MagicMock,
            mock_jwt_config: None
    ) -> None:
        mock_getenv.side_effect = lambda key, default=None: default

        assert JWTConfig.SECRET_KEY == "TEST_SECRET_KEY"
        assert JWTConfig.ALGORITHM == "HS256"
        assert JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES == 30.0

    def test_jwt_config_environment_variables(
            self,
            mock_getenv: MagicMock,
            mock_load_dotenv: MagicMock,
            mock_jwt_config_env_vars: None
    ) -> None:
        mock_getenv.side_effect = lambda key, default=None: {
            "SECRET_KEY": "CUSTOM_SECRET",
            "ALGORITHM": "HS512",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "60"
        }.get(key, default)

        assert JWTConfig.SECRET_KEY == "CUSTOM_SECRET"
        assert JWTConfig.ALGORITHM == "HS512"
        assert JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES == 60.0


class TestCreateAccessToken:
    def test_create_access_token_success_default_expiry(
            self, mock_jwt_encode: MagicMock, mock_load_dotenv: MagicMock, mock_jwt_config: None
    ) -> None:
        data = {"sub": "test@example.com"}
        mock_jwt_encode.return_value = "encoded_token"

        result = create_access_token(data)

        assert isinstance(result, JWTTokenResponse)
        assert result.access_token == "encoded_token"
        mock_jwt_encode.assert_called_once()
        call_args = mock_jwt_encode.call_args
        assert call_args[0][0]["sub"] == "test@example.com"
        assert "exp" in call_args[0][0]
        assert isinstance(call_args[0][0]["exp"], datetime)
        assert call_args[0][1] == JWTConfig.SECRET_KEY
        assert call_args.kwargs["algorithm"] == JWTConfig.ALGORITHM

    def test_create_access_token_with_expires_delta(
            self, mock_jwt_encode: MagicMock, mock_load_dotenv: MagicMock, mock_jwt_config: None
    ) -> None:
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        mock_jwt_encode.return_value = "encoded_token"

        result = create_access_token(data, expires_delta=expires_delta)

        assert isinstance(result, JWTTokenResponse)
        assert result.access_token == "encoded_token"

        mock_jwt_encode.assert_called_once()
        call_args = mock_jwt_encode.call_args

        assert call_args[0][0]["sub"] == "test@example.com"
        assert "exp" in call_args[0][0]
        assert isinstance(call_args[0][0]["exp"], datetime)

        expected_expiry = datetime.now(UTC) + expires_delta
        actual_expiry = call_args[0][0]["exp"]

        assert abs((actual_expiry - expected_expiry).total_seconds()) < 1
        assert call_args[0][1] == JWTConfig.SECRET_KEY
        assert call_args.kwargs["algorithm"] == JWTConfig.ALGORITHM

    def test_create_access_token_jwt_encoding_error(
            self, mock_jwt_encode: MagicMock, mock_load_dotenv: MagicMock, mock_jwt_config: None
    ) -> None:
        data: Dict[str, str] = {"sub": "test@example.com"}
        mock_jwt_encode.side_effect = JWTError("Encoding failed")

        with pytest.raises(JWTError) as exc_info:
            create_access_token(data)

        assert str(exc_info.value) == "Encoding failed"
        mock_jwt_encode.assert_called_once()
