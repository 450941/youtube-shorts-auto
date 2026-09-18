# ============================================================
# TRIVIA BATCH GENERATOR
# 1,000件ずつ追加して最終的に10,000件へ
# ============================================================

import json
import hashlib
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

TRIVIA_FILE = BASE_DIR / "trivia.json"


# ============================================================
# 10,000件のカテゴリー設計
# ============================================================

CATEGORY_TARGETS = {
    "身近な雑学": 2000,
    "心理学": 1500,
    "科学": 1500,
    "歴史": 1000,
    "哲学": 800,
    "人体": 800,
    "食べ物": 600,
    "動物・自然": 600,
    "テクノロジー": 500,
    "社会・文化": 500,
    "政治・制度": 200,
}


# ============================================================
# NORMALIZE
# ============================================================

def normalize(text):

    if text is None:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"\s+",
        "",
        text
    )

    text = re.sub(
        r"[。、！？!?「」『』（）()・,，.!?]",
        "",
        text
    )

    return text


# ============================================================
# HASH
# ============================================================

def make_hash(item):

    text = "|".join([
        normalize(item.get("category")),
        normalize(item.get("keyword")),
        normalize(item.get("title")),
        normalize(item.get("fact")),
        normalize(item.get("example")),
    ])

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


# ============================================================
# LOAD
# ============================================================

def load_database():

    if not TRIVIA_FILE.exists():

        return []

    try:

        with open(
            TRIVIA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if isinstance(data, list):

            return data

    except Exception as e:

        print(
            f"読み込みエラー: {e}"
        )

    return []


# ============================================================
# SAVE
# ============================================================

def save_database(database):

    with open(
        TRIVIA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            database,
            f,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# VALIDATE
# ============================================================

def valid_item(item):

    if not isinstance(
        item,
        dict
    ):
        return False

    fields = [
        "category",
        "keyword",
        "title",
        "fact",
        "example"
    ]

    for field in fields:

        value = item.get(field)

        if not value:
            return False

        if len(
            str(value).strip()
        ) < 5:
            return False

    return True


# ============================================================
# DUPLICATE CHECK
# ============================================================

def remove_duplicates(database):

    result = []

    hashes = set()

    titles = set()

    facts = set()

    for item in database:

        if not valid_item(item):

            continue

        full_hash = make_hash(
            item
        )

        title_hash = normalize(
            item["title"]
        )

        fact_hash = normalize(
            item["fact"]
        )

        # 完全重複
        if full_hash in hashes:
            continue

        # 同タイトル
        if title_hash in titles:
            continue

        # 同じ説明
        if fact_hash in facts:
            continue

        hashes.add(
            full_hash
        )

        titles.add(
            title_hash
        )

        facts.add(
            fact_hash
        )

        result.append(
            item
        )

    return result


# ============================================================
# ID
# ============================================================

def rebuild_ids(database):

    result = []

    for number, item in enumerate(
        database,
        start=1
    ):

        item = dict(item)

        item["id"] = number

        result.append(
            item
        )

    return result


# ============================================================
# CATEGORY COUNT
# ============================================================

def category_counts(database):

    counts = {}

    for item in database:

        category = item.get(
            "category",
            "不明"
        )

        counts[category] = (
            counts.get(
                category,
                0
            ) + 1
        )

    return counts


# ============================================================
# REMAINING
# ============================================================

def show_status(database):

    counts = category_counts(
        database
    )

    print()
    print("=" * 60)
    print("TRIVIA DATABASE STATUS")
    print("=" * 60)

    print(
        f"TOTAL: {len(database):,} / 10,000"
    )

    print(
        f"REMAINING: "
        f"{max(0, 10000 - len(database)):,}"
    )

    print()

    for category, target in CATEGORY_TARGETS.items():

        current = counts.get(
            category,
            0
        )

        remaining = max(
            0,
            target - current
        )

        print(
            f"{category:12s} "
            f"{current:4d} / "
            f"{target:4d} "
            f"(残り {remaining})"
        )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("LUMI 10,000 TRIVIA DATABASE")
    print("=" * 60)

    database = load_database()

    print(
        f"読み込み件数: {len(database):,}"
    )

    # 重複削除
    database = remove_duplicates(
        database
    )

    print(
        f"重複削除後: {len(database):,}"
    )

    # ID再構築
    database = rebuild_ids(
        database
    )

    # 保存
    save_database(
        database
    )

    show_status(
        database
    )


if __name__ == "__main__":

    main()
