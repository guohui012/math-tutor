# -*- coding: utf-8 -*-
"""DeepSeek API 讲解模块（OpenAI 兼容接口，流式返回）。"""
import json

import requests

SYSTEM_PROMPT = """你是一位治学严谨的大学数学教授，目标是把数学讲透、帮学生真正理解，而不是只给答案。

请严格遵循：
1. 严格性：每一步推导都注明依据（定理、定义、恒等变形），不跳步、不臆造、不糊弄。
2. 原理优先：先讲清本题涉及的核心概念/定理，再讲"为什么这样想、为什么这样做"。
3. 结构清晰：用 **粗体小标题** 分节，建议顺序：**核心概念** → **思路分析** → **详细步骤** → **易错点与推广**。
4. 公式一律用 LaTeX：行内用 $...$，独立公式用 $$...$$。讲解用中文。
5. 若题目附带了"计算引擎（SymPy）的精确结果"，必须以该结果为准讲解；不要自行重算、不要给出与之矛盾的结论。若你判断该结果可疑，明确指出来并说明理由。
6. 主动指出学生常见的概念误区；结尾可给一道同类变式题帮学生巩固（不直接给答案）。
7. 只讲数学本身，不编造来源或引用。"""


def build_messages(query, computation=None):
    system = SYSTEM_PROMPT
    if computation and computation.get("ok"):
        extra = ""
        if computation.get("approx"):
            extra = f"\n- 数值近似：{computation['approx']}"
        note = computation.get("note")
        user = (
            f"问题：{query}\n\n"
            f"计算引擎（SymPy）的精确结果如下，请基于它讲解原理与步骤：\n"
            f"- 输入理解：{computation.get('interpreted', '')}\n"
            f"- 结果：{computation.get('result', '')}{extra}\n"
            + (f"- 说明：{note}\n" if note else "")
            + "\n请讲解。"
        )
    else:
        user = f"问题：{query}\n\n请严谨地讲解（概念、原理、推导）。"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def stream_explain(query, computation, cfg):
    base = cfg.get("deepseek_base_url", "https://api.deepseek.com").rstrip("/")
    url = base + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg['deepseek_api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg.get("deepseek_model", "deepseek-chat"),
        "messages": build_messages(query, computation),
        "stream": True,
        "temperature": cfg.get("deepseek_temperature", 0.1),
    }
    with requests.post(url, headers=headers, json=payload, stream=True, timeout=(10, 180)) as resp:
        if resp.status_code != 200:
            raise RuntimeError(f"DeepSeek 接口返回 {resp.status_code}：{resp.text[:400]}")
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            line = line.strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            choices = obj.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            content = delta.get("content")
            if content:
                yield content
