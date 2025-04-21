from datetime import timedelta, datetime
from typing import Annotated, Any, Union, Dict, List, Tuple
from fastapi import Form, Depends, Query, Response, Path
from jose import jwt, ExpiredSignatureError

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
    GetPVZInfo
)
from src.dto import JWTTokenResponse
from src.sso.constants import ERRORS_MAPPING, VALID_USER_TYPES
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
from src.tokens import create_access_token, JWTConfig
from fastapi.security import OAuth2PasswordBearer

OAUTH2_SCHEME: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


async def get_current_user(
        response: Response,
        token: str = Depends(OAUTH2_SCHEME)
) -> GetCurrentUserResponse:
    result: GetCurrentUserResponse = GetCurrentUserResponse()
    try:
        if not token:
            result.errors = "Токен авторизации не был найден"
            return result

        payload: Dict[str, str] = jwt.decode(
            token,
            JWTConfig.SECRET_KEY,
            algorithms=[JWTConfig.ALGORITHM],
            options={"require_exp": True}
        )
        user_role: str = payload.get("role")  # type: ignore[assignment]
        user_email: str = payload.get("sub")  # type: ignore[assignment]

        db_token: str = await GetMe(
            email=user_email,
        ).get()

        if not db_token or db_token != token:
            result.errors = "Некорректный токен"
            return result

        if user_role not in VALID_USER_TYPES.values():
            result.errors = "Некорректная роль"
            return result

        return GetCurrentUserResponse(
            message="Authorization successful",
            role=user_role,
            email=user_email,
            result={"status": True}
        )

    except ExpiredSignatureError:
        response.headers["Authorization"] = ""
        result.errors = "Токен авторизации протух, войдите заново"
        return result

    except Exception as err:
        error_message = str(err).split("\nDETAIL:")[0].strip()
        result.errors = ERRORS_MAPPING.get(error_message, str(err))

    return result


