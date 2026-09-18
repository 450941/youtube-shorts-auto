# ============================================================
# LONG VIDEO GENERATOR
# 5-MINUTE TRIVIA + PSYCHOLOGY + ENCOURAGEMENT
#
# Version: 2026.09
# ============================================================

import os
import re
import json
import random
import asyncio
import hashlib
import subprocess
from pathlib import Path

import requests
import edge_tts

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageFilter,
    ImageEnhance,
)


# ============================================================
# SETTINGS
# ============================================================

WIDTH = 1920
HEIGHT = 1080
FPS = 30

THUMB_WIDTH = 3840
THUMB_HEIGHT = 2160

TOPICS_PER_VIDEO = 15

# 目標
TARGET_DURATION = 300

# 音声
VOICE = "ja-JP-NanamiNeural"
VOICE_RATE = "-3%"

# Pexels
PEXELS_API_KEY = os.environ.get(
    "PEXELS_API_KEY",
    ""
).strip()

PEXELS_URL = (
    "https://api.pexels.com/videos/search"
)

PEXELS_PHOTO_URL = (
    "https://api.pexels.com/v1/search"
)

PEXELS_HEADERS = {
    "Authorization": PEXELS_API_KEY
}

# directories
BASE_DIR = Path(".")

MEDIA_DIR = BASE_DIR / "media"
VOICE_DIR = MEDIA_DIR / "voice"
VIDEO_DIR = MEDIA_DIR / "cuts"
SUBTITLE_DIR = MEDIA_DIR / "subtitles"

OUTPUT_DIR = BASE_DIR / "output"

CACHE_DIR = BASE_DIR / "cache"

for d in [
    MEDIA_DIR,
    VOICE_DIR,
    VIDEO_DIR,
    SUBTITLE_DIR,
    OUTPUT_DIR,
    CACHE_DIR,
]:
    d.mkdir(
        parents=True,
        exist_ok=True
    )


# ============================================================
# FFMPEG
# ============================================================

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"


# ============================================================
# CONTENT DATABASE
# ============================================================
#
# 身近な疑問を中心にする。
#
# 「単なる雑学」ではなく、
#
# 1. フック
# 2. 意外な事実
# 3. なぜそうなる？
# 4. 日常へのつながり
#
# の流れにする。
# ============================================================

