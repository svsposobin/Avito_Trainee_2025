import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Generator, Dict, List, Any
from fastapi import Response
from datetime import datetime
from jose import ExpiredSignatureError
from src.sso.dependencies import (
    get_current_user,
    register,
    login,
    init_pvz,
    receptions,
    add_product,
    delete_last_product,
    close_last_reception,
    get_pvz_info
)
from src.sso.dto import (
    GetCurrentUserResponse,
    RegisterUserResponse,
    LoginUserResponse,
    InitPVZResponse,
    InitActiveReceptionsResponse,
    AddProductResponse,
    DeleteProductResponse,
    CloseReceptionResponse,
    PVZInfoResponse
)
from src.sso.constants import ERRORS_MAPPING, VALID_USER_TYPES
from src.tokens import JWTConfig
from postgres.sql.mutation import (
    UserRegisterMutation,
    UserLoginMutation,
    UpdateAccessTokenMutation,
    GetMe,
    PVZ,
    CheckActiveAccepting,
    InitReceptions,
    CheckAcceptingStatus,
    AddProduct,
    GetActiveAccepting,
    DeleteLastProduct,
    CloseReception,
)


@pytest.fixture
def mock_response() -> Generator[MagicMock, None, None]:
    response: MagicMock = MagicMock(spec=Response)
    response.headers = {}
    yield response


@pytest.fixture
def mock_jwt_decode() -> Generator[MagicMock, None, None]:
    with patch("jose.jwt.decode") as mock:
        yield mock


@pytest.fixture
def mock_create_access_token() -> Generator[MagicMock, None, None]:
    with patch("src.sso.dependencies.create_access_token") as mock:
        yield mock


