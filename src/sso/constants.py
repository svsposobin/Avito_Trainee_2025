from typing import Dict

ERRORS_MAPPING: Dict[str, str] = {
    "invalid input value for enum user_role: \"string\"\nCONTEXT:  unnamed portal parameter $2 = '...'":
        "Некорректный тип пользователя: валидны только client или moderator",

    "new row for relation \"users\" violates check constraint \"users_email_check\"":
        "Некорректный email",

    "password must be at least 7 characters long":
        "Пароль должен быть длиннее 7 символов",

    "new row for relation \"users\" violates check constraint \"users_username_check\"":
        "Имя пользователя должно быть длиннее 5 символов",

    "Invalid user type. Valid types: client or moderator":
        "Некорректный тип пользователя: валидны только client или moderator",

    "1 validation error for UserEmail\nemail\n value is not a valid email address: An email address must have an @-sign.":
        "Некорректный email",

    "invalid input value for enum city_type:":
        "Создать ПВЗ можно только в городах - Москва, Казань, Санкт-Петербург",

    "duplicate key value violates unique constraint \"users_username_key\"":
        "Пользователь с таким никнеймом уже зарегистрирован",

    "duplicate key value violates unique constraint \"users_email_key\"":
        "Пользователь с данным email-ом уже зарегистрирован",

    "insert or update on table":
        "Нельзя создать активную приемку на несуществующий ПВЗ",

    "invalid input value for enum product_type:":
        "Некорректный тип товара, нужен - Электроника, Одежда, Обувь"
}

VALID_USER_TYPES: Dict[str, str] = {
    "client": "client",
    "moderator": "moderator",
}
