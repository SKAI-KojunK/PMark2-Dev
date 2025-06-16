from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Optional, Dict, Any
import os
import openai
from dotenv import load_dotenv
import logging
import json

# 환경 변수 로드
load_dotenv()

# 로거 설정
logger = logging.getLogger(__name__)

# OpenAI 클라이언트 설정
def get_openai_client():
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY environment variable is not set")
            return None
        return openai.OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"Error creating OpenAI client: {str(e)}")
        return None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    text: str

class AnalyzeResponse(BaseModel):
    result: str

class RecommendRequest(BaseModel):
    text: str
    mode: Literal['itemno', 'equip']

class RecommendItem(BaseModel):
    itemno: str
    process: str
    location: str
    equipType: str
    statusCode: str
    score: int

class RecommendResponse(BaseModel):
    recommendations: List[RecommendItem]
    missing_fields: List[str] = []

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []

class FieldAnalysis(BaseModel):
    process: Optional[str] = None
    location: Optional[str] = None
    equipment: Optional[str] = None
    status: Optional[str] = None
    confidence_score: float = 0.0
    missing_fields: List[str] = []

class ChatResponse(BaseModel):
    message: str
    field_analysis: FieldAnalysis
    recommendations: List[RecommendItem] = []
    response_type: str  # "request_info", "provide_recommendations", "general"
    completeness_gauge: float  # 0.0 to 1.0

CONTEXT = """
공정명 예시: 생산 1팀, 제품운영팀, 정유1팀, Aromatic 1팀, FCC 1팀, 동력 1팀 등
로케이션 예시: 2RFCC, No.1 PE, PW-B3503, Nexlene 포장 공정, 합성수지 포장 등
설비유형 예시: Sample B/V Hand Wheel, Air Pump, Compressor, Dryer, Blower, Pump 등
현상코드 예시: 파손, 고장, 운전 Condition 이상, 예방 점검/정비, 기타, 정기/임시 보수 등
"""

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, client: openai.OpenAI = Depends(get_openai_client)) -> AnalyzeResponse:
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI client is not configured")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": req.text}],
            max_tokens=100
        )
        return AnalyzeResponse(result=response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest, client: openai.OpenAI = Depends(get_openai_client)) -> RecommendResponse:
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI client is not configured")
    
    try:
        extract_prompt = f"""
{CONTEXT}
아래 입력 문장에서 공정명(process), 로케이션(location), 설비유형(equipType), 현상코드(statusCode) 4가지를 반드시 추정해서 JSON으로 반환해줘.
입력값이 불완전하거나 명확하지 않아도, 반드시 4개 항목을 모두 채워서 반환해줘. 모르면 임의로라도 가장 그럴듯한 값을 넣어줘. 절대 빈 값이나 null을 반환하지 마.
예시:
입력: 생산 1팀, 2RFCC, Sample B/V Hand Wheel 파손
결과: {{"process": "생산 1팀", "location": "2RFCC", "equipType": "Sample B/V Hand Wheel", "statusCode": "파손"}}
입력: 정유1팀, No.1 PE, Air Pump 고장
결과: {{"process": "정유1팀", "location": "No.1 PE", "equipType": "Air Pump", "statusCode": "고장"}}
입력: {req.text}
"""
        extract_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": extract_prompt}],
            max_tokens=200
        )
        extract_content = extract_resp.choices[0].message.content
        try:
            fields = json.loads(extract_content[extract_content.find('{'):extract_content.rfind('}')+1])
        except Exception as e:
            logger.error(f"Error parsing JSON from OpenAI response: {str(e)}")
            fields = {}
        
        required = ["process", "location", "equipType", "statusCode"]
        missing = [k for k in required if not fields.get(k)]
        if missing:
            return RecommendResponse(recommendations=[], missing_fields=missing)
                
        recommend_prompt = f"""
{CONTEXT}
아래 항목(process, location, equipType, statusCode)에 기반해서, 예시와 비슷한 추천 5개를 반드시 JSON 리스트로 만들어줘.
예시:
[
  {{"itemno": "EG-AD-501", "process": "제품운영팀", "location": "No.1 PE", "equipType": "Air Pump", "statusCode": "운전 Condition 이상", "score": 92}},
  ...
]
항목: {json.dumps(fields, ensure_ascii=False)}
"""
        rec_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": recommend_prompt}],
            max_tokens=600
        )
        rec_content = rec_resp.choices[0].message.content
        try:
            data = json.loads(rec_content[rec_content.find('['):rec_content.rfind(']')+1])
            for d in data:
                if not (80 <= int(d.get('score', 0)) <= 99):
                    d['score'] = 90
            return RecommendResponse(recommendations=data, missing_fields=[])
        except Exception as e:
            logger.error(f"Error parsing recommendations: {str(e)}")
            pass
                
        return RecommendResponse(recommendations=[
            {"itemno": "EG-AD-501", "process": "제품운영팀", "location": "No.1 PE", "equipType": "Air Pump", "statusCode": "운전 Condition 이상", "score": 92},
            {"itemno": "EG-AD-502", "process": "정유1팀", "location": "PW-B3503", "equipType": "Compressor", "statusCode": "고장.결함.수명소진", "score": 89},
            {"itemno": "EG-AD-503", "process": "Aromatic 1팀", "location": "Nexlene 포장 공정", "equipType": "Dryer", "statusCode": "예방 점검/정비", "score": 86},
            {"itemno": "EG-AD-504", "process": "FCC 1팀", "location": "합성수지 포장", "equipType": "Blower", "statusCode": "기타", "score": 83},
            {"itemno": "EG-AD-505", "process": "생산 1팀", "location": "No.2 PP", "equipType": "Pump", "statusCode": "정기/임시 보수", "score": 80}
        ], missing_fields=[])
    except Exception as e:
        logger.error(f"Error in recommend endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-openai")
