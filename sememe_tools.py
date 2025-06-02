# sememe_tools.py

import os
import json
import jieba
import OpenHowNet
from opencc import OpenCC

cc_tw2sp = OpenCC('tw2sp')
custom_synonym_map = {}
custom_synonyms = {}
custom_sememe_relations = {}

try:
    OpenHowNet.download()
except Exception as e:
    # 建議改用 logging 或完全移除
    pass

hownet = OpenHowNet.HowNetDict()

def normalize_text(text):
    text = cc_tw2sp.convert(text)
    text = text.replace("台", "臺")
    return text.lower()

def inject_all_hownet_words(verbose=False):
    if verbose:
        print("正在注入 HowNet 詞彙進 jieba ...")
    all_words = set(sense.zh_word for sense in hownet.get_all_senses() if sense.zh_word)
    for word in all_words:
        try:
            jieba.add_word(word)
        except Exception as e:
            if verbose:
                print(f"加入 {word} 到 jieba 失敗：{e}")
    if verbose:
        print(f"已注入 {len(all_words)} 筆 HowNet 詞彙到 jieba")

def sememe_of_sentence(sentence):
    words = list(jieba.cut(sentence))
    sememe_map = {}
    skip_next = False
    for i in range(len(words)):
        if skip_next:
            skip_next = False
            continue
        word = words[i]
        standard_word = custom_synonym_map.get(word, word)
        simp_word = cc_tw2sp.convert(standard_word)
        senses = hownet.get_sense(simp_word)
        if (not senses or not getattr(senses[0], 'sememes', None)) and i + 1 < len(words):
            combined_word = word + words[i + 1]
            standard_combined_word = custom_synonym_map.get(combined_word, combined_word)
            combined_simp = cc_tw2sp.convert(standard_combined_word)
            combined_senses = hownet.get_sense(combined_simp)
            if combined_senses and getattr(combined_senses[0], 'sememes', None):
                sememe_map[combined_word] = [s.sememe if hasattr(s, "sememe") else str(s) for s in combined_senses[0].sememes]
                skip_next = True
                continue
        if senses and getattr(senses[0], 'sememes', None):
            sememe_map[word] = [s.sememe if hasattr(s, "sememe") else str(s) for s in senses[0].sememes]
        else:
            sememe_map[word] = []
    return sememe_map

def get_sememe_tags(sentence):
    sememe_map = sememe_of_sentence(sentence)
    tags = set()
    for taglist in sememe_map.values():
        tags.update(taglist)
    return sorted(tags)

def generate_pseudo_text(sentence):
    sememe_map = sememe_of_sentence(sentence)
    lines = []
    for word, sememes in sememe_map.items():
        if sememes:
            description = f'「{word}」這個詞表示 {"、".join(sememes)} 的語義。'
            lines.append(description)
    return " ".join(lines)

def analyze_sentence(sentence):
    sememe_map = sememe_of_sentence(sentence)
    sememe_set = set()
    for tags in sememe_map.values():
        sememe_set.update(tags)
    return {
        "input": sentence,
        "sememe_tags": sorted(sememe_set),
        "sememe_map": sememe_map
    }

def get_custom_synonym(sememe):
    if isinstance(sememe, dict) and "name" in sememe:
        key = sememe["name"]
    elif hasattr(sememe, "name"):
        key = sememe.name
    elif isinstance(sememe, str) and "|" in sememe:
        key = sememe.split("|")[0]
    else:
        key = str(sememe)
    entry = custom_synonyms.get(key)
    if not entry:
        for k, v in custom_synonyms.items():
            if key in v.get("synonyms", []):
                entry = v
                break
    if entry:
        main = entry.get("zh", key)
        alias = entry.get("synonyms", [])
        return [main] + alias
    return [key]

def format_sememe_map(sememe_map, style="display", clean_for_vector=False, remove_duplicates=True, sort_result=True):
    descriptions = []
    def clean_synonyms(synonyms):
        if remove_duplicates:
            synonyms = list(set(synonyms))
        if sort_result:
            synonyms = sorted(synonyms)
        return synonyms
    for word, sememes in sememe_map.items():
        if not sememes:
            continue
        enhanced = []
        for s in sememes:
            synonyms = get_custom_synonym(s)
            synonyms = clean_synonyms(synonyms)
            if clean_for_vector:
                enhanced.extend(synonyms)
            else:
                synonym_str = "、".join(synonyms)
                enhanced.append(f"{synonym_str}")
        if clean_for_vector:
            descriptions.append("、".join(enhanced))
        else:
            descriptions.append(f"「{word}」對應語意：{{{{{', '.join(enhanced)}}}}}")
    return descriptions

def generate_augmented_query(question: str, sememe_map: dict, remove_duplicates=True, sort_result=True) -> str:
    def clean_synonyms(synonyms):
        if remove_duplicates:
            synonyms = list(set(synonyms))
        if sort_result:
            synonyms = sorted(synonyms)
        return synonyms
    def describe(sememe_map):
        desc = []
        for word, sememes in sememe_map.items():
            if not sememes:
                continue
            expanded_synonyms = []
            for s in sememes:
                expanded_synonyms.extend(get_custom_synonym(s))
            expanded_synonyms = clean_synonyms(expanded_synonyms)
            sememe_text = "、".join(expanded_synonyms)
            desc.append(f"{word} 含有語意「{sememe_text}」")
        return "；".join(desc)
    pseudo_text = describe(sememe_map)
    return f"[Q] {question} [SEP] {pseudo_text}"

def set_custom_synonym_map(synonym_map):
    global custom_synonym_map
    custom_synonym_map = synonym_map

def set_custom_synonyms(synonyms):
    global custom_synonyms
    custom_synonyms = synonyms

def set_custom_sememe_relations(relations):
    global custom_sememe_relations
    custom_sememe_relations = relations

def load_custom_sememe_data(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    set_custom_synonyms(data.get("synonyms", {}))
    set_custom_sememe_relations(data.get("sememe_relations", {}))

def get_related_sememes(sememe_name):
    entry = custom_sememe_relations.get(sememe_name)
    if not entry:
        return []
    related = set(entry.get("related_to", []))
    for k, v in custom_sememe_relations.items():
        if sememe_name in v.get("related_to", []):
            related.add(k)
    return sorted(list(related))

# 只在直接執行才顯示提示
if __name__ == "__main__":
    inject_all_hownet_words(verbose=True)
    print("sememe_tools 完成初始化！")
