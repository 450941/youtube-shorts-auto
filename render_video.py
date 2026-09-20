# ============================================================
# LONG VIDEO GENERATOR
# 5-MINUTE / 15 TOPICS / FAST PACING
# HISTORY SYSTEM
#
# ・雑学の重複防止
# ・サムネ画像の重複防止
# ・サムネレイアウト変更
# ・概要欄15パターン
# ・タイトル重複防止
# ・GitHub Actionsで履歴を保存
# ============================================================

import os
import sys
import json
import time
import random
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps


# ============================================================
# BASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

TRIVIA_FILE = BASE_DIR / "trivia.json"

MEDIA_DIR = BASE_DIR / "media"
IMAGE_DIR = MEDIA_DIR / "images"
VOICE_DIR = MEDIA_DIR / "voice"
CUTS_DIR = MEDIA_DIR / "cuts"
SUBTITLE_DIR = MEDIA_DIR / "subtitles"

OUTPUT_DIR = BASE_DIR / "output"

HISTORY_DIR = BASE_DIR / "history"

USED_TRIVIA_FILE = HISTORY_DIR / "used_trivia.json"
USED_THUMBNAILS_FILE = HISTORY_DIR / "used_thumbnails.json"
DESCRIPTION_HISTORY_FILE = HISTORY_DIR / "description_history.json"
TITLE_HISTORY_FILE = HISTORY_DIR / "title_history.json"
THUMBNAIL_STYLE_HISTORY_FILE = HISTORY_DIR / "thumbnail_style_history.json"


# ============================================================
# SETTINGS
# ============================================================

TOPICS_PER_VIDEO = 15
TARGET_DURATION = 300

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

VOICE = "ja-JP-NanamiNeural"
VOICE_RATE = "+2%"

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()

JST = timezone(timedelta(hours=9))


# ============================================================
# DIRECTORIES
# ============================================================

for directory in [
    MEDIA_DIR,
    IMAGE_DIR,
    VOICE_DIR,
    CUTS_DIR,
    SUBTITLE_DIR,
    OUTPUT_DIR,
    HISTORY_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOG
# ============================================================

def log(message):
    print(f"[LONG VIDEO] {message}", flush=True)


# ============================================================
# COMMAND
# ============================================================

def run_command(command, check=True):
    log("COMMAND:")
    log(" ".join(str(x) for x in command))

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    print(result.stdout, flush=True)

    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}"
        )

    return result


# ============================================================
# JSON
# ============================================================

def load_json(path, default):
    path = Path(path)

    if not path.exists():
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"WARNING: JSON読み込み失敗: {path}")
        log(str(e))
        return default


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp = path.with_suffix(path.suffix + ".tmp")

    with open(temp, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    temp.replace(path)


# ============================================================
# HISTORY
# ============================================================

def load_history(path):
    data = load_json(path, [])

    if not isinstance(data, list):
        return []

    return data


def save_history(path, data, max_items=None):
    if max_items is not None:
        data = data[-max_items:]

    save_json(path, data)


# ============================================================
# TRIVIA DATABASE
# ============================================================

def make_trivia_id(item, index):
    """
    trivia.jsonにidがなくても、
    内容から安定したIDを作る。
    """

    if isinstance(item, dict):
        if item.get("id") is not None:
            return str(item["id"])

        text_parts = [
            str(item.get("title", "")),
            str(item.get("fact", "")),
            str(item.get("text", "")),
            str(item.get("description", "")),
        ]

        raw = "|".join(text_parts)

    else:
        raw = str(item)

    if not raw.strip():
        raw = f"index-{index}"

    digest = hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:20]

    return f"trivia-{digest}"


def normalize_trivia(item, index):
    if isinstance(item, str):
        title = item.strip()
        fact = item.strip()
        category = "雑学"
        keyword = title

    elif isinstance(item, dict):

        title = str(
            item.get("title")
            or item.get("question")
            or item.get("name")
            or item.get("fact")
            or item.get("text")
            or "面白い雑学"
        ).strip()

        fact = str(
            item.get("fact")
            or item.get("text")
            or item.get("description")
            or item.get("answer")
            or title
        ).strip()

        category = str(
            item.get("category")
            or item.get("genre")
            or "雑学"
        ).strip()

        keyword = str(
            item.get("keyword")
            or item.get("search")
            or item.get("search_keyword")
            or title
        ).strip()

    else:
        title = str(item)
        fact = str(item)
        category = "雑学"
        keyword = title

    trivia_id = make_trivia_id(item, index)

    return {
        "id": trivia_id,
        "title": title,
        "fact": fact,
        "category": category,
        "keyword": keyword,
    }


def load_trivia_database():
    log("========================================")
    log("LOAD TRIVIA DATABASE")
    log("========================================")

    if not TRIVIA_FILE.exists():
        raise FileNotFoundError(
            f"trivia.json がありません: {TRIVIA_FILE}"
        )

    data = load_json(TRIVIA_FILE, [])

    if not isinstance(data, list):
        raise RuntimeError(
            "trivia.json の形式が配列ではありません。"
        )

    database = []

    for index, item in enumerate(data):
        try:
            normalized = normalize_trivia(item, index)

            if normalized["fact"].strip():
                database.append(normalized)

        except Exception as e:
            log(
                f"WARNING: trivia #{index} "
                f"を読み込めませんでした: {e}"
            )

    log(f"trivia.json 読み込み: {len(database)}件")

    if len(database) < TOPICS_PER_VIDEO:
        raise RuntimeError(
            f"雑学が{TOPICS_PER_VIDEO}件未満です。"
        )

    return database


