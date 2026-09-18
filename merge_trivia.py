import json
import hashlib
import re
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent
OUTPUT = BASE_DIR / "trivia.json"

# ============================================================
# 設定
# ============================================================

BATCH_FILES = [
    BASE_DIR / f"trivia_batch_{i:03d}.json"
    for i in range(1, 11)
]

EXPECTED_TOTAL = 1000

EXPECTED_CATEGORY_COUNTS = {
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

# 1バッチあたりの予定数
EXPECTED_BATCH_TOTAL = 100


# ============================================================
# 正規化
# ============================================================

def normalize(text):
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
# ハッシュ
# ============================================================

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


# ============================================================
# データチェック
# ============================================================

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

        if not str(
            item.get(key, "")
        ).strip():

            return False

    return True


# ============================================================
# メイン
# ============================================================

def main():

    print("=" * 70)
    print("LUMI TRIVIA MERGER")
    print("trivia_batch_001 ～ 010")
    print("=" * 70)

    # --------------------------------------------------------
    # バッチ存在確認
    # --------------------------------------------------------

    print()
    print("【バッチファイル確認】")

    missing_files = []

    for file in BATCH_FILES:

        if file.exists():

            print(
                f"  OK   {file.name}"
            )

        else:

            print(
                f"  NG   {file.name}"
            )

            missing_files.append(file.name)

    if missing_files:

        print()
        print("❌ ファイルが不足しています")

        for name in missing_files:
            print(
                f"  - {name}"
            )

        return

    # --------------------------------------------------------
    # 読み込み
    # --------------------------------------------------------

    print()
    print("【読み込み】")

    all_items = []

    batch_counts = {}

    for file in BATCH_FILES:

        try:

            with open(
                file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        except Exception as e:

            print()
            print(
                f"❌ {file.name} の読み込み失敗"
            )

            print(e)

            return

        if not isinstance(data, list):

            print()
            print(
                f"❌ {file.name} がJSON配列ではありません"
            )

            return

        count = len(data)

        batch_counts[
            file.name
        ] = count

        print(
            f"  {file.name}: {count}件"
        )

        all_items.extend(data)

    # --------------------------------------------------------
    # バッチ件数チェック
    # --------------------------------------------------------

    print()
    print("【バッチ件数チェック】")

    batch_error = False

    for name, count in batch_counts.items():

        if count != EXPECTED_BATCH_TOTAL:

            print(
                f"  ⚠ {name}: {count}件"
                f" → 100件ではありません"
            )

            batch_error = True

        else:

            print(
                f"  OK {name}: 100件"
            )

    print()

    print(
        f"合計入力: {len(all_items):,}件"
    )

    # --------------------------------------------------------
    # 必須項目チェック
    # --------------------------------------------------------

    print()
    print("【データ形式チェック】")

    invalid_items = []

    for index, item in enumerate(
        all_items,
        start=1
    ):

        if not valid(item):

            invalid_items.append(index)

    if invalid_items:

        print(
            f"❌ 不正データ: "
            f"{len(invalid_items)}件"
        )

        print(
            "該当番号:",
            invalid_items[:20]
        )

        return

    print(
        "OK: すべてのデータ形式が正常"
    )

    # --------------------------------------------------------
    # 重複除去
    # --------------------------------------------------------

    print()
    print("【重複チェック】")

    unique = []

    hashes = set()
    titles = set()
    facts = set()

    duplicate_count = 0

    for item in all_items:

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

    print(
        f"重複: {duplicate_count}件"
    )

    print(
        f"重複除去後: {len(unique):,}件"
    )

    # --------------------------------------------------------
    # ID付与
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # カテゴリー集計
    # --------------------------------------------------------

    categories = Counter(
        item["category"]
        for item in final
    )

    print()
    print("【カテゴリー集計】")

    category_error = False

    for category, expected in (
        EXPECTED_CATEGORY_COUNTS.items()
    ):

        actual = categories.get(
            category,
            0
        )

        if actual == expected:

            print(
                f"  OK  {category}: "
                f"{actual}件"
            )

        else:

            print(
                f"  ⚠  {category}: "
                f"{actual}件"
                f" / 予定 {expected}件"
            )

            category_error = True

    # --------------------------------------------------------
    # 保存
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 最終結果
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("【最終結果】")
    print("=" * 70)

    print(
        f"入力件数       : {len(all_items):,}"
    )

    print(
        f"重複削除       : {duplicate_count:,}"
    )

    print(
        f"最終件数       : {len(final):,}"
    )

    print(
        f"目標件数       : {EXPECTED_TOTAL:,}"
    )

    print()

    # --------------------------------------------------------
    # 1000件判定
    # --------------------------------------------------------

    if len(final) == EXPECTED_TOTAL:

        print(
            "🎉🎉🎉 1000件完成！"
        )

    elif len(final) > EXPECTED_TOTAL:

        print(
            f"⚠ 目標より "
            f"{len(final) - EXPECTED_TOTAL}件多いです"
        )

    else:

        print(
            f"⚠ 目標まで "
            f"{EXPECTED_TOTAL - len(final)}件不足"
        )

    # --------------------------------------------------------
    # 警告
    # --------------------------------------------------------

    if batch_error:

        print()
        print(
            "⚠ バッチの中に100件ではない"
            "ファイルがあります"
        )

    if duplicate_count > 0:

        print()
        print(
            "⚠ 重複データがありました"
        )

    if category_error:

        print()
        print(
            "⚠ カテゴリー数が予定と一致していません"
        )

    # --------------------------------------------------------
    # 保存場所
    # --------------------------------------------------------

    print()
    print(
        f"保存先: {OUTPUT}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
