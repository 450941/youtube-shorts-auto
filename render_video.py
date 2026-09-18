# ============================================================
# LONG VIDEO GENERATOR
# 5-MINUTE TRIVIA + PSYCHOLOGY + ENCOURAGEMENT
#
# Version: 2026.09 MULTI-CUT
#
# 改良版
# - 自然な日本語
# - 1テーマ複数Pexels動画
# - 約3～5秒ごとに映像切替
# - 1文ごとのTTS時間から字幕生成
# - 強化サムネイル
# - 15問構成
# ============================================================

import os
import re
import json
import random
import asyncio
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

TARGET_DURATION = 300

# ------------------------------------------------------------
# 音声
# ------------------------------------------------------------

VOICE = "ja-JP-NanamiNeural"

# 現在の聞きやすさを維持
VOICE_RATE = "-3%"

# ------------------------------------------------------------
# Pexels
# ------------------------------------------------------------

PEXELS_API_KEY = os.environ.get(
    "PEXELS_API_KEY",
    ""
).strip()

PEXELS_VIDEO_URL = (
    "https://api.pexels.com/videos/search"
)

PEXELS_PHOTO_URL = (
    "https://api.pexels.com/v1/search"
)

PEXELS_HEADERS = {
    "Authorization": PEXELS_API_KEY
}

# ------------------------------------------------------------
# 映像テンポ
# ------------------------------------------------------------

MIN_CLIP_DURATION = 3.2
MAX_CLIP_DURATION = 5.2

# 1テーマにつき最低3種類
MIN_VIDEOS_PER_TOPIC = 3

# 1テーマにつき最大5種類
MAX_VIDEOS_PER_TOPIC = 5


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(".")

MEDIA_DIR = BASE_DIR / "media"
VOICE_DIR = MEDIA_DIR / "voice"
VIDEO_DIR = MEDIA_DIR / "cuts"
SUBTITLE_DIR = MEDIA_DIR / "subtitles"

OUTPUT_DIR = BASE_DIR / "output"

CACHE_DIR = BASE_DIR / "cache"

