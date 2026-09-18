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
    ImageEnhance
)


# =========================================================
# LONG VIDEO GENERATOR
# 5-MINUTE TRIVIA + PSYCHOLOGY + PHILOSOPHY
# =========================================================


# =========================================================
# SETTINGS
# =========================================================

WIDTH = 1920
HEIGHT = 1080

THUMB_WIDTH = 3840
THUMB_HEIGHT = 2160

FPS = 30

TARGET_MINUTES = 5

TOPICS_PER_VIDEO = 15

VOICE = "ja-JP-NanamiNeural"

VOICE_RATE = "-3%"

VOICE_VOLUME = "+0%"

PEXELS_PER_PAGE = 40

MIN_VIDEO_WIDTH = 1280

VIDEO_SEARCH_PAGES = 2

RANDOM_SEED = random.randint(
    100000,
    999999999
)

random.seed(RANDOM_SEED)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(".")

MEDIA_DIR = BASE_DIR / "media"

IMAGE_DIR = MEDIA_DIR / "images"

VOICE_DIR = MEDIA_DIR / "voice"

CUT_DIR = MEDIA_DIR / "cuts"

SUBTITLE_DIR = MEDIA_DIR / "subtitles"

OUTPUT_DIR = BASE_DIR / "output"

CACHE_DIR = BASE_DIR / "cache"

USED_TOPICS_FILE = (
    CACHE_DIR / "used_topics.json"
)

