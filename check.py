#check.py

import re
import json
import sememe_tools as st_module
from collections import defaultdict

# 正規化工具
class SimpleNormalizer:
    # 常見簡體／混用字 ➜ 標準繁體字對應表
    TRAD_MAPPING = {
    # 台灣縣市地名
    "台灣": "臺灣", 
    "台北": "臺北", 
    "台中": "臺中", 
    "台南": "臺南", 
    "台東": "臺東", 
    "台西": "臺西", 
    "台北市": "臺北市", 
    "台中市": "臺中市", 
    "台南市": "臺南市", 
    "台東縣": "臺東縣",
    "新北市": "新北市",
    "桃園市": "桃園市",
    "台中市": "臺中市",
    "台南市": "臺南市",
    "高雄市": "高雄市",
    "高雄市": "高雄市",
    "基隆市": "基隆市",
    "新竹市": "新竹市",
    "新竹縣": "新竹縣",
    "苗栗縣": "苗栗縣",
    "彰化縣": "彰化縣",
    "南投縣": "南投縣",
    "雲林縣": "雲林縣",
    "嘉義市": "嘉義市",
    "嘉義縣": "嘉義縣",
    "屏東縣": "屏東縣",
    "宜蘭縣": "宜蘭縣",
    "花蓮縣": "花蓮縣",
    "澎湖縣": "澎湖縣",
    "金門縣": "金門縣",
    "連江縣": "連江縣",
    
    # 台灣地理景點
    "台灣海峽": "臺灣海峽",
    "台北101": "臺北101",
    "台灣高鐵": "臺灣高鐵",
    "台鐵": "臺鐵",
    "台電": "臺電",
    "台積電": "臺積電",
    "台大": "臺大",
    "台師大": "臺師大",
    "台科大": "臺科大",
    "台清交": "臺清交",
    "台大醫院": "臺大醫院",
    "台北車站": "臺北車站",
    "台中港": "臺中港",
    "台南機場": "臺南機場",
    "台東機場": "臺東機場",
    
    # 行政區域
    "後裡": "後里",
    "大裡": "大里", 
    "草屯鎮": "草屯鎮",
    "埔裡": "埔里",
    
    # 天氣氣候相關
    "天气": "天氣",
    "气候": "氣候",
    "气温": "氣溫",
    "温度": "溫度",
    "湿度": "濕度",
    "气压": "氣壓",
    "风": "風",
    "台风": "颱風",
    "刮风": "颳風",
    "东风": "東風",
    "西风": "西風",
    "南风": "南風",
    "北风": "北風",
    "东北风": "東北風",
    "西南风": "西南風",
    "东南风": "東南風",
    "西北风": "西北風",
    "强风": "強風",
    "暴风": "暴風",
    "微风": "微風",
    "阵风": "陣風",
    "风力": "風力",
    "风速": "風速",
    "风向": "風向",
    "雨": "雨",
    "下雨": "下雨",
    "降雨": "降雨",
    "雨量": "雨量",
    "暴雨": "暴雨",
    "大雨": "大雨",
    "中雨": "中雨",
    "小雨": "小雨",
    "阵雨": "陣雨",
    "雷阵雨": "雷陣雨",
    "毛毛雨": "毛毛雨",
    "冰雹": "冰雹",
    "雪": "雪",
    "下雪": "下雪",
    "降雪": "降雪",
    "雪花": "雪花",
    "霜": "霜",
    "雾": "霧",
    "浓雾": "濃霧",
    "大雾": "大霧",
    "薄雾": "薄霧",
    "霾": "霾",
    "阴": "陰",
    "阴天": "陰天",
    "阴云": "陰雲",
    "多云": "多雲",
    "少云": "少雲",
    "晴": "晴",
    "晴天": "晴天",
    "晴朗": "晴朗",
    "艳阳": "豔陽",
    "阳光": "陽光",
    "日照": "日照",
    "紫外线": "紫外線",
    "闪电": "閃電",
    "打雷": "打雷",
    "雷": "雷",
    "雷声": "雷聲",
    "雷电": "雷電",
    "彩虹": "彩虹",
    "干旱": "乾旱",
    "洪水": "洪水",
    "洪涝": "洪澇",
    "潮湿": "潮濕",
    "干燥": "乾燥",
    "闷热": "悶熱",
    "炎热": "炎熱",
    "酷热": "酷熱",
    "寒冷": "寒冷",
    "严寒": "嚴寒",
    "冰冷": "冰冷",
    "凉爽": "涼爽",
    "温和": "溫和",
    "温暖": "溫暖",
    "热浪": "熱浪",
    "寒流": "寒流",
    "冷气团": "冷氣團",
    "暖气团": "暖氣團",
    "锋面": "鋒面",
    "冷锋": "冷鋒",
    "暖锋": "暖鋒",
    "梅雨": "梅雨",
    "梅雨季": "梅雨季",
    "梅雨锋": "梅雨鋒",
    "季风": "季風",
    "东北季风": "東北季風",
    "西南季风": "西南季風",
    "热带": "熱帶",
    "亚热带": "亞熱帶",
    "温带": "溫帶",
    "寒带": "寒帶",
    
    # 氣象預報用語
    "气象": "氣象",
    "预报": "預報",
    "天气预报": "天氣預報",
    "气象预报": "氣象預報",
    "气象台": "氣象臺",
    "气象局": "氣象局",
    "观测": "觀測",
    "监测": "監測",
    "预警": "預警",
    "警报": "警報",
    "台风警报": "颱風警報",
    "大雨特报": "大雨特報",
    "强风特报": "強風特報",
    "低温特报": "低溫特報",
    "高温特报": "高溫特報",
    
    # 常見混用字（保留原有）
    "裡": "里",
    "后": "後",
    "隻": "只",
    "里程": "里程",
    "发": "發",
    "发展": "發展",
    "发现": "發現",
    "发生": "發生",
    "发布": "發布",
    "发表": "發表",
    "发送": "發送",
    "发明": "發明",
    "头发": "頭髮",
    
    "对": "對",
    "对于": "對於",
    "对方": "對方",
    "对话": "對話",
    "对比": "對比",
    "绝对": "絕對",
    "相对": "相對",
    
    "为": "為",
    "为了": "為了",
    "因为": "因為",
    "认为": "認為",
    "作为": "作為",
    "成为": "成為",
    "行为": "行為",
    
    "过": "過",
    "过程": "過程",
    "过去": "過去",
    "通过": "通過",
    "经过": "經過",
    "不过": "不過",
    "过度": "過度",
    "过分": "過分",
    
    "来": "來",
    "来自": "來自",
    "来到": "來到",
    "本来": "本來",
    "原来": "原來",
    "未来": "未來",
    "出来": "出來",
    "起来": "起來",
    
    "个": "個",
    "个人": "個人",
    "个别": "個別",
    "个体": "個體",
    "一个": "一個",
    "两个": "兩個",
    
    "时": "時",
    "时间": "時間",
    "时候": "時候",
    "同时": "同時",
    "临时": "臨時",
    "时代": "時代",
    "时刻": "時刻",
    
    "现": "現",
    "现在": "現在",
    "现象": "現象",
    "出现": "出現",
    "发现": "發現",
    "表现": "表現",
    "实现": "實現",
    
    "国": "國",
    "国家": "國家",
    "中国": "中國",
    "美国": "美國",
    "英国": "英國",
    "法国": "法國",
    "德国": "德國",
    "韩国": "韓國",
    "国际": "國際",
    "国内": "國內",
    "外国": "外國",
    "爱国": "愛國",
    
    "学": "學",
    "学习": "學習",
    "学生": "學生",
    "学校": "學校",
    "大学": "大學",
    "科学": "科學",
    "数学": "數學",
    "文学": "文學",
    "医学": "醫學",
    
    "会": "會",
    "会议": "會議",
    "机会": "機會",
    "社会": "社會",
    "开会": "開會",
    "学会": "學會",
    "可会": "可會",
    
    "说": "說",
    "说话": "說話",
    "说明": "說明",
    "听说": "聽說",
    "据说": "據說",
    "小说": "小說",
    
    "经": "經",
    "经济": "經濟",
    "经验": "經驗",
    "经过": "經過",
    "经常": "經常",
    "已经": "已經",
    "曾经": "曾經",
    
    "长": "長",
    "长期": "長期",
    "成长": "成長",
    "长度": "長度",
    "很长": "很長",
    "校长": "校長",
    "市长": "市長",
    
    "门": "門",
    "大门": "大門",
    "门口": "門口",
    "专门": "專門",
    "部门": "部門",
    "热门": "熱門",
    
    "车": "車",
    "汽车": "汽車",
    "火车": "火車",
    "开车": "開車",
    "停车": "停車",
    "车站": "車站",
    
    "电": "電",
    "电话": "電話",
    "电脑": "電腦",
    "电影": "電影",
    "电视": "電視",
    "用电": "用電",
    "电子": "電子",
    
    "还": "還",
    "还是": "還是",
    "还有": "還有",
    "还要": "還要",
    "还没": "還沒",
    "归还": "歸還",
    
    "应": "應",
    "应该": "應該",
    "应当": "應當",
    "应用": "應用",
    "反应": "反應",
    "适应": "適應",
    
    "见": "見",
    "看见": "看見",
    "见面": "見面",
    "意见": "意見",
    "观点见": "觀點見",
    
    "买": "買",
    "购买": "購買",
    "买卖": "買賣",
    
    "卖": "賣",
    "出售": "出售",
    "销售": "銷售",
    
    "开": "開",
    "打开": "打開",
    "开始": "開始",
    "开放": "開放",
    "开发": "開發",
    "公开": "公開",
    
    "关": "關",
    "关于": "關於",
    "关系": "關係",
    "关键": "關鍵",
    "关心": "關心",
    "关闭": "關閉",
    
    "觉": "覺",
    "感觉": "感覺",
    "觉得": "覺得",
    "睡觉": "睡覺",
    
    "听": "聽",
    "听见": "聽見",
    "听说": "聽說",
    "听话": "聽話",
    
    "书": "書",
    "读书": "讀書",
    "书本": "書本",
    "图书": "圖書",
    "教科书": "教科書",
    
    "办": "辦",
    "办法": "辦法",
    "办公": "辦公",
    "举办": "舉辦",
    
    "认": "認",
    "认识": "認識",
    "确认": "確認",
    "承认": "承認",
    "认真": "認真",
    
    "让": "讓",
    "让步": "讓步",
    
    "这": "這",
    "这个": "這個",
    "这里": "這裡",
    "这样": "這樣",
    "这些": "這些",
    
    "那": "那",
    "哪": "哪",
    
    "万": "萬",
    "亿": "億",
    
    "着": "著",
    "么": "麼",
    "几": "幾",
    "钱": "錢",
    "岁": "歲"
    }

    @staticmethod
    def normalize_text(text):
        if not isinstance(text, str):
            text = str(text)

        # 替換常見簡體字或異體字為繁體標準
        for simp, trad in SimpleNormalizer.TRAD_MAPPING.items():
            text = text.replace(simp, trad)

        # 移除空白與轉小寫
        return re.sub(r"\s+", "", text).lower()


