"""
PMark1 AI Assistant - 자연어 입력 파서

이 파일은 사용자의 자연어 입력을 분석하여 구조화된 데이터로 변환합니다.
OpenAI GPT-4o를 활용하여 시나리오를 판단하고, 관련 정보를 추출합니다.

주요 담당자: AI/ML 엔지니어, 백엔드 개발자
수정 시 주의사항:
- OpenAI API 키가 필요합니다 (config.py에서 설정)
- 시나리오 판단 로직은 비즈니스 요구사항에 따라 조정
- 추출 필드는 models.py의 ParsedInput과 일치해야 함
"""

import re
import openai
from typing import Dict, List, Optional, Tuple
from ..config import Config
from ..models import ParsedInput
from ..logic.normalizer import normalizer
import json

class InputParser:
    """
    자연어 입력 파서 클래스
    
    사용처:
    - chat.py: POST /api/v1/chat에서 사용자 입력 분석
    - recommender.py: RecommendationEngine에서 파싱 결과 활용
    
    연계 파일:
    - models.py: ParsedInput 모델 사용
    - config.py: OpenAI API 설정
    - logic/normalizer.py: 추출된 용어 정규화
    
    담당자 수정 가이드:
    - 새로운 시나리오 추가 시 _create_scenario_prompt() 메서드 수정
    - 추출 필드 변경 시 models.py의 ParsedInput도 함께 수정
    - 프롬프트 수정 시 일관성 있는 응답을 위해 temperature 조정
    """
    
    def __init__(self):
        """
        입력 파서 초기화
        
        설정:
        - OpenAI 클라이언트 초기화
        - 모델 설정
        """
        self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # ITEMNO 패턴 (채번 규칙)
        self.itemno_patterns = [
            r'\b[A-Z]{2,4}-\d{5}\b',  # 예: RFCC-00123
            r'\b[A-Z]-\w+\b',         # 예: Y-MV1035
            r'\b\d{5}-[A-Z]{2}-\d+"-[A-Z]\b',  # 예: 44043-CA1-6"-P
            r'\b[A-Z]{2}-\w+-\d{2}\b',  # 예: SW-CV1307-02
        ]
        
        # 우선순위 키워드
        self.priority_keywords = {
            "긴급작업": ["긴급", "긴급작업", "urgent", "emergency"],
            "우선작업": ["우선", "우선작업", "priority", "high"],
            "일반작업": ["일반", "일반작업", "normal", "regular"]
        }
    
    def parse_input(self, user_input: str, conversation_history: list = None) -> ParsedInput:
        """
        사용자 입력을 파싱하여 구조화된 데이터로 변환
        
        Args:
            user_input: 사용자 입력 메시지
            
        Returns:
            ParsedInput: 파싱된 구조화된 데이터
            
        사용처:
        - chat.py: chat_endpoint()에서 사용자 입력 분석
        - recommender.py: RecommendationEngine에서 파싱 결과 활용
        
        연계 파일:
        - models.py: ParsedInput 모델로 반환
        - logic/normalizer.py: _normalize_extracted_terms()에서 용어 정규화
        
        예시:
        - "1PE 압력베젤 고장" → ParsedInput(scenario="S1", location="No.1 PE", equipment_type="Pressure Vessel", status_code="고장")
        - "ITEMNO 12345 작업상세" → ParsedInput(scenario="S2", itemno="12345")
        
        담당자 수정 가이드:
        - 시나리오 판단 로직은 비즈니스 요구사항에 따라 조정
        - 새로운 필드 추출 시 _create_scenario_1_prompt() 수정 필요
        - confidence 점수는 LLM 응답의 신뢰도를 반영
        """
        try:
            # 시나리오 판단
            scenario = self._determine_scenario(user_input)
            
            if scenario == "S1":
                # 시나리오 1: 자연어로 작업 요청
                return self._parse_scenario_1(user_input)
            elif scenario == "S2":
                # 시나리오 2: ITEMNO로 작업 상세 요청
                return self._parse_scenario_2(user_input)
            else:
                # 기본 시나리오
                return self._parse_default_scenario(user_input)
                
        except Exception as e:
            print(f"입력 파싱 오류: {e}")
            # 오류 시 기본값 반환
            return ParsedInput(
                scenario="S1",
                location=None,
                equipment_type=None,
                status_code=None,
                priority="일반작업",
                itemno=None,
                confidence=0.0
            )
    
    def _determine_scenario(self, user_input: str) -> str:
        """
        사용자 입력을 분석하여 시나리오 판단
        
        Args:
            user_input: 사용자 입력 메시지
            
        Returns:
            시나리오 타입 ("S1", "S2", "default")
            
        판단 기준:
        - S1: 자연어로 작업 요청 (위치, 설비, 현상 등 포함)
        - S2: ITEMNO로 작업 상세 요청 (ITEMNO 포함)
        - default: 기타
        
        담당자 수정 가이드:
        - 시나리오 판단 기준은 비즈니스 요구사항에 따라 조정
        - 정규표현식 패턴 추가로 더 정확한 판단 가능
        """
        # ITEMNO 패턴 확인 (시나리오 2)
        if re.search(r'ITEMNO\s*\d+', user_input, re.IGNORECASE) or re.search(r'\b\d{5,}\b', user_input):
            return "S2"
        
        # 자연어 작업 요청 패턴 확인 (시나리오 1)
        keywords = ['고장', '누설', '작동불량', '점검', '정비', '압력', '온도', '밸브', '펌프', '탱크']
        if any(keyword in user_input for keyword in keywords):
            return "S1"
        
        return "default"
    
    def _parse_scenario_1(self, user_input: str, conversation_history: list = None) -> ParsedInput:
        """
        시나리오 1 파싱: 자연어로 작업 요청
        
        Args:
            user_input: 사용자 입력 메시지
            
        Returns:
            ParsedInput: 파싱된 구조화된 데이터
            
        추출 정보:
        - location: 위치/공정
        - equipment_type: 설비유형
        - status_code: 현상코드
        - priority: 우선순위
        
        담당자 수정 가이드:
        - 추출 필드 변경 시 프롬프트 수정 필요
        - 대화 히스토리 활용 로직 개선 가능
        - 정규화 로직은 _normalize_extracted_terms()에서 처리
        """
        try:
            # LLM 프롬프트 생성
            prompt = self._create_scenario_1_prompt(user_input, conversation_history)
            
            # LLM 호출 (타임아웃 설정)
            import time
            start_time = time.time()
            
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 설비관리 시스템의 입력 분석 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 일관성을 위해 낮은 temperature
                max_tokens=500,
                timeout=15  # 15초 타임아웃
            )
            
            # 타임아웃 체크
            if time.time() - start_time > 15:
                print("LLM 호출 타임아웃")
                return self._create_default_parsed_input()
            
            result_text = response.choices[0].message.content.strip()
            
            # 응답 파싱
            parsed_data = self._parse_llm_response(result_text)
            
            # 추출된 용어 정규화
            normalized_data = self._normalize_extracted_terms(parsed_data)
            
            return ParsedInput(
                scenario="S1",
                location=normalized_data.get('location'),
                equipment_type=normalized_data.get('equipment_type'),
                status_code=normalized_data.get('status_code'),
                priority=normalized_data.get('priority', '일반작업'),
                itemno=None,
                confidence=parsed_data.get('confidence', 0.0)
            )
            
        except Exception as e:
            print(f"시나리오 1 파싱 오류: {e}")
            return self._create_default_parsed_input()
    
    def _parse_scenario_2(self, user_input: str) -> ParsedInput:
        """
        시나리오 2 파싱: ITEMNO로 작업 상세 요청
        
        Args:
            user_input: 사용자 입력 메시지
            
        Returns:
            ParsedInput: 파싱된 구조화된 데이터
            
        추출 정보:
        - itemno: ITEMNO
        
        담당자 수정 가이드:
        - ITEMNO 추출 패턴 개선 가능
        - 추가 정보 추출 로직 구현 가능
        """
        try:
            # ITEMNO 추출
            itemno_match = re.search(r'ITEMNO\s*(\d+)', user_input, re.IGNORECASE)
            if not itemno_match:
                itemno_match = re.search(r'\b(\d{5,})\b', user_input)
            
            itemno = itemno_match.group(1) if itemno_match else None
            
            return ParsedInput(
                scenario="S2",
                location=None,
                equipment_type=None,
                status_code=None,
                priority="일반작업",
                itemno=itemno,
                confidence=0.9 if itemno else 0.0
            )
            
        except Exception as e:
            print(f"시나리오 2 파싱 오류: {e}")
            return self._create_default_parsed_input()
    
    def _parse_default_scenario(self, user_input: str) -> ParsedInput:
        """
        기본 시나리오 파싱
        
        Args:
            user_input: 사용자 입력 메시지
            
        Returns:
            ParsedInput: 기본 파싱 결과
            
        담당자 수정 가이드:
        - 기본 시나리오 처리 로직 개선 가능
        - 사용자 안내 메시지 생성 로직 추가 가능
        """
        return ParsedInput(
            scenario="S1",
            location=None,
            equipment_type=None,
            status_code=None,
            priority="일반작업",
            itemno=None,
            confidence=0.0
        )
    
    def _create_scenario_1_prompt(self, user_input: str, conversation_history: list = None) -> str:
        """
        시나리오 1용 LLM 프롬프트 생성
        
        Args:
            user_input: 사용자 입력 메시지
            
        Returns:
            LLM 프롬프트 문자열
            
        담당자 수정 가이드:
        - 추출 필드 변경 시 이 프롬프트 수정 필요
        - 예시는 실제 사용 사례를 반영하여 업데이트
        - 대화 히스토리 활용 로직 개선 가능
        """
        
        # 대화 히스토리 컨텍스트 생성
        context = ""
        if conversation_history and len(conversation_history) > 0:
            context = "대화 히스토리:\n"
            for msg in conversation_history[-3:]:  # 최근 3개 메시지만 사용
                context += f"{msg['role']}: {msg['content']}\n"
            context += "\n"
        
        return f"""
{context}다음 사용자 입력에서 설비관리 작업 요청 관련 정보를 추출해주세요.

**사용자 입력**: {user_input}

**추출해야 할 정보**:
1. location: 위치/공정 (예: No.1 PE, No.2 PE, 석유제품배합/저장, 합성수지 포장, RFCC, 1창고 #7Line, 2창고 #8Line, 공통 시설)
2. equipment_type: 설비유형 (예: Pressure Vessel, Motor Operated Valve, Conveyor, Pump, Heat Exchanger, Valve, Control Valve, Tank, Storage Tank, Drum, Filter, Reactor, Compressor, Fan, Blower)
3. status_code: 현상코드 (예: 고장, 누설, 작동불량, 소음, 진동, 온도상승, 압력상승, 주기적 점검/정비, 고장.결함.수명소진)
4. priority: 우선순위 (긴급작업, 일반작업, 계획작업 중 선택)

**응답 형식**:
```json
{{
    "location": "추출된 위치/공정",
    "equipment_type": "추출된 설비유형",
    "status_code": "추출된 현상코드",
    "priority": "우선순위",
    "confidence": 0.95,
    "reasoning": "추출 이유"
}}
```

**예시**:
- 입력: "1PE 압력베젤 고장" → 출력: {{"location": "No.1 PE", "equipment_type": "Pressure Vessel", "status_code": "고장", "priority": "긴급작업", "confidence": 0.95, "reasoning": "고장은 긴급 상황"}}
- 입력: "모터밸브 누설 점검" → 출력: {{"location": null, "equipment_type": "Motor Operated Valve", "status_code": "누설", "priority": "일반작업", "confidence": 0.9, "reasoning": "누설은 일반적인 점검 대상"}}

**주의사항**:
- 추출할 수 없는 정보는 null로 설정
- confidence는 0.0~1.0 사이의 값으로 설정
- 대화 히스토리를 참고하여 맥락을 파악
"""
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """
        LLM 응답을 파싱하여 구조화된 데이터 추출
        
        Args:
            response_text: LLM 응답 텍스트
            
        Returns:
            파싱된 데이터 딕셔너리
            
        담당자 수정 가이드:
        - JSON 파싱 실패 시 폴백 로직으로 응답에서 정보 추출
        - 응답 형식이 변경되면 이 메서드 수정 필요
        """
        try:
            # JSON 부분 추출
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                # JSON 블록이 없는 경우 전체 텍스트를 JSON으로 파싱 시도
                data = json.loads(response_text)
            
            return data
            
        except Exception as e:
            print(f"LLM 응답 파싱 오류: {e}")
            # 폴백: 간단한 추출 로직
            return {
                'location': None,
                'equipment_type': None,
                'status_code': None,
                'priority': '일반작업',
                'confidence': 0.5,
                'reasoning': '파싱 실패로 기본값 사용'
            }
    
    def _normalize_extracted_terms(self, parsed_data: Dict) -> Dict:
        """
        추출된 용어를 LLM 정규화 엔진으로 정규화
        
        Args:
            parsed_data: 파싱된 데이터
            
        Returns:
            정규화된 데이터
            
        사용처:
        - _parse_scenario_1()에서 추출된 용어 정규화
        - database.py에서 검색 시 정확한 매칭을 위해 사용
        
        연계 파일:
        - logic/normalizer.py: LLM 정규화 엔진 사용
        
        담당자 수정 가이드:
        - 새로운 카테고리 추가 시 정규화 로직 추가
        - 신뢰도 임계값 조정으로 정규화 품질 제어 가능
        """
        normalized_data = parsed_data.copy()
        
        # 설비유형 정규화
        if parsed_data.get('equipment_type'):
            normalized_term, confidence = normalizer.normalize_term(
                parsed_data['equipment_type'], 'equipment'
            )
            if confidence > 0.3:  # 신뢰도 임계값
                normalized_data['equipment_type'] = normalized_term
        
        # 위치 정규화
        if parsed_data.get('location'):
            normalized_term, confidence = normalizer.normalize_term(
                parsed_data['location'], 'location'
            )
            if confidence > 0.3:
                normalized_data['location'] = normalized_term
        
        # 현상코드 정규화
        if parsed_data.get('status_code'):
            normalized_term, confidence = normalizer.normalize_term(
                parsed_data['status_code'], 'status'
            )
            if confidence > 0.3:
                normalized_data['status_code'] = normalized_term
        
        return normalized_data
    
    def _create_default_parsed_input(self) -> ParsedInput:
        """
        기본 ParsedInput 생성 (오류 시 사용)
        
        Returns:
            기본 ParsedInput 객체
            
        담당자 수정 가이드:
        - 기본값은 비즈니스 로직에 맞게 조정 가능
        - 오류 처리 로직 개선 가능
        """
        return ParsedInput(
            scenario="S1",
            location=None,
            equipment_type=None,
            status_code=None,
            priority="일반작업",
            itemno=None,
            confidence=0.0
        )

# 전역 입력 파서 인스턴스
# 다른 모듈에서 import하여 사용
input_parser = InputParser() 