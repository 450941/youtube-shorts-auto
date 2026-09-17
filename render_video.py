#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import math
import time
import random
import shutil
import hashlib
import subprocess
from pathlib import Path
from urllib.parse import quote, urljoin

import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


# ============================================================
# 基本設定
# ============================================================

WIDTH = 1920
HEIGHT = 1080
FPS = 30

OUTPUT_DIR = Path("output")
MEDIA_DIR = Path("media")
IMAGE_DIR = MEDIA_DIR / "images"
VIDEO_DIR = MEDIA_DIR / "videos"
AUDIO_DIR = MEDIA_DIR / "audio"

for d in [OUTPUT_DIR, MEDIA_DIR, IMAGE_DIR, VIDEO_DIR, AUDIO_DIR]:
    d.mkdir(parents=True, exist_ok=True)

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "").strip()

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 Chrome/128.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "ja,en-US;q=0.8,en;q=0.6",
}

REQUEST_TIMEOUT = 20

MAX_IRASUTOYA_UNIQUE = 20


# ============================================================
# 雑学
# ============================================================

FACTS = [
    {
        "title": "なぜ人は他人の目が気になる？",
        "chunks": [
            "人は、自分が周りからどう見られているかを意識しやすい生き物です。",
            "特に人がたくさんいる場所では、自然と周囲の人の視線を気にしてしまいます。",
            "これは昔から、人との関係を保つために役立ってきたと考えられています。",
            "つまり、他人の目が気になるのは、ある意味では人間らしい反応なんです。",
        ],
        "visuals": [
            {
                "ira": ["人に見られている人", "周りを見る人", "人がいる", "人"],
                "pexels": ["person surrounded by people", "people looking at person"],
            },
            {
                "ira": ["困っている人", "考えている人", "悩んでいる人"],
                "pexels": ["worried person", "thinking person"],
            },
            {
                "ira": ["人が集まる", "人が話している", "会話する人"],
                "pexels": ["group of people talking", "people together"],
            },
            {
                "ira": ["笑顔の人", "人間関係", "仲良くする人"],
                "pexels": ["friends talking", "happy people"],
            },
        ],
    },

    {
        "title": "なぜあくびはうつる？",
        "chunks": [
            "誰かがあくびをすると、自分まであくびをしたくなることがあります。",
            "これは人間だけでなく、一部の動物でも見られる現象です。",
            "相手の行動を無意識にまねすることと関係していると考えられています。",
            "つまり、あくびは意外にも、人と人とのつながりに関係しているんです。",
        ],
        "visuals": [
            {
                "ira": ["あくびをしている人", "眠そうな人", "眠い人"],
                "pexels": ["person yawning", "sleepy person"],
            },
            {
                "ira": ["眠そうな人", "目をこする人", "疲れた人"],
                "pexels": ["tired person", "sleepy person"],
            },
            {
                "ira": ["人を見る", "人と人", "向かい合う人"],
                "pexels": ["two people looking at each other"],
            },
            {
                "ira": ["眠る人", "ベッドで寝る人", "寝ている人"],
                "pexels": ["person sleeping in bed"],
            },
        ],
    },

    {
        "title": "なぜ炭酸を飲むとスッキリする？",
        "chunks": [
            "炭酸飲料を飲んだとき、口の中にシュワシュワした刺激を感じます。",
            "この刺激は、舌や口の中にある感覚に影響します。",
            "さらに冷たい飲み物なら、冷たさも加わって爽快感を感じやすくなります。",
            "つまり、炭酸そのものだけではなく、刺激や冷たさもスッキリ感に関係しているんです。",
        ],
        "visuals": [
            {
                "ira": ["飲み物を飲んでいる人", "コップで飲む人", "飲む人"],
                "pexels": ["person drinking from glass", "person drinking beverage"],
            },
            {
                "ira": ["ペットボトルを持つ人", "飲み物", "ペットボトル"],
                "pexels": ["person holding bottle", "bottle drink"],
            },
            {
                "ira": ["コップ", "飲み物", "ジュース"],
                "pexels": ["glass of drink", "cold beverage"],
            },
            {
                "ira": ["喜ぶ人", "笑顔の人", "元気な人"],
                "pexels": ["happy person drinking", "refreshing drink"],
            },
        ],
    },

    {
        "title": "なぜ人は昔の失敗を思い出す？",
        "chunks": [
            "寝る前などに、昔の恥ずかしい失敗を突然思い出すことがあります。",
            "嫌だった出来事は、強い感情と一緒に記憶されやすいからです。",
            "そのため、普通の日常よりも印象に残っていることがあります。",
            "忘れたい記憶ほど、なぜか突然出てくることがあるんです。",
        ],
        "visuals": [
            {
                "ira": ["失敗した人", "困っている人", "落ち込む人"],
                "pexels": ["sad person", "person feeling embarrassed"],
            },
            {
                "ira": ["考えている人", "思い出す人", "頭を抱える人"],
                "pexels": ["person thinking", "person remembering"],
            },
            {
                "ira": ["恥ずかしがる人", "顔を隠す人", "困る人"],
                "pexels": ["embarrassed person", "person covering face"],
            },
            {
                "ira": ["考える人", "悩む人", "一人で考える人"],
                "pexels": ["person thinking alone", "reflective person"],
            },
        ],
    },

    {
        "title": "なぜ寝ると記憶が整理される？",
        "chunks": [
            "眠っている間も、脳は完全に休んでいるわけではありません。",
            "日中に入ってきた情報の一部が整理され、記憶として定着していきます。",
            "そのため、勉強したあとに睡眠をとることは、記憶にとって重要です。",
            "寝ることは、ただ体を休ませるだけではないんです。",
        ],
        "visuals": [
            {
                "ira": ["ベッド", "寝ている人", "眠る人"],
                "pexels": ["person sleeping in bed", "bedroom sleeping"],
            },
            {
                "ira": ["眠そうな人", "目の下にクマ", "疲れた人"],
                "pexels": ["sleepy person", "tired face"],
            },
            {
                "ira": ["勉強する人", "本を読む人", "机で勉強"],
                "pexels": ["person studying", "student reading"],
            },
            {
                "ira": ["ぐっすり寝る人", "快眠", "ベッドで寝る"],
                "pexels": ["deep sleep", "sleeping person"],
            },
        ],
    },

    {
        "title": "なぜ緊張すると心臓が速くなる？",
        "chunks": [
            "大事な場面になると、心臓がドキドキすることがあります。",
            "これは体が緊張や危険を感じたときに起こる自然な反応です。",
            "体はすぐに動けるように、心拍数などを変化させます。",
            "つまり、ドキドキするのは体が準備をしているサインでもあるんです。",
        ],
        "visuals": [
            {
                "ira": ["緊張している人", "ドキドキする人", "緊張する人"],
                "pexels": ["nervous person", "person nervous"],
            },
            {
                "ira": ["心臓", "胸を押さえる人", "ドキドキ"],
                "pexels": ["person holding chest", "heartbeat"],
            },
            {
                "ira": ["汗をかく人", "困っている人", "焦る人"],
                "pexels": ["nervous sweating person", "stressed person"],
            },
            {
                "ira": ["頑張る人", "走る人", "元気な人"],
                "pexels": ["person running", "active person"],
            },
        ],
    },

    {
        "title": "なぜスマホを見ると時間が早く感じる？",
        "chunks": [
            "スマホを見ていると、気づいたら何十分も経っていることがあります。",
            "動画やSNSなどに集中すると、時間そのものへの注意が減ります。",
            "その結果、あとから振り返ったときに時間が短く感じられることがあります。",
            "スマホを少し見ただけのつもりが、かなり時間が経っていたというわけです。",
        ],
        "visuals": [
            {
                "ira": ["スマホを見る人", "携帯を見る人", "スマートフォン"],
                "pexels": ["person using smartphone", "person looking at phone"],
            },
            {
                "ira": ["スマホを持つ人", "携帯電話", "スマホ"],
                "pexels": ["person holding smartphone"],
            },
            {
                "ira": ["時計を見る人", "時計", "時間を見る"],
                "pexels": ["person looking at clock", "clock time"],
            },
            {
                "ira": ["夜にスマホを見る人", "ベッドでスマホ", "スマホと寝る人"],
                "pexels": ["person using phone in bed", "phone at night"],
            },
        ],
    },

    {
        "title": "なぜ笑うと気分が変わる？",
        "chunks": [
            "面白いことがなくても、笑っていると少し気分が変わることがあります。",
            "笑顔や笑いは、体の状態にもさまざまな変化を起こします。",
            "さらに、人が笑っていると周りの人も笑いやすくなります。",
            "笑いは、自分だけでなく周囲にも影響する行動なんです。",
        ],
        "visuals": [
            {
                "ira": ["笑っている人", "笑顔の人", "楽しそうな人"],
                "pexels": ["happy person laughing", "smiling person"],
            },
            {
                "ira": ["友達と笑う人", "人と話す", "楽しく話す人"],
                "pexels": ["friends laughing", "people laughing together"],
            },
            {
                "ira": ["笑顔", "嬉しい人", "喜ぶ人"],
                "pexels": ["happy smiling person"],
            },
            {
                "ira": ["仲良くする人", "友達", "人間関係"],
                "pexels": ["friends together", "friends talking"],
            },
        ],
    },

    {
        "title": "なぜ人は名前を忘れる？",
        "chunks": [
            "人の顔は覚えているのに、名前だけ出てこないことがあります。",
            "名前は顔や場所などの情報と比べて、意味との結びつきが弱い場合があります。",
            "そのため、知っているはずなのに一瞬だけ思い出せないことがあります。",
            "顔は浮かぶのに名前が出ない、という現象は珍しくありません。",
        ],
        "visuals": [
            {
                "ira": ["名前を思い出す人", "考えている人", "困っている人"],
                "pexels": ["person trying to remember", "thinking person"],
            },
            {
                "ira": ["人の顔", "人物", "人"],
                "pexels": ["person portrait", "people faces"],
            },
            {
                "ira": ["頭を抱える人", "悩む人", "困る人"],
                "pexels": ["confused person", "person thinking"],
            },
            {
                "ira": ["思いつく人", "ひらめく人", "喜ぶ人"],
                "pexels": ["person having an idea", "happy person"],
            },
        ],
    },

    {
        "title": "なぜ雨の前に眠くなることがある？",
        "chunks": [
            "雨が降る前になると、なんとなく眠く感じる人がいます。",
            "天気が変化すると、気圧や明るさなどの環境も変わります。",
            "そうした変化が、眠気やだるさを感じるきっかけになることがあります。",
            "雨の日に眠く感じるのには、環境の変化も関係しているんです。",
        ],
        "visuals": [
            {
                "ira": ["眠そうな人", "眠い人", "目をこする人"],
                "pexels": ["sleepy person", "tired person"],
            },
            {
                "ira": ["雨", "雨の日", "傘をさす人"],
                "pexels": ["person walking in rain", "rainy day"],
            },
            {
                "ira": ["窓を見る人", "窓の外を見る", "雨を見る人"],
                "pexels": ["person looking through window rain"],
            },
            {
                "ira": ["ベッド", "寝る人", "布団"],
                "pexels": ["bedroom", "person sleeping"],
            },
        ],
    },

    {
        "title": "なぜ好きな曲は何度も聴きたくなる？",
        "chunks": [
            "好きな曲は、何度聴いてもまた聴きたくなることがあります。",
            "聞き慣れた音楽は、次にどんな音が来るか予想しやすくなります。",
            "そして、その予想と実際の音が組み合わさることも楽しさにつながります。",
            "だからお気に入りの曲を何十回も聴いてしまうことがあるんです。",
        ],
        "visuals": [
            {
                "ira": ["音楽を聴く人", "イヤホンで音楽", "ヘッドホン"],
                "pexels": ["person listening to music", "headphones person"],
            },
            {
                "ira": ["スマホで音楽", "スマホを見る人", "音楽"],
                "pexels": ["person listening music phone"],
            },
            {
                "ira": ["楽しそうな人", "笑顔の人", "嬉しい人"],
                "pexels": ["happy person listening music"],
            },
            {
                "ira": ["歌う人", "音楽を聴く人", "イヤホン"],
                "pexels": ["person singing", "music headphones"],
            },
        ],
    },

    {
        "title": "なぜ甘いものを見ると食べたくなる？",
        "chunks": [
            "ケーキやチョコレートを見ると、急に食べたくなることがあります。",
            "見た目や香りなどの情報が、食欲と結びついているからです。",
            "特に過去に食べておいしいと感じたものほど、強く反応することがあります。",
            "つまり、食べる前から脳が食事の準備を始めることがあるんです。",
        ],
        "visuals": [
            {
                "ira": ["ケーキを見る人", "甘いもの", "お菓子を見る人"],
                "pexels": ["person looking at cake", "dessert person"],
            },
            {
                "ira": ["ケーキ", "チョコレート", "お菓子"],
                "pexels": ["cake dessert", "chocolate dessert"],
            },
            {
                "ira": ["食べる人", "お菓子を食べる人", "食事する人"],
                "pexels": ["person eating dessert"],
            },
            {
                "ira": ["嬉しい人", "笑顔の人", "喜ぶ人"],
                "pexels": ["happy person eating"],
            },
        ],
    },

    {
        "title": "なぜ時間は年齢によって早く感じる？",
        "chunks": [
            "子どもの頃は長く感じた一年が、大人になると短く感じることがあります。",
            "毎日が似たような生活になると、新しい出来事が少なくなります。",
            "あとから振り返ったとき、印象に残る出来事が少ないほど時間が短く感じられることがあります。",
            "同じ一年でも、過ごし方によって体感が変わるんです。",
        ],
        "visuals": [
            {
                "ira": ["子供", "子どもが遊ぶ", "遊ぶ人"],
                "pexels": ["child playing", "children playing"],
            },
            {
                "ira": ["大人", "働く人", "仕事をする人"],
                "pexels": ["adult working", "person working"],
            },
            {
                "ira": ["時計", "時間", "時計を見る人"],
                "pexels": ["clock time", "person looking at clock"],
            },
            {
                "ira": ["カレンダー", "予定", "日付を見る人"],
                "pexels": ["calendar", "person looking at calendar"],
            },
        ],
    },

    {
        "title": "なぜ人はつらいとき昔のことを思い出す？",
        "chunks": [
            "つらいとき、なぜか昔の出来事を思い出すことがあります。",
            "特に強い感情と結びついた記憶は、何かをきっかけに浮かびやすくなります。",
            "昔の写真や音楽、場所などがきっかけになることもあります。",
            "記憶は、現在の気分や周囲の刺激ともつながっているんです。",
        ],
        "visuals": [
            {
                "ira": ["落ち込む人", "悲しい人", "一人で悩む人"],
                "pexels": ["sad person alone", "person feeling down"],
            },
            {
                "ira": ["昔を思い出す人", "考えている人", "思い出す"],
                "pexels": ["person remembering past"],
            },
            {
                "ira": ["写真を見る人", "アルバム", "写真を見る"],
                "pexels": ["person looking at old photos"],
            },
            {
                "ira": ["音楽を聴く人", "イヤホン", "思い出す人"],
                "pexels": ["person listening to music alone"],
            },
        ],
    },

    {
        "title": "なぜ人は同じ曲を頭の中で繰り返す？",
        "chunks": [
            "一度聴いた曲が、頭の中で何度も繰り返されることがあります。",
            "特に短くて覚えやすいメロディーは、頭の中に残りやすいと言われています。",
            "曲を実際に聴いていなくても、脳の中でその一部が再生されることがあります。",
            "気づいたら同じフレーズをずっと考えていた、ということが起こるんです。",
        ],
        "visuals": [
            {
                "ira": ["音楽を聴く人", "イヤホン", "ヘッドホン"],
                "pexels": ["person listening to music"],
            },
            {
                "ira": ["考えている人", "頭の中", "思い出す人"],
                "pexels": ["person thinking"],
            },
            {
                "ira": ["歌う人", "音楽", "歌"],
                "pexels": ["person singing"],
            },
            {
                "ira": ["楽しそうな人", "笑顔", "音楽を聴く人"],
                "pexels": ["happy person music"],
            },
        ],
    },
]


