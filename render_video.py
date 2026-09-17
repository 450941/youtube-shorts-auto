import os
import re
import json
import time
import random
import hashlib
import subprocess
from pathlib import Path
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# 基本設定
# ============================================================

WIDTH = 1920
HEIGHT = 1080

FPS = 30

OUTPUT_DIR = Path("output")
MEDIA_DIR = Path("media")
AUDIO_DIR = MEDIA_DIR / "audio"
IMAGE_DIR = MEDIA_DIR / "irasutoya"
VIDEO_DIR = MEDIA_DIR / "pexels"

OUTPUT_DIR.mkdir(exist_ok=True)
MEDIA_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)
IMAGE_DIR.mkdir(exist_ok=True)
VIDEO_DIR.mkdir(exist_ok=True)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/140 Safari/537.36"
    )
}

FONT_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansJP-Regular.otf",
]

FONT_PATH = None

for p in FONT_PATHS:
    if os.path.exists(p):
        FONT_PATH = p
        break

if FONT_PATH is None:
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


# ============================================================
# 雑学15本
# ============================================================

FACTS = [
    {
        "title": "なぜ人は他人の目が気になる？",
        "text": (
            "街を歩いていると、意外と周りの人の視線が気になることがあります。"
            "でも実際には、自分が思っているほど他人は自分を見ていません。"
            "人間の脳は、自分自身に関係する情報を重要なものとして処理しやすいため、"
            "他人から見られているように感じやすいんです。"
        ),
        "scenes": [
            ["人", "people", "person"],
            ["視線", "people looking", "person looking"],
            ["街", "city people", "walking"],
            ["考える", "thinking person", "person thinking"],
        ],
    },
    {
        "title": "なぜあくびはうつる？",
        "text": (
            "誰かがあくびをすると、自分まであくびをしたくなることがあります。"
            "これは単なる偶然ではありません。"
            "人間は他人の行動を無意識にまねすることがあり、"
            "あくびもその一つだと考えられています。"
            "ただし、あくびがうつる仕組みにはまだ研究途中の部分もあります。"
        ),
        "scenes": [
            ["あくび", "yawning person", "person yawning"],
            ["眠い", "sleepy person", "tired person"],
            ["人", "people", "person"],
            ["眠る", "sleeping", "sleep"],
        ],
    },
    {
        "title": "なぜ炭酸を飲むとスッキリする？",
        "text": (
            "炭酸飲料を飲んだとき、口の中がシュワシュワしてスッキリしますよね。"
            "この刺激は炭酸ガスによるものです。"
            "炭酸ガスが水分に溶けることでできる成分が、"
            "口の中の感覚を刺激するため、独特の爽快感が生まれます。"
        ),
        "scenes": [
            ["炭酸", "sparkling drink", "soda drink"],
            ["飲む", "person drinking", "drinking"],
            ["飲み物", "drink", "beverage"],
            ["爽快", "refreshing drink", "happy drinking"],
        ],
    },
    {
        "title": "なぜ人は昔の失敗を思い出す？",
        "text": (
            "寝る前になると、昔の恥ずかしい失敗を突然思い出すことがあります。"
            "これは脳が感情の強かった出来事を記憶に残しやすいためです。"
            "特に強い感情をともなった出来事は、何年たっても思い出しやすくなります。"
        ),
        "scenes": [
            ["失敗", "mistake person", "person mistake"],
            ["思い出す", "remembering", "thinking person"],
            ["恥ずかしい", "embarrassed person", "embarrassed"],
            ["考える", "thinking person", "person thinking"],
        ],
    },
    {
        "title": "なぜ寝ると記憶が整理される？",
        "text": (
            "勉強したあとに眠ると、覚えたことが残りやすいと言われています。"
            "睡眠中には、起きている間に得た情報が整理されます。"
            "だから徹夜で勉強するより、適切に眠ることが記憶にとって重要なんです。"
        ),
        "scenes": [
            ["勉強", "studying person", "student studying"],
            ["本", "book studying", "reading"],
            ["眠る", "sleeping person", "sleep"],
            ["記憶", "memory thinking", "thinking"],
        ],
    },
    {
        "title": "なぜ緊張すると心臓が速くなる？",
        "text": (
            "人前で話すとき、心臓がドキドキすることがあります。"
            "これは体が危険や重要な場面に備えている反応の一つです。"
            "緊張すると交感神経が働き、心拍数が上がります。"
            "つまりドキドキは、体が頑張っているサインでもあるんです。"
        ),
        "scenes": [
            ["緊張", "nervous person", "nervous"],
            ["心臓", "heartbeat", "heart"],
            ["人前", "speaking people", "public speaking"],
            ["発表", "presentation person", "presentation"],
        ],
    },
    {
        "title": "なぜスマホを見ると時間が早く感じる？",
        "text": (
            "スマホを少しだけ見るつもりだったのに、気づいたら30分たっていた。"
            "そんな経験はありませんか。"
            "画面には次々と新しい情報が現れるため、注意が連続して引きつけられます。"
            "その結果、時間そのものへの意識が薄くなることがあります。"
        ),
        "scenes": [
            ["スマホ", "person smartphone", "phone"],
            ["SNS", "social media phone", "social media"],
            ["時間", "clock person", "time"],
            ["スマホを見る", "person using phone", "using smartphone"],
        ],
    },
    {
        "title": "なぜ笑うと気分が変わる？",
        "text": (
            "面白いことがあると自然に笑いますが、笑うという行動そのものが"
            "気分に影響することもあります。"
            "笑顔になることで表情や呼吸が変化し、"
            "気持ちの感じ方にも影響する可能性があります。"
        ),
        "scenes": [
            ["笑う", "laughing person", "happy person"],
            ["笑顔", "smiling person", "smile"],
            ["楽しい", "happy people", "happiness"],
            ["会話", "people talking", "conversation"],
        ],
    },
    {
        "title": "なぜ人は名前を忘れる？",
        "text": (
            "顔は覚えているのに、名前だけが出てこないことがあります。"
            "これは記憶が完全に消えているとは限りません。"
            "名前は顔や出来事と比べて、意味との結びつきが弱い場合があり、"
            "必要な瞬間に取り出しにくくなることがあります。"
        ),
        "scenes": [
            ["名前", "thinking person", "person thinking"],
            ["忘れる", "forgetting person", "confused person"],
            ["考える", "thinking", "person thinking"],
            ["人", "person", "people"],
        ],
    },
    {
        "title": "なぜ雨の前に眠くなることがある？",
        "text": (
            "雨の日になると、なんとなく眠いと感じる人がいます。"
            "天候による気圧や明るさ、生活リズムなど、"
            "さまざまな要因が関係している可能性があります。"
            "ただし、感じ方には個人差があります。"
        ),
        "scenes": [
            ["雨", "rain", "rainy day"],
            ["眠い", "sleepy person", "tired"],
            ["天気", "weather", "cloudy"],
            ["窓", "rain window", "window rain"],
        ],
    },
    {
        "title": "なぜ好きな曲は何度も聴きたくなる？",
        "text": (
            "お気に入りの曲は、何回聴いても飽きないことがあります。"
            "知っているメロディーには安心感があり、"
            "次に何が来るか予測できることも楽しさにつながります。"
            "そこに新鮮さが少し加わると、さらに魅力を感じることがあります。"
        ),
        "scenes": [
            ["音楽", "person listening music", "music"],
            ["イヤホン", "earphones person", "headphones"],
            ["歌", "singing person", "singing"],
            ["楽しむ", "happy music", "enjoying music"],
        ],
    },
    {
        "title": "なぜ甘いものを見ると食べたくなる？",
        "text": (
            "お腹がいっぱいなのに、ケーキやアイスを見ると食べたくなる。"
            "そんなことがあります。"
            "見た目や香りなどの情報が食欲に関係するためです。"
            "特に過去においしいと感じた食べ物は、見ただけでも食べたい気持ちが起こりやすくなります。"
        ),
        "scenes": [
            ["ケーキ", "cake", "dessert"],
            ["食べる", "person eating", "eating"],
            ["甘い", "sweet food", "dessert"],
            ["食欲", "hungry person", "hungry"],
        ],
    },
    {
        "title": "なぜ時間は年齢によって早く感じる？",
        "text": (
            "子どものころは一年が長く感じたのに、"
            "大人になると一年があっという間に感じることがあります。"
            "一つの理由として、毎日の生活に新しい経験が少なくなると、"
            "あとから振り返ったときの記憶が短く感じられるという考えがあります。"
        ),
        "scenes": [
            ["子ども", "child", "kid"],
            ["大人", "adult person", "adult"],
            ["時計", "clock", "time"],
            ["カレンダー", "calendar", "calendar"],
        ],
    },
    {
        "title": "なぜ人はつらいとき昔のことを思い出す？",
        "text": (
            "気分が落ち込んでいるとき、昔の出来事を思い出すことがあります。"
            "人間の記憶は、そのときの感情や状況と結びついています。"
            "そのため現在の気分が、似た感情をともなう過去の記憶を呼び起こすことがあります。"
            "記憶と感情は、意外と深くつながっているんです。"
        ),
        "scenes": [
            ["落ち込む", "sad person", "sad"],
            ["思い出", "remembering person", "memory"],
            ["昔", "old memories", "thinking"],
            ["一人", "person alone", "alone"],
        ],
    },
]


