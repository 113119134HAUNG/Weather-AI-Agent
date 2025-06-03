import os
import torch
import requests
from userdata import get
import vector_utils_advanced as vu
from transformers import AutoTokenizer, AutoModel
# ========== Groq API 設定 ==========
api_key = get("Groq")
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
groq_model_id = "meta-llama/llama-4-maverick-17b-128e-instruct"
api_url = "https://api.groq.com/openai/v1/chat/completions"

# ========== 載入索引 ==========
index_paths = [
    ("/content/index.faiss", "/content/metadata.jsonl"),
    ("/content/custom_index.faiss", "/content/custom_metadata.jsonl")
]
indices, metadatas = [], []
for idx_path, meta_path in index_paths:
    index, meta = vu.load_index_and_metadata(idx_path, meta_path)
    indices.append(index)
    metadatas.append(meta)
print(f"成功載入 {len(indices)} 個索引庫！")

# ========== 建立 RAG Prompt ==========
def build_rag_prompt(query, retrieved_results, history=[], mode="standard"):
    context_parts = []
    for r in retrieved_results:
        if mode == "standard":
            context_parts.append(
                f"- 問句：{r['meta'].get('query', r['text'])}\n  語義：{r['meta'].get('sememe', '')}"
            )
        else:
            context_parts.append(r.get("text", ""))
    context_block = "\n\n".join(context_parts)

    history_block = "\n".join([f"使用者：{q}\n助理：{a}" for q, a in history])

    prompt = f"""你是一位中文語意問答助理，擅長整合語意資訊與檢索片段。請根據下列語意資料與上下文紀錄，回答使用者的問題。

【語意檢索結果】
{context_block}

【對話紀錄】
{history_block}

🔸 使用者提問：{query}

請根據語意內容，以自然語言簡潔回答："""
    return prompt

# ========== 檢索並顯示 ==========
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
    print("\n檢索結果摘要（TopK）：")
    for r in results:
        print(f"來自：{r['source']}｜分數: {r['score']:.4f}")
        print(f"問句/詞：{r['meta'].get('query', r['meta'].get('term', '')).strip()}")
        print(f"語義描述：{r['meta'].get('sememe', r['meta'].get('synonyms', ''))}\n")
    return results

# ========== 呼叫 Groq API ==========
def generate_answer_with_groq(prompt):
    payload = {
        "model": groq_model_id,
        "messages": [
            {"role": "system", "content": "你是一位中文語意問答專家，擅長語意理解與知識整合。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"呼叫 Groq API 失敗：{str(e)}"

# ========== 啟動多回合問答 ==========
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-base-zh")
hf_model = AutoModel.from_pretrained("BAAI/bge-base-zh").to(device).eval()

chat_history = []
print("\n歡迎使用 Semantic RAG 多輪問答系統")
print("輸入 `exit` 結束對話。\n")

while True:
    user_input = input("使用者：")
    if user_input.strip().lower() in {"exit", "quit", "bye", "再見", "謝謝"}:
        print("對話結束，謝謝使用！")
        break

    search_results = run_query_and_get_results(user_input, indices, metadatas, hf_model, tokenizer, device)
    prompt = build_rag_prompt(user_input, search_results, history=chat_history, mode="standard")
    answer = generate_answer_with_groq(prompt)

    print("\nGroq 回答：", answer)
    chat_history.append((user_input, answer))