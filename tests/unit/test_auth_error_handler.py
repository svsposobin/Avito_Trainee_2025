from unittest.mock import MagicMock
from starlette import status
from starlette.responses import JSONResponse
from src.sso.auth_error_handler import auth_error


class TestAuthErrorHandler:
    def test_auth_error_expired_token(self) -> None:
        result = MagicMock()
        result.errors = "Токен авторизации протух, войдите заново"

        response = auth_error(result)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.body.decode(  # type: ignore[union-attr]
            "utf-8") == '{"errors":"Токен авторизации протух, войдите заново"}'

    def test_auth_error_no_expired_token(self) -> None:
        result = MagicMock()
        result.errors = "Некорректный токен"

        response = auth_error(result)

        assert response is None

    def test_auth_error_no_errors_attribute(self) -> None:
        result = MagicMock()
        result.errors = None

        response = auth_error(result)

        assert response is None
