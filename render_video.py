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


# =========================================================
# SETTINGS
# =========================================================

WIDTH = 1920
HEIGHT = 1080

THUMB_WIDTH = 3840
THUMB_HEIGHT = 2160

FPS = 30

TOPICS_PER_VIDEO = 15

VOICE = "ja-JP-NanamiNeural"
VOICE_RATE = "-3%"

PEXELS_API_KEY = os.environ.get(
    "PEXELS_API_KEY",
    ""
).strip()

REQUEST_TIMEOUT = 30

BASE_DIR = Path(".")

MEDIA_DIR = BASE_DIR / "media"
AUDIO_DIR = MEDIA_DIR / "audio"
VIDEO_DIR = MEDIA_DIR / "video"

CACHE_DIR = BASE_DIR / "cache"

OUTPUT_DIR = BASE_DIR / "output"

USED_TOPICS_FILE = (
    CACHE_DIR / "used_topics.json"
)

USED_VIDEOS_FILE = (
    CACHE_DIR / "used_pexels_videos.json"
)

VIDEO_SEARCH_CACHE = (
    CACHE_DIR / "pexels_video_cache.json"
)

PHOTO_SEARCH_CACHE = (
    CACHE_DIR / "pexels_photo_cache.json"
)

FINAL_VIDEO = (
    OUTPUT_DIR / "final_video.mp4"
)

THUMBNAIL = (
    OUTPUT_DIR / "thumbnail.jpg"
)

TITLE_FILE = (
    OUTPUT_DIR / "title.txt"
)

CREDIT_FILE = (
    OUTPUT_DIR / "pexels_credit.txt"
)


for directory in [
    MEDIA_DIR,
    AUDIO_DIR,
    VIDEO_DIR,
    CACHE_DIR,
    OUTPUT_DIR,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True
    )


# =========================================================
# BASIC FUNCTIONS
# =========================================================

def run_command(
    command,
    check=True
):

    print(
        "\n$ " +
        " ".join(
            str(x)
            for x in command
        )
    )

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print(
        result.stdout[-5000:]
    )

    if check and result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n" +
            " ".join(
                str(x)
                for x in command
            )
        )

    return result


def load_json(
    path,
    default
):

    if not path.exists():
        return default

    try:

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception:

        return default


def save_json(
    path,
    data
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def get_duration(path):

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path)
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:

        return float(
            result.stdout.strip()
        )

    except Exception:

        return 0.0


def find_font():

    candidates = [

        "/usr/share/fonts/opentype/noto/"
        "NotoSansCJK-Bold.ttc",

        "/usr/share/fonts/opentype/noto/"
        "NotoSansCJK-Regular.ttc",

        "/usr/share/fonts/truetype/noto/"
        "NotoSansCJK-Bold.ttf",

        "/usr/share/fonts/truetype/noto/"
        "NotoSansCJK-Regular.ttf",

    ]

    for font in candidates:

        if Path(font).exists():

            return font

    return None


# =========================================================
# TOPIC BANK
#
# 100ベーステーマ × 10視点
# = 最大1000パターン
# =========================================================

