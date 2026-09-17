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
from PIL import Image, ImageOps, ImageFilter

# ============================================================
# CONFIG
# ============================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 30

VOICE = "ja-JP-NanamiNeural"
VOICE_RATE = "+6%"

MAX_FACTS = 10
IMAGES_PER_FACT = 2

BG_COLOR = (247, 243, 235)

IMAGE_DIR = Path("media/images")
VOICE_DIR = Path("media/voice")
CUT_DIR = Path("media/cuts")
SUB_DIR = Path("media/subtitles")
OUTPUT_DIR = Path("output")

for p in [IMAGE_DIR, VOICE_DIR, CUT_DIR, SUB_DIR, OUTPUT_DIR]:
    p.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 Chrome/126 Safari/537.36"
    )
})

# ============================================================
# FACT DATA
# ============================================================

FACTS = [
    {
        "title": "なぜ人は他人の目が気になる？",
        "hook": "人に見られている気がして、つい気にしてしまうことありませんか？",
        "answer": "実は人間の脳は、自分が思っている以上に他人から見られていると思いやすいんです。",
        "reason": "心理学では、実際よりも自分の存在や行動が周囲から注目されていると感じる現象が知られています。",
        "punch": "つまり、あなたが思っているほど、周りはあなたを見ていないかもしれません。",
        "keywords": ["人", "見る", "考える", "悩む"]
    },
    {
        "title": "なぜあくびはうつる？",
        "hook": "誰かがあくびをすると、自分まであくびをしたくなりませんか？",
        "answer": "あくびがうつる現象には、他人の行動を無意識に読み取る脳の働きが関係していると考えられています。",
        "reason": "人は周囲の表情や動きを自然にまねる傾向があり、あくびでも同じような反応が起きることがあります。",
        "punch": "だから、この記事を読んでいる今、あくびした人はちょっと危険です。",
        "keywords": ["あくび", "眠い", "人", "顔"]
    },
    {
        "title": "なぜ昔の恥ずかしい記憶を思い出す？",
        "hook": "寝る前に突然、昔の恥ずかしい記憶が蘇ることありませんか？",
        "answer": "強い感情を伴った出来事は、普通の出来事より記憶に残りやすいからです。",
        "reason": "特に恥ずかしさや不安などの感情は、その出来事を重要な情報として脳に残しやすくします。",
        "punch": "数年前の自分から突然ダメージを受けるのは、このせいかもしれません。",
        "keywords": ["恥ずかしい", "思い出す", "悩む", "人"]
    },
    {
        "title": "なぜスマホを触ると時間が早い？",
        "hook": "少しだけスマホを見るつもりが、気づいたら30分経っていたことありませんか？",
        "answer": "スマホには次々と新しい刺激が入ってくるため、時間そのものへの注意がそれやすくなります。",
        "reason": "短い動画や通知など、変化のある情報が連続すると、時間を細かく意識しにくくなります。",
        "punch": "5分だけのつもりが、気づけば夜。スマホあるあるです。",
        "keywords": ["スマホ", "見る", "驚く", "人"]
    },
    {
        "title": "なぜ好きな曲は何度も聴きたくなる？",
        "hook": "同じ曲を何十回も聴いてしまったことありませんか？",
        "answer": "好きな音楽を聴くと、脳の報酬系が刺激されることがあります。",
        "reason": "さらに曲の展開を知っていることで、次に何が来るか予測する楽しさも生まれます。",
        "punch": "だからお気に入りの曲は、何回聴いても飽きにくいんです。",
        "keywords": ["音楽", "聞く", "楽しい", "人"]
    },
    {
        "title": "なぜ寝る前に色々考えてしまう？",
        "hook": "布団に入った瞬間、急に色々なことを考え始めませんか？",
        "answer": "日中は仕事やスマホなどに注意が向いていますが、静かになると頭の中の考えに意識が向きやすくなります。",
        "reason": "周囲からの刺激が減ることで、未処理の考えや明日の予定などが浮かびやすくなるんです。",
        "punch": "布団に入ってから脳だけが元気になるのは、珍しいことではありません。",
        "keywords": ["寝る", "考える", "布団", "悩む"]
    },
    {
        "title": "なぜ初対面の印象は強く残る？",
        "hook": "初めて会った人の印象って、意外と覚えていませんか？",
        "answer": "人間は最初に得た情報を、その後の判断の基準にしやすい傾向があります。",
        "reason": "最初の表情や話し方、服装などから相手について素早く判断しようとするためです。",
        "punch": "最初の数秒が意外と記憶に残る理由はここにあります。",
        "keywords": ["初対面", "人", "話す", "笑う"]
    },
    {
        "title": "なぜ名前が出てこない？",
        "hook": "顔は分かるのに、名前だけ出てこないことありませんか？",
        "answer": "記憶そのものが消えたというより、保存された情報をうまく取り出せない場合があります。",
        "reason": "名前と顔の情報が別々に処理されることもあり、知っているのに言葉だけ出てこない状態が起こります。",
        "punch": "だから名前が出てこなくても、記憶力が悪いとは限りません。",
        "keywords": ["名前", "忘れる", "人", "考える"]
    },
    {
        "title": "なぜ他人の失敗は覚えている？",
        "hook": "自分の失敗は忘れたいのに、他人の失敗は妙に覚えていませんか？",
        "answer": "他人の行動は自分にとって重要な情報として記憶されることがあります。",
        "reason": "同じ失敗を避けるために、他人の行動を観察して学習する働きがあるからです。",
        "punch": "つまり、人の失敗を覚えてしまう脳にも理由があるんです。",
        "keywords": ["人", "失敗", "見る", "考える"]
    },
    {
        "title": "なぜ休日は一瞬で終わる？",
        "hook": "休みの日って、平日より時間が早く感じませんか？",
        "answer": "楽しい時間や刺激の多い時間は、あとから振り返ると短く感じられることがあります。",
        "reason": "一方で新しい体験が多いと、記憶にはたくさんの出来事が残り、時間感覚が変わることもあります。",
        "punch": "楽しい時間だけ一瞬なの、ちょっとずるいですよね。",
        "keywords": ["休日", "楽しい", "時間", "人"]
    },
    {
        "title": "なぜ炭酸を飲むとスッキリする？",
        "hook": "疲れたときに炭酸飲料を飲むとスッキリしませんか？",
        "answer": "炭酸の刺激が口や喉に伝わることで、強い感覚刺激として感じられます。",
        "reason": "冷たさや酸味などが組み合わさることで、爽快感として感じやすくなります。",
        "punch": "あのシュワシュワ感、ちゃんと刺激だったんです。",
        "keywords": ["炭酸", "飲む", "笑う", "人"]
    },
    {
        "title": "なぜ辛いものを食べたくなる？",
        "hook": "辛いものが苦手なのに、なぜかまた食べたくなることありませんか？",
        "answer": "辛さによる強い刺激のあとに、爽快感や満足感を感じる人がいます。",
        "reason": "唐辛子の辛味成分は痛みに近い刺激として感じられ、その刺激への反応が独特の快感につながることがあります。",
        "punch": "辛いのにもう一口。これにはちゃんと理由があります。",
        "keywords": ["辛い", "食べる", "驚く", "人"]
    },
    {
        "title": "なぜ物を探すと見つからない？",
        "hook": "目の前にあるのに、探している物が見つからないことありませんか？",
        "answer": "探すことに集中しすぎると、目に入っている情報を正しく認識できないことがあります。",
        "reason": "脳は必要な情報を優先して処理するため、探している物以外の情報を無視しやすくなります。",
        "punch": "そして誰かに『そこにあるよ』と言われた瞬間、急に見えるんです。",
        "keywords": ["探す", "見つける", "人", "驚く"]
    },
    {
        "title": "なぜ応援されると頑張れる？",
        "hook": "誰かに『頑張って』と言われるだけで、少し元気になることありませんか？",
        "answer": "人は自分が誰かに支えられていると感じることで、心理的な負担が軽くなることがあります。",
        "reason": "一人で抱えている感覚が減ると、行動を続ける力につながることがあります。",
        "punch": "たった一言が、人を動かすことって本当にあります。",
        "keywords": ["応援", "頑張る", "人", "笑う"]
    },
]

