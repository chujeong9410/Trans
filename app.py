import os

import openai
import streamlit as st
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# 버튼 라벨 → 프롬프트에 넣을 언어명
# (국기 이모지는 Windows에서 "US"/"JP"/"VN" 글자로 보이므로 쓰지 않는다)
LANGUAGES = {
    "영어": "English",
    "일본어": "Japanese",
    "베트남어": "Vietnamese",
}
MAX_CHARS = 5000
DEFAULT_MODEL = "gpt-6-astra"  # OpenAI 모델 ID는 소문자 ("GPT-6-Astra"는 404)
SYSTEM_PROMPT = (
    "You are a professional translator. Translate the user's text into {target_language}. "
    "Output only the translated text, without explanations, quotes, or notes. "
    "Preserve line breaks and formatting."
)

# PRD 표준은 OPENAI_API_KEY. 기존 .env의 OPEN_API_KEY도 호환용으로 허용.
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY")
MODEL = os.getenv("OPENAI_MODEL") or DEFAULT_MODEL


class TranslationError(Exception):
    """사용자에게 그대로 보여줄 한국어 메시지를 담는 예외."""


@st.cache_resource
def get_client(api_key: str) -> openai.OpenAI:
    return openai.OpenAI(api_key=api_key, timeout=60)


def translate(text: str, target_language: str) -> str:
    # gpt-6-astra는 temperature 기본값(1)만 지원하므로 지정하지 않는다.
    try:
        response = get_client(API_KEY).chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(target_language=target_language)},
                {"role": "user", "content": text},
            ],
        )
    except openai.AuthenticationError:
        raise TranslationError("API 키가 올바르지 않습니다. .env의 OPENAI_API_KEY를 확인하세요.")
    except openai.NotFoundError:
        raise TranslationError(f"모델 '{MODEL}'을(를) 찾을 수 없습니다. .env의 OPENAI_MODEL을 확인하세요.")
    except openai.RateLimitError:
        raise TranslationError("요청 한도를 초과했거나 크레딧이 부족합니다. 잠시 후 다시 시도하세요.")
    except (openai.APIConnectionError, openai.APITimeoutError):
        raise TranslationError("OpenAI 서버에 연결할 수 없습니다. 네트워크 상태를 확인하세요.")
    except openai.BadRequestError:
        raise TranslationError(f"요청 형식이 모델 '{MODEL}'과(와) 맞지 않습니다. 모델 설정을 확인하세요.")
    except openai.APIStatusError as e:
        raise TranslationError(f"번역 요청이 실패했습니다. (HTTP {e.status_code})")

    result = (response.choices[0].message.content or "").strip()
    if not result:
        raise TranslationError("번역 결과가 비어 있습니다. 다시 시도하세요.")
    return result


st.set_page_config(page_title="다국어 번역기", page_icon="🌐", layout="centered")

st.markdown(
    """
    <style>
    .block-container { max-width: 760px; padding-top: 2.5rem; }
    h1, h3 { word-break: keep-all; }
    .stButton > button { border-radius: 10px; font-weight: 600; padding: 0.55rem 0; }
    .hint { opacity: 0.55; text-align: center; padding: 2rem 0 1rem; }
    .footer { text-align: center; font-size: 0.75rem; opacity: 0.5; margin-top: 3rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌐 다국어 번역기")
st.caption("글을 입력하고 번역할 언어를 선택하세요.")

if not API_KEY:
    st.error(
        "OpenAI API 키가 설정되지 않았습니다.\n\n"
        "프로젝트 폴더의 `.env` 파일에 `OPENAI_API_KEY=sk-...`를 추가한 뒤 앱을 다시 실행하세요."
    )

text = st.text_area(
    "번역할 글",
    height=180,
    max_chars=MAX_CHARS,
    placeholder="번역할 글을 입력하세요",
    label_visibility="collapsed",
)

result = st.session_state.get("result")
last_label = result["label"] if result else None

clicked = None
cols = st.columns(len(LANGUAGES))
for col, label in zip(cols, LANGUAGES):
    if col.button(
        label,
        key=f"btn_{label}",
        type="primary" if label == last_label else "secondary",
        disabled=not API_KEY,
        use_container_width=True,
    ):
        clicked = label

if clicked:
    if not text.strip():
        st.warning("번역할 글을 입력하세요.")
    elif len(text) > MAX_CHARS:
        st.warning(f"최대 {MAX_CHARS:,}자까지 번역할 수 있습니다.")
    else:
        with st.spinner(f"{clicked}로 번역 중..."):
            try:
                st.session_state.result = {
                    "source": text,
                    "label": clicked,
                    "translation": translate(text, LANGUAGES[clicked]),
                }
                # 강조할 버튼이 바뀌었으므로 다시 그린다
                st.rerun()
            except TranslationError as e:
                st.error(str(e))

result = st.session_state.get("result")
if result:
    st.subheader(f"번역 결과 ({result['label']})")
    with st.container(border=True):
        st.code(result["translation"], language=None, wrap_lines=True)
    if result["source"] != text:
        st.caption("입력한 글이 바뀌었습니다. 다시 번역하려면 언어 버튼을 누르세요.")
else:
    st.markdown('<div class="hint">번역 결과가 여기에 표시됩니다.</div>', unsafe_allow_html=True)

st.markdown(f'<div class="footer">Powered by OpenAI {MODEL}</div>', unsafe_allow_html=True)
