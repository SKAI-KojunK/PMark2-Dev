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
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
from ..config import Config
from ..models import ParsedInput
from ..logic.normalizer import normalizer
import json
from difflib import SequenceMatcher

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
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # ITEMNO 패턴 (채번 규칙)
        self.itemno_patterns = [
            r'\b[A-Z]{2,4}-\d{5}\b',  # 예: RFCC-00123
            r'\b[A-Z]-\w+\b',         # 예: Y-MV1035
            r'\b\d{5}-[A-Z]{2}-\d+-[A-Z]\b',  # 예: 44043-CA1-6-P
            r'\b\d{4,}-[A-Z]{2}-\d+-[A-Z]\b',  # 예: 44043-CA1-6-P (더 유연한 패턴)
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
                priority=None,
                itemno=None,
                confidence=0.0
            )
    
    def parse_input_with_context(self, user_input: str, conversation_history: list = None, session_id: str = None) -> ParsedInput:
        """
        세션 컨텍스트를 포함한 입력 파싱 (PMark2.5 고급 기능)
        
        Args:
            user_input: 사용자 입력 메시지
            conversation_history: 대화 히스토리
            session_id: 세션 ID
            
        Returns:
            ParsedInput: 컨텍스트를 반영한 파싱 결과
        """
        try:
            # 세션 컨텍스트 로드
            from ..session_manager import session_manager
            session_state = session_manager.get_session(session_id) if session_id else None
            
            if session_state and session_state.accumulated_clues.has_any_clue():
                # 기존 누적 단서가 있을 때만 컨텍스트 파싱 사용
                return self._parse_scenario_1_with_context(user_input, conversation_history, session_state.accumulated_clues)
            else:
                # 첫 번째 입력이거나 누적 단서가 없으면 일반 파싱 사용
                print(f"누적 단서가 없어 일반 파싱 사용")
                return self.parse_input(user_input, conversation_history)
                
        except Exception as e:
            print(f"컨텍스트 파싱 오류: {e}")
            # 기본 파싱으로 fallback
            return self.parse_input(user_input, conversation_history)

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
        # ITEMNO 패턴 확인 (시나리오 2) - 더 정확한 패턴 매칭
        itemno_patterns = [
            r'ITEMNO\s*\d+',  # ITEMNO 12345
            r'\b\d{4,}-\w+',  # 44043-CA1-6-P
            r'\b[A-Z]-\w+\d+',  # Y-MV1035
            r'\b[A-Z]{2,4}-\w+',  # PE-SE1304B
            r'\b[A-Z]{2,4}\d+',  # SW-CV1307-02
            r'\b\d{5,}',  # 5자리 이상 숫자
            r'"[^"]*"',  # 따옴표로 둘러싸인 코드
        ]
        
        for pattern in itemno_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return "S2"
        
        # 자연어 작업 요청 패턴 확인 (시나리오 1)
        # 더 포괄적인 키워드 목록
        keywords = [
            '고장', '누설', '작동불량', '점검', '정비', '압력', '온도', '밸브', '펌프', '탱크',
            '베젤', '베셀', 'vessel', 'pressure', 'valve', 'motor', 'pump', 'tank',
            '컨베이어', 'conveyor', '열교환', 'heat', 'exchanger', '필터', 'filter',
            '압축', 'compressor', '팬', 'fan', '블로워', 'blower', '드럼', 'drum',
            '반응', 'reactor', '분석', 'analyzer', '누출', 'leak', 'bolting',
            '소음', '진동', '온도상승', '압력상승', '결함', '수명소진'
        ]
        
        if any(keyword.lower() in user_input.lower() for keyword in keywords):
            return "S1"
        
        # 기본값: 시나리오 1 (자연어 입력으로 가정)
        return "S1"
    
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
            
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 설비관리 시스템의 입력 분석 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 일관성을 위해 낮은 temperature
                max_tokens=500
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
                priority=normalized_data.get('priority'),  # None일 수 있음 - 추후 DB에서 가져오거나 기본값 설정
                itemno=None,
                confidence=parsed_data.get('confidence', 0.0)
            )
            
        except Exception as e:
            print(f"시나리오 1 파싱 오류: {e}")
            return self._create_default_parsed_input()

    def _parse_scenario_1_with_context(self, user_input: str, conversation_history: list, accumulated_clues) -> ParsedInput:
        """
        누적된 단서와 함께 시나리오 1 파싱
        
        Args:
            user_input: 사용자 입력
            conversation_history: 대화 히스토리
            accumulated_clues: 누적된 단서들
            
        Returns:
            ParsedInput: 컨텍스트를 반영한 파싱 결과
        """
        try:
            print(f"컨텍스트 파싱 시작: {user_input[:50]}...")
            print(f"누적 단서 - 위치: {accumulated_clues.location}, 설비: {accumulated_clues.equipment_type}, 현상: {accumulated_clues.status_code}")
            
            # 컨텍스트 포함 프롬프트 생성
            prompt = self._create_scenario_1_context_prompt(user_input, conversation_history, accumulated_clues)
            
            # LLM 호출
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 설비관리 시스템의 멀티턴 대화 분석 전문가입니다. 이전 대화 컨텍스트를 고려하여 입력을 분석합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"LLM 응답: {result_text}")
            
            # 응답 파싱
            parsed_data = self._parse_llm_response(result_text)
            
            # 추출된 용어 정규화
            normalized_data = self._normalize_extracted_terms(parsed_data)
            
            # ParsedInput 객체 생성
            parsed_input = ParsedInput(
                scenario="S1",
                location=normalized_data.get("location"),
                equipment_type=normalized_data.get("equipment_type"),
                status_code=normalized_data.get("status_code"),
                priority=normalized_data.get("priority"),  # None일 수 있음 - 추후 DB에서 가져오거나 기본값 설정
                confidence=normalized_data.get("confidence", 0.8)
            )
            
            print(f"컨텍스트 파싱 완료: {parsed_input}")
            return parsed_input
            
        except Exception as e:
            print(f"컨텍스트 파싱 오류: {e}")
            import traceback
            traceback.print_exc()
            # 기본 파싱으로 fallback
            return self._parse_scenario_1(user_input, conversation_history)

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
   - 사용자가 "위치" 또는 "공정"으로 언급한 내용을 우선적으로 추출
   - 위치 정보가 없으면 공정명을 위치로 사용
