# Описание

Проект YaMDb собирает отзывы пользователей на произведения. Сами произведения в YaMDb не хранятся, здесь нельзя посмотреть фильм или послушать музыку.

Произведения делятся на категории, такие как «Книги», «Фильмы», «Музыка». Например, в категории «Книги» могут быть произведения «Винни-Пух и все-все-все» и «Марсианские хроники», а в категории «Музыка» — песня «Давеча» группы «Жуки» и вторая сюита Баха. Список категорий может быть расширен (например, можно добавить категорию «Изобразительное искусство» или «Ювелирка»).

Произведению может быть присвоен жанр из списка предустановленных (например, «Сказка», «Рок» или «Артхаус»).
Добавлять произведения, категории и жанры может только администратор.

Благодарные или возмущённые пользователи оставляют к произведениям текстовые отзывы и ставят произведению оценку в диапазоне от одного до десяти (целое число); из пользовательских оценок формируется усреднённая оценка произведения — рейтинг (целое число). На одно произведение пользователь может оставить только один отзыв.

Пользователи могут оставлять комментарии к отзывам.
Добавлять отзывы, комментарии и ставить оценки могут только аутентифицированные пользователи.

## Стек технологий

Проект реализован на современном стеке для разработки REST API:

- **Backend:** Python 3.10+, Django 5.2
- **API:** Django REST Framework
- **Аутентификация:** JWT (SimpleJWT), Djoser
- **Авторизация:** RBAC (roles: user, moderator, admin)
- **Фильтрация и поиск:** django-filter, DRF SearchFilter
- **Тестирование:** pytest, pytest-django

## Установка и запуск проекта

### 1. Клонировать репозиторий

```bash
git clone https://github.com/xx6598/api-yamdb.git && cd api-yamdb
```

### 2. Создать и активировать виртуальное окружение

```bash
python3 -m venv venv
. venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Выполнить миграции

```bash
python3 manage.py migrate
```

### 5. Создать суперпользователя (опционально)

```bash
python3 manage.py createsuperuser
```

### 6. Запустить сервер разработки

```bash
python3 manage.py runserver
```

### 7. Проект будет доступен по адресу:

http://127.0.0.1:8000/


## Примеры выполнения запросов

### 1. Регистрация

#### Запрос
```bash
curl -X 'POST' \
-H 'Content-Type: application/json' \
--data '{"email": "available-email@user.ru", "username": "regularr-userr"}' \
http://127.0.0.1:8000/api/v1/auth/signup/
```
### 2. Получение API токена

#### Запрос
```bash
curl -X 'POST' \
-H 'Content-Type: application/json' \
--data '{"username": "regularr-userr", "confirmation_code": "ba2e5717cffb41469d8fde3bd7339619"}' \
http://127.0.0.1:8000/api/v1/auth/token/
```
#### Ответ

```bash
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY3NjI1MDk5LCJpYXQiOjE3Njc1Mzg2OTksImp0aSI6IjhmMTYxNTE2ZTcxMTQ2NzRiMThjOGYwMTI3YTg1YjMyIiwidXNlcl9pZCI6Mn0.4fQkhzYRRdXY8A7bzjUrGX7II3EgbaXGQpro4uAi8m4"
}
```

### 3. Получение списка пользователей

#### Запрос

```bash
curl -X 'GET' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY3NjI1MTg3LCJpYXQiOjE3Njc1Mzg3ODcsImp0aSI6ImVlODljNGJmOTNlZTQzMzVhYTMyMWYxMGMzOGQyNDYzIiwidXNlcl9pZCI6MX0.VCiSkCqbzF4W322lTzVPv6TBDKC8c_wIVLIhYQY0sWM' \
http://127.0.0.1:8000/api/v1/users/
```

#### Ответ

```bash
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "username": "admin",
            "email": "admin@example.com",
            "first_name": "",
            "last_name": "",
            "bio": "",
            "role": "user"
        },
        {
            "username": "regularr-userr",
            "email": "available-email@user.ru",
            "first_name": "",
            "last_name": "",
            "bio": "",
            "role": "user"
        }
    ]
}
```

## Авторы

- Vladislav Pavlov
- Sergey Gritsun
