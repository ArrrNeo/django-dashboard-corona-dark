#!/bin/bash

python manage.py migrate --fake app zero
rm -rf app/migrations/000*
python manage.py makemigrations
rm db.sqlite3
python manage.py migrate