# ============================================================
# RUN SLOT
# ============================================================

def get_run_slot():
    now = datetime.now(JST)

    if now.hour < 15:
        slot = "noon"
    else:
        slot = "evening"

    return now.strftime("%Y-%m-%d"), slot


# ============================================================
# SELECT TOPICS
# ============================================================

def select_topics(database):
    """
    過去に使った雑学を避けて15件選択。

    1000件の場合、
    15件 × 約66回で一巡。

    最後に10件だけ残った場合は、
    残り10件 + 過去の雑学5件で15件にする。
    """

    used_ids = set(
        str(x)
        for x in load_history(USED_TRIVIA_FILE)
    )

    database_by_id = {
        item["id"]: item
        for item in database
    }

    available = [
        item
        for item in database
        if item["id"] not in used_ids
    ]

    date_string, slot = get_run_slot()

    seed_text = (
        f"LUMI-LONG-{date_string}-"
        f"{slot}-{len(used_ids)}"
    )

    seed = int(
        hashlib.sha256(
            seed_text.encode("utf-8")
        ).hexdigest()[:16],
        16,
    )

    rng = random.Random(seed)

    log(f"現在の使用済み雑学: {len(used_ids)}件")
    log(f"今回使用可能な雑学: {len(available)}件")

    # --------------------------------------------------------
    # 通常
    # --------------------------------------------------------

    if len(available) >= TOPICS_PER_VIDEO:

        shuffled = available[:]
        rng.shuffle(shuffled)

        # カテゴリーをなるべく分散
        selected = []
        category_counts = {}

        for item in shuffled:

            category = item["category"]

            count = category_counts.get(category, 0)

            if count >= 3:
                continue

            selected.append(item)
            category_counts[category] = count + 1

            if len(selected) >= TOPICS_PER_VIDEO:
                break

        # 足りない場合
        if len(selected) < TOPICS_PER_VIDEO:

            selected_ids = {
                x["id"]
                for x in selected
            }

            for item in shuffled:

                if item["id"] in selected_ids:
                    continue

                selected.append(item)

                if len(selected) >= TOPICS_PER_VIDEO:
                    break

    # --------------------------------------------------------
    # 一巡直前
    # --------------------------------------------------------

    else:

        log(
            "WARNING: 未使用雑学が15件未満です。"
        )

        selected = available[:]

        selected_ids = {
            x["id"]
            for x in selected
        }

        old_items = [
            item
            for item in database
            if item["id"] not in selected_ids
        ]

        rng.shuffle(old_items)

        need = TOPICS_PER_VIDEO - len(selected)

        selected.extend(
            old_items[:need]
        )

        log(
            "雑学データベースを一巡します。"
        )

    if len(selected) != TOPICS_PER_VIDEO:
        raise RuntimeError(
            f"雑学選択数が15件ではありません: "
            f"{len(selected)}"
        )

    rng.shuffle(selected)

    log("今回の15雑学:")

    for i, item in enumerate(selected, 1):
        log(
            f"{i:02d}. "
            f"[{item['category']}] "
            f"{item['title']}"
        )

    return selected


# ============================================================
# TEXT
# ============================================================

def clean_text(text):
    if text is None:
        return ""

    text = str(text)

    replacements = {
        "\r": "",
        "\n": " ",
        "　": " ",
    }

    for a, b in replacements.items():
        text = text.replace(a, b)

    return " ".join(
        text.split()
    ).strip()


# ============================================================
# HOOKS
# ============================================================

HOOKS = [
    "実はこれ、知っていましたか？",
    "意外と知られていない話です。",
    "これを知ると少し見方が変わります。",
    "あなたはこの事実を知っていますか？",
    "身近なのに、意外と知らない雑学です。",
    "実は科学的にも面白いポイントがあります。",
    "多くの人が知らない、ちょっと意外な話です。",
    "これ、実はかなり不思議なんです。",
    "知っているようで知らない話を紹介します。",
    "今日誰かに話したくなる雑学です。",
]


ENDINGS = [
    "知っていると、ちょっと得した気分になりますね。",
    "こういう身近な雑学って面白いですよね。",
    "知らない世界を知ると、日常が少し楽しくなります。",
    "次にこれを見たとき、少し違って見えるかもしれません。",
    "あなたはいくつ知っていましたか？",
    "ぜひ誰かに教えてあげてください。",
    "まだまだ面白い雑学はたくさんあります。",
    "こういう小さな知識を楽しんでいきましょう。",
]


def make_script(topic, index):
    rng = random.Random(
        f"{topic['id']}-{index}"
    )

    hook = rng.choice(HOOKS)
    ending = rng.choice(ENDINGS)

    title = clean_text(topic["title"])
    fact = clean_text(topic["fact"])

    script = (
        f"{hook} "
        f"{title}。 "
        f"{fact}。 "
        f"{ending}"
    )

    return script


# ============================================================
# AUDIO
# ============================================================

def get_audio_duration(path):
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )

    return float(
        result.stdout.strip()
    )


def generate_tts(text, output_path):
    output_path = Path(output_path)

    run_command(
        [
            sys.executable,
            "-m",
            "edge_tts",
            "--voice",
            VOICE,
            "--rate",
            VOICE_RATE,
            "--text",
            text,
            "--write-media",
            str(output_path),
        ]
    )

    if not output_path.exists():
        raise RuntimeError(
            f"TTSファイルが作成されませんでした: "
            f"{output_path}"
        )

    return output_path