BASE_TOPICS = [

    (
        "心理",
        "なぜ人は他人の目を気にするのか",
        [
            "person thinking",
            "worried person",
            "people talking",
            "social interaction"
        ]
    ),

    (
        "心理",
        "なぜ失敗すると何度も思い出してしまうのか",
        [
            "sad person thinking",
            "person remembering",
            "worried person",
            "thinking man"
        ]
    ),

    (
        "心理",
        "なぜ褒められると嬉しくなるのか",
        [
            "happy person",
            "smiling person",
            "people talking",
            "celebration"
        ]
    ),

    (
        "心理",
        "なぜ嫌な記憶ほど残りやすいのか",
        [
            "person thinking",
            "memory",
            "sad person",
            "deep thinking"
        ]
    ),

    (
        "心理",
        "なぜ人は比較してしまうのか",
        [
            "people comparison",
            "person using smartphone",
            "social media",
            "thinking person"
        ]
    ),

    (
        "心理",
        "なぜ緊張すると手が震えるのか",
        [
            "nervous person",
            "anxious person",
            "business meeting",
            "worried man"
        ]
    ),

    (
        "心理",
        "なぜ初対面では緊張するのか",
        [
            "first meeting",
            "people meeting",
            "nervous person",
            "conversation"
        ]
    ),

    (
        "心理",
        "なぜ笑い声につられて笑ってしまうのか",
        [
            "friends laughing",
            "people laughing",
            "happy friends",
            "smiling people"
        ]
    ),

    (
        "心理",
        "なぜ好きな人のことばかり考えてしまうのか",
        [
            "romantic couple",
            "person thinking",
            "love",
            "young couple"
        ]
    ),

    (
        "心理",
        "なぜ人は秘密を知りたくなるのか",
        [
            "curious person",
            "secret",
            "mysterious person",
            "thinking person"
        ]
    ),

    (
        "脳",
        "なぜあくびはうつるのか",
        [
            "yawning person",
            "sleepy person",
            "tired person",
            "people yawning"
        ]
    ),

    (
        "脳",
        "なぜ夢を見るのか",
        [
            "sleeping person",
            "dream",
            "bedroom night",
            "sleep"
        ]
    ),

    (
        "脳",
        "なぜ眠いと集中できなくなるのか",
        [
            "sleepy person working",
            "tired office worker",
            "sleepy student",
            "person tired"
        ]
    ),

    (
        "脳",
        "なぜ寝不足だとイライラしやすいのか",
        [
            "tired person",
            "angry person",
            "sleep deprived",
            "exhausted worker"
        ]
    ),

    (
        "脳",
        "なぜ昔の曲を聞くと記憶がよみがえるのか",
        [
            "person listening music",
            "headphones",
            "nostalgia",
            "music listener"
        ]
    ),

    (
        "脳",
        "なぜ名前を忘れてしまうのか",
        [
            "confused person",
            "thinking person",
            "forgetful person",
            "memory"
        ]
    ),

    (
        "脳",
        "なぜ勉強すると疲れるのか",
        [
            "student studying",
            "tired student",
            "books",
            "studying desk"
        ]
    ),

    (
        "脳",
        "なぜ時間が早く感じる日と遅く感じる日があるのか",
        [
            "clock",
            "person thinking",
            "time",
            "waiting person"
        ]
    ),

    (
        "脳",
        "なぜ同じことを繰り返すと飽きるのか",
        [
            "bored person",
            "tired person",
            "repetition",
            "office worker"
        ]
    ),

    (
        "脳",
        "なぜ集中すると周りが見えなくなるのか",
        [
            "focused person",
            "person working",
            "concentration",
            "office worker"
        ]
    ),

    (
        "人体",
        "なぜ炭酸飲料を飲むとげっぷが出るのか",
        [
            "person drinking soda",
            "soda bottle",
            "carbonated drink",
            "glass soda"
        ]
    ),

    (
        "人体",
        "なぜ辛いものを食べると汗が出るのか",
        [
            "person eating spicy food",
            "spicy food",
            "sweating person",
            "hot food"
        ]
    ),

    (
        "人体",
        "なぜ寒いと鳥肌が立つのか",
        [
            "cold person",
            "winter person",
            "cold weather",
            "person outside winter"
        ]
    ),

    (
        "人体",
        "なぜ運動すると息が上がるのか",
        [
            "running person",
            "runner breathing",
            "exercise",
            "fitness"
        ]
    ),

    (
        "人体",
        "なぜ疲れると眠くなるのか",
        [
            "tired person",
            "sleepy person",
            "person sleeping",
            "bed"
        ]
    ),

    (
        "人体",
        "なぜ緊張すると汗をかくのか",
        [
            "nervous person",
            "sweating person",
            "anxious person",
            "stress"
        ]
    ),

    (
        "人体",
        "なぜ目を閉じると眠りやすくなるのか",
        [
            "person sleeping",
            "closed eyes",
            "bedroom",
            "sleep"
        ]
    ),

    (
        "人体",
        "なぜ水を飲むと喉の渇きが落ち着くのか",
        [
            "person drinking water",
            "water glass",
            "drinking water",
            "hydration"
        ]
    ),

    (
        "人体",
        "なぜ運動後に心臓が速く動くのか",
        [
            "runner",
            "exercise person",
            "fitness",
            "running"
        ]
    ),

    (
        "人体",
        "なぜ長時間スマホを見ると目が疲れるのか",
        [
            "person using smartphone",
            "tired eyes",
            "smartphone",
            "phone screen"
        ]
    ),

    (
        "日常",
        "なぜ電子レンジは食べ物を温められるのか",
        [
            "microwave kitchen",
            "person cooking",
            "kitchen appliance",
            "food microwave"
        ]
    ),

    (
        "日常",
        "なぜ氷は水に浮くのか",
        [
            "ice water",
            "glass ice",
            "ice cube",
            "cold drink"
        ]
    ),

    (
        "日常",
        "なぜ雨の日は眠く感じることがあるのか",
        [
            "rain window",
            "sleepy person",
            "rainy day",
            "bedroom rain"
        ]
    ),

    (
        "日常",
        "なぜシャワーを浴びるとスッキリするのか",
        [
            "person shower",
            "shower water",
            "bathroom",
            "relaxing shower"
        ]
    ),

    (
        "日常",
        "なぜ朝は起きるのがつらいのか",
        [
            "person waking up",
            "alarm clock",
            "sleepy person",
            "morning bed"
        ]
    ),

    (
        "日常",
        "なぜ夜になると考え事が増えるのか",
        [
            "person thinking at night",
            "night bedroom",
            "person alone",
            "night smartphone"
        ]
    ),

    (
        "日常",
        "なぜ部屋を片付けると気分が変わるのか",
        [
            "cleaning room",
            "organized room",
            "person cleaning",
            "tidy home"
        ]
    ),

    (
        "日常",
        "なぜ香りで昔の記憶を思い出すのか",
        [
            "smelling flowers",
            "perfume person",
            "memory",
            "person smelling"
        ]
    ),

    (
        "日常",
        "なぜ人は時計を何度も確認するのか",
        [
            "person checking clock",
            "wristwatch",
            "smartphone time",
            "waiting person"
        ]
    ),

    (
        "日常",
        "なぜ待ち時間は長く感じるのか",
        [
            "person waiting",
            "waiting room",
            "clock waiting",
            "bored person"
        ]
    ),

    (
        "科学",
        "なぜ空は青く見えるのか",
        [
            "blue sky",
            "person looking sky",
            "clouds sky",
            "nature sky"
        ]
    ),

    (
        "科学",
        "なぜ夕焼けは赤く見えるのか",
        [
            "sunset",
            "red sky",
            "person watching sunset",
            "sunset landscape"
        ]
    ),

    (
        "科学",
        "なぜ虹が見えるのか",
        [
            "rainbow",
            "person looking rainbow",
            "rain sky",
            "nature rainbow"
        ]
    ),

    (
        "科学",
        "なぜ雷が光ってから音が聞こえるのか",
        [
            "lightning storm",
            "thunderstorm",
            "storm sky",
            "person watching storm"
        ]
    ),

    (
        "科学",
        "なぜ海は青く見えるのか",
        [
            "blue ocean",
            "person beach",
            "ocean water",
            "sea waves"
        ]
    ),

    (
        "科学",
        "なぜ植物は太陽の方向へ伸びるのか",
        [
            "plants sunlight",
            "plant growing",
            "sunlight plant",
            "person gardening"
        ]
    ),

    (
        "科学",
        "なぜ金属は冷たく感じるのか",
        [
            "metal object",
            "person touching metal",
            "cold metal",
            "hand metal"
        ]
    ),

    (
        "科学",
        "なぜ水滴は丸くなるのか",
        [
            "water droplets",
            "rain drop",
            "water closeup",
            "droplets"
        ]
    ),

    (
        "科学",
        "なぜシャボン玉は虹色に見えるのか",
        [
            "soap bubbles",
            "rainbow bubbles",
            "bubbles closeup",
            "person bubbles"
        ]
    ),

    (
        "科学",
        "なぜ熱い飲み物から湯気が出るのか",
        [
            "hot coffee",
            "steam coffee",
            "tea cup",
            "hot drink"
        ]
    ),

    (
        "哲学",
        "自分とは何なのか",
        [
            "person mirror",
            "thinking person",
            "reflection",
            "philosophy person"
        ]
    ),

    (
        "哲学",
        "自由とは何なのか",
        [
            "person outdoors",
            "freedom person",
            "open sky",
            "person landscape"
        ]
    ),

    (
        "哲学",
        "幸せとは何なのか",
        [
            "happy person",
            "smiling person",
            "friends happiness",
            "joy"
        ]
    ),

    (
        "哲学",
        "なぜ人は意味を求めるのか",
        [
            "person thinking",
            "deep thinking",
            "person looking sky",
            "philosophy"
        ]
    ),

    (
        "哲学",
        "なぜ人は未来を不安に感じるのか",
        [
            "worried person",
            "future thinking",
            "anxious person",
            "person looking horizon"
        ]
    ),

    (
        "哲学",
        "なぜ過去を変えられないのに考えてしまうのか",
        [
            "nostalgia person",
            "person remembering",
            "old photos",
            "thinking person"
        ]
    ),

    (
        "哲学",
        "もし時間を戻せたら人生は変わるのか",
        [
            "clock person",
            "time concept",
            "person thinking",
            "old clock"
        ]
    ),

    (
        "哲学",
        "完璧を目指すと苦しくなるのはなぜか",
        [
            "stressed person",
            "perfectionist",
            "worried worker",
            "person working"
        ]
    ),

    (
        "哲学",
        "なぜ人は正解を探してしまうのか",
        [
            "person thinking",
            "choice person",
            "decision",
            "confused person"
        ]
    ),

    (
        "哲学",
        "本当に自分で選んでいると言えるのか",
        [
            "person choosing",
            "decision person",
            "thinking person",
            "choices"
        ]
    ),

    (
        "SNS",
        "なぜSNSを見ると時間が早く過ぎるのか",
        [
            "person smartphone",
            "social media phone",
            "phone scrolling",
            "smartphone user"
        ]
    ),

    (
        "SNS",
        "なぜ通知が来ると確認したくなるのか",
        [
            "phone notification",
            "person checking phone",
            "smartphone notification",
            "phone user"
        ]
    ),

    (
        "SNS",
        "なぜ他人の楽しそうな投稿が気になるのか",
        [
            "social media person",
            "happy person smartphone",
            "phone scrolling",
            "social media"
        ]
    ),

    (
        "SNS",
        "なぜ既読が気になってしまうのか",
        [
            "person texting",
            "messaging smartphone",
            "waiting phone",
            "phone message"
        ]
    ),

    (
        "SNS",
        "なぜ短い動画は次々見てしまうのか",
        [
            "person watching smartphone",
            "short video phone",
            "scrolling smartphone",
            "phone user"
        ]
    ),

    (
        "SNS",
        "なぜコメント欄を読んでしまうのか",
        [
            "person reading smartphone",
            "social media comments",
            "phone scrolling",
            "smartphone user"
        ]
    ),

    (
        "SNS",
        "なぜ数字が多い投稿ほど気になるのか",
        [
            "social media smartphone",
            "phone numbers",
            "person phone",
            "social media user"
        ]
    ),

    (
        "SNS",
        "なぜSNSを見た後に疲れることがあるのか",
        [
            "tired smartphone user",
            "person phone tired",
            "social media fatigue",
            "exhausted person"
        ]
    ),

    (
        "SNS",
        "なぜ知らない人の生活が気になるのか",
        [
            "person using phone",
            "social media",
            "smartphone user",
            "curious person"
        ]
    ),

    (
        "SNS",
        "なぜ通知音に反応してしまうのか",
        [
            "phone notification",
            "person hearing phone",
            "smartphone alert",
            "phone user"
        ]
    ),

    (
        "食べ物",
        "なぜ甘いものを食べたくなるのか",
        [
            "person eating dessert",
            "sweet food",
            "dessert person",
            "cake eating"
        ]
    ),

    (
        "食べ物",
        "なぜ空腹だとイライラしやすいのか",
        [
            "hungry person",
            "hungry angry person",
            "food person",
            "hungry"
        ]
    ),

    (
        "食べ物",
        "なぜ熱い料理はおいしく感じるのか",
        [
            "hot food",
            "person eating",
            "restaurant food",
            "cooking"
        ]
    ),

    (
        "食べ物",
        "なぜ冷たい飲み物がおいしく感じるのか",
        [
            "cold drink",
            "ice drink",
            "person drinking",
            "summer drink"
        ]
    ),

    (
        "食べ物",
        "なぜコーヒーを飲むと眠気が減るのか",
        [
            "person drinking coffee",
            "coffee office",
            "coffee cup",
            "tired person coffee"
        ]
    ),

    (
        "食べ物",
        "なぜポップコーンは映画館で食べたくなるのか",
        [
            "popcorn movie",
            "person eating popcorn",
            "cinema popcorn",
            "movie theater"
        ]
    ),

    (
        "食べ物",
        "なぜ香ばしい匂いでお腹が空くのか",
        [
            "cooking food",
            "food aroma",
            "person cooking",
            "restaurant food"
        ]
    ),

    (
        "食べ物",
        "なぜ炭酸飲料は刺激的に感じるのか",
        [
            "soda drinking",
            "carbonated drink",
            "soda bottle",
            "person drinking soda"
        ]
    ),

    (
        "食べ物",
        "なぜ辛い食べ物がクセになるのか",
        [
            "spicy food person",
            "eating spicy food",
            "hot food",
            "spicy meal"
        ]
    ),

    (
        "食べ物",
        "なぜ食後に眠くなるのか",
        [
            "sleepy after eating",
            "person eating",
            "sleepy person",
            "meal person"
        ]
    ),

    (
        "人間関係",
        "なぜ第一印象は強く残るのか",
        [
            "first impression",
            "people meeting",
            "business meeting",
            "person portrait"
        ]
    ),

    (
        "人間関係",
        "なぜ親しい人ほど気を使わなくなるのか",
        [
            "friends talking",
            "close friends",
            "friends laughing",
            "people conversation"
        ]
    ),

    (
        "人間関係",
        "なぜ沈黙が気まずく感じるのか",
        [
            "awkward silence",
            "two people talking",
            "nervous person",
            "conversation"
        ]
    ),

    (
        "人間関係",
        "なぜ目を合わせると緊張するのか",
        [
            "eye contact",
            "conversation",
            "nervous person",
            "people talking"
        ]
    ),

    (
        "人間関係",
        "なぜ人は同じ趣味の人に親近感を持つのか",
        [
            "friends hobby",
            "friends talking",
            "people hobby",
            "friends laughing"
        ]
    ),

    (
        "人間関係",
        "なぜ謝るのが難しいのか",
        [
            "apologizing person",
            "sad person",
            "conversation",
            "relationship"
        ]
    ),

    (
        "人間関係",
        "なぜありがとうと言われると嬉しいのか",
        [
            "happy people",
            "thank you conversation",
            "smiling person",
            "friends"
        ]
    ),

    (
        "人間関係",
        "なぜ人は表情から感情を読み取るのか",
        [
            "facial expression",
            "human face",
            "conversation",
            "emotion"
        ]
    ),

    (
        "人間関係",
        "なぜ共感されると安心するのか",
        [
            "friends talking",
            "supportive conversation",
            "comfort person",
            "friends"
        ]
    ),

    (
        "人間関係",
        "なぜ人は孤独を感じるのか",
        [
            "lonely person",
            "person alone",
            "sad person",
            "night alone"
        ]
    ),

    (
        "仕事",
        "なぜ先延ばししてしまうのか",
        [
            "procrastination",
            "person smartphone office",
            "lazy worker",
            "office worker"
        ]
    ),

    (
        "仕事",
        "なぜ締切直前になると集中できるのか",
        [
            "deadline worker",
            "focused office worker",
            "computer worker",
            "office work"
        ]
    ),

    (
        "仕事",
        "なぜ同時に色々やると疲れるのか",
        [
            "busy office worker",
            "stressed worker",
            "multitasking",
            "office computer"
        ]
    ),

    (
        "仕事",
        "なぜ休憩すると頭がスッキリするのか",
        [
            "office break",
            "coffee break",
            "relaxed worker",
            "office worker"
        ]
    ),

    (
        "仕事",
        "なぜ朝のほうが集中しやすい人がいるのか",
        [
            "morning worker",
            "morning office",
            "focused person",
            "coffee office"
        ]
    ),

    (
        "仕事",
        "なぜ机が散らかると集中しにくいのか",
        [
            "messy desk",
            "office desk",
            "stressed worker",
            "cluttered desk"
        ]
    ),

    (
        "仕事",
        "なぜ一度気が散ると戻りにくいのか",
        [
            "distracted worker",
            "smartphone office",
            "office worker",
            "concentration"
        ]
    ),

    (
        "仕事",
        "なぜ目標を紙に書くと意識しやすいのか",
        [
            "writing goals",
            "notebook goals",
            "person writing",
            "goal planning"
        ]
    ),

    (
        "仕事",
        "なぜ小さな達成感がやる気につながるのか",
        [
            "happy worker",
            "successful person",
            "achievement",
            "smiling worker"
        ]
    ),

    (
        "仕事",
        "なぜ疲れると判断が雑になるのか",
        [
            "tired worker",
            "exhausted office worker",
            "stress worker",
            "tired person"
        ]
    ),

    (
        "自然",
        "なぜ雲は空に浮いているのか",
        [
            "clouds sky",
            "person looking sky",
            "blue sky",
            "cloud landscape"
        ]
    ),

    (
        "自然",
        "なぜ風が吹くのか",
        [
            "wind trees",
            "person outdoors",
            "wind nature",
            "trees moving wind"
        ]
    ),

    (
        "自然",
        "なぜ雪は白いのか",
        [
            "snow landscape",
            "person snow",
            "winter snow",
            "snow nature"
        ]
    ),

    (
        "自然",
        "なぜ葉っぱは緑色なのか",
        [
            "green leaves",
            "plant closeup",
            "person gardening",
            "green nature"
        ]
    ),

    (
        "自然",
        "なぜ海には波があるのか",
        [
            "ocean waves",
            "person beach",
            "sea waves",
            "ocean landscape"
        ]
    ),

    (
        "自然",
        "なぜ朝日を見ると気持ちが変わるのか",
        [
            "sunrise person",
            "person watching sunrise",
            "morning nature",
            "sunrise"
        ]
    ),

    (
        "自然",
        "なぜ夜空には星が見えるのか",
        [
            "night sky stars",
            "person looking stars",
            "milky way",
            "stars night"
        ]
    ),

    (
        "自然",
        "なぜ月の形は変わって見えるのか",
        [
            "moon night",
            "person looking moon",
            "night sky",
            "moon"
        ]
    ),

    (
        "自然",
        "なぜ虹は雨上がりに見えるのか",
        [
            "rainbow after rain",
            "rainbow sky",
            "person rainbow",
            "rain nature"
        ]
    ),

    (
        "自然",
        "なぜ秋になると葉が色づくのか",
        [
            "autumn leaves",
            "person autumn",
            "fall nature",
            "red leaves"
        ]
    ),
]


