#check.py

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
                "categories": path.copy(),
                "related_items": item.get("related_items", []),
                "linked_sememe": item.get("linked_sememe", {}),
                "tags": item.get("tags", []),
                "concepts": item.get("concepts", {})
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

# 分類邏輯設定
CATEGORY_PREFIX_TO_TYPE = {
    # Basic
    "basic-schema": "basic",
    "basic-category": "basic",
    "basic-": "basic",

    # Geo
    "geo-category": "geo_feature",
    "geo-": "geo_feature",

    # Politics
    "pol-category": "politics",
    "pol-": "politics",

    # Economy
    "eco-category": "economy",
    "econ-": "economy",

    # Society
    "soc-category": "society",
    "soc-": "society",

    # Tech
    "tech-category": "technology",
    "tech-": "technology",

    # History
    "hist-category": "history",
    "hist-": "history",

    # Environment
    "env-category": "environment",
    "env-": "environment",

    # Infrastructure
    "infra-category": "infrastructure",
    "infra-": "infrastructure",

    # Tourism
    "tour-category": "tourism",
    "tour-": "tourism",

    # International
    "intl-category": "international",
    "intl-": "international",

    # Health
    "health-category": "health",
    "health-": "health",

    # Agriculture
    "agri-category": "agriculture",
    "agri-": "agriculture",

    # Legal
    "legal-category": "legal",
    "legal-": "legal",

    # Media
    "media-category": "media",
    "media-": "media",

    # Culture
    "culture-category": "culture",
    "culture-": "culture",

    # Science
    "sci-category": "science",
    "sci-": "science",

    # Defense
    "def-category": "defense",
    "def-": "defense",

    # Transport
    "trans-category": "transport",
    "trans-": "transport",

    # Finance
    "fin-category": "finance",
    "fin-": "finance",

    # Energy
    "energy-category": "energy",
    "energy-": "energy",

    # Crisis
    "crisis-category": "crisis",
    "crisis-": "crisis",

    # Population
    "pop-category": "population",
    "pop-": "population",

    # Urban
    "urban-category": "urban",
    "urban-": "urban",

    # Taiwan - Basic
    "tw-basic-schema": "location",
    "tw-basic-category": "location",
    "tw-basic-": "location",

    # Taiwan - Geo
    "tw-geo-category": "geo_feature",
    "tw-geo-": "geo_feature",
    "tw-geo-water-category": "geo_feature",
    "tw-geo-water-": "geo_feature",
    "tw-geo-geology-category": "geo_feature",
    "tw-geo-geology-": "geo_feature",
    "tw-geo-coast-category": "geo_feature",
    "tw-geo-coast-": "geo_feature",
    "tw-geo-nature-category": "geo_feature",
    "tw-geo-nature-": "geo_feature",

    # Taiwan - City
    "tw-city-schema": "location",
    "tw-city-direct-category": "location",
    "tw-city-direct-": "location",
    "tw-city-provincial-category": "location",
    "tw-city-provincial-": "location",
    "tw-city-county-category": "location",
    "tw-city-county-": "location",
    "tw-city-countycity-category": "location",
    "tw-city-countycity-": "location",
    "tw-city-district-category": "location",
    "tw-city-district-": "location",

    # Taiwan - Climate
    "tw-climate-schema": "climate",
    "climate-types-category": "climate",
    "tw-climate-type-": "climate",
    "tw-climate-phenomenon-category": "climate",
    "tw-climate-phenomenon-": "climate",
    "tw-climate-indicator-category": "climate",
    "tw-climate-indicator-": "climate",
    "tw-climate-extreme-category": "climate",
    "tw-climate-extreme-": "climate",
    "tw-climate-change-category": "climate",
    "tw-climate-change-": "climate",
    "tw-climate-disaster-category": "climate",
    "tw-climate-disaster-": "climate",
    "tw-climate-technology-category": "climate",
    "tw-climate-technology-": "climate",

    # Taiwan - Weather
    "tw-weather-schema": "weather",
    "tw-weather-clear-category": "weather",
    "tw-weather-clear-": "weather",
    "tw-weather-rain-category": "weather",
    "tw-weather-rain-": "weather",
    "tw-weather-temp-category": "weather",
    "tw-weather-temp-": "weather",
    "tw-weather-wind-category": "weather",
    "tw-weather-wind-": "weather",
    "tw-weather-vis-category": "weather",
    "tw-weather-vis-": "weather",
    "tw-weather-severe-category": "weather",
    "tw-weather-severe-": "weather",

    # Global Weather Categories
    "weather-air-quality-category": "weather",
    "weather-air-quality-": "weather",
    "weather-season-category": "weather",
    "weather-season-": "weather",
    "weather-optical-category": "weather",
    "weather-optical-": "weather"
}

