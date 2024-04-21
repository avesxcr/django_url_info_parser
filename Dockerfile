FROM python

ENV APP_NAME=DJANGO_TEST_TASK

WORKDIR /test_task

COPY . .

ADD requirements.txt /test_task/
RUN pip install -r requirements.txt
RUN python manage.py makemigrations
RUN python manage.py migrate

EXPOSE 8000

CMD gunicorn django_test_task.wsgi:application -b 0.0.0.0:8000