async def test_openai(client: openai.OpenAI = Depends(get_openai_client)):
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI client is not configured")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello, OpenAI! 이 응답이 보이면 API가 정상입니다."}],
            max_tokens=20
        )
        return {"result": response.choices[0].message.content}
    except Exception as e:
        logger.error(f"Error in test-openai endpoint: {str(e)}")
        if "API key" in str(e):
            raise HTTPException(status_code=401, detail="Invalid API key")
        elif "model" in str(e):
            raise HTTPException(status_code=400, detail="Invalid model name")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

# 헬스체크 엔드포인트 추가
@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Server is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, client: openai.OpenAI = Depends(get_openai_client)) -> ChatResponse:
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI client is not configured")
    
    try:
        # 1. 사용자 입력에서 4가지 항목 추출 및 분석
        field_analysis = await analyze_user_input(req.message, client)
        
        # 2. 완전성 게이지 계산
        completeness = calculate_completeness(field_analysis)
        
        # 3. 응답 타입 결정 및 메시지 생성
        if completeness <= 0.5:  # 2개 이하의 항목
            response_type = "request_info"
            message = "보다 정확한 안내를 위해 추가 정보를 입력해주세요.\n\n"
            if not field_analysis.process:
                message += "• 공정명: 어느 팀에서 작업하시나요? (예: 생산 1팀, 정유1팀 등)\n"
            if not field_analysis.location:
                message += "• 위치: 어떤 장소에서 발생한 문제인가요? (예: 2RFCC, No.1 PE 등)\n"
            if not field_analysis.equipment:
                message += "• 설비: 어떤 장비와 관련된 문제인가요? (예: Air Pump, Compressor 등)\n"
            if not field_analysis.status:
                message += "• 상태: 어떤 상황인가요? (예: 파손, 고장, 예방 점검 등)\n"
            
            return ChatResponse(
                message=message.strip(),
                field_analysis=field_analysis,
                recommendations=[],
                response_type=response_type,
                completeness_gauge=completeness
            )
        
        elif completeness < 1.0:  # 3개 항목 (1개 부족)
            response_type = "provide_recommendations"
            recommendations = await generate_recommendations_with_missing(field_analysis, client)
            message = f"입력하신 정보를 바탕으로 추천 결과를 준비했습니다.\n\n"
            if field_analysis.missing_fields:
                message += f"빠진 항목({', '.join(field_analysis.missing_fields)})에 대한 추천도 포함했습니다.\n\n"
            message += "해당하는 내용을 선택하시면, 작업요청을 완성해드립니다."
            
            return ChatResponse(
                message=message,
                field_analysis=field_analysis,
                recommendations=recommendations,
                response_type=response_type,
                completeness_gauge=completeness
            )
        
        else:  # 4개 항목 모두 있음
            response_type = "provide_recommendations"
            recommendations = await generate_full_recommendations(field_analysis, client)
            message = "모든 정보가 충분합니다! 다음과 같은 추천 결과를 준비했습니다.\n\n해당하는 내용을 선택하시면, 작업요청을 완성해드립니다."
            
            return ChatResponse(
                message=message,
                field_analysis=field_analysis,
                recommendations=recommendations,
                response_type=response_type,
                completeness_gauge=completeness
            )
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_user_input(text: str, client: openai.OpenAI) -> FieldAnalysis:
    """사용자 입력을 분석하여 4가지 항목을 추출합니다."""
    
    analysis_prompt = f"""
{CONTEXT}

다음 사용자 입력을 분석하여 4가지 항목을 추출해주세요:
1. process (공정명)
2. location (위치)  
3. equipment (설비)
4. status (상태)

각 항목이 명확하게 식별되면 해당 값을, 불명확하거나 없으면 null을 반환해주세요.
자연어 분석을 통해 의미를 유추할 수 있는 경우에만 값을 채워주세요.

응답은 반드시 다음 JSON 형식으로 해주세요:
{{
    "process": "값 또는 null",
    "location": "값 또는 null", 
    "equipment": "값 또는 null",
    "status": "값 또는 null",
    "confidence_score": 0.0-1.0
}}

사용자 입력: {text}
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=300
        )
        
        content = response.choices[0].message.content
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            data = json.loads(content[json_start:json_end])
            
            # null 값을 None으로 변환하고 missing_fields 계산
            process = data.get("process") if data.get("process") != "null" else None
            location = data.get("location") if data.get("location") != "null" else None
            equipment = data.get("equipment") if data.get("equipment") != "null" else None
            status = data.get("status") if data.get("status") != "null" else None
            
            missing_fields = []
            if not process:
                missing_fields.append("공정명")
            if not location:
                missing_fields.append("위치")
            if not equipment:
                missing_fields.append("설비")
            if not status:
                missing_fields.append("상태")
            
            return FieldAnalysis(
                process=process,
                location=location,
                equipment=equipment,
                status=status,
                confidence_score=data.get("confidence_score", 0.0),
                missing_fields=missing_fields
            )
    except Exception as e:
        logger.error(f"Error analyzing user input: {str(e)}")
    
    # 기본값 반환
    return FieldAnalysis(
        confidence_score=0.0,
        missing_fields=["공정명", "위치", "설비", "상태"]
    )

def calculate_completeness(field_analysis: FieldAnalysis) -> float:
    """4가지 항목의 완전성을 0.0-1.0으로 계산합니다."""
    filled_count = sum([
        1 if field_analysis.process else 0,
        1 if field_analysis.location else 0,
        1 if field_analysis.equipment else 0,
        1 if field_analysis.status else 0
    ])
    return filled_count / 4.0

async def generate_recommendations_with_missing(field_analysis: FieldAnalysis, client: openai.OpenAI) -> List[RecommendItem]:
    """부족한 항목이 있는 경우의 추천을 생성합니다."""
    
    filled_info = {}
    if field_analysis.process:
        filled_info["process"] = field_analysis.process
    if field_analysis.location:
        filled_info["location"] = field_analysis.location
    if field_analysis.equipment:
        filled_info["equipment"] = field_analysis.equipment
    if field_analysis.status:
        filled_info["status"] = field_analysis.status
    
    prompt = f"""
{CONTEXT}