FACTS = [

    # --------------------------------------------------------
    # 心理
    # --------------------------------------------------------

    {
        "id": "psych_first_impression",
        "category": "心理",
        "title": "第一印象",
        "fact": (
            "最初に得た情報が、その後の判断の基準になってしまうことがあります。"
        ),
        "explanation": (
            "最初の情報を基準にすると、その後に入ってくる情報も、最初の印象に合わせて解釈しやすくなるからです。"
        ),
        "lesson": (
            "だから第一印象は大切ですが、一度の印象だけで人を決めつけないことも大切です。"
        ),
        "query": "people meeting conversation",
    },

    {
        "id": "psych_name_memory",
        "category": "心理",
        "title": "名前を呼ばれる",
        "fact": (
            "自分の名前は、たくさんの音の中でも特に注意を向けやすい情報です。"
        ),
        "explanation": (
            "自分に関係する情報は重要度が高いと脳が判断するため、周囲が騒がしくても名前には気づきやすくなります。"
        ),
        "lesson": (
            "人との会話では、相手の名前を自然に使うだけでも印象に残りやすくなります。"
        ),
        "query": "friends talking smiling",
    },

    {
        "id": "psych_choice",
        "category": "心理",
        "title": "選択肢が多すぎる",
        "fact": (
            "選択肢が増えれば増えるほど、必ずしも決めやすくなるわけではありません。"
        ),
        "explanation": (
            "候補が多いと比較する項目も増えるため、決めるための精神的な負担が大きくなることがあります。"
        ),
        "lesson": (
            "迷ったときは、最初から候補を三つ程度まで絞るだけでも考えやすくなります。"
        ),
        "query": "person choosing shopping products",
    },

    {
        "id": "psych_music_mood",
        "category": "心理",
        "title": "音楽と気分",
        "fact": (
            "音楽は、そのときの気分や記憶と強く結びつきやすいものです。"
        ),
        "explanation": (
            "特定の曲を聞いた瞬間に昔の出来事を思い出すことがあるのは、音と感情や記憶が一緒に保存されることがあるためです。"
        ),
        "lesson": (
            "気分を切り替えたいときに、いつも聞く曲を使うのも一つの方法です。"
        ),
        "query": "person listening music headphones",
    },

    {
        "id": "psych_smile",
        "category": "心理",
        "title": "笑顔",
        "fact": (
            "笑顔は、自分だけでなく周囲の人の感情にも影響することがあります。"
        ),
        "explanation": (
            "人は相手の表情から感情を読み取るため、明るい表情を見ると自分の反応も変わりやすくなります。"
        ),
        "lesson": (
            "無理に笑う必要はありませんが、自然な笑顔は人との距離を縮めるきっかけになります。"
        ),
        "query": "friends laughing together",
    },

    # --------------------------------------------------------
    # 脳
    # --------------------------------------------------------

    {
        "id": "brain_sleep_memory",
        "category": "脳",
        "title": "睡眠と記憶",
        "fact": (
            "寝ている間、脳が完全に休んで何もしていないわけではありません。"
        ),
        "explanation": (
            "睡眠中にも、起きている間に得た情報を整理する働きが行われています。"
        ),
        "lesson": (
            "何かを覚えたいときは、徹夜で詰め込むより睡眠も含めて考えることが大切です。"
        ),
        "query": "person sleeping bedroom",
    },

    {
        "id": "brain_attention",
        "category": "脳",
        "title": "注意力",
        "fact": (
            "人は目の前にあるものを、すべて同じ強さで意識しているわけではありません。"
        ),
        "explanation": (
            "脳は大量の情報の中から、重要だと判断したものに注意を向けています。"
        ),
        "lesson": (
            "集中したいときは、スマホなど注意を奪うものを視界から外すだけでも環境を変えられます。"
        ),
        "query": "person focused working laptop",
    },

    {
        "id": "brain_habit",
        "category": "脳",
        "title": "習慣",
        "fact": (
            "毎日繰り返す行動は、少しずつ意識しなくても行いやすくなります。"
        ),
        "explanation": (
            "同じ状況で同じ行動を繰り返すことで、その行動への負担が小さく感じられるようになるためです。"
        ),
        "lesson": (
            "大きな目標より、毎日一分だけ始めるほうが続けるきっかけを作りやすいことがあります。"
        ),
        "query": "person morning routine",
    },

    # --------------------------------------------------------
    # 人体
    # --------------------------------------------------------

    {
        "id": "body_yawn",
        "category": "人体",
        "title": "あくび",
        "fact": (
            "あくびは眠いときだけに起こるものではありません。"
        ),
        "explanation": (
            "退屈しているときや、緊張が変化するときなど、さまざまな場面であくびは起こります。"
        ),
        "lesson": (
            "つまり、あくびをしたからといって、必ずしも相手が話をつまらないと思っているとは限りません。"
        ),
        "query": "person tired yawning",
    },

    {
        "id": "body_heartbeat",
        "category": "人体",
        "title": "心拍数",
        "fact": (
            "緊張すると心臓が速く動くのを感じることがあります。"
        ),
        "explanation": (
            "体が活動に備える反応によって、心拍数などが変化するためです。"
        ),
        "lesson": (
            "大事な場面で緊張するのは、弱さではなく体が準備している反応とも考えられます。"
        ),
        "query": "person nervous presentation",
    },

    # --------------------------------------------------------
    # 日常
    # --------------------------------------------------------

    {
        "id": "daily_phone",
        "category": "日常",
        "title": "スマホを見る",
        "fact": (
            "スマホは、通知が来ていなくても何となく確認してしまうことがあります。"
        ),
        "explanation": (
            "新しい情報があるかもしれないという期待そのものが、確認する行動のきっかけになることがあります。"
        ),
        "lesson": (
            "集中したい時間だけ通知を切ると、意識を戻す回数を減らせます。"
        ),
        "query": "person smartphone home",
    },

    {
        "id": "daily_smell_memory",
        "category": "日常",
        "title": "匂いと記憶",
        "fact": (
            "昔の記憶が、突然ある匂いによってよみがえることがあります。"
        ),
        "explanation": (
            "匂いの情報は感情や記憶に関係する脳の領域と近い経路で処理されるため、強い記憶と結びつくことがあります。"
        ),
        "lesson": (
            "だから昔の場所の匂いを感じると、一瞬で過去に戻ったような感覚になることがあります。"
        ),
        "query": "person smelling coffee",
    },

    # --------------------------------------------------------
    # 科学
    # --------------------------------------------------------

    {
        "id": "science_ice",
        "category": "科学",
        "title": "氷",
        "fact": (
            "水は凍ると、液体の水より体積が大きくなります。"
        ),
        "explanation": (
            "水分子が氷の中で規則的な構造を作ることで、分子同士の間隔が広がるためです。"
        ),
        "lesson": (
            "だからペットボトルいっぱいに水を入れて凍らせると、容器が変形することがあります。"
        ),
        "query": "ice water glass close up",
    },

    {
        "id": "science_sky",
        "category": "科学",
        "title": "空が青い理由",
        "fact": (
            "昼間の空が青く見えるのは、太陽の光がそのまま青いからではありません。"
        ),
        "explanation": (
            "大気中で光が散らばるとき、青い光は比較的強く散乱されるため、空全体から青い光が届きやすくなります。"
        ),
        "lesson": (
            "夕方に空が赤くなるのも、光が大気を通る距離が変わることと関係しています。"
        ),
        "query": "blue sky clouds sunset",
    },

    # --------------------------------------------------------
    # 哲学・考え方
    # --------------------------------------------------------

    {
        "id": "philosophy_control",
        "category": "哲学",
        "title": "コントロールできること",
        "fact": (
            "人生では、自分では変えられないことに悩んでしまうことがあります。"
        ),
        "explanation": (
            "他人の評価や過去の出来事などは、直接コントロールすることが難しいからです。"
        ),
        "lesson": (
            "そんなときは、今日自分ができる小さな行動に意識を戻すだけでも考え方を整理しやすくなります。"
        ),
        "query": "person thinking peaceful nature",
    },

    {
        "id": "philosophy_failure",
        "category": "哲学",
        "title": "失敗",
        "fact": (
            "失敗した出来事そのものより、失敗をどう解釈するかで次の行動は変わります。"
        ),
        "explanation": (
            "同じ出来事でも、終わりだと考えるか、次に使える情報だと考えるかで、その後の選択が変わるからです。"
        ),
        "lesson": (
            "うまくいかなかった日は、全部を否定するのではなく、一つだけ学びを持ち帰れば十分です。"
        ),
        "query": "person overcoming challenge",
    },

    # --------------------------------------------------------
    # 人間関係
    # --------------------------------------------------------

    {
        "id": "relationship_listening",
        "category": "人間関係",
        "title": "聞く力",
        "fact": (
            "会話では、面白い話をすることだけが大切なわけではありません。"
        ),
        "explanation": (
            "人は自分の話をきちんと聞いてもらえると、相手に理解されていると感じやすくなります。"
        ),
        "lesson": (
            "会話に困ったら、無理に話題を作るより相手の話を一つ深掘りする方法もあります。"
        ),
        "query": "two people talking listening",
    },

    {
        "id": "relationship_comparison",
        "category": "人間関係",
        "title": "人と比べる",
        "fact": (
            "人は自分の状況を、周囲の人と比べて判断してしまうことがあります。"
        ),
        "explanation": (
            "自分だけを見ても、それが良いのか悪いのか判断しにくいため、他人を基準にしてしまうことがあるからです。"
        ),
        "lesson": (
            "でも他人の結果だけを見て、自分の途中経過と比べると苦しくなります。"
        ),
        "query": "person looking city window",
    },

    # --------------------------------------------------------
    # 仕事・勉強
    # --------------------------------------------------------

    {
        "id": "work_start",
        "category": "仕事",
        "title": "始めるだけ",
        "fact": (
            "やる気が出てから行動するとは限りません。"
        ),
        "explanation": (
            "まず少し行動することで、あとから集中状態に入りやすくなることがあります。"
        ),
        "lesson": (
            "やる気がない日は、五分だけやると決めると始めるハードルを下げられます。"
        ),
        "query": "person working desk laptop",
    },

    {
        "id": "work_break",
        "category": "仕事",
        "title": "休憩",
        "fact": (
            "長時間ずっと集中し続けることだけが効率的とは限りません。"
        ),
        "explanation": (
            "注意力や疲労は時間とともに変化するため、適切に休憩を入れることが役立つ場合があります。"
        ),
        "lesson": (
            "休むことをサボりと考えず、次の集中のための時間と考えるのも一つです。"
        ),
        "query": "person taking break coffee work",
    },

    # --------------------------------------------------------
    # 食べ物
    # --------------------------------------------------------

    {
        "id": "food_spicy",
        "category": "食べ物",
        "title": "辛さ",
        "fact": (
            "唐辛子の辛さは、味覚そのものとは少し違います。"
        ),
        "explanation": (
            "唐辛子に含まれるカプサイシンが、熱さや痛みに関係する受容体を刺激することで、辛いと感じます。"
        ),
        "lesson": (
            "だから辛い料理を食べたとき、実際に熱いわけではなくても熱く感じることがあります。"
        ),
        "query": "spicy food chili peppers",
    },

    # --------------------------------------------------------
    # 自然
    # --------------------------------------------------------

    {
        "id": "nature_rain",
        "category": "自然",
        "title": "雨の匂い",
        "fact": (
            "雨が降ったあとに独特の匂いを感じることがあります。"
        ),
        "explanation": (
            "土や植物などに由来する物質が雨によって空気中に広がることなどが関係しています。"
        ),
        "lesson": (
            "普段何気なく感じる雨の匂いにも、実は自然の化学反応が隠れています。"
        ),
        "query": "rain street nature",
    },

]


