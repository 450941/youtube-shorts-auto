# ============================================================
# LONG VIDEO GENERATOR
# 5-MINUTE / 15 TOPICS / FAST PACING
# 10,000+ TRIVIA DATABASE READY
# ============================================================

import os
import sys
import json
import time
import random
import hashlib
import subprocess
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ============================================================
# SETTINGS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

TRIVIA_FILE = BASE_DIR / "trivia.json"

MEDIA_DIR = BASE_DIR / "media"
VOICE_DIR = MEDIA_DIR / "voice"
CUTS_DIR = MEDIA_DIR / "cuts"
SUBTITLE_DIR = MEDIA_DIR / "subtitles"
IMAGE_DIR = MEDIA_DIR / "images"

OUTPUT_DIR = BASE_DIR / "output"

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "").strip()

TOPICS_PER_VIDEO = 15

TARGET_DURATION = 300

# 少し速め
VOICE = "ja-JP-NanamiNeural"
VOICE_RATE = "+2%"

# 映像切り替え間隔
MIN_CLIP_DURATION = 3.0
MAX_CLIP_DURATION = 4.2

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

FPS = 30

JST = timezone(timedelta(hours=9))


# ============================================================
# DIRECTORIES
# ============================================================

for directory in [
    MEDIA_DIR,
    VOICE_DIR,
    CUTS_DIR,
    SUBTITLE_DIR,
    IMAGE_DIR,
    OUTPUT_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOG
# ============================================================

def log(message):
    print(f"[LUMI-LONG] {message}", flush=True)


# ============================================================
# COMMAND
# ============================================================

def run_command(command, check=True):
    log("CMD: " + " ".join(str(x) for x in command))

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print(result.stdout, flush=True)

    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(map(str, command))}"
        )

    return result


# ============================================================
# JSON
# ============================================================

def load_json(path, default=None):

    if not path.exists():
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"JSON read error: {e}")
        return default


def save_json(path, data):

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# TRIVIA DATABASE
# ============================================================

def load_trivia_database():

    if not TRIVIA_FILE.exists():
        raise RuntimeError(
            "trivia.json がありません"
        )

    data = load_json(TRIVIA_FILE)

    if not isinstance(data, list):
        raise RuntimeError(
            "trivia.json は配列形式にしてください"
        )

    cleaned = []

    for index, item in enumerate(data):

        if not isinstance(item, dict):
            continue

        title = str(
            item.get("title")
            or item.get("question")
            or item.get("keyword")
            or f"雑学 {index + 1}"
        ).strip()

        category = str(
            item.get("category")
            or item.get("genre")
            or "雑学"
        ).strip()

        fact = str(
            item.get("fact")
            or item.get("text")
            or item.get("trivia")
            or item.get("description")
            or ""
        ).strip()

        example = str(
            item.get("example")
            or item.get("explanation")
            or ""
        ).strip()

        script = str(
            item.get("script")
            or ""
        ).strip()

        if not fact and not script:
            continue

        keyword = str(
            item.get("keyword")
            or title
        ).strip()

        cleaned.append({
            "id": str(
                item.get("id")
                or hashlib.sha256(
                    f"{index}-{title}-{fact}".encode(
                        "utf-8"
                    )
                ).hexdigest()[:16]
            ),
            "title": title,
            "category": category,
            "keyword": keyword,
            "fact": fact,
            "example": example,
            "script": script
        })

    if len(cleaned) < TOPICS_PER_VIDEO:
        raise RuntimeError(
            f"利用可能なネタが{len(cleaned)}件しかありません。"
            f"{TOPICS_PER_VIDEO}件以上必要です。"
        )

    log(
        f"Trivia database: {len(cleaned):,} topics"
    )

    return cleaned


# ============================================================
# DETERMINISTIC DAILY SELECTION
# ============================================================

def get_run_slot():

    now = datetime.now(JST)

    # 1日2本
    if now.hour < 12:
        slot = 0
    else:
        slot = 1

    return now.strftime("%Y-%m-%d"), slot


