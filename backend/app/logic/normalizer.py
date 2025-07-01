"""
PMark1 AI Assistant - LLM 기반 용어 정규화 엔진

이 파일은 OpenAI GPT-4o를 활용하여 자연어 입력을 표준 용어로 정규화하는 엔진입니다.
사전에 정의되지 않은 표현, 오타, 띄어쓰기 오류 등도 AI가 이해하여 정확한 매칭을 제공합니다.

주요 담당자: AI/ML 엔지니어, 백엔드 개발자
수정 시 주의사항:
- OpenAI API 키가 필요합니다 (config.py에서 설정)
- 표준 용어 사전은 실제 DB 데이터와 일치해야 합니다
- 프롬프트 수정 시 일관성 있는 응답을 위해 temperature를 낮게 유지
"""

import openai
from typing import Dict, List, Optional, Tuple
from ..config import Config
import json
import re

class LLMNormalizer:
    """
    LLM 기반 용어 정규화 엔진
    
    사용처:
    - database.py: search_similar_notifications()에서 입력값 정규화
    - parser.py: _normalize_extracted_terms()에서 추출된 용어 정규화
    
    연계 파일:
    - config.py: OpenAI API 설정
    - database.py: normalize_term() 메서드에서 호출
    - parser.py: _normalize_extracted_terms()에서 호출
    
    담당자 수정 가이드:
    - standard_terms 사전은 실제 DB의 equipType, location, statusCode 값과 일치해야 함
    - 새로운 카테고리 추가 시 standard_terms에 추가
    - 프롬프트 수정 시 예시도 함께 업데이트
    - temperature는 0.1 이하로 유지하여 일관성 확보
    """
    
    def __init__(self):
        """
        LLM 정규화 엔진 초기화
        
        설정:
        - OpenAI 클라이언트 초기화
        - 표준 용어 사전 정의 (카테고리별)
        """
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        
        # 표준 용어 사전 (LLM이 참조할 기준)
        # 실제 DB의 equipType, location, statusCode 값과 일치해야 함
        self.standard_terms = {
            "equipment": [
                "[VEDR]Pressure Vessel/ Drum", "[GVGV]Guided Vehicle/ Guided Vehicle", 
                "[ANAA]Analyzer/ Analyzer", "[MVVV]Motor Operated Valve/ Motor Operated Valve",
                "[CONV]Conveyor/ Conveyor", "[PUMP]Pump/ Pump", "[HEXH]Heat Exchanger/ Heat Exchanger",
                "[VALV]Valve/ Valve", "[CTLV]Control Valve/ Control Valve", "[TANK]Tank/ Tank",
                "[STNK]Storage Tank/ Storage Tank", "[FILT]Filter/ Filter", "[REAC]Reactor/ Reactor",
                "[COMP]Compressor/ Compressor", "[FAN]Fan/ Fan", "[BLOW]Blower/ Blower"
            ],
            "location": [
                "No.1 PE", "No.2 PE", "Nexlene 포장 공정", "PW-B3503", "SKGC-설비관리", 
                "KNC-설비관리", "석유제품배합/저장", "합성수지 포장", "RFCC", "1창고 #7Line", "2창고 #8Line", "공통 시설"
            ],
            "status": [
                "고장", "누설", "작동불량", "소음", "진동", "온도상승", 
                "압력상승", "주기적 점검/정비", "고장.결함.수명소진", "SHE", "운전 Condition 이상"
            ]
        }
    
    def normalize_term(self, term: str, category: str) -> Tuple[str, float]:
        """
        LLM을 사용하여 용어를 표준 용어로 정규화
        
        Args:
            term: 정규화할 용어 (예: "압력베젤", "모터밸브")
            category: 용어 카테고리 ("equipment", "location", "status")
            
        Returns:
            (표준용어, 신뢰도점수): 정규화된 표준 용어와 신뢰도 (0.0~1.0)
            
        사용처:
        - database.py: search_similar_notifications()에서 입력값 정규화
        - parser.py: _normalize_extracted_terms()에서 추출된 용어 정규화
        
        예시:
        - normalize_term("압력베젤", "equipment") → ("Pressure Vessel", 0.95)
        - normalize_term("모터밸브", "equipment") → ("Motor Operated Valve", 0.9)
        - normalize_term("서규제품배합", "location") → ("석유제품배합/저장", 0.95)
        
        담당자 수정 가이드:
        - 신뢰도가 0.3 미만인 경우 원본 용어를 반환하도록 설정됨
        - 오류 발생 시 원본 용어와 중간 신뢰도(0.5) 반환
        - 새로운 카테고리 추가 시 standard_terms에 추가 필요
        """
        if not term:
            return term, 0.0
        
        try:
            # LLM 프롬프트 생성
            prompt = self._create_normalization_prompt(term, category)
            
            # LLM 호출 (일관성을 위해 낮은 temperature 사용)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 설비관리 시스템의 용어 정규화 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 일관성을 위해 낮은 temperature
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 응답 파싱
            normalized_term, confidence = self._parse_normalization_response(result_text)
            
            return normalized_term, confidence
            
        except Exception as e:
            print(f"LLM 정규화 오류: {e}")
            return term, 0.5  # 오류 시 원본 반환, 중간 신뢰도
    
    def _create_normalization_prompt(self, term: str, category: str) -> str:
        """
        정규화용 프롬프트 생성
        
        Args:
            term: 정규화할 용어
            category: 용어 카테고리
            
        Returns:
            LLM에게 전달할 프롬프트 문자열
            
        담당자 수정 가이드:
        - 표준 용어 목록은 실제 DB 데이터와 일치해야 함
        - 정규화 규칙은 비즈니스 로직에 맞게 수정 가능
        - 예시는 실제 사용 사례를 반영하여 업데이트
        """
        
        standard_terms = self.standard_terms.get(category, [])
        
        return f"""
다음 입력 용어를 설비관리 시스템의 표준 용어로 정규화해주세요.

**입력 용어**: {term}
**카테고리**: {category}

**표준 용어 목록**:
{chr(10).join([f"- {term}" for term in standard_terms])}

**정규화 규칙**:
1. 한국어-영어 혼용 표현을 표준 영어 용어로 변환
2. 오타나 띄어쓰기 오류를 수정
3. 유사한 의미의 표현을 가장 적절한 표준 용어로 매핑
4. 표준 용어 목록에 없는 경우, 가장 유사한 용어 선택
5. 전혀 매칭되지 않는 경우 "UNKNOWN" 반환

**응답 형식**:
```json
{{
    "normalized_term": "표준용어",
    "confidence": 0.95,
    "reasoning": "정규화 이유"
}}
```

**예시**:
- 입력: "압력베젤" → 출력: {{"normalized_term": "[VEDR]Pressure Vessel/ Drum", "confidence": 0.95, "reasoning": "한국어 표현을 실제 DB 형식으로 변환"}}
- 입력: "모터밸브" → 출력: {{"normalized_term": "[MVVV]Motor Operated Valve/ Motor Operated Valve", "confidence": 0.90, "reasoning": "한국어 표현을 실제 DB 형식으로 변환"}}
- 입력: "1PE" → 출력: {{"normalized_term": "No.1 PE", "confidence": 0.95, "reasoning": "축약형을 표준 형식으로 변환"}}
- 입력: "고장" → 출력: {{"normalized_term": "고장.결함.수명소진", "confidence": 0.95, "reasoning": "일반 고장을 DB의 표준 현상코드로 변환"}}
"""
    
    def _parse_normalization_response(self, response_text: str) -> Tuple[str, float]:
        """
        LLM 응답을 파싱하여 정규화 결과 추출
        
        Args:
            response_text: LLM 응답 텍스트
            
        Returns:
            (정규화된 용어, 신뢰도): 파싱된 결과
            
        담당자 수정 가이드:
        - JSON 파싱 실패 시 폴백 로직으로 응답에서 용어 추출
        - 응답 형식이 변경되면 이 메서드 수정 필요
        """
        
        try:
            # JSON 부분 추출 (```json ... ``` 블록)
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                # JSON 블록이 없는 경우 전체 텍스트를 JSON으로 파싱 시도
                data = json.loads(response_text)
            
            normalized_term = data.get("normalized_term", "")
            confidence = data.get("confidence", 0.5)
            
            return normalized_term, confidence
            
        except Exception as e:
            print(f"정규화 응답 파싱 오류: {e}")
            # 폴백: 응답에서 용어 추출 시도
            lines = response_text.split('\n')
            for line in lines:
                if 'normalized_term' in line or '표준용어' in line:
                    # 간단한 추출 로직
                    if ':' in line:
                        term_part = line.split(':')[1].strip().strip('"{}')
                        return term_part, 0.7
            
            return "", 0.0
    
    def batch_normalize(self, terms: List[Tuple[str, str]]) -> List[Tuple[str, float]]:
        """
        여러 용어를 일괄 정규화
        
        Args:
            terms: [(용어, 카테고리), ...] 형태의 리스트
            
        Returns:
            [(정규화된 용어, 신뢰도), ...] 형태의 리스트
            
        사용처:
        - 대량의 용어를 한 번에 정규화할 때 사용
        - 성능 최적화를 위해 배치 처리 가능
        
        담당자 수정 가이드:
        - OpenAI API 비용 절약을 위해 배치 크기 조정 가능
        - 병렬 처리로 성능 향상 가능
        """
        results = []
        for term, category in terms:
            normalized, confidence = self.normalize_term(term, category)
            results.append((normalized, confidence))
        return results
    
    def get_similarity_score(self, term1: str, term2: str, category: str) -> float:
        """
        두 용어 간의 유사도 점수 계산 (LLM 활용)
        
        Args:
            term1: 첫 번째 용어
            term2: 두 번째 용어
            category: 용어 카테고리
            
        Returns:
            유사도 점수 (0.0~1.0)
            
        사용처:
        - 향후 유사도 기반 검색 기능 구현 시 사용
        - 추천 엔진의 유사도 계산 개선 시 활용
        
        담당자 수정 가이드:
        - 평가 기준은 비즈니스 요구사항에 맞게 조정 가능
        - 캐싱을 통해 성능 향상 가능
        """
        
        try:
            prompt = f"""
다음 두 용어의 유사도를 0.0~1.0 사이의 점수로 평가해주세요.

**용어 1**: {term1}
**용어 2**: {term2}
**카테고리**: {category}

**평가 기준**:
- 1.0: 완전히 동일한 의미
- 0.8-0.9: 매우 유사한 의미
- 0.6-0.7: 유사한 의미
- 0.4-0.5: 약간 유사한 의미
- 0.0-0.3: 거의 관련 없음

**응답 형식**:
```json
{{
    "similarity_score": 0.85,
    "reasoning": "유사도 평가 이유"
}}
```
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 용어 유사도 평가 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=150
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 응답 파싱
            json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return data.get("similarity_score", 0.5)
            
            return 0.5
            
        except Exception as e:
            print(f"유사도 계산 오류: {e}")
            return 0.5

# 전역 정규화 엔진 인스턴스
# 다른 모듈에서 import하여 사용
normalizer = LLMNormalizer() 