for directory in [
    MEDIA_DIR,
    VOICE_DIR,
    VIDEO_DIR,
    SUBTITLE_DIR,
    OUTPUT_DIR,
    CACHE_DIR,
]:
    directory.mkdir(
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
# 「雑学を読むだけ」にならないように、
#
# フック
# ↓
# 意外な事実
# ↓
# 理由
# ↓
# 日常へのつながり
# ↓
# 一言
#
# の流れにする。
#
# query はPexels用。
# visual_queries はテーマごとの映像切り替え用。
# thumbnail_text はサムネ用。
# ============================================================

FACTS = [

    # ========================================================
    # 心理
    # ========================================================

    {
        "id": "psych_first_impression",
        "category": "心理",
        "title": "第一印象",

        "fact": (
            "人は最初に受けた印象を、その後の判断の基準にしやすいんです。"
        ),

        "explanation": (
            "たとえば最初に「この人は優しそう」と思うと、その後の行動まで好意的に見てしまうことがあります。"
        ),

        "lesson": (
            "第一印象は大切。でも、最初の数秒だけで相手を決めつけないことも大切です。"
        ),

        "query": "people meeting conversation",

        "visual_queries": [
            "people meeting first time",
            "friends talking face",
            "person smiling conversation",
            "people making eye contact",
            "friendly people talking",
        ],

        "thumbnail_text": "第一印象は\n数秒で決まる？",
    },

    {
        "id": "psych_name_memory",
        "category": "心理",
        "title": "名前を呼ばれる",

        "fact": (
            "自分の名前は、周りが騒がしくても気づきやすい情報です。"
        ),

        "explanation": (
            "自分に関係する情報を、脳が重要なものとして扱いやすいからです。"
        ),

        "lesson": (
            "会話では、相手の名前を自然に呼ぶだけでも記憶に残るきっかけになります。"
        ),

        "query": "friends talking smiling",

        "visual_queries": [
            "friends talking",
            "people conversation",
            "person listening",
            "friends smiling",
            "people greeting",
        ],

        "thumbnail_text": "なぜ自分の名前は\nすぐ聞こえる？",
    },

    {
        "id": "psych_choice",
        "category": "心理",
        "title": "選択肢が多すぎる",

        "fact": (
            "選択肢は多ければ多いほど、決めやすくなるわけではありません。"
        ),

        "explanation": (
            "候補が増えると比較することも増えて、決めるための負担が大きくなります。"
        ),

        "lesson": (
            "迷ったときは、候補を三つくらいまで絞ると考えやすくなります。"
        ),

        "query": "person choosing shopping products",

        "visual_queries": [
            "shopping choices",
            "person choosing product",
            "shopping store",
            "person thinking decision",
            "online shopping phone",
        ],

        "thumbnail_text": "選択肢が多いほど\n迷う理由",
    },

    {
        "id": "psych_music_mood",
        "category": "心理",
        "title": "音楽と記憶",

        "fact": (
            "昔の曲を聞いた瞬間、当時の記憶がよみがえることがあります。"
        ),

        "explanation": (
            "音楽は、そのときの感情や出来事と一緒に記憶されることがあるからです。"
        ),

        "lesson": (
            "気分を変えたいときに、好きな曲を一曲だけ流すのも一つの方法です。"
        ),

        "query": "person listening music headphones",

        "visual_queries": [
            "person headphones",
            "music listening",
            "person remembering",
            "happy person music",
            "headphones close up",
        ],

        "thumbnail_text": "なぜ昔の曲で\n記憶が戻る？",
    },

    {
        "id": "psych_smile",
        "category": "心理",
        "title": "笑顔",

        "fact": (
            "人は相手の表情から、相手の感情を読み取ろうとします。"
        ),

        "explanation": (
            "だから明るい表情を見ていると、自分の気分や反応まで変わることがあります。"
        ),

        "lesson": (
            "無理に笑う必要はありませんが、自然な笑顔は会話のきっかけになります。"
        ),

        "query": "friends laughing together",

        "visual_queries": [
            "friends laughing",
            "happy people smiling",
            "friends conversation",
            "person smiling close up",
            "people having fun",
        ],

        "thumbnail_text": "笑顔を見ると\n気分まで変わる？",
    },

    # ========================================================
    # 脳
    # ========================================================

    {
        "id": "brain_sleep_memory",
        "category": "脳",
        "title": "睡眠と記憶",

        "fact": (
            "寝ている間も、脳は起きている間に得た情報を整理しています。"
        ),

        "explanation": (
            "睡眠中には記憶に関係するさまざまな脳の働きが続いています。"
        ),

        "lesson": (
            "何かを覚えたいなら、勉強だけでなく睡眠まで含めて考えることが大切です。"
        ),

        "query": "person sleeping bedroom",

        "visual_queries": [
            "person sleeping",
            "bedroom night",
            "peaceful sleep",
            "morning waking up",
            "person relaxing bed",
        ],

        "thumbnail_text": "寝ている間に\n脳は何をしてる？",
    },

    {
        "id": "brain_attention",
        "category": "脳",
        "title": "注意力",

        "fact": (
            "人は目の前にある情報を、全部同じように意識しているわけではありません。"
        ),

        "explanation": (
            "脳は大量の情報の中から、重要だと判断したものに注意を向けます。"
        ),

        "lesson": (
            "集中したいときは、スマホなど注意を奪うものを視界から外すだけでも環境を変えられます。"
        ),

        "query": "person focused working laptop",

        "visual_queries": [
            "person focused laptop",
            "person studying",
            "office concentration",
            "smartphone distraction",
            "focused person desk",
        ],

        "thumbnail_text": "集中できないのは\n脳のせい？",
    },

    {
        "id": "brain_habit",
        "category": "脳",
        "title": "習慣",

        "fact": (
            "同じ行動を繰り返すと、少しずつ意識しなくても行いやすくなります。"
        ),

        "explanation": (
            "同じ状況で同じ行動を続けることで、その行動への負担が小さくなっていくからです。"
        ),

        "lesson": (
            "大きな目標より、まず一分だけ始めるほうが続けるきっかけを作りやすくなります。"
        ),

        "query": "person morning routine",

        "visual_queries": [
            "morning routine",
            "person brushing teeth",
            "person exercising morning",
            "person making coffee",
            "daily routine",
        ],

        "thumbnail_text": "習慣はなぜ\n続いてしまう？",
    },

    # ========================================================
    # 人体
    # ========================================================

    {
        "id": "body_yawn",
        "category": "人体",
        "title": "あくび",

        "fact": (
            "あくびは、眠いときだけに起こるものではありません。"
        ),

        "explanation": (
            "退屈しているときや、緊張が変化するときなどにも起こります。"
        ),

        "lesson": (
            "だから誰かがあくびをしても、必ずしも話をつまらないと思っているとは限りません。"
        ),

        "query": "person tired yawning",

        "visual_queries": [
            "person yawning",
            "tired person",
            "sleepy person",
            "person bored",
            "morning tired",
        ],

        "thumbnail_text": "あくびは\n眠いだけじゃない？",
    },

    {
        "id": "body_heartbeat",
        "category": "人体",
        "title": "緊張すると心臓が速くなる",

        "fact": (
            "大事な場面で緊張すると、心臓が速く動くのを感じます。"
        ),

        "explanation": (
            "体が活動に備える反応によって、心拍数などが変化するためです。"
        ),

        "lesson": (
            "緊張するのは弱さではなく、体が準備している反応とも考えられます。"
        ),

        "query": "person nervous presentation",

        "visual_queries": [
            "nervous presentation",
            "person public speaking",
            "person nervous",
            "business presentation",
            "person taking deep breath",
        ],

        "thumbnail_text": "緊張すると\n心臓が速くなる理由",
    },

    # ========================================================
    # 日常
    # ========================================================

    {
        "id": "daily_phone",
        "category": "日常",
        "title": "スマホを何度も見る",

        "fact": (
            "通知が来ていなくても、スマホを何となく確認してしまうことがあります。"
        ),

        "explanation": (
            "新しい情報があるかもしれないという期待が、確認する行動のきっかけになることがあります。"
        ),

        "lesson": (
            "集中したい時間だけ通知を切ると、意識を戻す回数を減らせます。"
        ),

        "query": "person smartphone home",

        "visual_queries": [
            "person using smartphone",
            "smartphone notification",
            "social media phone",
            "person scrolling phone",
            "phone close up",
        ],

        "thumbnail_text": "なぜスマホを\n何度も見る？",
    },

    {
        "id": "daily_smell_memory",
        "category": "日常",
        "title": "匂いと記憶",

        "fact": (
            "ある匂いを感じた瞬間、昔の記憶がよみがえることがあります。"
        ),

        "explanation": (
            "匂いは感情や記憶に関係する脳の仕組みと強く結びつくことがあるからです。"
        ),

        "lesson": (
            "昔の場所の匂いで、一瞬だけ過去に戻ったように感じるのは不思議ですが自然な反応です。"
        ),

        "query": "person smelling coffee",

        "visual_queries": [
            "coffee smell",
            "person smelling coffee",
            "fresh coffee",
            "bakery smell",
            "person remembering",
        ],

        "thumbnail_text": "匂いだけで\n昔を思い出す理由",
    },

    # ========================================================
    # 科学
    # ========================================================

    {
        "id": "science_ice",
        "category": "科学",
        "title": "氷",

        "fact": (
            "水は凍ると、液体のときより体積が大きくなります。"
        ),

        "explanation": (
            "氷になると、水の分子が規則的な構造を作り、分子同士の間隔が広がるからです。"
        ),

        "lesson": (
            "だから水を容器いっぱいまで入れて凍らせると、容器が変形することがあります。"
        ),

        "query": "ice water glass close up",

        "visual_queries": [
            "ice cube water",
            "freezing water",
            "ice close up",
            "glass ice water",
            "snow ice macro",
        ],

        "thumbnail_text": "水は凍ると\nなぜ膨らむ？",
    },

    {
        "id": "science_sky",
        "category": "科学",
        "title": "空が青い理由",

        "fact": (
            "昼間の空が青く見えるのは、太陽の光そのものが青いからではありません。"
        ),

        "explanation": (
            "大気の中で光が散らばるとき、青い光は比較的強く散乱されるためです。"
        ),

        "lesson": (
            "夕方の空が赤く見えるのも、光が大気を通る距離と関係しています。"
        ),

        "query": "blue sky clouds sunset",

        "visual_queries": [
            "blue sky clouds",
            "bright sky",
            "clouds moving sky",
            "sunset sky",
            "dramatic clouds",
        ],

        "thumbnail_text": "空が青いのは\nなぜ？",
    },

    # ========================================================
    # 哲学・考え方
    # ========================================================

    {
        "id": "philosophy_control",
        "category": "哲学",
        "title": "コントロールできること",

        "fact": (
            "自分では変えられないことに悩み続けてしまうことがあります。"
        ),

        "explanation": (
            "他人の評価や過去の出来事は、自分の力だけでは直接変えられないからです。"
        ),

        "lesson": (
            "そんなときは、今日自分ができる小さな行動に意識を戻すと考えを整理しやすくなります。"
        ),

        "query": "person thinking peaceful nature",

        "visual_queries": [
            "person thinking nature",
            "peaceful person",
            "person looking sky",
            "walking nature",
            "calm landscape",
        ],

        "thumbnail_text": "悩みが消えないなら\nここを変える",
    },

    {
        "id": "philosophy_failure",
        "category": "哲学",
        "title": "失敗",

        "fact": (
            "同じ失敗でも、どう受け止めるかによって次の行動は変わります。"
        ),

        "explanation": (
            "終わりだと考えるのか、次に使える情報だと考えるのかで、その後の選択が変わるからです。"
        ),

        "lesson": (
            "うまくいかなかった日は、全部を否定せず、一つだけ学びを持ち帰れば十分です。"
        ),

        "query": "person overcoming challenge",

        "visual_queries": [
            "person overcoming challenge",
            "person climbing stairs",
            "runner training",
            "person standing mountain",
            "success achievement",
        ],

        "thumbnail_text": "失敗したとき\n脳で起きていること",
    },

    # ========================================================
    # 人間関係
    # ========================================================

    {
        "id": "relationship_listening",
        "category": "人間関係",
        "title": "聞く力",

        "fact": (
            "会話では、面白い話をすることだけが大切なわけではありません。"
        ),

        "explanation": (
            "話をきちんと聞いてもらうと、理解されていると感じやすくなります。"
        ),

        "lesson": (
            "話題に困ったら、無理に話を作るより相手の話を一つ深掘りする方法もあります。"
        ),

        "query": "two people talking listening",

        "visual_queries": [
            "two people talking",
            "person listening",
            "friends conversation",
            "people smiling talking",
            "close conversation",
        ],

        "thumbnail_text": "会話が上手い人は\n何をしてる？",
    },

    {
        "id": "relationship_comparison",
        "category": "人間関係",
        "title": "人と比べる",

        "fact": (
            "人は自分の状況を、周囲の人と比べて判断してしまうことがあります。"
        ),

        "explanation": (
            "自分だけを見ても、今の状態が良いのか判断しにくいからです。"
        ),

        "lesson": (
            "他人の結果だけを見て、自分の途中経過と比べると苦しくなります。"
        ),

        "query": "person looking city window",

        "visual_queries": [
            "person looking city",
            "person alone window",
            "busy city people",
            "person thinking",
            "person walking city",
        ],

        "thumbnail_text": "人と比べると\n苦しくなる理由",
    },

    # ========================================================
    # 仕事・勉強
    # ========================================================

    {
        "id": "work_start",
        "category": "仕事",
        "title": "やる気は後から",

        "fact": (
            "やる気が出てから行動するとは限りません。"
        ),

        "explanation": (
            "まず少し行動すると、そのまま集中状態に入りやすくなることがあります。"
        ),

        "lesson": (
            "やる気がない日は、五分だけやると決めて始めるのも効果的です。"
        ),

        "query": "person working desk laptop",

        "visual_queries": [
            "person working laptop",
            "person starting work",
            "study desk",
            "writing notebook",
            "productive workspace",
        ],

        "thumbnail_text": "やる気は\n待つものじゃない？",
    },

    {
        "id": "work_break",
        "category": "仕事",
        "title": "休憩",

        "fact": (
            "長時間ずっと集中し続ければ、必ず効率が上がるわけではありません。"
        ),

        "explanation": (
            "注意力や疲労は時間とともに変化するため、適切に休憩を入れることが役立ちます。"
        ),

        "lesson": (
            "休むことをサボりではなく、次の集中のための時間と考えるのも一つです。"
        ),

        "query": "person taking break coffee work",

        "visual_queries": [
            "coffee work break",
            "person relaxing office",
            "coffee desk",
            "person stretching work",
            "office break",
        ],

        "thumbnail_text": "休憩すると\n逆に集中できる？",
    },

    # ========================================================
    # 食べ物
    # ========================================================

    {
        "id": "food_spicy",
        "category": "食べ物",
        "title": "辛さ",

        "fact": (
            "唐辛子の辛さは、普通の味覚とは少し違います。"
        ),

        "explanation": (
            "カプサイシンが熱さや痛みに関係する受容体を刺激することで、辛いと感じます。"
        ),

        "lesson": (
            "だから実際には熱くなくても、辛い料理を食べると熱く感じることがあります。"
        ),

        "query": "spicy food chili peppers",

        "visual_queries": [
            "chili peppers",
            "spicy food",
            "red chili close up",
            "cooking spicy food",
            "hot sauce",
        ],

        "thumbnail_text": "辛さは\n味覚じゃない？",
    },

    # ========================================================
    # 自然
    # ========================================================

    {
        "id": "nature_rain",
        "category": "自然",
        "title": "雨の匂い",

        "fact": (
            "雨が降ったあとに、独特の匂いを感じることがあります。"
        ),

        "explanation": (
            "土や植物などに由来する物質が、雨によって空気中に広がることなどが関係しています。"
        ),

        "lesson": (
            "普段何気なく感じる雨の匂いにも、自然の化学的な仕組みが関係しています。"
        ),

        "query": "rain street nature",

        "visual_queries": [
            "rain street",
            "rain drops close up",
            "rain nature",
            "wet road rain",
            "forest rain",
        ],

        "thumbnail_text": "雨の匂いは\nどこから来る？",
    },

    # ========================================================
    # 追加雑学
    # ========================================================

    {
        "id": "daily_mirror",
        "category": "日常",
        "title": "鏡を見る時間",

        "fact": (
            "鏡を見るとき、人は自分の顔の細かい部分に意識が向きやすくなります。"
        ),

        "explanation": (
            "普段は気にしていない小さな変化まで、自分の顔だと気づきやすくなるからです。"
        ),

        "lesson": (
            "だから鏡を見た直後だけ、急に自分の顔が気になってしまうことがあります。"
        ),

        "query": "person looking mirror",

        "visual_queries": [
            "person looking mirror",
            "mirror reflection",
            "morning mirror",
            "person face mirror",
            "bathroom mirror",
        ],

        "thumbnail_text": "鏡を見ると\n顔が気になる理由",
    },

    {
        "id": "daily_coffee",
        "category": "日常",
        "title": "コーヒーの香り",

        "fact": (
            "コーヒーの香りだけで、眠気や気分が少し変わるように感じることがあります。"
        ),

        "explanation": (
            "香りは記憶や感情と結びつきやすく、飲み物を飲む前から期待感が生まれることもあります。"
        ),

        "lesson": (
            "毎朝同じ香りを感じることが、生活のスイッチになる人もいます。"
        ),

        "query": "coffee morning",

        "visual_queries": [
            "coffee morning",
            "coffee pouring",
            "coffee beans",
            "person drinking coffee",
            "coffee shop",
        ],

        "thumbnail_text": "コーヒーの香りで\n気分が変わる？",
    },

    {
        "id": "science_shadow",
        "category": "科学",
        "title": "影",

        "fact": (
            "影の形は、物そのものの形だけで決まるわけではありません。"
        ),

        "explanation": (
            "光の位置や角度が変わると、同じ物でも影の長さや形が大きく変わります。"
        ),

        "lesson": (
            "夕方に影が長くなるのは、太陽の位置が低くなるからです。"
        ),

        "query": "long shadow sunset",

        "visual_queries": [
            "long shadow",
            "sunset shadow",
            "person shadow",
            "street shadow",
            "sunlight",
        ],

        "thumbnail_text": "影が長くなる\n本当の理由",
    },

    {
        "id": "brain_multitask",
        "category": "脳",
        "title": "マルチタスク",

        "fact": (
            "人は複数のことを同時にやっているように見えても、注意を素早く切り替えていることがあります。"
        ),

        "explanation": (
            "注意できる量には限りがあるため、複雑な作業を同時に進めると効率が落ちることがあります。"
        ),

        "lesson": (
            "集中したい作業は、一つずつ片づけるほうが楽になる場合があります。"
        ),

        "query": "person multitasking laptop phone",

        "visual_queries": [
            "multitasking laptop phone",
            "busy person desk",
            "person phone laptop",
            "office busy",
            "focused work",
        ],

        "thumbnail_text": "同時にやるほど\n効率が落ちる？",
    },

]


# ============================================================
# HOOKS
# ============================================================

HOOKS = [
    "これ、たぶん一度は経験あります。",
    "実はこれ、かなり身近な話です。",
    "知っているようで、意外と知らない話です。",
    "これを知ると、少し見方が変わります。",
    "これ、あなたにも起きているかもしれません。",
    "日常の何気ない瞬間に、実はこんなことが起きています。",
    "一見普通ですが、仕組みを知ると面白い話です。",
    "これを知ると、昨日までの日常が少し違って見えます。",
]


# ============================================================
# ENCOURAGEMENT
# ============================================================

ENCOURAGEMENT = [
    "知らなかったことを一つ知るだけでも、今日は前進です。",
    "全部を変えなくても、今日一つ行動できれば十分です。",
    "小さな変化でも、積み重なると大きな違いになります。",
    "うまくいかない日があっても、それだけで終わりではありません。",
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

    used_file = (
        CACHE_DIR
        / "used_topics.json"
    )

    used = load_json(
        used_file,
        []
    )

    if not isinstance(
        used,
        list
    ):
        used = []

    available = [
        topic
        for topic in FACTS
        if topic["id"] not in used
    ]

    if len(available) < TOPICS_PER_VIDEO:

        print(
            "Topic pool exhausted. "
            "Resetting topic history."
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
        topic["id"]
        for topic in selected
    )

    used = list(
        dict.fromkeys(
            used
        )
    )

    save_json(
        used_file,
        used
    )

    return selected


# ============================================================
# SCRIPT CREATION
# ============================================================

def make_script(
    topic,
    index
):
    """
    不自然な
    「〜ということがあります」
    を使わない。

    短く区切って、
    話し言葉にする。
    """

    hook = random.choice(
        HOOKS
    )

    sentences = [

        f"第{index}問。{hook}",

        topic["fact"],

        topic["explanation"],

        topic["lesson"],

        random.choice(
            ENCOURAGEMENT
        ),
    ]

    result = []

    for sentence in sentences:

        sentence = (
            sentence
            .strip()
        )

        if not sentence:
            continue

        # 余計な空白除去
        sentence = re.sub(
            r"\s+",
            "",
            sentence
        )

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
    print(
        "Creating TTS..."
    )

    print(
        text
    )

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
        f"Audio duration: "
        f"{duration:.2f}s"
    )

    if duration <= 0:

        raise RuntimeError(
            "TTS音声の長さを取得できません: "
            f"{output_path}"
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
            PEXELS_VIDEO_URL,
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


# ============================================================
# CHOOSE VIDEO FILE
# ============================================================

def choose_video_file(
    video
):

    files = video.get(
        "video_files",
        []
    )

    if not files:
        return None

    candidates = []

    for item in files:

        width = (
            item.get("width")
            or 0
        )

        height = (
            item.get("height")
            or 0
        )

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

    # HD以上を優先
    for (
        area,
        width,
        height,
        link
    ) in candidates:

        if (
            width >= 1280
            and height >= 720
        ):

            return {
                "link": link,
                "width": width,
                "height": height
            }

    (
        area,
        width,
        height,
        link
    ) = candidates[0]

    return {
        "link": link,
        "width": width,
        "height": height
    }


# ============================================================
# GET MULTIPLE VIDEOS FOR TOPIC
# ============================================================

def get_videos_for_topic(
    topic,
    used_video_ids
):

    queries = list(
        topic.get(
            "visual_queries",
            []
        )
    )

    if not queries:

        queries = [
            topic.get(
                "query",
                ""
            )
        ]

    random.shuffle(
        queries
    )

    selected = []

    # --------------------------------------------------------
    # 各検索から動画を集める
    # --------------------------------------------------------

    for query in queries:

        if not query:
            continue

        videos = search_pexels_videos(
            query,
            per_page=15
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

            video_id = str(
                video_id
            )

            if video_id in used_video_ids:
                continue

            selected_file = (
                choose_video_file(
                    video
                )
            )

            if not selected_file:
                continue

            info = {
                "id": video_id,
                "url": selected_file[
                    "link"
                ],
                "width": selected_file[
                    "width"
                ],
                "height": selected_file[
                    "height"
                ],
                "user": video.get(
                    "user",
                    {}
                ),
                "page": video.get(
                    "url",
                    ""
                )
            }

            selected.append(
                info
            )

            used_video_ids.add(
                video_id
            )

            print(
                "Selected Pexels:",
                video_id
            )

            if len(selected) >= MAX_VIDEOS_PER_TOPIC:
                return selected

            break

        if len(selected) >= MIN_VIDEOS_PER_TOPIC:
            # 3本集まったら、
            # 残りは必要に応じて追加
            if random.random() < 0.7:
                return selected

    # --------------------------------------------------------
    # 汎用フォールバック
    # --------------------------------------------------------

    if len(selected) < MIN_VIDEOS_PER_TOPIC:

        fallback_queries = [
            "people lifestyle",
            "daily life",
            "happy people",
            "person thinking",
            "nature landscape",
        ]

        random.shuffle(
            fallback_queries
        )

        for query in fallback_queries:

            videos = search_pexels_videos(
                query,
                per_page=20
            )

            random.shuffle(
                videos
            )

            for video in videos:

                video_id = video.get(
                    "id"
                )

                if not video_id:
                    continue

                video_id = str(
                    video_id
                )

                if video_id in used_video_ids:
                    continue

                selected_file = (
                    choose_video_file(
                        video
                    )
                )

                if not selected_file:
                    continue

                info = {
                    "id": video_id,
                    "url": selected_file[
                        "link"
                    ],
                    "width": selected_file[
                        "width"
                    ],
                    "height": selected_file[
                        "height"
                    ],
                    "user": video.get(
                        "user",
                        {}
                    ),
                    "page": video.get(
                        "url",
                        ""
                    )
                }

                selected.append(
                    info
                )

                used_video_ids.add(
                    video_id
                )

                if len(selected) >= MIN_VIDEOS_PER_TOPIC:
                    break

            if len(selected) >= MIN_VIDEOS_PER_TOPIC:
                break

    # --------------------------------------------------------
    # 最低1本は必要
    # --------------------------------------------------------

    if not selected:

        raise RuntimeError(
            "Pexels動画を取得できませんでした: "
            f"{topic['title']}"
        )

    return selected


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

    url = video_info[
        "url"
    ]

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
# CALCULATE CLIP DURATIONS
# ============================================================

def calculate_clip_durations(
    total_duration,
    video_count
):

    if total_duration <= 0:
        return []

    if video_count <= 1:
        return [total_duration]

    # まず各クリップを均等化
    base = (
        total_duration
        / video_count
    )

    durations = []

    remaining = total_duration

    for index in range(
        video_count
    ):

        remaining_count = (
            video_count
            - index
        )

        if index == video_count - 1:

            duration = remaining

        else:

            # 少しだけランダムにして
            # 機械的なテンポを避ける
            variation = random.uniform(
                -0.6,
                0.6
            )

            duration = (
                base
                + variation
            )

            min_allowed = (
                MIN_CLIP_DURATION
            )

            max_allowed = (
                MAX_CLIP_DURATION
            )

            duration = max(
                min_allowed,
                duration
            )

            duration = min(
                max_allowed,
                duration
            )

            # 残り時間を考慮
            max_for_remaining = (
                remaining
                - MIN_CLIP_DURATION
                * (
                    remaining_count
                    - 1
                )
            )

            duration = min(
                duration,
                max_for_remaining
            )

        durations.append(
            duration
        )

        remaining -= duration

    # 最後が短すぎる場合
    if (
        durations
        and durations[-1]
        < 2.0
    ):

        extra = (
            2.0
            - durations[-1]
        )

        if len(durations) >= 2:

            durations[-2] -= extra
            durations[-1] += extra

    return durations


# ============================================================
# CREATE VIDEO CLIP
# ============================================================

def create_video_clip(
    source_video,
    duration,
    output_file
):

    print()
    print(
        f"Creating visual clip: "
        f"{duration:.2f}s"
    )

    vf = (
        f"scale={WIDTH}:{HEIGHT}:"
        "force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        "setsar=1,"
        "fps=30"
    )

    cmd = [
        FFMPEG,
        "-y",

        "-stream_loop",
        "-1",

        "-i",
        str(source_video),

        "-t",
        f"{duration:.3f}",

        "-an",

        "-vf",
        vf,

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

        str(output_file)
    ]

    run_command(
        cmd
    )

    if not output_file.exists():

        raise RuntimeError(
            f"映像クリップ作成失敗: "
            f"{output_file}"
        )


# ============================================================
# CONCAT VIDEO ONLY
# ============================================================

def concat_video_only(
    clip_files,
    output_file
):

    list_file = (
        VIDEO_DIR
        / f"{output_file.stem}_list.txt"
    )

    with open(
        list_file,
        "w",
        encoding="utf-8"
    ) as f:

        for clip in clip_files:

            absolute = (
                clip.resolve()
            )

            path_text = (
                str(absolute)
                .replace(
                    "'",
                    "'\\''"
                )
            )

            f.write(
                f"file '{path_text}'\n"
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
            "映像クリップ結合失敗"
        )


# ============================================================
# MUX VIDEO + AUDIO
# ============================================================

def mux_video_audio(
    video_file,
    audio_file,
    output_file
):

    audio_duration = get_duration(
        audio_file
    )

    cmd = [
        FFMPEG,
        "-y",

        "-i",
        str(video_file),

        "-i",
        str(audio_file),

        "-map",
        "0:v",

        "-map",
        "1:a",

        "-t",
        f"{audio_duration:.3f}",

        "-c:v",
        "copy",

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
            "動画と音声の結合に失敗しました"
        )


# ============================================================
# CREATE MULTI-CUT SCENE
# ============================================================

def create_multi_cut_scene(
    video_infos,
    audio_file,
    topic_index,
    topic_title
):

    topic_duration = get_duration(
        audio_file
    )

    if topic_duration <= 0:

        raise RuntimeError(
            "音声時間が取得できません"
        )

    print()
    print("=" * 60)
    print(
        f"Creating MULTI-CUT scene: "
        f"{topic_title}"
    )
    print(
        f"Duration: {topic_duration:.2f}s"
    )
    print(
        f"Videos: {len(video_infos)}"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # 使用する本数を決定
    # --------------------------------------------------------

    desired_count = int(
        round(
            topic_duration
            / 4.2
        )
    )

    desired_count = max(
        MIN_VIDEOS_PER_TOPIC,
        desired_count
    )

    desired_count = min(
        MAX_VIDEOS_PER_TOPIC,
        desired_count
    )

    # 取得できた本数を超えない
    desired_count = min(
        desired_count,
        len(video_infos)
    )

    selected_infos = list(
        video_infos[:desired_count]
    )

    random.shuffle(
        selected_infos
    )

    durations = calculate_clip_durations(
        topic_duration,
        len(selected_infos)
    )

    clip_files = []

    source_files = []

    # --------------------------------------------------------
    # 各動画をダウンロード
    # --------------------------------------------------------

    for clip_index, (
        video_info,
        clip_duration
    ) in enumerate(
        zip(
            selected_infos,
            durations
        ),
        start=1
    ):

        source_file = (
            MEDIA_DIR
            / (
                f"topic_{topic_index:02d}_"
                f"source_{clip_index:02d}.mp4"
            )
        )

        download_video(
            video_info,
            source_file
        )

        source_files.append(
            source_file
        )

        clip_file = (
            VIDEO_DIR
            / (
                f"topic_{topic_index:02d}_"
                f"clip_{clip_index:02d}.mp4"
            )
        )

        create_video_clip(
            source_file,
            clip_duration,
            clip_file
        )

        clip_files.append(
            clip_file
        )

    # --------------------------------------------------------
    # 映像結合
    # --------------------------------------------------------

    visual_video = (
        VIDEO_DIR
        / (
            f"topic_{topic_index:02d}_"
            "visual.mp4"
        )
    )

    concat_video_only(
        clip_files,
        visual_video
    )

    # --------------------------------------------------------
    # 音声を載せる
    # --------------------------------------------------------

    scene_file = (
        VIDEO_DIR
        / (
            f"scene_{topic_index:02d}.mp4"
        )
    )

    mux_video_audio(
        visual_video,
        audio_file,
        scene_file
    )

    # --------------------------------------------------------
    # クリーンアップ
    # --------------------------------------------------------

    for source in source_files:

        try:
            source.unlink()
        except Exception:
            pass

    for clip in clip_files:

        try:
            clip.unlink()
        except Exception:
            pass

    try:
        visual_video.unlink()
    except Exception:
        pass

    try:
        (
            VIDEO_DIR
            / (
                f"{visual_video.stem}_list.txt"
            )
        ).unlink()
    except Exception:
        pass

    return scene_file


# ============================================================
# SRT
# ============================================================

def format_srt_time(
    seconds
):

    if seconds < 0:
        seconds = 0

    total_seconds = int(
        seconds
    )

    millis = int(
        round(
            (
                seconds
                - total_seconds
            ) * 1000
        )
    )

    if millis >= 1000:

        total_seconds += 1
        millis = 0

    hours = (
        total_seconds
        // 3600
    )

    minutes = (
        total_seconds
        % 3600
    ) // 60

    secs = (
        total_seconds
        % 60
    )

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

        start = entry[
            "start"
        ]

        end = entry[
            "end"
        ]

        text = entry[
            "text"
        ]

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
            "[a0][a1]"
            "amix=inputs=2:"
            "duration=longest,"
            "afade=t=in:st=0:d=2,"
            f"afade=t=out:"
            f"st={max(duration - 3, 0)}:"
            "d=3"
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

    downloaded = (
        MEDIA_DIR
        / "bgm.ogg"
    )

    fallback = (
        MEDIA_DIR
        / "bgm_fallback.m4a"
    )

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
# BURN SUBTITLES + BGM
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

    subtitle_path = str(
        subtitle_file.resolve()
    )

    subtitle_path = (
        subtitle_path
        .replace(
            "\\",
            "\\\\"
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
# PEXELS PHOTO
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

            image_url = (
                src.get(
                    "original"
                )
                or src.get(
                    "large2x"
                )
                or src.get(
                    "large"
                )
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
        "NotoSansCJK-Bold.ttc",

        "/usr/share/fonts/opentype/noto/"
        "NotoSansCJK-Regular.ttc",

        "/usr/share/fonts/truetype/"
        "noto/NotoSansCJK-Bold.ttc",

        "/usr/share/fonts/truetype/"
        "noto/NotoSansCJK-Regular.ttc",

        "/usr/share/fonts/truetype/"
        "dejavu/"
        "DejaVuSans-Bold.ttf",
    ]

    for font in candidates:

        path = Path(
            font
        )

        if path.exists():
            return str(path)

    return None


# ============================================================
# TEXT WRAP
# ============================================================

def draw_centered_multiline(
    draw,
    text,
    font,
    center_x,
    top_y,
    fill,
    stroke_width=0,
    stroke_fill=None,
    line_spacing=20
):

    lines = text.split(
        "\n"
    )

    heights = []

    for line in lines:

        box = draw.textbbox(
            (0, 0),
            line,
            font=font,
            stroke_width=stroke_width
        )

        heights.append(
            box[3] - box[1]
        )

    total_height = (
        sum(heights)
        + line_spacing
        * (
            len(lines)
            - 1
        )
    )

    current_y = (
        top_y
        - total_height / 2
    )

    for line, height in zip(
        lines,
        heights
    ):

        box = draw.textbbox(
            (0, 0),
            line,
            font=font,
            stroke_width=stroke_width
        )

        text_width = (
            box[2]
            - box[0]
        )

        x = (
            center_x
            - text_width / 2
        )

        draw.text(
            (
                int(x),
                int(current_y)
            ),
            line,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill
        )

        current_y += (
            height
            + line_spacing
        )


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
        "Creating HIGH IMPACT thumbnail..."
    )

    image = Image.open(
        photo_file
    ).convert(
        "RGB"
    )

    # --------------------------------------------------------
    # COVER CROP
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # IMAGE ENHANCEMENT
    # --------------------------------------------------------

    image = ImageEnhance.Contrast(
        image
    ).enhance(
        1.18
    )

    image = ImageEnhance.Color(
        image
    ).enhance(
        1.12
    )

    image = ImageEnhance.Sharpness(
        image
    ).enhance(
        1.18
    )

    # --------------------------------------------------------
    # DARK LEFT GRADIENT
    # --------------------------------------------------------

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

    for x in range(
        THUMB_WIDTH
    ):

        ratio = (
            x
            / THUMB_WIDTH
        )

        alpha = int(
            210
            * max(
                0,
                1 - ratio * 1.45
            )
        )

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

    # --------------------------------------------------------
    # FONT
    # --------------------------------------------------------

    font_path = find_font()

    if font_path:

        huge_font = ImageFont.truetype(
            font_path,
            250
        )

        medium_font = ImageFont.truetype(
            font_path,
            145
        )

        small_font = ImageFont.truetype(
            font_path,
            82
        )

    else:

        huge_font = (
            ImageFont.load_default()
        )

        medium_font = (
            ImageFont.load_default()
        )

        small_font = (
            ImageFont.load_default()
        )

    # --------------------------------------------------------
    # BADGE
    # --------------------------------------------------------

    badge_text = (
        "実は知らない"
    )

    badge_box = (
        170,
        150,
        1050,
        350
    )

    draw.rounded_rectangle(
        badge_box,
        radius=45,
        fill=(
            255,
            230,
            70,
            255
        )
    )

    draw.text(
        (
            220,
            185
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

    # --------------------------------------------------------
    # MAIN HOOK
    # --------------------------------------------------------

    thumbnail_text = topic.get(
        "thumbnail_text",
        f"{topic['title']}\n知ってる？"
    )

    draw_centered_multiline(
        draw,
        thumbnail_text,
        huge_font,
        850,
        1030,
        fill=(
            255,
            255,
            255,
            255
        ),
        stroke_width=10,
        stroke_fill=(
            0,
            0,
            0,
            230
        ),
        line_spacing=45
    )

    # --------------------------------------------------------
    # SMALL TOPIC
    # --------------------------------------------------------

    category_text = (
        f"【{topic['category']}】"
    )

    draw.text(
        (
            190,
            1660
        ),
        category_text,
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
            220
        )
    )

    # --------------------------------------------------------
    # BOTTOM TEXT
    # --------------------------------------------------------

    bottom_text = (
        "知ると日常がちょっと面白い"
    )

    draw.text(
        (
            195,
            1870
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
            200
        )
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    image = image.convert(
        "RGB"
    )

    image.save(
        output_file,
        "JPEG",
        quality=95,
        optimize=True
    )

    print(
        "Thumbnail created:",
        output_file
    )


# ============================================================
# TITLE
# ============================================================

def create_title(
    topic
):

    patterns = [

        f"【知らないと面白い】{topic['title']}の意外な雑学15選",

        f"知ると日常が変わって見える雑学15選【{topic['title']}】",

        "実は知らない人が多い身近な雑学15選",

        "知ってるようで知らない雑学15選",

        f"「え、そうなの？」となる雑学15選【{topic['title']}】",
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
    print(
        "MULTI-CUT EDITION"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # API KEY
    # --------------------------------------------------------

    if not PEXELS_API_KEY:

        raise RuntimeError(
            "PEXELS_API_KEY がありません"
        )

    # --------------------------------------------------------
    # CLEAN
    # --------------------------------------------------------

    print()
    print(
        "Cleaning old generated files..."
    )

    for path in VOICE_DIR.glob("*"):

        if path.is_file():

            try:
                path.unlink()
            except Exception:
                pass

    for path in VIDEO_DIR.glob("*"):

        if path.is_file():

            try:
                path.unlink()
            except Exception:
                pass

    for path in SUBTITLE_DIR.glob("*"):

        if path.is_file():

            try:
                path.unlink()
            except Exception:
                pass

    # --------------------------------------------------------
    # TOPICS
    # --------------------------------------------------------

    topics = select_topics()

    print()
    print(
        "Selected topics:"
    )

    for index, topic in enumerate(
        topics,
        start=1
    ):

        print(
            f"{index:02d}. "
            f"[{topic['category']}] "
            f"{topic['title']}"
        )

    # --------------------------------------------------------
    # SCRIPTS
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

        print()
        print(
            f"--- SCRIPT {index} ---"
        )

        for sentence in script:

            print(
                sentence
            )

    # --------------------------------------------------------
    # PROCESS
    # --------------------------------------------------------

    subtitle_entries = []

    global_time = 0.0

    used_video_ids = set()

    scene_files = []

    pexels_sources = []

    # --------------------------------------------------------
    # TOPICS
    # --------------------------------------------------------

    for topic_index, item in enumerate(
        all_scripts,
        start=1
    ):

        topic = item[
            "topic"
        ]

        print()
        print("=" * 70)
        print(
            f"TOPIC "
            f"{topic_index}/"
            f"{TOPICS_PER_VIDEO}"
        )
        print(
            topic["title"]
        )
        print("=" * 70)

        topic_audio_files = []

        topic_start = (
            global_time
        )

        # ----------------------------------------------------
        # TTS
        # ----------------------------------------------------

        for sentence_index, sentence in enumerate(
            item["sentences"],
            start=1
        ):

            audio_file = (
                VOICE_DIR
                / (
                    f"topic_"
                    f"{topic_index:02d}_"
                    f"{sentence_index:02d}.mp3"
                )
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
                    "end": (
                        global_time
                        + duration
                    ),
                    "text": sentence
                }
            )

            global_time += duration

        # ----------------------------------------------------
        # MERGE AUDIO
        # ----------------------------------------------------

        topic_audio = (
            VOICE_DIR
            / (
                f"topic_"
                f"{topic_index:02d}.mp3"
            )
        )

        concat_file = (
            VOICE_DIR
            / (
                f"topic_"
                f"{topic_index:02d}.txt"
            )
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

                escaped = (
                    str(absolute)
                    .replace(
                        "'",
                        "'\\''"
                    )
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
        # MULTIPLE PEXELS VIDEOS
        # ----------------------------------------------------

        video_infos = get_videos_for_topic(
            topic,
            used_video_ids
        )

        print()
        print(
            f"Selected {len(video_infos)} "
            f"Pexels videos for "
            f"{topic['title']}"
        )

        # ----------------------------------------------------
        # CREDIT
        # ----------------------------------------------------

        for video_info in video_infos:

            pexels_sources.append(
                {
                    "topic": topic["title"],
                    "video_id": video_info[
                        "id"
                    ],
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
        # CREATE MULTI-CUT SCENE
        # ----------------------------------------------------

        scene_file = (
            create_multi_cut_scene(
                video_infos,
                topic_audio,
                topic_index,
                topic["title"]
            )
        )

        scene_files.append(
            scene_file
        )

        # ----------------------------------------------------
        # TOPIC DURATION
        # ----------------------------------------------------

        topic_duration = (
            global_time
            - topic_start
        )

        print()
        print(
            f"Topic duration: "
            f"{topic_duration:.2f}s"
        )

    # ========================================================
    # TOTAL
    # ========================================================

    total_duration = (
        global_time
    )

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
    # CONCAT SCENES
    # --------------------------------------------------------

    concatenated = (
        MEDIA_DIR
        / "concatenated.mp4"
    )

    concat_scenes = (
        VIDEO_DIR
        / "all_scenes.txt"
    )

    with open(
        concat_scenes,
        "w",
        encoding="utf-8"
    ) as f:

        for scene in scene_files:

            absolute = (
                scene.resolve()
            )

            escaped = (
                str(absolute)
                .replace(
                    "'",
                    "'\\''"
                )
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
            str(concat_scenes),

            "-c",
            "copy",

            str(concatenated)
        ]
    )

    if not concatenated.exists():

        raise RuntimeError(
            "動画結合に失敗しました"
        )

    # --------------------------------------------------------
    # SUBTITLE
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

    actual_video_duration = (
        get_duration(
            concatenated
        )
    )

    bgm_file = prepare_bgm(
        actual_video_duration
    )

    # --------------------------------------------------------
    # FINAL VIDEO
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

    # ========================================================
    # THUMBNAIL
    # ========================================================

    thumbnail_queries = [

        # 1問目専用
        topics[0].get(
            "query",
            ""
        ),

        # 強い人物系
        "surprised person thinking",

        "curious person looking camera",

        "shocked surprised face",

        "person reacting surprised",
    ]

    photo_info = None

    for query in thumbnail_queries:

        if not query:
            continue

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

    # ========================================================
    # TITLE
    # ========================================================

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

    # ========================================================
    # DESCRIPTION
    # ========================================================

    description = (
        "身近なのに意外と知らない雑学を15個紹介します。\n"
        "心理学、脳、人体、日常、科学、哲学など、"
        "普段の生活でちょっと気になる話をまとめました。\n\n"
        "知っているだけで、日常の見え方が少し変わるかもしれません。\n"
        "気になった話があれば、ぜひ最後まで見てみてください。\n\n"
        "#雑学 #豆知識 #心理学 #面白い話 #日常 #科学"
    )

    # ========================================================
    # VIDEO INFO
    # ========================================================

    info = {

        "title": title,

        "description": description,

        "category": "27",

        "topics": [

            {
                "number": i,
                "id": topic["id"],
                "category": topic[
                    "category"
                ],
                "title": topic[
                    "title"
                ]
            }

            for i, topic in enumerate(
                topics,
                start=1
            )
        ],

        "duration_seconds": (
            get_duration(
                final_video
            )
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

    # ========================================================
    # PEXELS CREDIT
    # ========================================================

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
        )

        f.write(
            "====================\n\n"
        )

        for source in pexels_sources:

            f.write(
                f"Topic: "
                f"{source['topic']}\n"
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

    # ========================================================
    # IRASUTOYA COMPATIBILITY
    # ========================================================

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
                "This version uses "
                "multiple Pexels video/photo "
                "assets instead of Irassutoya assets."
            )
        }
    )

    # ========================================================
    # MANIFEST
    # ========================================================

    manifest_file = (
        OUTPUT_DIR
        / "generation_manifest.json"
    )

    save_json(
        manifest_file,
        {

            "version": (
                "2026.09-multi-cut"
            ),

            "topics_count": len(
                topics
            ),

            "duration_seconds": (
                get_duration(
                    final_video
                )
            ),

            "voice": VOICE,

            "voice_rate": VOICE_RATE,

            "resolution": (
                f"{WIDTH}x{HEIGHT}"
            ),

            "fps": FPS,

            "clip_duration_range": [
                MIN_CLIP_DURATION,
                MAX_CLIP_DURATION
            ],

            "pexels_videos": (
                pexels_sources
            ),
        }
    )

    # ========================================================
    # FINAL CHECK
    # ========================================================

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
                "必要ファイルがありません: "
                f"{file}"
            )

        print(
            "OK:",
            file,
            f"{file.stat().st_size / 1024 / 1024:.2f} MB"
        )

    final_duration = (
        get_duration(
            final_video
        )
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

    print(
        "Pexels clips used:",
        len(pexels_sources)
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