def select_topics(database):

    date_string, slot = get_run_slot()

    seed_text = f"LUMI-LONG-{date_string}-{slot}"

    seed = int(
        hashlib.sha256(
            seed_text.encode("utf-8")
        ).hexdigest()[:16],
        16
    )

    rng = random.Random(seed)

    # 全体をシャッフル
    pool = database.copy()

    rng.shuffle(pool)

    selected = []

    used_ids = set()

    # できるだけカテゴリーが偏らないようにする
    categories = {}

    for item in pool:

        cat = item["category"]

        categories.setdefault(
            cat,
            []
        ).append(item)

    category_list = list(categories.keys())

    rng.shuffle(category_list)

    # まずカテゴリーを散らす
    while len(selected) < TOPICS_PER_VIDEO:

        added = False

        for category in category_list:

            if not categories[category]:
                continue

            item = categories[category].pop()

            if item["id"] in used_ids:
                continue

            selected.append(item)
            used_ids.add(item["id"])

            added = True

            if len(selected) >= TOPICS_PER_VIDEO:
                break

        if not added:
            break

    # 足りなければ通常選択
    if len(selected) < TOPICS_PER_VIDEO:

        for item in pool:

            if item["id"] in used_ids:
                continue

            selected.append(item)
            used_ids.add(item)

            if len(selected) >= TOPICS_PER_VIDEO:
                break

    rng.shuffle(selected)

    log(
        f"Selected {len(selected)} topics "
        f"for {date_string} slot {slot}"
    )

    return selected


# ============================================================
# TEXT CLEANING
# ============================================================

BAD_PHRASES = [
    "ということがあります",
    "ということがあるんです",
    "かもしれません",
    "と言われています",
    "と言えるでしょう",
    "ではないでしょうか",
    "ご存じでしょうか",
    "知っているようで知らない",
    "これを知ると一歩進めます",
    "少し見方が変わります",
]


def clean_text(text):

    text = str(text)

    for phrase in BAD_PHRASES:
        text = text.replace(
            phrase,
            ""
        )

    replacements = {
        "実は、": "",
        "実は実は": "",
        "なんと、": "なんと",
        "驚くことに、": "驚くことに",
        "つまり、": "つまり",
        "です。です。": "です。",
        "。。": "。",
        "、、": "、",
    }

    for a, b in replacements.items():
        text = text.replace(a, b)

    return text.strip()


# ============================================================
# HOOKS
# ============================================================

HOOKS = [
    "ここ、意外と知られていません。",
    "これ、身近なのに理由を知ると面白いです。",
    "知らないままでも困らない。でも知ると見え方が変わります。",
    "これ、あなたの日常にもあります。",
    "一見普通ですが、裏にはちゃんと理由があります。",
    "これを知っていると、日常の見え方が少し変わります。",
    "この話、意外なところにつながります。",
    "思い当たる人、かなり多いはずです。",
    "これ、実際に毎日の生活で起きています。",
    "答えを知ると『なるほど』となる話です。",
]


# ============================================================
# SCRIPT
# ============================================================

def make_script(item, number):

    title = clean_text(item["title"])
    category = clean_text(item["category"])
    fact = clean_text(item["fact"])
    example = clean_text(item["example"])
    script = clean_text(item["script"])

    hook = random.choice(HOOKS)

    sentences = []

    sentences.append(
        f"{number}番。{hook}"
    )

    sentences.append(
        f"{title}。"
    )

    if script:

        sentences.append(
            script
        )

    else:

        sentences.append(
            fact
        )

        if example:

            sentences.append(
                example
            )

    # 短い締め
    endings = [
        "こう考えると、身近なことでもかなり面白く見えてきます。",
        "知らないだけで、毎日の中にはこうした現象がたくさんあります。",
        "こういう小さな知識が、意外と記憶に残ります。",
        "身近だからこそ、知ると面白いポイントです。",
        "こうして見ると、普段の生活も少し面白くなります。",
    ]

    sentences.append(
        random.choice(endings)
    )

    result = []

    for sentence in sentences:

        sentence = clean_text(sentence)

        if not sentence:
            continue

        result.append(sentence)

    return result


# ============================================================
# TTS
# ============================================================

def get_audio_duration(path):

    result = run_command([
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path)
    ])

    try:
        return float(
            result.stdout.strip()
        )
    except Exception:
        return 0.0


def generate_tts(text, output_path):

    import asyncio
    import edge_tts

    async def generate():

        communicate = edge_tts.Communicate(
            text=text,
            voice=VOICE,
            rate=VOICE_RATE
        )

        await communicate.save(
            str(output_path)
        )

    asyncio.run(generate())

    duration = get_audio_duration(
        output_path
    )

    if duration <= 0:
        raise RuntimeError(
            f"TTS duration取得失敗: {output_path}"
        )

    return duration