# ============================================================
# 文字・字幕
# ============================================================

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(text, max_chars=22):
    result = []
    current = ""

    for ch in text:
        current += ch

        if len(current) >= max_chars:
            result.append(current)
            current = ""

    if current:
        result.append(current)

    return "\n".join(result)


def create_subtitle_image(text, output_path):
    img = Image.new("RGBA", (WIDTH, 240), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = get_font(54)

    wrapped = wrap_text(text, 25)

    bbox = draw.multiline_textbbox(
        (0, 0),
        wrapped,
        font=font,
        spacing=12,
        align="center",
        stroke_width=2,
    )

    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (WIDTH - text_w) // 2
    y = (240 - text_h) // 2

    pad_x = 35
    pad_y = 20

    draw.rounded_rectangle(
        (
            x - pad_x,
            y - pad_y,
            x + text_w + pad_x,
            y + text_h + pad_y,
        ),
        radius=22,
        fill=(0, 0, 0, 175),
    )

    draw.multiline_text(
        (x, y),
        wrapped,
        font=font,
        fill=(255, 255, 255, 255),
        stroke_width=3,
        stroke_fill=(0, 0, 0, 255),
        spacing=12,
        align="center",
    )

    img.save(output_path)


# ============================================================
# HTTP
# ============================================================

def safe_get(url, timeout=20, headers=None):
    h = HEADERS.copy()

    if headers:
        h.update(headers)

    try:
        r = requests.get(
            url,
            headers=h,
            timeout=timeout,
        )

        if r.status_code == 200:
            return r

        print(f"HTTP {r.status_code}: {url}")

    except Exception as e:
        print(f"GET error: {e}")

    return None


# ============================================================
# いらすとや検索
# ============================================================

class IrasutoyaLibrary:

    def __init__(self):
        self.used_urls = []
        self.cache = {}

    def search(self, query):
        if not query:
            return None

        if query in self.cache:
            return self.cache[query]

        print(f"[いらすとや] Searching: {query}")

        encoded = quote(query)

        search_urls = [
            f"https://www.irasutoya.com/search?q={encoded}",
            f"https://www.irasutoya.com/search/label/{encoded}",
        ]

        candidates = []

        for search_url in search_urls:

            response = safe_get(search_url)

            if not response:
                continue

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            # ------------------------------------------------
            # 通常の投稿リンク
            # ------------------------------------------------

            for a in soup.find_all("a", href=True):

                href = a.get("href", "")

                if "irasutoya.com/" not in href:
                    continue

                if not re.search(
                    r"irasutoya\.com/\d{4}/\d{2}/",
                    href,
                ):
                    continue

                if href not in candidates:
                    candidates.append(href)

            # ------------------------------------------------
            # img親リンク
            # ------------------------------------------------

            for img in soup.find_all("img"):

                parent = img.find_parent("a")

                if not parent:
                    continue

                href = parent.get("href", "")

                if re.search(
                    r"irasutoya\.com/\d{4}/\d{2}/",
                    href,
                ):
                    if href not in candidates:
                        candidates.append(href)

            if candidates:
                break

        # 最大10ページ候補
        candidates = candidates[:10]

        for page_url in candidates:

            image_url = self.extract_image(page_url)

            if image_url:
                self.cache[query] = (
                    page_url,
                    image_url,
                )

                return (
                    page_url,
                    image_url,
                )

        print(
            f"[いらすとや] 見つからない: {query}"
        )

        self.cache[query] = None

        return None

    def extract_image(self, page_url):

        response = safe_get(page_url)

        if not response:
            return None

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        # og:image
        meta = soup.find(
            "meta",
            property="og:image",
        )

        if meta and meta.get("content"):
            url = meta["content"]

            if "irasutoya.com" in url:
                return url

        # 記事内画像
        article = soup.find(
            class_=re.compile(
                "post-body|entry-content"
            )
        )

        if article:

            for img in article.find_all(
                "img",
                src=True,
            ):

                src = img.get("src")

                if src and (
                    "irasutoya.com" in src
                    or "bp.blogspot.com" in src
                    or "blogger.googleusercontent.com" in src
                ):
                    return urljoin(
                        page_url,
                        src,
                    )

        # 全画像から探す
        for img in soup.find_all(
            "img",
            src=True,
        ):

            src = img.get("src", "")

            if any(
                host in src
                for host in [
                    "irasutoya.com",
                    "bp.blogspot.com",
                    "blogger.googleusercontent.com",
                ]
            ):
                return urljoin(
                    page_url,
                    src,
                )

        return None

    def download(self, result):

        if not result:
            return None

        page_url, image_url = result

        digest = hashlib.md5(
            image_url.encode()
        ).hexdigest()

        output = IMAGE_DIR / f"{digest}.png"

        if output.exists():
            if str(output) not in self.used_urls:
                self.used_urls.append(str(output))

            return output

        response = safe_get(
            image_url,
            timeout=30,
        )

        if not response:
            return None

        try:
            output.write_bytes(
                response.content
            )

            # 画像として開けるか確認
            with Image.open(output) as im:
                im.verify()

            self.used_urls.append(
                str(output)
            )

            return output

        except Exception as e:

            print(
                f"[いらすとや] 画像保存失敗: {e}"
            )

            try:
                output.unlink()
            except Exception:
                pass

            return None


# ============================================================
# Pexels動画検索
# ============================================================

class PexelsLibrary:

    def __init__(self):
        self.cache = {}
        self.used_videos = []

    def search(self, queries):

        if not PEXELS_API_KEY:
            print(
                "[Pexels] PEXELS_API_KEY がありません"
            )
            return None

        if isinstance(queries, str):
            queries = [queries]

        for query in queries:

            if not query:
                continue

            if query in self.cache:
                cached = self.cache[query]

                if cached:
                    return cached

                continue

            print(
                f"[Pexels] Searching: {query}"
            )

            params = {
                "query": query,
                "orientation": "landscape",
                "size": "medium",
                "locale": "en-US",
                "per_page": 15,
                "page": 1,
            }

            headers = {
                "Authorization": PEXELS_API_KEY
            }

            try:

                r = requests.get(
                    "https://api.pexels.com/v1/videos/search",
                    params=params,
                    headers=headers,
                    timeout=30,
                )

                if r.status_code != 200:

                    print(
                        f"[Pexels] HTTP {r.status_code}"
                    )

                    continue

                data = r.json()

                videos = data.get(
                    "videos",
                    [],
                )

                # 横長を優先
                videos = sorted(
                    videos,
                    key=lambda v: (
                        abs(
                            (
                                v.get("width", 16)
                                /
                                max(
                                    v.get("height", 9),
                                    1,
                                )
                            )
                            - (16 / 9)
                        )
                    ),
                )

                for video in videos:

                    video_id = str(
                        video.get("id")
                    )

                    if video_id in self.used_videos:
                        continue

                    files = video.get(
                        "video_files",
                        [],
                    )

                    # HD以上を優先
                    files = sorted(
                        files,
                        key=lambda x: (
                            x.get("width", 0),
                            x.get("height", 0),
                        ),
                        reverse=True,
                    )

                    for file in files:

                        link = file.get(
                            "link"
                        )

                        width = file.get(
                            "width",
                            0,
                        )

                        height = file.get(
                            "height",
                            0,
                        )

                        if (
                            link
                            and width >= 1280
                            and height >= 600
                        ):

                            result = {
                                "id": video_id,
                                "url": link,
                                "width": width,
                                "height": height,
                                "duration": video.get(
                                    "duration",
                                    10,
                                ),
                            }

                            self.cache[
                                query
                            ] = result

                            self.used_videos.append(
                                video_id
                            )

                            return result

            except Exception as e:

                print(
                    f"[Pexels] 検索エラー: {e}"
                )

            self.cache[query] = None

        return None

    def download(self, video):

        if not video:
            return None

        video_id = video["id"]

        output = (
            VIDEO_DIR
            / f"pexels_{video_id}.mp4"
        )

        if output.exists():
            return output

        try:

            print(
                f"[Pexels] Downloading: {video_id}"
            )

            r = requests.get(
                video["url"],
                headers=HEADERS,
                timeout=120,
                stream=True,
            )

            if r.status_code != 200:
                return None

            with open(
                output,
                "wb",
            ) as f:

                for chunk in r.iter_content(
                    chunk_size=1024 * 1024
                ):

                    if chunk:
                        f.write(chunk)

            return output

        except Exception as e:

            print(
                f"[Pexels] ダウンロード失敗: {e}"
            )

            try:
                output.unlink()
            except Exception:
                pass

            return None


# ============================================================
# 音声
# ============================================================

def run(cmd):

    print(
        "\n$ "
        + " ".join(map(str, cmd))
    )

    subprocess.run(
        cmd,
        check=True,
    )


def create_tts(text, output):

    if output.exists():
        return output

    script = (
        "import asyncio\n"
        "import edge_tts\n"
        "\n"
        "async def main():\n"
        "    communicate = edge_tts.Communicate(\n"
        "        text="
        + repr(text)
        + ",\n"
        "        voice='ja-JP-NanamiNeural',\n"
        "        rate='-3%',\n"
        "    )\n"
        "    await communicate.save("
        + repr(str(output))
        + ")\n"
        "\n"
        "asyncio.run(main())\n"
    )

    temp = output.with_suffix(".py")

    temp.write_text(
        script,
        encoding="utf-8",
    )

    run(
        [
            "python",
            str(temp),
        ]
    )

    temp.unlink(
        missing_ok=True
    )

    return output


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
# 画像を1920x1080に収める
# ============================================================

def prepare_image(
    image_path,
    output_path,
):

    if output_path.exists():
        return output_path

    with Image.open(image_path) as original:

        original = original.convert(
            "RGB"
        )

        # 絶対にクロップしない
        original.thumbnail(
            (WIDTH - 80, HEIGHT - 80),
            Image.Resampling.LANCZOS,
        )

        canvas = Image.new(
            "RGB",
            (WIDTH, HEIGHT),
            (245, 245, 245),
        )

        x = (
            WIDTH
            - original.width
        ) // 2

        y = (
            HEIGHT
            - original.height
        ) // 2

        canvas.paste(
            original,
            (x, y),
        )

        canvas.save(
            output_path,
            quality=95,
        )

    return output_path


# ============================================================
# 字幕を動画に焼き込む
# ============================================================

def create_image_segment(
    image_path,
    audio_path,
    subtitle,
    output_path,
):

    if output_path.exists():
        return output_path

    prepared = (
        MEDIA_DIR
        / "prepared"
    )

    prepared.mkdir(
        exist_ok=True
    )

    image_name = (
        hashlib.md5(
            str(image_path).encode()
        ).hexdigest()
        + ".jpg"
    )

    prepared_image = (
        prepared
        / image_name
    )

    prepare_image(
        image_path,
        prepared_image,
    )

    duration = get_duration(
        audio_path
    )

    subtitle_file = (
        prepared
        / (
            hashlib.md5(
                subtitle.encode()
            ).hexdigest()
            + ".png"
        )
    )

    if not subtitle_file.exists():
        create_subtitle_image(
            subtitle,
            subtitle_file,
        )

    # 字幕画像を下側に配置
    filter_complex = (
        "[0:v]scale=1920:1080,"
        "setsar=1[bg];"
        "[1:v]format=rgba,"
        "colorchannelmixer=aa=1[sub];"
        "[bg][sub]overlay=0:820,"
        "format=yuv420p[v]"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(prepared_image),
            "-loop",
            "1",
            "-i",
            str(subtitle_file),
            "-i",
            str(audio_path),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "2:a",
            "-t",
            str(duration),
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "21",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )

    return output_path


# ============================================================
# 実写動画セグメント
# ============================================================

def create_video_segment(
    video_path,
    audio_path,
    subtitle,
    output_path,
):

    if output_path.exists():
        return output_path

    duration = get_duration(
        audio_path
    )

    subtitle_file = (
        MEDIA_DIR
        / "prepared"
        / (
            hashlib.md5(
                subtitle.encode()
            ).hexdigest()
            + ".png"
        )
    )

    subtitle_file.parent.mkdir(
        exist_ok=True
    )

    if not subtitle_file.exists():
        create_subtitle_image(
            subtitle,
            subtitle_file,
        )

    filter_complex = (
        "[0:v]"
        "scale=1920:1080:"
        "force_original_aspect_ratio=decrease,"
        "pad=1920:1080:"
        "(ow-iw)/2:"
        "(oh-ih)/2,"
        "setsar=1,"
        "fps=30,"
        "format=yuv420p"
        "[bg];"
        "[1:v]"
        "format=rgba"
        "[sub];"
        "[bg][sub]"
        "overlay=0:820"
        "[v]"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(video_path),
            "-loop",
            "1",
            "-i",
            str(subtitle_file),
            "-i",
            str(audio_path),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "2:a",
            "-t",
            str(duration),
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "21",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )

    return output_path


# ============================================================
# BGM
# ============================================================

def create_bgm(duration):

    bgm = MEDIA_DIR / "bgm.wav"

    if not bgm.exists():

        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=220:sample_rate=44100",
                "-t",
                "10",
                "-af",
                "volume=0.015,"
                "afade=t=in:st=0:d=2,"
                "afade=t=out:st=8:d=2",
                str(bgm),
            ]
        )

    return bgm


