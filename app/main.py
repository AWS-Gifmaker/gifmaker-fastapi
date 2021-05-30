import uvicorn

from fastapi import FastAPI
from mangum import Mangum

import uuid

import boto3

from app.constants import (
    REGION,
    VIDEO_BUCKET,
    RAW_VIDEOS_DIR,
    READ_CAPACITY_UNITS,
    WRITE_CAPACITY_UNITS,
)
from app.models import Gif, GifCreateModel

app = FastAPI()


@app.get("/")
def read_root():
    return ""


@app.post("/gifs/create")
def create_gif(gif_data: GifCreateModel):
    # create DynamoDB entry
    hash_key = str(uuid.uuid4())
    image_url = f"https://{RAW_VIDEOS_DIR}.s3.{REGION}.amazonaws.com/{RAW_VIDEOS_DIR}/{hash_key}"
    if not Gif.exists():
        Gif.create_table(
            read_capacity_units=READ_CAPACITY_UNITS,
            write_capacity_units=WRITE_CAPACITY_UNITS,
        )
    gif = Gif(
        key=hash_key,
        image_url=image_url,
        name=gif_data.name,
    )
    gif.save()

    # upload file to S3
    s3 = boto3.resource("s3")
    s3.Bucket(VIDEO_BUCKET).put_object(
        Key=f"{RAW_VIDEOS_DIR}/{hash_key}",
        Body=gif_data.image_file,
    )

    return {"id": hash_key, "name": gif.name, "image_url": image_url}


@app.get("/gifs")
def get_gif(key: str = None, name: str = None, tags: str = None):
    if key:
        gifs = Gif.query(key)
    elif name:
        gifs = Gif.name_index.query(name)
    elif tags:
        tags = tags.split(",")
        gifs = []
    else:
        gifs = []
    return {"gifs": [gif.serialize() for gif in gifs]}


handler = Mangum(app=app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