# ============================================================
# SRT
# ============================================================

def seconds_to_srt_time(seconds):

    milliseconds = int(
        round(seconds * 1000)
    )

    hours = milliseconds // 3600000
    milliseconds %= 3600000

    minutes = milliseconds // 60000
    milliseconds %= 60000

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
        encoding="utf-8"
    ) as f:

        for index, entry in enumerate(
            entries,
            start=1
        ):

            start = entry["start"]
            end = entry["end"]
            text = entry["text"]

            f.write(
                f"{index}\n"
            )

            f.write(
                f"{seconds_to_srt_time(start)} --> "
                f"{seconds_to_srt_time(end)}\n"
            )

            f.write(
                f"{text}\n\n"
            )


# ============================================================
# CREATE VOICE TRACK
# ============================================================

def create_voice_track(topics):

    all_audio = []
    subtitle_entries = []

    current_time = 0.0

    audio_index = 0

    for topic_number, topic in enumerate(
        topics,
        start=1
    ):

        sentences = make_script(
            topic,
            topic_number
        )

        log(
            f"VOICE TOPIC {topic_number}: "
            f"{topic['title']}"
        )

        for sentence in sentences:

            audio_index += 1

            audio_path = (
                VOICE_DIR /
                f"voice_{audio_index:04d}.mp3"
            )

            duration = generate_tts(
                sentence,
                audio_path
            )

            start = current_time
            end = current_time + duration

            subtitle_entries.append({
                "start": start,
                "end": end,
                "text": sentence
            })

            all_audio.append(
                audio_path
            )

            current_time = end

    concat_file = (
        VOICE_DIR /
        "voice_concat.txt"
    )

    with open(
        concat_file,
        "w",
        encoding="utf-8"
    ) as f:

        for audio in all_audio:

            f.write(
                f"file '{audio.resolve()}'\n"
            )

    voice_output = (
        VOICE_DIR /
        "voice_full.mp3"
    )

    run_command([
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c:a",
        "libmp3lame",
        "-b:a",
        "192k",
        str(voice_output)
    ])

    subtitle_path = (
        SUBTITLE_DIR /
        "captions.srt"
    )

    write_srt(
        subtitle_entries,
        subtitle_path
    )

    log(
        f"VOICE DURATION: {current_time:.2f}s"
    )

    return (
        voice_output,
        subtitle_path,
        current_time
    )


# ============================================================
# PEXELS SEARCH
# ============================================================

PEXELS_HEADERS = {}


def pexels_video_search(query, per_page=8):

    if not PEXELS_API_KEY:
        raise RuntimeError(
            "PEXELS_API_KEY がありません"
        )

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    url = (
        "https://api.pexels.com/videos/search"
    )

    params = {
        "query": query,
        "per_page": per_page,
        "orientation": "landscape"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "videos",
        []
    )


# ============================================================
# PEXELS DOWNLOAD
# ============================================================

def get_best_video_file(video):

    files = video.get(
        "video_files",
        []
    )

    candidates = []

    for file in files:

        width = file.get(
            "width",
            0
        )

        height = file.get(
            "height",
            0
        )

        link = file.get(
            "link"
        )

        if not link:
            continue

        if width < 1000:
            continue

        ratio = (
            width / height
            if height
            else 0
        )

        if ratio < 1.4:
            continue

        candidates.append(
            (
                width * height,
                link
            )
        )

    if not candidates:
        return None

    candidates.sort(
        reverse=True
    )

    return candidates[0][1]


def download_file(url, output):

    response = requests.get(
        url,
        stream=True,
        timeout=120
    )

    response.raise_for_status()

    with open(
        output,
        "wb"
    ) as f:

        for chunk in response.iter_content(
            chunk_size=1024 * 1024
        ):

            if chunk:
                f.write(chunk)

    return output


# ============================================================
# UNIQUE VISUAL QUERY
# ============================================================