# ============================================================
# HOOKS
# ============================================================

HOOKS = [
    "これ、たぶん一度は経験あります。",
    "実はこれ、かなり身近な心理現象です。",
    "知っているようで、意外と知らない話です。",
    "もし今までこう思っていたなら、少しだけ見方が変わるかもしれません。",
    "これ、あなたにも起きているかもしれません。",
    "日常の何気ない瞬間に、実はこんなことが起きています。",
    "一見すると普通ですが、脳の仕組みを知ると面白くなります。",
    "これを知ると、昨日までの日常が少し違って見えるかもしれません。",
]


# ============================================================
# ENCOURAGEMENT
# ============================================================

ENCOURAGEMENT = [
    "知らなかったことを一つ知るだけでも、今日は前進です。",
    "全部を変えなくても、今日一つ行動できれば十分です。",
    "小さな変化でも、積み重なると大きな違いになります。",
    "うまくいかない日があっても、それだけで失敗とは限りません。",
    "今日できる小さなことから始めれば大丈夫です。",
]


# ============================================================
# UTILS
# ============================================================

def run_command(
    cmd,
    check=True,
    capture_output=False
):
    print()
    print("RUN:")
    print(" ".join(map(str, cmd)))

    result = subprocess.run(
        cmd,
        check=check,
        text=True,
        capture_output=capture_output
    )

    if capture_output:
        return result.stdout.strip()

    return result


def get_duration(path):
    cmd = [
        FFPROBE,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]

    output = run_command(
        cmd,
        capture_output=True
    )

    try:
        return float(output)
    except Exception:
        return 0.0


def safe_name(text):
    text = re.sub(
        r'[\\/:*?"<>|]',
        "_",
        text
    )

    text = text.replace(
        " ",
        "_"
    )

    return text[:80]


def load_json(path, default):
    if not path.exists():
        return default

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# TOPIC SELECTION
# ============================================================

def select_topics():
    used_file = CACHE_DIR / "used_topics.json"

    used = load_json(
        used_file,
        []
    )

    if not isinstance(used, list):
        used = []

    available = [
        x for x in FACTS
        if x["id"] not in used
    ]

    if len(available) < TOPICS_PER_VIDEO:
        print(
            "Topic pool almost exhausted."
        )

        used = []

        available = list(
            FACTS
        )

    random.shuffle(
        available
    )

    selected = available[
        :TOPICS_PER_VIDEO
    ]

    used.extend(
        x["id"]
        for x in selected
    )

    # 重複除去
    used = list(
        dict.fromkeys(used)
    )

    save_json(
        used_file,
        used
    )

    return selected


# ============================================================
# SCRIPT CREATION
# ============================================================

def make_script(topic, index):
    hook = random.choice(
        HOOKS
    )

    encouragement = random.choice(
        ENCOURAGEMENT
    )

    title = topic["title"]

    sentences = [
        f"第{index}問。{hook}",
        f"{title}について、実は「{topic['fact']}」ということがあります。",
        topic["explanation"],
        topic["lesson"],
        encouragement,
    ]

    # 長すぎる場合に軽く整理
    result = []

    for sentence in sentences:
        sentence = sentence.strip()

        if sentence:
            result.append(
                sentence
            )

    return result