ANGLES = [
    "意外な理由",
    "科学的な理由",
    "脳の仕組み",
    "身近な生活との関係",
    "知られざる理由",
    "意外な共通点",
    "人間の本能との関係",
    "日常で起きている仕組み",
    "知ると見方が変わる理由",
    "実は身近な理由",
]


def build_topic_bank():

    bank = []

    for base_index, (
        category,
        title,
        queries
    ) in enumerate(
        BASE_TOPICS
    ):

        for angle_index, angle in enumerate(
            ANGLES
        ):

            bank.append(
                {
                    "id": (
                        f"{base_index:03d}_"
                        f"{angle_index:02d}"
                    ),

                    "category": category,

                    "title": title,

                    "angle": angle,

                    "queries": queries,
                }
            )

    return bank


TOPIC_BANK = build_topic_bank()


# =========================================================
# TOPIC SELECT
# =========================================================

def select_topics():

    used = load_json(
        USED_TOPICS_FILE,
        []
    )

    used_set = set(
        used
    )

    unused = [
        topic
        for topic in TOPIC_BANK
        if topic["id"]
        not in used_set
    ]

    if len(unused) < TOPICS_PER_VIDEO:

        print(
            "1000パターンを一巡。"
            "使用履歴を整理して再利用します。"
        )

        used = []

        unused = TOPIC_BANK.copy()

    random.shuffle(
        unused
    )

    selected = []

    category_count = {}

    for topic in unused:

        category = topic[
            "category"
        ]

        count = category_count.get(
            category,
            0
        )

        if count >= 3:
            continue

        selected.append(
            topic
        )

        category_count[
            category
        ] = count + 1

        if len(selected) >= TOPICS_PER_VIDEO:
            break

    if len(selected) < TOPICS_PER_VIDEO:

        for topic in unused:

            if topic not in selected:

                selected.append(
                    topic
                )

            if len(selected) >= TOPICS_PER_VIDEO:
                break

    used.extend(
        topic["id"]
        for topic in selected
    )

    save_json(
        USED_TOPICS_FILE,
        used[-1000:]
    )

    return selected