# ============================================================
# 共通関数
# ============================================================

def run_cmd(cmd, check=True):
    print("RUN:", " ".join(str(x) for x in cmd))
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if result.stdout:
        print(result.stdout[-5000:])

    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {result.returncode}\n"
            + result.stdout[-5000:]
        )

    return result


def safe_name(text):
    text = re.sub(r"[^\wぁ-んァ-ヶ一-龯]+", "_", text)
    return text[:80]


def md5_text(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:16]


# ============================================================
# フォント
# ============================================================

def find_font():
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    ]

    for p in candidates:
        if Path(p).exists():
            return p

    return None


FONT_PATH = find_font()


# ============================================================
# イラスト屋
# ============================================================

class IrasutoyaLibrary:

    def __init__(self):
        self.used_urls = set()
        self.used_files = set()
        self.count = 0

    def search_result_pages(self, query):
        url = "https://www.irasutoya.com/search?q=" + quote(query)

        try:
            r = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )

            if r.status_code != 200:
                print(f"[IRA] HTTP {r.status_code}: {query}")
                return []

            html = r.text

            post_urls = []

            # Blogger型の投稿URL
            patterns = [
                r'https?://www\.irasutoya\.com/\d{4}/\d{2}/[^"\']+\.html',
                r'href=["\'](/?\d{4}/\d{2}/[^"\']+\.html)["\']',
            ]

            for pattern in patterns:
                for match in re.findall(pattern, html, re.I):
                    if match.startswith("/"):
                        full = "https://www.irasutoya.com" + match
                    else:
                        full = match

                    full = full.split("#")[0]

                    if full not in post_urls:
                        post_urls.append(full)

            # 最大12件だけ
            return post_urls[:12]

        except Exception as e:
            print(f"[IRA] search error: {query} / {e}")
            return []

    def get_image_from_post(self, post_url):
        try:
            r = requests.get(
                post_url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )

            if r.status_code != 200:
                return None

            html = r.text

            candidates = []

            # og:image
            m = re.search(
                r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                html,
                re.I,
            )

            if m:
                candidates.append(m.group(1))

            # content -> og:image の順番が逆の場合
            m = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
                html,
                re.I,
            )

            if m:
                candidates.append(m.group(1))

            # img src
            img_patterns = [
                r'<img[^>]+src=["\']([^"\']+)["\']',
                r'<img[^>]+data-src=["\']([^"\']+)["\']',
                r'<img[^>]+data-original=["\']([^"\']+)["\']',
                r'<img[^>]+data-lazy-src=["\']([^"\']+)["\']',
            ]

            for pattern in img_patterns:
                for img_url in re.findall(pattern, html, re.I):
                    candidates.append(img_url)

            for image_url in candidates:
                image_url = image_url.replace("&amp;", "&")

                if image_url.startswith("//"):
                    image_url = "https:" + image_url

                elif image_url.startswith("/"):
                    image_url = urljoin(post_url, image_url)

                if not image_url.startswith("http"):
                    continue

                low = image_url.lower()

                if any(
                    x in low
                    for x in [
                        "logo",
                        "icon",
                        "avatar",
                        "favicon",
                        "profile",
                    ]
                ):
                    continue

                if image_url in self.used_urls:
                    continue

                self.used_urls.add(image_url)

                return image_url

            return None

        except Exception as e:
            print(f"[IRA] post error: {e}")
            return None

    def download(self, query_list):
        if self.count >= MAX_IRASUTOYA_UNIQUE:
            return None

        for query in query_list:

            if self.count >= MAX_IRASUTOYA_UNIQUE:
                break

            print(f"[IRA SEARCH] {query}")

            posts = self.search_result_pages(query)

            for post in posts:

                if self.count >= MAX_IRASUTOYA_UNIQUE:
                    break

                image_url = self.get_image_from_post(post)

                if not image_url:
                    continue

                filename = IMAGE_DIR / (
                    f"ira_{self.count:02d}_{md5_text(image_url)}.png"
                )

                try:
                    r = requests.get(
                        image_url,
                        headers=HEADERS,
                        timeout=REQUEST_TIMEOUT,
                    )

                    if r.status_code != 200:
                        continue

                    if len(r.content) < 1000:
                        continue

                    img = Image.open(BytesIO(r.content))

                    if img.width < 100 or img.height < 100:
                        continue

                    # RGB/RGBAに変換して確実に保存
                    if img.mode not in ["RGB", "RGBA"]:
                        img = img.convert("RGBA")

                    img.save(filename, "PNG")

                    # 保存確認
                    check = Image.open(filename)
                    if check.width < 100 or check.height < 100:
                        filename.unlink(missing_ok=True)
                        continue

                    self.count += 1
                    self.used_files.add(str(filename))

                    print(
                        f"[IRA OK] {filename} "
                        f"{img.width}x{img.height}"
                    )

                    return filename

                except Exception as e:
                    print(f"[IRA DOWNLOAD ERROR] {e}")

        return None