def build_queries(topic):

    title = topic["title"]
    keyword = topic["keyword"]
    category = topic["category"]

    queries = [
        keyword,
        title,
        f"{keyword} lifestyle",
        f"{keyword} people",
        f"{keyword} daily life",
        f"{category} lifestyle"
    ]

    # 重複除去
    result = []

    for q in queries:

        q = str(q).strip()

        if q and q not in result:
            result.append(q)

    return result


# ============================================================
# CREATE VISUAL CUTS
# ============================================================

def create_visual_cuts(topics):

    used_video_ids = set()

    cuts = []

    global_cut_index = 0

    for topic_number, topic in enumerate(
        topics,
        start=1
    ):

        log(
            f"SEARCH VISUALS "
            f"{topic_number}/"
            f"{len(topics)}: "
            f"{topic['keyword']}"
        )

        queries = build_queries(
            topic
        )

        topic_videos = []

        for query in queries:

            try:

                videos = pexels_video_search(
                    query,
                    per_page=8
                )

            except Exception as e:

                log(
                    f"Pexels search error: {e}"
                )

                continue

            for video in videos:

                video_id = str(
                    video.get("id", "")
                )

                if not video_id:
                    continue

                if video_id in used_video_ids:
                    continue

                link = get_best_video_file(
                    video
                )

                if not link:
                    continue

                topic_videos.append({
                    "id": video_id,
                    "link": link
                })

                used_video_ids.add(
                    video_id
                )

                if len(topic_videos) >= 6:
                    break

            if len(topic_videos) >= 6:
                break

        # フォールバック
        if not topic_videos:

            fallback_queries = [
                "lifestyle",
                "people",
                "nature",
                "city",
                "daily life"
            ]

            for query in fallback_queries:

                try:

                    videos = pexels_video_search(
                        query,
                        per_page=8
                    )

                except Exception:
                    continue

                for video in videos:

                    video_id = str(
                        video.get("id", "")
                    )

                    if (
                        not video_id
                        or video_id in used_video_ids
                    ):
                        continue

                    link = get_best_video_file(
                        video
                    )

                    if not link:
                        continue

                    topic_videos.append({
                        "id": video_id,
                        "link": link
                    })

                    used_video_ids.add(
                        video_id
                    )

                    if len(topic_videos) >= 3:
                        break

                if topic_videos:
                    break

        if not topic_videos:
            log(
                "WARNING: visual not found"
            )
            continue

        # 1テーマ複数カット
        for video in topic_videos:

            global_cut_index += 1

            raw_path = (
                CUTS_DIR /
                f"raw_{global_cut_index:04d}.mp4"
            )

            final_path = (
                CUTS_DIR /
                f"cut_{global_cut_index:04d}.mp4"
            )

            try:

                download_file(
                    video["link"],
                    raw_path
                )

                duration = random.uniform(
                    MIN_CLIP_DURATION,
                    MAX_CLIP_DURATION
                )

                run_command([
                    "ffmpeg",
                    "-y",
                    "-stream_loop",
                    "-1",
                    "-i",
                    str(raw_path),
                    "-t",
                    f"{duration:.2f}",
                    "-vf",
                    (
                        f"scale={VIDEO_WIDTH}:"
                        f"{VIDEO_HEIGHT}:"
                        "force_original_aspect_ratio=increase,"
                        f"crop={VIDEO_WIDTH}:"
                        f"{VIDEO_HEIGHT}"
                    ),
                    "-r",
                    str(FPS),
                    "-an",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "23",
                    "-pix_fmt",
                    "yuv420p",
                    str(final_path)
                ])

                cuts.append(
                    final_path
                )

                try:
                    raw_path.unlink()
                except Exception:
                    pass

            except Exception as e:

                log(
                    f"Visual processing failed: {e}"
                )

    if not cuts:
        raise RuntimeError(
            "Pexels映像を1本も作成できませんでした"
        )

    return cuts


# ============================================================
# CONCAT VIDEO
# ============================================================

def concat_video(cuts):

    concat_file = (
        CUTS_DIR /
        "video_concat.txt"
    )

    with open(
        concat_file,
        "w",
        encoding="utf-8"
    ) as f:

        for cut in cuts:

            f.write(
                f"file '{cut.resolve()}'\n"
            )

    output = (
        CUTS_DIR /
        "visual_track.mp4"
    )

    run_command([
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FPS),
        str(output)
    ])

    return output


# ============================================================
# BGM
# ============================================================