async def register(
        username: Annotated[
            str,
            Form(description="Уникальное имя пользователя (От 5 символов)")
        ],
        user_type: Annotated[str, Form(description="Тип пользователя (client или moderator)")],
        password: Annotated[str, Form(description="Пароль (От 7 символов)")],
        email: Annotated[str, Form(description="Уникальный email пользователя")]
) -> RegisterUserResponse:
    result: RegisterUserResponse = RegisterUserResponse()

    try:
        access_token: JWTTokenResponse = create_access_token(  # type: ignore[assignment]
            data={"sub": email, "role": user_type},
            expires_delta=timedelta(minutes=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        sql_query: Tuple = await UserRegisterMutation(  # type: ignore[assignment]
            username=username,
            user_type=user_type,
            password=password,
            email=email,
            uuid=access_token.access_token
        ).register()

        return RegisterUserResponse(
            result={"success": True},
            user={
                "id": sql_query[0],
                "username": sql_query[1],
                "email": sql_query[3]
            }
        )

    except Exception as err:
        error_message = str(err).split("\nDETAIL:")[0].strip()
        result.errors = ERRORS_MAPPING.get(error_message, str(err))
        result.result = None

    return result


async def login(
        username: Annotated[str, Form(description="Указанный никнейм при регистрации")],
        password: Annotated[str, Form(description="Указанный пароль при регистрации")],
) -> LoginUserResponse:
    result: LoginUserResponse = LoginUserResponse()

    try:
        process_login: Tuple = await UserLoginMutation(  # type: ignore[assignment]
            username=username,
            password=password
        ).login()

        new_token: str = await UpdateAccessTokenMutation(  # type: ignore[assignment]
            email=process_login[3],
            user_type=process_login[2]
        ).update()

        return LoginUserResponse(
            result={"success": True},
            token=new_token
        )

    except Exception as err:
        error_message = str(err).split("\nDETAIL:")[0].strip()
        result.errors = ERRORS_MAPPING.get(error_message, str(err))
        result.result = None

    return result


async def init_pvz(
        city: Annotated[str, Form(description="Город, в котором нужно создать ПВЗ")],
        current_user: GetCurrentUserResponse = Depends(get_current_user),
) -> InitPVZResponse:
    result: InitPVZResponse = InitPVZResponse()

    try:
        if current_user.errors == "Токен авторизации протух, войдите заново":
            result.errors = "Токен авторизации протух, войдите заново"
            return result
        if current_user.email is None or current_user.role is None:
            raise Exception("Токен доступа протух или не найден")
        if current_user.role != VALID_USER_TYPES.get("moderator"):
            raise Exception("У вас недостаточно прав - необходимая роль: moderator")

        sql_query: Tuple = await PVZ(  # type: ignore[assignment]
            city=city
        ).create()

        return InitPVZResponse(
            id=sql_query[0],
            city=sql_query[1],
            registered_at=sql_query[2],
            result={"status": True}
        )

    except Exception as err:
        error_message = str(err).split("\"")[0].strip()
        result.errors = ERRORS_MAPPING.get(error_message, str(err))

    return result


async def receptions(
        pvz_id: Annotated[int, Form(description="ID Конкретного созданного ПВЗ")],
        current_user: GetCurrentUserResponse = Depends(get_current_user),
) -> InitActiveReceptionsResponse:
    result: InitActiveReceptionsResponse = InitActiveReceptionsResponse()

    try:
        if current_user.errors == "Токен авторизации протух, войдите заново":
            result.errors = "Токен авторизации протух, войдите заново"
            return result
        if current_user.email is None or current_user.role is None:
            raise Exception("Токен доступа протух или не найден")
        if current_user.role != VALID_USER_TYPES.get("client"):
            raise Exception("У вас недостаточно прав - необходимая роль: client")

        await CheckActiveAccepting(pvz_id=pvz_id).check()

        sql_query: Tuple = await InitReceptions(  # type: ignore[assignment]
            pvz_id=pvz_id,
        ).init()

        return InitActiveReceptionsResponse(
            receptions_id=sql_query[0],
            pvz_id=sql_query[1],
            status=sql_query[2],
            result={"status": True}
        )

    except Exception as err:
        error_message = str(err).split("\"")[0].strip()
        result.errors = ERRORS_MAPPING.get(error_message, str(err))

    return result


async def add_product(
        accepting_id: Annotated[int, Form(description="ID Конкретной открытой - 'Приемки заказов'")],
        product_type: Annotated[str, Form(description="Тип товара - Одежда, Электроника, Обувь")],
        current_user: GetCurrentUserResponse = Depends(get_current_user),
) -> AddProductResponse:
    result: AddProductResponse = AddProductResponse()

    try:
        if current_user.errors == "Токен авторизации протух, войдите заново":
            result.errors = "Токен авторизации протух, войдите заново"
            return result
        if current_user.email is None or current_user.role is None:
            raise Exception("Токен доступа протух или не найден")
        if current_user.role != VALID_USER_TYPES.get("client"):
            raise Exception("У вас недостаточно прав - необходимая роль: client")

        await CheckAcceptingStatus(accepting_id=accepting_id).check()

        sql_query: Tuple = await AddProduct(  # type: ignore[assignment]
            accepting_id=accepting_id,
            product_type=product_type.lower(),
        ).add()

        return AddProductResponse(
            product_id=sql_query[0],
            accepting_id=sql_query[1],
            type=sql_query[2],
            datetime=str(sql_query[3]),
            result={"status": True}
        )

    except Exception as err:
        error_message = str(err).split("\"")[0].strip()
        result.errors = ERRORS_MAPPING.get(error_message, str(err))

    return result


async def delete_last_product(
        pvz_id: int = Path(description="ID ПВЗ для удаления товара"),
        current_user: GetCurrentUserResponse = Depends(get_current_user),
) -> DeleteProductResponse:
    result: DeleteProductResponse = DeleteProductResponse()

    try:
        if current_user.errors == "Токен авторизации протух, войдите заново":
            result.errors = "Токен авторизации протух, войдите заново"
            return result
        if current_user.email is None or current_user.role is None:
            raise Exception("Токен доступа протух или не найден")
        if current_user.role != VALID_USER_TYPES.get("client"):
            raise Exception("У вас недостаточно прав - необходимая роль: client")

        active_accepting: Tuple = await GetActiveAccepting(pvz_id=pvz_id).get()  # type: ignore[assignment]
        accepting_id: int = active_accepting[0]
        product_ids: List[int] = active_accepting[1]

        if not product_ids:
            raise Exception("В приемке нет товаров для удаления")

        # Определяем последний добавленный товар (LIFO)
        last_product_id = product_ids[-1]

        deleted_product: Tuple = await DeleteLastProduct(  # type: ignore[assignment]
            accepting_id=accepting_id,
            product_id=last_product_id,
        ).delete()

        return DeleteProductResponse(
            product_id=deleted_product[0],
            accepting_id=deleted_product[1],
            type=deleted_product[2],
            datetime=str(deleted_product[3]),
            result={"status": True}
        )

    except Exception as err:
        error_message = str(err).split("\"")[0].strip()
        result.errors = ERRORS_MAPPING.get(error_message, str(err))

    return result


async def close_last_reception(
        pvz_id: int = Path(description="ID ПВЗ Для закрытия последней приемки"),
        current_user: GetCurrentUserResponse = Depends(get_current_user),
) -> CloseReceptionResponse:
    result: CloseReceptionResponse = CloseReceptionResponse()

    try:
        if current_user.errors == "Токен авторизации протух, войдите заново":
            result.errors = "Токен авторизации протух, войдите заново"
            return result
        if current_user.email is None or current_user.role is None:
            raise Exception("Токен доступа протух или не найден")
        if current_user.role != VALID_USER_TYPES.get("client"):
            raise Exception("У вас недостаточно прав - необходимая роль: client")

        close_reception: Tuple = await CloseReception(pvz_id=pvz_id).close()  # type: ignore[assignment]

        return CloseReceptionResponse(
            reception_id=close_reception[0],
            pvz_id=close_reception[1],
            status=close_reception[2],
            result={"status": True}
        )

    except Exception as err:
        error_message = str(err).split("\"")[0].strip()
        result.errors = ERRORS_MAPPING.get(error_message, str(err))

    return result


async def get_pvz_info(
        start_date: Annotated[str, Query(description="Введите начальную дату в формате ISO - 2025-04-01T00:00:00")],
        end_date: Annotated[str, Query(description="Введите конечную дату в формате ISO - 2025-04-30T23:59:59")],
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 10,
        current_user: GetCurrentUserResponse = Depends(get_current_user),
) -> PVZInfoResponse:
    result: PVZInfoResponse = PVZInfoResponse()

    try:
        if current_user.errors == "Токен авторизации протух, войдите заново":
            result.errors = "Токен авторизации протух, войдите заново"
            return result
        if current_user.email is None or current_user.role is None:
            raise Exception("Токен доступа протух или не найден")
        if current_user.role not in [VALID_USER_TYPES.get("client"), VALID_USER_TYPES.get("moderator")]:
            raise Exception("У вас недостаточно прав - необходимая роль: client или moderator")

        start_dt: datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt: datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        pvz_data: List[Union[Dict[str, str], List[Union[Dict[str, Union[str, Any]]]]]]
        total: int
        pvz_data, total = await GetPVZInfo(
            page=page,
            page_size=page_size,
            start_date=start_dt,
            end_date=end_dt
        ).get()

        return PVZInfoResponse(
            pvz_list=pvz_data,
            total=total,
            page=page,
            page_size=page_size,
            result={"status": True}
        )

    except Exception as err:
        error_message = str(err).split("\"")[0].strip()
        result.errors = ERRORS_MAPPING.get(error_message, str(err))

    return result
