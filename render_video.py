import os
import re
import json
import time
import random
import subprocess
from pathlib import Path
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageFilter

# ============================================================
# SETTINGS
# ============================================================

WIDTH = 1920
HEIGHT = 1080
FPS = 30

VOICE = "ja-JP-NanamiNeural"
VOICE_RATE = "+5%"

FACT_COUNT = 15

# いらすとやの使用素材数を最大20種類に抑える
MAX_UNIQUE_IMAGES = 20

BGM_VOLUME = 0.035

IMAGE_DIR = Path("media/images")
VOICE_DIR = Path("media/voice")
CUT_DIR = Path("media/cuts")
SUB_DIR = Path("media/subtitles")
OUTPUT_DIR = Path("output")

for folder in [
    IMAGE_DIR,
    VOICE_DIR,
    CUT_DIR,
    SUB_DIR,
    OUTPUT_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)

session = requests.Session()

session.headers.update({
    "User-Agent":
        "Mozilla/5.0 "
        "(X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "Chrome/126 Safari/537.36"
})


# ============================================================
# FACTS
# ============================================================

FACTS = [

    {
        "title": "なぜ人は他人の目が気になる？",
        "hook": "人に見られている気がして、つい気にしてしまうことありませんか？",
        "answer": "実は人間の脳は、自分が思っている以上に他人から見られていると思いやすいんです。",
        "reason": "自分の行動を周囲がどのように見ているかを考えることで、人間関係を保とうとする働きが関係しています。",
        "punch": "つまり、あなたが思っているほど周りはあなたを見ていないかもしれません。",
        "scenes": [
            ["人", "見られる", "視線", "注目"],
            ["悩む", "考える", "緊張", "人"],
            ["周りを見る", "人", "見る"]
        ]
    },

    {
        "title": "なぜあくびはうつる？",
        "hook": "誰かがあくびをすると、自分まであくびをしたくなりませんか？",
        "answer": "あくびがうつる現象には、他人の行動を無意識に読み取る脳の働きが関係していると考えられています。",
        "reason": "人は周囲の表情や動きを自然にまねる傾向があり、あくびでも同じような反応が起きることがあります。",
        "punch": "だから、この記事を読んでいる今、あくびした人はちょっと危険です。",
        "scenes": [
            ["あくび", "眠い", "眠る"],
            ["人", "あくび", "顔"],
            ["眠い", "人", "寝る"]
        ]
    },

    {
        "title": "なぜ昔の恥ずかしい記憶を思い出す？",
        "hook": "寝る前に突然、昔の恥ずかしい記憶が蘇ることありませんか？",
        "answer": "強い感情を伴った出来事は、普通の出来事より記憶に残りやすいからです。",
        "reason": "特に恥ずかしさや不安などの感情は、その出来事を重要な情報として脳に残しやすくします。",
        "punch": "数年前の自分から突然ダメージを受けるのは、このせいかもしれません。",
        "scenes": [
            ["恥ずかしい", "顔を隠す", "人"],
            ["思い出す", "考える", "悩む"],
            ["寝る", "考える", "布団"]
        ]
    },

    {
        "title": "なぜスマホを見ると時間が早い？",
        "hook": "少しだけスマホを見るつもりが、気づいたら30分経っていたことありませんか？",
        "answer": "スマホには次々と新しい刺激が入ってくるため、時間そのものへの注意がそれやすくなります。",
        "reason": "短い動画や通知など、変化のある情報が連続すると時間を細かく意識しにくくなります。",
        "punch": "5分だけのつもりが、気づけば夜。スマホあるあるです。",
        "scenes": [
            ["スマホ", "見る", "携帯電話"],
            ["スマホ", "夢中", "人"],
            ["時計", "時間", "驚く"]
        ]
    },

    {
        "title": "なぜ好きな曲は何度も聴きたくなる？",
        "hook": "同じ曲を何十回も聴いてしまったことありませんか？",
        "answer": "好きな音楽を聴くと、脳の報酬系が刺激されることがあります。",
        "reason": "さらに曲の展開を知っていることで、次に何が来るか予測する楽しさも生まれます。",
        "punch": "だからお気に入りの曲は、何回聴いても飽きにくいんです。",
        "scenes": [
            ["音楽", "聞く", "イヤホン"],
            ["歌う", "音楽", "楽しい"],
            ["イヤホン", "スマホ", "音楽"]
        ]
    },

    {
        "title": "なぜ寝る前に色々考えてしまう？",
        "hook": "布団に入った瞬間、急に色々なことを考え始めませんか？",
        "answer": "日中は仕事やスマホなどに注意が向いていますが、静かになると頭の中の考えに意識が向きやすくなります。",
        "reason": "周囲からの刺激が減ることで、未処理の考えや明日の予定などが浮かびやすくなるんです。",
        "punch": "布団に入ってから脳だけが元気になるのは、珍しいことではありません。",
        "scenes": [
            ["布団", "寝る", "人"],
            ["考える", "悩む", "人"],
            ["夜", "寝る", "時計"]
        ]
    },

    {
        "title": "なぜ初対面の印象は強く残る？",
        "hook": "初めて会った人の印象って、意外と覚えていませんか？",
        "answer": "人間は最初に得た情報を、その後の判断の基準にしやすい傾向があります。",
        "reason": "最初の表情や話し方などから、相手について素早く判断しようとするためです。",
        "punch": "最初の数秒が意外と記憶に残る理由はここにあります。",
        "scenes": [
            ["初対面", "人", "挨拶"],
            ["話す", "人", "会話"],
            ["笑う", "人", "笑顔"]
        ]
    },

    {
        "title": "なぜ名前が出てこない？",
        "hook": "顔は分かるのに、名前だけ出てこないことありませんか？",
        "answer": "記憶そのものが消えたというより、保存された情報をうまく取り出せない場合があります。",
        "reason": "名前と顔の情報が別々に処理されることもあり、知っているのに言葉だけ出てこない状態が起こります。",
        "punch": "だから名前が出てこなくても、記憶力が悪いとは限りません。",
        "scenes": [
            ["名前", "人", "考える"],
            ["忘れる", "悩む", "人"],
            ["思い出す", "考える", "人"]
        ]
    },

    {
        "title": "なぜ他人の失敗は覚えている？",
        "hook": "自分の失敗は忘れたいのに、他人の失敗は妙に覚えていませんか？",
        "answer": "他人の行動は自分にとって重要な情報として記憶されることがあります。",
        "reason": "同じ失敗を避けるために、他人の行動を観察して学習する働きがあるからです。",
        "punch": "つまり、人の失敗を覚えてしまう脳にも理由があるんです。",
        "scenes": [
            ["失敗", "人", "困る"],
            ["見る", "人", "注目"],
            ["考える", "人", "悩む"]
        ]
    },

    {
        "title": "なぜ休日は一瞬で終わる？",
        "hook": "休みの日って、平日より時間が早く感じませんか？",
        "answer": "楽しい時間や刺激の多い時間は、あとから振り返ると短く感じられることがあります。",
        "reason": "楽しいことに集中していると、時計を意識する時間が少なくなるからです。",
        "punch": "楽しい時間だけ一瞬なの、ちょっとずるいですよね。",
        "scenes": [
            ["休日", "休む", "人"],
            ["楽しい", "笑う", "人"],
            ["時計", "時間", "驚く"]
        ]
    },

    {
        "title": "なぜ炭酸を飲むとスッキリする？",
        "hook": "疲れたときに炭酸飲料を飲むとスッキリしませんか？",
        "answer": "炭酸の刺激が口や喉に伝わることで、強い感覚刺激として感じられます。",
        "reason": "冷たさや酸味などが組み合わさることで、爽快感として感じやすくなります。",
        "punch": "あのシュワシュワ感、ちゃんと刺激だったんです。",
        "scenes": [
            ["炭酸飲料", "飲み物", "ジュース"],
            ["飲む", "コップ", "飲み物"],
            ["スッキリ", "飲む", "人"]
        ]
    },

    {
        "title": "なぜ辛いものを食べたくなる？",
        "hook": "辛いものが苦手なのに、なぜかまた食べたくなることありませんか？",
        "answer": "辛さによる強い刺激のあとに、爽快感や満足感を感じる人がいます。",
        "reason": "唐辛子の辛味成分は痛みに近い刺激として感じられ、その刺激への反応が独特の感覚につながります。",
        "punch": "辛いのにもう一口。これにはちゃんと理由があります。",
        "scenes": [
            ["辛い", "唐辛子", "食べる"],
            ["辛いもの", "料理", "食事"],
            ["水を飲む", "飲む", "辛い"]
        ]
    },

    {
        "title": "なぜ物を探すと見つからない？",
        "hook": "目の前にあるのに、探している物が見つからないことありませんか？",
        "answer": "探すことに集中しすぎると、目に入っている情報を正しく認識できないことがあります。",
        "reason": "脳は必要な情報を優先して処理するため、探している物以外の情報を無視しやすくなります。",
        "punch": "そして誰かに『そこにあるよ』と言われた瞬間、急に見えるんです。",
        "scenes": [
            ["探す", "探し物", "人"],
            ["見つからない", "困る", "人"],
            ["見つける", "驚く", "人"]
        ]
    },

    {
        "title": "なぜ応援されると頑張れる？",
        "hook": "誰かに『頑張って』と言われるだけで、少し元気になることありませんか？",
        "answer": "人は自分が誰かに支えられていると感じることで、心理的な負担が軽くなることがあります。",
        "reason": "一人で抱えている感覚が減ると、行動を続ける力につながることがあります。",
        "punch": "たった一言が、人を動かすことって本当にあります。",
        "scenes": [
            ["応援", "人", "頑張る"],
            ["励ます", "話す", "人"],
            ["笑顔", "人", "応援"]
        ]
    },

    {
        "title": "なぜ返信を待つと長く感じる？",
        "hook": "メッセージを送ったあと、返信が来るまでが妙に長く感じませんか？",
        "answer": "気になっている出来事には注意が向きやすく、時間を強く意識しやすくなります。",
        "reason": "スマホを何度も確認すると、そのたびに『まだ来ていない』と時間を意識することになります。",
        "punch": "1分が長い。返信待ちのときだけ時間が別人になります。",
        "scenes": [
            ["スマホ", "メッセージ", "見る"],
            ["返信", "待つ", "人"],
            ["スマホ", "時計", "悩む"]
        ]
    },

    {
        "title": "なぜあと5分だけ寝たくなる？",
        "hook": "朝、あと5分だけ……と思ったことありませんか？",
        "answer": "眠気が残った状態では、起きることより眠りを続けることが魅力的に感じられます。",
        "reason": "睡眠不足や睡眠の途中で起きた状態では、脳がまだ休息を求めている場合があります。",
        "punch": "そして『あと5分』が30分になる。朝の5分は信用できません。",
        "scenes": [
            ["目覚まし", "朝", "寝る"],
            ["布団", "眠い", "人"],
            ["時計", "驚く", "朝"]
        ]
    },

]