def prepare_bgm():

    bgm = MEDIA_DIR / "bgm.ogg"

    if bgm.exists() and bgm.stat().st_size > 0:
        return bgm

    log(
        "BGM not found. Creating simple background."
    )

    generated = (
        MEDIA_DIR /
        "generated_bgm.wav"
    )

    run_command([
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=220:sample_rate=44100",
        "-t",
        "10",
        "-af",
        "volume=0.025",
        str(generated)
    ])

    return generated


# ============================================================
# FINAL VIDEO
# ============================================================

def render_final_video(
    visual_track,
    voice_track,
    subtitle_file,
    duration
):

    bgm = prepare_bgm()

    final_video = (
        OUTPUT_DIR /
        "final_video.mp4"
    )

    # 字幕を大きくして読みやすく
    subtitle_filter = (
        "subtitles="
        f"'{subtitle_file}':"
        "force_style="
        "'FontName=Noto Sans CJK JP,"
        "FontSize=22,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=3,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=80'"
    )

    run_command([
        "ffmpeg",
        "-y",

        "-stream_loop",
        "-1",
        "-i",
        str(visual_track),

        "-i",
        str(voice_track),

        "-stream_loop",
        "-1",
        "-i",
        str(bgm),

        "-filter_complex",
        (
            f"[2:a]"
            "volume=0.035,"
            "aresample=44100,"
            "aformat=sample_fmts=fltp"
            "[bgm];"

            "[1:a]"
            "volume=1.0"
            "[voice];"

            "[voice][bgm]"
            "amix=inputs=2:"
            "duration=first:"
            "dropout_transition=2"
            "[audio];"

            f"[0:v]"
            f"trim=duration={duration:.3f},"
            "setpts=PTS-STARTPTS,"
            f"{subtitle_filter}"
            "[video]"
        ),

        "-map",
        "[video]",

        "-map",
        "[audio]",

        "-t",
        f"{duration:.3f}",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "21",

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        str(final_video)
    ])

    return final_video


# ============================================================
# THUMBNAIL
# ============================================================

def pexels_photo_search(query):

    if not PEXELS_API_KEY:
        return None

    url = (
        "https://api.pexels.com/v1/search"
    )

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": query,
        "per_page": 10,
        "orientation": "landscape"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    photos = response.json().get(
        "photos",
        []
    )

    if not photos:
        return None

    random_photo = random.choice(
        photos
    )

    src = random_photo.get(
        "src",
        {}
    )

    return (
        src.get("large2x")
        or src.get("large")
        or src.get("original")
    )


def create_thumbnail(topic):

    from PIL import Image, ImageDraw, ImageFont

    title = clean_text(
        topic["title"]
    )

    query = (
        topic["keyword"]
        or topic["title"]
    )

    photo_url = None

    try:
        photo_url = pexels_photo_search(
            query
        )
    except Exception as e:
        log(
            f"Thumbnail search error: {e}"
        )

    if not photo_url:

        try:
            photo_url = pexels_photo_search(
                "surprised person lifestyle"
            )
        except Exception:
            pass

    if not photo_url:
        raise RuntimeError(
            "サムネイル画像を取得できませんでした"
        )

    raw_thumbnail = (
        IMAGE_DIR /
        "thumbnail_raw.jpg"
    )

    download_file(
        photo_url,
        raw_thumbnail
    )

    image = Image.open(
        raw_thumbnail
    ).convert("RGB")

    image = image.resize(
        (1280, 720)
    )

    draw = ImageDraw.Draw(
        image
    )

    # フォント
    font_candidates = [
        "/usr/share/fonts/opentype/noto/"
        "NotoSansCJK-Bold.ttc",

        "/usr/share/fonts/opentype/noto/"
        "NotoSansCJK-Black.ttc",

        "/usr/share/fonts/truetype/"
        "noto/NotoSansCJK-Bold.ttc"
    ]

    font_path = None

    for path in font_candidates:

        if os.path.exists(path):
            font_path = path
            break

    if font_path:

        big_font = ImageFont.truetype(
            font_path,
            70
        )

        small_font = ImageFont.truetype(
            font_path,
            36
        )

        badge_font = ImageFont.truetype(
            font_path,
            32
        )

    else:

        big_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    # 暗いオーバーレイ
    overlay = Image.new(
        "RGBA",
        image.size,
        (0, 0, 0, 0)
    )

    overlay_draw = ImageDraw.Draw(
        overlay
    )

    overlay_draw.rectangle(
        (0, 0, 1280, 720),
        fill=(0, 0, 0, 85)
    )

    image = Image.alpha_composite(
        image.convert("RGBA"),
        overlay
    ).convert("RGB")

    draw = ImageDraw.Draw(
        image
    )

    # 強いバッジ
    badge = "15選"

    draw.rounded_rectangle(
        (40, 35, 190, 95),
        radius=15,
        fill=(0, 0, 0)
    )

    draw.text(
        (65, 47),
        badge,
        font=badge_font,
        fill=(255, 255, 255)
    )

    # タイトルを短く
    display_title = title

    if len(display_title) > 22:
        display_title = (
            display_title[:22]
            + "…"
        )

    # 改行
    if len(display_title) > 11:

        middle = len(display_title) // 2

        display_title = (
            display_title[:middle]
            + "\n"
            + display_title[middle:]
        )

    # メイン文字
    draw.multiline_text(
        (50, 175),
        display_title,
        font=big_font,
        fill=(255, 255, 255),
        stroke_width=6,
        stroke_fill=(0, 0, 0),
        spacing=10
    )

    # 下部
    bottom_text = (
        "知らないとちょっと損する"
    )

    draw.text(
        (50, 620),
        bottom_text,
        font=small_font,
        fill=(255, 255, 255),
        stroke_width=3,
        stroke_fill=(0, 0, 0)
    )

    thumbnail = (
        OUTPUT_DIR /
        "thumbnail.jpg"
    )

    image.save(
        thumbnail,
        quality=95
    )

    return thumbnail