def seconds_to_srt_time(seconds):
    milliseconds = int(
        round(seconds * 1000)
    )

    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000

    minutes = milliseconds // 60_000
    milliseconds %= 60_000

    secs = milliseconds // 1000
    milliseconds %= 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{milliseconds:03d}"
    )


def write_srt(entries, path):
    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:

        for i, entry in enumerate(entries, 1):

            start = entry["start"]
            end = entry["end"]
            text = entry["text"]

            f.write(
                f"{i}\n"
                f"{seconds_to_srt_time(start)} --> "
                f"{seconds_to_srt_time(end)}\n"
                f"{text}\n\n"
            )


def create_voice_track(topics):
    log("========================================")
    log("CREATE VOICE")
    log("========================================")

    voice_files = []
    subtitles = []

    current_time = 0.0

    for index, topic in enumerate(
        topics,
        1,
    ):

        script = make_script(
            topic,
            index,
        )

        log(
            f"VOICE {index}/{len(topics)}: "
            f"{script[:80]}"
        )

        voice_path = (
            VOICE_DIR
            / f"voice_{index:02d}.mp3"
        )

        generate_tts(
            script,
            voice_path,
        )

        duration = get_audio_duration(
            voice_path
        )

        voice_files.append(
            voice_path
        )

        subtitles.append(
            {
                "start": current_time,
                "end": current_time + duration,
                "text": script,
            }
        )

        current_time += duration

    voice_list = (
        VOICE_DIR
        / "voice_list.txt"
    )

    with open(
        voice_list,
        "w",
        encoding="utf-8",
    ) as f:

        for voice_file in voice_files:
            f.write(
                f"file '{voice_file.resolve()}'\n"
            )

    combined_voice = (
        VOICE_DIR
        / "combined_voice.mp3"
    )

    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(voice_list),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(combined_voice),
        ]
    )

    subtitle_path = (
        SUBTITLE_DIR
        / "subtitles.srt"
    )

    write_srt(
        subtitles,
        subtitle_path,
    )

    duration = get_audio_duration(
        combined_voice
    )

    log(
        f"VOICE TOTAL: {duration:.2f} sec"
    )

    return (
        combined_voice,
        subtitle_path,
        duration,
    )


# ============================================================
# PEXELS
# ============================================================

def pexels_headers():
    if not PEXELS_API_KEY:
        raise RuntimeError(
            "PEXELS_API_KEY がありません。"
        )

    return {
        "Authorization": PEXELS_API_KEY
    }


def pexels_video_search(
    query,
    per_page=8,
):
    url = (
        "https://api.pexels.com/videos/search"
    )

    params = {
        "query": query,
        "per_page": per_page,
        "orientation": "landscape",
        "size": "medium",
    }

    response = requests.get(
        url,
        headers=pexels_headers(),
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json().get(
        "videos",
        [],
    )


def choose_video_file(video):
    files = video.get(
        "video_files",
        [],
    )

    candidates = []

    for file in files:

        width = file.get("width") or 0
        height = file.get("height") or 0
        link = file.get("link")

        if not link:
            continue

        if width < 640 or height < 360:
            continue

        candidates.append(
            (
                width * height,
                width,
                height,
                link,
            )
        )

    if not candidates:
        return None

    # 1080p付近を優先
    candidates.sort(
        key=lambda x: (
            abs(x[1] - 1920)
            + abs(x[2] - 1080),
            -x[0],
        )
    )

    return candidates[0][3]


def download_file(
    url,
    output_path,
):
    output_path = Path(output_path)

    response = requests.get(
        url,
        timeout=60,
        stream=True,
    )

    response.raise_for_status()

    with open(
        output_path,
        "wb",
    ) as f:

        for chunk in response.iter_content(
            chunk_size=1024 * 1024
        ):
            if chunk:
                f.write(chunk)

    if not output_path.exists():
        raise RuntimeError(
            f"ダウンロード失敗: {output_path}"
        )

    if output_path.stat().st_size < 10_000:
        raise RuntimeError(
            f"動画ファイルが小さすぎます: "
            f"{output_path}"
        )

    return output_path


# ============================================================
# VISUAL QUERIES
# ============================================================

def build_queries(topic):
    keyword = clean_text(
        topic["keyword"]
    )

    title = clean_text(
        topic["title"]
    )

    category = clean_text(
        topic["category"]
    )

    return [
        keyword,
        title,
        f"{keyword} lifestyle",
        f"{keyword} people",
        f"{category} lifestyle",
        "interesting everyday life",
    ]


def create_visual_cuts(
    topics,
):
    log("========================================")
    log("CREATE VISUAL CUTS")
    log("========================================")

    cuts = []

    global_used_video_ids = set()

    cut_index = 0

    for topic_index, topic in enumerate(
        topics,
        1,
    ):

        log(
            f"VISUAL {topic_index}/{len(topics)}: "
            f"{topic['title']}"
        )

        queries = build_queries(
            topic
        )

        selected_videos = []

        for query in queries:

            try:
                videos = pexels_video_search(
                    query,
                    per_page=8,
                )
            except Exception as e:
                log(
                    f"PEXELS検索失敗: "
                    f"{query} / {e}"
                )
                continue

            for video in videos:

                video_id = str(
                    video.get("id", "")
                )

                if not video_id:
                    continue

                if video_id in global_used_video_ids:
                    continue

                link = choose_video_file(
                    video
                )

                if not link:
                    continue

                selected_videos.append(
                    {
                        "id": video_id,
                        "link": link,
                    }
                )

                global_used_video_ids.add(
                    video_id
                )

                if len(selected_videos) >= 6:
                    break

            if len(selected_videos) >= 6:
                break

        for video in selected_videos:

            cut_index += 1

            output_path = (
                CUTS_DIR
                / f"cut_{cut_index:03d}.mp4"
            )

            try:
                download_file(
                    video["link"],
                    output_path,
                )
            except Exception as e:
                log(
                    f"動画DL失敗: {e}"
                )
                continue

            cuts.append(
                output_path
            )

    if not cuts:
        raise RuntimeError(
            "Pexelsから動画を取得できませんでした。"
        )

    log(
        f"VISUAL CUTS: {len(cuts)}"
    )

    return cuts


# ============================================================
# CONCAT VIDEO
# ============================================================

def concat_video(
    cut_files,
):
    concat_list = (
        CUTS_DIR
        / "concat.txt"
    )

    with open(
        concat_list,
        "w",
        encoding="utf-8",
    ) as f:

        for path in cut_files:
            f.write(
                f"file '{path.resolve()}'\n"
            )

    visual_track = (
        CUTS_DIR
        / "visual_track.mp4"
    )

    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            str(visual_track),
        ]
    )

    return visual_track