# ============================================================
# COMMAND
# ============================================================

def run(cmd):
    print("\n$", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def duration(path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path)
        ],
        capture_output=True,
        text=True,
        check=True
    )
    return float(result.stdout.strip())


# ============================================================
# IRASUTOYA
# ============================================================

ALLOWED_IMAGE_HOSTS = {
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

        return (
            host in ALLOWED_IMAGE_HOSTS
            and url.lower().split("?")[0].endswith(
                (".png", ".jpg", ".jpeg", ".webp")
            )
        )
    except Exception:
        return False


def extract_image_from_page(page_url):
    try:
        r = session.get(page_url, timeout=20)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            image_url = urljoin(page_url, og["content"])
            if valid_image_url(image_url):
                return image_url

        candidates = []

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if not src:
                continue

            src = urljoin(page_url, src)

            if not valid_image_url(src):
                continue

            width = img.get("width", "0")
            height = img.get("height", "0")

            try:
                score = int(width) * int(height)
            except Exception:
                score = 0

            candidates.append((score, src))

        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]

    except Exception as e:
        print("image extraction failed:", e)

    return None


def search_irasutoya(term):
    print("Irasutoya search:", term)

    url = (
        "https://www.irasutoya.com/search?q="
        + quote_plus(term)
    )

    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        pages = []

        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])

            if "irasutoya.com" not in href:
                continue

            if not re.search(r"/20\d{2}/", href):
                continue

            if href not in pages:
                pages.append(href)

        for page in pages[:12]:
            image_url = extract_image_from_page(page)

            if image_url:
                return {
                    "term": term,
                    "page": page,
                    "image": image_url
                }

    except Exception as e:
        print("Irasutoya search failed:", e)

    return None


