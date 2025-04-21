from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Optional, Union, List, Dict, Any, Tuple

from bcrypt import gensalt as bcrypt_salt, hashpw as bcrypt_hashpw, checkpw as bcrypt_checkpw
from psycopg.sql import SQL

from postgres.config import connect
from src.dto import JWTTokenResponse
from src.tokens import create_access_token, JWTConfig


@dataclass(frozen=True)
class UserRegisterMutation:
    username: str
    user_type: str
    password: str
    email: str
    uuid: str

    async def register(self) -> Union[Tuple, Exception]:
        if len(self.password) < 7:
            raise ValueError("password must be at least 7 characters long")

        try:
            hashed_password: Union[str, Exception] = self.__hashed_password(self.password)

            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query="""
                                INSERT INTO users (username, user_type, password, email, uuid_token)
                                VALUES (%s, %s, %s, %s, %s)
                                RETURNING id, user_type, username, email
                            """,
                        params=(self.username, self.user_type, hashed_password, self.email, self.uuid)
                    )

                    result: Optional[Tuple[Any]] = await cursor.fetchone()
                    if result is None:
                        raise Exception("Что-то пошло не так")

                    return result

        except Exception as error:
            raise error

    @staticmethod
    def __hashed_password(password: str) -> Union[str, Exception]:
        try:
            salt = bcrypt_salt()
            hashed = bcrypt_hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")

        except Exception as error:
            raise error


@dataclass(frozen=True)
class UserLoginMutation:
    username: str
    password: str

    async def login(self) -> Union[Tuple, Exception]:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query=
                        """
                            SELECT username, password, user_type, email FROM users WHERE username = %s
                        """,
                        params=(self.username,)
                    )

                    user: Optional[Tuple] = await cursor.fetchone()
                    if user is None:
                        raise Exception("Пользователь не найден")

                    hashed_password: str = user[1]  # type: ignore[misc]
                    if not bcrypt_checkpw(self.password.encode(), hashed_password.encode()):
                        raise Exception("Некорректный пароль")

                    user_name: str = user[0]
                    if self.username != user_name:
                        raise Exception("Некорректный никнейм")

                    return user

        except Exception as error:
            raise error


@dataclass(frozen=True)
class UpdateAccessTokenMutation:
    email: str
    user_type: str

    async def update(self) -> Union[str, Exception]:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    new_token: JWTTokenResponse = create_access_token(  # type: ignore[assignment]
                        data={"sub": self.email, "role": self.user_type},
                        expires_delta=timedelta(minutes=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
                    )
                    await cursor.execute(
                        query=
                        """
                            UPDATE users
                            SET uuid_token = %s
                            WHERE email = %s
                            RETURNING uuid_token
                        """,
                        params=(str(new_token.access_token), self.email)
                    )
                    result: Optional[tuple[str]] = await cursor.fetchone()
                    if result is None:
                        raise Exception("Oops, token not found")

                    return result[0]

        except Exception as error:
            raise error


@dataclass(frozen=True)
class GetMe:
    email: str

    async def get(self) -> str:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query=
                        """
                            SELECT uuid_token FROM users WHERE email = %s
                        """,
                        params=(self.email,)
                    )
                    token: Optional[tuple[str]] = await cursor.fetchone()
                    if token is None:
                        raise Exception("Access not found")

                    return token[0]

        except Exception as error:
            raise error


@dataclass(frozen=True)
class PVZ:
    city: str

    async def create(self) -> Union[Tuple, Exception]:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query=
                        """
                            INSERT INTO pvz_list (city)
                            VALUES (%s)
                            RETURNING id, city, registered_at
                        """,
                        params=(self.city,)
                    )
                    result: Optional[tuple[str]] = await cursor.fetchone()
                    if not result:
                        raise Exception("Не получилось завести запись о новом ПВЗ")

                    return result

        except Exception as error:
            raise error


@dataclass(frozen=True)
class CheckActiveAccepting:
    pvz_id: int

    async def check(self) -> None:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query=
                        """
                            SELECT id FROM accepting_products WHERE pvz_id = %s AND status = 'in_progress'
                        """,
                        params=(self.pvz_id,)
                    )

                    if await cursor.fetchone():
                        raise Exception("Для этого ПВЗ уже существуют активная приемка")

        except Exception as error:
            raise error