# ============================================================
# TTS
# ============================================================

async def create_tts(
    text,
    output_path
):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate=VOICE_RATE
    )

    await communicate.save(
        str(output_path)
    )


def create_tts_sync(
    text,
    output_path
):
    print()
    print("Creating TTS...")
    print(text)

    asyncio.run(
        create_tts(
            text,
            output_path
        )
    )

    duration = get_duration(
        output_path
    )

    print(
        f"Audio duration: {duration:.2f}s"
    )

    if duration <= 0:
        raise RuntimeError(
            f"TTS音声の長さを取得できません: {output_path}"
        )

    return duration


# ============================================================
# PEXELS VIDEO SEARCH
# ============================================================

def search_pexels_videos(
    query,
    per_page=20
):
    if not PEXELS_API_KEY:
        raise RuntimeError(
            "PEXELS_API_KEY がありません"
        )

    print()
    print(
        f"Searching Pexels: {query}"
    )

    params = {
        "query": query,
        "orientation": "landscape",
        "size": "medium",
        "per_page": per_page,
        "page": random.randint(
            1,
            3
        )
    }

    try:
        response = requests.get(
            PEXELS_URL,
            headers=PEXELS_HEADERS,
            params=params,
            timeout=30
        )

        print(
            "Pexels status:",
            response.status_code
        )

        response.raise_for_status()

        data = response.json()

        videos = data.get(
            "videos",
            []
        )

        print(
            "Found videos:",
            len(videos)
        )

        return videos

    except Exception as e:
        print(
            "Pexels search error:",
            e
        )

        return []


def choose_video_file(video):
    files = video.get(
        "video_files",
        []
    )

    if not files:
        return None

    # HD以上を優先
    candidates = []

    for item in files:
        width = item.get(
            "width"
        ) or 0

        height = item.get(
            "height"
        ) or 0

        link = item.get(
            "link"
        )

        if not link:
            continue

        candidates.append(
            (
                width * height,
                width,
                height,
                link
            )
        )

    if not candidates:
        return None

    candidates.sort(
        reverse=True
    )

    # なるべく1920x1080前後
    for area, width, height, link in candidates:
        if width >= 1280 and height >= 720:
            return {
                "link": link,
                "width": width,
                "height": height
            }

    area, width, height, link = candidates[0]

    return {
        "link": link,
        "width": width,
        "height": height
    }


def get_video_for_topic(
    topic,
    used_video_ids
):
    queries = [
        topic["query"],
    ]

    # 日本語タイトルも候補
    queries.append(
        topic["title"]
    )

    for query in queries:

        videos = search_pexels_videos(
            query,
            per_page=20
        )

        if not videos:
            continue

        random.shuffle(
            videos
        )

        for video in videos:

            video_id = video.get(
                "id"
            )

            if not video_id:
                continue

            if str(video_id) in used_video_ids:
                continue

            selected_file = choose_video_file(
                video
            )

            if not selected_file:
                continue

            return {
                "id": str(video_id),
                "url": selected_file["link"],
                "width": selected_file["width"],
                "height": selected_file["height"],
                "user": video.get(
                    "user",
                    {}
                ),
                "page": video.get(
                    "url",
                    ""
                )
            }

    # 最終フォールバック
    print(
        "Pexels動画が見つかりませんでした。"
    )

    return None


# ============================================================
# DOWNLOAD VIDEO
# ============================================================

def download_video(
    video_info,
    output_path
):
    print()
    print(
        "Downloading Pexels video..."
    )

    url = video_info["url"]

    response = requests.get(
        url,
        stream=True,
        timeout=120
    )

    response.raise_for_status()

    with open(
        output_path,
        "wb"
    ) as f:

        for chunk in response.iter_content(
            chunk_size=1024 * 1024
        ):

            if chunk:
                f.write(chunk)

    size = output_path.stat().st_size

    print(
        "Downloaded:",
        output_path,
        f"{size / 1024 / 1024:.1f} MB"
    )

    if size < 10000:
        raise RuntimeError(
            "Pexels動画のダウンロードサイズが小さすぎます"
        )


# ============================================================
# CREATE SCENE
# ============================================================

def create_scene(
    source_video,
    audio_file,
    output_file
):
    duration = get_duration(
        audio_file
    )

    if duration <= 0:
        raise RuntimeError(
            "音声時間が取得できません"
        )

    print()
    print(
        f"Creating scene: {duration:.2f}s"
    )

    # 縦・横どちらでも中央クロップ
    vf = (
        f"scale={WIDTH}:{HEIGHT}:"
        "force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        "setsar=1"
    )

    cmd = [
        FFMPEG,
        "-y",

        "-stream_loop",
        "-1",

        "-i",
        str(source_video),

        "-i",
        str(audio_file),

        "-filter_complex",
        f"[0:v]{vf}[v]",

        "-map",
        "[v]",

        "-map",
        "1:a",

        "-t",
        f"{duration:.3f}",

        "-r",
        str(FPS),

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-shortest",

        str(output_file)
    ]

    run_command(
        cmd
    )

    if not output_file.exists():
        raise RuntimeError(
            f"Scene作成失敗: {output_file}"
        )


# ============================================================
# CONCAT
# ============================================================

def concat_scenes(
    scene_files,
    output_file
):
    list_file = VIDEO_DIR / "concat.txt"

    with open(
        list_file,
        "w",
        encoding="utf-8"
    ) as f:

        for path in scene_files:
            absolute = path.resolve()

            f.write(
                "file '"
                + str(absolute).replace(
                    "'",
                    "'\\''"
                )
                + "'\n"
            )

    cmd = [
        FFMPEG,
        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(list_file),

        "-c",
        "copy",

        str(output_file)
    ]

    run_command(
        cmd
    )

    if not output_file.exists():
        raise RuntimeError(
            "動画結合に失敗しました"
        )


