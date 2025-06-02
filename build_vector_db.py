# build_vector_db.py

import os
import json
from tqdm import tqdm
import torch
from transformers import AutoTokenizer, AutoModel
import sememe_tools as st
import vector_utils_advanced as vu

# 處理 NLPCC-MH 資料並建置向量庫
def prepare_nlpccmh_augmented_data(
    input_path, index_path, meta_path, model, tokenizer, device, pooling="cls", silent=False
):
    assert os.path.exists(input_path), f"找不到輸入檔案: {input_path}"

    texts, ids, metas = [], [], []
    with open(input_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(tqdm(f, desc="處理 NLPCC-MH 資料", disable=silent)):
            entry = json.loads(line.strip())
            question = entry["question"]
            sememe_map = entry["question_sememe_map"]

            pseudo_text = "；".join(st.format_sememe_map(sememe_map, style="display"))
            merged_query = st.generate_augmented_query(question, sememe_map)

            texts.append(merged_query)
            ids.append(entry["id"])
            metas.append({
                "query": question,
                "sememe": pseudo_text
            })

    vu.build_faiss_index_and_save(
        texts=texts,
        ids=ids,
        meta_list=metas,
        model=model,
        tokenizer=tokenizer,
        device=device,
        index_path=index_path,
        meta_path=meta_path,
        pooling=pooling
    )
    if not silent:
        print(f"NLPCC-MH 向量庫已建置完成，共 {len(texts)} 筆資料。")

# 處理自製同義詞資料，建立向量庫
def prepare_custom_augmented_data(synonym_path, index_path, meta_path, model, tokenizer, device, pooling="cls", silent=False):
    assert os.path.exists(synonym_path), f"找不到輸入檔案: {synonym_path}"

    texts, ids, metas = [], [], []
    with open(synonym_path, "r", encoding="utf-8") as f:
        synonym_data = json.load(f)

    for i, (key, entry) in enumerate(tqdm(synonym_data.items(), desc="處理自製同義詞資料", disable=silent)):
        zh_entry = entry.get("zh", key)
        synonyms = entry.get("synonyms", [])
        categories = entry.get("categories", {})

        if isinstance(zh_entry, list):
            standard_word = zh_entry[0]
            parts = zh_entry.copy()
        else:
            standard_word = zh_entry
            parts = [zh_entry]

        parts.extend(synonyms)

        description = "、".join(parts) + "。這些是相關語義擴展資訊。"
        merged = f"[Q] {standard_word} [SEP] {description}"

        texts.append(merged)
        ids.append(f"custom_{i}")
        metas.append({
            "term": standard_word,
            "synonyms": synonyms,
            "categories": categories,
            "is_location": False
        })

        for cat_name, city_list in categories.items():
            for city in city_list:
                texts.append(f"[Q] {city} [SEP] {standard_word}地區")
                ids.append(f"city_{i}_{city}")
                metas.append({
                    "term": city,
                    "synonyms": [],
                    "categories": {},
                    "is_location": True
                })

    vu.build_faiss_index_and_save(
        texts=texts,
        ids=ids,
        meta_list=metas,
        model=model,
        tokenizer=tokenizer,
        device=device,
        index_path=index_path,
        meta_path=meta_path,
        pooling=pooling
    )
    if not silent:
        print(f"自製 Synonym 向量庫已建置完成，共 {len(texts)} 筆資料。")

# 執行全部向量庫建立
def run_all_indexing(
    nlpcc_input_path,
    nlpcc_index_path,
    nlpcc_meta_path,
    synonym_path,
    custom_index_path,
    custom_meta_path,
    model,
    tokenizer,
    device,
    silent=False
):
    if not silent:
        print("開始全流程向量庫建立...")

    # 先建立 NLPCC
    if not silent:
        print("\n開始建立 NLPCC-MH 向量庫...")
    prepare_nlpccmh_augmented_data(
        input_path=nlpcc_input_path,
        index_path=nlpcc_index_path,
        meta_path=nlpcc_meta_path,
        model=model,
        tokenizer=tokenizer,
        device=device,
        silent=silent
    )
    # 建立 Custom
    if not silent:
        print("\n開始建立自製 Synonym 向量庫...")
    prepare_custom_augmented_data(
        synonym_path=synonym_path,
        index_path=custom_index_path,
        meta_path=custom_meta_path,
        model=model,
        tokenizer=tokenizer,
        device=device,
        silent=silent
    )
    if not silent:
        print("\n全部向量庫建立完成！")

# ---- 執行模型初始化與 run_all_indexing ----
if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-base-zh")
    hf_model = AutoModel.from_pretrained("BAAI/bge-base-zh").to(device).eval()
    run_all_indexing(
        nlpcc_input_path="/content/NLPCC-MH/data/nlpcc-mh.train_sememe.jsonl",
        nlpcc_index_path="/content/index.faiss",
        nlpcc_meta_path="/content/metadata.jsonl",
        synonym_path="/content/sememe_synonym.json",
        custom_index_path="/content/custom_index.faiss",
        custom_meta_path="/content/custom_metadata.jsonl",
        model=hf_model,
        tokenizer=tokenizer,
        device=device
    )
