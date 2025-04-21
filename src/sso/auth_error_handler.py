from typing import Optional

from starlette import status
from starlette.responses import JSONResponse


def auth_error(result) -> Optional[JSONResponse]:
    if result.errors == "Токен авторизации протух, войдите заново":
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"errors": result.errors}
        )

    return None