# ============================================================
# Pexels
# ============================================================

class PexelsLibrary:

    def __init__(self):
        self.used_ids = set()
        self.count = 0

    def search(self, queries):

        if not PEXELS_API_KEY:
            print("[PEXELS] API KEYなし")
            return None

        headers = {
            "Authorization": PEXELS_API_KEY,
            "User-Agent": USER_AGENT,
        }

        for query in queries:

            print(f"[PEXELS SEARCH] {query}")

            try:
                params = {
                    "query": query,
                    "orientation": "landscape",
                    "size": "medium",
                    "locale": "en-US",
                    "per_page": 15,
                }

                r = requests.get(
                    "https://api.pexels.com/v1/videos/search",
                    headers=headers,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )

                if r.status_code != 200:
                    print(
                        f"[PEXELS] HTTP {r.status_code}: "
                        f"{r.text[:500]}"
                    )
                    continue

                data = r.json()

                videos = data.get("videos", [])

                # 大きいものを優先
                videos = sorted(
                    videos,
                    key=lambda v: (
                        v.get("width", 0) * v.get("height", 0)
                    ),
                    reverse=True,
                )

                for video in videos:

                    video_id = video.get("id")

                    if not video_id:
                        continue

                    if video_id in self.used_ids:
                        continue

                    files = video.get("video_files", [])

                    candidates = []

                    for f in files:

                        link = f.get("link")

                        if not link:
                            continue

                        width = f.get("width") or 0
                        height = f.get("height") or 0
                        file_type = f.get("file_type", "")

                        if file_type and file_type != "video/mp4":
                            continue

                        if width <= 0 or height <= 0:
                            continue

                        # 横動画だけ
                        if width < height:
                            continue

                        candidates.append(f)

                    if not candidates:
                        continue

                    candidates.sort(
                        key=lambda f: (
                            (f.get("width") or 0)
                            * (f.get("height") or 0)
                        ),
                        reverse=True,
                    )

                    selected = candidates[0]
                    link = selected["link"]

                    filename = VIDEO_DIR / (
                        f"pexels_{video_id}_{md5_text(link)}.mp4"
                    )

                    if not filename.exists():

                        try:
                            vr = requests.get(
                                link,
                                headers={"User-Agent": USER_AGENT},
                                stream=True,
                                timeout=60,
                            )

                            if vr.status_code != 200:
                                continue

                            with open(filename, "wb") as f:
                                for chunk in vr.iter_content(1024 * 1024):
                                    if chunk:
                                        f.write(chunk)

                        except Exception as e:
                            print(
                                f"[PEXELS DOWNLOAD ERROR] {e}"
                            )
                            filename.unlink(missing_ok=True)
                            continue

                    if filename.exists() and filename.stat().st_size > 10000:

                        # ffprobe確認
                        probe = subprocess.run(
                            [
                                "ffprobe",
                                "-v",
                                "error",
                                "-show_entries",
                                "format=duration",
                                "-of",
                                "default=noprint_wrappers=1:nokey=1",
                                str(filename),
                            ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                        )

                        try:
                            duration = float(probe.stdout.strip())
                        except Exception:
                            duration = 0

                        if duration < 0.5:
                            filename.unlink(missing_ok=True)
                            continue

                        self.used_ids.add(video_id)
                        self.count += 1

                        print(
                            f"[PEXELS OK] {filename} "
                            f"{selected.get('width')}x"
                            f"{selected.get('height')} "
                            f"{duration:.1f}s"
                        )

                        return filename

            except Exception as e:
                print(f"[PEXELS ERROR] {query}: {e}")

        return None


# ============================================================
# フォールバック画像
# ============================================================

def create_fallback_image(text, index):
    """
    何も取れなかった場合でも真っ黒にはしない。
    人物っぽいシンプルなカードを生成。
    """

    path = IMAGE_DIR / f"fallback_{index:04d}.png"

    img = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        (245, 245, 245),
    )

    draw = ImageDraw.Draw(img)

    # シンプルな人物アイコン
    cx = WIDTH // 2
    cy = 390

    draw.ellipse(
        (cx - 90, cy - 90, cx + 90, cy + 90),
        fill=(80, 80, 80),
    )

    draw.rounded_rectangle(
        (
            cx - 170,
            cy + 70,
            cx + 170,
            cy + 420,
        ),
        radius=80,
        fill=(110, 110, 110),
    )

    if FONT_PATH:
        font = ImageFont.truetype(FONT_PATH, 60)
    else:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]

    draw.text(
        (
            (WIDTH - tw) / 2,
            700,
        ),
        text,
        fill=(40, 40, 40),
        font=font,
    )

    img.save(path)

    return path


