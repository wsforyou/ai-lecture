#aionu_example.py
import os
from autogen import AssistantAgent, UserProxyAgent
# AIONU 클라이언트 임포트
from aionu_assistant_agent import AionuAssistantAgent

# 코드 실행에 특화된 UserProxyAgent
user_proxy = UserProxyAgent(
    name="code_executor",
    system_message="""코드 실행 전문 에이전트입니다.
    안전하고 효율적인 코드 실행을 담당합니다.""",
    human_input_mode="NEVER",  # 사용자 입력 없이 자동 실행
    max_consecutive_auto_reply=3,
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

assistant = AionuAssistantAgent(
    name="coding_assistant",  # 에이전트 이름
    system_message="""당신은 숙련된 Python 개발자입니다.
    사용자의 코딩 질문에 명확하고 실용적인 답변을 제공하세요.
    코드 예제를 MarkDown 양식으로 반드시 code임을 명확하게 하여 설명해주세요.""",
    max_consecutive_auto_reply=2,  # 최대 3번까지 연속 응답,
    # is_termination_msg=lambda msg: "작업 완료" in msg.get("content", "") or
    #                                "TERMINATE" in msg.get("content", "")
)

#실행 및 결과 확인
response = user_proxy.initiate_chat(
    assistant,
    message="""Python으로 간단한 계산기 클래스를 만들어주세요.
    다음 기능이 포함되어야 합니다:
    1. 사칙연산 (덧셈, 뺄셈, 곱셈, 나눗셈)
    2. 계산 이력 저장
    3. 이력 조회 기능

    코드를 작성한 후 간단하게 테스트를 한번만 실행해서 결과를 출력해 주세요.
    """
)

print(response)
