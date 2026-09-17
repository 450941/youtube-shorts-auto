import os
import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


CLIENT_ID = os.environ["YOUTUBE_CLIENT_ID"]
CLIENT_SECRET = os.environ["YOUTUBE_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["YOUTUBE_REFRESH_TOKEN"]

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]


def main():
    info_path = "output/video_info.json"

    with open(
        info_path,
        "r",
        encoding="utf-8"
    ) as f:
        info = json.load(f)

    title = info["title"]

    description = (
        "身近なのに意外と知らない雑学を10個紹介します。\n"
        "「なんで？」と思う身近な疑問を、短く分かりやすく紹介しています。\n\n"
        "#雑学 #豆知識 #面白い話 #心理学 #YouTube"
    )

    credentials = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES
    )

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "categoryId": "27",
            "tags": [
                "雑学",
                "豆知識",
                "面白い話",
                "心理学",
                "身近な雑学"
            ]
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        "output/final_video.mp4",
        mimetype="video/mp4",
        resumable=True
    )

    print("Uploading:", title)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None

    while response is None:
        status, response = request.next_chunk()

        if status:
            print(
                "Upload progress:",
                int(status.progress() * 100),
                "%"
            )

    video_id = response["id"]

    print("Uploaded successfully")
    print("Video ID:", video_id)

    thumbnail = "output/thumbnail.jpg"

    if os.path.exists(thumbnail):
        print("Uploading thumbnail...")

        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(
                thumbnail,
                mimetype="image/jpeg"
            )
        ).execute()

        print("Thumbnail uploaded")

    with open(
        "output/video_info.json",
        "w",
        encoding="utf-8"
    ) as f:
        info["youtube_video_id"] = video_id
        info["youtube_url"] = (
            "https://youtu.be/" + video_id
        )

        json.dump(
            info,
            f,
            ensure_ascii=False,
            indent=2
        )


if __name__ == "__main__":
    main()
