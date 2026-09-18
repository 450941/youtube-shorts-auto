import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent
OUTPUT = BASE_DIR / "trivia.json"

BATCH_FILES = [
    BASE_DIR / f"trivia_batch_{i:03d}.json"
    for i in range(1, 11)
]

EXPECTED_TOTAL = 1000


def main():

    print("=" * 70)
    print("LUMI TRIVIA MERGER")
    print("001 ～ 010")
    print("=" * 70)

    all_items = []

    # ============================================================
    # 読み込み
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

    print()
    print(
        f"入力合計: {len(all_items)}件"
    )

    # ============================================================
    # データチェック
    # ============================================================

    required = [
        "category",
        "keyword",
        "title",
        "fact",
        "example"
    ]

    valid_items = []

    for index, item in enumerate(
        all_items,
        start=1
    ):

        if not isinstance(item, dict):
            print(
                f"WARNING: {index}番目がオブジェクトではありません"
            )
            continue

        missing = [
            key
            for key in required
            if not str(item.get(key, "")).strip()
        ]

        if missing:

            print(
                f"WARNING: {index}番目に不足:"
                f" {missing}"
            )

            continue

        valid_items.append(item)

    print(
        f"有効データ: {len(valid_items)}件"
    )

    # ============================================================
    # 重複削除しない
    # ============================================================

    print()
    print(
        "重複削除: OFF"
    )

    print(
        "全データをそのまま保持します"
    )

    # ============================================================
    # IDを振り直す
    # ============================================================

    final = []

    for index, item in enumerate(
        valid_items,
        start=1
    ):

        final.append({

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
            final,
            f,
            ensure_ascii=False,
            indent=2
        )

    # ============================================================
    # カテゴリー集計
    # ============================================================

    categories = Counter(
        item["category"]
        for item in final
    )

    print()
    print("=" * 70)
    print("カテゴリー")
    print("=" * 70)

    for category, count in sorted(
        categories.items()
    ):

        print(
            f"{category}: {count}件"
        )

    # ============================================================
    # 結果
    # ============================================================

    print()
    print("=" * 70)
    print("完成")
    print("=" * 70)

    print(
        f"最終件数: {len(final)}件"
    )

    print(
        f"目標件数: {EXPECTED_TOTAL}件"
    )

    if len(final) == EXPECTED_TOTAL:

        print()
        print(
            "🎉 1000件完成！"
        )

    elif len(final) < EXPECTED_TOTAL:

        print()
        print(
            f"⚠ {EXPECTED_TOTAL - len(final)}件不足"
        )

    else:

        print()
        print(
            f"⚠ {len(final) - EXPECTED_TOTAL}件多い"
        )

    print()
    print(
        f"保存先: {OUTPUT}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