# ============================================================
# ビジュアル取得
# ============================================================

class VisualManager:

    def __init__(self):
        self.ira = IrasutoyaLibrary()
        self.pexels = PexelsLibrary()
        self.used_visual_paths = set()
        self.fallback_index = 0

    def get_visual(self, scene):

        # ----------------------------------------------------
        # 1. イラスト屋
        # ----------------------------------------------------

        image = self.ira.download(scene["ira"])

        if image and str(image) not in self.used_visual_paths:
            self.used_visual_paths.add(str(image))

            print(f"[VISUAL] IRASUTOYA: {image}")

            return {
                "type": "image",
                "path": image,
            }

        # ----------------------------------------------------
        # 2. Pexels
        # ----------------------------------------------------

        video = self.pexels.search(scene["pexels"])

        if video and str(video) not in self.used_visual_paths:
            self.used_visual_paths.add(str(video))

            print(f"[VISUAL] PEXELS: {video}")

            return {
                "type": "video",
                "path": video,
            }

        # ----------------------------------------------------
        # 3. 既存素材を探す
        # ----------------------------------------------------

        for p in list(IMAGE_DIR.glob("*.png")):
            if str(p) not in self.used_visual_paths:
                self.used_visual_paths.add(str(p))

                print(f"[VISUAL] REUSE IMAGE: {p}")

                return {
                    "type": "image",
                    "path": p,
                }

        for p in list(VIDEO_DIR.glob("*.mp4")):
            if str(p) not in self.used_visual_paths:
                self.used_visual_paths.add(str(p))

                print(f"[VISUAL] REUSE VIDEO: {p}")

                return {
                    "type": "video",
                    "path": p,
                }

        # ----------------------------------------------------
        # 4. 最終フォールバック
        # ----------------------------------------------------

        self.fallback_index += 1

        fallback = create_fallback_image(
            scene["ira"][0],
            self.fallback_index,
        )

        self.used_visual_paths.add(str(fallback))

        print(f"[VISUAL] FALLBACK: {fallback}")

        return {
            "type": "image",
            "path": fallback,
        }