# ============================================================
# BGM
# ============================================================

def prepare_bgm(
    voice_duration,
):
    bgm_path = (
        MEDIA_DIR
        / "bgm.ogg"
    )

    if not bgm_path.exists():
        log(
            "BGMがありません。BGMなしで続行します。"
        )
        return None

    output = (
        MEDIA_DIR
        / "bgm_looped.m4a"
    )

    run_command(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(bgm_path),
            "-t",
            str(voice_duration),
            "-vn",
            "-af",
            "volume=0.035",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(output),
        ]
    )

    return output


# ============================================================
# FINAL VIDEO
# ============================================================

def render_final_video(
    visual_track,
    voice_track,
    subtitle_path,
    voice_duration,
):
    log("========================================")
    log("RENDER FINAL VIDEO")
    log("========================================")

    final_video = (
        OUTPUT_DIR
        / "final_video.mp4"
    )

    bgm = prepare_bgm(
        voice_duration
    )

    subtitle_filter = (
        f"subtitles="
        f"'{subtitle_path.resolve()}':"
        f"force_style="
        f"'FontName=Noto Sans CJK JP,"
        f"FontSize=22,"
        f"PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,"
        f"BorderStyle=1,"
        f"Outline=2,"
        f"Shadow=1,"
        f"Alignment=2,"
        f"MarginV=70'"
    )

    video_input = [
        "-stream_loop",
        "-1",
        "-i",
        str(visual_track),
    ]

    audio_inputs = [
        "-i",
        str(voice_track),
    ]

    command = [
        "ffmpeg",
        "-y",
    ]

    command.extend(video_input)
    command.extend(audio_inputs)

    if bgm:
        command.extend(
            [
                "-i",
                str(bgm),
            ]
        )

    command.extend(
        [
            "-filter_complex",
            (
                f"[0:v]"
                f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:"
                f"force_original_aspect_ratio=increase,"
                f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
                f"{subtitle_filter}"
                f"[v]"
            ),
            "-map",
            "[v]",
            "-map",
            "1:a",
        ]
    )

    if bgm:

        command.extend(
            [
                "-map",
                "2:a",
                "-filter_complex",
                (
                    f"[0:v]"
                    f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:"
                    f"force_original_aspect_ratio=increase,"
                    f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
                    f"{subtitle_filter}"
                    f"[v];"
                    f"[1:a]volume=1.0[voice];"
                    f"[2:a]volume=0.035[bgm];"
                    f"[voice][bgm]"
                    f"amix=inputs=2:"
                    f"duration=first:"
                    f"dropout_transition=2[a]"
                ),
                "-map",
                "[v]",
                "-map",
                "[a]",
            ]
        )

    command.extend(
        [
            "-t",
            str(voice_duration),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "21",
            "-r",
            str(FPS),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(final_video),
        ]
    )

    run_command(command)

    if not final_video.exists():
        raise RuntimeError(
            "final_video.mp4 が作成されませんでした。"
        )

    log(
        f"FINAL VIDEO: {final_video}"
    )

    return final_video


# ============================================================
# THUMBNAIL PEXELS
# ============================================================

