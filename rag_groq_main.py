import os
import requests
import vector_utils_advanced as vu

# ====== Groq API 設定 ======
from userdata import get  # 或根據你儲存 token 的方式
api_key = get("Groq")
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
groq_model_id = "meta-llama/llama-4-maverick-17b-128e-instruct"
api_url = "https://api.groq.com/openai/v1/chat/completions"

# ====== 索引路徑 ======
index_paths = [
    ("/content/index.faiss", "/content/metadata.jsonl"),
    ("/content/custom_index.faiss", "/content/custom_metadata.jsonl")
]

# ====== 載入所有索引 ======
indices, metadatas = [], []
for idx_path, meta_path in index_paths:
    index, meta = vu.load_index_and_metadata(idx_path, meta_path)
    indices.append(index)
    metadatas.append(meta)
print(f"成功載入 {len(indices)} 個索引庫！")

# ====== 建立 Prompt 的函數 ======
def build_rag_prompt(query, retrieved_results, mode="standard"):
    context_parts = []
    for r in retrieved_results:
        if mode == "standard":
            context_parts.append(
                f"- 問句：{r['meta'].get('query', r['text'])}\n  語義：{r['meta'].get('sememe', '')}"
            )
        elif mode == "flat":
            context_parts.append(r.get("text", ""))
    context_block = "\n\n".join(context_parts)
    prompt = f"""您是一位專業的中文問答助理，請根據以下檢索到的語意資訊，準確且詳盡地回答原始問題：

【語意資訊】：{context_block}

  原始問題：{query}

  請以清晰、自然且具專業度的中文，撰寫完整回答。若相關資訊不足，亦請明確說明不足處。"""
    return prompt

# ====== 查詢並列出語意片段 ======
def run_query_and_get_results(query, indices, metadatas, model, tokenizer, device, topk=5):
    results = vu.combine_search(
        query=query,
        indices=indices,
        metadatas=metadatas,
        model=model,
        tokenizer=tokenizer,
        device=device,
        topk=topk
    )
    print("\n檢索結果（TopK 語意片段）：")
    for r in results:
        print(f"來自：{r['source']}｜分數: {r['score']:.4f}")
        print(f"問句/詞：{r['meta'].get('query', r['meta'].get('term', '')).strip()}")
        print(f"語義描述：{r['meta'].get('sememe', r['meta'].get('synonyms', ''))}\n")
    return results

# ====== 呼叫 Groq API ======
def generate_answer_with_groq(prompt, model=groq_model_id):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一個中文語意問答專家，擅長根據語義線索推理。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ 呼叫 Groq API 失敗：{str(e)}"

# ====== 使用者互動輸入 ======
print("\n歡迎使用 Semantic RAG 中文問答系統")
query = input("請輸入您的自然語言問題：\n> ")

# ====== 語意檢索與組 Prompt ======
combined_results = run_query_and_get_results(query, indices, metadatas, model=hf_model, tokenizer=tokenizer, device=device)
rag_prompt = build_rag_prompt(query, combined_results, mode="standard")

# ====== 呼叫 LLM 回答 ======
print("\n發送以下 Prompt 給 Groq：\n" + rag_prompt)
answer = generate_answer_with_groq(rag_prompt)

# ====== 顯示回答 ======
print("\nGroq 回答：\n" + answer)