@dataclass(frozen=True)
class InitReceptions:
    pvz_id: int

    async def init(self) -> Union[Tuple, Exception]:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query=
                        """
                            INSERT INTO accepting_products (pvz_id, status)
                            VALUES (%s, %s)
                            RETURNING id, pvz_id, status
                        """,
                        params=(self.pvz_id, "in_progress")
                    )

                    result: Optional[tuple[str]] = await cursor.fetchone()
                    if result is None:
                        raise Exception("Не получилось создать приемку")

                    return result

        except Exception as error:
            raise error


@dataclass(frozen=True)
class CheckAcceptingStatus:
    accepting_id: int

    async def check(self) -> None:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query=
                        """
                            SELECT status FROM accepting_products WHERE id = %s
                        """,
                        params=(self.accepting_id,)
                    )

                    result: Optional[tuple[str]] = await cursor.fetchone()
                    if result is None:
                        raise Exception("Приемка не найдена")

                    if result[0] != "in_progress":
                        raise Exception("Приемка закрыта")

        except Exception as error:
            raise error


@dataclass(frozen=True)
class AddProduct:
    accepting_id: int
    product_type: str

    async def add(self) -> Union[Tuple, Exception]:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query=
                        """
                            INSERT INTO products (accepting_id, type)
                            VALUES (%s, %s)
                            RETURNING id, accepting_id, type, datetime
                        """,
                        params=(self.accepting_id, self.product_type)
                    )
                    product: Optional[tuple[str]] = await cursor.fetchone()
                    if product is None:
                        raise Exception("Не удалось обновить товар")

                    product_id: str = product[0]

                    await cursor.execute(
                        query=
                        """
                            UPDATE accepting_products
                            SET product_id = array_append(product_id, %s)
                            WHERE id = %s
                            RETURNING product_id
                        """,
                        params=(product_id, self.accepting_id)
                    )

                    updated_products: Optional[tuple[str]] = await cursor.fetchone()
                    if updated_products is None:
                        raise Exception("Не удалось обновить список товаров в приемке")

                    return product

        except Exception as error:
            raise error


@dataclass(frozen=True)
class GetActiveAccepting:
    pvz_id: int

    async def get(self) -> Union[Tuple, Exception]:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query=
                        """
                            SELECT id, product_id FROM accepting_products
                            WHERE pvz_id = %s AND status = 'in_progress'
                        """,
                        params=(self.pvz_id,)
                    )
                    result: Optional[tuple[str]] = await cursor.fetchone()
                    if result is None:
                        raise Exception("Активная приемка для данного ПВЗ не найдена")

                    return result

        except Exception as error:
            raise error


@dataclass(frozen=True)
class DeleteLastProduct:
    accepting_id: int
    product_id: int

    async def delete(self) -> Union[Tuple, Exception]:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query=
                        """
                            SELECT id, accepting_id, type, datetime
                            FROM products
                            WHERE accepting_id = %s AND id = %s
                        """,
                        params=(self.accepting_id, self.product_id)
                    )
                    product: Optional[tuple[str]] = await cursor.fetchone()
                    if product is None:
                        raise Exception("Товар не найден")

                    await cursor.execute(
                        query=
                        """
                            DELETE FROM products
                            WHERE id = %s AND accepting_id = %s
                        """,
                        params=(self.product_id, self.accepting_id)
                    )

                    await cursor.execute(
                        query=
                        """
                            UPDATE accepting_products
                            SET product_id = array_remove(product_id, %s)
                            WHERE id = %s
                            RETURNING product_id
                        """,
                        params=(self.product_id, self.accepting_id)
                    )
                    updated_products: Optional[tuple[str]] = await cursor.fetchone()
                    if updated_products is None:
                        raise Exception("Не удалось обновить список товаров в приемке")

                    return product

        except Exception as error:
            raise error