2. equipment_type: 설비유형 (예: Pressure Vessel, Motor Operated Valve, Conveyor, Pump, Heat Exchanger, Valve, Control Valve, Tank, Storage Tank, Drum, Filter, Reactor, Compressor, Fan, Blower)
3. status_code: 현상코드 (예: 고장, 누설, 작동불량, 소음, 진동, 온도상승, 압력상승, 주기적 점검/정비, 고장.결함.수명소진)
4. priority: 우선순위 (선택사항 - 사용자가 명시적으로 언급한 경우에만 추출)
   - 긴급작업: "긴급", "긴급작업", "최우선", "urgent", "emergency"
   - 우선작업: "우선", "우선작업", "priority", "high priority"
   - 일반작업: "일반", "일반작업", "normal", "regular"
   - 주기작업: "주기", "주기작업", "정기", "PM", "TA"

**추출 규칙**:
1. 문장의 어느 위치에 있든 해당 카테고리의 내용을 찾아 추출
2. 한 단어가 아닌 여러 단어로 구성된 표현도 해당 범주로 인식
3. 유사한 표현이나 동의어도 적절한 카테고리로 매핑
4. 맥락을 고려하여 가장 적절한 카테고리 선택
5. **위치 정보가 가장 중요하므로, 위치 관련 키워드를 우선적으로 찾아 추출**
6. **우선순위는 사용자가 명시적으로 언급한 경우에만 추출하며, 필수 항목이 아님**
7. **한국어-영어 혼용 표현도 정확히 인식** (예: "Pressure Vessel/ Drum" → "Pressure Vessel")
8. **오타, 띄어쓰기, 특수문자 무시하고 의미 파악**

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
- 입력: "No.1 PE의 Pressure Vessel/ Drum에 고장 발생" → 출력: {{"location": "No.1 PE", "equipment_type": "Pressure Vessel", "status_code": "고장", "priority": null, "confidence": 0.95, "reasoning": "위치와 설비유형, 현상코드 모두 추출"}}
- 입력: "석유제품배합/저장의 Motor Operated Valve, 작동불량. 긴급작업 요망" → 출력: {{"location": "석유제품배합/저장", "equipment_type": "Motor Operated Valve", "status_code": "작동불량", "priority": "긴급작업", "confidence": 0.95, "reasoning": "긴급작업 명시적 언급"}}
- 입력: "합성수지 포장, Miscellaneous Equipment/ Conveyor, 고장, 우선작업 요청" → 출력: {{"location": "합성수지 포장", "equipment_type": "Conveyor", "status_code": "고장", "priority": "우선작업", "confidence": 0.9, "reasoning": "우선작업 명시적 언급"}}
- 입력: "44043-CA1-6"-P, Leak 볼팅 작업" → 출력: {{"location": null, "equipment_type": null, "status_code": "누설", "priority": null, "confidence": 0.8, "reasoning": "ITEMNO 패턴이므로 시나리오 2로 처리"}}