# ============================================================
# Edge TTS
# ============================================================

def create_tts(text, output_path):

    if output_path.exists() and output_path.stat().st_size > 1000:
        return output_path

    code = f"""
import asyncio
import edge_tts

async def main():
    communicate = edge_tts.Communicate(
        {text!r},
        "ja-JP-NanamiNeural",
        rate="-3%",
        volume="+0%",
    )
    await communicate.save({str(output_path)!r})

asyncio.run(main())
"""

    tmp = AUDIO_DIR / "tts_temp.py"
    tmp.write_text(code, encoding="utf-8")

    run_cmd(["python", str(tmp)])

    if not output_path.exists():
        raise RuntimeError(
            f"TTS生成失敗: {output_path}"
        )

    return output_path


def get_audio_duration(path):

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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        return float(result.stdout.strip())
    except Exception:
        return 1.0


# ============================================================
# 字幕PNG
# ============================================================

def make_subtitle_png(text, index):

    path = MEDIA_DIR / f"subtitle_{index:04d}.png"

    img = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (0, 0, 0, 0),
    )

    draw = ImageDraw.Draw(img)

    if FONT_PATH:
        font_size = 64

        while font_size >= 42:

            font = ImageFont.truetype(
                FONT_PATH,
                font_size,
            )

            bbox = draw.textbbox(
                (0, 0),
                text,
                font=font,
                stroke_width=2,
            )

            tw = bbox[2] - bbox[0]

            if tw <= WIDTH - 220:
                break

            font_size -= 2

    else:
        font = ImageFont.load_default()

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
        stroke_width=3,
    )

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = (WIDTH - tw) // 2
    y = 830

    # 半透明黒背景
    padding_x = 35
    padding_y = 20

    draw.rounded_rectangle(
        (
            x - padding_x,
            y - padding_y,
            x + tw + padding_x,
            y + th + padding_y,
        ),
        radius=20,
        fill=(0, 0, 0, 175),
    )

    draw.text(
        (x, y),
        text,
        font=font,
        fill=(255, 255, 255, 255),
        stroke_width=3,
        stroke_fill=(0, 0, 0, 255),
    )

    img.save(path)

    return path