# ============================================================
# SUBTITLES
# ============================================================

def format_srt_time(seconds):
    if seconds < 0:
        seconds = 0

    millis = int(
        round(
            (seconds - int(seconds))
            * 1000
        )
    )

    total = int(
        seconds
    )

    hours = total // 3600

    minutes = (
        total % 3600
    ) // 60

    secs = total % 60

    if millis >= 1000:
        secs += 1
        millis = 0

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{millis:03d}"
    )


def create_srt(
    subtitle_entries,
    output_file
):
    print()
    print(
        "Creating subtitles..."
    )

    lines = []

    for index, entry in enumerate(
        subtitle_entries,
        start=1
    ):

        start = entry["start"]
        end = entry["end"]
        text = entry["text"]

        lines.append(
            str(index)
        )

        lines.append(
            f"{format_srt_time(start)} --> "
            f"{format_srt_time(end)}"
        )

        lines.append(
            text
        )

        lines.append("")

    output_file.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print(
        "Subtitle file:",
        output_file
    )


# ============================================================
# BGM
# ============================================================

def create_fallback_bgm(
    output_file,
    duration
):
    print()
    print(
        "Creating fallback BGM..."
    )

    cmd = [
        FFMPEG,
        "-y",

        "-f",
        "lavfi",

        "-i",
        "sine=frequency=220:sample_rate=44100",

        "-f",
        "lavfi",

        "-i",
        "sine=frequency=277:sample_rate=44100",

        "-filter_complex",
        (
            "[0:a]volume=0.06[a0];"
            "[1:a]volume=0.04[a1];"
            "[a0][a1]amix=inputs=2:"
            "duration=longest,"
            "afade=t=in:st=0:d=2,"
            f"afade=t=out:st={max(duration - 3, 0)}:d=3"
        ),

        "-t",
        f"{duration:.3f}",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        str(output_file)
    ]

    run_command(
        cmd
    )


def prepare_bgm(
    duration
):
    downloaded = MEDIA_DIR / "bgm.ogg"

    fallback = MEDIA_DIR / "bgm_fallback.m4a"

    if downloaded.exists():
        print()
        print(
            "Using downloaded BGM:",
            downloaded
        )

        return downloaded

    create_fallback_bgm(
        fallback,
        duration
    )

    return fallback


# ============================================================
# BURN SUBTITLES + MIX BGM
# ============================================================

def burn_subtitles_and_mix_bgm(
    video_file,
    subtitle_file,
    bgm_file,
    output_file
):
    print()
    print(
        "Burning subtitles and mixing BGM..."
    )

    duration = get_duration(
        video_file
    )

    # Linux上のFFmpeg/libass向け
    subtitle_path = str(
        subtitle_file.resolve()
    )

    # subtitles filterのエスケープ
    subtitle_path = (
        subtitle_path
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )

    subtitle_filter = (
        f"subtitles='{subtitle_path}':"
        "force_style="
        "'FontName=Noto Sans CJK JP,"
        "FontSize=22,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H80000000,"
        "BorderStyle=1,"
        "Outline=3,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=55'"
    )

    cmd = [
        FFMPEG,
        "-y",

        "-i",
        str(video_file),

        "-stream_loop",
        "-1",

        "-i",
        str(bgm_file),

        "-filter_complex",
        (
            f"[0:v]{subtitle_filter}[v];"
            "[1:a]volume=0.08[bgm];"
            "[0:a][bgm]"
            "amix=inputs=2:"
            "duration=first:"
            "dropout_transition=2"
            "[a]"
        ),

        "-map",
        "[v]",

        "-map",
        "[a]",

        "-t",
        f"{duration:.3f}",

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "21",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-movflags",
        "+faststart",

        str(output_file)
    ]

    run_command(
        cmd
    )

    if not output_file.exists():
        raise RuntimeError(
            "字幕付き最終動画の作成に失敗しました"
        )


# ============================================================
# PEXELS PHOTO SEARCH
# ============================================================