사용자가 제공한 정보: {json.dumps(filled_info, ensure_ascii=False)}
누락된 항목: {', '.join(field_analysis.missing_fields)}

위 정보를 바탕으로 누락된 항목들을 합리적으로 추정하여 5개의 추천을 생성해주세요.
각 추천은 사용자가 제공한 정보는 그대로 유지하고, 누락된 부분만 채워서 완성해주세요.

응답은 반드시 다음 JSON 배열 형식으로 해주세요:
[
    {{
        "itemno": "EG-AD-XXX",
        "process": "공정명",
        "location": "위치",
        "equipType": "설비유형", 
        "statusCode": "상태코드",
        "score": 80-99
    }}
]
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        json_start = content.find('[')
        json_end = content.rfind(']') + 1
        
        if json_start != -1 and json_end > json_start:
            data = json.loads(content[json_start:json_end])
            return [RecommendItem(**item) for item in data]
            
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
    
    # 기본 추천 반환
    return [
        RecommendItem(itemno="EG-AD-501", process="생산 1팀", location="No.1 PE", equipType="Air Pump", statusCode="운전 Condition 이상", score=92),
        RecommendItem(itemno="EG-AD-502", process="정유1팀", location="PW-B3503", equipType="Compressor", statusCode="고장", score=89),
        RecommendItem(itemno="EG-AD-503", process="Aromatic 1팀", location="Nexlene 포장 공정", equipType="Dryer", statusCode="예방 점검/정비", score=86)
    ]