# =========================================================
# SCRIPT
# =========================================================

def make_script(topic):

    title = topic[
        "title"
    ]

    angle = topic[
        "angle"
    ]

    templates = [

        f"""
知っているようで、
実はちゃんと理由を知らない疑問。

今回のテーマは、
「{title}」です。

これ、普段は当たり前すぎて
気にすることもありません。

でも少し考えてみると、
「そもそも、なぜ？」となりますよね。

実はここには、
{angle}が関係しています。

私たちは毎日の生活の中で、
この現象を何度も経験しています。

ところが仕組みを知ると、
いつもの光景が少し違って見えてきます。

つまり、
身近なことほど、
意外な理由が隠れているんです。

知っているだけで得をする知識ではありません。

でも、
知っていると誰かに話したくなる。

そんな身近な雑学です。
""".strip(),

        f"""
今日の疑問は、
「{title}」。

一見すると、
当たり前に思える現象です。

ところが実際には、
ちゃんとした理由があります。

ポイントになるのは、
{angle}です。

私たちの体や脳、
そして普段の生活には、
思っている以上に面白い仕組みがあります。

この仕組みを知ると、
次に同じ場面を見たとき、
「あ、これのことか」と
気づくかもしれません。

普段何気なく見ているものにも、
実は小さな謎がたくさんあります。

今回はその一つを、
分かりやすく見ていきましょう。
""".strip(),
    ]

    return random.choice(
        templates
    )


# =========================================================
# TTS
# =========================================================

