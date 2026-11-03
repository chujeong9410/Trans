# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 상태

Streamlit 기반 다국어 번역기(영어/일본어/베트남어)입니다. 요구사항의 기준 문서는 `PRD.md`입니다. 기능을 구현하거나 검토할 때는 PRD의 기능 ID(F1~F9)와 성공 기준(11번)을 기준으로 삼으세요.

PRD와 다르게 구현한 부분(API 제약 때문):
- 모델 ID는 소문자 `gpt-6-astra`입니다. `GPT-6-Astra`로 호출하면 404가 납니다.
- `gpt-6-astra`는 `temperature`를 기본값만 지원하므로 지정하지 않습니다.
- 버튼에 국기 이모지를 넣지 않습니다. Windows에서는 "US/JP/VN" 글자로 보입니다.
- 키 이름은 `OPENAI_API_KEY`를 우선 읽고, 기존 `.env`에 맞춰 `OPEN_API_KEY`도 읽습니다.

## 명령어

```bash
pip install -r requirements.txt
streamlit run app.py                              # http://localhost:8501
streamlit run app.py --server.headless true       # 브라우저 자동 실행 없이 (Playwright 테스트용)
```

자동 테스트나 린터는 없습니다. 동작 확인은 Playwright MCP로 실행 중인 앱에 접속해 진행합니다. 스크린샷은 `.playwright-mcp/`(gitignore 대상)에만 저장할 수 있습니다. 오류 상황은 `.env`를 건드리지 말고 환경 변수를 덮어쓴 서버를 다른 포트로 띄워 확인하세요. 예: `OPENAI_API_KEY=sk-invalid streamlit run app.py --server.port 8503`. `load_dotenv`는 이미 설정된 환경 변수를 덮어쓰지 않습니다. 키가 없는 상황은 `OPENAI_API_KEY=` `OPEN_API_KEY=` 두 변수를 모두 비워야 재현됩니다.

## 아키텍처

- 앱 전체가 `app.py` 단일 파일입니다. OpenAI 예외는 `translate()` 안에서 한국어 메시지를 담은 `TranslationError`로 바꿔 던지고, UI에서는 이것만 잡아 `st.error`로 보여줍니다.
- 번역 흐름: 텍스트 입력 → 언어 버튼 클릭 → `translate(text, target_language)` → OpenAI Chat API → 결과를 `st.session_state`에 저장 → 렌더링
- 버튼 라벨(한국어)과 프롬프트에 넣을 언어명(영어)은 `LANGUAGES` 딕셔너리 하나로 매핑합니다(영어→English, 일본어→Japanese, 베트남어→Vietnamese). 언어를 추가할 때는 이 매핑만 고치면 됩니다.
- Streamlit은 상호작용할 때마다 스크립트 전체를 다시 실행합니다. 따라서 번역 결과(원문, 대상 언어, 번역문)는 반드시 `st.session_state`에 보관해야 화면이 다시 그려진 뒤에도 남습니다(F8).
- System 프롬프트 원문은 PRD 6.1에 있습니다. 번역문만 출력하고 줄바꿈을 유지해야 하며, `temperature`는 지정하지 않습니다(gpt-6-astra는 기본값 1만 지원).

## 설정

- `.env`에서 `python-dotenv`로 읽습니다: `OPENAI_API_KEY`, `OPENAI_MODEL`(기본값 `gpt-6-astra` — OpenAI 모델 ID는 소문자). 모델명은 코드에 직접 쓰지 말고 항상 `OPENAI_MODEL`에서 읽으세요.
- `.env`에는 실제 키가 들어 있습니다. 내용을 읽거나 출력하거나 수정하지 마세요. API 키가 없는 경우 등을 테스트할 때는 `.env`를 고치지 말고 환경 변수를 바꿔 앱을 따로 실행하세요.
- API 키가 없으면 안내 메시지를 띄우고 번역 버튼을 비활성화합니다. 입력은 최대 5,000자로 제한합니다.