# ============================================================
# イラストを1920x1080に変換
# ============================================================

def prepare_image(image_path, index):

    output = MEDIA_DIR / f"prepared_image_{index:04d}.png"

    img = Image.open(image_path)

    if img.mode not in ["RGB", "RGBA"]:
        img = img.convert("RGBA")

    # 白背景
    canvas = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        (255, 255, 255),
    )

    img.thumbnail(
        (
            WIDTH - 160,
            HEIGHT - 160,
        ),
        Image.Resampling.LANCZOS,
    )

    if img.mode == "RGBA":
        canvas.paste(
            img,
            (
                (WIDTH - img.width) // 2,
                (HEIGHT - img.height) // 2,
            ),
            img,
        )
    else:
        canvas.paste(
            img,
            (
                (WIDTH - img.width) // 2,
                (HEIGHT - img.height) // 2,
            ),
        )

    canvas.save(output, quality=95)

    return output


# ============================================================
# 静止画セグメント
# ============================================================

def create_image_segment(
    image_path,
    subtitle_path,
    audio_path,
    output_path,
    duration,
):

    prepared = prepare_image(
        image_path,
        random.randint(1, 999999),
    )

    run_cmd(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(prepared),
            "-i",
            str(audio_path),
            "-i",
            str(subtitle_path),
            "-filter_complex",
            "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white,"
            "format=yuv420p[base];"
            "[base][2:v]overlay=0:0:format=auto[outv]",
            "-map",
            "[outv]",
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
            "21",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            str(output_path),
        ]
    )