def download_image(item, index):
    try:
        r = session.get(item["image"], timeout=30)
        r.raise_for_status()

        path = IMAGE_DIR / f"image_{index:03d}.png"

        with open(path, "wb") as f:
            f.write(r.content)

        im = Image.open(path).convert("RGBA")

        if im.width < 100 or im.height < 100:
            return None

        im.save(path)

        return path

    except Exception as e:
        print("download failed:", e)
        return None


def get_images_for_fact(fact, fact_index):
    results = []

    for keyword in fact["keywords"]:
        if len(results) >= IMAGES_PER_FACT:
            break

        item = search_irasutoya(keyword)

        if not item:
            continue

        if any(x["image"] == item["image"] for x in results):
            continue

        path = download_image(
            item,
            fact_index * 10 + len(results)
        )

        if path:
            results.append({
                "path": path,
                "term": keyword,
                "page": item["page"],
                "image": item["image"]
            })

    return results


# ============================================================
# IMAGE PROCESSING
# ============================================================

def make_visual(src, out_path, seed):
    random.seed(seed)

    canvas = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BG_COLOR
    )

    img = Image.open(src).convert("RGBA")

    # 少し柔らかく
    if img.width > 1600 or img.height > 1600:
        img.thumbnail((1500, 1500), Image.Resampling.LANCZOS)

    max_w = 900
    max_h = 1350

    scale = min(
        max_w / img.width,
        max_h / img.height,
        1.0
    )

    nw = max(1, int(img.width * scale))
    nh = max(1, int(img.height * scale))

    img = img.resize(
        (nw, nh),
        Image.Resampling.LANCZOS
    )

    # 影
    shadow = Image.new(
        "RGBA",
        (nw + 50, nh + 50),
        (0, 0, 0, 0)
    )

    alpha = img.getchannel("A")

    shadow_alpha = Image.new(
        "L",
        alpha.size,
        0
    )

    shadow_alpha.paste(
        alpha,
        (18, 18)
    )

    shadow_alpha = shadow_alpha.filter(
        ImageFilter.GaussianBlur(15)
    )

    shadow.paste(
        (0, 0, 0, 60),
        (0, 0),
        shadow_alpha
    )

    x = (WIDTH - nw) // 2
    y = 360 + random.randint(-80, 80)

    canvas.paste(
        shadow,
        (x - 25, y - 25),
        shadow
    )

    canvas.paste(
        img,
        (x, y),
        img
    )

    canvas.save(
        out_path,
        quality=95
    )


# ============================================================
# TEXT / SUBTITLE
# ============================================================

def clean_text(text):
    text = re.sub(r"\s+", "", text)
    return text.strip()


def split_subtitle(text):
    text = clean_text(text)

    if len(text) <= 18:
        return text

    if "。" in text:
        parts = text.split("。")
        parts = [x for x in parts if x]

        if len(parts) >= 2:
            return "\n".join(parts[:2])

    mid = len(text) // 2

    return (
        text[:mid]
        + "\n"
        + text[mid:]
    )


def ass_time(seconds):
    cs = int(round(seconds * 100))
    h = cs // 360000
    cs %= 360000
    m = cs // 6000
    cs %= 6000
    s = cs // 100
    cs %= 100

    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def write_ass(segments):
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Main,Noto Sans CJK JP,55,&H00FFF9EF,&H00FFF9EF,&H66000000,&H00000000,0,0,0,0,100,100,0,0,1,2,1,2,80,80,170,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for seg in segments:
        start = seg["start"]
        end = seg["end"]
        text = split_subtitle(seg["text"])

        lines.append(
            f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Main,,0,0,0,,{text}"
        )

    path = SUB_DIR / "main.ass"

    path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    return path


# ============================================================
# TTS
# ============================================================

async def tts(text, output):
    import edge_tts

    communicate = edge_tts.Communicate(
        text,
        VOICE,
        rate=VOICE_RATE
    )

    await communicate.save(str(output))


def make_voice(text, index):
    path = VOICE_DIR / f"voice_{index:03d}.mp3"

    if not path.exists():
        import asyncio
        asyncio.run(tts(text, path))

    return path


# ============================================================
# VIDEO SEGMENTS
# ============================================================

