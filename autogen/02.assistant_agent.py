# 02.assistant_agent.py
import os
from autogen import AssistantAgent, UserProxyAgent

# LLM 설정 구성
config_list_azure = [
    {
        "model": "gpt-4o",
        "api_key": "", # 실제 키 사용 시 주의
        "base_url": "https://api.openai.com/v1",
    },
]
llm_config = {
    "cache_seed": 42, # 임의의 시드값
    "temperature": 0.7, # LLM 응답의 다양성 제어
    "config_list" : config_list_azure
}

# 코드 실행에 특화된 UserProxyAgent
user_proxy = UserProxyAgent(
    name="code_executor",
    system_message="""코드 실행 전문 에이전트입니다.
    안전하고 효율적인 코드 실행을 담당합니다.""",
    human_input_mode="ALWAYS",  # 사용자 입력 없이 자동 실행
    max_consecutive_auto_reply=15,
    code_execution_config={
        "work_dir": "./",
        "use_docker": False,
        "timeout": 120,  # 더 긴 타임아웃
        "last_n_messages": 5,  # 더 많은 메시지 저장
    },
    # 커스텀 종료 조건
    is_termination_msg=lambda msg: "작업 완료" in msg.get("content", "") or
                                   "TERMINATE" in msg.get("content", "")
)

# AssistantAgent 생성
assistant = AssistantAgent(
    name="coding_assistant",  # 에이전트 이름
    system_message="""당신은 숙련된 Python 개발자입니다.
    사용자의 코딩 질문에 명확하고 실용적인 답변을 제공하세요.
    코드 예제를 포함하여 설명해주세요.""",
    llm_config=llm_config,
    max_consecutive_auto_reply=3,  # 최대 3번까지 연속 응답
)

#실행 및 결과 확인
response = user_proxy.initiate_chat(
    assistant,
    message="""Python으로 간단한 계산기 클래스를 만들어주세요.
    다음 기능이 포함되어야 합니다:
    1. 사칙연산 (덧셈, 뺄셈, 곱셈, 나눗셈)
    2. 계산 이력 저장
    3. 이력 조회 기능

    코드를 작성한 후 간단한 테스트도 실행해주세요."""
)

# Python으로 간단한 문자열 분리해서 배열로 변환하는 클래스를 만들어 주세요. 코드를 작성한 후 간단한 테스트도 실행해 주세요

print(response)