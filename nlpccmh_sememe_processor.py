# nlpccmh_sememe_processor.py

import json
from tqdm import tqdm
import sememe_tools as st

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