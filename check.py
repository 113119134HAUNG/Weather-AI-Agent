#check.py

你說：
import re
import json
from collections import defaultdict

# 簡易文字正規化
class SimpleNormalizer:
    @staticmethod
    def normalize_text(text):
        return re.sub(r"\s+", "", str(text).lower())

st = SimpleNormalizer()

# 展平 JSON 結構
def flatten_sememe_data(data, path=None, results=None):
    if results is None:
        results = {}
    if path is None:
        path = []

    if not isinstance(data, dict):
        return results

    if "items" in data and isinstance(data["items"], list):
        for item in data["items"]:
            if not isinstance(item, dict):
                continue
            key = item.get("id") or item.get("zh") or item.get("en")
            if not key:
                continue
            linked = item.get("linked_sememe", {})
            zh_syns = linked.get("zh", []) if isinstance(linked, dict) else []
            en_syns = linked.get("en", []) if isinstance(linked, dict) else []
            zh_syns = zh_syns if isinstance(zh_syns, list) else [zh_syns]
            en_syns = en_syns if isinstance(en_syns, list) else [en_syns]
            synonyms = list(set(filter(None, zh_syns + en_syns + item.get("synonyms", []))))
            zh_main = item.get("zh") or (zh_syns[0] if zh_syns else "")
            results[key] = {
                "zh": zh_main,
                "en": item.get("en", ""),
                "synonyms": synonyms,
                "categories": path.copy()
            }

    if "categories" in data and isinstance(data["categories"], dict):
        for cat_name, cat_data in data["categories"].items():
            flatten_sememe_data(cat_data, path + [cat_name], results)

    if "subcategories" in data and isinstance(data["subcategories"], dict):
        for subcat_name, subcat_data in data["subcategories"].items():
            flatten_sememe_data(subcat_data, path + [subcat_name], results)

    for key, value in data.items():
        if key not in {"items", "categories", "subcategories"}:
            if isinstance(value, dict):
                if any(k in value for k in ("items", "categories", "subcategories")):
                    flatten_sememe_data(value, path + [key], results)

    return results

# 對應前綴 → 分類型別
CATEGORY_PREFIX_TO_TYPE = {
    "tw-geo-": "geo_feature",
    "tw-climate-": "climate",
    "tw-weather-": "weather",
    "weather-air-quality-": "weather",
    "weather-season-": "weather",
    "weather-optical-": "weather",
    "climate-types-": "climate",
    "tw-city-": "location",
    "tw-basic-": "location",
}

WEATHER_OVERRIDE = ["冷鋒", "暖鋒", "滯留鋒", "鋒面雨", "雷陣雨", "短時強降雨", "間歇性小雨", "霜凍", "揚沙", "晴朗無雲", "大雷雨", "豪雨", "雷擊"]
CLIMATE_EXCLUDE_FROM_WEATHER = ["強降雨事件", "年降雨量", "梅雨季", "平均氣溫變化", "氣候區劃"]