# ============================================================
# 動画セグメント
# ============================================================

def create_video_segment(
    video_path,
    subtitle_path,
    audio_path,
    output_path,
    duration,
):

    run_cmd(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-i",
            str(subtitle_path),
            "-filter_complex",
            "[0:v]"
            "scale=1920:1080:"
            "force_original_aspect_ratio=decrease,"
            "pad=1920:1080:"
            "(ow-iw)/2:(oh-ih)/2:"
            "color=black,"
            "fps=30,"
            "format=yuv420p"
            "[base];"
            "[base][2:v]"
            "overlay=0:0:format=auto"
            "[outv]",
            "-map",
            "[outv]",
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
            "21",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            str(output_path),
        ]
    )


# ============================================================
# BGM
# ============================================================

def create_bgm(duration):

    bgm = MEDIA_DIR / "bgm.wav"

    run_cmd(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=220:sample_rate=24000",
            "-t",
            f"{duration:.3f}",
            "-af",
            "volume=0.025",
            "-c:a",
            "pcm_s16le",
            str(bgm),
        ]
    )

    return bgm


# ============================================================
# 動画結合
# ============================================================

def concat_segments(segment_files, output_path):

    concat_file = MEDIA_DIR / "concat.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for p in segment_files:
            f.write(
                "file '"
                + str(Path(p).resolve()).replace("'", "'\\''")
                + "'\n"
            )

    run_cmd(
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
            str(output_path),
        ]
    )


# ============================================================
# BGMを最終動画に追加
# ============================================================

def add_bgm(video_path, output_path):

    duration = get_audio_duration(video_path)

    bgm = create_bgm(duration)

    run_cmd(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-stream_loop",
            "-1",
            "-i",
            str(bgm),
            "-filter_complex",
            "[0:a]volume=1.0[voice];"
            "[1:a]volume=0.018[bg];"
            "[voice][bg]"
            "amix=inputs=2:"
            "duration=first:"
            "dropout_transition=2"
            "[audio]",
            "-map",
            "0:v",
            "-map",
            "[audio]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            str(output_path),
        ]
    )


# ============================================================
# video_info.json
# ============================================================

def create_video_info(final_video):

    duration = get_audio_duration(final_video)

    info = {
        "video_file": str(final_video),
        "title": "なぜ人は他人の目が気になる？ 知ると面白い身近な雑学15選",
        "description": (
            "身近だけど意外と知らない、ちょっと気になる雑学を15個紹介します。\n\n"
            "人間の心理、記憶、睡眠、音楽、食べ物など、"
            "日常生活に関係する雑学をまとめました。\n\n"
            "#雑学 #豆知識 #面白い雑学 #心理学 #人間心理"
        ),
        "tags": [
            "雑学",
            "豆知識",
            "面白い雑学",
            "身近な雑学",
            "心理学",
            "人間心理",
            "睡眠",
            "記憶",
            "音楽",
            "YouTube",
        ],
        "category_id": "27",
        "privacy_status": "public",
        "duration": round(duration, 1),
    }

    path = OUTPUT_DIR / "video_info.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            info,
            f,
            ensure_ascii=False,
            indent=2,
        )

    return path