USED_VIDEOS_FILE = (
    CACHE_DIR / "used_pexels_videos.json"
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

VIDEO_INFO_FILE = (
    OUTPUT_DIR / "video_info.json"
)

CREDIT_FILE = (
    OUTPUT_DIR / "pexels_credit.txt"
)

IRASUTOYA_FILE = (
    OUTPUT_DIR / "irasutoya_sources.json"
)


# =========================================================
# ENVIRONMENT
# =========================================================

PEXELS_API_KEY = (
    os.environ
    .get("PEXELS_API_KEY", "")
    .strip()
)


# =========================================================
# TOPIC DATABASE
# =========================================================

TOPICS = [

    # -----------------------------------------------------
    # 心理学
    # -----------------------------------------------------

    {
        "id": "psych_001",
        "category": "心理学",
        "keyword": "心理学",
        "title": "人はなぜ忘れようとすると余計に思い出すのか",
        "fact": (
            "忘れようと意識するほど、その対象が頭に浮かびやすくなることがあります。"
            "これは、考えないようにするために脳が対象を監視してしまうためです。"
        ),
        "hook": "「絶対に考えないで」と言われると、逆に考えてしまったことありませんか？",
        "why": "考えないようにするためには、まず「今それを考えていないか」を確認する必要があります。",
        "ending": "つまり、無理に追い出すより、いったん受け流したほうが楽になることもあるんです。"
    },

    {
        "id": "psych_002",
        "category": "心理学",
        "keyword": "スマホ",
        "title": "スマホが近くにあるだけで気が散る理由",
        "fact": (
            "スマートフォンを使っていなくても、近くにあること自体が注意資源を奪う可能性があります。"
        ),
        "hook": "スマホを机の上に置いたまま勉強してませんか？",
        "why": "通知が来るかもしれない、という期待や確認したい気持ちが、無意識に注意を使わせます。",
        "ending": "集中したいときは、画面を伏せるだけでなく、少し離してみるのも一つの方法です。"
    },

    {
        "id": "psych_003",
        "category": "心理学",
        "keyword": "選択",
        "title": "選択肢が多すぎると決められなくなる理由",
        "fact": (
            "選択肢が増えるほど、比較する情報も増え、決断に負担を感じやすくなります。"
        ),
        "hook": "メニューが多すぎて、逆に何も決められなくなったことありませんか？",
        "why": "脳は候補を一つずつ比較しようとするため、選択肢が増えるほど処理する量も増えていきます。",
        "ending": "だから迷ったときは、最初から候補を3つくらいに絞ると考えやすくなります。"
    },

    {
        "id": "psych_004",
        "category": "心理学",
        "keyword": "記憶",
        "title": "昔の失敗を何度も思い出してしまう理由",
        "fact": (
            "強く感情が動いた出来事は、普通の出来事より記憶に残りやすくなります。"
        ),
        "hook": "寝る前になると、昔の恥ずかしい記憶が突然出てくることありませんか？",
        "why": "感情の強さは記憶の形成に影響するため、重要だった出来事として残りやすいのです。",
        "ending": "その記憶が残っているからといって、あなたがずっと失敗しているという意味ではありません。"
    },

    {
        "id": "psych_005",
        "category": "心理学",
        "keyword": "第一印象",
        "title": "最初の印象が後からも影響しやすい理由",
        "fact": (
            "最初に得た情報は、その後の判断の基準になってしまうことがあります。"
        ),
        "hook": "初対面で感じた印象って、あとからなかなか変わらないですよね。",
        "why": "最初の情報を基準にして、その後の情報を解釈してしまうことがあるからです。",
        "ending": "だから第一印象は重要ですが、一度の印象だけで人を決めつけないことも大切です。"
    },

    # -----------------------------------------------------
    # 人体
    # -----------------------------------------------------

    {
        "id": "body_001",
        "category": "人体",
        "keyword": "あくび",
        "title": "あくびがうつるのはなぜ",
        "fact": (
            "人があくびをすると、それを見た人もあくびをしたくなることがあります。"
            "この現象は「伝染性あくび」と呼ばれています。"
        ),
        "hook": "今「あくび」って聞いて、ちょっとあくびしたくなりませんでした？",
        "why": "他人の行動を見たときに、自分も似た行動を起こす仕組みが関係していると考えられています。",
        "ending": "つまり、あくびは眠気だけじゃなく、人とのつながりとも関係しているかもしれません。"
    },

    {
        "id": "body_002",
        "category": "人体",
        "keyword": "鳥肌",
        "title": "怖いときに鳥肌が立つ理由",
        "fact": (
            "鳥肌は、寒さや強い感情などによって皮膚の毛が立つ反応です。"
        ),
        "hook": "怖い映画を見ていると、寒くないのに鳥肌が立つことありませんか？",
        "why": "自律神経の働きによって、皮膚の毛の根元にある小さな筋肉が収縮するためです。",
        "ending": "昔の人間にとっては体温維持などに役立った反応の名残とも考えられています。"
    },

    {
        "id": "body_003",
        "category": "人体",
        "keyword": "くしゃみ",
        "title": "くしゃみの速度が速い理由",
        "fact": (
            "くしゃみでは、鼻や口から空気を一気に外へ押し出します。"
        ),
        "hook": "くしゃみって、どうしてあんなに一瞬で出るんでしょう？",
        "why": "異物などを外へ出すため、呼吸に使う筋肉が短時間に連動して働くからです。",
        "ending": "体が勝手に行う、かなりダイナミックな防御反応なんです。"
    },

    {
        "id": "body_004",
        "category": "人体",
        "keyword": "睡眠",
        "title": "寝ている間も脳が止まらない理由",
        "fact": (
            "睡眠中も脳は活動しており、記憶の整理など重要な働きを続けています。"
        ),
        "hook": "寝ている間、脳は完全に休んでいると思っていませんか？",
        "why": "睡眠中にも神経活動は続き、起きている間とは異なる状態で情報処理が行われます。",
        "ending": "だから睡眠は「何もしない時間」ではなく、脳にとって大切な作業時間でもあるんです。"
    },

    # -----------------------------------------------------
    # 日常
    # -----------------------------------------------------

    {
        "id": "daily_001",
        "category": "日常",
        "keyword": "電子レンジ",
        "title": "電子レンジで温まり方に差が出る理由",
        "fact": (
            "電子レンジでは、食品の形や水分量、置き方などによって温まり方が変わります。"
        ),
        "hook": "同じ皿なのに、熱々の部分と冷たい部分がありませんか？",
        "why": "電磁波によるエネルギーの伝わり方や食品内部の水分分布などが関係しています。",
        "ending": "だから途中で位置を変えたり、少し置いて熱をなじませたりすると食べやすくなります。"
    },

    {
        "id": "daily_002",
        "category": "日常",
        "keyword": "氷",
        "title": "氷が水に浮くのは実は珍しい",
        "fact": (
            "水は固体の氷になると、液体の水より密度が小さくなります。"
        ),
        "hook": "普通、固体って液体よりギュッと詰まっていそうですよね。",
        "why": "氷の中では水分子が特徴的な構造を作り、液体よりすき間の多い状態になります。",
        "ending": "そのため氷は水に沈まず、表面に浮くことができます。"
    },

    {
        "id": "daily_003",
        "category": "日常",
        "keyword": "雨",
        "title": "雨の匂いを感じる理由",
        "fact": (
            "雨が降る前後に感じる独特の匂いには、土壌由来の物質などが関係しています。"
        ),
        "hook": "雨が降りそうなとき、なんとなく匂いで分かることありませんか？",
        "why": "雨によって地面の物質が空気中へ移動し、鼻に届きやすくなることがあります。",
        "ending": "天気の変化を、私たちは目だけでなく鼻でも感じ取っているんです。"
    },

    {
        "id": "daily_004",
        "category": "日常",
        "keyword": "お風呂",
        "title": "お風呂に入ると眠くなる理由",
        "fact": (
            "入浴による体温変化は、眠気と関係する体のリズムに影響します。"
        ),
        "hook": "お風呂から出たら急に眠くなった経験ありませんか？",
        "why": "入浴で一時的に体温が上がり、その後ゆっくり下がる過程が眠気と関連すると考えられています。",
        "ending": "夜のお風呂は、ただ体を洗うだけの時間ではないんです。"
    },

    # -----------------------------------------------------
    # 食べ物
    # -----------------------------------------------------

    {
        "id": "food_001",
        "category": "食べ物",
        "keyword": "辛い食べ物",
        "title": "辛いものを食べると汗が出る理由",
        "fact": (
            "唐辛子に含まれるカプサイシンは、熱さを感じる神経を刺激します。"
        ),
        "hook": "辛いラーメンを食べて汗だくになったことありませんか？",
        "why": "体が実際に熱くなったというより、熱さに似た刺激を受けるためです。",
        "ending": "つまり舌が感じている「熱い！」と、実際の温度は別物なんです。"
    },

    {
        "id": "food_002",
        "category": "食べ物",
        "keyword": "チョコレート",
        "title": "甘いものを食べたくなるタイミング",
        "fact": (
            "疲労感やストレスなどによって、甘いものを食べたいと感じることがあります。"
        ),
        "hook": "疲れたとき、なぜか甘いものが欲しくなりませんか？",
        "why": "エネルギー補給への欲求や、味による満足感など複数の要因が関係します。",
        "ending": "「疲れたら甘いもの」という感覚には、ちゃんと理由があるんです。"
    },

    # -----------------------------------------------------
    # 科学
    # -----------------------------------------------------

    {
        "id": "science_001",
        "category": "科学",
        "keyword": "音",
        "title": "音が見えないのに聞こえる理由",
        "fact": (
            "音は空気などの物質中を伝わる振動です。"
        ),
        "hook": "声も音楽も見えないのに、どうして耳に届くのでしょう？",
        "why": "物体の振動が周囲の空気を振動させ、その変化が耳へ伝わります。",
        "ending": "つまり私たちは、空気の小さな振動を「音」として感じ取っているんです。"
    },

    {
        "id": "science_002",
        "category": "科学",
        "keyword": "虹",
        "title": "虹が七色に見える理由",
        "fact": (
            "虹は、太陽光が水滴の中で屈折・反射・分散することで生まれます。"
        ),
        "hook": "雨上がりの虹って、どうしてあんなに色が分かれるのでしょう？",
        "why": "白く見える太陽光にはさまざまな波長の光が含まれていて、水滴を通ると分かれて見えます。",
        "ending": "あの虹は、空に新しい色が生まれたわけではなく、光が分解されて見えているんです。"
    },

    # -----------------------------------------------------
    # 哲学
    # -----------------------------------------------------

    {
        "id": "philosophy_001",
        "category": "哲学",
        "keyword": "幸福",
        "title": "幸せは物の量だけでは決まらない",
        "fact": (
            "人が感じる幸福には、物質的な条件だけでなく、人間関係や自分の感じ方など複数の要因が関係します。"
        ),
        "hook": "欲しかったものを買ったのに、しばらくすると普通になったことありませんか？",
        "why": "人は環境の変化に慣れる傾向があり、以前は特別だったものが日常になることがあります。",
        "ending": "だから幸せを考えるときは、「何を持っているか」だけでなく「何を感じているか」も大切なんです。"
    },

    {
        "id": "philosophy_002",
        "category": "哲学",
        "keyword": "失敗",
        "title": "失敗した経験にも意味がある理由",
        "fact": (
            "失敗は、その後の判断や行動を変えるための情報になることがあります。"
        ),
        "hook": "失敗した瞬間は最悪でも、あとから「あれがあってよかった」と思うことありませんか？",
        "why": "失敗によって、自分に合わない方法や改善すべき点を具体的に知ることができるからです。",
        "ending": "失敗そのものが成功になるわけではありません。でも、次の行動を変える材料にはできます。"
    },

    # -----------------------------------------------------
    # 人間関係
    # -----------------------------------------------------

    {
        "id": "relation_001",
        "category": "人間関係",
        "keyword": "名前",
        "title": "名前を呼ばれると少し嬉しくなる理由",
        "fact": (
            "自分の名前は、自分にとって非常に身近で重要な情報です。"
        ),
        "hook": "名前で呼ばれると、なんとなく距離が近く感じませんか？",
        "why": "名前は自分自身と強く結びついた情報なので、注意を向けやすい特徴があります。",
        "ending": "だから会話の中で相手の名前を自然に使うことは、親しみを感じてもらう一つのきっかけになります。"
    },

    {
        "id": "relation_002",
        "category": "人間関係",
        "keyword": "笑顔",
        "title": "笑顔を見るとこちらも笑いやすくなる理由",
        "fact": (
            "人は他人の表情を見て、自分の表情や感情にも影響を受けることがあります。"
        ),
        "hook": "誰かが楽しそうに笑っていると、こっちまで笑ってしまいませんか？",
        "why": "表情や感情の情報を読み取り、自分の反応にも影響する仕組みがあるためです。",
        "ending": "だから笑顔は、自分一人のものではなく、周りにも伝わる行動なんです。"
    },

    # -----------------------------------------------------
    # 仕事
    # -----------------------------------------------------

    {
        "id": "work_001",
        "category": "仕事",
        "keyword": "集中",
        "title": "集中力がずっと続かないのは普通",
        "fact": (
            "人間の注意力は一定ではなく、時間や環境によって変化します。"
        ),
        "hook": "「今日は集中できない…」って、自分を責めてませんか？",
        "why": "注意には限界があり、疲労や睡眠、周囲の刺激などにも左右されます。",
        "ending": "集中できない日があること自体は珍しくありません。大切なのは、集中できる環境を作ることです。"
    },

    {
        "id": "work_002",
        "category": "仕事",
        "keyword": "先延ばし",
        "title": "やるべきことほど後回しにしたくなる理由",
        "fact": (
            "難しそうな作業や失敗への不安がある作業ほど、始めること自体を避けたくなる場合があります。"
        ),
        "hook": "重要な仕事ほど、なぜか掃除したくなったりしませんか？",
        "why": "作業そのものより、「始めたら大変そう」という予想が心理的な負担になることがあります。",
        "ending": "そんなときは完成させようとせず、まず5分だけ始めるという方法があります。"
    },

    # -----------------------------------------------------
    # 自然
    # -----------------------------------------------------

    {
        "id": "nature_001",
        "category": "自然",
        "keyword": "植物",
        "title": "植物にも昼と夜のリズムがある",
        "fact": (
            "植物も光や温度などの環境変化に応じて、活動状態を変化させています。"
        ),
        "hook": "植物って、ずっと同じ状態に見えますよね。でも実は違います。",
        "why": "植物には光を受ける時間などを手がかりにする生理的なリズムがあります。",
        "ending": "静かに見える植物も、時間の流れの中でちゃんと変化しているんです。"
    },

    {
        "id": "nature_002",
        "category": "自然",
        "keyword": "猫",
        "title": "猫が狭い場所を好む理由",
        "fact": (
            "猫は狭い場所や囲まれた場所に入りたがる行動を見せることがあります。"
        ),
        "hook": "猫って、わざわざ箱の中に入りますよね。",
        "why": "周囲をある程度遮る場所は、安心して休める環境になる場合があります。",
        "ending": "人間にとってはただの段ボールでも、猫にとっては立派な安心スペースなんです。"
    }

]


# =========================================================
# FONT SEARCH
# =========================================================

FONT_CANDIDATES = [

    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",

    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",

    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",

    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",

    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",

    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

]


def find_font():

    for path in FONT_CANDIDATES:

        if os.path.exists(path):

            return path

    return None


FONT_PATH = find_font()


# =========================================================
# BASIC HELPERS
# =========================================================

def ensure_directories():

    IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    VOICE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    CUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    SUBTITLE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def run_command(
    command,
    check=True
):

    print()

    print(
        "COMMAND:",
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

    if result.stdout:

        print(
            result.stdout
        )

    if check and result.returncode != 0:

        raise RuntimeError(
            "Command failed: "
            + " ".join(
                str(x)
                for x in command
            )
        )

    return result


def save_json(
    path,
    data
):

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


def load_json(
    path,
    default
):

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


def get_duration(
    path
):

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

    if result.returncode != 0:

        raise RuntimeError(
            "ffprobe failed"
        )

    return float(
        result.stdout.strip()
    )


def safe_filename(
    text
):

    text = re.sub(
        r'[\\/:*?"<>|]',
        "_",
        text
    )

    text = text.strip()

    if not text:

        text = "item"

    return text[:100]


# =========================================================
# TOPIC SELECTION
# =========================================================

def select_topics():

    used = load_json(
        USED_TOPICS_FILE,
        []
    )

    if not isinstance(
        used,
        list
    ):

        used = []

    available = [
        topic
        for topic in TOPICS
        if topic["id"] not in used
    ]

    if len(available) < TOPICS_PER_VIDEO:

        print(
            "使用済みネタが増えたため、"
            "トピック履歴をリセットします。"
        )

        used = []

        available = list(
            TOPICS
        )

    random.shuffle(
        available
    )

    selected = (
        available[
            :TOPICS_PER_VIDEO
        ]
    )

    return selected


# =========================================================
# SCRIPT GENERATION
# =========================================================

def make_script(
    topic,
    index
):

    number = index + 1

    intro = (
        f"第{number}問。"
    )

    hook = topic["hook"]

    fact = topic["fact"]

    why = topic["why"]

    ending = topic["ending"]

    bridge = random.choice(
        [
            "ここが面白いところです。",
            "実はここには理由があります。",
            "ここからがちょっと意外です。",
            "これ、身近なのに意外と知られていません。",
            "知っているだけで見え方が少し変わります。"
        ]
    )

    script = (
        f"{intro}"
        f"{hook} "
        f"{bridge} "
        f"{fact} "
        f"{why} "
        f"{ending}"
    )

    return script


# =========================================================
# TTS
# =========================================================

async def create_tts_async(
    text,
    output_path
):

    communicate = edge_tts.Communicate(
        text,
        VOICE,
        rate=VOICE_RATE,
        volume=VOICE_VOLUME
    )

    await communicate.save(
        str(output_path)
    )


def create_tts(
    text,
    output_path
):

    asyncio.run(
        create_tts_async(
            text,
            output_path
        )
    )


# =========================================================
# PEXELS
# =========================================================

PEXELS_HEADERS = {
    "Authorization": PEXELS_API_KEY
}


def pexels_search_videos(
    query
):

    url = (
        "https://api.pexels.com/videos/search"
    )

    params = {
        "query": query,
        "orientation": "landscape",
        "size": "medium",
        "per_page": PEXELS_PER_PAGE,
        "page": random.randint(
            1,
            VIDEO_SEARCH_PAGES
        )
    }

    response = requests.get(
        url,
        headers=PEXELS_HEADERS,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json().get(
        "videos",
        []
    )


def choose_pexels_file(
    videos,
    used_ids
):

    candidates = []

    for video in videos:

        video_id = str(
            video.get(
                "id",
                ""
            )
        )

        if not video_id:
            continue

        if video_id in used_ids:
            continue

        width = int(
            video.get(
                "width",
                0
            )
            or 0
        )

        height = int(
            video.get(
                "height",
                0
            )
            or 0
        )

        if width < MIN_VIDEO_WIDTH:
            continue

        files = video.get(
            "video_files",
            []
        )

        best = None

        for file in files:

            fw = int(
                file.get(
                    "width",
                    0
                )
                or 0
            )

            fh = int(
                file.get(
                    "height",
                    0
                )
                or 0
            )

            link = file.get(
                "link"
            )

            if not link:
                continue

            if fw < MIN_VIDEO_WIDTH:
                continue

            if best is None:

                best = file

            else:

                old_width = int(
                    best.get(
                        "width",
                        0
                    )
                    or 0
                )

                if fw > old_width:

                    best = file

        if best:

            candidates.append(
                (
                    video,
                    best
                )
            )

    if not candidates:

        return None

    return random.choice(
        candidates
    )


def download_file(
    url,
    path
):

    print(
        "Downloading:",
        url
    )

    with requests.get(
        url,
        stream=True,
        timeout=60
    ) as response:

        response.raise_for_status()

        with open(
            path,
            "wb"
        ) as f:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if chunk:

                    f.write(
                        chunk
                    )


# =========================================================
# VIDEO SEARCH QUERIES
# =========================================================

QUERY_MAP = {

    "心理学": [
        "person thinking",
        "people thinking",
        "person looking at smartphone",
        "human emotion",
        "people talking"
    ],

    "人体": [
        "human face",
        "person sleeping",
        "person yawning",
        "human body",
        "person relaxing"
    ],

    "日常": [
        "daily life",
        "home kitchen",
        "person cooking",
        "coffee morning",
        "household"
    ],

    "食べ物": [
        "food",
        "eating",
        "cooking",
        "restaurant",
        "dessert"
    ],

    "科学": [
        "science",
        "laboratory",
        "technology",
        "space",
        "light"
    ],

    "哲学": [
        "person thinking",
        "silhouette thinking",
        "person walking",
        "sunset person",
        "reflection"
    ],

    "人間関係": [
        "friends talking",
        "people smiling",
        "friends laughing",
        "conversation",
        "people together"
    ],

    "仕事": [
        "office work",
        "person working",
        "computer office",
        "desk work",
        "business"
    ],

    "自然": [
        "nature",
        "forest",
        "plants",
        "cat",
        "outdoors"
    ]

}


def get_queries(
    topic
):

    category = topic.get(
        "category",
        "日常"
    )

    keyword = topic.get(
        "keyword",
        ""
    )

    queries = []

    if keyword:

        queries.append(
            keyword
        )

    queries.extend(
        QUERY_MAP.get(
            category,
            [
                "daily life",
                "people"
            ]
        )
    )

    # Remove duplicates
    result = []

    for q in queries:

        if q not in result:

            result.append(q)

    return result


# =========================================================
# DOWNLOAD VISUAL
# =========================================================

def get_video_for_topic(
    topic,
    index,
    used_video_ids
):

    queries = get_queries(
        topic
    )

    for query in queries:

        print()
        print(
            f"Searching Pexels: {query}"
        )

        try:

            videos = pexels_search_videos(
                query
            )

        except Exception as e:

            print(
                "Pexels search error:",
                e
            )

            continue

        selected = choose_pexels_file(
            videos,
            used_video_ids
        )

        if not selected:

            continue

        video,
        video_file = selected

        video_id = str(
            video.get(
                "id"
            )
        )

        url = video_file.get(
            "link"
        )

        filename = (
            f"scene_{index + 1:02d}_"
            f"{video_id}.mp4"
        )

        output_path = (
            IMAGE_DIR /
            filename
        )

        try:

            download_file(
                url,
                output_path
            )

            used_video_ids.append(
                video_id
            )

            return {
                "path": output_path,
                "id": video_id,
                "url": url,
                "page": video.get(
                    "url",
                    ""
                ),
                "query": query
            }

        except Exception as e:

            print(
                "Video download error:",
                e
            )

    return None


# =========================================================
# VIDEO PROCESSING
# =========================================================

def create_scene(
    video_path,
    audio_path,
    output_path
):

    duration = get_duration(
        audio_path
    )

    video_duration = get_duration(
        video_path
    )

    if video_duration <= 0:

        raise RuntimeError(
            "動画の長さを取得できませんでした"
        )

    if video_duration < duration:

        loop_count = int(
            duration / video_duration
        ) + 2

        filter_complex = (
            f"[0:v]scale={WIDTH}:{HEIGHT}:"
            f"force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            f"setsar=1,"
            f"fps={FPS},"
            f"trim=duration={duration},"
            f"setpts=PTS-STARTPTS[v]"
        )

        command = [
            "ffmpeg",
            "-y",

            "-stream_loop",
            str(loop_count),

            "-i",
            str(video_path),

            "-i",
            str(audio_path),

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
            "21",

            "-pix_fmt",
            "yuv420p",

            "-c:a",
            "aac",

            "-b:a",
            "192k",

            "-movflags",
            "+faststart",

            str(output_path)
        ]

    else:

        start = 0

        if video_duration > duration + 3:

            max_start = (
                video_duration
                - duration
            )

            start = random.uniform(
                0,
                max_start
            )

        command = [
            "ffmpeg",
            "-y",

            "-ss",
            str(start),

            "-i",
            str(video_path),

            "-i",
            str(audio_path),

            "-filter_complex",

            (
                f"[0:v]"
                f"scale={WIDTH}:{HEIGHT}:"
                f"force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},"
                f"setsar=1,"
                f"fps={FPS},"
                f"setpts=PTS-STARTPTS[v]"
            ),

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
            "21",

            "-pix_fmt",
            "yuv420p",

            "-c:a",
            "aac",

            "-b:a",
            "192k",

            "-movflags",
            "+faststart",

            str(output_path)
        ]

    run_command(
        command
    )


# =========================================================
# SUBTITLE HELPERS
# =========================================================

def format_srt_time(
    seconds
):

    milliseconds = int(
        round(
            seconds * 1000
        )
    )

    hours = (
        milliseconds // 3600000
    )

    milliseconds %= 3600000

    minutes = (
        milliseconds // 60000
    )

    milliseconds %= 60000

    secs = (
        milliseconds // 1000
    )

    milliseconds %= 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{milliseconds:03d}"
    )


def split_text(
    text,
    max_chars=20
):

    text = re.sub(
        r"\s+",
        "",
        text
    )

    parts = re.split(
        r"(?<=[。！？])",
        text
    )

    result = []

    for part in parts:

        part = part.strip()

        if not part:
            continue

        if len(part) <= max_chars:

            result.append(
                part
            )

            continue

        for i in range(
            0,
            len(part),
            max_chars
        ):

            chunk = part[
                i:i + max_chars
            ].strip()

            if chunk:

                result.append(
                    chunk
                )

    return result


def create_subtitle_file(
    segments,
    output_path
):

    entries = []

    global_time = 0.0

    subtitle_index = 1

    for segment in segments:

        text = segment["text"]

        duration = float(
            segment["duration"]
        )

        chunks = split_text(
            text,
            max_chars=18
        )

        if not chunks:

            global_time += duration

            continue

        # Character-weighted timing.
        # This is more natural than simply dividing
        # the audio duration equally.

        total_chars = sum(
            max(
                1,
                len(chunk)
            )
            for chunk in chunks
        )

        current = global_time

        for chunk in chunks:

            ratio = (
                max(
                    1,
                    len(chunk)
                )
                / total_chars
            )

            chunk_duration = (
                duration * ratio
            )

            start = current

            end = (
                current
                + chunk_duration
            )

            entries.append(
                (
                    subtitle_index,
                    start,
                    end,
                    chunk
                )
            )

            subtitle_index += 1

            current = end

        global_time += duration

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        for index, start, end, text in entries:

            f.write(
                f"{index}\n"
            )

            f.write(
                f"{format_srt_time(start)} "
                f"--> "
                f"{format_srt_time(end)}\n"
            )

            f.write(
                text
            )

            f.write(
                "\n\n"
            )


# =========================================================
# BGM
# =========================================================

def create_bgm(
    output_path,
    duration
):

    command = [

        "ffmpeg",
        "-y",

        "-f",
        "lavfi",

        "-i",
        (
            "sine=frequency=220:"
            "sample_rate=44100"
        ),

        "-f",
        "lavfi",

        "-i",
        (
            "sine=frequency=277:"
            "sample_rate=44100"
        ),

        "-filter_complex",

        (
            "[0:a]volume=0.018[a0];"
            "[1:a]volume=0.012[a1];"
            "[a0][a1]amix=inputs=2:"
            "duration=longest,"
            "afade=t=in:st=0:d=2,"
            f"afade=t=out:st={max(0, duration - 3)}:d=3"
        ),

        "-t",
        str(duration),

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        str(output_path)
    ]

    run_command(
        command
    )


# =========================================================
# CONCAT
# =========================================================

def concat_scenes(
    scene_files,
    output_path
):

    concat_file = (
        CUT_DIR /
        "concat.txt"
    )

    with open(
        concat_file,
        "w",
        encoding="utf-8"
    ) as f:

        for path in scene_files:

            absolute = (
                Path(path)
                .resolve()
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

    command = [

        "ffmpeg",
        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(concat_file),

        "-c",
        "copy",

        "-movflags",
        "+faststart",

        str(output_path)
    ]

    run_command(
        command
    )


# =========================================================
# FINAL VIDEO
# =========================================================

def create_final_video(
    video_path,
    subtitle_path,
    bgm_path,
    output_path
):

    subtitle_path_abs = (
        subtitle_path
        .resolve()
    )

    subtitle_filter_path = (
        str(
            subtitle_path_abs
        )
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
        f"'{subtitle_filter_path}'"
        ":force_style="

        "'"
        "FontName=Noto Sans CJK JP,"
        "FontSize=20,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=4,"
        "Shadow=2,"
        "Alignment=2,"
        "MarginV=70"
        "'"
    )

    filter_complex = (

        f"[0:v]"
        f"{subtitle_filter}"
        "[v];"

        "[1:a]"
        "volume=0.07"
        "[bgm];"

        "[0:a]"
        "volume=1.0"
        "[voice];"

        "[voice][bgm]"
        "amix=inputs=2:"
        "duration=first:"
        "dropout_transition=2"
        "[a]"
    )

    command = [

        "ffmpeg",
        "-y",

        "-i",
        str(video_path),

        "-i",
        str(bgm_path),

        "-filter_complex",
        filter_complex,

        "-map",
        "[v]",

        "-map",
        "[a]",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "20",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-movflags",
        "+faststart",

        str(output_path)
    ]

    run_command(
        command
    )


# =========================================================
# THUMBNAIL
# =========================================================

def search_pexels_photo(
    query
):

    url = (
        "https://api.pexels.com/v1/search"
    )

    params = {

        "query": query,

        "orientation": "landscape",

        "size": "large",

        "per_page": 20,

        "page": random.randint(
            1,
            3
        )
    }

    response = requests.get(
        url,
        headers=PEXELS_HEADERS,
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

    # Prefer images containing people.
    random.shuffle(
        photos
    )

    for photo in photos:

        alt = (
            photo.get(
                "alt",
                ""
            )
            or ""
        ).lower()

        if any(
            word in alt
            for word in [
                "person",
                "people",
                "man",
                "woman",
                "human"
            ]
        ):

            return photo

    return photos[0]


def download_photo(
    photo,
    output_path
):

    src = photo.get(
        "src",
        {}
    )

    url = (
        src.get(
            "large2x"
        )
        or
        src.get(
            "large"
        )
        or
        src.get(
            "original"
        )
    )

    if not url:

        raise RuntimeError(
            "Pexels photo URL not found"
        )

    download_file(
        url,
        output_path
    )

    return url


def make_thumbnail(
    image_path,
    title,
    output_path
):

    image = Image.open(
        image_path
    ).convert(
        "RGB"
    )

    image = image.resize(
        (
            THUMB_WIDTH,
            THUMB_HEIGHT
        ),
        Image.Resampling.LANCZOS
    )

    # -----------------------------------------------------
    # Slight enhancement
    # -----------------------------------------------------

    image = ImageEnhance.Contrast(
        image
    ).enhance(
        1.08
    )

    image = ImageEnhance.Color(
        image
    ).enhance(
        1.05
    )

    # -----------------------------------------------------
    # Dark gradient-like overlay
    # -----------------------------------------------------

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
            1
            - (
                x
                / THUMB_WIDTH
            )
        )

        alpha = int(
            220
            * ratio
        )

        draw.line(
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

    image = Image.alpha_composite(
        image.convert(
            "RGBA"
        ),
        overlay
    )

    # -----------------------------------------------------
    # Text
    # -----------------------------------------------------

    draw = ImageDraw.Draw(
        image
    )

    font_path = FONT_PATH

    if font_path:

        main_font = ImageFont.truetype(
            font_path,
            190
        )

        small_font = ImageFont.truetype(
            font_path,
            78
        )

    else:

        main_font = ImageFont.load_default()

        small_font = ImageFont.load_default()

    # Curiosity text.
    category_text = "知ってるようで知らない"

    draw.text(
        (
            190,
            170
        ),
        category_text,
        font=small_font,
        fill=(
            255,
            255,
            255,
            255
        ),
        stroke_width=3,
        stroke_fill=(
            0,
            0,
            0,
            255
        )
    )

    # Main title.
    lines = []

    clean_title = title.strip()

    if len(clean_title) <= 15:

        lines = [
            clean_title
        ]

    else:

        mid = len(clean_title) // 2

        split_pos = clean_title.rfind(
            " ",
            0,
            mid
        )

        if split_pos <= 0:

            split_pos = mid

        lines = [
            clean_title[:split_pos],
            clean_title[split_pos:]
        ]

    y = 430

    for line in lines:

        draw.text(
            (
                190,
                y
            ),
            line,
            font=main_font,
            fill=(
                255,
                255,
                255,
                255
            ),
            stroke_width=8,
            stroke_fill=(
                0,
                0,
                0,
                255
            )
        )

        y += 230

    # Bottom hook.
    draw.text(
        (
            190,
            THUMB_HEIGHT - 300
        ),
        "あなたはいくつ知ってる？",
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
            255
        )
    )

    image = image.convert(
        "RGB"
    )

    image.save(
        output_path,
        "JPEG",
        quality=94,
        optimize=True
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 70)
    print("LONG VIDEO GENERATOR")
    print("5-MINUTE TRIVIA / PSYCHOLOGY / PHILOSOPHY")
    print("=" * 70)
    print()

    # -----------------------------------------------------
    # Environment check
    # -----------------------------------------------------

    if not PEXELS_API_KEY:

        raise RuntimeError(
            "PEXELS_API_KEY がありません。"
            "GitHub Secretsとworkflowのenvを確認してください。"
        )

    # -----------------------------------------------------
    # Directories
    # -----------------------------------------------------

    ensure_directories()

    # -----------------------------------------------------
    # Select topics
    # -----------------------------------------------------

    topics = select_topics()

    print()
    print(
        f"Selected {len(topics)} topics."
    )

    print()

    for i, topic in enumerate(
        topics,
        start=1
    ):

        print(
            f"{i:02d}. "
            f"[{topic['category']}] "
            f"{topic['title']}"
        )

    # -----------------------------------------------------
    # Generate title
    # -----------------------------------------------------

    title_candidates = [

        "知らないと損する身近な雑学15選",

        "実は理由があった身近な雑学15選",

        "知っているようで知らない雑学15選",

        "なぜ？が分かる身近な雑学15選",

        "思わず誰かに話したくなる雑学15選"

    ]

    title = random.choice(
        title_candidates
    )

    TITLE_FILE.write_text(
        title,
        encoding="utf-8"
    )

    print()
    print(
        "TITLE:"
    )

    print(
        title
    )

    # -----------------------------------------------------
    # Used video IDs
    # -----------------------------------------------------

    used_video_ids = load_json(
        USED_VIDEOS_FILE,
        []
    )

    if not isinstance(
        used_video_ids,
        list
    ):

        used_video_ids = []

    # -----------------------------------------------------
    # Generate each segment
    # -----------------------------------------------------

    segments = []

    scene_files = []

    credits = []

    for index, topic in enumerate(
        topics
    ):

        print()
        print("=" * 70)
        print(
            f"SCENE {index + 1}/{len(topics)}"
        )
        print("=" * 70)

        script = make_script(
            topic,
            index
        )

        print()
        print(
            "SCRIPT:"
        )

        print(
            script
        )

        # -------------------------------------------------
        # TTS
        # -------------------------------------------------

        voice_file = (
            VOICE_DIR
            / f"voice_{index + 1:02d}.mp3"
        )

        print()
        print(
            "Creating TTS..."
        )

        create_tts(
            script,
            voice_file
        )

        audio_duration = get_duration(
            voice_file
        )

        print(
            "Audio duration:",
            f"{audio_duration:.2f}s"
        )

        # -------------------------------------------------
        # Pexels
        # -------------------------------------------------

        video_info = get_video_for_topic(
            topic,
            index,
            used_video_ids
        )

        if video_info is None:

            raise RuntimeError(
                "Pexels動画を取得できませんでした: "
                + topic["title"]
            )

        print()
        print(
            "Pexels video ID:",
            video_info["id"]
        )

        # -------------------------------------------------
        # Scene
        # -------------------------------------------------

        scene_file = (
            CUT_DIR
            / f"scene_{index + 1:02d}.mp4"
        )

        print()
        print(
            "Creating scene..."
        )

        create_scene(
            video_info["path"],
            voice_file,
            scene_file
        )

        scene_files.append(
            scene_file
        )

        # -------------------------------------------------
        # Segment information
        # -------------------------------------------------

        segments.append(
            {
                "index": index + 1,
                "topic_id": topic["id"],
                "category": topic["category"],
                "title": topic["title"],
                "script": script,
                "duration": audio_duration,
                "video_id": video_info["id"]
            }
        )

        credits.append(
            {
                "scene": index + 1,
                "topic": topic["title"],
                "pexels_video_id": video_info["id"],
                "pexels_page": video_info["page"],
                "search_query": video_info["query"]
            }
        )

    # -----------------------------------------------------
    # Save caches
    # -----------------------------------------------------

    old_topics = load_json(
        USED_TOPICS_FILE,
        []
    )

    if not isinstance(
        old_topics,
        list
    ):

        old_topics = []

    for topic in topics:

        if topic["id"] not in old_topics:

            old_topics.append(
                topic["id"]
            )

    save_json(
        USED_TOPICS_FILE,
        old_topics
    )

    save_json(
        USED_VIDEOS_FILE,
        used_video_ids
    )

    # -----------------------------------------------------
    # Scene concat
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("CONCAT SCENES")
    print("=" * 70)

    combined_video = (
        CUT_DIR /
        "combined.mp4"
    )

    concat_scenes(
        scene_files,
        combined_video
    )

    # -----------------------------------------------------
    # Total duration
    # -----------------------------------------------------

    combined_duration = get_duration(
        combined_video
    )

    print()
    print(
        "Combined duration:",
        f"{combined_duration:.2f}s"
    )

    print(
        "Target duration:",
        f"{TARGET_MINUTES * 60}s"
    )

    # -----------------------------------------------------
    # Subtitles
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("CREATE SUBTITLES")
    print("=" * 70)

    subtitle_file = (
        SUBTITLE_DIR /
        "captions.srt"
    )

    create_subtitle_file(
        segments,
        subtitle_file
    )

    print()
    print(
        "Subtitle:",
        subtitle_file
    )

    # -----------------------------------------------------
    # BGM
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("CREATE BGM")
    print("=" * 70)

    bgm_file = (
        MEDIA_DIR /
        "bgm_generated.m4a"
    )

    create_bgm(
        bgm_file,
        combined_duration
    )

    # -----------------------------------------------------
    # Final render
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("CREATE FINAL VIDEO")
    print("=" * 70)

    create_final_video(
        combined_video,
        subtitle_file,
        bgm_file,
        FINAL_VIDEO
    )

    if not FINAL_VIDEO.exists():

        raise RuntimeError(
            "final_video.mp4 が生成されませんでした。"
        )

    final_duration = get_duration(
        FINAL_VIDEO
    )

    print()
    print(
        "FINAL VIDEO:"
    )

    print(
        FINAL_VIDEO
    )

    print(
        "Duration:",
        f"{final_duration:.2f}s"
    )

    # -----------------------------------------------------
    # Thumbnail
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("CREATE THUMBNAIL")
    print("=" * 70)

    thumbnail_source = (
        IMAGE_DIR /
        "thumbnail_source.jpg"
    )

    thumbnail_photo = search_pexels_photo(
        "Japanese person thinking"
    )

    if thumbnail_photo is None:

        thumbnail_photo = search_pexels_photo(
            "person thinking"
        )

    if thumbnail_photo is None:

        raise RuntimeError(
            "サムネイル用Pexels画像を取得できませんでした。"
        )

    thumbnail_url = download_photo(
        thumbnail_photo,
        thumbnail_source
    )

    make_thumbnail(
        thumbnail_source,
        title,
        THUMBNAIL
    )

    print()
    print(
        "Thumbnail created:"
    )

    print(
        THUMBNAIL
    )

    # -----------------------------------------------------
    # Pexels credits
    # -----------------------------------------------------

    credits.append(
        {
            "type": "thumbnail",
            "pexels_photo_id": thumbnail_photo.get(
                "id"
            ),
            "pexels_photo_page": thumbnail_photo.get(
                "url",
                ""
            ),
            "source_url": thumbnail_url
        }
    )

    save_json(
        IRASUTOYA_FILE,
        []
    )

    with open(
        CREDIT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "Pexels media used in this video\n"
        )

        f.write(
            "========================================\n\n"
        )

        for credit in credits:

            if credit.get(
                "type"
            ) == "thumbnail":

                f.write(
                    "Thumbnail\n"
                )

                f.write(
                    f"Pexels Photo ID: "
                    f"{credit.get('pexels_photo_id')}\n"
                )

                f.write(
                    f"Page: "
                    f"{credit.get('pexels_photo_page')}\n\n"
                )

            else:

                f.write(
                    f"Scene {credit['scene']}\n"
                )

                f.write(
                    f"Topic: "
                    f"{credit['topic']}\n"
                )

                f.write(
                    f"Pexels Video ID: "
                    f"{credit['pexels_video_id']}\n"
                )

                f.write(
                    f"Page: "
                    f"{credit['pexels_page']}\n"
                )

                f.write(
                    f"Search: "
                    f"{credit['search_query']}\n\n"
                )

    # -----------------------------------------------------
    # video_info.json
    # -----------------------------------------------------

    video_info = {

        "title": title,

        "video_file": str(
            FINAL_VIDEO
        ),

        "thumbnail_file": str(
            THUMBNAIL
        ),

        "duration_seconds": final_duration,

        "width": WIDTH,

        "height": HEIGHT,

        "fps": FPS,

        "topics_count": len(
            topics
        ),

        "voice": VOICE,

        "voice_rate": VOICE_RATE,

        "random_seed": RANDOM_SEED,

        "topics": segments

    }

    save_json(
        VIDEO_INFO_FILE,
        video_info
    )

    # -----------------------------------------------------
    # Final checks
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL CHECK")
    print("=" * 70)

    required_files = [

        FINAL_VIDEO,

        THUMBNAIL,

        TITLE_FILE,

        VIDEO_INFO_FILE,

        CREDIT_FILE

    ]

    for path in required_files:

        if not path.exists():

            raise RuntimeError(
                "必要ファイルがありません: "
                + str(path)
            )

        size = path.stat().st_size

        print(
            f"OK: {path} "
            f"({size / 1024 / 1024:.2f} MB)"
        )

    # -----------------------------------------------------
    # Save topic information
    # -----------------------------------------------------

    topics_json = (
        OUTPUT_DIR /
        "topics.json"
    )

    save_json(
        topics_json,
        segments
    )

    # -----------------------------------------------------
    # Final message
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("LONG VIDEO GENERATION COMPLETE")
    print("=" * 70)

    print()

    print(
        "Title:",
        title
    )

    print(
        "Duration:",
        f"{final_duration:.2f}s"
    )

    print(
        "Topics:",
        len(topics)
    )

    print(
        "Video:",
        FINAL_VIDEO
    )

    print(
        "Thumbnail:",
        THUMBNAIL
    )

    print(
        "Video info:",
        VIDEO_INFO_FILE
    )

    print(
        "Credits:",
        CREDIT_FILE
    )

    print()
    print("=" * 70)


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()