@dataclass(frozen=True)
class CloseReception:
    pvz_id: int

    async def close(self) -> Union[Tuple, Exception]:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query=
                        """
                            SELECT id, pvz_id, status FROM accepting_products
                            WHERE pvz_id = %s AND status = 'in_progress'
                        """,
                        params=(self.pvz_id,)
                    )
                    reception: Optional[tuple[str]] = await cursor.fetchone()
                    if reception is None:
                        raise Exception("Активная приемка для данного ПВЗ не найдена")

                    reception_id: str = reception[0]

                    await cursor.execute(
                        query=
                        """
                            UPDATE accepting_products
                            SET status = 'close'
                            WHERE id = %s
                            RETURNING id, pvz_id, status
                        """,
                        params=(reception_id,)
                    )
                    updated_reception: Optional[tuple[str]] = await cursor.fetchone()
                    if updated_reception is None:
                        raise Exception("Не удалось закрыть приемку")

                    return updated_reception

        except Exception as error:
            raise error


@dataclass(frozen=True)
class GetPVZInfo:
    page: int
    page_size: int
    start_date: datetime
    end_date: datetime

    async def get(self) -> Tuple[List[Union[Dict[str, str], List[Union[Dict[str, Union[str, Any]]]]]], int]:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    """Определение time-zone"""
                    await cursor.execute("SET TIME ZONE 'Europe/Moscow';")

                    offset: int = (self.page - 1) * self.page_size
                    query: SQL = SQL("""
                        SELECT 
                            p.id,
                            p.city,
                            p.registered_at,
                            COALESCE(
                                json_agg(
                                    json_build_object(
                                        'id', ap.id,
                                        'pvz_id', ap.pvz_id,
                                        'datetime', ap.datetime,
                                        'product_ids', ap.product_id,
                                        'status', ap.status,
                                        'products', (
                                            SELECT COALESCE(
                                                json_agg(
                                                    json_build_object(
                                                        'id', pr.id,
                                                        'accepting_id', pr.accepting_id,
                                                        'datetime', pr.datetime,
                                                        'type', pr.type
                                                    )
                                                ),
                                                '[]'::json
                                            )
                                            FROM products pr
                                            WHERE pr.accepting_id = ap.id
                                        )
                                    )
                                ) FILTER (WHERE ap.id IS NOT NULL),
                                '[]'::json
                            ) as receptions
                        FROM pvz_list p
                        LEFT JOIN (
                            SELECT *
                            FROM accepting_products
                            WHERE %s IS NULL OR datetime >= %s
                            AND %s IS NULL OR datetime <= %s
                        ) ap ON p.id = ap.pvz_id
                        GROUP BY p.id, p.city, p.registered_at
                        ORDER BY p.id
                        LIMIT %s OFFSET %s
                    """)

                    count_query: SQL = SQL("""
                        SELECT COUNT(DISTINCT p.id)
                        FROM pvz_list p
                        LEFT JOIN (
                            SELECT pvz_id
                            FROM accepting_products
                            WHERE %s IS NULL OR datetime >= %s
                            AND %s IS NULL OR datetime <= %s
                        ) ap ON p.id = ap.pvz_id
                    """)

                    params: List[Union[Optional[datetime | int]]] = [
                        self.start_date, self.start_date,
                        self.end_date, self.end_date,
                        self.page_size, offset
                    ]

                    await cursor.execute(query, params)
                    pvz_data: Optional[List[Any]] = await cursor.fetchall()

                    count_params = params[:-2]
                    await cursor.execute(count_query, count_params)
                    total: int = (await cursor.fetchone())[0]  # type: ignore[index]

                    formatted_data: List[Union[Dict[str, str] | List[Union[Dict[str, str | Any]]]]] = [
                        {
                            "id": row[0],
                            "city": row[1],
                            "registered_at": str(row[2]),
                            "receptions": [  # type: ignore[dict-item]
                                {
                                    "id": reception["id"],
                                    "pvz_id": reception["pvz_id"],
                                    "datetime": str(reception["datetime"]),
                                    "product_ids": reception["product_ids"],
                                    "status": reception["status"],
                                    "products": [
                                        {
                                            "id": product["id"],
                                            "accepting_id": product["accepting_id"],
                                            "datetime": str(product["datetime"]),
                                            "type": product["type"]
                                        }
                                        for product in reception["products"]
                                    ]
                                }
                                for reception in row[3]
                            ]
                        }
                        for row in pvz_data  # type: ignore[union-attr]
                    ]

                    return formatted_data, total

        except Exception as error:
            raise error