# ============================================================
# 最終結合
# ============================================================

def concat_segments(
    segments,
    output,
):

    concat_file = (
        MEDIA_DIR
        / "concat.txt"
    )

    with open(
        concat_file,
        "w",
        encoding="utf-8",
    ) as f:

        for segment in segments:

            f.write(
                "file '"
                + str(
                    segment.resolve()
                ).replace(
                    "'",
                    "'\\''",
                )
                + "'\n"
            )

    run(
        [
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
            str(output),
        ]
    )

    return output


def add_bgm(
    video,
    output,
):

    duration = get_duration(
        video
    )

    bgm = create_bgm(
        duration
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-stream_loop",
            "-1",
            "-i",
            str(bgm),
            "-filter_complex",
            "[1:a]volume=0.035,"
            "aloop=loop=-1:size=2e+09,"
            "atrim=0:"
            + str(duration)
            + "[bgm];"
            "[0:a][bgm]"
            "amix=inputs=2:"
            "duration=first:"
            "dropout_transition=2"
            "[a]",
            "-map",
            "0:v",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )

    return output


# ============================================================
# シーン取得
# ============================================================

def get_visual(
    queries,
    irasutoya,
    pexels,
    scene_index,
):

    # --------------------------------------------------------
    # ① いらすとや
    # --------------------------------------------------------

    for query in queries:

        result = irasutoya.search(
            query
        )

        if not result:
            continue

        image = irasutoya.download(
            result
        )

        if image:

            # 20種類を超えたら新規取得を止める
            if len(
                set(irasutoya.used_urls)
            ) <= 20:

                print(
                    "[VISUAL] いらすとや使用"
                )

                return {
                    "type": "image",
                    "path": image,
                }

    # --------------------------------------------------------
    # ② Pexels実写
    # --------------------------------------------------------

    # 日本語キーワードではヒットが弱い場合があるので
    # scenes側に英語検索語を入れている
    pexels_result = pexels.search(
        queries
    )

    if pexels_result:

        video = pexels.download(
            pexels_result
        )

        if video:

            print(
                "[VISUAL] いらすとや無し → Pexels実写"
            )

            return {
                "type": "video",
                "path": video,
            }

    # --------------------------------------------------------
    # ③ 最終保険
    # --------------------------------------------------------

    existing_videos = list(
        VIDEO_DIR.glob("*.mp4")
    )

    if existing_videos:

        fallback = existing_videos[
            scene_index
            % len(existing_videos)
        ]

        print(
            "[VISUAL] Pexels再利用"
        )

        return {
            "type": "video",
            "path": fallback,
        }

    existing_images = list(
        IMAGE_DIR.glob("*.png")
    )

    if existing_images:

        fallback = existing_images[
            scene_index
            % len(existing_images)
        ]

        print(
            "[VISUAL] いらすとや再利用"
        )

        return {
            "type": "image",
            "path": fallback,
        }

    return None


