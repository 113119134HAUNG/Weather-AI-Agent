#check.py

import json
import re
from collections import defaultdict

# 簡易文字正規化
class SimpleNormalizer:
    @staticmethod
    def normalize_text(text):
        return re.sub(r"\s+", "", str(text).lower())

st = SimpleNormalizer()

# 扁平化資料結構（主詞、同義詞、linked_sememe 詞全納入）
def flatten_sememe_data(data, path=None, results=None):
    if results is None:
        results = {}
    if path is None:
        path = []
    if isinstance(data, dict):
        if "items" in data:
            for item in data["items"]:
                key = item.get("id") or item.get("zh") or item.get("en")
                if not key:
                    continue
                linked = item.get("linked_sememe", {})
                zh_syns = linked.get("zh", []) if isinstance(linked, dict) else []
                en_syns = linked.get("en", []) if isinstance(linked, dict) else []
                zh_syns = zh_syns if isinstance(zh_syns, list) else [zh_syns]
                en_syns = en_syns if isinstance(en_syns, list) else [en_syns]
                synonyms = list(set(filter(None, zh_syns + en_syns + item.get("synonyms", []))))
                # 強化主詞：如果沒有zh，直接抓linked_sememe首個zh
                zh_main = item.get("zh") or (zh_syns[0] if zh_syns else "")
                results[key] = {
                    "zh": zh_main,
                    "en": item.get("en", ""),
                    "synonyms": synonyms,
                    "categories": path.copy()
                }
        if "categories" in data:
            for cat_name, cat_data in data["categories"].items():
                flatten_sememe_data(cat_data, path + [cat_name], results)
    return results

# 類別定義與優先順序
CATEGORY_TREE = {
    "geo_feature": ["地形地貌", "水文環境", "火山與地質", "海洋與沿岸", "國家公園與自然保護區", "特殊自然景觀"],
    "climate": ["氣候", "氣候變遷", "季風", "乾季", "濕季", "氣候災害"],
    "weather": ["天氣", "晴朗與雲量變化", "降水與雷雨現象", "特殊降水與冰雪現象", "能見度與空氣現象", "極端天氣與災害", "鋒面與氣候變化", "天氣現象"],
    "location": ["直轄市", "省轄市", "縣", "縣轄市", "區", "鄉", "鎮", "城市", "都市區", "村", "里", "行政區"]
}
CATEGORY_PRIORITY = ["geo_feature", "climate", "weather", "location"]

# 語意矯正設定
WEATHER_OVERRIDE = ["冷鋒", "暖鋒", "滯留鋒", "鋒面雨", "雷陣雨", "短時強降雨", "間歇性小雨", "霜凍", "揚沙", "晴朗無雲"]
CLIMATE_EXCLUDE_FROM_WEATHER = ["強降雨事件", "年降雨量", "梅雨季"]

# 精準分類 + 語意補正 + fallback 城市詞尾判斷
def build_precise_maps(flattened_data):
    category_term_sets = {cat: set() for cat in CATEGORY_TREE.keys()}
    custom_synonym_map = {}
    classified_terms = set()
    unclassified_terms = set()
    reclassified_terms = []

    for key, entry in flattened_data.items():
        zh_entry = entry.get("zh", key)
        synonyms = entry.get("synonyms", [])
        zh_words = zh_entry if isinstance(zh_entry, list) else [zh_entry]
        all_words = zh_words + synonyms

        standard_word = st.normalize_text(zh_words[0]) if zh_words and zh_words[0] else None
        if not standard_word:
            continue

        # 建立 synonym map（主詞、同義詞、linked_sememe全部納入）
        for word in all_words:
            if isinstance(word, str) and word:
                custom_synonym_map[st.normalize_text(word)] = standard_word

        path = entry.get("categories", [])
        entry["classification"] = []
        entry["triggered_by"] = []

        classified = False
        for cat in CATEGORY_PRIORITY:
            keywords = CATEGORY_TREE[cat]
            matched = [p for p in path if any(k in p for k in keywords)]
            if matched:
                entry["classification"].append(cat)
                entry["triggered_by"].extend(matched)
                category_term_sets[cat].add(standard_word)
                classified_terms.add(standard_word)
                classified = True
                break

        # fallback 城市詞尾判斷
        if not classified:
            location_suffixes = ["市", "區", "鄉", "鎮", "村", "里", "島"]
            if any(isinstance(w, str) and w and w[-1] in location_suffixes for w in zh_words):
                category_term_sets["location"].add(standard_word)
                entry["classification"].append("location")
                entry["triggered_by"].append("suffix_match")
                classified_terms.add(standard_word)
                classified = True

        if not classified:
            unclassified_terms.add(standard_word)

    # 語意矯正 weather 與 climate 的誤歸類
    for word in list(classified_terms):
        original = None
        for cat, terms in category_term_sets.items():
            if word in terms:
                original = cat
                break
        if any(keyword in word for keyword in WEATHER_OVERRIDE):
            if word not in CLIMATE_EXCLUDE_FROM_WEATHER and original != "weather":
                if original:
                    category_term_sets[original].remove(word)
                category_term_sets["weather"].add(word)
                reclassified_terms.append((word, original, "weather"))

    return custom_synonym_map, category_term_sets, classified_terms, unclassified_terms, reclassified_terms

# 主程式
with open("/content/Weather-AI-Agent/sememe_synonym_OK.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

taiwan_data = raw_data.get("Country", {}).get("categories", {}).get("Taiwan", {})
flattened_data = flatten_sememe_data(taiwan_data)

custom_synonym_map, category_term_sets, classified_terms, unclassified_terms, reclassified_terms = build_precise_maps(flattened_data)

# 結果輸出
print(f"\n自訂 Synonym Map 已載入，共 {len(custom_synonym_map)} 筆\n")
for cat, terms in category_term_sets.items():
    print(f"分類「{cat}」詞彙數量：{len(terms)}")
    print(f"範例：{list(terms)[:10]}\n")

total_classified = sum(len(terms) for terms in category_term_sets.values())
print(f"已分類詞彙總數：{total_classified}")
print(f"未分類詞彙總數：{len(unclassified_terms)}")
if unclassified_terms:
    print(f"未分類範例：{list(unclassified_terms)[:10]}")
if reclassified_terms:
    print("\n語意矯正重新分類：")
    for word, from_cat, to_cat in reclassified_terms:
        print(f"    {word}：{from_cat} → {to_cat}")