**주의사항**:
- 추출할 수 없는 정보는 null로 설정
- **우선순위는 사용자가 명시적으로 언급한 경우에만 추출하며, 없으면 null로 설정**
- confidence는 0.0~1.0 사이의 값으로 설정
- 대화 히스토리를 참고하여 맥락을 파악
- 여러 단어로 구성된 표현도 정확히 인식
- **한국어-영어 혼용 표현도 정확히 인식하고 정규화**
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
                'priority': None,
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
        
        # 우선순위 정규화
        if parsed_data.get('priority'):
            normalized_term, confidence = normalizer.normalize_term(
                parsed_data['priority'], 'priority'
            )
            if confidence > 0.3:
                normalized_data['priority'] = normalized_term
        
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
            priority=None,
            itemno=None,
            confidence=0.0
        )

    def _create_scenario_1_context_prompt(self, user_input: str, conversation_history: list, accumulated_clues) -> str:
        """
        컨텍스트 포함 시나리오 1 프롬프트 생성
        
        Args:
            user_input: 사용자 입력
            conversation_history: 대화 히스토리
            accumulated_clues: 누적된 단서들
            
        Returns:
            LLM 프롬프트
        """
        prompt = f"""
# 멀티턴 대화 기반 설비관리 입력 분석

## 이전 대화에서 수집된 정보:
- 위치/공정: {accumulated_clues.location or "❌ 미확인"}
- 설비유형: {accumulated_clues.equipment_type or "❌ 미확인"}
- 현상코드: {accumulated_clues.status_code or "❌ 미확인"}
- 우선순위: {accumulated_clues.priority or "⚪ 미지정 (선택사항)"}

## 현재 사용자 입력:
"{user_input}"

## 분석 지시사항:
1. 현재 입력에서 새로운 정보를 추출하세요
2. 이전 정보가 없는 경우에만 새로운 정보를 추출하세요
3. 이전 정보를 수정하려는 의도가 명확한 경우에만 기존 정보를 덮어쓰세요
4. 위치 정보를 최우선으로 추출하세요
5. **설비유형 관련 키워드가 있으면 반드시 추출하세요**
6. **입력 순서와 관계없이 모든 관련 정보를 찾아 추출하세요**

## 추출할 정보:
- location: 위치/공정명 (예: No.1 PE, No.2 PP, 석유제품배합/저장)
- equipment_type: 설비유형 (예: 압력베젤, Pressure Vessel, 펌프, Pump, 열교환기, Heat Exchanger, 탱크, Tank)
- status_code: 현상코드 (예: 고장, 누출, 소음, 진동)
- priority: 우선순위 (선택사항 - 사용자가 명시적으로 언급한 경우에만 추출)
- confidence: 분석 신뢰도 (0.0~1.0)

## 설비유형 키워드 매핑:
- "압력베젤", "베젤", "베셀", "vessel", "pressure vessel" → "Pressure Vessel"
- "펌프", "pump" → "Pump"
- "열교환", "열교환기", "heat exchanger" → "Heat Exchanger"
- "탱크", "tank", "저장탱크" → "Storage Tank"
- "밸브", "valve", "모터밸브" → "Motor Operated Valve"
- "컨베이어", "conveyor" → "Conveyor"
- "필터", "filter" → "Filter"
- "반응기", "reactor" → "Reactor"
- "압축기", "compressor" → "Compressor"
- "팬", "fan" → "Fan"
- "블로워", "blower" → "Blower"

## 응답 형식:
location: [추출된 위치 또는 null]
equipment_type: [추출된 설비유형 또는 null]
status_code: [추출된 현상코드 또는 null]
priority: [추출된 우선순위 또는 null]
confidence: [신뢰도 점수]

## 예시:
사용자 입력: "No.1 PE"
→ location: No.1 PE
→ equipment_type: null
→ status_code: null
→ priority: null
→ confidence: 0.9

사용자 입력: "압력베젤"
→ location: null
→ equipment_type: Pressure Vessel
→ status_code: null
→ priority: null
→ confidence: 0.8

사용자 입력: "고장났어요"
→ location: null
→ equipment_type: null
→ status_code: 고장
→ priority: null
→ confidence: 0.7

사용자 입력: "펌프"
→ location: null
→ equipment_type: Pump
→ status_code: null
→ priority: null
→ confidence: 0.8

사용자 입력: "고장난 펌프" (순서 무관)
→ location: null
→ equipment_type: Pump
→ status_code: 고장
→ priority: null
→ confidence: 0.9
"""
        return prompt

    def _parse_scenario_2(self, user_input: str) -> ParsedInput:
        """
        시나리오 2 파싱: ITEMNO 직접 입력 + 현상 설명 (유사도 기반 매칭)
        
        Args:
            user_input: 사용자 입력 메시지
            
        Returns:
            ParsedInput: 파싱된 구조화된 데이터
            
        추출 정보:
        - itemno: 작업대상 (설비 고유번호) - 유사도 기반 매칭
        - status_code: 현상코드
        - priority: 우선순위 (선택사항)
        """
        try:
            # 1. 먼저 정확한 패턴 매칭 시도
            itemno = None
            for pattern in self.itemno_patterns:
                match = re.search(pattern, user_input)
                if match:
                    itemno = match.group(0)
                    break
            
            # 2. 정확한 매칭이 없으면 유사도 기반 매칭 시도
            if not itemno:
                itemno = self._find_similar_itemno(user_input)
            
            # 현상코드 추출 (간단한 키워드 매칭)
            status_keywords = ['고장', '누설', '작동불량', '소음', '진동', '온도상승', '압력상승', '점검', '정비', '결함', '수명소진', 'leak', 'bolting']
            status_code = None
            for keyword in status_keywords:
                if keyword.lower() in user_input.lower():
                    status_code = keyword
                    break
            
            # 우선순위 추출 (선택사항)
            priority = None
            for priority_type, keywords in self.priority_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in user_input.lower():
                        priority = priority_type
                        break
                if priority:
                    break
            
            # confidence 계산 (정확한 매칭 vs 유사도 매칭)
            confidence = 0.8 if itemno and self._is_exact_match(user_input, itemno) else 0.6 if itemno else 0.5
            
            return ParsedInput(
                scenario="S2",
                location=None,
                equipment_type=None,
                status_code=status_code,
                priority=priority,
                itemno=itemno,
                confidence=confidence
            )
            
        except Exception as e:
            print(f"시나리오 2 파싱 오류: {e}")
            return self._create_default_parsed_input()

    def _find_similar_itemno(self, user_input: str) -> Optional[str]:
        """
        사용자 입력에서 ITEMNO와 유사한 패턴을 찾아 DB의 작업대상과 매칭
        
        Args:
            user_input: 사용자 입력 메시지
            
        Returns:
            매칭된 ITEMNO 또는 None
        """
        try:
            # DB에서 모든 작업대상 가져오기
            from ..database import DatabaseManager
            db = DatabaseManager()
            
            # 작업대상 컬럼에서 모든 고유값 가져오기
            query = "SELECT DISTINCT itemno FROM notification_history WHERE itemno IS NOT NULL AND itemno != ''"
            cursor = db.conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            
            if not results:
                return None
            
            # 사용자 입력에서 ITEMNO 패턴 추출 시도
            potential_itemno = self._extract_potential_itemno(user_input)
            
            if not potential_itemno:
                return None
            
            # 유사도 계산 및 매칭
            best_match = None
            best_score = 0.0
            min_similarity_threshold = 0.6  # 최소 유사도 임계값
            
            for row in results:
                db_itemno = row[0]
                if db_itemno:
                    # 유사도 계산
                    similarity = self._calculate_similarity(potential_itemno, db_itemno)
                    
                    if similarity > best_score and similarity >= min_similarity_threshold:
                        best_score = similarity
                        best_match = db_itemno
            
            return best_match
            
        except Exception as e:
            print(f"유사도 매칭 오류: {e}")
            return None
    
    def _extract_potential_itemno(self, user_input: str) -> Optional[str]:
        """
        사용자 입력에서 잠재적인 ITEMNO 패턴 추출
        
        Args:
            user_input: 사용자 입력 메시지
            
        Returns:
            추출된 패턴 또는 None
        """
        # 다양한 ITEMNO 패턴 시도
        patterns = [
            r'\b\d{4,}-\w+',  # 44043-CA1
            r'\b[A-Z]-\w+',   # Y-MV1035
            r'\b[A-Z]{2,4}-\w+',  # PE-SE1304B
            r'\b\d{5,}',      # 5자리 이상 숫자
            r'\b[A-Z]{2,4}\d+',  # PE12345
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input)
            if match:
                return match.group(0)
        
        return None
    
    def _calculate_similarity(self, input_itemno: str, db_itemno: str) -> float:
        """
        두 ITEMNO 간의 유사도 계산
        
        Args:
            input_itemno: 사용자 입력 ITEMNO
            db_itemno: DB의 ITEMNO
            
        Returns:
            유사도 점수 (0.0 ~ 1.0)
        """
        # 기본 문자열 유사도
        base_similarity = SequenceMatcher(None, input_itemno.lower(), db_itemno.lower()).ratio()
        
        # 추가 규칙들
        bonus = 0.0
        
        # 1. 정확한 매칭
        if input_itemno.lower() == db_itemno.lower():
            bonus = 0.3
        
        # 2. 부분 매칭 (포함 관계)
        elif input_itemno.lower() in db_itemno.lower() or db_itemno.lower() in input_itemno.lower():
            bonus = 0.2
        
        # 3. 숫자 부분이 동일한 경우
        input_numbers = re.findall(r'\d+', input_itemno)
        db_numbers = re.findall(r'\d+', db_itemno)
        if input_numbers and db_numbers and any(in_num in db_num for in_num in input_numbers for db_num in db_numbers):
            bonus = 0.1
        
        return min(1.0, base_similarity + bonus)
    
    def _is_exact_match(self, user_input: str, itemno: str) -> bool:
        """
        사용자 입력에서 정확한 ITEMNO 매칭 여부 확인
        
        Args:
            user_input: 사용자 입력 메시지
            itemno: 매칭된 ITEMNO
            
        Returns:
            정확한 매칭 여부
        """
        # 정규표현식 패턴으로 정확한 매칭 확인
        for pattern in self.itemno_patterns:
            match = re.search(pattern, user_input)
            if match and match.group(0) == itemno:
                return True
        
        return False

    def _parse_default_scenario(self, user_input: str) -> ParsedInput:
        """
        기본 시나리오 파싱
        
        Args:
            user_input: 사용자 입력 메시지
            
        Returns:
            ParsedInput: 기본 파싱 결과
        """
        return ParsedInput(
            scenario="default",
            location=None,
            equipment_type=None,
            status_code=None,
            priority=None,
            itemno=None,
            confidence=0.3
        )

# 전역 입력 파서 인스턴스
# 다른 모듈에서 import하여 사용
input_parser = InputParser() 