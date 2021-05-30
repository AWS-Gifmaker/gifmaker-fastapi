import boto3

from app.constants import GIF_TABLE


def get_object_url(bucket: str, key: str) -> str:
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket)
    location = boto3.client("s3").get_bucket_location(Bucket=bucket)[
        "LocationConstraint"
    ]
    return "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, key)


def put_item(id: str, name: str, image_url: str):
    dynamodb = boto3.client("dynamodb")
    return dynamodb.put_item(
        TableName=GIF_TABLE,
        Item={
            'id': {
                'S': id,
            },
            'name': {
                'S': name,
            },
            'image_url': {
                'S': image_url,
            },
        }
    )