# ============================================================
# TITLE
# ============================================================

TITLE_TEMPLATES = [
    "知らないと面白い雑学15選｜身近なことの意外な理由",
    "知ると世界の見え方が変わる雑学15選",
    "実は知られていない身近な雑学15選",
    "思わず誰かに話したくなる雑学15選",
    "知っているだけで面白い雑学・心理学15選",
    "身近なのに知らないこと15選｜雑学・心理・哲学",
]


def create_title(topics):

    first = topics[0]["title"]

    template = random.choice(
        TITLE_TEMPLATES
    )

    # 先頭ネタを使ったタイトルも用意
    special_templates = [
        f"「{first}」知ってた？｜身近な雑学15選",
        f"{first}の理由、知ってる？｜雑学15選",
        f"意外と知らない「{first}」｜雑学15選",
    ]

    if random.random() < 0.45:
        return random.choice(
            special_templates
        )

    return template


# ============================================================
# DESCRIPTION
# ============================================================

DESCRIPTION_OPENINGS = [
    "今回は、身近なのに意外と知られていない話を15個まとめました。",
    "毎日の生活でふと気になることを、15個ピックアップしました。",
    "雑学、心理、哲学、科学などから、思わず誰かに話したくなる話を集めました。",
    "知っているだけで日常の見え方が少し変わる話を15個紹介します。",
    "今回は、身近な疑問から意外な知識まで15個をテンポよく紹介します。",
]


def create_description(topics):

    opening = random.choice(
        DESCRIPTION_OPENINGS
    )

    lines = [
        opening,
        "",
        "今回の15選：",
        ""
    ]

    for index, topic in enumerate(
        topics,
        start=1
    ):

        lines.append(
            f"{index}. {clean_text(topic['title'])}"
        )

    hashtags = [
        "#雑学 #豆知識 #心理学 #哲学 #身近な話",
        "#雑学15選 #豆知識 #心理学 #知識",
        "#雑学 #面白い話 #心理学 #科学",
        "#豆知識 #雑学動画 #哲学 #心理",
    ]

    lines.extend([
        "",
        random.choice(hashtags),
    ])

    return "\n".join(lines)


# ============================================================
# VIDEO INFO
# ============================================================

def create_video_info(
    topics,
    title,
    description
):

    info = {
        "title": title,
        "description": description,
        "category": "27",
        "privacyStatus": "public",
        "madeForKids": False,
        "topics": [
            {
                "number": index,
                "id": topic["id"],
                "title": topic["title"],
                "category": topic["category"]
            }
            for index, topic in enumerate(
                topics,
                start=1
            )
        ],
        "generatedAt": datetime.now(
            JST
        ).isoformat()
    }

    path = (
        OUTPUT_DIR /
        "video_info.json"
    )

    save_json(
        path,
        info
    )

    return path