def pexels_photo_search(
    query,
    per_page=20,
):
    url = (
        "https://api.pexels.com/v1/search"
    )

    params = {
        "query": query,
        "per_page": per_page,
        "orientation": "landscape",
    }

    response = requests.get(
        url,
        headers=pexels_headers(),
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json().get(
        "photos",
        [],
    )


def download_thumbnail_photo(
    photo,
    output_path,
):
    src = photo.get(
        "src",
        {}
    )

    url = (
        src.get("large2x")
        or src.get("large")
        or src.get("original")
    )

    if not url:
        return False

    response = requests.get(
        url,
        timeout=60,
    )

    response.raise_for_status()

    with open(
        output_path,
        "wb",
    ) as f:
        f.write(
            response.content
        )

    return True


# ============================================================
# THUMBNAIL FONT
# ============================================================

def find_font(size):
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.otf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(
                    path,
                    size,
                )
            except Exception:
                pass

    return ImageFont.load_default()


# ============================================================
# THUMBNAIL STYLE
# ============================================================

THUMBNAIL_STYLES = [
    "left_title",
    "center_box",
    "big_number",
    "top_title",
    "bottom_bar",
    "split_layout",
]


def create_thumbnail(
    topic,
):
    log("========================================")
    log("CREATE THUMBNAIL")
    log("========================================")

    used_ids = set(
        str(x)
        for x in load_history(
            USED_THUMBNAILS_FILE
        )
    )

    queries = [
        clean_text(topic["keyword"]),
        clean_text(topic["title"]),
        f"{clean_text(topic['keyword'])} people",
        f"{clean_text(topic['keyword'])} surprised",
        "interesting lifestyle",
        "curious person",
        "science discovery",
        "everyday life",
    ]

    selected_photo = None

    for query in queries:

        try:
            photos = pexels_photo_search(
                query,
                per_page=20,
            )
        except Exception as e:
            log(
                f"サムネ検索失敗: "
                f"{query} / {e}"
            )
            continue

        candidates = []

        for photo in photos:

            photo_id = str(
                photo.get("id", "")
            )

            if not photo_id:
                continue

            if photo_id in used_ids:
                continue

            candidates.append(
                photo
            )

        if candidates:
            selected_photo = random.choice(
                candidates
            )
            break

    # --------------------------------------------------------
    # 全候補が使用済みだった場合
    # --------------------------------------------------------

    if selected_photo is None:

        log(
            "WARNING: 未使用サムネが見つかりません。"
        )

        for query in queries:

            try:
                photos = pexels_photo_search(
                    query,
                    per_page=20,
                )
            except Exception:
                continue

            if photos:
                selected_photo = random.choice(
                    photos
                )
                break

    if selected_photo is None:
        raise RuntimeError(
            "サムネイル画像を取得できませんでした。"
        )

    photo_id = str(
        selected_photo.get("id")
    )

    raw_thumbnail = (
        MEDIA_DIR
        / "thumbnail_source.jpg"
    )

    download_thumbnail_photo(
        selected_photo,
        raw_thumbnail,
    )

    image = Image.open(
        raw_thumbnail
    ).convert("RGB")

    image = ImageOps.fit(
        image,
        (1280, 720),
        method=Image.Resampling.LANCZOS,
    )

    # --------------------------------------------------------
    # STYLE
    # --------------------------------------------------------

    style_history = [
        int(x)
        for x in load_history(
            THUMBNAIL_STYLE_HISTORY_FILE
        )
        if str(x).isdigit()
    ]

    available_styles = [
        i
        for i in range(
            len(THUMBNAIL_STYLES)
        )
        if i not in style_history
    ]

    if not available_styles:
        available_styles = list(
            range(
                len(THUMBNAIL_STYLES)
            )
        )

    style_index = random.choice(
        available_styles
    )

    style_name = THUMBNAIL_STYLES[
        style_index
    ]

    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    title = clean_text(
        topic["title"]
    )

    if len(title) > 28:
        title = title[:28] + "…"

    title_font = find_font(52)
    small_font = find_font(34)
    number_font = find_font(110)

    # --------------------------------------------------------
    # 共通暗幕
    # --------------------------------------------------------

    if style_name == "left_title":

        draw.rectangle(
            (0, 0, 620, 720),
            fill=(0, 0, 0, 155),
        )

        draw.rounded_rectangle(
            (45, 45, 260, 115),
            radius=20,
            fill=(255, 80, 80, 235),
        )

        draw.text(
            (75, 62),
            "15選",
            font=small_font,
            fill=(255, 255, 255, 255),
        )

        draw.multiline_text(
            (55, 190),
            title,
            font=title_font,
            fill=(255, 255, 255, 255),
            spacing=12,
            stroke_width=2,
            stroke_fill=(0, 0, 0, 220),
        )

        draw.text(
            (55, 620),
            "知らないとちょっと驚く雑学",
            font=small_font,
            fill=(255, 255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 220),
        )

    elif style_name == "center_box":

        draw.rectangle(
            (0, 0, 1280, 720),
            fill=(0, 0, 0, 70),
        )

        draw.rounded_rectangle(
            (100, 175, 1180, 545),
            radius=35,
            fill=(0, 0, 0, 185),
            outline=(255, 255, 255, 190),
            width=4,
        )

        draw.text(
            (470, 215),
            "15選",
            font=small_font,
            fill=(255, 230, 100, 255),
        )

        bbox = draw.multiline_textbbox(
            (0, 0),
            title,
            font=title_font,
            spacing=10,
        )

        text_width = (
            bbox[2] - bbox[0]
        )

        x = max(
            60,
            (1280 - text_width) // 2,
        )

        draw.multiline_text(
            (x, 290),
            title,
            font=title_font,
            fill=(255, 255, 255, 255),
            spacing=10,
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255),
        )

    elif style_name == "big_number":

        draw.rectangle(
            (0, 0, 440, 720),
            fill=(0, 0, 0, 165),
        )

        draw.text(
            (50, 80),
            "15",
            font=number_font,
            fill=(255, 230, 80, 255),
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255),
        )

        draw.text(
            (65, 205),
            "選",
            font=title_font,
            fill=(255, 255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255),
        )

        draw.multiline_text(
            (500, 230),
            title,
            font=title_font,
            fill=(255, 255, 255, 255),
            spacing=12,
            stroke_width=3,
            stroke_fill=(0, 0, 0, 230),
        )

        draw.text(
            (500, 600),
            "知ってる？",
            font=small_font,
            fill=(255, 255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255),
        )

    elif style_name == "top_title":

        draw.rectangle(
            (0, 0, 1280, 210),
            fill=(0, 0, 0, 185),
        )

        draw.rounded_rectangle(
            (45, 45, 220, 120),
            radius=18,
            fill=(255, 90, 90, 235),
        )

        draw.text(
            (78, 62),
            "15選",
            font=small_font,
            fill=(255, 255, 255, 255),
        )

        draw.multiline_text(
            (270, 45),
            title,
            font=title_font,
            fill=(255, 255, 255, 255),
            spacing=8,
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255),
        )

        draw.rectangle(
            (0, 610, 1280, 720),
            fill=(0, 0, 0, 165),
        )

        draw.text(
            (50, 645),
            "今日誰かに話したくなる雑学",
            font=small_font,
            fill=(255, 255, 255, 255),
        )

    elif style_name == "bottom_bar":

        draw.rectangle(
            (0, 500, 1280, 720),
            fill=(0, 0, 0, 185),
        )

        draw.text(
            (50, 530),
            title,
            font=title_font,
            fill=(255, 255, 255, 255),
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255),
        )

        draw.rounded_rectangle(
            (50, 620, 220, 685),
            radius=15,
            fill=(255, 100, 80, 240),
        )

        draw.text(
            (82, 635),
            "15選",
            font=small_font,
            fill=(255, 255, 255, 255),
        )

    elif style_name == "split_layout":

        draw.rectangle(
            (0, 0, 640, 720),
            fill=(0, 0, 0, 150),
        )

        draw.rectangle(
            (0, 0, 1280, 18),
            fill=(255, 220, 80, 255),
        )

        draw.text(
            (55, 80),
            "15選",
            font=small_font,
            fill=(255, 220, 80, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255),
        )

        draw.multiline_text(
            (55, 170),
            title,
            font=title_font,
            fill=(255, 255, 255, 255),
            spacing=12,
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255),
        )

        draw.rounded_rectangle(
            (55, 580, 580, 670),
            radius=20,
            fill=(0, 0, 0, 180),
        )

        draw.text(
            (85, 605),
            "知らないと損するかも？",
            font=small_font,
            fill=(255, 255, 255, 255),
        )

    thumbnail_path = (
        OUTPUT_DIR
        / "thumbnail.jpg"
    )

    image.save(
        thumbnail_path,
        "JPEG",
        quality=95,
    )

    log(
        f"THUMBNAIL PHOTO ID: {photo_id}"
    )

    log(
        f"THUMBNAIL STYLE: "
        f"{style_index} / {style_name}"
    )

    return (
        thumbnail_path,
        photo_id,
        style_index,
    )


