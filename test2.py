import json

# 1) อ่านไฟล์เดิม (ที่เป็น JSON string)
with open("full_market.txt", "r", encoding="utf-8") as f:
    raw = json.load(f)    # ได้เป็น string

# 2) แปลง JSON string → dict
market_dict = json.loads(raw)

# 3) เขียนกลับไปเป็นไฟล์ JSON ปกติ
with open("full_market_clean.json", "w", encoding="utf-8") as f:
    json.dump(market_dict, f, indent=4, ensure_ascii=False)

print("Done! Saved to full_market_clean.json")