WEATHER_OVERRIDE = ["冷鋒", "暖鋒", "滯留鋒", "鋒面雨", "雷陣雨", "短時強降雨", "間歇性小雨", "霜凍", "揚沙", "晴朗無雲", "大雷雨", "豪雨", "雷擊"]
CLIMATE_EXCLUDE_FROM_WEATHER = ["強降雨事件", "年降雨量", "梅雨季", "平均氣溫變化", "氣候區劃"]

# 主分類邏輯
def build_precise_maps(flattened_data):
    category_term_sets = defaultdict(set)
    custom_synonym_map = {}
    classified_terms = set()
    unclassified_terms = set()
    reclassified_terms = []

    sorted_prefixes = sorted(CATEGORY_PREFIX_TO_TYPE.items(), key=lambda x: -len(x[0]))

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

        categories = [c.lower() for c in entry.get("categories", [])]
        related_items = [r.lower() for r in entry.get("related_items", []) if isinstance(r, str)]
        classified = False

        # 分類依據 categories
        for cat in categories:
            for prefix, cat_type in sorted_prefixes:
                if cat.startswith(prefix):
                    entry["classification"].append(cat_type)
                    entry["triggered_by"].append("分類代碼：" + cat)
                    category_term_sets[cat_type].add(zh_words[0])
                    classified_terms.add(zh_words[0])
                    classified = True
                    break
            if classified:
                break

        # 分類依據 ID
        if not classified:
            item_id = key.lower()
            for prefix, cat_type in sorted_prefixes:
                if item_id.startswith(prefix):
                    entry["classification"].append(cat_type)
                    entry["triggered_by"].append("依據ID前綴：" + item_id)
                    category_term_sets[cat_type].add(zh_words[0])
                    classified_terms.add(zh_words[0])
                    classified = True
                    break

        # 分類依據 related_items
        if not classified:
            for rel_id in related_items:
                for prefix, cat_type in sorted_prefixes:
                    if rel_id.startswith(prefix):
                        entry["classification"].append(cat_type)
                        entry["triggered_by"].append("依據關聯ID：" + rel_id)
                        category_term_sets[cat_type].add(zh_words[0])
                        classified_terms.add(zh_words[0])
                        classified = True
                        break
                if classified:
                    break

        # 語意推斷分類
        if not classified:
            semantic_clues = []
            linked = entry.get("linked_sememe", {})
            if isinstance(linked, dict):
                semantic_clues += linked.get("zh", []) if isinstance(linked.get("zh"), list) else [linked.get("zh")]
            semantic_clues += entry.get("tags", [])
            concepts = entry.get("concepts", {})
            if isinstance(concepts, dict):
                semantic_clues += concepts.get("related_to", []) if isinstance(concepts.get("related_to"), list) else []
                if isinstance(concepts.get("zh"), str):
                    semantic_clues.append(concepts["zh"])
                if isinstance(concepts.get("parent"), str):
                    semantic_clues.append(concepts["parent"])

            for clue in filter(None, semantic_clues):
                clue_norm = st.normalize_text(clue)
                if "氣候" in clue_norm:
                    cat_type = "climate"
                elif any(k in clue_norm for k in ["天氣", "雷", "風", "光學現象"]):
                    cat_type = "weather"
                elif any(k in clue_norm for k in ["地理", "地形", "山"]):
                    cat_type = "geo_feature"
                elif any(k in clue_norm for k in ["城市", "都市", "行政"]):
                    cat_type = "location"
                else:
                    continue
                entry["classification"].append(cat_type)
                entry["triggered_by"].append("語意線索：" + clue)
                category_term_sets[cat_type].add(zh_words[0])
                classified_terms.add(zh_words[0])
                classified = True
                break

        # 詞尾判斷 location
        if not classified:
            location_suffixes = ["市", "區", "鄉", "鎮", "村", "里"]
            if any(isinstance(w, str) and w and w[-1] in location_suffixes for w in zh_words):
                category_term_sets["location"].add(zh_words[0])
                entry["classification"].append("location")
                entry["triggered_by"].append("詞尾推斷")
                classified_terms.add(zh_words[0])
                classified = True

        # 無法分類
        if not classified:
            unclassified_terms.add(zh_words[0])

    # 語意矯正為 weather 類別
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
        print(f"範例：{list(terms)[:10]}\n")

    total_classified = sum(len(terms) for terms in category_term_sets.values())
    print(f" 已分類詞彙總數：{total_classified}")
    print(f"未分類詞彙總數：{len(unclassified_terms)}")
    if unclassified_terms:
        print(f"  ⤷ 未分類範例：{list(unclassified_terms)[:10]}")

    if reclassified_terms:
        print("\n語意矯正重新分類結果：")
        for word, from_cat, to_cat in reclassified_terms:
            print(f" {word}：{from_cat} → {to_cat}")

    st_module.set_custom_synonym_map(custom_synonym_map)
    st_module.set_custom_synonyms(flattened_data)