async def generate_full_recommendations(field_analysis: FieldAnalysis, client: openai.OpenAI) -> List[RecommendItem]:
    """모든 항목이 있는 경우의 추천을 생성합니다."""
    
    info = {
        "process": field_analysis.process,
        "location": field_analysis.location,
        "equipment": field_analysis.equipment,
        "status": field_analysis.status
    }
    
    prompt = f"""
{CONTEXT}

사용자 정보: {json.dumps(info, ensure_ascii=False)}

위 정보를 바탕으로 정확히 일치하거나 유사한 5개의 추천을 생성해주세요.
사용자가 제공한 정보와 최대한 일치하되, 약간의 변형도 포함해주세요.

응답은 반드시 다음 JSON 배열 형식으로 해주세요:
[
    {{
        "itemno": "EG-AD-XXX",
        "process": "공정명",
        "location": "위치",
        "equipType": "설비유형",
        "statusCode": "상태코드", 
        "score": 80-99
    }}
]
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        json_start = content.find('[')
        json_end = content.rfind(']') + 1
        
        if json_start != -1 and json_end > json_start:
            data = json.loads(content[json_start:json_end])
            return [RecommendItem(**item) for item in data]
            
    except Exception as e:
        logger.error(f"Error generating full recommendations: {str(e)}")
    
    # 기본 추천 반환
    return [
        RecommendItem(itemno="EG-AD-501", process=field_analysis.process or "생산 1팀", location=field_analysis.location or "No.1 PE", equipType=field_analysis.equipment or "Air Pump", statusCode=field_analysis.status or "운전 Condition 이상", score=95),
        RecommendItem(itemno="EG-AD-502", process=field_analysis.process or "생산 1팀", location=field_analysis.location or "No.1 PE", equipType=field_analysis.equipment or "Air Pump", statusCode=field_analysis.status or "운전 Condition 이상", score=92),
        RecommendItem(itemno="EG-AD-503", process=field_analysis.process or "생산 1팀", location=field_analysis.location or "No.1 PE", equipType=field_analysis.equipment or "Air Pump", statusCode=field_analysis.status or "운전 Condition 이상", score=88)
    ]

class WorkOrderRequest(BaseModel):
    selected_recommendation: RecommendItem
    user_message: str

@app.post("/complete-work-order")
async def complete_work_order(req: WorkOrderRequest):
    """작업요청을 완성합니다."""
    try:
        # 여기서 실제 작업요청 시스템과 연동할 수 있습니다
        return {
            "status": "success",
            "message": "작업요청이 완성되었습니다.",
            "work_order": {
                "itemno": req.selected_recommendation.itemno,
                "process": req.selected_recommendation.process,
                "location": req.selected_recommendation.location,
                "equipType": req.selected_recommendation.equipType,
                "statusCode": req.selected_recommendation.statusCode,
                "user_message": req.user_message
            }
        }
    except Exception as e:
        logger.error(f"Error completing work order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class WorkOrderDetailsRequest(BaseModel):
    selected_recommendation: RecommendItem
    user_message: str

class WorkOrderDetailsResponse(BaseModel):
    work_title: str
    work_details: str

@app.post("/generate-work-details", response_model=WorkOrderDetailsResponse)
async def generate_work_details(req: WorkOrderDetailsRequest, client: openai.OpenAI = Depends(get_openai_client)) -> WorkOrderDetailsResponse:
    """선택된 추천을 바탕으로 작업명과 작업상세를 생성합니다."""
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI client is not configured")
    
    try:
        rec = req.selected_recommendation
        
        # 작업명 생성
        title_prompt = f"""
