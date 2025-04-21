from dataclasses import dataclass
from dotenv import load_dotenv, find_dotenv
from os import getenv
from datetime import datetime, timedelta, UTC
from jose import jwt
from typing import Optional, Union
from src.dto import JWTTokenResponse

load_dotenv(find_dotenv(".env.jwt.local"))


@dataclass(frozen=True)
class JWTConfig:
    SECRET_KEY: str = getenv("SECRET_KEY", default="TEST_SECRET_KEY")
    ALGORITHM: str = getenv("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: float = float(getenv("ACCESS_TOKEN_EXPIRE_MINUTES", default=30))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> Union[JWTTokenResponse, Exception]:
    try:
        to_encode = data.copy()
        if expires_delta:
            expire: datetime = datetime.now(UTC) + expires_delta
        else:
            expire: datetime = datetime.now(UTC) + timedelta(  # type: ignore[no-redef]
                minutes=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire})

        return JWTTokenResponse(access_token=jwt.encode(to_encode, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM))

    except Exception as error:
        raise error