def search_pexels_photo(
    query
):
    print()
    print(
        f"Searching Pexels photo: {query}"
    )

    try:
        response = requests.get(
            PEXELS_PHOTO_URL,
            headers=PEXELS_HEADERS,
            params={
                "query": query,
                "orientation": "landscape",
                "per_page": 20,
                "page": random.randint(
                    1,
                    3
                )
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        photos = data.get(
            "photos",
            []
        )

        if not photos:
            return None

        random.shuffle(
            photos
        )

        for photo in photos:

            src = photo.get(
                "src",
                {}
            )

            # 大きい画像優先
            image_url = (
                src.get("original")
                or src.get("large2x")
                or src.get("large")
            )

            if image_url:
                return {
                    "id": photo.get(
                        "id"
                    ),
                    "url": image_url,
                    "page": photo.get(
                        "url",
                        ""
                    ),
                    "photographer": photo.get(
                        "photographer",
                        ""
                    )
                }

    except Exception as e:
        print(
            "Pexels photo error:",
            e
        )

    return None


def download_photo(
    photo_info,
    output_file
):
    response = requests.get(
        photo_info["url"],
        timeout=120
    )

    response.raise_for_status()

    output_file.write_bytes(
        response.content
    )

    if output_file.stat().st_size < 10000:
        raise RuntimeError(
            "サムネイル画像が小さすぎます"
        )


# ============================================================
# FONT
# ============================================================

def find_font():
    candidates = [

        "/usr/share/fonts/opentype/noto/"
        "NotoSansCJK-Regular.ttc",

        "/usr/share/fonts/opentype/noto/"
        "NotoSansCJK-Bold.ttc",

        "/usr/share/fonts/truetype/"
        "noto/NotoSansCJK-Regular.ttc",

        "/usr/share/fonts/truetype/"
        "noto/NotoSansCJK-Bold.ttc",

        "/usr/share/fonts/truetype/dejavu/"
        "DejaVuSans-Bold.ttf",

    ]

    for font in candidates:

        path = Path(font)

        if path.exists():
            return str(path)

    return None


# ============================================================
# THUMBNAIL
# ============================================================

def create_thumbnail(
    photo_file,
    topic,
    output_file
):
    print()
    print(
        "Creating thumbnail..."
    )

    image = Image.open(
        photo_file
    ).convert(
        "RGB"
    )

    # cover crop
    image_ratio = (
        image.width
        / image.height
    )

    target_ratio = (
        THUMB_WIDTH
        / THUMB_HEIGHT
    )

    if image_ratio > target_ratio:

        new_height = THUMB_HEIGHT

        new_width = int(
            new_height
            * image_ratio
        )

        image = image.resize(
            (
                new_width,
                new_height
            ),
            Image.Resampling.LANCZOS
        )

        left = (
            new_width
            - THUMB_WIDTH
        ) // 2

        image = image.crop(
            (
                left,
                0,
                left + THUMB_WIDTH,
                THUMB_HEIGHT
            )
        )

    else:

        new_width = THUMB_WIDTH

        new_height = int(
            new_width
            / image_ratio
        )

        image = image.resize(
            (
                new_width,
                new_height
            ),
            Image.Resampling.LANCZOS
        )

        top = (
            new_height
            - THUMB_HEIGHT
        ) // 2

        image = image.crop(
            (
                0,
                top,
                THUMB_WIDTH,
                top + THUMB_HEIGHT
            )
        )

    # 軽いシャープ化
    image = ImageEnhance.Contrast(
        image
    ).enhance(
        1.08
    )

    image = ImageEnhance.Color(
        image
    ).enhance(
        1.08
    )

    # 背景を少しぼかす
    image = image.filter(
        ImageFilter.GaussianBlur(
            0.5
        )
    )

    overlay = Image.new(
        "RGBA",
        image.size,
        (
            0,
            0,
            0,
            0
        )
    )

    draw = ImageDraw.Draw(
        overlay
    )

    # 左側を暗くする
    for x in range(
        THUMB_WIDTH
    ):

        alpha = int(
            190
            * (
                1
                - x / THUMB_WIDTH
            )
        )

        if alpha < 0:
            alpha = 0

        draw.line(
            [
                (x, 0),
                (
                    x,
                    THUMB_HEIGHT
                )
            ],
            fill=(
                0,
                0,
                0,
                alpha
            )
        )

    image = Image.alpha_composite(
        image.convert("RGBA"),
        overlay
    )

    draw = ImageDraw.Draw(
        image
    )

    font_path = find_font()

    if font_path:

        big_font = ImageFont.truetype(
            font_path,
            250
        )

        medium_font = ImageFont.truetype(
            font_path,
            130
        )

        small_font = ImageFont.truetype(
            font_path,
            85
        )

    else:

        big_font = ImageFont.load_default()
        medium_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # バッジ
    badge_text = "知らないと面白い"

    badge_box = (
        180,
        180,
        1150,
        350
    )

    draw.rounded_rectangle(
        badge_box,
        radius=40,
        fill=(
            255,
            255,
            255,
            235
        )
    )

    draw.text(
        (
            230,
            205
        ),
        badge_text,
        font=small_font,
        fill=(
            20,
            20,
            20,
            255
        )
    )

    # メインタイトル
    title = (
        "身近な雑学"
    )

    draw.text(
        (
            180,
            500
        ),
        title,
        font=medium_font,
        fill=(
            255,
            255,
            255,
            255
        ),
        stroke_width=6,
        stroke_fill=(
            0,
            0,
            0,
            180
        )
    )

    # topic
    topic_text = (
        f"「{topic['title']}」"
    )

    draw.text(
        (
            180,
            690
        ),
        topic_text,
        font=big_font,
        fill=(
            255,
            230,
            80,
            255
        ),
        stroke_width=8,
        stroke_fill=(
            0,
            0,
            0,
            210
        )
    )

    # 下部
    bottom_text = "15問まとめて紹介"

    draw.text(
        (
            190,
            1780
        ),
        bottom_text,
        font=small_font,
        fill=(
            255,
            255,
            255,
            255
        ),
        stroke_width=4,
        stroke_fill=(
            0,
            0,
            0,
            180
        )
    )

    image = image.convert(
        "RGB"
    )

    image.save(
        output_file,
        "JPEG",
        quality=94,
        optimize=True
    )

    print(
        "Thumbnail created:",
        output_file
    )


# ============================================================
# TITLE
# ============================================================

def create_title(topic):
    patterns = [
        f"知らないと面白い「{topic['title']}」の雑学15選",
        f"身近なのに意外と知らない雑学15選【{topic['title']}】",
        f"知ると日常がちょっと面白くなる雑学15選",
        f"実は知らない人が多い身近な雑学15選",
    ]

    return random.choice(
        patterns
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print(
        "LONG VIDEO GENERATOR"
    )
    print(
        "5-MINUTE TRIVIA + PSYCHOLOGY"
    )
    print("=" * 70)

    if not PEXELS_API_KEY:

        raise RuntimeError(
            "PEXELS_API_KEY がありません"
        )

    # --------------------------------------------------------
    # Clean old generated files
    # --------------------------------------------------------

    for path in VOICE_DIR.glob("*"):
        if path.is_file():
            path.unlink()

    for path in VIDEO_DIR.glob("*"):
        if path.is_file():
            path.unlink()

    for path in SUBTITLE_DIR.glob("*"):
        if path.is_file():
            path.unlink()

    # --------------------------------------------------------
    # Select topics
    # --------------------------------------------------------

    topics = select_topics()

    print()
    print(
        "Selected topics:"
    )

    for i, topic in enumerate(
        topics,
        start=1
    ):

        print(
            f"{i:02d}. "
            f"[{topic['category']}] "
            f"{topic['title']}"
        )

    # --------------------------------------------------------
    # Create scripts
    # --------------------------------------------------------

    all_scripts = []

    for index, topic in enumerate(
        topics,
        start=1
    ):

        script = make_script(
            topic,
            index
        )

        all_scripts.append(
            {
                "topic": topic,
                "sentences": script
            }
        )

    # --------------------------------------------------------
    # Generate TTS
    # --------------------------------------------------------

    sentence_audio = []

    subtitle_entries = []

    global_time = 0.0

    used_video_ids = set()

    scene_files = []

    pexels_sources = []

    # --------------------------------------------------------
    # Each topic
    # --------------------------------------------------------

    for topic_index, item in enumerate(
        all_scripts,
        start=1
    ):

        topic = item["topic"]

        print()
        print("=" * 70)
        print(
            f"TOPIC {topic_index}/{TOPICS_PER_VIDEO}"
        )
        print(
            topic["title"]
        )
        print("=" * 70)

        topic_audio_files = []

        topic_start = global_time

        # ----------------------------------------------------
        # Sentence TTS
        # ----------------------------------------------------

        for sentence_index, sentence in enumerate(
            item["sentences"],
            start=1
        ):

            audio_file = (
                VOICE_DIR
                / f"topic_{topic_index:02d}_"
                  f"{sentence_index:02d}.mp3"
            )

            duration = create_tts_sync(
                sentence,
                audio_file
            )

            topic_audio_files.append(
                audio_file
            )

            subtitle_entries.append(
                {
                    "start": global_time,
                    "end": global_time + duration,
                    "text": sentence
                }
            )

            global_time += duration

        # ----------------------------------------------------
        # Merge topic audio
        # ----------------------------------------------------

        topic_audio = (
            VOICE_DIR
            / f"topic_{topic_index:02d}.mp3"
        )

        concat_file = (
            VOICE_DIR
            / f"topic_{topic_index:02d}.txt"
        )

        with open(
            concat_file,
            "w",
            encoding="utf-8"
        ) as f:

            for audio in topic_audio_files:

                absolute = (
                    audio.resolve()
                )

                escaped = str(
                    absolute
                ).replace(
                    "'",
                    "'\\''"
                )

                f.write(
                    f"file '{escaped}'\n"
                )

        run_command(
            [
                FFMPEG,
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
                str(topic_audio)
            ]
        )

        # ----------------------------------------------------
        # Get Pexels video
        # ----------------------------------------------------

        video_info = get_video_for_topic(
            topic,
            used_video_ids
        )

        if video_info is None:

            # 最終安全策として汎用動画を探す
            fallback_queries = [
                "people lifestyle",
                "happy people",
                "daily life",
                "person thinking",
                "modern lifestyle",
            ]

            for fallback_query in fallback_queries:

                print(
                    "Fallback Pexels search:",
                    fallback_query
                )

                videos = search_pexels_videos(
                    fallback_query,
                    per_page=20
                )

                random.shuffle(
                    videos
                )

                for candidate in videos:

                    candidate_id = str(
                        candidate.get(
                            "id",
                            ""
                        )
                    )

                    if (
                        not candidate_id
                        or candidate_id
                        in used_video_ids
                    ):
                        continue

                    candidate_file = choose_video_file(
                        candidate
                    )

                    if not candidate_file:
                        continue

                    video_info = {
                        "id": candidate_id,
                        "url": candidate_file[
                            "link"
                        ],
                        "width": candidate_file[
                            "width"
                        ],
                        "height": candidate_file[
                            "height"
                        ],
                        "user": candidate.get(
                            "user",
                            {}
                        ),
                        "page": candidate.get(
                            "url",
                            ""
                        )
                    }

                    break

                if video_info:
                    break

        if video_info is None:
            raise RuntimeError(
                f"Pexels動画を取得できませんでした: "
                f"{topic['title']}"
            )

        used_video_ids.add(
            video_info["id"]
        )

        pexels_sources.append(
            {
                "topic": topic["title"],
                "video_id": video_info["id"],
                "url": video_info.get(
                    "page",
                    ""
                ),
                "photographer": (
                    video_info.get(
                        "user",
                        {}
                    ).get(
                        "name",
                        ""
                    )
                )
            }
        )

        # ----------------------------------------------------
        # Download
        # ----------------------------------------------------

        source_video = (
            MEDIA_DIR
            / f"source_{topic_index:02d}.mp4"
        )

        download_video(
            video_info,
            source_video
        )

        # ----------------------------------------------------
        # Scene
        # ----------------------------------------------------

        scene_file = (
            VIDEO_DIR
            / f"scene_{topic_index:02d}.mp4"
        )

        create_scene(
            source_video,
            topic_audio,
            scene_file
        )

        scene_files.append(
            scene_file
        )

        # cleanup source to save space
        try:
            source_video.unlink()
        except Exception:
            pass

        # topic duration
        topic_duration = (
            global_time
            - topic_start
        )

        print()
        print(
            f"Topic duration: "
            f"{topic_duration:.2f}s"
        )

    # --------------------------------------------------------
    # Total duration
    # --------------------------------------------------------

    total_duration = global_time

    print()
    print("=" * 70)
    print(
        f"TOTAL NARRATION: "
        f"{total_duration:.2f}s"
    )
    print(
        f"TARGET: "
        f"{TARGET_DURATION}s"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # Concatenate scenes
    # --------------------------------------------------------

    concatenated = (
        MEDIA_DIR
        / "concatenated.mp4"
    )

    concat_scenes(
        scene_files,
        concatenated
    )

    # --------------------------------------------------------
    # Subtitle
    # --------------------------------------------------------

    subtitle_file = (
        SUBTITLE_DIR
        / "final.srt"
    )

    create_srt(
        subtitle_entries,
        subtitle_file
    )

    # --------------------------------------------------------
    # BGM
    # --------------------------------------------------------

    actual_video_duration = get_duration(
        concatenated
    )

    bgm_file = prepare_bgm(
        actual_video_duration
    )

    # --------------------------------------------------------
    # Final video
    # --------------------------------------------------------

    final_video = (
        OUTPUT_DIR
        / "final_video.mp4"
    )

    burn_subtitles_and_mix_bgm(
        concatenated,
        subtitle_file,
        bgm_file,
        final_video
    )

    # --------------------------------------------------------
    # Thumbnail
    # --------------------------------------------------------

    thumbnail_queries = [
        f"{topics[0]['query']}",
        "surprised person thinking",
        "person curious smartphone",
        "happy person looking camera",
    ]

    photo_info = None

    for query in thumbnail_queries:

        photo_info = search_pexels_photo(
            query
        )

        if photo_info:
            break

    thumbnail_source = (
        MEDIA_DIR
        / "thumbnail_source.jpg"
    )

    thumbnail_file = (
        OUTPUT_DIR
        / "thumbnail.jpg"
    )

    if photo_info:

        download_photo(
            photo_info,
            thumbnail_source
        )

        create_thumbnail(
            thumbnail_source,
            topics[0],
            thumbnail_file
        )

    else:

        print(
            "Thumbnail Pexels photo not found."
        )

        # 動画の最初のフレームを代用
        run_command(
            [
                FFMPEG,
                "-y",
                "-i",
                str(final_video),
                "-frames:v",
                "1",
                str(thumbnail_file)
            ]
        )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title = create_title(
        topics[0]
    )

    title_file = (
        OUTPUT_DIR
        / "title.txt"
    )

    title_file.write_text(
        title,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    description = (
        "身近なのに意外と知らない雑学を15個紹介します。\n"
        "心理学、脳、人体、日常、科学、哲学など、"
        "普段の生活でちょっと気になる話をまとめました。\n\n"
        "知らなかったことを一つ知るだけでも、"
        "日常の見え方が少し変わるかもしれません。\n\n"
        "#雑学 #豆知識 #心理学 #面白い話 #日常"
    )

    # --------------------------------------------------------
    # video_info.json
    # --------------------------------------------------------

    info = {
        "title": title,
        "description": description,
        "category": "27",
        "topics": [
            {
                "number": i,
                "id": topic["id"],
                "category": topic["category"],
                "title": topic["title"]
            }
            for i, topic in enumerate(
                topics,
                start=1
            )
        ],
        "duration_seconds": get_duration(
            final_video
        ),
        "video_file": str(
            final_video
        ),
        "thumbnail_file": str(
            thumbnail_file
        )
    }

    info_file = (
        OUTPUT_DIR
        / "video_info.json"
    )

    save_json(
        info_file,
        info
    )

    # --------------------------------------------------------
    # Pexels credit
    # --------------------------------------------------------

    credit_file = (
        OUTPUT_DIR
        / "pexels_credit.txt"
    )

    with open(
        credit_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "Pexels video sources\n"
            "====================\n\n"
        )

        for source in pexels_sources:

            f.write(
                f"Topic: {source['topic']}\n"
            )

            f.write(
                f"Video ID: "
                f"{source['video_id']}\n"
            )

            f.write(
                f"Photographer: "
                f"{source['photographer']}\n"
            )

            f.write(
                f"Page: "
                f"{source['url']}\n\n"
            )

    # --------------------------------------------------------
    # Irassutoya compatibility file
    # --------------------------------------------------------
    #
    # 今回はPexels素材を使用。
    # YAMLのartifact対象にあるためファイルだけ作る。
    # --------------------------------------------------------

    irasutoya_file = (
        OUTPUT_DIR
        / "irasutoya_sources.json"
    )

    save_json(
        irasutoya_file,
        {
            "used": False,
            "sources": [],
            "note": (
                "This version uses Pexels video/photo "
                "assets instead of Irassutoya assets."
            )
        }
    )

    # --------------------------------------------------------
    # Manifest
    # --------------------------------------------------------

    manifest_file = (
        OUTPUT_DIR
        / "generation_manifest.json"
    )

    save_json(
        manifest_file,
        {
            "version": "2026.09",
            "topics_count": len(
                topics
            ),
            "duration_seconds": get_duration(
                final_video
            ),
            "voice": VOICE,
            "voice_rate": VOICE_RATE,
            "resolution": (
                f"{WIDTH}x{HEIGHT}"
            ),
            "fps": FPS,
            "pexels_videos": pexels_sources,
        }
    )

    # --------------------------------------------------------
    # Final checks
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "FINAL CHECK"
    )
    print("=" * 70)

    required_files = [
        final_video,
        thumbnail_file,
        title_file,
        info_file,
        irasutoya_file,
    ]

    for file in required_files:

        if not file.exists():

            raise RuntimeError(
                f"必要ファイルがありません: "
                f"{file}"
            )

        print(
            "OK:",
            file,
            f"{file.stat().st_size / 1024 / 1024:.2f} MB"
        )

    final_duration = get_duration(
        final_video
    )

    print()
    print("=" * 70)
    print(
        "LONG VIDEO GENERATION COMPLETE"
    )
    print("=" * 70)

    print(
        f"Duration: "
        f"{final_duration:.2f}s"
    )

    print(
        f"Duration: "
        f"{final_duration / 60:.2f} minutes"
    )

    print(
        "Video:",
        final_video
    )

    print(
        "Thumbnail:",
        thumbnail_file
    )

    print(
        "Title:",
        title
    )

    print(
        "Video info:",
        info_file
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
