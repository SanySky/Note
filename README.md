# Приложение для создания заметок


## Шаг 1: Клонирование репозитория

`Сначала клонируйте репозиторий на ваш локальный компьютер. Для этого выполните следующую команду:`

```bash
git clone https://github.com/SanySky/Note
```

## Шаг 2: Настройка переменных окружения

`Создайте файл .env в корневой директории проекта и добавьте в него необходимые переменные окружения:`
```
SECRET_KEY= you_secret_key
DATABASE_URL=you_pass
DB_NAME=database_note
DB_USER=postgres
```

## Шаг 3: Сборка и запуск контейнеров Docker

`Соберите и запустите контейнеры Docker с помощью docker-compose:`
```bash
docker compose -f docker-compose.yml up -d --build
```
`Эта команда соберет образы Docker и запустит контейнеры в соответствии с конфигурацией, указанной в файле docker-compose.yml.`

## Шаг 4: Создание миграций

`Создайте миграции с помощью команды:`
```bash
docker compose -f docker-compose.yml exec web alembic revision --autogenerate -m "initial migration" --no-input
```
```bash
docker compose -f docker-compose.yml exec web alembic upgrade head --no-input
```

## Использование API

`Описание функциональности:`
## Базовый URL

```
http://127.0.0.1:8000
```
#### Примеры GET запросов:

```markdown
### Получить список заметок пользователя 

```bash
curl -X GET "http://127.0.0.1:8000/notes" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
```

#### Примеры POST запросов 

```markdown
### Создать новую заметку 

```bash
curl -X POST "http://127.0.0.1:8000/notes" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "content": "John Doe",
         }'
```

```markdown
### Зарегистрировать нового пользователя 

```bash
curl -X POST "http://127.0.0.1:8000/register" \
     -H "Content-Type: application/json" \
     -d '{
           "username": "testuser1",
           "password": "testpassword1"
         }'
```

```markdown
### Войти в систему 

```bash
curl -X POST "http://127.0.0.1:8000/login" \
     -H "Content-Type: application/json" \
     -d '{
           "username": "testuser",
           "password": "testpassword"
         }'
```
