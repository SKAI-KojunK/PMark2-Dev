"""
PMark1 AI Assistant - 채팅 API

이 파일은 사용자와의 대화를 처리하는 메인 API 엔드포인트입니다.
사용자 입력을 파싱하고, 추천 엔진을 통해 유사한 작업을 찾아 응답을 생성합니다.

주요 담당자: 백엔드 개발자, API 개발자
수정 시 주의사항:
- API 응답 형식은 frontend와 호환되어야 함
- 에러 처리는 사용자 친화적으로 구현
- 로깅을 통한 디버깅 지원 필요
"""

from fastapi import APIRouter, HTTPException
from typing import List
from ..models import ChatRequest, ChatResponse, ParsedInput, Recommendation
from ..agents.parser import InputParser
from ..logic.recommender import RecommendationEngine
from ..config import Config
import logging

# API 라우터 설정
router = APIRouter()

# 로깅 설정
logger = logging.getLogger(__name__)

# 전역 인스턴스
parser = InputParser()
recommender = RecommendationEngine()

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    채팅 메인 엔드포인트
    
    사용자 입력을 받아 파싱하고 추천 목록을 생성하여 응답합니다.
    
    Args:
        request: ChatRequest - 사용자 메시지와 대화 히스토리
        
    Returns:
        ChatResponse - 봇 응답, 추천 목록, 파싱 결과
        
    사용처:
    - frontend: 채팅 인터페이스에서 사용자 입력 처리
    - 모바일 앱: 동일한 API 사용 가능
        
    연계 파일:
    - models.py: ChatRequest, ChatResponse, ParsedInput 모델 사용
    - agents/parser.py: input_parser.parse_input() 호출
    - logic/recommender.py: recommendation_engine.get_recommendations() 호출
    
    API 흐름:
    1. 사용자 입력 수신
    2. 입력 파싱 (시나리오 판단, 정보 추출)
    3. 추천 엔진 호출 (유사 작업 검색)
    4. 응답 메시지 생성
    5. 결과 반환
    
    담당자 수정 가이드:
    - 새로운 시나리오 추가 시 _handle_scenario() 메서드 수정
    - 응답 메시지 형식 변경 시 _create_response_message() 수정
    - 에러 처리 로직 개선 가능
    - 성능 최적화를 위해 캐싱 추가 가능
    """
    try:
        logger.info(f"채팅 요청 수신: {request.message[:50]}...")
        
        # 1단계: 사용자 입력 파싱
        parsed_input = parser.parse_input(request.message)
        logger.info(f"입력 파싱 완료: 시나리오={parsed_input.scenario}, 신뢰도={parsed_input.confidence}")
        
        # 2단계: 시나리오별 처리
        response = await _handle_scenario(parsed_input, request.message, request.conversation_history)
        
        logger.info(f"채팅 응답 생성 완료: 추천 수={len(response.recommendations)}")
        return response
        
    except Exception as e:
        logger.error(f"채팅 처리 오류: {e}")
        # 사용자 친화적인 에러 응답
        return ChatResponse(
            message="죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다. 다시 시도해주세요.",
            recommendations=[],
            parsed_input=None,
            needs_additional_input=False,
            missing_fields=[]
        )

async def _handle_scenario(parsed_input: ParsedInput, user_message: str, conversation_history: list) -> ChatResponse:
    """
    시나리오별 처리 로직
    
    Args:
        parsed_input: 파싱된 입력 데이터
        user_message: 원본 사용자 메시지
        conversation_history: 대화 히스토리
        
    Returns:
        ChatResponse: 시나리오별 응답
        
    시나리오별 처리:
    - S1: 자연어 작업 요청 → 추천 목록 생성
    - S2: ITEMNO 작업 상세 요청 → 특정 작업 정보 제공
    - default: 기본 안내 메시지
    
    담당자 수정 가이드:
    - 새로운 시나리오 추가 시 이 메서드 수정
    - 각 시나리오별 처리 로직 개선 가능
    - 대화 히스토리 활용 로직 추가 가능
    """
    
    if parsed_input.scenario == "S1":
        return await _handle_scenario_1(parsed_input, user_message, conversation_history)
    elif parsed_input.scenario == "S2":
        return await _handle_scenario_2(parsed_input, user_message, conversation_history)
    else:
        return await _handle_default_scenario(parsed_input, user_message, conversation_history)

async def _handle_scenario_1(parsed_input: ParsedInput, user_message: str, conversation_history: list) -> ChatResponse:
    """
    시나리오 1 처리: 자연어 작업 요청
    
    Args:
        parsed_input: 파싱된 입력 데이터
        user_message: 원본 사용자 메시지
        conversation_history: 대화 히스토리
        
    Returns:
        ChatResponse: 추천 목록이 포함된 응답
        
    처리 로직:
    1. 누락된 필드 확인
    2. 추천 엔진 호출
    3. 응답 메시지 생성
    
    담당자 수정 가이드:
    - 추천 수 조정 가능 (현재 5개)
    - 누락 필드 처리 로직 개선 가능
    - 응답 메시지 개인화 가능
    """
    
    # 누락된 필드 확인
    missing_fields = _check_missing_fields(parsed_input)
    
    # 추천 엔진 호출
    recommendations = recommender.get_recommendations(parsed_input)
    
    # 응답 메시지 생성
    message = _create_response_message(parsed_input, recommendations, missing_fields)
    
    return ChatResponse(
        message=message,
        recommendations=recommendations,
        parsed_input=parsed_input,
        needs_additional_input=len(missing_fields) > 0,
        missing_fields=missing_fields
    )

async def _handle_scenario_2(parsed_input: ParsedInput, user_message: str, conversation_history: list) -> ChatResponse:
    """
    시나리오 2 처리: ITEMNO 작업 상세 요청
    
    Args:
        parsed_input: 파싱된 입력 데이터
        user_message: 원본 사용자 메시지
        conversation_history: 대화 히스토리
        
    Returns:
        ChatResponse: 특정 작업 정보가 포함된 응답
        
    처리 로직:
    1. ITEMNO로 특정 작업 조회
    2. 작업 상세 정보 제공
    3. 관련 추천 항목 제공
    
    담당자 수정 가이드:
    - ITEMNO 검증 로직 추가 가능
    - 관련 작업 추천 로직 개선 가능
    - 작업 이력 조회 기능 추가 가능
    """
    
    if not parsed_input.itemno:
        return ChatResponse(
            message="ITEMNO를 찾을 수 없습니다. 올바른 ITEMNO를 입력해주세요.",
            recommendations=[],
            parsed_input=parsed_input,
            needs_additional_input=True,
            missing_fields=["itemno"]
        )
    
    # ITEMNO로 특정 작업 조회
    specific_recommendation = recommender.get_recommendation_by_itemno(parsed_input.itemno)
    
    if specific_recommendation:
        # 관련 추천 항목도 함께 제공
        related_recommendations = recommender.get_recommendations(parsed_input, limit=3)
        
        message = f"ITEMNO {parsed_input.itemno}에 대한 작업 정보입니다:\n\n"
        message += f"• 공정: {specific_recommendation.process}\n"
        message += f"• 위치: {specific_recommendation.location}\n"
        message += f"• 설비유형: {specific_recommendation.equipType}\n"
        message += f"• 현상코드: {specific_recommendation.statusCode}\n"
        message += f"• 우선순위: {specific_recommendation.priority}\n\n"
        
        if specific_recommendation.work_title:
            message += f"작업명: {specific_recommendation.work_title}\n"
        if specific_recommendation.work_details:
            message += f"작업상세: {specific_recommendation.work_details}\n"
        
        return ChatResponse(
            message=message,
            recommendations=[specific_recommendation] + related_recommendations,
            parsed_input=parsed_input,
            needs_additional_input=False,
            missing_fields=[]
        )
    else:
        return ChatResponse(
            message=f"ITEMNO {parsed_input.itemno}에 해당하는 작업을 찾을 수 없습니다.",
            recommendations=[],
            parsed_input=parsed_input,
            needs_additional_input=True,
            missing_fields=["itemno"]
        )

async def _handle_default_scenario(parsed_input: ParsedInput, user_message: str, conversation_history: list) -> ChatResponse:
    """
    기본 시나리오 처리: 인식되지 않는 입력
    
    Args:
        parsed_input: 파싱된 입력 데이터
        user_message: 원본 사용자 메시지
        conversation_history: 대화 히스토리
        
    Returns:
        ChatResponse: 안내 메시지가 포함된 응답
        
    담당자 수정 가이드:
    - 사용자 안내 메시지 개선 가능
    - 예시 제공 로직 추가 가능
    - 대화 히스토리 기반 컨텍스트 파악 가능
    """
    
    message = "안녕하세요! 설비관리 작업요청을 도와드리겠습니다.\n\n"
    message += "다음과 같은 형식으로 입력해주세요:\n"
    message += "• \"1PE 압력베젤 고장\" - 자연어로 작업 요청\n"
    message += "• \"ITEMNO 12345\" - 특정 작업 상세 조회\n\n"
    message += "**위치 정보를 포함하면 더 정확한 추천을 받을 수 있습니다.**\n"
    message += "예시: \"No.1 PE 압력베젤 고장\", \"석유제품배합/저장 탱크 누설\"\n\n"
    message += "어떤 작업을 도와드릴까요?"
    
    return ChatResponse(
        message=message,
        recommendations=[],
        parsed_input=parsed_input,
        needs_additional_input=True,
        missing_fields=[]
    )

def _check_missing_fields(parsed_input: ParsedInput) -> list:
    """
    누락된 필드 확인
    
    Args:
        parsed_input: 파싱된 입력 데이터
        
    Returns:
        누락된 필드 리스트
        
    필수 필드:
    - location: 위치/공정
    - equipment_type: 설비유형
    - status_code: 현상코드
    
    담당자 수정 가이드:
    - 필수 필드 기준 조정 가능
    - 필드별 중요도 가중치 적용 가능
    - 신뢰도 기반 필드 검증 가능
    """
    missing_fields = []
    
    if not parsed_input.location:
        missing_fields.append("location")
    if not parsed_input.equipment_type:
        missing_fields.append("equipment_type")
    if not parsed_input.status_code:
        missing_fields.append("status_code")
    
    return missing_fields

def _create_response_message(parsed_input: ParsedInput, recommendations: list, missing_fields: list) -> str:
    """
    응답 메시지 생성
    
    Args:
        parsed_input: 파싱된 입력 데이터
        recommendations: 추천 목록
        missing_fields: 누락된 필드 리스트
        
    Returns:
        사용자에게 보여질 응답 메시지
        
    메시지 구성:
    1. 파싱 결과 요약
    2. 누락 필드 안내 (있는 경우)
    3. 추천 결과 안내
    
    담당자 수정 가이드:
    - 메시지 형식 개선 가능
    - 개인화된 메시지 생성 가능
    - 다국어 지원 추가 가능
    """
    
    message = "입력하신 내용을 분석했습니다:\n\n"
    
    # 파싱 결과 요약
    if parsed_input.location:
        message += f"• 위치/공정: {parsed_input.location}\n"
    if parsed_input.equipment_type:
        message += f"• 설비유형: {parsed_input.equipment_type}\n"
    if parsed_input.status_code:
        message += f"• 현상코드: {parsed_input.status_code}\n"
    if parsed_input.priority:
        message += f"• 우선순위: {parsed_input.priority}\n"
    
    message += f"\n분석 신뢰도: {parsed_input.confidence:.1%}\n\n"
    
    # 누락 필드 안내
    if missing_fields:
        message += "다음 정보가 누락되었습니다:\n"
        for field in missing_fields:
            field_names = {
                "location": "위치/공정 (가장 중요)",
                "equipment_type": "설비유형",
                "status_code": "현상코드"
            }
            message += f"• {field_names.get(field, field)}\n"
        message += "\n**위치 정보를 포함하면 더 정확한 추천을 받을 수 있습니다.**\n"
        message += "예시: \"No.1 PE 압력베젤 고장\", \"석유제품배합/저장 탱크 누설\"\n\n"
    
    # 추천 결과 안내
    if recommendations:
        message += f"유사한 작업 {len(recommendations)}건을 찾았습니다:\n"
        for i, rec in enumerate(recommendations[:3], 1):  # 상위 3개만 표시
            message += f"{i}. {rec.equipType} ({rec.location}) - 유사도 {rec.score:.1%}\n"
        
        if len(recommendations) > 3:
            message += f"... 외 {len(recommendations) - 3}건\n"
        
        message += "\n원하는 작업을 선택하시면 상세 정보를 제공해드립니다."
    else:
        message += "유사한 작업을 찾을 수 없습니다. 다른 키워드로 다시 시도해주세요."
    
    return message 