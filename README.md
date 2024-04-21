# README.md

### API

- http://127.0.0.1:8000/swagger/schema/
- http://127.0.0.1:8000/redoc/

### URL parser
API для хранения ссылок пользователя.   

### ** Требования**   
- Python 3.12+;   
- Django 5.0+ (Django Rest Framework);
- Есть возможность запуска в Docker;

### Features

- Возможность парсить за один раз информацию как с одного веб-сайта, так и 100+ (скрипт-парсер выполнен с использованием async);
- Наличие личного кабинета (возможность регистрации, логина, смены и сброса пароля);
- Возможность управления своими ссылками (создание, редактирование, удаление, просмотр);
- Возможность управления своими коллекциями (создание, редактирование, удаление, просмотр).

#### Запуск в Docker контейнере:

##### SMTP

Укажите настройки SMTP в файле settings.py

- EMAIL_HOST_USER = 'example@gmail.com'
- EMAIL_HOST_PASSWORD = 'app code google'
- DEFAULT_FROM_EMAIL = 'example@gmail.com'

bash:

- cd django_test_task
- docker build -t url-parser .
- docker run -p 8000:8000 url-parser


#### Запуск с помощью development server:

bash:

- cd django_test_task
- pip install -r requirements.txt
- python manage.py makemigrations
- python manage.py migrate
- python manage.py runserver
