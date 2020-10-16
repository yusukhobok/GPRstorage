import boto3
from app import app


def upload_file(file, file_name):
    data = file.read()
    s3_client = boto3.client(service_name='s3', region_name='ap-northeast-1',
                             aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
                             aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'])
    s3_client.put_object(Key=file_name, Body=data, Bucket=app.config['FLASKS3_BUCKET_NAME'])


def download_file(file_name):
    s3 = boto3.resource('s3')
    output = f"/home/yuri/downloads/{file_name}"
    s3.Bucket(app.config['FLASKS3_BUCKET_NAME']).download_file(file_name, output)

    return output


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