def create_segment(image, voice, output):
    d = duration(voice)

    if d < 0.4:
        d = 0.4

    run([
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", str(image),
        "-t", str(d),
        "-vf",
        (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "zoompan="
            "z='min(zoom+0.0008,1.08)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:"
            "s=1080x1920:"
            "fps=30"
        ),
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "24",
        "-pix_fmt", "yuv420p",
        str(output)
    ])

    return d


# ============================================================
# MAIN RENDER
# ============================================================

def main():
    random.seed(
        int(time.time()) ^
        os.getpid()
    )

    facts = random.sample(
        FACTS,
        min(MAX_FACTS, len(FACTS))
    )

    print("\nSelected facts:")

    for i, fact in enumerate(facts, 1):
        print(i, fact["title"])

    source_log = []

    all_segments = []
    total_time = 0.0

    visual_index = 0

    for fact_index, fact in enumerate(facts):
        print("\n==============================")
        print("FACT", fact_index + 1)
        print(fact["title"])
        print("==============================")

        images = get_images_for_fact(
            fact,
            fact_index
        )

        if not images:
            print("No Irasutoya image found. Skipping fact.")
            continue

        for item in images:
            source_log.append({
                "fact": fact["title"],
                "search_term": item["term"],
                "page": item["page"],
                "image": item["image"]
            })

        texts = [
            fact["hook"],
            fact["answer"],
            fact["reason"],
            fact["punch"]
        ]

        for local_index, text in enumerate(texts):
            voice = make_voice(
                text,
                visual_index
            )

            prepared = CUT_DIR / (
                f"visual_{visual_index:03d}.jpg"
            )

            source_image = images[
                local_index % len(images)
            ]["path"]

            make_visual(
                source_image,
                prepared,
                visual_index
            )

            segment = CUT_DIR / (
                f"segment_{visual_index:03d}.mp4"
            )

            d = create_segment(
                prepared,
                voice,
                segment
            )

            all_segments.append({
                "video": segment,
                "audio": voice,
                "text": text,
                "duration": d,
                "start": total_time,
                "end": total_time + d
            })

            total_time += d
            visual_index += 1

    if not all_segments:
        raise RuntimeError(
            "No video segments were generated."
        )

    # subtitles
    write_ass(all_segments)

    # concat video
    video_list = Path("media/video_concat.txt")

    with video_list.open("w", encoding="utf-8") as f:
        for seg in all_segments:
            f.write(
                "file '"
                + str(seg["video"].resolve())
                + "'\n"
            )

    run([
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(video_list),
        "-c", "copy",
        "media/video_no_audio.mp4"
    ])

    # concat voice
    audio_list = Path("media/audio_concat.txt")

    with audio_list.open("w", encoding="utf-8") as f:
        for seg in all_segments:
            f.write(
                "file '"
                + str(seg["audio"].resolve())
                + "'\n"
            )

    run([
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(audio_list),
        "-c:a", "aac",
        "-b:a", "192k",
        "media/narration.m4a"
    ])

    # BGM + narration + subtitles
    run([
        "ffmpeg",
        "-y",
        "-i", "media/video_no_audio.mp4",
        "-i", "media/narration.m4a",
        "-stream_loop", "-1",
        "-i", "media/bgm.ogg",
        "-filter_complex",
        (
            "[2:a]volume=0.035[bgm];"
            "[1:a]volume=1.0[narr];"
            "[narr][bgm]amix="
            "inputs=2:"
            "duration=first:"
            "dropout_transition=2[a]"
        ),
        "-map", "0:v",
        "-map", "[a]",
        "-vf",
        "subtitles=media/subtitles/main.ass",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "output/final_video.mp4"
    ])

    # thumbnail
    first_image = CUT_DIR / "visual_000.jpg"

    if first_image.exists():
        Image.open(first_image).save(
            "output/thumbnail.jpg",
            quality=95
        )

    # metadata
    first_title = facts[0]["title"]

    title = (
        first_title
        + " 知ると面白い身近な雑学10選"
    )

    info = {
        "title": title,
        "facts": [f["title"] for f in facts],
        "duration": total_time,
        "segments": len(all_segments),
        "style": {
            "image": "Irasutoya",
            "subtitle": "soft transparent background",
            "bgm": True,
            "multiple_cuts": True
        }
    }

    Path(
        "output/video_info.json"
    ).write_text(
        json.dumps(
            info,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    Path(
        "output/irasutoya_sources.json"
    ).write_text(
        json.dumps(
            source_log,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("\n================================")
    print("VIDEO COMPLETE")
    print("Duration:", round(total_time, 2), "seconds")
    print("Segments:", len(all_segments))
    print("================================")


if __name__ == "__main__":
    main()
