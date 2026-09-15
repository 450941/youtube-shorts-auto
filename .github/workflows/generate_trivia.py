import json
import random

facts = [
    {
        "category": "科学",
        "topic": "光",
        "fact": "光は真空中では1秒間に約30万キロメートル進みます。"
    },
    {
        "category": "宇宙",
        "topic": "月",
        "fact": "月が地球の周りを一周するのにかかる時間は約27.3日です。"
    },
    {
        "category": "動物",
        "topic": "タコ",
        "fact": "タコには3つの心臓があります。"
    },
    {
        "category": "日本",
        "topic": "新幹線",
        "fact": "東海道新幹線は1964年に開業しました。"
    },
    {
        "category": "食べ物",
        "topic": "バナナ",
        "fact": "バナナは植物学上ではベリーの仲間に分類されます。"
    },
    {
        "category": "人体",
        "topic": "脳",
        "fact": "人間の脳は体重に占める割合が小さい一方で、多くのエネルギーを消費します。"
    },
    {
        "category": "自然",
        "topic": "虹",
        "fact": "虹は太陽の光が水滴の中で屈折や反射することで見えます。"
    },
    {
        "category": "動物",
        "topic": "イルカ",
        "fact": "イルカは睡眠中も呼吸する必要があるため、脳の左右を交互に休ませることがあります。"
    },
    {
        "category": "宇宙",
        "topic": "太陽",
        "fact": "太陽から地球まで光が届くには約8分20秒かかります。"
    },
    {
        "category": "日本",
        "topic": "富士山",
        "fact": "富士山は日本で最も高い山で、標高は3776メートルです。"
    }
]

# 重複を避けながら並び替え
random.shuffle(facts)

# IDを付ける
for i, item in enumerate(facts, 1):
    item["id"] = i

with open("trivia.json", "w", encoding="utf-8") as f:
    json.dump(
        facts,
        f,
        ensure_ascii=False,
        indent=2
    )

print("===================================")
print("trivia.json 作成完了")
print("雑学データ数:", len(facts))
print("===================================")