async def create_tts(
    text,
    output
):

    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate=VOICE_RATE
    )

    await communicate.save(
        str(output)
    )


def generate_audio(
    text,
    output
):

    asyncio.run(
        create_tts(
            text,
            output
        )
    )


# =========================================================
# PEXELS VIDEO SEARCH
# =========================================================

def search_pexels_videos(
    query
):

    cache = load_json(
        VIDEO_SEARCH_CACHE,
        {}
    )

    cache_key = hashlib.md5(
        query.encode(
            "utf-8"
        )
    ).hexdigest()

    if cache_key in cache:

        return cache[
            cache_key
        ]

    headers = {
        "Authorization":
            PEXELS_API_KEY,

        "User-Agent":
            "Mozilla/5.0"
    }

    response = requests.get(
        "https://api.pexels.com/v1/videos/search",
        headers=headers,
        params={
            "query": query,
            "orientation": "landscape",
            "size": "medium",
            "locale": "en-US",
            "per_page": 40,
        },
        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()

    videos = response.json().get(
        "videos",
        []
    )

    cache[
        cache_key
    ] = videos

    save_json(
        VIDEO_SEARCH_CACHE,
        cache
    )

    return videos


def choose_video(
    topic,
    used_video_ids
):

    all_results = []

    queries = list(
        topic["queries"]
    )

    random.shuffle(
        queries
    )

    for query in queries:

        try:

            results = search_pexels_videos(
                query
            )

            all_results.extend(
                results
            )

        except Exception as e:

            print(
                "Pexels動画検索失敗:",
                query,
                e
            )

    unique = {}

    for video in all_results:

        video_id = str(
            video.get("id")
        )

        if not video_id:
            continue

        if video_id in used_video_ids:
            continue

        unique[
            video_id
        ] = video

    candidates = []

    for video in unique.values():

        files = video.get(
            "video_files",
            []
        )

        good_files = []

        for file in files:

            width = file.get(
                "width",
                0
            )

            height = file.get(
                "height",
                0
            )

            if (
                width >= 1280
                and height >= 720
            ):

                good_files.append(
                    file
                )

        if not good_files:
            continue

        good_files.sort(
            key=lambda x:
                x.get(
                    "width",
                    0
                )
        )

        selected_file = (
            good_files[-1]
        )

        candidates.append(
            {
                "id": video.get(
                    "id"
                ),

                "url": selected_file.get(
                    "link"
                ),

                "width":
                    selected_file.get(
                        "width",
                        0
                    ),

                "height":
                    selected_file.get(
                        "height",
                        0
                    )
            }
        )

    if not candidates:

        raise RuntimeError(
            "Pexels動画が見つかりません: "
            + topic["title"]
        )

    selected = random.choice(
        candidates[
            :min(
                20,
                len(candidates)
            )
        ]
    )

    used_video_ids.add(
        str(
            selected["id"]
        )
    )

    return selected


def download_file(
    url,
    output
):

    response = requests.get(
        url,
        headers={
            "User-Agent":
                "Mozilla/5.0"
        },
        timeout=REQUEST_TIMEOUT,
        stream=True
    )

    response.raise_for_status()

    with open(
        output,
        "wb"
    ) as file:

        for chunk in response.iter_content(
            1024 * 1024
        ):

            if chunk:
                file.write(
                    chunk
                )


# =========================================================
# VIDEO SCENE
# =========================================================

def create_scene(
    video,
    audio,
    output,
    duration
):

    filter_complex = (
        f"[0:v]"
        f"scale={WIDTH}:{HEIGHT}:"
        "force_original_aspect_ratio=decrease,"
        f"pad={WIDTH}:{HEIGHT}:"
        "(ow-iw)/2:(oh-ih)/2,"
        f"fps={FPS},"
        "setsar=1,"
        "format=yuv420p[v]"
    )

    run_command(
        [
            "ffmpeg",
            "-y",

            "-stream_loop",
            "-1",

            "-i",
            str(video),

            "-i",
            str(audio),

            "-filter_complex",
            filter_complex,

            "-map",
            "[v]",

            "-map",
            "1:a",

            "-t",
            str(duration),

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-crf",
            "23",

            "-c:a",
            "aac",

            "-b:a",
            "128k",

            "-shortest",

            str(output)
        ]
    )


# =========================================================
# SUBTITLE
# =========================================================

def split_text(
    text,
    max_chars=20
):

    text = re.sub(
        r"\s+",
        "",
        text
    )

    chunks = []

    while len(text) > max_chars:

        cut = max_chars

        for mark in [
            "。",
            "、",
            "！",
            "？"
        ]:

            position = text.rfind(
                mark,
                0,
                max_chars
            )

            if position > 5:

                cut = (
                    position +
                    1
                )

                break

        chunks.append(
            text[:cut]
        )

        text = text[
            cut:
        ]

    if text:

        chunks.append(
            text
        )

    return chunks


def timestamp(
    seconds
):

    milliseconds = int(
        (seconds % 1) *
        1000
    )

    total = int(
        seconds
    )

    sec = total % 60

    minute = (
        total // 60
    ) % 60

    hour = (
        total // 3600
    )

    return (
        f"{hour:02d}:"
        f"{minute:02d}:"
        f"{sec:02d},"
        f"{milliseconds:03d}"
    )


def create_srt(
    items,
    output
):

    lines = []

    index = 1

    current_time = 0.0

    for item in items:

        text = item[
            "text"
        ]

        duration = item[
            "duration"
        ]

        chunks = split_text(
            text
        )

        if not chunks:
            continue

        chunk_duration = (
            duration /
            len(chunks)
        )

        for chunk in chunks:

            start = current_time

            end = (
                current_time +
                chunk_duration
            )

            lines.append(
                str(index)
            )

            lines.append(
                timestamp(start)
                + " --> "
                + timestamp(end)
            )

            lines.append(
                chunk
            )

            lines.append("")

            current_time = end

            index += 1

    output.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )


# =========================================================
# BGM
# =========================================================

def create_bgm(
    duration,
    output
):

    run_command(
        [
            "ffmpeg",
            "-y",

            "-f",
            "lavfi",

            "-i",
            "sine=frequency=220:"
            "sample_rate=44100",

            "-f",
            "lavfi",

            "-i",
            "sine=frequency=330:"
            "sample_rate=44100",

            "-filter_complex",

            "[0:a]volume=0.025[a0];"
            "[1:a]volume=0.018[a1];"
            "[a0][a1]"
            "amix=inputs=2:"
            "duration=longest,"
            "lowpass=f=1000",

            "-t",
            str(duration),

            "-c:a",
            "aac",

            "-b:a",
            "96k",

            str(output)
        ]
    )


# =========================================================
# CONCAT
# =========================================================

