#!/usr/bin/env bash
echo "Start backend server"
until cd D:\Binh\my_project\app\backend\server
do
    echo "Waiting for server volume..."
done
until D:\Binh\my_project\app\backend\server\manage.py migrate
do
    echo "Waiting for database to be ready..."
    sleep 2
done
D:\Binh\my_project\app\backend\server\manage.py collectstatic --noinput
gunicorn server.wsgi --bind 0.0.0.0:8000 --workers 4 --threads 4
