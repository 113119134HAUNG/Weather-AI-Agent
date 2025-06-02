# vector_utils_advanced.py

import os
import json
import faiss
import torch
import numpy as np
from tqdm import tqdm
from sklearn.preprocessing import normalize
from transformers import AutoTokenizer, AutoModel

# 文字向量編碼
def encode_texts(
    texts,
    model,
    tokenizer,
    device,
    pooling="cls",
    normalize_vec=True,
    max_length=512,
    batch_size=32,
):
    if isinstance(texts, str):
        texts = [texts]

    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        encoded = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        ).to(device)
        with torch.no_grad():
            output = model(**encoded)

        if pooling == "cls":
            embeddings = output.last_hidden_state[:, 0]
        elif pooling == "mean":
            mask = encoded["attention_mask"].unsqueeze(-1).expand(output.last_hidden_state.size()).float()
            embeddings = torch.sum(output.last_hidden_state * mask, dim=1) / torch.clamp(mask.sum(1), min=1e-9)
        else:
            raise ValueError("pooling 必須是 'cls' 或 'mean'")

        all_embeddings.append(embeddings.cpu())

    all_embeddings = torch.cat(all_embeddings, dim=0).numpy()
    return normalize(all_embeddings) if normalize_vec else all_embeddings

# FAISS 向量庫操作
def build_faiss_index_and_save(
    texts,
    ids,
    meta_list,
    model,
    tokenizer,
    device,
    index_path,
    meta_path,
    pooling="cls"
):
    vectors = encode_texts(texts, model, tokenizer, device, pooling)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, index_path)

    with open(meta_path, "w", encoding="utf-8") as f:
        for i, meta in enumerate(meta_list):
            meta_record = {
                "id": ids[i],
                "text": texts[i],
                "meta": meta,
            }
            f.write(json.dumps(meta_record, ensure_ascii=False) + "\n")
    print(f"儲存完成：{index_path}, {meta_path}")

def load_index_and_metadata(index_path, meta_path):
    index = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = [json.loads(line.strip()) for line in f]
    return index, metadata

# 基礎搜尋
def search_with_metadata(
    query,
    index,
    metadata,
    model,
    tokenizer,
    device,
    topk=5,
    pooling="cls"
):
    q_vec = encode_texts(query, model, tokenizer, device, pooling)
    D, I = index.search(q_vec, topk)
    return [
        {
            "score": float(D[0][i]),
            **metadata[idx],
        }
        for i, idx in enumerate(I[0])
    ]

# 合併多個資料庫搜尋
def combine_search(
    query,
    indices_and_metadata=None,
    indices=None,
    metadatas=None,
    model=None,
    tokenizer=None,
    device=None,
    topk=5,
    pooling="cls"
):
    if indices_and_metadata:
        if not isinstance(indices_and_metadata, list):
            raise ValueError("indices_and_metadata 必須是 [(index, metadata), ...] 格式")
        indices = [pair[0] for pair in indices_and_metadata]
        metadatas = [pair[1] for pair in indices_and_metadata]
    else:
        if indices is None or metadatas is None:
            raise ValueError("必須提供 indices 和 metadatas 或 indices_and_metadata。")
        if len(indices) != len(metadatas):
            raise ValueError("indices 和 metadatas 長度必須一致。")

    query_vec = encode_texts(query, model, tokenizer, device, pooling)
    all_results = []

    for idx, (index, metadata) in enumerate(zip(indices, metadatas)):
        D, I = index.search(query_vec, topk)
        for i, score in enumerate(D[0]):
            if I[0][i] >= 0:
                all_results.append(
                    {
                        "score": float(score),
                        **metadata[I[0][i]],
                        "source": f"index_{idx}",
                    }
                )

    sorted_results = sorted(all_results, key=lambda x: x["score"], reverse=True)[:topk]
    return sorted_results

# 簡易多庫搜尋
def easy_search_all(
    query,
    index_list,
    model,
    tokenizer,
    device,
    topk=5,
    pooling="cls"
):
    query_vec = encode_texts(query, model, tokenizer, device, pooling)
    all_results = []

    for idx, (index, metadata) in enumerate(index_list):
        D, I = index.search(query_vec, topk)
        for score, idx_ in zip(D[0], I[0]):
            if idx_ >= 0:
                all_results.append(
                    {
                        "score": float(score),
                        "text": metadata[idx_]["text"],
                        "meta": metadata[idx_]["meta"],
                        "source": f"index_{idx}",
                    }
                )

    sorted_results = sorted(all_results, key=lambda x: x["score"], reverse=True)[:topk]
    return sorted_results
