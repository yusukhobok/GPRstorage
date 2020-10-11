# Project Setup
(https://realpython.com/flask-by-example-part-1-project-setup/)

## basic
* git init
* python3 -m venv env
* source env/bin/activate
---
* python -m pip install Flask autoenv psycopg2 Flask-SQLAlchemy Flask-Migrate
* python -m pip freeze > requirements.txt

python app.py

## heroku
* heroku create gprstorage-pro
* heroku create gprstorage-stage
---
* git remote add pro git@heroku.com:gprstorage-pro.git
* git remote add stage git@heroku.com:gprstorage-stage.git
* git push stage master
* git push pro master


## config settings

* pip install autoenv
* .env file:
    * source env/bin/activate
    * export APP_SETTINGS="config.DevelopmentConfig"
---
* echo "source `which activate.sh`" >> ~/.bashrc
* source ~/.bashrc


## heroku settings
* heroku config:set APP_SETTINGS=config.StagingConfig --remote stage
* heroku config:set APP_SETTINGS=config.ProductionConfig --remote pro
---
* heroku run python app.py --app gprstorage-stage
* heroku run python app.py --app gprstorage-pro


## postgresql
* SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
* export DATABASE_URL="postgresql://yuri:yurist@localhost:5432/gprstorage"
* postgresql://логин:пароль@хост:порт/база_данных
---
* heroku addons:create heroku-postgresql:hobby-dev --app gprstorage-stage
* heroku run python manage.py db upgrade --app gprstorage-stage
* heroku addons:create heroku-postgresql:hobby-dev --app gprstorage-pro
* heroku run python manage.py db upgrade --app gprstorage-pro


## curl
* curl -F "datafile=@/home/yuri/data/short.rdr" URL
* curl -X "POST" -d "name1=value1" -d "name2=value2" URL


## authentication
* pip install passlib
* curl -i -X POST -H "Content-Type: application/json" -d '{"username":"miguel","password":"python"}' http://127.0.0.1:5000/api/users
* curl -u miguel:python http://127.0.0.1:5000/projects