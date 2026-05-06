import streamlit as st
import requests
import hashlib
import json

st.set_page_config(page_title="Grok TTS 英語学習アプリ", layout="wide")
st.title("🚀 Grok TTS バイリンガル読み上げアプリ")

api_key = st.text_input("xAI APIキー（sk-から始まるキー）", type="password", value=st.session_state.get("api_key", ""))

voice = st.selectbox("声を選ぶ（Grok TTS）", ["eve", "ara", "rex", "sal", "leo"], index=0)

LLM_PROMPT = """あなたは最高の言語学習アシスタントです。
以下の英語テキストを処理して、JSON形式で返してください。

1. 自然な1文ごとに分割
2. 各文に自然な日本語訳
3. Grok TTS用に<emphasis>重要語</emphasis>や[pause]などを入れたtts_textを作成

出力はJSON配列のみ：
[
  {"id":1, "english":"原文", "japanese":"日本語訳", "tts_text":"Speech Tags入りテキスト"}
]

テキスト：
{user_text}"""

def process_text_with_grok(text: str):
    if not api_key:
        st.error("APIキーを入力してください")
        return []
    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "grok-4",
            "messages": [{"role": "system", "content": LLM_PROMPT.format(user_text=text)}],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
    )
    response.raise_for_status()
    data = response.json()
    return json.loads(data["choices"][0]["message"]["content"])

def generate_tts(tts_text: str, voice: str):
    cache_key = hashlib.sha256(f"{tts_text}{voice}".encode()).hexdigest()
    if cache_key in st.session_state.get("audio_cache", {}):
        return st.session_state.audio_cache[cache_key]
    
    response = requests.post(
        "https://api.x.ai/v1/tts",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"text": tts_text, "voice_id": voice, "language": "en"}
    )
    response.raise_for_status()
    audio = response.content
    if "audio_cache" not in st.session_state:
        st.session_state.audio_cache = {}
    st.session_state.audio_cache[cache_key] = audio
    return audio

user_text = st.text_area("英語テキストをここに貼り付けてください", height=200)

if st.button("✨ Grokで処理＆音声生成", type="primary"):
    with st.spinner("Grokが処理中..."):
        sentences = process_text_with_grok(user_text)
        if sentences:
            st.session_state.sentences = sentences
            st.session_state.voice = voice
            st.success(f"{len(sentences)}文に分割完了！")

if "sentences" in st.session_state:
    st.divider()
    for sent in st.session_state.sentences:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write(sent["english"])
            if st.button("▶️ 再生", key=f"play_{sent['id']}"):
                audio = generate_tts(sent["tts_text"], st.session_state.voice)
                st.audio(audio, format="audio/mp3")
        with col2:
            st.write(sent["japanese"])
        if st.button("📥 MP3ダウンロード", key=f"dl_{sent['id']}"):
            audio = generate_tts(sent["tts_text"], st.session_state.voice)
            st.download_button("今すぐダウンロード", audio, f"sentence_{sent['id']}.mp3", "audio/mp3", key=f"download_{sent['id']}")

st.caption("Grok TTS全力活用｜1文ごと再生・日本語訳・MP3ダウンロード・キャッシュ対応")
