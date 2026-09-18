# ============================================================
# TRIVIA 10,000 DATABASE BUILDER
# ============================================================

import json
import hashlib
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_FILE = BASE_DIR / "trivia.json"
REPORT_FILE = BASE_DIR / "trivia_report.json"

TARGET_COUNT = 10000


# ============================================================
# CATEGORIES
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

    text = str(text)

    text = text.lower()

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

    content = "|".join([
        normalize(item.get("category")),
        normalize(item.get("keyword")),
        normalize(item.get("title")),
        normalize(item.get("fact")),
        normalize(item.get("example")),
    ])

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


# ============================================================
# LOAD EXISTING DATABASE
# ============================================================

def load_database():

    if not OUTPUT_FILE.exists():

        return []

    try:

        with open(
            OUTPUT_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if not isinstance(data, list):

            return []

        return data

    except Exception:

        return []


# ============================================================
# VALIDATE ITEM
# ============================================================

def validate_item(item):

    if not isinstance(item, dict):

        return False

    required = [
        "category",
        "keyword",
        "title",
        "fact",
        "example"
    ]

    for key in required:

        value = item.get(key)

        if not value:
            return False

        if len(str(value).strip()) < 5:
            return False

    return True


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(database):

    unique = []

    hashes = set()

    title_hashes = set()

    fact_hashes = set()

    for item in database:

        if not validate_item(item):
            continue

        full_hash = make_hash(item)

        title_hash = normalize(
            item["title"]
        )

        fact_hash = normalize(
            item["fact"]
        )

        if full_hash in hashes:
            continue

        if title_hash in title_hashes:
            continue

        if fact_hash in fact_hashes:
            continue

        hashes.add(
            full_hash
        )

        title_hashes.add(
            title_hash
        )

        fact_hashes.add(
            fact_hash
        )

        unique.append(item)

    return unique


# ============================================================
# ASSIGN IDS
# ============================================================

def assign_ids(database):

    result = []

    for index, item in enumerate(
        database,
        start=1
    ):

        new_item = dict(item)

        new_item["id"] = index

        result.append(
            new_item
        )

    return result


# ============================================================
# CATEGORY REPORT
# ============================================================

def category_report(database):

    counts = {}

    for item in database:

        category = item.get(
            "category",
            "不明"
        )

        counts[category] = (
            counts.get(category, 0)
            + 1
        )

    return counts


# ============================================================
# SAVE
# ============================================================

def save_database(database):

    with open(
        OUTPUT_FILE,
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
# MAIN
# ============================================================

def main():

    print("=" * 60)

    print(
        "TRIVIA 10,000 DATABASE BUILDER"
    )

    print("=" * 60)

    database = load_database()

    print(
        f"読み込み: {len(database):,}件"
    )

    # 重複除去
    database = remove_duplicates(
        database
    )

    print(
        f"重複除去後: {len(database):,}件"
    )

    # ID振り直し
    database = assign_ids(
        database
    )

    # 保存
    save_database(
        database
    )

    counts = category_report(
        database
    )

    report = {
        "total": len(database),
        "target": TARGET_COUNT,
        "remaining": max(
            0,
            TARGET_COUNT - len(database)
        ),
        "complete": (
            len(database)
            >= TARGET_COUNT
        ),
        "categories": counts,
        "category_targets": CATEGORY_TARGETS
    }

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()

    print(
        f"現在の件数: {len(database):,}"
    )

    print(
        f"目標件数:   {TARGET_COUNT:,}"
    )

    print(
        f"残り:       "
        f"{max(0, TARGET_COUNT - len(database)):,}"
    )

    print()

    print("カテゴリー:")

    for category, count in sorted(
        counts.items()
    ):

        print(
            f"  {category}: {count:,}"
        )

    print()

    if len(database) >= TARGET_COUNT:

        print(
            "🎉 10,000件達成"
        )

    else:

        print(
            "まだ生成が必要です"
        )

    print("=" * 60)


if __name__ == "__main__":

    main()
