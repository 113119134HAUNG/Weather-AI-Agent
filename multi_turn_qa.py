# multi_turn_qa.py

import requests
import vector_utils_advanced as vu

# Groq 問答函數
def generate_answer_with_groq(
    query,
    search_results,
    api_key,
    model="meta-llama/llama-4-maverick-17b-128e-instruct",
    mode="standard"
):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 整理檢索內容
    if mode == "standard":
        context_parts = [
            f"- 問句：{r['meta'].get('query', r['text'])}\n  語義：{r['meta'].get('sememe', '')}"
            for r in search_results
        ]
    else:
        context_parts = [r.get("text", "") for r in search_results]

    context_block = "\n\n".join(context_parts)

    # 填入 Prompt
    prompt = f"""
    你是一位中文語意理解與問答助理，請根據下列檢索資料回答問題。

    請注意：
-   優先根據檢索資料直接作答。
-   若資料無明確答案，請合理推論並標註「（推論）」。
-   回答避免重複資料或編造事實。
-   如遇不確定處，簡要說明原因。

    檢索結果：
    {context_block}

    問題：
    {query}

    請根據上述內容作答：
""".strip()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是中文語意問答專家，擅長整合語意描述與知識線索。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"呼叫 Groq API 失敗：{str(e)}"

# 多回合 QA 函數
def multi_turn_qa(initial_query,index_list,model,tokenizer,device,api_key,max_turns=3,topk=5,verbose=True,stop_words=None,dynamic_next_query=True):
    """
    多回合問答流程

    Args:
        initial_query (str): 初始提問
        index_list (list): [(faiss.Index, metadata)] 格式
        model, tokenizer, device: 向量化工具
        api_key (str): Groq API 金鑰
        max_turns (int): 最大回合數
        topk (int): 每輪檢索 TopK
        verbose (bool): 是否輸出過程
        stop_words (list): 碰到這些關鍵字就停止
        dynamic_next_query (bool): 根據回答自動產生下一個問題
    """
    if stop_words is None:
        stop_words = ["無法回答", "缺少資料", "無相關資訊"]

    history = []
    current_query = initial_query

    for turn in range(1, max_turns + 1):
        if verbose:
            print(f"\n第 {turn} 輪問題：{current_query}")

        # 搜索步驟
        try:
            search_results = vu.easy_search_all(
                query=current_query,
                index_list=index_list,
                model=model,
                tokenizer=tokenizer,
                device=device,
                topk=topk
            )
        except Exception as e:
            print(f"向量檢索失敗：{e}")
            break

        # Groq問答步驟
        try:
            answer = generate_answer_with_groq(
                query=current_query,
                search_results=search_results,
                api_key=api_key
            )
        except Exception as e:
            print(f"Groq回答失敗：{e}")
            break

        if verbose:
            print(f"回答：{answer}")

        history.append({
            "turn": turn,
            "query": current_query,
            "answer": answer,
            "search_results": search_results
        })

        # 判斷停止
        if any(word in answer for word in stop_words):
            if verbose:
                print("偵測到停止條件，提早結束。")
            break

        # 更新下一輪 Query
        if dynamic_next_query:
            current_query = f"根據你的回答「{answer}」，請補充更多細節、地點或時間背景。"
        else:
            break

    if verbose:
        print("\n多回合問答流程結束。")

    return history
