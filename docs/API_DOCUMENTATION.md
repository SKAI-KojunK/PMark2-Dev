# PMark1 API 문서

## 📋 목차

1. [개요](#개요)
2. [인증](#인증)
3. [기본 응답 형식](#기본-응답-형식)
4. [채팅 API](#채팅-api)
5. [작업상세 API](#작업상세-api)
6. [헬스 체크 API](#헬스-체크-api)
7. [에러 처리](#에러-처리)
8. [예시 및 사용법](#예시-및-사용법)

## 📖 개요

PMark1 AI Assistant는 설비관리 시스템을 위한 자연어 기반 AI 작업요청 생성 API를 제공합니다. 이 API를 통해 사용자의 자연어 입력을 분석하고, 유사한 작업을 추천하며, 작업상세를 자동 생성할 수 있습니다.

### 기본 정보
- **Base URL**: `http://localhost:8000`
- **API 버전**: v1
- **문서**: `http://localhost:8000/docs` (Swagger UI)
- **대안 문서**: `http://localhost:8000/redoc` (ReDoc)

### 지원하는 기능
- 자연어 입력 파싱 및 분석
- LLM 기반 용어 정규화
- 유사 작업 추천
- 작업상세 자동 생성
- 최종 작업요청 완성

## 🔐 인증

현재 버전에서는 인증이 필요하지 않습니다. 향후 버전에서 JWT 토큰 기반 인증이 추가될 예정입니다.

## 📄 기본 응답 형식

### 성공 응답
```json
{
  "message": "응답 메시지",
  "data": {
    // 응답 데이터
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 에러 응답
```json
{
  "detail": "에러 메시지",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 💬 채팅 API

### POST /api/v1/chat

사용자의 자연어 입력을 분석하고 유사한 작업을 추천합니다.

#### 요청

**Content-Type**: `application/json`

```json
{
  "message": "1PE 압력베젤 고장",
  "conversation_history": [
    {
      "role": "user",
      "content": "안녕하세요",
      "timestamp": "2024-01-01T00:00:00Z"
    },
    {
      "role": "assistant", 
      "content": "안녕하세요! 설비관리 작업요청을 도와드리겠습니다.",
      "timestamp": "2024-01-01T00:00:01Z"
    }
  ]
}
```

#### 응답

**Status**: `200 OK`

```json
{
  "message": "입력하신 내용을 분석했습니다:\n\n• 위치/공정: No.1 PE\n• 설비유형: Pressure Vessel\n• 현상코드: 고장\n• 우선순위: 일반작업\n\n분석 신뢰도: 95.0%\n\n유사한 작업 3건을 찾았습니다:\n1. Pressure Vessel (No.1 PE) - 유사도 95.0%\n2. Pressure Vessel (No.2 PE) - 유사도 85.0%\n3. Storage Tank (No.1 PE) - 유사도 75.0%\n\n원하는 작업을 선택하시면 상세 정보를 제공해드립니다.",
  "recommendations": [
    {
      "itemno": "12345",
      "process": "RFCC",
      "location": "No.1 PE",
      "equipType": "Pressure Vessel",
      "statusCode": "고장",
      "priority": "일반작업",
      "score": 0.95,
      "work_title": "압력용기 고장 점검 및 수리",
      "work_details": "압력용기 내부 점검 후 고장 부위 확인 및 수리 작업 수행"
    },
    {
      "itemno": "12346",
      "process": "RFCC",
      "location": "No.2 PE",
      "equipType": "Pressure Vessel",
      "statusCode": "고장",
      "priority": "일반작업",
      "score": 0.85,
      "work_title": "압력용기 고장 점검",
      "work_details": "압력용기 고장 부위 점검 및 수리 작업"
    }
  ],
  "parsed_input": {
    "scenario": "S1",
    "location": "No.1 PE",
    "equipment_type": "Pressure Vessel",
    "status_code": "고장",
    "priority": "일반작업",
    "itemno": null,
    "confidence": 0.95
  },
  "needs_additional_input": false,
  "missing_fields": []
}
```

#### 요청 파라미터

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| message | string | ✅ | 사용자 입력 메시지 |
| conversation_history | array | ❌ | 대화 히스토리 |

#### 응답 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| message | string | 봇 응답 메시지 |
| recommendations | array | 추천 항목 목록 |
| parsed_input | object | 파싱된 입력 데이터 |
| needs_additional_input | boolean | 추가 입력 필요 여부 |
| missing_fields | array | 누락된 필드 목록 |

#### 추천 항목 구조

| 필드 | 타입 | 설명 |
|------|------|------|
| itemno | string | 작업 번호 |
| process | string | 공정명 |
| location | string | 위치 |
| equipType | string | 설비유형 |
| statusCode | string | 현상코드 |
| priority | string | 우선순위 |
| score | float | 유사도 점수 (0.0~1.0) |
| work_title | string | 작업명 |
| work_details | string | 작업상세 |

#### 파싱된 입력 구조

| 필드 | 타입 | 설명 |
|------|------|------|
| scenario | string | 시나리오 (S1/S2) |
| location | string | 위치/공정 |
| equipment_type | string | 설비유형 |
| status_code | string | 현상코드 |
| priority | string | 우선순위 |
| itemno | string | ITEMNO (시나리오 2용) |
| confidence | float | 분석 신뢰도 (0.0~1.0) |

## 🔧 작업상세 API

### POST /api/v1/generate-work-details

선택된 추천 항목에 대한 작업명과 작업상세를 생성합니다.

#### 요청

**Content-Type**: `application/json`

```json
{
  "selected_recommendation": {
    "itemno": "12345",
    "process": "RFCC",
    "location": "No.1 PE",
    "equipType": "Pressure Vessel",
    "statusCode": "고장",
    "priority": "일반작업",
    "score": 0.95
  },
  "user_message": "1PE 압력베젤 고장"
}
```

#### 응답

**Status**: `200 OK`

```json
{
  "work_title": "압력용기 고장 점검 및 수리",
  "work_details": "압력용기 내부 점검 후 고장 부위 확인 및 수리 작업 수행. 안전 작업 절차를 준수하여 작업을 진행합니다."
}
```

#### 요청 파라미터

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| selected_recommendation | object | ✅ | 선택된 추천 항목 |
| user_message | string | ✅ | 사용자 원본 메시지 |

#### 응답 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| work_title | string | 생성된 작업명 |
| work_details | string | 생성된 작업상세 |

### POST /api/v1/finalize-work-order

최종 작업요청을 완성하고 시스템에 저장합니다.

#### 요청

**Content-Type**: `application/json`

```json
{
  "work_title": "압력용기 고장 점검 및 수리",
  "work_details": "압력용기 내부 점검 후 고장 부위 확인 및 수리 작업 수행",
  "selected_recommendation": {
    "itemno": "12345",
    "process": "RFCC",
    "location": "No.1 PE",
    "equipType": "Pressure Vessel",
    "statusCode": "고장",
    "priority": "일반작업",
    "score": 0.95
  },
  "user_message": "1PE 압력베젤 고장"
}
```

#### 응답

**Status**: `200 OK`

```json
{
  "message": "✅ 작업요청이 성공적으로 완성되었습니다!\n\n**작업요청 번호**: WO12345678\n**작업명**: 압력용기 고장 점검 및 수리\n**작업상세**: 압력용기 내부 점검 후 고장 부위 확인 및 수리 작업 수행\n\n**설비 정보**\n• 공정: RFCC\n• 위치: No.1 PE\n• 설비유형: Pressure Vessel\n• 현상코드: 고장\n• 우선순위: 일반작업\n\n작업요청이 시스템에 등록되었습니다. 담당자가 검토 후 작업을 진행할 예정입니다.",
  "work_order": {
    "itemno": "WO12345678",
    "work_title": "압력용기 고장 점검 및 수리",
    "work_details": "압력용기 내부 점검 후 고장 부위 확인 및 수리 작업 수행",
    "process": "RFCC",
    "location": "No.1 PE",
    "equipType": "Pressure Vessel",
    "statusCode": "고장",
    "priority": "일반작업",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 요청 파라미터

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| work_title | string | ✅ | 최종 작업명 |
| work_details | string | ✅ | 최종 작업상세 |
| selected_recommendation | object | ✅ | 선택된 추천 항목 |
| user_message | string | ✅ | 사용자 원본 메시지 |

#### 응답 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| message | string | 완성 메시지 |
| work_order | object | 완성된 작업요청 정보 |

#### 작업요청 구조

| 필드 | 타입 | 설명 |
|------|------|------|
| itemno | string | 작업요청 번호 |
| work_title | string | 작업명 |
| work_details | string | 작업상세 |
| process | string | 공정명 |
| location | string | 위치 |
| equipType | string | 설비유형 |
| statusCode | string | 현상코드 |
| priority | string | 우선순위 |
| created_at | string | 생성일시 |

## 🏥 헬스 체크 API

### GET /health

시스템 상태를 확인합니다.

#### 요청

**Method**: `GET`

#### 응답

**Status**: `200 OK`

```json
{
  "status": "healthy",
  "database": "healthy",
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "disk_percent": 23.1
  },
  "timestamp": 1704067200.0
}
```

#### 응답 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| status | string | 전체 시스템 상태 |
| database | string | 데이터베이스 상태 |
| system | object | 시스템 리소스 정보 |
| timestamp | float | 응답 시간 |

## ❌ 에러 처리

### HTTP 상태 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 |
| 404 | 리소스를 찾을 수 없음 |
| 422 | 유효성 검사 실패 |
| 500 | 서버 내부 오류 |

### 에러 응답 예시

#### 400 Bad Request
```json
{
  "detail": "선택된 추천 항목이 없습니다.",
  "error_code": "MISSING_RECOMMENDATION",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "서버 내부 오류가 발생했습니다.",
  "error_code": "INTERNAL_ERROR",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 📝 예시 및 사용법

### 1. 기본 채팅 플로우

```bash
# 1. 사용자 입력 분석
curl -X POST "http://localhost:8000/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "1PE 압력베젤 고장"
     }'

# 2. 작업상세 생성
curl -X POST "http://localhost:8000/api/v1/generate-work-details" \
     -H "Content-Type: application/json" \
     -d '{
       "selected_recommendation": {
         "itemno": "12345",
         "process": "RFCC",
         "location": "No.1 PE",
         "equipType": "Pressure Vessel",
         "statusCode": "고장",
         "priority": "일반작업",
         "score": 0.95
       },
       "user_message": "1PE 압력베젤 고장"
     }'

# 3. 작업요청 완성
curl -X POST "http://localhost:8000/api/v1/finalize-work-order" \
     -H "Content-Type: application/json" \
     -d '{
       "work_title": "압력용기 고장 점검 및 수리",
       "work_details": "압력용기 내부 점검 후 고장 부위 확인 및 수리 작업 수행",
       "selected_recommendation": {
         "itemno": "12345",
         "process": "RFCC",
         "location": "No.1 PE",
         "equipType": "Pressure Vessel",
         "statusCode": "고장",
         "priority": "일반작업",
         "score": 0.95
       },
       "user_message": "1PE 압력베젤 고장"
     }'
```

### 2. Python 클라이언트 예시

```python
import requests
import json

class PMark1Client:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def chat(self, message, conversation_history=None):
        """채팅 API 호출"""
        url = f"{self.base_url}/api/v1/chat"
        data = {
            "message": message,
            "conversation_history": conversation_history or []
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def generate_work_details(self, selected_recommendation, user_message):
        """작업상세 생성 API 호출"""
        url = f"{self.base_url}/api/v1/generate-work-details"
        data = {
            "selected_recommendation": selected_recommendation,
            "user_message": user_message
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def finalize_work_order(self, work_title, work_details, selected_recommendation, user_message):
        """작업요청 완성 API 호출"""
        url = f"{self.base_url}/api/v1/finalize-work-order"
        data = {
            "work_title": work_title,
            "work_details": work_details,
            "selected_recommendation": selected_recommendation,
            "user_message": user_message
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

# 사용 예시
client = PMark1Client()

# 1. 채팅
chat_response = client.chat("1PE 압력베젤 고장")
print(f"봇 응답: {chat_response['message']}")

# 2. 추천 항목 선택
recommendation = chat_response['recommendations'][0]

# 3. 작업상세 생성
work_details_response = client.generate_work_details(
    recommendation, 
    "1PE 압력베젤 고장"
)
print(f"작업명: {work_details_response['work_title']}")

# 4. 작업요청 완성
finalize_response = client.finalize_work_order(
    work_details_response['work_title'],
    work_details_response['work_details'],
    recommendation,
    "1PE 압력베젤 고장"
)
print(f"완성 메시지: {finalize_response['message']}")
```

### 3. JavaScript 클라이언트 예시

```javascript
class PMark1Client {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async chat(message, conversationHistory = []) {
        const response = await fetch(`${this.baseUrl}/api/v1/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                conversation_history: conversationHistory
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async generateWorkDetails(selectedRecommendation, userMessage) {
        const response = await fetch(`${this.baseUrl}/api/v1/generate-work-details`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                selected_recommendation: selectedRecommendation,
                user_message: userMessage
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async finalizeWorkOrder(workTitle, workDetails, selectedRecommendation, userMessage) {
        const response = await fetch(`${this.baseUrl}/api/v1/finalize-work-order`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                work_title: workTitle,
                work_details: workDetails,
                selected_recommendation: selectedRecommendation,
                user_message: userMessage
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
}

// 사용 예시
const client = new PMark1Client();

async function processWorkRequest() {
    try {
        // 1. 채팅
        const chatResponse = await client.chat('1PE 압력베젤 고장');
        console.log('봇 응답:', chatResponse.message);
        
        // 2. 추천 항목 선택
        const recommendation = chatResponse.recommendations[0];
        
        // 3. 작업상세 생성
        const workDetailsResponse = await client.generateWorkDetails(
            recommendation,
            '1PE 압력베젤 고장'
        );
        console.log('작업명:', workDetailsResponse.work_title);
        
        // 4. 작업요청 완성
        const finalizeResponse = await client.finalizeWorkOrder(
            workDetailsResponse.work_title,
            workDetailsResponse.work_details,
            recommendation,
            '1PE 압력베젤 고장'
        );
        console.log('완성 메시지:', finalizeResponse.message);
        
    } catch (error) {
        console.error('오류 발생:', error);
    }
}

processWorkRequest();
```

## 🔧 개발자 도구

### Swagger UI
- **URL**: `http://localhost:8000/docs`
- **설명**: 인터랙티브 API 문서 및 테스트 도구

### ReDoc
- **URL**: `http://localhost:8000/redoc`
- **설명**: 읽기 쉬운 API 문서

### OpenAPI 스키마
- **URL**: `http://localhost:8000/openapi.json`
- **설명**: OpenAPI 3.0 스키마 파일

## 📞 지원

API 사용 중 문제가 발생하거나 질문이 있으시면 개발팀에 연락해주세요.

- **이메일**: [개발팀 이메일]
- **GitHub Issues**: [저장소 URL]/issues
- **문서**: 이 문서 또는 Swagger UI 참조

---

**PMark1 AI Assistant API** - 설비관리 시스템의 미래를 만들어갑니다. 