# ============================================================
# メイン
# ============================================================

def main():

    print("=" * 70)
    print("5分雑学動画 自動生成")
    print("1920x1080 / 15雑学 / 抽象検索ビジュアル")
    print("=" * 70)

    if not PEXELS_API_KEY:
        print(
            "[WARNING] PEXELS_API_KEY がありません。"
            "イラスト屋中心になります。"
        )

    visual_manager = VisualManager()

    segment_files = []

    scene_number = 0

    total_facts = len(FACTS)

    print(f"雑学数: {total_facts}")

    for fact_index, fact in enumerate(FACTS, start=1):

        print()
        print("=" * 70)
        print(
            f"[FACT {fact_index}/{total_facts}] "
            f"{fact['title']}"
        )
        print("=" * 70)

        chunks = fact["chunks"]
        visuals = fact["visuals"]

        for chunk_index, text in enumerate(chunks):

            scene_number += 1

            print()
            print(
                f"--- SCENE {scene_number} "
                f"(Fact {fact_index}, "
                f"{chunk_index + 1}/4) ---"
            )

            # ------------------------------------------------
            # 音声
            # ------------------------------------------------

            audio_path = AUDIO_DIR / (
                f"fact_{fact_index:02d}_"
                f"scene_{chunk_index + 1:02d}.mp3"
            )

            create_tts(
                text,
                audio_path,
            )

            duration = get_audio_duration(audio_path)

            # 少しだけ余裕
            duration += 0.05

            print(
                f"[AUDIO] {duration:.2f}s"
            )

            # ------------------------------------------------
            # 字幕
            # ------------------------------------------------

            subtitle_path = make_subtitle_png(
                text,
                scene_number,
            )

            # ------------------------------------------------
            # ビジュアル
            # ------------------------------------------------

            scene_data = visuals[
                min(
                    chunk_index,
                    len(visuals) - 1,
                )
            ]

            visual = visual_manager.get_visual(
                scene_data
            )

            # ------------------------------------------------
            # セグメント生成
            # ------------------------------------------------

            segment_path = MEDIA_DIR / (
                f"segment_{scene_number:04d}.mp4"
            )

            if visual["type"] == "image":

                create_image_segment(
                    visual["path"],
                    subtitle_path,
                    audio_path,
                    segment_path,
                    duration,
                )

            elif visual["type"] == "video":

                create_video_segment(
                    visual["path"],
                    subtitle_path,
                    audio_path,
                    segment_path,
                    duration,
                )

            else:
                raise RuntimeError(
                    "不明なvisual type"
                )

            if not segment_path.exists():
                raise RuntimeError(
                    f"セグメント生成失敗: "
                    f"{segment_path}"
                )

            segment_files.append(segment_path)

            print(
                f"[SEGMENT OK] {segment_path}"
            )

    # ========================================================
    # 全セグメント結合
    # ========================================================

    print()
    print("=" * 70)
    print("全セグメントを結合")
    print("=" * 70)

    silent_video = OUTPUT_DIR / "silent_video.mp4"

    concat_segments(
        segment_files,
        silent_video,
    )

    # ========================================================
    # BGM
    # ========================================================

    print()
    print("=" * 70)
    print("BGM追加")
    print("=" * 70)

    final_video = OUTPUT_DIR / "final_video.mp4"

    add_bgm(
        silent_video,
        final_video,
    )

    # ========================================================
    # video_info.json
    # ========================================================

    info_path = create_video_info(
        final_video
    )

    # ========================================================
    # 最終確認
    # ========================================================

    duration = get_audio_duration(
        final_video
    )

    image_count = visual_manager.ira.count
    video_count = visual_manager.pexels.count

    print()
    print("=" * 70)
    print("完成！")
    print("=" * 70)

    print(
        f"Output: {final_video}"
    )

    print(
        f"Duration: {duration:.1f} seconds"
    )

    print(
        f"Duration: {duration / 60:.2f} minutes"
    )

    print(
        f"Irasutoya unique images: "
        f"{image_count}"
    )

    print(
        f"Pexels videos: "
        f"{video_count}"
    )

    print(
        f"Scenes: "
        f"{len(segment_files)}"
    )

    print(
        f"Video info: "
        f"{info_path}"
    )

    if not final_video.exists():
        raise RuntimeError(
            "final_video.mp4 が生成されていません"
        )

    if not info_path.exists():
        raise RuntimeError(
            "video_info.json が生成されていません"
        )

    print()
    print("YouTubeアップロード用ファイル確認OK")


if __name__ == "__main__":
    main()
