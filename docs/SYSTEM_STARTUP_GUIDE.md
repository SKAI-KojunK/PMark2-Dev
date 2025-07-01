# PMark1 시스템 시작/종료 가이드

## 📋 개요

이 문서는 PMark1 AI Assistant 시스템을 시작하고 종료하는 방법을 순차적으로 설명합니다.

### 🏗️ 시스템 구성
- **백엔드**: FastAPI 서버 (포트 8001)
- **프론트엔드**: 정적 HTML 서버 (포트 3001)
- **데이터베이스**: SQLite (자동 생성)

---

## 🚀 시스템 시작 방법

### 1단계: 프로젝트 디렉토리 이동
```bash
cd /Users/YMARX/Dropbox/2025_ECMiner/C_P02_SKAI/03_진행/PMark1-Dev
```

### 2단계: 백엔드 서버 시작
```bash
# 백엔드 디렉토리로 이동
cd backend

# 가상환경 활성화
source venv/bin/activate

# 백엔드 서버 시작
python run.py
```

**예상 출력:**
```
🚀 PMark1 Backend Server Starting...
🌐 Server running on:
   • Local:    http://localhost:8001
   • Network:  http://192.168.0.4:8001
📡 Other computers can access: http://192.168.0.4:8001
🛑 Press Ctrl+C to stop the server
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
🚀 PMark1 AI Assistant 시작 중...
✅ 데이터베이스 초기화 완료
INFO:     Application startup complete.
```

### 3단계: 백엔드 서버 상태 확인
새로운 터미널 창을 열고:
```bash
curl http://localhost:8001/health
```

**정상 응답:**
```json
{"status":"healthy"}
```

### 4단계: 프론트엔드 서버 시작
새로운 터미널 창을 열고:
```bash
# 프로젝트 루트 디렉토리로 이동
cd /Users/YMARX/Dropbox/2025_ECMiner/C_P02_SKAI/03_진행/PMark1-Dev

# 프론트엔드 서버 시작
python start_frontend.py
```

**예상 출력:**
```
🚀 PMark1 Frontend Server Starting...
📁 Current directory: /Users/YMARX/Dropbox/2025_ECMiner/C_P02_SKAI/03_진행/PMark1-Dev
🌐 Server running on:
   • Local:    http://localhost:3001
   • Network:  http://192.168.0.4:3001
📡 Other computers can access:
   • Chatbot:     http://192.168.0.4:3001/
   • Prototype:   http://192.168.0.4:3001/old
👥 Multi-user support: ✅ ENABLED
🛑 Press Ctrl+C to stop the server
✅ chatbot.html found
🔥 Server ready for multiple concurrent users!
```

### 5단계: 프론트엔드 서버 상태 확인
새로운 터미널 창을 열고:
```bash
curl http://localhost:3001
```

**정상 응답:** HTML 페이지 내용이 출력됨

### 6단계: 웹 브라우저에서 접속
브라우저에서 다음 URL로 접속:
```
http://localhost:3001
```

---

## 🛑 시스템 종료 방법

### 방법 1: 각 서버별 개별 종료 (권장)

#### 백엔드 서버 종료
백엔드 서버가 실행 중인 터미널에서:
```
Ctrl + C
```

**예상 출력:**
```
INFO:     Shutting down
INFO:     Waiting for application shutdown.
🛑 PMark1 AI Assistant 종료 중...
INFO:     Application shutdown complete.
INFO:     Finished server process [XXXXX]
INFO:     Stopping reloader process [XXXXX]
```

#### 프론트엔드 서버 종료
프론트엔드 서버가 실행 중인 터미널에서:
```
Ctrl + C
```

**예상 출력:**
```
✨ Frontend server stopped.
```

### 방법 2: 프로세스 강제 종료

#### 모든 Python 프로세스 종료
```bash
# 백엔드 서버 프로세스 종료
pkill -f "python run.py"

# 프론트엔드 서버 프로세스 종료
pkill -f "python start_frontend.py"

# 모든 uvicorn 프로세스 종료
pkill -f "uvicorn"
```

#### 포트 사용 확인
```bash
# 8001 포트 사용 확인
lsof -i :8001

# 3001 포트 사용 확인
lsof -i :3001
```

---

## 🔄 시스템 재시작 방법

### 전체 시스템 재시작
1. **기존 서버 종료** (위의 종료 방법 참조)
2. **잠시 대기** (3-5초)
3. **백엔드 서버 시작** (2단계 참조)
4. **프론트엔드 서버 시작** (4단계 참조)
5. **상태 확인** (3단계, 5단계 참조)

### 빠른 재시작 스크립트
```bash
#!/bin/bash
# PMark1 시스템 재시작 스크립트

echo "🛑 기존 서버 종료 중..."
pkill -f "python run.py"
pkill -f "python start_frontend.py"
sleep 3

echo "🚀 백엔드 서버 시작 중..."
cd /Users/YMARX/Dropbox/2025_ECMiner/C_P02_SKAI/03_진행/PMark1-Dev/backend
source venv/bin/activate
python run.py &
sleep 10

echo "🌐 프론트엔드 서버 시작 중..."
cd /Users/YMARX/Dropbox/2025_ECMiner/C_P02_SKAI/03_진행/PMark1-Dev
python start_frontend.py &
sleep 5

echo "✅ 시스템 재시작 완료!"
echo "🌐 접속 URL: http://localhost:3001"
```

---

## 🔧 문제 해결

### 포트 충돌 문제
```bash
# 포트 사용 확인
lsof -i :8001
lsof -i :3001

# 충돌하는 프로세스 종료
kill -9 [PID]
```

### 데이터베이스 문제
```bash
# 데이터베이스 파일 확인
ls -la backend/data/

# 데이터베이스 재초기화
cd backend
source venv/bin/activate
python -c "from app.database import db_manager; db_manager.load_excel_data()"
```

### 가상환경 문제
```bash
# 가상환경 재생성
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### API 테스트
```bash
# 백엔드 API 테스트
curl http://localhost:8001/health
curl -X POST "http://localhost:8001/api/v1/chat" -H "Content-Type: application/json" -d '{"message": "test"}'

# 프론트엔드 테스트
curl http://localhost:3001
```

---

## 📝 주의사항

### ✅ 권장사항
- 각 서버를 별도 터미널에서 실행
- 서버 시작 후 상태 확인 필수
- 종료 시 Ctrl+C 사용 권장

### ❌ 주의사항
- 프로세스 강제 종료는 마지막 수단으로만 사용
- 데이터베이스 파일 삭제 금지
- 가상환경 활성화 상태 확인 필수

### 🔍 모니터링
- 서버 로그 확인
- 포트 사용 상태 확인
- API 응답 상태 확인

---

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. 서버 로그 메시지
2. 포트 사용 상태
3. 데이터베이스 연결 상태
4. 가상환경 활성화 상태

**로그 위치:**
- 백엔드: 터미널 출력
- 프론트엔드: 터미널 출력
- 데이터베이스: `backend/data/sample_notifications.db` 