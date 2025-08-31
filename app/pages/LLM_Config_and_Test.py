import os
import re
from typing import Dict, Optional

import httpx
import streamlit as st


st.set_page_config(page_title="LLM 配置与测试", layout="wide")
st.title("LLM 配置与测试")


def _read_env_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _update_env_content(content: str, updates: Dict[str, str]) -> str:
    # Only update keys with non-empty values; preserve comments and order
    lines = content.splitlines()
    present = {k: False for k in updates.keys() if updates[k]}
    key_pattern = re.compile(r"^([A-Z0-9_]+)=.*$")
    out_lines = []
    for line in lines:
        m = key_pattern.match(line.strip())
        if m:
            key = m.group(1)
            if key in updates and updates[key]:
                out_lines.append(f"{key}={updates[key]}")
                present[key] = True
            else:
                out_lines.append(line)
        else:
            out_lines.append(line)
    # Append any missing keys
    for k, v in updates.items():
        if v and not present.get(k, True):
            out_lines.append(f"{k}={v}")
    return "\n".join(out_lines) + ("\n" if out_lines else "")


def save_env(updates: Dict[str, str]) -> None:
    env_path = os.path.join(os.getcwd(), ".env")
    content = _read_env_file(env_path)
    new_content = _update_env_content(content, updates)
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def test_openai(api_key: str, model: str, prompt: str, base_url: Optional[str] = None) -> str:
    base = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com").rstrip("/")
    url = f"{base}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    with httpx.Client(timeout=30) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return str(data)


def test_gemini(api_key: str, model: str, prompt: str) -> str:
    # Generative Language API (v1beta)
    base = "https://generativelanguage.googleapis.com"
    url = f"{base}/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    with httpx.Client(timeout=30) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return str(data)


def test_ollama(host: str, model: str, prompt: str) -> str:
    base = (host or "http://localhost:11434").rstrip("/")
    url = f"{base}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    with httpx.Client(timeout=60) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    return data.get("response", "")


with st.sidebar:
    st.header("提供商选择")
    provider = st.selectbox("LLM 提供商", ["OpenAI", "Gemini", "Ollama"], index=0)


st.subheader("配置")

col1, col2 = st.columns(2)
with col1:
    openai_api_key = st.text_input(
        "OPENAI_API_KEY", value=os.environ.get("OPENAI_API_KEY", ""), type="password"
    )
    openai_base = st.text_input(
        "OPENAI_BASE_URL (可选)", value=os.environ.get("OPENAI_BASE_URL", "")
    )
    openai_model = st.text_input(
        "OPENAI_MODEL", value=os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    )

with col2:
    gemini_key = st.text_input(
        "GEMINI_API_KEY", value=os.environ.get("GEMINI_API_KEY", ""), type="password"
    )
    gemini_model = st.text_input("GEMINI_MODEL", value=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"))
    ollama_host = st.text_input("OLLAMA_HOST", value=os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
    ollama_model = st.text_input("OLLAMA_MODEL", value=os.environ.get("OLLAMA_MODEL", "llama3.1:8b"))


def _updates_for_provider(p: str) -> Dict[str, str]:
    if p == "OpenAI":
        return {
            "OPENAI_API_KEY": openai_api_key.strip(),
            "OPENAI_BASE_URL": openai_base.strip(),
            "OPENAI_MODEL": openai_model.strip(),
        }
    if p == "Gemini":
        return {
            "GEMINI_API_KEY": gemini_key.strip(),
            "GEMINI_MODEL": gemini_model.strip(),
        }
    # Ollama
    return {
        "OLLAMA_HOST": ollama_host.strip(),
        "OLLAMA_MODEL": ollama_model.strip(),
    }


st.markdown("—")

save_col, test_col = st.columns([1, 3])
with save_col:
    if st.button("保存到 .env"):
        updates = {k: v for k, v in _updates_for_provider(provider).items() if v}
        if not updates:
            st.warning("没有可保存的值（空字段将被忽略）")
        else:
            try:
                save_env(updates)
                st.success("已写入 .env。重启应用以使环境变量生效。")
            except Exception as e:
                st.error(f"保存失败: {e}")


st.subheader("测试对话")
prompt = st.text_area("输入测试提示", value="用一句话介绍这个应用。", height=120)

if st.button("发送测试"):
    try:
        if provider == "OpenAI":
            key = openai_api_key.strip()
            model = (openai_model.strip() or "gpt-4o-mini")
            if not key:
                st.error("请填写 OPENAI_API_KEY")
            else:
                with st.spinner("调用 OpenAI..."):
                    reply = test_openai(key, model, prompt, base_url=openai_base.strip() or None)
                st.write(reply)
        elif provider == "Gemini":
            key = gemini_key.strip()
            model = (gemini_model.strip() or "gemini-2.0-flash")
            if not key:
                st.error("请填写 GEMINI_API_KEY")
            else:
                with st.spinner("调用 Gemini..."):
                    reply = test_gemini(key, model, prompt)
                st.write(reply)
        else:
            host = ollama_host.strip() or "http://localhost:11434"
            model = ollama_model.strip() or "llama3.1:8b"
            with st.spinner("调用 Ollama..."):
                reply = test_ollama(host, model, prompt)
            st.write(reply)
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP {e.response.status_code}: {e.response.text[:400]}")
    except Exception as e:
        st.error(f"请求失败: {e}")

