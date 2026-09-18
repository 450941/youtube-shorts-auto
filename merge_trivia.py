import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
OUTPUT = BASE_DIR / "trivia.json"

BATCH_FILES = [
    BASE_DIR / f"trivia_batch_{i:03d}.json"
    for i in range(1, 11)
]

EXTRA_FILE = BASE_DIR / "trivia_extra.json"

TARGET_COUNTS = {
    "身近な雑学": 250,
    "心理学": 150,
    "科学": 150,
    "歴史": 100,
    "哲学": 50,
    "人体": 100,
    "食べ物": 50,
    "動物・自然": 50,
    "テクノロジー": 50,
    "社会・文化": 50,
}


def main():

    print("=" * 70)
    print("LUMI TRIVIA MERGER")
    print("001 ～ 010 + EXTRA")
    print("=" * 70)

    all_items = []

    # ============================================================
    # バッチ読み込み
    # ============================================================

    for file in BATCH_FILES:

        if not file.exists():
            print(f"ERROR: {file.name} がありません")
            raise SystemExit(1)

        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if not isinstance(data, list):
            print(f"ERROR: {file.name} が配列ではありません")
            raise SystemExit(1)

        print(
            f"{file.name}: {len(data)}件"
        )

        all_items.extend(data)

    # ============================================================
    # EXTRA
    # ============================================================

    if EXTRA_FILE.exists():

        with open(
            EXTRA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            extra = json.load(f)

        if not isinstance(extra, list):
            print("ERROR: trivia_extra.json が配列ではありません")
            raise SystemExit(1)

        print(
            f"trivia_extra.json: {len(extra)}件"
        )

        all_items.extend(extra)

    else:

        print(
            "WARNING: trivia_extra.json がありません"
        )

    print()
    print(
        f"入力合計: {len(all_items)}件"
    )

    # ============================================================
    # データをカテゴリーごとに分ける
    # ============================================================

    grouped = defaultdict(list)

    required = [
        "category",
        "keyword",
        "title",
        "fact",
        "example"
    ]

    invalid = 0

    for item in all_items:

        if not isinstance(item, dict):
            invalid += 1
            continue

        if any(
            not str(item.get(key, "")).strip()
            for key in required
        ):
            invalid += 1
            continue

        category = str(
            item["category"]
        ).strip()

        if category in TARGET_COUNTS:

            grouped[category].append(item)

    # ============================================================
    # カテゴリー確認
    # ============================================================

    print()
    print("=" * 70)
    print("カテゴリー確認")
    print("=" * 70)

    for category, target in TARGET_COUNTS.items():

        available = len(
            grouped[category]
        )

        print(
            f"{category}: "
            f"{available}件 → 必要 {target}件"
        )

        if available < target:

            print(
                f"ERROR: {category} が "
                f"{target - available}件不足しています"
            )

            raise SystemExit(1)

    # ============================================================
    # 各カテゴリーから必要数だけ採用
    # ============================================================

    final = []

    for category, target in TARGET_COUNTS.items():

        selected = grouped[category][:target]

        final.extend(selected)

    # ============================================================
    # IDを1から振り直す
    # ============================================================

    result = []

    for index, item in enumerate(
        final,
        start=1
    ):

        result.append({

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
        })

    # ============================================================
    # 保存
    # ============================================================

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    # ============================================================
    # 最終確認
    # ============================================================

    print()
    print("=" * 70)
    print("最終結果")
    print("=" * 70)

    print(
        f"最終件数: {len(result)}件"
    )

    print()

    for category, target in TARGET_COUNTS.items():

        count = sum(
            1
            for item in result
            if item["category"] == category
        )

        print(
            f"{category}: {count}件"
        )

    print()

    if len(result) != 1000:

        print(
            f"ERROR: 1000件ではありません"
            f" → {len(result)}件"
        )

        raise SystemExit(1)

    print(
        "🎉 1000件完成！"
    )

    print()
    print(
        f"保存先: {OUTPUT}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
