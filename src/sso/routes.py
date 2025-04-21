from fastapi import APIRouter, Depends, Response
from starlette import status
from starlette.responses import JSONResponse
from src.sso.auth_error_handler import auth_error
from src.sso.dependencies import (
    register as register_dependency,
    get_current_user as get_current_user_dependency,
    login as login_dependency,
    init_pvz as init_pvz_dependency,
    receptions as receptions_dependency,
    add_product as add_product_dependency,
    delete_last_product as delete_last_product_dependency,
    close_last_reception as close_last_reception_dependency,
    get_pvz_info as get_pvz_info_dependency,
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

sso_router = APIRouter()


@sso_router.post(
    path="/register",
    response_class=JSONResponse,
    name="register",
    tags=["Вход и регистрация"])
async def register(
        current_user: GetCurrentUserResponse = Depends(get_current_user_dependency),
        result: RegisterUserResponse = Depends(register_dependency),
):
    if current_user.message == "Authorization successful":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=RegisterUserResponse(errors="Вы уже авторизованы").__dict__
        )

    expired_token_error = auth_error(result=current_user)
    if expired_token_error:
        return expired_token_error
    if result.errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=RegisterUserResponse(errors=result.errors).__dict__
        )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=result.__dict__
    )


@sso_router.post(
    path="/login",
    response_class=JSONResponse,
    name="login",
    tags=["Вход и регистрация"]
)
async def login(
        response: Response,
        current_user: GetCurrentUserResponse = Depends(get_current_user_dependency),
        result: LoginUserResponse = Depends(login_dependency),
):
    if current_user.message == "Authorization successful":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=LoginUserResponse(errors="Вы уже авторизованы").__dict__
        )

    expired_token_error = auth_error(result=current_user)
    if expired_token_error:
        return expired_token_error
    if result.errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=LoginUserResponse(errors=result.errors).__dict__
        )

    response.headers["Authorization"] = f"Bearer {result.token}"
    return {"access_token": result.token, "token_type": "bearer"}


@sso_router.get(
    path="/authorization-checker",
    response_class=JSONResponse,
    name="Проверка наличия активной авторизации за текущую сессию",
    tags=["Различные проверки"]
)
async def token_checker(
        result: GetCurrentUserResponse = Depends(get_current_user_dependency),
):
    expired_token_error = auth_error(result=result)
    if expired_token_error:
        return expired_token_error
    if result.errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=GetCurrentUserResponse(errors=result.errors).__dict__
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result.__dict__
    )


@sso_router.post(
    path="/pvz",
    response_class=JSONResponse,
    name="Создание нового ПВЗ (Только для - moderator)",
    tags=["ПВЗ"],
    description=
    """
        --------------------------------------------------------\n
        ПВЗ можно открыть только в - Москва, Казань, Санкт-Петербург
    """
)
async def init_pvz(
        result: InitPVZResponse = Depends(init_pvz_dependency)
):
    expired_token_error = auth_error(result=result)
    if expired_token_error:
        return expired_token_error
    if result.errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=InitPVZResponse(errors=result.errors).__dict__
        )

    return result


@sso_router.post(
    path="/receptions",
    response_class=JSONResponse,
    name="Создание активной приемки (Только для - client)",
    tags=["ПВЗ"],
    description=
    """
        --------------------------------------------------------\n
        Для успешной инициализации активной приемки нужны:\n
          - ID Созданного в БД ПВЗ (pvz_id);
          - Отсутствие других активных приемок на данном ПВЗ
          - Роль пользователя: client
    """
)
async def receptions(
        result: InitActiveReceptionsResponse = Depends(receptions_dependency),
):
    expired_token_error = auth_error(result=result)
    if expired_token_error:
        return expired_token_error
    if result.errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=InitActiveReceptionsResponse(errors=result.errors).__dict__
        )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=result.__dict__
    )


@sso_router.post(
    path="/products",
    response_class=JSONResponse,
    name="Добавление товара в активную приемку (Только для - Client)",
    tags=["ПВЗ"],
    description=
    """
        --------------------------------------------------------\n
        Для успешного добавления товара в приемку нужны:\n
          - ID существующей незакрытой приемки (accepting_id);
          - Тип товара (электроника, одежда, обувь);
          - Роль пользователя: client
    """
)
async def add_product(
        result: AddProductResponse = Depends(add_product_dependency),
):
    expired_token_error = auth_error(result=result)
    if expired_token_error:
        return expired_token_error
    if result.errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=AddProductResponse(errors=result.errors).__dict__
        )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=result.__dict__
    )


@sso_router.delete(
    path="/pvz/{pvz_id}/delete_last_product",
    response_class=JSONResponse,
    name="Удаление последнего товара из приемки (Только для - Client)",
    tags=["ПВЗ"],
    description=
    """
        --------------------------------------------------------\n
        Удаляет последний добавленный товар (LIFO) из незакрытой приемки для указанного ПВЗ.\n
        Условия:\n
          - Пользователь должен иметь роль client;
          - Приемка должна быть незакрытой (status = 'in_progress');
          - Должны быть товары в приемке
    """
)
async def delete_last_product(
        result: DeleteProductResponse = Depends(delete_last_product_dependency),
):
    expired_token_error = auth_error(result=result)
    if expired_token_error:
        return expired_token_error
    if result.errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=DeleteProductResponse(errors=result.errors).__dict__
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result.__dict__
    )


@sso_router.post(
    path="/pvz/{pvz_id}/close_last_reception",
    response_class=JSONResponse,
    name="Закрытие последней приемки (Только для - client)",
    tags=["ПВЗ"],
    description=
    """
        --------------------------------------------------------\n
        Закрывает последнюю незакрытую приемку для указанного ПВЗ.\n
        Условия:\n
          - Пользователь должен иметь роль client;
          - Приемка должна быть незакрытой (status = 'in_progress')
    """
)
async def close_last_reception(
        result: CloseReceptionResponse = Depends(close_last_reception_dependency),
):
    expired_token_error = auth_error(result=result)
    if expired_token_error:
        return expired_token_error
    if result.errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=CloseReceptionResponse(errors=result.errors).__dict__
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result.__dict__
    )


@sso_router.get(
    path="/pvz-info",
    response_class=JSONResponse,
    name="Получение информации о ПВЗ с пагинацией и фильтром по дате (Только для - client и moderator)",
    tags=["ПВЗ"],
    description=
    """
        --------------------------------------------------------\n
        Возвращает список ПВЗ с информацией о приемках и товарах.\n
        Условия:\n
          - Пользователь должен иметь роль client или moderator;
          - Поддерживает пагинацию (параметры page и page_size);
          - Поддерживает фильтрацию по диапазону дат приемки (start_date и end_date)
    """
)
async def get_pvz_info(
        result: PVZInfoResponse = Depends(get_pvz_info_dependency),
):
    expired_token_error = auth_error(result=result)
    if expired_token_error:
        return expired_token_error
    if result.errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=PVZInfoResponse(errors=result.errors).__dict__
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result.__dict__
    )
