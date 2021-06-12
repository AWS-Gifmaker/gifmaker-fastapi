import json

import uvicorn

from fastapi import FastAPI, HTTPException, UploadFile, File
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware

import uuid

import boto3

from constants import (
    REGION,
    VIDEO_BUCKET,
    RAW_VIDEOS_DIR,
    READ_CAPACITY_UNITS,
    WRITE_CAPACITY_UNITS, GIF_BUCKET, RANKING_LEN,
)
from models import Gif, TopResults

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return ""


@app.post("/gifs")
def create_gif(name: str, gif_file: UploadFile = File(...)):
    contents = gif_file.file.read()

    # create DynamoDB entry
    hash_key = str(uuid.uuid4())
    image_url = f"https://{GIF_BUCKET}.s3.{REGION}.amazonaws.com/{hash_key}.gif"
    # if not Gif.exists():
    #     Gif.create_table(
    #         read_capacity_units=READ_CAPACITY_UNITS,
    #         write_capacity_units=WRITE_CAPACITY_UNITS,
    #     )
    gif = Gif(
        key=hash_key,
        image_url=image_url,
        name=name,
        visits=0,
    )
    gif.save()

    # upload file to S3
    s3 = boto3.resource("s3")
    s3.Bucket(VIDEO_BUCKET).put_object(
        Key=f"{RAW_VIDEOS_DIR}/{hash_key}.mov",
        Body=contents,
    )

    return {"id": hash_key, "name": gif.name, "image_url": image_url}


@app.get("/gifs")
def list_gifs(key: str = None, name: str = None, tags: str = None):
    if key:
        gifs = Gif.query(key)
    elif name:
        gifs = Gif.name_index.query(name)
    elif tags:
        tags = tags.split(",")
        gifs = []
        for tag in tags:
            # convoluted list comprehension removes duplicates (repeating keys)
            gifs += [gif for gif in Gif.scan(Gif.tags.contains(tag)) if gif.key not in [gif.key for gif in gifs]]
    else:
        gifs = []

    gifs = [gif for gif in gifs if gif.ready]

    return {"gifs": [gif.serialize() for gif in gifs]}


def update_top_results(gif: Gif):
    # if not TopResults.exists():
    #     TopResults.create_table(
    #         read_capacity_units=READ_CAPACITY_UNITS,
    #         write_capacity_units=WRITE_CAPACITY_UNITS,
    #     )

    try:
        top_results = TopResults.get("overall")
    except TopResults.DoesNotExist:
        top_results = TopResults(key="overall")

    ranking = json.loads(top_results.ranking)

    if len(ranking) < RANKING_LEN or gif.visits > min([gif["visits"] for gif in ranking]):
        # avoid duplicating gif in ranking list
        if gif.key not in [x["key"] for x in ranking]:
            # ranking list not full, simply add current gif
            ranking.append({"key": gif.key, "visits": gif.visits})
            ranking = sorted(ranking, key=lambda x: x.get("visits", 0))[:RANKING_LEN]
            top_results.ranking = json.dumps(ranking)
            top_results.save()


@app.get("/gifs/{key}")
def get_gif(key: str):
    try:
        gif = Gif.get(key)
    except Gif.DoesNotExist:
        raise HTTPException(status_code=404, detail="Gif with given key not found")

    if not gif.ready:
        raise HTTPException(status_code=422, detail="Gif not ready")

    gif.visits += 1
    gif.save()

    update_top_results(gif)

    return gif.serialize()


handler = Mangum(app=app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
