# Atom Chat

Этот проект представляет собой API для приватного общения между пользователями с использованием WebSocket.

## Используемые технологии

- **FastAPI**: фреймворк для создания API.
- **SQLAlchemy**: ORM для работы с базой данных.
- **asyncpg**: асинхронный драйвер для PostgreSQL.
- **JWT**: JSON Web Tokens для аутентификации и авторизации.
- **PostgreSQL**: база данных для хранения данных.
- **Docker и Docker Compose**: для контейнеризации и упрощения разворачивания приложения.
- **OpenSSL**: для генерации приватных и публичных ключей, используемых при создании и проверке JWT.

## Функциональные возможности

- **Приватные чаты**: обмен сообщениями между пользователями в режиме реального времени через WebSocket.
- **Поиск пользователей**: возможность поиска других пользователей по имени.
- **Модерация и блокировка**: администраторы могут модерировать чаты и блокировать пользователей.
- **Регистрация и авторизация**: пользователи могут регистрироваться и входить в систему с помощью JWT-токенов.

## Запуск

### Предварительные требования

Для запуска проекта убедитесь, что на вашем компьютере установлены **Docker** и **Docker Compose**.


1. **Сборка и запуск контейнеров**  
   В корневой директории проекта выполните команду для сборки и запуска контейнеров:

   ```bash
   docker-compose up --build
   ```
   При первом запуске автоматически генерируются необходимые ключи, инициализируются тестовые данные в базе данных.
2. **API и документация**  
   API будет доступно по адресу http://localhost:7777. С документацией можно ознакомиться по адресу http://localhost:7777/docs.

## Тестовые пользователи

В базе данных автоматически создаются три тестовых пользователя, между которыми есть 10 тестовых сообщений:

| Role        | Email                | Password          |
|-------------|----------------------|-------------------|
| Пользователь | test1@example.com    | test_password_1   |
| Пользователь | test2@example.com    | test_password_2   |
| Модератор    | moderator@example.com | moderator_password_3 |