# 分類主邏輯
def build_precise_maps(flattened_data):
    category_term_sets = defaultdict(set)
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

        for word in all_words:
            if isinstance(word, str) and word:
                custom_synonym_map[st.normalize_text(word)] = standard_word

        entry["classification"] = []
        entry["triggered_by"] = []

        classified = False

        # 優先從 categories 判斷分類
        for cat in entry.get("categories", []):
            for prefix, cat_type in CATEGORY_PREFIX_TO_TYPE.items():
                if cat.startswith(prefix):
                    entry["classification"].append(cat_type)
                    entry["triggered_by"].append(cat)
                    category_term_sets[cat_type].add(standard_word)
                    classified_terms.add(standard_word)
                    classified = True
                    break
            if classified:
                break

        # 如果還沒分類，嘗試從 id 推斷分類
        if not classified:
            item_id = key.lower()
            for prefix, cat_type in CATEGORY_PREFIX_TO_TYPE.items():
                if item_id.startswith(prefix):
                    entry["classification"].append(cat_type)
                    entry["triggered_by"].append("id:" + item_id)
                    category_term_sets[cat_type].add(standard_word)
                    classified_terms.add(standard_word)
                    classified = True
                    break

        # 如果還沒分類，嘗試從 related_items 判斷
        if not classified:
            for rel_id in entry.get("related_items", []):
                rel_id = rel_id.lower()
                for prefix, cat_type in CATEGORY_PREFIX_TO_TYPE.items():
                    if rel_id.startswith(prefix):
                        entry["classification"].append(cat_type)
                        entry["triggered_by"].append("related:" + rel_id)
                        category_term_sets[cat_type].add(standard_word)
                        classified_terms.add(standard_word)
                        classified = True
                        break
                if classified:
                    break

        # 再來從語義詞彙模糊比對（linked_sememe、tags、concepts.related_to）
        if not classified:
            semantic_clues = []
            for field in ["linked_sememe", "tags", "concepts"]:
                raw = entry.get(field, {})
                if isinstance(raw, dict):
                    semantic_clues += raw.get("zh", []) if isinstance(raw.get("zh"), list) else [raw.get("zh")]
                    semantic_clues += raw.get("related_to", []) if "related_to" in raw else []
                elif isinstance(raw, list):
                    semantic_clues += raw
            for clue in filter(None, semantic_clues):
                clue_norm = st.normalize_text(clue)
                if "氣候" in clue_norm:
                    cat_type = "climate"
                elif "天氣" in clue_norm or "雷" in clue_norm:
                    cat_type = "weather"
                elif "地理" in clue_norm or "地形" in clue_norm:
                    cat_type = "geo_feature"
                elif "城市" in clue_norm or "都市" in clue_norm:
                    cat_type = "location"
                else:
                    continue
                entry["classification"].append(cat_type)
                entry["triggered_by"].append("semantic:" + clue)
                category_term_sets[cat_type].add(standard_word)
                classified_terms.add(standard_word)
                classified = True
                break

        # fallback：suffix 判斷地理位置
        if not classified:
            location_suffixes = ["市", "區", "鄉", "鎮", "村", "里", "島"]
            if any(isinstance(w, str) and w and w[-1] in location_suffixes for w in zh_words):
                category_term_sets["location"].add(standard_word)
                entry["classification"].append("location")
                entry["triggered_by"].append("suffix_match")
                classified_terms.add(standard_word)
                classified = True

        # 最後放進未分類集合
        if not classified:
            unclassified_terms.add(standard_word)

    # 語意矯正再分類
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
if __name__ == "__main__":
    import sememe_tools as st_module

    with open("/content/Weather-AI-Agent/sememe_synonym.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    flattened_data = flatten_sememe_data(raw_data)

    custom_synonym_map, category_term_sets, classified_terms, unclassified_terms, reclassified_terms = build_precise_maps(flattened_data)

    print(f"\n自訂 Synonym Map 已載入，共 {len(custom_synonym_map)} 筆\n")
    for cat, terms in category_term_sets.items():
        print(f"分類「{cat}」詞彙數量：{len(terms)}")
        print(f"  ⤷ 範例：{list(terms)[:10]}\n")

    total_classified = sum(len(terms) for terms in category_term_sets.values())
    print(f"已分類詞彙總數：{total_classified}")
    print(f"未分類詞彙總數：{len(unclassified_terms)}")
    if unclassified_terms:
        print(f"  ⤷ 未分類範例：{list(unclassified_terms)[:10]}")
    if reclassified_terms:
        print("\n語意矯正重新分類：")
        for word, from_cat, to_cat in reclassified_terms:
            print(f"    {word}：{from_cat} → {to_cat}")

    st_module.set_custom_synonym_map(custom_synonym_map)
    st_module.set_custom_synonyms(flattened_data)