# ============================================================
# メイン
# ============================================================

def main():

    print("=" * 70)
    print(
        "Generate 5-Minute Trivia Encouragement Video"
    )
    print(
        "1920x1080 / 15 facts / Irasutoya -> Pexels"
    )
    print("=" * 70)

    if not PEXELS_API_KEY:

        print(
            "WARNING: PEXELS_API_KEY がありません。"
        )

    irasutoya = IrasutoyaLibrary()
    pexels = PexelsLibrary()

    segments = []

    scene_counter = 0

    for fact_index, fact in enumerate(
        FACTS,
        start=1,
    ):

        print("\n")
        print("=" * 70)
        print(
            f"FACT {fact_index}/{len(FACTS)}"
        )
        print(
            fact["title"]
        )
        print("=" * 70)

        # ----------------------------------------------------
        # 本文を4分割
        # ----------------------------------------------------

        text = fact["text"]

        sentences = re.split(
            r"(?<=[。！？])",
            text,
        )

        sentences = [
            s.strip()
            for s in sentences
            if s.strip()
        ]

        # 4シーン程度にする
        scene_texts = []

        if len(sentences) <= 4:
            scene_texts = sentences
        else:

            chunks = [[] for _ in range(4)]

            for i, sentence in enumerate(
                sentences
            ):
                chunks[
                    i % 4
                ].append(sentence)

            scene_texts = [
                "".join(x)
                for x in chunks
                if x
            ]

        # ----------------------------------------------------
        # 各シーン
        # ----------------------------------------------------

        for local_index, scene_text in enumerate(
            scene_texts
        ):

            scene_counter += 1

            audio_path = (
                AUDIO_DIR
                / (
                    f"fact_{fact_index:02d}"
                    f"_scene_{local_index:02d}.mp3"
                )
            )

            create_tts(
                scene_text,
                audio_path,
            )

            # ------------------------------------------------
            # この場面用の検索語
            # ------------------------------------------------

            query_index = min(
                local_index,
                len(fact["scenes"]) - 1,
            )

            queries = fact[
                "scenes"
            ][query_index]

            visual = get_visual(
                queries,
                irasutoya,
                pexels,
                scene_counter,
            )

            if visual is None:

                print(
                    "WARNING: "
                    "画像・映像が取得できませんでした。"
                )

                # 最終的にも止めない
                # 黒背景＋字幕だけの動画を作る
                blank = (
                    MEDIA_DIR
                    / "blank.jpg"
                )

                if not blank.exists():

                    img = Image.new(
                        "RGB",
                        (
                            WIDTH,
                            HEIGHT,
                        ),
                        (25, 25, 25),
                    )

                    img.save(
                        blank,
                        quality=95,
                    )

                visual = {
                    "type": "image",
                    "path": blank,
                }

            segment_path = (
                MEDIA_DIR
                / (
                    f"segment_"
                    f"{fact_index:02d}_"
                    f"{local_index:02d}.mp4"
                )
            )

            if visual["type"] == "image":

                create_image_segment(
                    visual["path"],
                    audio_path,
                    scene_text,
                    segment_path,
                )

            else:

                create_video_segment(
                    visual["path"],
                    audio_path,
                    scene_text,
                    segment_path,
                )

            segments.append(
                segment_path
            )

    # ========================================================
    # 全シーン結合
    # ========================================================

    combined = (
        OUTPUT_DIR
        / "combined.mp4"
    )

    concat_segments(
        segments,
        combined,
    )

    # ========================================================
    # BGM追加
    # ========================================================

    final_video = (
        OUTPUT_DIR
        / "final_video.mp4"
    )

    add_bgm(
        combined,
        final_video,
    )

    print("\n")
    print("=" * 70)
    print("完成！")
    print("=" * 70)
    print(
        f"Output: {final_video}"
    )

    duration = get_duration(
        final_video
    )

    print(
        f"Duration: {duration:.1f} seconds"
    )

    print(
        f"Duration: {duration / 60:.2f} minutes"
    )

    print(
        "Irasutoya images:",
        len(
            set(
                irasutoya.used_urls
            )
        ),
    )

    print(
        "Pexels videos:",
        len(
            set(
                pexels.used_videos
            )
        ),
    )


if __name__ == "__main__":
    main()
