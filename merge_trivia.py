import json
import hashlib
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

OUTPUT = BASE_DIR / "trivia.json"


def normalize(text):
    text = str(text).lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(
        r"[。、！？!?「」『』（）()・,，.!?]",
        "",
        text
    )
    return text


def make_hash(item):
    text = "|".join([
        normalize(item.get("category", "")),
        normalize(item.get("keyword", "")),
        normalize(item.get("title", "")),
        normalize(item.get("fact", "")),
        normalize(item.get("example", "")),
    ])

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def valid(item):
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
        if not str(item.get(key, "")).strip():
            return False

    return True


def main():

    print("=" * 60)
    print("LUMI TRIVIA MERGER")
    print("=" * 60)

    batch_files = sorted(
        BASE_DIR.glob("trivia_batch_*.json")
    )

    if not batch_files:
        print("trivia_batch_*.json がありません")
        return

    print(
        f"バッチファイル: {len(batch_files)}個"
    )

    all_items = []

    for file in batch_files:

        print(
            f"読み込み: {file.name}"
        )

        try:
            with open(
                file,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

        except Exception as e:

            print(
                f"  ERROR: {e}"
            )
            continue

        if not isinstance(data, list):

            print(
                "  配列ではないためスキップ"
            )
            continue

        print(
            f"  {len(data)}件"
        )

        all_items.extend(data)

    print()
    print(
        f"合計入力: {len(all_items):,}件"
    )

    # ========================================================
    # 重複除去
    # ========================================================

    unique = []

    hashes = set()
    titles = set()
    facts = set()

    invalid_count = 0
    duplicate_count = 0

    for item in all_items:

        if not valid(item):

            invalid_count += 1
            continue

        full_hash = make_hash(item)

        title = normalize(
            item["title"]
        )

        fact = normalize(
            item["fact"]
        )

        if full_hash in hashes:
            duplicate_count += 1
            continue

        if title in titles:
            duplicate_count += 1
            continue

        if fact in facts:
            duplicate_count += 1
            continue

        hashes.add(
            full_hash
        )

        titles.add(
            title
        )

        facts.add(
            fact
        )

        unique.append(item)

    # ========================================================
    # ID
    # ========================================================

    final = []

    for index, item in enumerate(
        unique,
        start=1
    ):

        new_item = {
            "id": index,
            "category": str(
                item["category"]
            ).strip(),
            "keyword": str(
                item["keyword"]
            ).strip(),
            "title": str(
                item["title"]
            ).strip(),
            "fact": str(
                item["fact"]
            ).strip(),
            "example": str(
                item["example"]
            ).strip()
        }

        final.append(
            new_item
        )

    # ========================================================
    # SAVE
    # ========================================================

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            final,
            f,
            ensure_ascii=False,
            indent=2
        )

    # ========================================================
    # CATEGORY
    # ========================================================

    categories = {}

    for item in final:

        category = item["category"]

        categories[category] = (
            categories.get(
                category,
                0
            ) + 1
        )

    # ========================================================
    # RESULT
    # ========================================================

    print()
    print("=" * 60)
    print("完成")
    print("=" * 60)

    print(
        f"最終件数       : {len(final):,}"
    )

    print(
        f"重複削除       : {duplicate_count:,}"
    )

    print(
        f"不正データ削除 : {invalid_count:,}"
    )

    print()

    print("カテゴリー:")

    for category, count in sorted(
        categories.items()
    ):

        print(
            f"  {category}: {count:,}"
        )

    print()

    if len(final) >= 10000:

        print(
            "🎉 10,000件達成！"
        )

    else:

        print(
            f"あと {10000 - len(final):,}件"
        )

    print()

    print(
        f"保存先: {OUTPUT}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