# ============================================================
# TITLE
# ============================================================

TITLE_PATTERNS = [
    "【雑学15選】{}を知っていますか？意外と知らない面白い話",
    "【知らないと損】{}にまつわる驚きの雑学15選",
    "【雑学】実は知られていない{}の秘密15選",
    "【衝撃の事実】{}について知っておきたい雑学15選",
    "【面白い雑学15選】{}の意外な真実",
    "【知ってた？】{}から分かる意外な雑学15選",
    "【今日の雑学】{}がちょっと面白くなる15の話",
    "【驚き】身近な{}に隠された雑学15選",
]


def create_title(topics):
    history = [
        str(x)
        for x in load_history(
            TITLE_HISTORY_FILE
        )
    ]

    first_topic = topics[0]

    keyword = clean_text(
        first_topic["keyword"]
    )

    title_candidates = []

    for pattern in TITLE_PATTERNS:
        title_candidates.append(
            pattern.format(keyword)
        )

    # さらに複数候補
    for topic in topics[:5]:

        key = clean_text(
            topic["keyword"]
        )

        title_candidates.extend(
            [
                f"【雑学15選】{key}の意外な事実を紹介",
                f"【驚き】{key}について知っておきたい話15選",
            ]
        )

    random.shuffle(
        title_candidates
    )

    selected = None

    for candidate in title_candidates:

        if candidate not in history:
            selected = candidate
            break

    if selected is None:
        selected = title_candidates[0]

    # パターンを記録するのはmainの最後
    return selected


# ============================================================
# DESCRIPTION 15 PATTERNS
# ============================================================

