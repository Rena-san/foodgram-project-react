# Foodgram - сайт для публикации рецептов
![workflow](https://github.com/Rena-san/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)
---
### Сервис доступен по адресу:
158.160.48.65
### Возможности сервиса:
- Размещение различных рецептов;
- Просмотр рецептов пользователей сайта;
- Добавление рецептов в избранное;
- Получение списка ингредиентов необходимых для приготовления выбранного рецепта
- Подписка на авторов понравившихся рецептов.

### Технологии:
- Django
- Python
- Docker



### Запуск проекта:
1. Клонируйте проект:
```
git clone <foodgram-project>
```
2. Скопируйте на сервер следующие файлы:
```
scp docker-compose.yml <username>@<host>:/home/<username>/
scp nginx.conf <username>@<host>:/home/<username>/
scp .env <username>@<host>:/home/<username>/<foodgram-project>/infra/

```
3. Установите docker и docker-compose:
```
sudo apt install docker.io 
sudo apt install docker-compose
```
4. Соберите контейнер и выполните миграции:
```
sudo docker-compose up -d --build
sudo docker-compose exec backend python manage.py migrate
```
5. Создайте суперюзера и соберите статику:
```
sudo docker-compose exec backend python manage.py createsuperuser
sudo docker-compose exec backend python manage.py collectstatic --no-input
```
6. Скопируйте предустановленные данные json:
```
sudo docker-compose exec backend python manage.py load_ingredients
sudo docker-compose exec backend python manage.py loaddata tags.json
```
7. Данные для проверки работы приложения:

Cуперпользователь:
```
Админ зона: 158.160.48.65/admin
login: admin
email: admin@mail.ru
password: admin
```
Тестовый юзер:
```
login: matrosskin
email: matrosskin@mail.ru
password: figbam
```
