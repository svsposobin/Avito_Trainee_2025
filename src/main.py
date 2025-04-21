from sys import path as sys_path
from os import getcwd
from uvicorn import run as uvicorn_run
from fastapi import FastAPI

# Adding ./src to python path for running from console purpose:
sys_path.append(getcwd())

from src.sso.routes import sso_router

app = FastAPI(
    title="[AVITO] - Trainee-spring-2025 - ",
    description=
    """
        --------------------------------------------------------------------------------------------------------------------------------------------------
        OpenAPI (Swagger) Для выполненного тех.задания\n
        Ссылка на ТЗ: https://github.com/avito-tech/tech-internship/blob/main/Tech%20Internships/Backend/Backend-trainee-assignment-spring-2025/Backend-trainee-assignment-spring-2025.md
        --------------------------------------------------------------------------------------------------------------------------------------------------
        Было создано по смехе: https://github.com/avito-tech/tech-internship/blob/main/Tech%20Internships/Backend/Backend-trainee-assignment-spring-2025/swagger.yaml
    """,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "operationsSorter": "alpha"
    }
)

app.include_router(router=sso_router)

if __name__ == "__main__":
    # Разкомментить, если миграция не прошла (Инициализация таблиц):
    from asyncio import run as asyncio_run
    from postgres.sql.init_tables import Tables
    asyncio_run(Tables.init())

    uvicorn_run(app, host="0.0.0.0", port=8090)