다음 정보를 바탕으로 간결하고 명확한 작업명을 생성해주세요.

공정명: {rec.process}
위치: {rec.location}
설비: {rec.equipType}
상태: {rec.statusCode}

작업명은 다음 형식으로 작성해주세요:
[공정명] [위치] [설비] [상태] [작업유형]

예시: "제품운영팀 석유배합저장 시설 저장탱크 누수 보수 (중간점검)"

작업명만 반환해주세요. 추가 설명은 불필요합니다.
"""
        
        title_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": title_prompt}],
            max_tokens=100
        )
        
        work_title = title_response.choices[0].message.content.strip()
        
        # 작업상세 생성
        details_prompt = f"""
다음 정보를 바탕으로 작업의 내용을 구체적이고 이해하기 쉬운 자연어 문장으로 작성해주세요.

공정명: {rec.process}
위치: {rec.location}
설비: {rec.equipType}
상태: {rec.statusCode}
사용자 메시지: {req.user_message}

작업상세는 다음과 같은 정보를 포함해야 합니다:
- 어느 팀에서 (공정명)
- 어느 위치에서 (위치)
- 어떤 설비의 (설비)
- 어떤 문제로 인한 (상태)
- 어떤 작업이 필요한지

예시: "제품운영팀의 석유배합저장시설 옆에 있는 저장탱크에서 중간점검 지적 사항으로 나온 워터드레인 밸브 누수되는 내용 보수"

자연스럽고 구체적인 문장으로 작성해주세요. 작업상세 내용만 반환해주세요.
"""
        
        details_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": details_prompt}],
            max_tokens=200
        )
        
        work_details = details_response.choices[0].message.content.strip()
        
        return WorkOrderDetailsResponse(
            work_title=work_title,
            work_details=work_details
        )
        
    except Exception as e:
        logger.error(f"Error generating work details: {str(e)}")
        # 기본값 반환
        rec = req.selected_recommendation
        default_title = f"{rec.process} {rec.location} {rec.equipType} {rec.statusCode} 작업"
        default_details = f"{rec.process}에서 {rec.location} 위치의 {rec.equipType} 설비에 {rec.statusCode} 상황이 발생하여 관련 작업이 필요합니다."
        
        return WorkOrderDetailsResponse(
            work_title=default_title,
            work_details=default_details
        )

class FinalWorkOrderRequest(BaseModel):
    work_title: str
    work_details: str
    selected_recommendation: RecommendItem
    user_message: str

@app.post("/finalize-work-order")
async def finalize_work_order(req: FinalWorkOrderRequest):
    """최종 작업요청을 완성합니다."""
    try:
        # 여기서 실제 작업요청 시스템과 연동할 수 있습니다
        return {
            "status": "success",
            "message": "작업요청이 완성되었습니다.",
            "work_order": {
                "itemno": req.selected_recommendation.itemno,
                "work_title": req.work_title,
                "work_details": req.work_details,
                "process": req.selected_recommendation.process,
                "location": req.selected_recommendation.location,
                "equipType": req.selected_recommendation.equipType,
                "statusCode": req.selected_recommendation.statusCode,
                "user_message": req.user_message
            }
        }
    except Exception as e:
        logger.error(f"Error finalizing work order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))