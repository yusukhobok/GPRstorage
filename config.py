import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    # ACL = 'public-read'
    FLASKS3_BUCKET_NAME = os.environ.get('FLASKS3_BUCKET_NAME')
    # FLASKS3_REGION = os.environ.get('FLASKS3_REGION')


class ProductionConfig(Config):
    DEBUG = False
    FLASKS3_BUCKET_NAME = "gprstorage"
    UPLOAD_FOLDER = '/tmp/'


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    FLASKS3_BUCKET_NAME = "gprstorage"
    UPLOAD_FOLDER = '/tmp/'


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    FLASKS3_BUCKET_NAME = "gprstorage-local"
    UPLOAD_FOLDER = 'tmp/'


class TestingConfig(Config):
    TESTING = True