DESCRIPTION_TEMPLATES = [
    (
        "今回は、知っているようで意外と知らない雑学を15個紹介します。"
        "身近なことから思わず誰かに話したくなる話まで、テンポよくまとめました。"
    ),
    (
        "あなたはいくつ知っていますか？"
        "今回は、日常生活で役立つかもしれない面白い雑学を15個集めました。"
    ),
    (
        "ちょっとした知識が増えると、いつもの日常が少し違って見えることがあります。"
        "今回はそんな面白い雑学を15個紹介します。"
    ),
    (
        "今回の動画では、思わず『へぇ！』と言いたくなる雑学を15個紹介します。"
        "最後まで気軽に楽しんでいってください。"
    ),
    (
        "身近なのに知らなかった。"
        "そんな発見につながる雑学を15個ピックアップしました。"
        "知っているものがいくつあるかもチェックしてみてください。"
    ),
    (
        "今日誰かに話したくなるような雑学を15個まとめました。"
        "短時間で楽しめるので、ぜひ最後まで見てみてください。"
    ),
    (
        "世の中には、意外と知られていない面白い事実がたくさんあります。"
        "今回はその中から15個を厳選して紹介します。"
    ),
    (
        "『これ本当なの？』と思ってしまうような面白い雑学を15個紹介します。"
        "知識として楽しみながらご覧ください。"
    ),
    (
        "普段何気なく見ているものにも、意外な秘密が隠れているかもしれません。"
        "今回はそんな身近な雑学を15個紹介します。"
    ),
    (
        "知っていると少し得した気分になる雑学を集めました。"
        "今回は15個の面白い話をテンポよく紹介していきます。"
    ),
    (
        "雑学が好きな人はもちろん、ちょっとした暇つぶしにもおすすめです。"
        "今回は面白い雑学を15個まとめました。"
    ),
    (
        "あなたの日常に新しい『へぇ』を。"
        "今回は、意外と知らない面白い雑学を15個紹介します。"
    ),
    (
        "知らなくても困らないけれど、知るとちょっと面白い。"
        "そんな雑学を15個集めてみました。"
    ),
    (
        "今回は、日常・科学・心理など、さまざまなジャンルから雑学を15個紹介します。"
        "気になった話があればぜひ覚えておいてください。"
    ),
    (
        "最後まで見ると、誰かに話したくなる知識が一つくらい見つかるかもしれません。"
        "今回はそんな雑学を15個紹介します。"
    ),
]


def create_description(topics):
    history = [
        int(x)
        for x in load_history(
            DESCRIPTION_HISTORY_FILE
        )
        if str(x).isdigit()
    ]

    available = [
        i
        for i in range(
            len(DESCRIPTION_TEMPLATES)
        )
        if i not in history
    ]

    if not available:
        available = list(
            range(
                len(DESCRIPTION_TEMPLATES)
            )
        )

    template_index = random.choice(
        available
    )

    intro = DESCRIPTION_TEMPLATES[
        template_index
    ]

    topic_lines = []

    for index, topic in enumerate(
        topics,
        1,
    ):
        topic_lines.append(
            f"{index}. {topic['title']}"
        )

    description = (
        f"{intro}\n\n"
        "【今回紹介する雑学】\n"
        + "\n".join(topic_lines)
        + "\n\n"
        "このチャンネルでは、"
        "雑学・心理・日常の不思議など、"
        "知るとちょっと面白い情報を紹介しています。\n"
        "気に入ったらチャンネル登録・高評価をお願いします！\n\n"
        "#雑学 #豆知識 #面白い話 #知識 #トリビア"
    )

    return (
        description,
        template_index,
    )


# ============================================================
# VIDEO INFO
# ============================================================

def create_video_info(
    title,
    description,
    topics,
    thumbnail_style,
):
    now = datetime.now(JST)

    return {
        "title": title,
        "description": description,
        "category": "27",
        "privacyStatus": "public",
        "madeForKids": False,
        "generatedAt": now.isoformat(),
        "topicCount": len(topics),
        "topics": [
            {
                "id": topic["id"],
                "title": topic["title"],
                "category": topic["category"],
            }
            for topic in topics
        ],
        "thumbnailStyle": thumbnail_style,
    }


# ============================================================
# MANIFEST
# ============================================================

def create_manifest(
    topics,
    title,
    description_template,
    thumbnail_id,
    thumbnail_style,
):
    return {
        "generatedAt": datetime.now(
            JST
        ).isoformat(),
        "title": title,
        "descriptionTemplate": description_template,
        "thumbnail": {
            "pexelsPhotoId": thumbnail_id,
            "style": thumbnail_style,
            "styleName": THUMBNAIL_STYLES[
                thumbnail_style
            ],
        },
        "topics": [
            {
                "id": topic["id"],
                "title": topic["title"],
                "category": topic["category"],
            }
            for topic in topics
        ],
    }


# ============================================================
# SAVE HISTORY
# ============================================================