def concat_scenes(
    scenes,
    output
):

    list_file = (
        MEDIA_DIR /
        "concat.txt"
    )

    with open(
        list_file,
        "w",
        encoding="utf-8"
    ) as file:

        for scene in scenes:

            path = (
                scene
                .resolve()
                .as_posix()
            )

            file.write(
                "file '"
                + path.replace(
                    "'",
                    "'\\''"
                )
                + "'\n"
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
            str(list_file),

            "-c",
            "copy",

            str(output)
        ]
    )


# =========================================================
# FINAL VIDEO
# =========================================================

def add_subtitles_and_bgm(
    video,
    srt,
    bgm,
    output
):

    subtitle_path = (
        str(srt)
        .replace(
            "\\",
            "/"
        )
        .replace(
            ":",
            "\\:"
        )
        .replace(
            "'",
            "\\'"
        )
    )

    subtitle_filter = (
        "subtitles="
        f"'{subtitle_path}':"
        "force_style="
        "'FontName=Noto Sans CJK JP,"
        "FontSize=20,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=3,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=55'"
    )

    run_command(
        [
            "ffmpeg",
            "-y",

            "-i",
            str(video),

            "-i",
            str(bgm),

            "-filter_complex",

            f"[0:v]"
            f"{subtitle_filter}"
            "[v];"
            "[1:a]"
            "volume=0.06"
            "[bgm];"
            "[0:a]"
            "volume=1.0"
            "[voice];"
            "[voice][bgm]"
            "amix=inputs=2:"
            "duration=first:"
            "dropout_transition=2"
            "[a]",

            "-map",
            "[v]",

            "-map",
            "[a]",

            "-c:v",
            "libx264",

            "-preset",
            "medium",

            "-crf",
            "21",

            "-c:a",
            "aac",

            "-b:a",
            "160k",

            "-movflags",
            "+faststart",

            str(output)
        ]
    )


# =========================================================
# PEXELS PHOTO SEARCH
# =========================================================