@pytest.fixture
def mock_user_register_mutation() -> Generator[AsyncMock, None, None]:
    with patch.object(UserRegisterMutation, "register", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_user_login_mutation() -> Generator[AsyncMock, None, None]:
    with patch.object(UserLoginMutation, "login", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_update_access_token_mutation() -> Generator[AsyncMock, None, None]:
    with patch.object(UpdateAccessTokenMutation, "update", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_get_me() -> Generator[AsyncMock, None, None]:
    with patch.object(GetMe, "get", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_pvz_create() -> Generator[AsyncMock, None, None]:
    with patch.object(PVZ, "create", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_check_active_accepting() -> Generator[AsyncMock, None, None]:
    with patch.object(CheckActiveAccepting, "check", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_init_receptions() -> Generator[AsyncMock, None, None]:
    with patch.object(InitReceptions, "init", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_check_accepting_status() -> Generator[AsyncMock, None, None]:
    with patch.object(CheckAcceptingStatus, "check", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_add_product() -> Generator[AsyncMock, None, None]:
    with patch.object(AddProduct, "add", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_get_active_accepting() -> Generator[AsyncMock, None, None]:
    with patch.object(GetActiveAccepting, "get", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_delete_last_product() -> Generator[AsyncMock, None, None]:
    with patch.object(DeleteLastProduct, "delete", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_close_reception() -> Generator[AsyncMock, None, None]:
    with patch.object(CloseReception, "close", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_get_pvz_info() -> Generator[MagicMock, None, None]:
    with patch("src.sso.dependencies.GetPVZInfo", new_callable=MagicMock) as mock:
        yield mock


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        mock_jwt_decode: MagicMock,
        mock_get_me: AsyncMock,
        mock_response: MagicMock
    ) -> None:
        token: str = "valid_token"
        payload: Dict[str, str] = {"sub": "test@example.com", "role": VALID_USER_TYPES["client"]}
        mock_jwt_decode.return_value = payload
        mock_get_me.return_value = token

        result: GetCurrentUserResponse = await get_current_user(mock_response, token)

        mock_jwt_decode.assert_called_once_with(
            token,
            JWTConfig.SECRET_KEY,
            algorithms=[JWTConfig.ALGORITHM],
            options={"require_exp": True}
        )
        mock_get_me.assert_called_once()
        assert result.message == "Authorization successful"
        assert result.email == "test@example.com"
        assert result.role == VALID_USER_TYPES["client"]
        assert result.result == {"status": True}
        assert result.errors is None

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(
        self,
        mock_response: MagicMock
    ) -> None:
        result: GetCurrentUserResponse = await get_current_user(mock_response, "")

        assert result.errors == "Токен авторизации не был найден"
        assert result.message is None
        assert result.email is None
        assert result.role is None

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(
        self,
        mock_jwt_decode: MagicMock,
        mock_response: MagicMock
    ) -> None:
        mock_jwt_decode.side_effect = ExpiredSignatureError
        result: GetCurrentUserResponse = await get_current_user(mock_response, "expired_token")

        assert result.errors == "Токен авторизации протух, войдите заново"
        assert mock_response.headers["Authorization"] == ""

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self,
        mock_jwt_decode: MagicMock,
        mock_get_me: AsyncMock,
        mock_response: MagicMock
    ) -> None:
        payload: Dict[str, str] = {"sub": "test@example.com", "role": VALID_USER_TYPES["client"]}
        mock_jwt_decode.return_value = payload
        mock_get_me.return_value = "different_token"

        result: GetCurrentUserResponse = await get_current_user(mock_response, "invalid_token")

        assert result.errors == "Некорректный токен"
        assert result.message is None

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_role(
        self,
        mock_jwt_decode: MagicMock,
        mock_get_me: AsyncMock,
        mock_response: MagicMock
    ) -> None:
        payload: Dict[str, str] = {"sub": "test@example.com", "role": "invalid_role"}
        mock_jwt_decode.return_value = payload
        mock_get_me.return_value = "valid_token"

        result: GetCurrentUserResponse = await get_current_user(mock_response, "valid_token")

        assert result.errors == "Некорректная роль"
        assert result.message is None


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(
        self,
        mock_user_register_mutation: AsyncMock,
        mock_create_access_token: MagicMock
    ) -> None:
        mock_create_access_token.return_value = MagicMock(access_token="new_token")
        mock_user_register_mutation.return_value = (1, "testuser", VALID_USER_TYPES["client"], "test@example.com")

        result: RegisterUserResponse = await register(
            username="testuser",
            user_type=VALID_USER_TYPES["client"],
            password="password123",
            email="test@example.com"
        )

        mock_create_access_token.assert_called_once()
        mock_user_register_mutation.assert_called_once()
        assert result.result == {"success": True}
        assert result.user == {"id": 1, "username": "testuser", "email": "test@example.com"}
        assert result.errors is None

    @pytest.mark.asyncio
    async def test_register_failure(
        self,
        mock_user_register_mutation: AsyncMock,
        mock_create_access_token: MagicMock
    ) -> None:
        mock_create_access_token.return_value = MagicMock(access_token="new_token")
        mock_user_register_mutation.side_effect = Exception(
            "duplicate key value violates unique constraint \"users_username_key\"")

        result: RegisterUserResponse = await register(
            username="testuser",
            user_type=VALID_USER_TYPES["client"],
            password="password123",
            email="test@example.com"
        )

        assert result.errors == ERRORS_MAPPING["duplicate key value violates unique constraint \"users_username_key\""]
        assert result.result is None


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(
        self,
        mock_user_login_mutation: AsyncMock,
        mock_update_access_token_mutation: AsyncMock
    ) -> None:
        mock_user_login_mutation.return_value = (
            "testuser", "hashed_password", VALID_USER_TYPES["client"], "test@example.com")
        mock_update_access_token_mutation.return_value = "new_token"

        result: LoginUserResponse = await login(username="testuser", password="password123")

        mock_user_login_mutation.assert_called_once()
        mock_update_access_token_mutation.assert_called_once()
        assert result.result == {"success": True}
        assert result.token == "new_token"
        assert result.errors is None

    @pytest.mark.asyncio
    async def test_login_failure(
        self,
        mock_user_login_mutation: AsyncMock
    ) -> None:
        mock_user_login_mutation.side_effect = Exception("Пользователь не найден")

        result: LoginUserResponse = await login(username="testuser", password="password123")

        assert result.errors == "Пользователь не найден"
        assert result.result is None


class TestInitPVZ:
    @pytest.mark.asyncio
    async def test_init_pvz_success(
        self,
        mock_pvz_create: AsyncMock
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            message="Authorization successful",
            email="test@example.com",
            role=VALID_USER_TYPES["moderator"],
            result={"status": True}
        )
        mock_pvz_create.return_value = (1, "Москва", "2025-04-21T10:00:00+03:00")

        result: InitPVZResponse = await init_pvz(city="Москва", current_user=current_user)

        mock_pvz_create.assert_called_once()
        assert result.id == 1
        assert result.city == "Москва"
        assert result.registered_at == "2025-04-21T10:00:00+03:00"
        assert result.result == {"status": True}
        assert result.errors is None

    @pytest.mark.asyncio
    async def test_init_pvz_unauthorized(
        self
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            errors="Токен авторизации протух, войдите заново")

        result: InitPVZResponse = await init_pvz(city="Москва", current_user=current_user)

        assert result.errors == "Токен авторизации протух, войдите заново"
        assert result.id is None
        assert result.city is None
        assert result.registered_at is None

    @pytest.mark.asyncio
    async def test_init_pvz_insufficient_role(
        self
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            message="Authorization successful",
            email="test@example.com",
            role=VALID_USER_TYPES["client"],
            result={"status": True}
        )

        result: InitPVZResponse = await init_pvz(city="Москва", current_user=current_user)

        assert result.errors == "У вас недостаточно прав - необходимая роль: moderator"
        assert result.id is None
        assert result.city is None
        assert result.registered_at is None


class TestReceptions:
    @pytest.mark.asyncio
    async def test_receptions_success(
        self,
        mock_check_active_accepting: AsyncMock,
        mock_init_receptions: AsyncMock
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            message="Authorization successful",
            email="test@example.com",
            role=VALID_USER_TYPES["client"],
            result={"status": True}
        )
        mock_check_active_accepting.return_value = None
        mock_init_receptions.return_value = (1, 1, "in_progress")

        result: InitActiveReceptionsResponse = await receptions(pvz_id=1, current_user=current_user)

        mock_check_active_accepting.assert_called_once()
        mock_init_receptions.assert_called_once()
        assert result.receptions_id == 1
        assert result.pvz_id == 1
        assert result.status == "in_progress"
        assert result.result == {"status": True}
        assert result.errors is None

    @pytest.mark.asyncio
    async def test_receptions_unauthorized(
        self
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            errors="Токен авторизации протух, войдите заново")

        result: InitActiveReceptionsResponse = await receptions(pvz_id=1, current_user=current_user)

        assert result.errors == "Токен авторизации протух, войдите заново"
        assert result.receptions_id is None
        assert result.pvz_id is None
        assert result.status is None

    @pytest.mark.asyncio
    async def test_receptions_insufficient_role(
        self
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            message="Authorization successful",
            email="test@example.com",
            role=VALID_USER_TYPES["moderator"],
            result={"status": True}
        )

        result: InitActiveReceptionsResponse = await receptions(pvz_id=1, current_user=current_user)

        assert result.errors == "У вас недостаточно прав - необходимая роль: client"
        assert result.receptions_id is None
        assert result.pvz_id is None
        assert result.status is None


class TestAddProduct:
    @pytest.mark.asyncio
    async def test_add_product_success(
        self,
        mock_check_accepting_status: AsyncMock,
        mock_add_product: AsyncMock
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            message="Authorization successful",
            email="test@example.com",
            role=VALID_USER_TYPES["client"],
            result={"status": True}
        )
        mock_check_accepting_status.return_value = None
        mock_add_product.return_value = (1, 1, "электроника", "2025-04-21T10:00:00+03:00")

        result: AddProductResponse = await add_product(
            accepting_id=1, product_type="электроника", current_user=current_user)

        mock_check_accepting_status.assert_called_once()
        mock_add_product.assert_called_once()
        assert result.product_id == 1
        assert result.accepting_id == 1
        assert result.type == "электроника"
        assert result.datetime == "2025-04-21T10:00:00+03:00"
        assert result.result == {"status": True}
        assert result.errors is None

    @pytest.mark.asyncio
    async def test_add_product_unauthorized(
        self
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            errors="Токен авторизации протух, войдите заново")

        result: AddProductResponse = await add_product(
            accepting_id=1, product_type="электроника", current_user=current_user)

        assert result.errors == "Токен авторизации протух, войдите заново"
        assert result.product_id is None
        assert result.accepting_id is None
        assert result.type is None
        assert result.datetime is None

    @pytest.mark.asyncio
    async def test_add_product_insufficient_role(
        self
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            message="Authorization successful",
            email="test@example.com",
            role=VALID_USER_TYPES["moderator"],
            result={"status": True}
        )

        result: AddProductResponse = await add_product(
            accepting_id=1, product_type="электроника", current_user=current_user)

        assert result.errors == "У вас недостаточно прав - необходимая роль: client"
        assert result.product_id is None
        assert result.accepting_id is None
        assert result.type is None
        assert result.datetime is None


class TestDeleteLastProduct:
    @pytest.mark.asyncio
    async def test_delete_last_product_success(
        self,
        mock_get_active_accepting: AsyncMock,
        mock_delete_last_product: AsyncMock
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            message="Authorization successful",
            email="test@example.com",
            role=VALID_USER_TYPES["client"],
            result={"status": True}
        )
        mock_get_active_accepting.return_value = (1, [1, 2, 3])
        mock_delete_last_product.return_value = (3, 1, "электроника", "2025-04-21T10:00:00+03:00")

        result: DeleteProductResponse = await delete_last_product(pvz_id=1, current_user=current_user)

        mock_get_active_accepting.assert_called_once()
        mock_delete_last_product.assert_called_once()
        assert result.product_id == 3
        assert result.accepting_id == 1
        assert result.type == "электроника"
        assert result.datetime == "2025-04-21T10:00:00+03:00"
        assert result.result == {"status": True}
        assert result.errors is None

    @pytest.mark.asyncio
    async def test_delete_last_product_no_products(
        self,
        mock_get_active_accepting: AsyncMock
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            message="Authorization successful",
            email="test@example.com",
            role=VALID_USER_TYPES["client"],
            result={"status": True}
        )
        mock_get_active_accepting.return_value = (1, [])

        result: DeleteProductResponse = await delete_last_product(pvz_id=1, current_user=current_user)

        mock_get_active_accepting.assert_called_once()
        assert result.errors == "В приемке нет товаров для удаления"
        assert result.product_id is None
        assert result.accepting_id is None
        assert result.type is None
        assert result.datetime is None

    @pytest.mark.asyncio
    async def test_delete_last_product_unauthorized(
        self
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            errors="Токен авторизации протух, войдите заново")

        result: DeleteProductResponse = await delete_last_product(pvz_id=1, current_user=current_user)

        assert result.errors == "Токен авторизации протух, войдите заново"
        assert result.product_id is None
        assert result.accepting_id is None
        assert result.type is None
        assert result.datetime is None


class TestCloseLastReception:
    @pytest.mark.asyncio
    async def test_close_last_reception_success(
        self,
        mock_close_reception: AsyncMock
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            message="Authorization successful",
            email="test@example.com",
            role=VALID_USER_TYPES["client"],
            result={"status": True}
        )
        mock_close_reception.return_value = (1, 1, "close")

        result: CloseReceptionResponse = await close_last_reception(pvz_id=1, current_user=current_user)

        mock_close_reception.assert_called_once()
        assert result.reception_id == 1
        assert result.pvz_id == 1
        assert result.status == "close"
        assert result.result == {"status": True}
        assert result.errors is None

    @pytest.mark.asyncio
    async def test_close_last_reception_unauthorized(
        self
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            errors="Токен авторизации протух, войдите заново")

        result: CloseReceptionResponse = await close_last_reception(pvz_id=1, current_user=current_user)

        assert result.errors == "Токен авторизации протух, войдите заново"
        assert result.reception_id is None
        assert result.pvz_id is None
        assert result.status is None

    @pytest.mark.asyncio
    async def test_close_last_reception_insufficient_role(
        self
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            message="Authorization successful",
            email="test@example.com",
            role=VALID_USER_TYPES["moderator"],
            result={"status": True}
        )

        result: CloseReceptionResponse = await close_last_reception(pvz_id=1, current_user=current_user)

        assert result.errors == "У вас недостаточно прав - необходимая роль: client"
        assert result.reception_id is None
        assert result.pvz_id is None
        assert result.status is None


class TestGetPVZInfo:
    @pytest.mark.asyncio
    async def test_get_pvz_info_success(
        self,
        mock_get_pvz_info: MagicMock
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            message="Authorization successful",
            email="test@example.com",
            role=VALID_USER_TYPES["client"],
            result={"status": True}
        )
        pvz_data: List[Dict[str, Any]] = [
            {"id": 1, "city": "Москва", "registered_at": "2025-04-21T10:00:00+03:00", "receptions": []}]
        total: int = 1

        mock_get_pvz_info.return_value.get = AsyncMock(return_value=(pvz_data, total))

        start_date_str: str = "2025-04-01T00:00:00"
        end_date_str: str = "2025-04-30T23:59:59"
        start_date: datetime = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        end_date: datetime = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))

        result: PVZInfoResponse = await get_pvz_info(
            start_date=start_date_str,
            end_date=end_date_str,
            page=1,
            page_size=10,
            current_user=current_user
        )

        mock_get_pvz_info.assert_called_once_with(
            page=1,
            page_size=10,
            start_date=start_date,
            end_date=end_date
        )
        mock_get_pvz_info.return_value.get.assert_called_once()

        assert result.pvz_list == pvz_data
        assert result.total == total
        assert result.page == 1
        assert result.page_size == 10
        assert result.result == {"status": True}
        assert result.errors is None

    @pytest.mark.asyncio
    async def test_get_pvz_info_unauthorized(
        self,
        mock_get_pvz_info: MagicMock
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            errors="Токен авторизации протух, войдите заново")

        result: PVZInfoResponse = await get_pvz_info(
            start_date="2025-04-01T00:00:00",
            end_date="2025-04-30T23:59:59",
            page=1,
            page_size=10,
            current_user=current_user
        )

        assert result.errors == "Токен авторизации протух, войдите заново"
        assert result.pvz_list is None
        assert result.total is None
        assert result.page is None
        assert result.page_size is None

    @pytest.mark.asyncio
    async def test_get_pvz_info_invalid_role(
        self,
        mock_get_pvz_info: MagicMock
    ) -> None:
        current_user: GetCurrentUserResponse = GetCurrentUserResponse(
            message="Authorization successful",
            email="test@example.com",
            role="invalid_role",
            result={"status": True}
        )

        result: PVZInfoResponse = await get_pvz_info(
            start_date="2025-04-01T00:00:00",
            end_date="2025-04-30T23:59:59",
            page=1,
            page_size=10,
            current_user=current_user
        )

        assert result.errors == "У вас недостаточно прав - необходимая роль: client или moderator"
        assert result.pvz_list is None
        assert result.total is None
        assert result.page is None
        assert result.page_size is None