# ============================================================
# MANIFEST
# ============================================================

def create_manifest(
    topics,
    title,
    duration,
    cuts
):

    manifest = {
        "generated_at": datetime.now(
            JST
        ).isoformat(),

        "title": title,

        "duration_seconds": duration,

        "topic_count": len(topics),

        "visual_cut_count": len(cuts),

        "topics": topics
    }

    path = (
        OUTPUT_DIR /
        "generation_manifest.json"
    )

    save_json(
        path,
        manifest
    )


# ============================================================
# MAIN
# ============================================================

def main():

    log("=" * 60)
    log("LUMI LONG VIDEO GENERATOR")
    log("5 MIN / 15 TOPICS / FAST MULTI CUT")
    log("=" * 60)

    if not PEXELS_API_KEY:

        raise RuntimeError(
            "PEXELS_API_KEY がありません"
        )

    # 古い生成物削除
    for folder in [
        VOICE_DIR,
        CUTS_DIR,
        SUBTITLE_DIR,
        IMAGE_DIR
    ]:

        for file in folder.iterdir():

            if file.is_file():

                try:
                    file.unlink()
                except Exception:
                    pass

    # ========================================================
    # 1. DATABASE
    # ========================================================

    database = load_trivia_database()

    # ========================================================
    # 2. SELECT
    # ========================================================

    topics = select_topics(
        database
    )

    if len(topics) != TOPICS_PER_VIDEO:

        raise RuntimeError(
            "15ネタを選択できませんでした"
        )

    # ========================================================
    # 3. VOICE
    # ========================================================

    voice_track, subtitle_file, duration = (
        create_voice_track(
            topics
        )
    )

    # 5分を超えた場合
    if duration > TARGET_DURATION:

        log(
            f"Voice is longer than target: "
            f"{duration:.2f}s"
        )

    # ========================================================
    # 4. VISUAL
    # ========================================================

    visual_cuts = create_visual_cuts(
        topics
    )

    visual_track = concat_video(
        visual_cuts
    )

    # ========================================================
    # 5. FINAL VIDEO
    # ========================================================

    final_video = render_final_video(
        visual_track,
        voice_track,
        subtitle_file,
        duration
    )

    # ========================================================
    # 6. TITLE
    # ========================================================

    title = create_title(
        topics
    )

    # ========================================================
    # 7. DESCRIPTION
    # ========================================================

    description = create_description(
        topics
    )

    # ========================================================
    # 8. VIDEO INFO
    # ========================================================

    create_video_info(
        topics,
        title,
        description
    )

    # ========================================================
    # 9. THUMBNAIL
    # ========================================================

    create_thumbnail(
        topics[0]
    )

    # ========================================================
    # 10. MANIFEST
    # ========================================================

    create_manifest(
        topics,
        title,
        duration,
        visual_cuts
    )

    # ========================================================
    # 11. TITLE FILE
    # ========================================================

    with open(
        OUTPUT_DIR / "title.txt",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(title)

    # ========================================================
    # 12. DESCRIPTION FILE
    # ========================================================

    with open(
        OUTPUT_DIR / "description.txt",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(description)

    # ========================================================
    # 13. FINAL CHECK
    # ========================================================

    if not final_video.exists():

        raise RuntimeError(
            "final_video.mp4 が生成されませんでした"
        )

    if not (
        OUTPUT_DIR /
        "thumbnail.jpg"
    ).exists():

        raise RuntimeError(
            "thumbnail.jpg が生成されませんでした"
        )

    log("=" * 60)
    log("GENERATION COMPLETE")
    log("=" * 60)

    log(
        f"VIDEO: {final_video}"
    )

    log(
        f"DURATION: {duration:.2f}s"
    )

    log(
        f"TOPICS: {len(topics)}"
    )

    log(
        f"VISUAL CUTS: {len(visual_cuts)}"
    )

    log(
        f"TITLE: {title}"
    )

    log("=" * 60)


if __name__ == "__main__":

    try:

        main()

    except Exception as e:

        log(
            f"FATAL ERROR: {e}"
        )

        import traceback

        traceback.print_exc()

        sys.exit(1)