def search_pexels_photos(
    query
):

    cache = load_json(
        PHOTO_SEARCH_CACHE,
        {}
    )

    cache_key = hashlib.md5(
        query.encode(
            "utf-8"
        )
    ).hexdigest()

    if cache_key in cache:

        return cache[
            cache_key
        ]

    headers = {
        "Authorization":
            PEXELS_API_KEY,

        "User-Agent":
            "Mozilla/5.0"
    }

    response = requests.get(
        "https://api.pexels.com/v1/search",
        headers=headers,
        params={
            "query": query,

            "orientation":
                "landscape",

            "size":
                "large",

            "locale":
                "en-US",

            "per_page":
                40
        },

        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()

    photos = response.json().get(
        "photos",
        []
    )

    cache[
        cache_key
    ] = photos

    save_json(
        PHOTO_SEARCH_CACHE,
        cache
    )

    return photos


# =========================================================
# REAL PERSON THUMBNAIL SEARCH
# =========================================================

def get_thumbnail_queries(
    topic
):

    category = topic[
        "category"
    ]

    mapping = {

        "心理": [
            "surprised person portrait",
            "thinking person portrait",
            "confused person face",
            "worried person portrait",
            "shocked person"
        ],

        "脳": [
            "thinking person portrait",
            "confused person",
            "surprised person portrait",
            "sleepy person",
            "thoughtful person"
        ],

        "人体": [
            "surprised person",
            "person drinking",
            "person eating",
            "healthy person portrait",
            "shocked person"
        ],

        "日常": [
            "surprised person portrait",
            "thinking person",
            "confused person",
            "person reaction",
            "curious person"
        ],

        "科学": [
            "scientist portrait",
            "curious person",
            "surprised scientist",
            "thinking person",
            "science person"
        ],

        "哲学": [
            "deep thinking person",
            "thoughtful person portrait",
            "person looking sky",
            "thinking man",
            "thinking woman"
        ],

        "SNS": [
            "surprised person smartphone",
            "person looking phone",
            "shocked person phone",
            "smartphone user portrait",
            "person using smartphone"
        ],

        "食べ物": [
            "surprised person eating",
            "person eating food",
            "happy person food",
            "person drinking",
            "food reaction"
        ],

        "人間関係": [
            "people talking portrait",
            "surprised person",
            "friends talking",
            "conversation person",
            "human reaction"
        ],

        "仕事": [
            "business person portrait",
            "office worker surprised",
            "thinking businessman",
            "stressed worker",
            "business woman portrait"
        ],

        "自然": [
            "person looking sky",
            "person looking nature",
            "surprised person outdoors",
            "person looking stars",
            "person sunset"
        ],
    }

    return mapping.get(
        category,
        [
            "surprised person portrait",
            "thinking person portrait",
            "curious person"
        ]
    )


def choose_thumbnail_photo(
    topic
):

    queries = get_thumbnail_queries(
        topic
    )

    random.shuffle(
        queries
    )

    candidates = []

    for query in queries:

        try:

            photos = search_pexels_photos(
                query
            )

            candidates.extend(
                photos
            )

        except Exception as e:

            print(
                "サムネ人物検索エラー:",
                query,
                e
            )

    if not candidates:

        raise RuntimeError(
            "Pexels人物写真を取得できませんでした。"
        )

    unique = {}

    for photo in candidates:

        photo_id = str(
            photo.get(
                "id",
                ""
            )
        )

        if photo_id:

            unique[
                photo_id
            ] = photo

    scored = []

    for photo in unique.values():

        width = photo.get(
            "width",
            0
        )

        height = photo.get(
            "height",
            0
        )

        score = 0

        # 横長
        if width > height:
            score += 10

        # 高解像度
        if width >= 2500:
            score += 10

        if width >= 3500:
            score += 5

        alt = (
            photo.get(
                "alt",
                ""
            )
            or ""
        ).lower()

        for word in [
            "person",
            "people",
            "man",
            "woman",
            "portrait",
            "face",
            "thinking",
            "surprised",
            "shocked",
            "phone",
        ]:

            if word in alt:

                score += 3

        # ランダム性
        score += random.randint(
            0,
            10
        )

        scored.append(
            (
                score,
                photo
            )
        )

    scored.sort(
        key=lambda x:
            x[0],
        reverse=True
    )

    top = [
        photo
        for _, photo
        in scored[:20]
    ]

    return random.choice(
        top
    )


def download_photo(
    photo,
    output
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

        raise RuntimeError(
            "Pexels写真URLがありません。"
        )

    response = requests.get(
        url,
        headers={
            "User-Agent":
                "Mozilla/5.0"
        },
        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()

    with open(
        output,
        "wb"
    ) as file:

        file.write(
            response.content
        )


# =========================================================
# THUMBNAIL IMAGE PROCESSING
# =========================================================

def crop_to_fill(
    image,
    width,
    height
):

    source_ratio = (
        image.width /
        image.height
    )

    target_ratio = (
        width /
        height
    )

    if source_ratio > target_ratio:

        new_height = height

        new_width = int(
            height *
            source_ratio
        )

    else:

        new_width = width

        new_height = int(
            width /
            source_ratio
        )

    image = image.resize(
        (
            new_width,
            new_height
        ),
        Image.Resampling.LANCZOS
    )

    left = (
        new_width -
        width
    ) // 2

    top = (
        new_height -
        height
    ) // 2

    return image.crop(
        (
            left,
            top,
            left + width,
            top + height
        )
    )


def make_thumbnail(
    topic
):

    print(
        "\n"
        "======================================"
    )

    print(
        "リアル人物サムネイル生成"
    )

    print(
        "======================================"
    )

    photo = choose_thumbnail_photo(
        topic
    )

    print(
        "Pexels Photo ID:",
        photo.get("id")
    )

    print(
        "Photographer:",
        photo.get(
            "photographer"
        )
    )

    photo_file = (
        MEDIA_DIR /
        "thumbnail_person.jpg"
    )

    download_photo(
        photo,
        photo_file
    )

    person = Image.open(
        photo_file
    ).convert(
        "RGB"
    )

    # -----------------------------------------
    # キャンバス
    # -----------------------------------------

    canvas = Image.new(
        "RGB",
        (
            THUMB_WIDTH,
            THUMB_HEIGHT
        ),
        (
            8,
            10,
            18
        )
    )

    # -----------------------------------------
    # 人物写真を右側へ
    # -----------------------------------------

    person_height = int(
        THUMB_HEIGHT *
        1.08
    )

    person_ratio = (
        person.width /
        person.height
    )

    person_width = int(
        person_height *
        person_ratio
    )

    person = person.resize(
        (
            person_width,
            person_height
        ),
        Image.Resampling.LANCZOS
    )

    # 右側へ配置
    person_x = (
        THUMB_WIDTH -
        person_width +
        150
    )

    person_y = (
        THUMB_HEIGHT -
        person_height
    ) // 2

    # -----------------------------------------
    # 写真補正
    # -----------------------------------------

    person = ImageEnhance.Contrast(
        person
    ).enhance(
        1.12
    )

    person = ImageEnhance.Color(
        person
    ).enhance(
        1.08
    )

    person = ImageEnhance.Sharpness(
        person
    ).enhance(
        1.15
    )

    canvas.paste(
        person,
        (
            person_x,
            person_y
        )
    )

    # -----------------------------------------
    # 左側暗幕
    # -----------------------------------------

    overlay = Image.new(
        "RGBA",
        canvas.size,
        (
            0,
            0,
            0,
            0
        )
    )

    overlay_draw = ImageDraw.Draw(
        overlay
    )

    for x in range(
        THUMB_WIDTH
    ):

        if x < 2500:

            alpha = int(
                190 *
                (
                    1 -
                    x / 2500
                )
            )

        else:

            alpha = 0

        overlay_draw.line(
            [
                (
                    x,
                    0
                ),
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

    canvas = Image.alpha_composite(
        canvas.convert("RGBA"),
        overlay
    ).convert(
        "RGB"
    )

    # -----------------------------------------
    # カラーアクセント
    # -----------------------------------------

    accent = Image.new(
        "RGBA",
        canvas.size,
        (
            0,
            0,
            0,
            0
        )
    )

    accent_draw = ImageDraw.Draw(
        accent
    )

    accent_draw.ellipse(
        (
            2600,
            250,
            4100,
            1900
        ),
        fill=(
            255,
            180,
            20,
            38
        )
    )

    accent = accent.filter(
        ImageFilter.GaussianBlur(
            160
        )
    )

    canvas = Image.alpha_composite(
        canvas.convert("RGBA"),
        accent
    ).convert(
        "RGB"
    )

    draw = ImageDraw.Draw(
        canvas
    )

    # -----------------------------------------
    # フォント
    # -----------------------------------------

    font_path = find_font()

    if font_path:

        category_font = (
            ImageFont.truetype(
                font_path,
                125
            )
        )

        question_font = (
            ImageFont.truetype(
                font_path,
                180
            )
        )

        main_font = (
            ImageFont.truetype(
                font_path,
                250
            )
        )

        bottom_font = (
            ImageFont.truetype(
                font_path,
                145
            )
        )

    else:

        category_font = (
            ImageFont.load_default()
        )

        question_font = (
            ImageFont.load_default()
        )

        main_font = (
            ImageFont.load_default()
        )

        bottom_font = (
            ImageFont.load_default()
        )

    # -----------------------------------------
    # テキスト
    # -----------------------------------------

    category = topic[
        "category"
    ]

    title = topic[
        "title"
    ]

    main_text = title

    if main_text.startswith(
        "なぜ"
    ):

        main_text = (
            main_text[2:]
        )

    main_text = (
        main_text
        .replace(
            "？",
            ""
        )
        .replace(
            "。",
            ""
        )
    )

    if len(main_text) > 18:

        main_text = (
            main_text[:18]
            + "…"
        )

    # -----------------------------------------
    # カテゴリー
    # -----------------------------------------

    draw.text(
        (
            170,
            160
        ),
        f"知ると面白い {category}",
        font=category_font,
        fill=(
            255,
            220,
            45
        ),
        stroke_width=10,
        stroke_fill=(
            0,
            0,
            0
        )
    )

    # -----------------------------------------
    # 「なぜ？」
    # -----------------------------------------

    draw.text(
        (
            160,
            390
        ),
        "なぜ？",
        font=question_font,
        fill=(
            255,
            255,
            255
        ),
        stroke_width=12,
        stroke_fill=(
            0,
            0,
            0
        )
    )

    # -----------------------------------------
    # メインタイトル
    # -----------------------------------------

    if len(main_text) >= 9:

        middle = (
            len(main_text) // 2
        )

        line1 = (
            main_text[:middle]
        )

        line2 = (
            main_text[middle:]
        )

        draw.text(
            (
                150,
                650
            ),
            line1,
            font=main_font,
            fill=(
                255,
                255,
                255
            ),
            stroke_width=16,
            stroke_fill=(
                0,
                0,
                0
            )
        )

        draw.text(
            (
                150,
                970
            ),
            line2,
            font=main_font,
            fill=(
                255,
                225,
                35
            ),
            stroke_width=16,
            stroke_fill=(
                0,
                0,
                0
            )
        )

    else:

        draw.text(
            (
                150,
                780
            ),
            main_text,
            font=main_font,
            fill=(
                255,
                225,
                35
            ),
            stroke_width=16,
            stroke_fill=(
                0,
                0,
                0
            )
        )

    # -----------------------------------------
    # 下部コピー
    # -----------------------------------------

    draw.text(
        (
            170,
            1780
        ),
        "身近な雑学15選",
        font=bottom_font,
        fill=(
            255,
            255,
            255
        ),
        stroke_width=8,
        stroke_fill=(
            0,
            0,
            0
        )
    )

    # -----------------------------------------
    # 黄色ライン
    # -----------------------------------------

    draw.rounded_rectangle(
        (
            160,
            2020,
            1550,
            2060
        ),
        radius=20,
        fill=(
            255,
            220,
            40
        )
    )

    # -----------------------------------------
    # コントラスト
    # -----------------------------------------

    canvas = ImageEnhance.Contrast(
        canvas
    ).enhance(
        1.12
    )

    canvas = ImageEnhance.Sharpness(
        canvas
    ).enhance(
        1.25
    )

    # -----------------------------------------
    # 保存
    # -----------------------------------------

    canvas.save(
        THUMBNAIL,
        "JPEG",
        quality=95,
        optimize=True
    )

    # -----------------------------------------
    # Pexelsクレジット
    # -----------------------------------------

    photographer = photo.get(
        "photographer",
        "Unknown"
    )

    photo_url = photo.get(
        "url",
        ""
    )

    credit = (
        "Photo by "
        + photographer
        + " on Pexels\n"
        + photo_url
        + "\n"
        + "Photo ID: "
        + str(
            photo.get(
                "id",
                ""
            )
        )
    )

    CREDIT_FILE.write_text(
        credit,
        encoding="utf-8"
    )

    print(
        "サムネイル完成:"
    )

    print(
        THUMBNAIL
    )


# =========================================================
# TITLE
# =========================================================

def make_title(
    topics
):

    first = topics[0][
        "title"
    ]

    first = (
        first
        .replace(
            "なぜ",
            ""
        )
        .replace(
            "？",
            ""
        )
        .replace(
            "。",
            ""
        )
    )

    choices = [

        f"なぜ{first}？ 知ると面白い身近な雑学15選",

        "知らないと気になる身近な雑学15選",

        "実は理由があった！身近な雑学15選",

        "知ると見方が変わる身近な雑学15選",

    ]

    return random.choice(
        choices
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "=" * 70
    )

    print(
        "LONG VIDEO GENERATOR"
    )

    print(
        "REALISTIC PEXELS THUMBNAIL"
    )

    print(
        "=" * 70
    )

    if not PEXELS_API_KEY:

        raise RuntimeError(
            "PEXELS_API_KEY がありません。"
            "GitHub Secretsを確認してください。"
        )

    # -----------------------------------------
    # 1. TOPICS
    # -----------------------------------------

    topics = select_topics()

    print(
        "\n今回の15ネタ:"
    )

    for i, topic in enumerate(
        topics,
        1
    ):

        print(
            f"{i:02d}. "
            f"[{topic['category']}] "
            f"{topic['title']}"
        )

    # -----------------------------------------
    # 2. TITLE
    # -----------------------------------------

    title = make_title(
        topics
    )

    TITLE_FILE.write_text(
        title,
        encoding="utf-8"
    )

    print(
        "\nタイトル:"
    )

    print(
        title
    )

    # -----------------------------------------
    # 3. VIDEO
    # -----------------------------------------

    used_video_ids = set(
        load_json(
            USED_VIDEOS_FILE,
            []
        )
    )

    scenes = []

    subtitle_items = []

    for index, topic in enumerate(
        topics
    ):

        print(
            "\n"
            + "=" * 60
        )

        print(
            f"{index + 1}/"
            f"{len(topics)}"
        )

        print(
            topic["title"]
        )

        print(
            "=" * 60
        )

        # -------------------------------------
        # SCRIPT
        # -------------------------------------

        script = make_script(
            topic
        )

        # -------------------------------------
        # AUDIO
        # -------------------------------------

        audio_file = (
            AUDIO_DIR /
            f"{index:02d}.mp3"
        )

        if audio_file.exists():

            audio_file.unlink()

        generate_audio(
            script,
            audio_file
        )

        duration = get_duration(
            audio_file
        )

        print(
            f"音声時間: "
            f"{duration:.2f}秒"
        )

        # -------------------------------------
        # PEXELS VIDEO
        # -------------------------------------

        selected = choose_video(
            topic,
            used_video_ids
        )

        video_file = (
            VIDEO_DIR /
            f"{index:02d}_"
            f"{selected['id']}.mp4"
        )

        print(
            "Pexels Video ID:",
            selected["id"]
        )

        download_file(
            selected["url"],
            video_file
        )

        # -------------------------------------
        # SCENE
        # -------------------------------------

        scene_file = (
            MEDIA_DIR /
            f"scene_{index:02d}.mp4"
        )

        create_scene(
            video_file,
            audio_file,
            scene_file,
            duration
        )

        scenes.append(
            scene_file
        )

        subtitle_items.append(
            {
                "text":
                    script,

                "duration":
                    duration
            }
        )

    save_json(
        USED_VIDEOS_FILE,
        list(
            used_video_ids
        )[-500:]
    )

    # -----------------------------------------
    # 4. CONCAT
    # -----------------------------------------

    raw_video = (
        MEDIA_DIR /
        "raw_video.mp4"
    )

    concat_scenes(
        scenes,
        raw_video
    )

    # -----------------------------------------
    # 5. SUBTITLES
    # -----------------------------------------

    subtitle_file = (
        MEDIA_DIR /
        "subtitles.srt"
    )

    create_srt(
        subtitle_items,
        subtitle_file
    )

    # -----------------------------------------
    # 6. BGM
    # -----------------------------------------

    total_duration = get_duration(
        raw_video
    )

    bgm_file = (
        MEDIA_DIR /
        "bgm.m4a"
    )

    create_bgm(
        total_duration,
        bgm_file
    )

    # -----------------------------------------
    # 7. FINAL VIDEO
    # -----------------------------------------

    if FINAL_VIDEO.exists():

        FINAL_VIDEO.unlink()

    add_subtitles_and_bgm(
        raw_video,
        subtitle_file,
        bgm_file,
        FINAL_VIDEO
    )

    # -----------------------------------------
    # 8. REALISTIC THUMBNAIL
    # -----------------------------------------

    make_thumbnail(
        topics[0]
    )

    # -----------------------------------------
    # 9. CHECK
    # -----------------------------------------

    final_duration = get_duration(
        FINAL_VIDEO
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        "VIDEO:"
    )

    print(
        FINAL_VIDEO
    )

    print(
        "THUMBNAIL:"
    )

    print(
        THUMBNAIL
    )

    print(
        "TITLE:"
    )

    print(
        title
    )

    print(
        f"DURATION: "
        f"{final_duration:.1f} sec"
    )

    print(
        f"DURATION: "
        f"{final_duration / 60:.2f} min"
    )

    print(
        "PEXELS CREDIT:"
    )

    print(
        CREDIT_FILE
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()
