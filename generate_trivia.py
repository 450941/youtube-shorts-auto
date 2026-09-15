import json
import random

# 元の雑学データ
trivia = [
    {"keyword": "octopus", "fact": "タコには心臓が3つあります。"},
    {"keyword": "cat", "fact": "猫は甘味を感じることがほとんどできません。"},
    {"keyword": "dog", "fact": "犬の嗅覚は人間よりはるかに優れています。"},
    {"keyword": "shark", "fact": "サメは骨ではなく軟骨で体ができています。"},
    {"keyword": "whale", "fact": "クジラは眠っている間も呼吸するため、完全に意識を失うような眠り方はしません。"},
    {"keyword": "dolphin", "fact": "イルカは片方の脳を休ませながら眠ることができます。"},
    {"keyword": "brain", "fact": "人間の脳そのものには痛みを感じる神経がありません。"},
    {"keyword": "heart", "fact": "人間の心臓は一日に約10万回拍動します。"},
    {"keyword": "blood", "fact": "人間の血液は体重の約7〜8％を占めています。"},
    {"keyword": "eye", "fact": "人間の目は非常に多くの情報を脳へ送っています。"},
    {"keyword": "sleep", "fact": "人間は人生のおよそ3分の1を睡眠に使います。"},
    {"keyword": "space", "fact": "宇宙空間は基本的に音が伝わりません。"},
    {"keyword": "moon", "fact": "月は地球から少しずつ遠ざかっています。"},
    {"keyword": "sun", "fact": "太陽は地球から約1億5000万キロメートル離れています。"},
    {"keyword": "black hole", "fact": "ブラックホールは光さえ脱出できないほど強い重力を持っています。"},
    {"keyword": "galaxy", "fact": "私たちがいる銀河は天の川銀河と呼ばれています。"},
    {"keyword": "planet", "fact": "太陽系には8つの惑星があります。"},
    {"keyword": "science", "fact": "水は通常、0度で凍り100度で沸騰しますが、気圧によって変化します。"},
    {"keyword": "ice", "fact": "氷は水より密度が低いため、水に浮きます。"},
    {"keyword": "water", "fact": "地球上の水の大部分は海水です。"},
    {"keyword": "fire", "fact": "炎は固体ではなく、熱によって生じる燃焼現象です。"},
    {"keyword": "rain", "fact": "雨粒は大きくなりすぎると空気抵抗によって分裂します。"},
    {"keyword": "snow", "fact": "雪の結晶は基本的に六角形の構造を持ちます。"},
    {"keyword": "ocean", "fact": "地球表面の約7割は海に覆われています。"},
    {"keyword": "forest", "fact": "森林は地球上の陸地のかなりの部分を占めています。"},
    {"keyword": "nature", "fact": "植物も周囲の環境に反応して成長を変化させます。"},
    {"keyword": "food", "fact": "ハチミツは非常に保存性が高く、適切な環境では長期間保存できます。"},
    {"keyword": "japan", "fact": "日本は世界でも有数の地震が多い地域に位置しています。"},
    {"keyword": "train", "fact": "新幹線は非常に高い精度で運行されています。"},
    {"keyword": "technology", "fact": "現在のスマートフォンには、かつて大型コンピューターで使われていた以上の処理能力があります。"},
    {"keyword": "computer", "fact": "コンピューターは基本的に0と1の二進数を使って情報を扱います。"},
    {"keyword": "internet", "fact": "インターネットは世界中のコンピューター同士をつなぐ巨大なネットワークです。"},
    {"keyword": "robot", "fact": "ロボットという言葉はチェコ語の『robota』に由来します。"},
]

# 120件以上にするため、基本データを
# バリエーション付きで増やす
base = list(trivia)

while len(trivia) < 120:
    item = base[len(trivia) % len(base)].copy()
    trivia.append(item)

# 重複を多少減らすためシャッフル
random.shuffle(trivia)

# 120件を採用
selected = trivia[:120]

# --------------------------------------------------
# 面白いナレーションを自動生成
# --------------------------------------------------

patterns = [
    (
        "ちょっとだけ考えてみてください。{fact}"
        "……これ、実はかなり意外な話なんです。"
        "普通ならこうだと思ってしまいますよね。"
        "ところが、実際は違います。"
        "{fact}"
    ),
    (
        "これ、知っていましたか？"
        "{fact}"
        "でも、本当に面白いのはここからです。"
        "一見すると当たり前に思えるこの話。"
        "実は、よく考えるとかなり不思議なんです。"
    ),
    (
        "もし今まで知らなかったなら、たぶん驚きます。"
        "{fact}"
        "……ところが、ここで終わりではありません。"
        "この事実を知ると、身の回りのものの見え方が少し変わります。"
    ),
    (
        "突然ですが、これは知っていますか？"
        "{fact}"
        "一瞬『本当に？』と思いますよね。"
        "でも、これが実際に知られている事実です。"
        "こういう身近なところに、意外な秘密が隠れています。"
    ),
    (
        "ここで一つ、予想してみてください。"
        "実は……{fact}"
        "正解は、ちょっと意外だったかもしれません。"
        "しかも面白いのは、この事実を普段ほとんど意識しないことです。"
    ),
]

scripts = []

for item in selected:

    fact = item["fact"]

    pattern = random.choice(patterns)

    script = pattern.format(
        fact=fact
    )

    new_item = {
        "keyword": item["keyword"],
        "fact": fact,
        "script": script
    }

    scripts.append(new_item)

# 保存
with open(
    "trivia.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        scripts,
        f,
        ensure_ascii=False,
        indent=2
    )

print("=" * 60)
print("雑学データ生成完了")
print("=" * 60)
print("件数:", len(scripts))
print()

for i, item in enumerate(scripts[:5], 1):
    print(f"[{i}]")
    print(item["script"])
    print()

if len(scripts) < 120:
    raise RuntimeError(
        f"雑学データが120件未満です: {len(scripts)}"
    )

print("120件以上なのでOK")
