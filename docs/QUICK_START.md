# PMark1-Dev 빠른 시작 가이드

이 문서는 PMark1-Dev 프로젝트의 **백엔드**와 **프론트엔드**를 최신 버전으로 올바르게 구동하는 방법을 안내합니다.

---

## 1. 환경 준비

### 1-1. Python 가상환경 및 의존성 설치
```bash
cd ~/Dropbox/2025_ECMiner/C_P02_SKAI/03_진행/PMark1-Dev/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 1-2. Node.js 및 프론트엔드 의존성 설치
```bash
cd ~/Dropbox/2025_ECMiner/C_P02_SKAI/03_진행/PMark1-Dev/frontend
npm install
```

### 1-3. 환경 변수 설정
- `backend/.env` 파일에 OpenAI API 키 등 필수 환경변수를 입력하세요.
- 예시:
  ```env
  OPENAI_API_KEY=sk-...
  ```

---

## 2. 서버 실행

### 2-1. 백엔드 서버 실행 (포트 8001)
```bash
cd ~/Dropbox/2025_ECMiner/C_P02_SKAI/03_진행/PMark1-Dev/backend
source venv/bin/activate
python run.py
```
- 서버가 정상적으로 시작되면 `http://localhost:8001/health`에서 `{ "status": "healthy" }` 응답을 확인할 수 있습니다.

### 2-2. 프론트엔드 서버 실행 (포트 3001)
```bash
cd ~/Dropbox/2025_ECMiner/C_P02_SKAI/03_진행/PMark1-Dev
python scripts/start_frontend.py
```
- 브라우저가 자동으로 열리며, `http://localhost:3001/chatbot.html`에서 챗봇 UI를 사용할 수 있습니다.

---

## 3. 문제 해결 및 주의사항

- **구버전(PMark-old, prototype 등) 코드/스크립트는 사용하지 마세요.**
- 반드시 `PMark1-Dev` 폴더 하위에서만 서버를 실행하세요.
- 포트 충돌이 발생하면 기존 프로세스를 종료하세요:
  ```bash
  pkill -f "python"
  pkill -f "uvicorn"
  pkill -f "node"
  pkill -f "react-scripts"
  ```
- 환경변수, 포트(8001/3001), 실행 경로가 올바른지 항상 확인하세요.
- `backend/.env` 파일이 없으면 백엔드가 실행되지 않습니다.
- 프론트엔드에서 `chatbot.html`이 없으면 UI가 표시되지 않습니다.

---

## 4. 참고
- 자세한 개발/운영 가이드는 `README.md`, `docs/DEVELOPMENT_GUIDE.md`를 참고하세요.
- 추가 문의는 개발팀에 연락하세요. 