def save_generation_history(
    topics,
    title,
    description_template,
    thumbnail_id,
    thumbnail_style,
):
    log("========================================")
    log("SAVE GENERATION HISTORY")
    log("========================================")

    # --------------------------------------------------------
    # Trivia
    # --------------------------------------------------------

    used_trivia = load_history(
        USED_TRIVIA_FILE
    )

    used_trivia_set = set(
        str(x)
        for x in used_trivia
    )

    for topic in topics:
        if topic["id"] not in used_trivia_set:
            used_trivia.append(
                topic["id"]
            )
            used_trivia_set.add(
                topic["id"]
            )

    save_history(
        USED_TRIVIA_FILE,
        used_trivia,
    )

    # --------------------------------------------------------
    # Thumbnail
    # --------------------------------------------------------

    used_thumbnails = load_history(
        USED_THUMBNAILS_FILE
    )

    if str(thumbnail_id) not in {
        str(x)
        for x in used_thumbnails
    }:
        used_thumbnails.append(
            str(thumbnail_id)
        )

    save_history(
        USED_THUMBNAILS_FILE,
        used_thumbnails,
    )

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    description_history = load_history(
        DESCRIPTION_HISTORY_FILE
    )

    description_history.append(
        int(description_template)
    )

    save_history(
        DESCRIPTION_HISTORY_FILE,
        description_history,
        max_items=100,
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title_history = load_history(
        TITLE_HISTORY_FILE
    )

    title_history.append(
        title
    )

    save_history(
        TITLE_HISTORY_FILE,
        title_history,
        max_items=100,
    )

    # --------------------------------------------------------
    # Thumbnail style
    # --------------------------------------------------------

    style_history = load_history(
        THUMBNAIL_STYLE_HISTORY_FILE
    )

    style_history.append(
        int(thumbnail_style)
    )

    save_history(
        THUMBNAIL_STYLE_HISTORY_FILE,
        style_history,
        max_items=100,
    )

    log(
        f"使用済み雑学履歴: "
        f"{len(used_trivia)}件"
    )

    log(
        f"使用済みサムネ履歴: "
        f"{len(used_thumbnails)}件"
    )

    log(
        f"概要欄パターン: "
        f"{description_template + 1}/"
        f"{len(DESCRIPTION_TEMPLATES)}"
    )

    log(
        f"サムネスタイル: "
        f"{thumbnail_style + 1}/"
        f"{len(THUMBNAIL_STYLES)}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    start_time = time.time()

    log("========================================")
    log("LUMI LONG VIDEO GENERATOR")
    log("========================================")
    log("5分動画 / 15雑学")
    log("重複防止システム: ON")
    log("概要欄15パターン: ON")
    log("サムネ履歴: ON")
    log("タイトル履歴: ON")
    log("========================================")

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    if not PEXELS_API_KEY:
        raise RuntimeError(
            "PEXELS_API_KEY がありません"
        )

    # --------------------------------------------------------
    # Clean temporary folders
    # --------------------------------------------------------

    for directory in [
        IMAGE_DIR,
        VOICE_DIR,
        CUTS_DIR,
        SUBTITLE_DIR,
    ]:

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        for file in directory.iterdir():

            if file.is_file():
                try:
                    file.unlink()
                except Exception:
                    pass

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    database = load_trivia_database()

    # --------------------------------------------------------
    # Topics
    # --------------------------------------------------------

    topics = select_topics(
        database
    )

    # --------------------------------------------------------
    # Voice
    # --------------------------------------------------------

    (
        voice_track,
        subtitle_path,
        voice_duration,
    ) = create_voice_track(
        topics
    )

    # --------------------------------------------------------
    # Visual
    # --------------------------------------------------------

    cut_files = create_visual_cuts(
        topics
    )

    visual_track = concat_video(
        cut_files
    )

    # --------------------------------------------------------
    # Final video
    # --------------------------------------------------------

    final_video = render_final_video(
        visual_track,
        voice_track,
        subtitle_path,
        voice_duration,
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title = create_title(
        topics
    )

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    (
        description,
        description_template,
    ) = create_description(
        topics
    )

    # --------------------------------------------------------
    # Thumbnail
    # --------------------------------------------------------

    (
        thumbnail_path,
        thumbnail_id,
        thumbnail_style,
    ) = create_thumbnail(
        topics[0]
    )

    # --------------------------------------------------------
    # Video info
    # --------------------------------------------------------

    video_info = create_video_info(
        title,
        description,
        topics,
        thumbnail_style,
    )

    video_info_path = (
        OUTPUT_DIR
        / "video_info.json"
    )

    save_json(
        video_info_path,
        video_info,
    )

    # --------------------------------------------------------
    # Manifest
    # --------------------------------------------------------

    manifest = create_manifest(
        topics,
        title,
        description_template,
        thumbnail_id,
        thumbnail_style,
    )

    manifest_path = (
        OUTPUT_DIR
        / "manifest.json"
    )

    save_json(
        manifest_path,
        manifest,
    )

    # --------------------------------------------------------
    # title.txt
    # --------------------------------------------------------

    with open(
        OUTPUT_DIR / "title.txt",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(title)

    # --------------------------------------------------------
    # description.txt
    # --------------------------------------------------------

    with open(
        OUTPUT_DIR / "description.txt",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(description)

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    log("========================================")
    log("FINAL VALIDATION")
    log("========================================")

    required_files = [
        final_video,
        thumbnail_path,
        video_info_path,
        manifest_path,
    ]

    for path in required_files:

        if not Path(path).exists():
            raise RuntimeError(
                f"必要ファイルがありません: "
                f"{path}"
            )

        log(
            f"OK: {path}"
        )

    # --------------------------------------------------------
    # IMPORTANT:
    # History is saved only after the entire video
    # generation has successfully completed.
    # --------------------------------------------------------

    save_generation_history(
        topics,
        title,
        description_template,
        thumbnail_id,
        thumbnail_style,
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    elapsed = (
        time.time()
        - start_time
    )

    log("========================================")
    log("GENERATION COMPLETE")
    log("========================================")

    log(
        f"Video: {final_video}"
    )

    log(
        f"Thumbnail: {thumbnail_path}"
    )

    log(
        f"Title: {title}"
    )

    log(
        f"Description pattern: "
        f"{description_template + 1}/15"
    )

    log(
        f"Thumbnail style: "
        f"{THUMBNAIL_STYLES[thumbnail_style]}"
    )

    log(
        f"Voice duration: "
        f"{voice_duration:.2f} sec"
    )

    log(
        f"Elapsed: "
        f"{elapsed:.1f} sec"
    )

    log("========================================")


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":

    try:
        main()

    except Exception as e:

        log("========================================")
        log("GENERATION FAILED")
        log("========================================")

        log(
            f"{type(e).__name__}: {e}"
        )

        raise
