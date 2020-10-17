import logging
import boto3
from app import app
from botocore.exceptions import ClientError


def upload_file(file, file_name: str):
    print(app.config['AWS_ACCESS_KEY_ID'])
    print(app.config['AWS_SECRET_ACCESS_KEY'])
    print(app.config['FLASKS3_BUCKET_NAME'])
    data = file.read()
    s3_client = boto3.client(service_name='s3', region_name='ap-northeast-1',
                             aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
                             aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'])
    s3_client.put_object(Key=file_name, Body=data, Bucket=app.config['FLASKS3_BUCKET_NAME'])


def get_link(file_name: str, expiration: int = 3600):
    s3_client = boto3.client(service_name='s3', region_name='ap-northeast-1',
                             aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
                             aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'])
    response = s3_client.generate_presigned_url('get_object',
                                                Params={'Bucket': app.config['FLASKS3_BUCKET_NAME'], 'Key': file_name},
                                                ExpiresIn=expiration)
    return response


def delete_file(file_name: str):
    s3_client = boto3.client(service_name='s3', region_name='ap-northeast-1',
                             aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
                             aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'])
    s3_client.Object(app.config['FLASKS3_BUCKET_NAME'], file_name).delete()


def list_files():
    s3 = boto3.client('s3')
    contents = []
    try:
        for item in s3.list_objects(Bucket=app.config['FLASKS3_BUCKET_NAME'])['Contents']:
            print(item)
            contents.append(item)
    except Exception as e:
        pass
    return contents