from postgres.config import connect
from postgres.dto import InitTableResponse


class Tables:
    @staticmethod
    async def init() -> InitTableResponse:
        try:
            async with await connect() as connection:
                async with connection.cursor() as cursor:
                    """Установка btree_gist"""
                    await cursor.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

                    """EMUNS-ограничения для типов данных"""
                    await cursor.execute(
                        """
                            DO $$
                            BEGIN
                                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                                CREATE TYPE user_role AS ENUM ('client', 'moderator');
                            END IF;
                            END$$;
                            DO $$
                            BEGIN
                                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'city_type') THEN
                                    CREATE TYPE city_type AS ENUM ('Москва', 'Казань', 'Санкт-Петербург');
                            END IF;
                            END$$;
                            DO $$
                            BEGIN
                                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'acceptance_status') THEN
                                    CREATE TYPE acceptance_status AS ENUM ('in_progress', 'close');
                                END IF;
                            END$$;
                            DO $$
                            BEGIN
                                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'product_type') THEN
                                    CREATE TYPE product_type AS ENUM ('электроника', 'одежда', 'обувь');
                                END IF;
                            END$$;
                        """
                    )
                    """Определение time-zone"""
                    await cursor.execute("SET TIME ZONE 'Europe/Moscow';")

                    """Инициализация таблиц"""
                    await cursor.execute(
                        """
                            CREATE TABLE IF NOT EXISTS users (
                                id SERIAL PRIMARY KEY,
                                user_type user_role NOT NULL,
                                username VARCHAR(100) NOT NULL UNIQUE CHECK (length(username) >= 5),
                                password VARCHAR(100) NOT NULL CHECK (length(password) >= 7),
                                email VARCHAR(100) NOT NULL UNIQUE CHECK (
                                    email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$'),
                                uuid_token VARCHAR);
                                
                            CREATE TABLE IF NOT EXISTS pvz_list (
                            id SERIAL PRIMARY KEY,
                            city city_type NOT NULL,
                            registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());
                            
                            CREATE TABLE  IF NOT EXISTS accepting_products (
                            id SERIAL PRIMARY KEY,
                            pvz_id INTEGER NOT NULL REFERENCES pvz_list(id),
                            datetime TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            product_id INTEGER[],
                            status acceptance_status NOT NULL,
                            CONSTRAINT only_one_active_reception 
                                EXCLUDE USING gist (
                                    pvz_id WITH =,
                                    status WITH =) 
                                    WHERE (status = 'in_progress'));
                                    
                            CREATE TABLE IF NOT EXISTS products (
                                id SERIAL PRIMARY KEY,
                                accepting_id INTEGER NOT NULL REFERENCES accepting_products(id),
                                datetime TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                type product_type NOT NULL);
                        """
                    )
            return InitTableResponse(result={"status": True})

        except Exception as error:
            return InitTableResponse(errors=str(error))