# ============================================================
# HELPERS
# ============================================================

def run(cmd):
    print("\n$", " ".join(map(str, cmd)))

    subprocess.run(
        cmd,
        check=True
    )


def probe_duration(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return float(
        result.stdout.strip()
    )


# ============================================================
# IRASUTOYA SEARCH
# ============================================================

ALLOWED_HOSTS = {
    "blogger.googleusercontent.com",
    "bp.blogspot.com",
    "www.irasutoya.com",
    "irasutoya.com",
}


def valid_image_url(url):
    if not url:
        return False

    try:
        host = urlparse(url).hostname

        if not host:
            return False

        if host not in ALLOWED_HOSTS:
            return False

        return bool(
            re.search(
                r"\.(png|jpg|jpeg|webp)(\?.*)?$",
                url,
                re.I,
            )
        )

    except Exception:
        return False


def get_page_image(page_url):

    try:
        response = session.get(
            page_url,
            timeout=20,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        og = soup.find(
            "meta",
            property="og:image",
        )

        if og:
            image_url = og.get("content")

            image_url = urljoin(
                page_url,
                image_url,
            )

            if valid_image_url(image_url):
                return image_url

        candidates = []

        for img in soup.find_all(
            "img",
            src=True,
        ):

            src = urljoin(
                page_url,
                img["src"],
            )

            if not valid_image_url(src):
                continue

            width = 0
            height = 0

            try:
                width = int(
                    re.sub(
                        r"\D",
                        "",
                        img.get("width", "0"),
                    ) or 0
                )

                height = int(
                    re.sub(
                        r"\D",
                        "",
                        img.get("height", "0"),
                    ) or 0
                )

            except Exception:
                pass

            score = width * height

            candidates.append(
                (score, src)
            )

        candidates.sort(
            reverse=True
        )

        if candidates:
            return candidates[0][1]

    except Exception as e:
        print(
            "page image error:",
            e
        )

    return None


def search_irasutoya(term):

    print(
        "Searching:",
        term
    )

    search_url = (
        "https://www.irasutoya.com/search?q="
        + quote_plus(term)
    )

    try:
        response = session.get(
            search_url,
            timeout=20,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        pages = []

        for a in soup.find_all(
            "a",
            href=True,
        ):

            href = urljoin(
                search_url,
                a["href"],
            )

            if "irasutoya.com" not in href:
                continue

            if not re.search(
                r"/20\d{2}/",
                href,
            ):
                continue

            if href not in pages:
                pages.append(href)

        for page in pages[:15]:

            image_url = get_page_image(
                page
            )

            if image_url:
                return {
                    "page": page,
                    "image": image_url,
                    "term": term,
                }

    except Exception as e:
        print(
            "search error:",
            e
        )

    return None


# ============================================================
# IMAGE QUALITY
# ============================================================

def inspect_image(path):

    try:
        image = Image.open(path)

        width, height = image.size

        if width < 150 or height < 150:
            return False

        # 極端に細長い素材は避ける
        ratio = width / height

        if ratio < 0.12:
            return False

        if ratio > 8.0:
            return False

        return True

    except Exception:
        return False


def download_image(item, index):

    path = (
        IMAGE_DIR
        / f"source_{index:02d}.png"
    )

    try:

        response = session.get(
            item["image"],
            timeout=30,
        )

        response.raise_for_status()

        with open(
            path,
            "wb",
        ) as f:
            f.write(
                response.content
            )

        image = Image.open(
            path
        ).convert("RGBA")

        image.save(path)

        if not inspect_image(path):
            path.unlink(
                missing_ok=True
            )
            return None

        return path

    except Exception as e:

        print(
            "download error:",
            e
        )

        path.unlink(
            missing_ok=True
        )

        return None


# ============================================================
# IMAGE LIBRARY
# ============================================================

class ImageLibrary:

    def __init__(self):
        self.items = []
        self.by_term = {}

    def find(self, term):

        for item in self.items:

            if item["term"] == term:
                return item

        return None

    def search(self, term):

        existing = self.find(term)

        if existing:
            return existing

        if len(self.items) >= MAX_UNIQUE_IMAGES:
            return None

        result = search_irasutoya(
            term
        )

        if not result:
            return None

        # 同一画像を重複登録しない
        for item in self.items:

            if item["url"] == result["image"]:
                return item

        path = download_image(
            result,
            len(self.items),
        )

        if not path:
            return None

        item = {
            "term": term,
            "url": result["image"],
            "page": result["page"],
            "path": path,
        }

        self.items.append(
            item
        )

        return item


library = ImageLibrary()


def get_scene_images(scene_terms):

    # 優先順位順に探す
    for term in scene_terms:

        result = library.search(
            term
        )

        if result:
            return result

    return None


# ============================================================
# IMAGE FIT
# ============================================================

def make_background():

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        (248, 245, 239),
    )

    return image


def fit_full_image(
    source_path,
    output_path,
    variant,
):

    source = Image.open(
        source_path
    ).convert("RGBA")

    # 元画像を絶対にcropしない
    source.thumbnail(
        (1450, 820),
        Image.Resampling.LANCZOS,
    )

    canvas = make_background()

    # 影
    shadow = Image.new(
        "RGBA",
        (
            source.width + 50,
            source.height + 50,
        ),
        (0, 0, 0, 0),
    )

    alpha = source.getchannel(
        "A"
    )

    blurred = alpha.filter(
        ImageFilter.GaussianBlur(12)
    )

    shadow.paste(
        (0, 0, 0, 45),
        (18, 18),
        blurred,
    )

    x = (
        WIDTH - shadow.width
    ) // 2

    # 場面ごとに少し位置を変える
    y_base = (
        HEIGHT
        - source.height
    ) // 2

    offsets = [
        -20,
        10,
        35,
        -5,
    ]

    y = y_base + offsets[
        variant % len(offsets)
    ]

    canvas.paste(
        shadow,
        (x, y),
        shadow,
    )

    x2 = (
        WIDTH - source.width
    ) // 2

    y2 = y_base + offsets[
        variant % len(offsets)
    ]

    canvas.paste(
        source,
        (x2, y2),
        source,
    )

    canvas.save(
        output_path,
        quality=95,
    )


# ============================================================
# TTS
# ============================================================

async def generate_tts(
    text,
    output_path,
):

    import edge_tts

    voice = edge_tts.Communicate(
        text,
        VOICE,
        rate=VOICE_RATE,
    )

    await voice.save(
        str(output_path)
    )


def make_voice(
    text,
    index,
):

    path = (
        VOICE_DIR
        / f"voice_{index:03d}.mp3"
    )

    if not path.exists():

        import asyncio

        asyncio.run(
            generate_tts(
                text,
                path,
            )
        )

    return path


# ============================================================
# SUBTITLE
# ============================================================

def clean_text(text):

    return re.sub(
        r"\s+",
        "",
        text,
    ).strip()


def split_subtitle(text):

    text = clean_text(
        text
    )

    if len(text) <= 22:
        return text

    # 句読点で優先的に改行
    punctuation = [
        "。",
        "？",
        "！",
        "、",
    ]

    for mark in punctuation:

        position = text.find(
            mark,
            8,
        )

        if 8 <= position <= 24:

            return (
                text[:position + 1]
                + "\\N"
                + text[position + 1:]
            )

    mid = len(text) // 2

    return (
        text[:mid]
        + "\\N"
        + text[mid:]
    )


def ass_time(seconds):

    total = int(
        round(
            seconds * 100
        )
    )

    hour = total // 360000

    total %= 360000

    minute = total // 6000

    total %= 6000

    second = total // 100

    centisecond = total % 100

    return (
        f"{hour}:"
        f"{minute:02d}:"
        f"{second:02d}."
        f"{centisecond:02d}"
    )


def create_ass(segments):

    lines = [

        "[Script Info]",

        "ScriptType: v4.00+",

        "PlayResX: 1920",

        "PlayResY: 1080",

        "",

        "[V4+ Styles]",

        (
            "Format: Name, Fontname, Fontsize, "
            "PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, "
            "BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, "
            "MarginV, Encoding"
        ),

        (
            "Style: Main,"
            "Noto Sans CJK JP,"
            "52,"
            "&H00FFF9EF,"
            "&H00FFF9EF,"
            "&H66000000,"
            "&H00000000,"
            "0,0,0,0,"
            "100,100,0,0,"
            "1,2,1,"
            "2,80,80,70,1"
        ),

        "",

        "[Events]",

        (
            "Format: Layer, Start, End, "
            "Style, Name, MarginL, "
            "MarginR, MarginV, Effect, Text"
        ),
    ]

    for seg in segments:

        start = ass_time(
            seg["start"]
        )

        end = ass_time(
            seg["end"]
        )

        text = split_subtitle(
            seg["text"]
        )

        lines.append(
            "Dialogue: 0,"
            f"{start},"
            f"{end},"
            "Main,,0,0,0,,"
            f"{text}"
        )

    path = (
        SUB_DIR
        / "main.ass"
    )

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return path


# ============================================================
# VIDEO SEGMENT
# ============================================================

def create_segment(
    image,
    voice,
    output,
    variant,
):

    seconds = probe_duration(
        voice
    )

    seconds = max(
        1.0,
        seconds,
    )

    # 16:9
    # cropしない
    # 緩やかなズームのみ
    if variant % 2 == 0:

        zoom = (
            "zoompan="
            "z='min(zoom+0.00045,1.06)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:"
            "s=1920x1080:"
            "fps=30"
        )

    else:

        zoom = (
            "zoompan="
            "z='if(lte(zoom,1.0),1.06,max(zoom-0.00045,1.0))':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:"
            "s=1920x1080:"
            "fps=30"
        )

    vf = (
        "scale=1920:1080:"
        "force_original_aspect_ratio=decrease,"
        "pad=1920:1080:"
        "(ow-iw)/2:"
        "(oh-ih)/2:"
        "color=0xF8F5EF,"
        + zoom
    )

    run([
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(image),
        "-t",
        str(seconds),
        "-vf",
        vf,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        str(output),
    ])

    return seconds


# ============================================================
# MAIN
# ============================================================

def main():

    random.seed(
        int(time.time())
        ^ os.getpid()
    )

    facts = random.sample(
        FACTS,
        FACT_COUNT,
    )

    print("")
    print("====================================")
    print("15 FACT LONG VIDEO")
    print("1920x1080")
    print("====================================")

    for i, fact in enumerate(
        facts,
        1,
    ):

        print(
            f"{i:02d}.",
            fact["title"],
        )

    segments = []

    total_time = 0.0

    segment_index = 0

    source_log = []

    # ========================================================
    # GENERATE
    # ========================================================

    for fact_index, fact in enumerate(
        facts
    ):

        print("")
        print(
            "========== FACT",
            fact_index + 1,
            "=========="
        )

        texts = [
            fact["hook"],
            fact["answer"],
            fact["reason"],
            fact["punch"],
        ]

        for scene_index, text in enumerate(
            texts
        ):

            scene_terms = fact[
                "scenes"
            ][
                scene_index
                % len(fact["scenes"])
            ]

            print(
                "Scene:",
                scene_terms,
            )

            image_item = get_scene_images(
                scene_terms
            )

            # 見つからなかったら汎用候補
            if image_item is None:

                fallback_terms = [
                    "人",
                    "考える",
                    "生活",
                ]

                for fallback in fallback_terms:

                    image_item = library.search(
                        fallback
                    )

                    if image_item:
                        break

            if image_item is None:

                raise RuntimeError(
                    "画像を取得できませんでした: "
                    + str(scene_terms)
                )

            source_log.append({
                "fact": fact["title"],
                "scene": scene_terms,
                "used_term": image_item["term"],
                "page": image_item["page"],
                "image": image_item["url"],
            })

            # =================================================
            # IMAGE
            # =================================================

            visual_path = (
                CUT_DIR
                / f"visual_{segment_index:03d}.jpg"
            )

            fit_full_image(
                image_item["path"],
                visual_path,
                segment_index,
            )

            # =================================================
            # VOICE
            # =================================================

            voice_path = make_voice(
                text,
                segment_index,
            )

            # =================================================
            # VIDEO
            # =================================================

            segment_path = (
                CUT_DIR
                / f"segment_{segment_index:03d}.mp4"
            )

            seconds = create_segment(
                visual_path,
                voice_path,
                segment_path,
                segment_index,
            )

            segments.append({
                "video": segment_path,
                "audio": voice_path,
                "text": text,
                "start": total_time,
                "end": total_time + seconds,
                "duration": seconds,
            })

            total_time += seconds

            segment_index += 1

    # ========================================================
    # CONCAT VIDEO
    # ========================================================

    video_list = (
        Path("media")
        / "video_concat.txt"
    )

    with video_list.open(
        "w",
        encoding="utf-8",
    ) as f:

        for seg in segments:

            f.write(
                "file '"
                + str(
                    seg["video"]
                    .resolve()
                )
                + "'\n"
            )

    run([
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(video_list),
        "-c",
        "copy",
        "media/video_no_audio.mp4",
    ])

    # ========================================================
    # CONCAT VOICE
    # ========================================================

    audio_list = (
        Path("media")
        / "audio_concat.txt"
    )

    with audio_list.open(
        "w",
        encoding="utf-8",
    ) as f:

        for seg in segments:

            f.write(
                "file '"
                + str(
                    seg["audio"]
                    .resolve()
                )
                + "'\n"
            )

    run([
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(audio_list),
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "media/narration.m4a",
    ])

    # ========================================================
    # SUBTITLE
    # ========================================================

    ass_path = create_ass(
        segments
    )

    # ========================================================
    # FINAL VIDEO
    # ========================================================

    run([
        "ffmpeg",
        "-y",

        "-i",
        "media/video_no_audio.mp4",

        "-i",
        "media/narration.m4a",

        "-stream_loop",
        "-1",
        "-i",
        "media/bgm.ogg",

        "-filter_complex",

        (
            "[2:a]"
            f"volume={BGM_VOLUME}"
            "[bgm];"

            "[1:a]"
            "volume=1.0"
            "[voice];"

            "[voice][bgm]"
            "amix="
            "inputs=2:"
            "duration=first:"
            "dropout_transition=2"
            "[audio]"
        ),

        "-map",
        "0:v",

        "-map",
        "[audio]",

        "-vf",
        f"subtitles={ass_path}",

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "22",

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        "output/final_video.mp4",
    ])

    # ========================================================
    # THUMBNAIL
    # ========================================================

    if segments:

        first_visual = (
            CUT_DIR
            / "visual_000.jpg"
        )

        if first_visual.exists():

            Image.open(
                first_visual
            ).save(
                "output/thumbnail.jpg",
                quality=95,
            )

    # ========================================================
    # METADATA
    # ========================================================

    title = (
        facts[0]["title"]
        + " 知ると面白い身近な雑学15選"
    )

    info = {
        "title": title,

        "format": "1920x1080",

        "facts": [
            fact["title"]
            for fact in facts
        ],

        "fact_count": len(facts),

        "duration_seconds": total_time,

        "duration_minutes": (
            total_time / 60
        ),

        "segment_count": len(
            segments
        ),

        "image_count": len(
            library.items
        ),

        "style": {
            "orientation": "landscape",
            "subtitle": "transparent",
            "image_fit": "full",
            "image_crop": False,
            "multiple_scenes": True,
        },
    }

    Path(
        "output/video_info.json"
    ).write_text(
        json.dumps(
            info,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    Path(
        "output/irasutoya_sources.json"
    ).write_text(
        json.dumps(
            source_log,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("")
    print("====================================")
    print("VIDEO COMPLETE")
    print(
        "Duration:",
        round(
            total_time / 60,
            2
        ),
        "minutes",
    )
    print(
        "Facts:",
        len(facts),
    )
    print(
        "Segments:",
        len(segments),
    )
    print(
        "Unique images:",
        len(library.items),
    )
    print("====================================")


if __name__ == "__main__":
    main()
