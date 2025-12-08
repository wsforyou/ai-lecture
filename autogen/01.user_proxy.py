# 01.user_proxy.py
import os
from autogen import UserProxyAgent

# 코드 실행에 특화된 UserProxyAgent
user_proxy = UserProxyAgent(
    name="code_executor",
    system_message="""코드 실행 전문 에이전트입니다.
    안전하고 효율적인 코드 실행을 담당합니다.""",
    human_input_mode="NEVER",  # 사용자 입력 없이 자동 실행
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

#Autogen Agent는 Markdown 코드펜스 문법을 인식하여 정의된 언어 기반으로 실행한다.
#기본은 Python 이며 Linux 환경일 경우 bash, Windows 환경일 경우 shell, 나머지 언어는 별도 커스텀 Executor가 필요하다.
messages = [{"role": "user", "content": "```shell\nls\n```"}]
print("messages", messages)

#실행 및 결과 확인
response = user_proxy.generate_reply(messages)
print(response)