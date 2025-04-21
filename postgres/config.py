from dotenv import load_dotenv, find_dotenv
from os import getenv
from dataclasses import dataclass
from psycopg import AsyncConnection

load_dotenv(find_dotenv(filename=".env.postgres.local"))


@dataclass
class PSQLConfig:
    DB_USER: str = getenv("PSG_LOCAL_USER", default="postgres")
    DB_NAME: str = getenv("PSG_LOCAL_NAME", default="postgres")
    DB_PASSWORD: str = getenv("PSG_LOCAL_PASSWORD", default="")
    DB_HOST: str = getenv("PSG_LOCAL_HOST", default="localhost")
    DB_PORT: str = getenv("PSG_LOCAL_PORT", default="5432")


async def connect(db: PSQLConfig = PSQLConfig) -> AsyncConnection:  # type: ignore[assignment]
    connection: AsyncConnection = await AsyncConnection.connect(
        host=db.DB_HOST,
        port=db.DB_PORT,
        user=db.DB_USER,
        password=db.DB_PASSWORD,
        dbname=db.DB_NAME,
    )
    return connection