# 建立實例
st = SimpleNormalizer()

# 巢狀 json 壓平（保留路徑、語意、相關欄位）
def flatten_sememe_data(data, path=None, results=None):
    if results is None:
        results = {}
    if path is None:
        path = []
    if not isinstance(data, dict):
        return results

    # 處理 items
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
                "id": item.get("id", ""),
                "zh": zh_main,
                "en": item.get("en", ""),
                "synonyms": synonyms,
                "categories": path.copy(),
                "related_items": item.get("related_items", []),
                "linked_sememe": item.get("linked_sememe", {}),
                "tags": item.get("tags", []),
                "concepts": item.get("concepts", {}),
                "raw": item   # 保留原始資料
            }

    # 下探 categories
    if "categories" in data and isinstance(data["categories"], dict):
        for cat_name, cat_data in data["categories"].items():
            flatten_sememe_data(cat_data, path + [cat_name], results)

    # 下探 subcategories
    if "subcategories" in data and isinstance(data["subcategories"], dict):
        for subcat_name, subcat_data in data["subcategories"].items():
            flatten_sememe_data(subcat_data, path + [subcat_name], results)

    # 泛化：還有其他自定義巢狀結構就自動下探
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

# 天氣優先詞
WEATHER_OVERRIDE = ["冷鋒", "暖鋒", "滯留鋒", "鋒面雨", "雷陣雨", "短時強降雨", "間歇性小雨", "霜凍", "揚沙", "晴朗無雲", "大雷雨", "豪雨", "雷擊"]
CLIMATE_EXCLUDE_FROM_WEATHER = ["強降雨事件", "年降雨量", "梅雨季", "平均氣溫變化", "氣候區劃"]

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

        # 同義詞表
        for word in all_words:
            if isinstance(word, str) and word:
                custom_synonym_map[st.normalize_text(word)] = standard_word

        entry["classification"] = []
        entry["triggered_by"] = []

        classified = False

        # 1. 由 path / categories 判斷（最強依據）
        for cat in entry.get("categories", []):
            cat_lower = str(cat).lower()
            for prefix, cat_type in CATEGORY_PREFIX_TO_TYPE.items():
                if cat_lower.startswith(prefix):
                    entry["classification"].append(cat_type)
                    entry["triggered_by"].append(cat_lower)
                    category_term_sets[cat_type].add(standard_word)
                    classified_terms.add(standard_word)
                    classified = True
                    break
            if classified:
                break

        # 2. 由 id 判斷
        if not classified and entry.get("id"):
            item_id = entry.get("id", "").lower()
            for prefix, cat_type in CATEGORY_PREFIX_TO_TYPE.items():
                if item_id.startswith(prefix):
                    entry["classification"].append(cat_type)
                    entry["triggered_by"].append("id:" + item_id)
                    category_term_sets[cat_type].add(standard_word)
                    classified_terms.add(standard_word)
                    classified = True
                    break

        # 3. 由 related_items 判斷
        if not classified:
            for rel_id in entry.get("related_items", []):
                rel_id = str(rel_id).lower()
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

        # 4. 語意關鍵詞（linked_sememe、tags、concepts、路徑文字）
        if not classified:
            clues = []
            linked = entry.get("linked_sememe", {})
            if isinstance(linked, dict):
                clues += linked.get("zh", []) if isinstance(linked.get("zh"), list) else [linked.get("zh", "")]
            clues += entry.get("tags", [])
            concepts = entry.get("concepts", {})
            if isinstance(concepts, dict):
                clues += concepts.get("related_to", []) if isinstance(concepts.get("related_to"), list) else []
                if isinstance(concepts.get("zh"), str): clues.append(concepts["zh"])
                if isinstance(concepts.get("parent"), str): clues.append(concepts["parent"])
            clues += entry.get("categories", [])
            for clue in filter(None, clues):
                clue_norm = st.normalize_text(clue)
                if "氣候" in clue_norm:
                    cat_type = "climate"
                elif any(kw in clue_norm for kw in ("天氣", "雷", "風", "雨", "溫", "霜", "雪")):
                    cat_type = "weather"
                elif any(kw in clue_norm for kw in ("地理", "地形", "地貌", "山", "海", "灘", "谷", "湖", "溪", "坪", "島")):
                    cat_type = "geo_feature"
                elif any(kw in clue_norm for kw in ("城市", "都市", "區", "鄉", "鎮", "村", "里", "行政", "縣", "市")):
                    cat_type = "location"
                else:
                    continue
                entry["classification"].append(cat_type)
                entry["triggered_by"].append("semantic:" + clue)
                category_term_sets[cat_type].add(standard_word)
                classified_terms.add(standard_word)
                classified = True
                break

        # 5. 地理名詞詞尾 fallback
        if not classified:
            location_suffixes = ["市", "區", "鄉", "鎮", "村", "里", "島"]
            if any(isinstance(w, str) and w and w[-1] in location_suffixes for w in zh_words):
                category_term_sets["location"].add(standard_word)
                entry["classification"].append("location")
                entry["triggered_by"].append("suffix_match")
                classified_terms.add(standard_word)
                classified = True

        # 6. 未分類
        if not classified:
            unclassified_terms.add(standard_word)

    # 最後語意再分類修正（例如天氣與氣候邊界）
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

# ==== 主程式 ====
if __name__ == "__main__":
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

    # 儲存結果
    with open("/content/Weather-AI-Agent/flattened_sememe_synonym.json", "w", encoding="utf-8") as f:
        json.dump(flattened_data, f, ensure_ascii=False, indent=2)
    print("已儲存為：flattened_sememe_synonym.json")
