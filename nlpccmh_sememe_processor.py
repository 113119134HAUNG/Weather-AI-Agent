# nlpccmh_sememe_processor.py

import json
from tqdm import tqdm
import sememe_tools as st

# === 自動載入語義/同義詞 mapping ===
def setup_sememe_synonyms():
    with open("/content/Weather-AI-Agent/sememe_synonym_OK.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    taiwan_data = raw_data.get("Country", {}).get("categories", {}).get("Taiwan", {})

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

    flattened_data = flatten_sememe_data(taiwan_data)

    def build_custom_synonym_map(flattened_data):
        def normalize(text):
            return text.lower().replace(" ", "")
        custom_synonym_map = {}
        for entry in flattened_data.values():
            zh_entry = entry.get("zh") or ""
            synonyms = entry.get("synonyms", [])
            all_words = [zh_entry] + synonyms
            standard_word = normalize(zh_entry) if zh_entry else None
            if not standard_word:
                continue
            for word in all_words:
                if isinstance(word, str) and word:
                    custom_synonym_map[normalize(word)] = standard_word
        return custom_synonym_map

    custom_synonym_map = build_custom_synonym_map(flattened_data)
    st.set_custom_synonym_map(custom_synonym_map)
    st.set_custom_synonyms(flattened_data)

# 初始化 custom mapping
setup_sememe_synonyms()
# === end of setup ===

def process_nlpccmh_sample(sample, base_id="nlpcc", index=0):
    result = []
    question = sample["q"]

    sememe_analysis = st.analyze_sentence(question)
    sememe_tags = sememe_analysis["sememe_tags"]
    sememe_map = sememe_analysis["sememe_map"]

    for path_id, triple in enumerate(sample.get("path", [])):
        head = triple[0].split(" ||| ")[0]
        relation = triple[1]
        tail = triple[2].split(" ||| ")[0]
        sentence = f"{head} {relation} {tail}"

        result.append({
            "id": f"{base_id}_{index}_{path_id}",
            "question": question,
            "question_sememe": sememe_tags,
            "question_sememe_map": sememe_map,
            "triple_sentence": sentence,
            "head": head,
            "relation": relation,
            "tail": tail
        })

    return result


def process_nlpccmh_file(input_path, output_path, batch_size=1000):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(output_path, "w", encoding="utf-8") as out_f:
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            for j, sample in enumerate(tqdm(batch, desc=f"Batch {i // batch_size}")):
                processed = process_nlpccmh_sample(sample, index=i + j)
                for entry in processed:
                    out_f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    process_nlpccmh_file(
        input_path="/content/NLPCC-MH/data/nlpcc-mh.train.json",
        output_path="/content/NLPCC-MH/data/nlpcc-mh.train_sememe.jsonl"
    )
