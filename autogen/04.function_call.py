# 04.function_call.py

import os
import logging
import autogen

"""상세 로깅을 활성화한 AutoGen 예제"""
print("===== 상세 로깅 AutoGen 예제 시작 =====")


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
    "temperature": 0.3, # LLM 응답의 다양성 제어
    "config_list" : config_list_azure
}

#function_map = {
#    "search_documentation": search_documentation,
#    "execute_code_analysis": execute_code_analysis
#}

def search_documentation(query: str, language: str = "python") -> str:
    """
    온라인 문서에서 python 정보를 검색합니다.

    Args:
        query (str): 검색할 키워드
        language (str): 프로그래밍 언어

    Returns:
        str: 검색 결과
    """
    # 실제 검색 로직 (예시)
    return f"{language}에서 '{query}'에 대한 문서 정보입니다."

def execute_code_analysis(code: str) -> dict:
    """
    코드 분석을 수행합니다.

    Args:
        code (str): 분석할 코드

    Returns:
        dict: 분석 결과
    """
    return {
        "lines": len(code.split('\n')),
        "complexity": "Medium",
        "suggestions": ["변수명 개선", "주석 추가"]
    }


# AssistantAgent 생성
assistant = autogen.AssistantAgent(
    name="coding_assistant",  # 에이전트 이름
    system_message="""
        역할:
        - 당신은 숙련된 Python 분석가 입니다.
        - 사용자의 요청에 따라 적절한 답변을 제공합니다.
        전제 조건:
        - 사용자의 요청이 Python 사용법 및 코드 분석일 경우, 반드시 함수 호출을 실행합니다.
        - 호출 결과를 바탕으로 사용자 및 다른 에이전트에게 유용한 정보를 제공합니다.
    """,
    llm_config=llm_config,
    max_consecutive_auto_reply=1,  # 최대 3번까지 연속 응답
)

# UserProxyAgent 생성
user_proxy = autogen.UserProxyAgent(
    name="code_executor",
    system_message="""
        역할:
        - 사용자 역할을 대변하며, 다른 에이전트들의 응답을 취합 합니다.
        - 최종 사용자에게 전달할 응답을 결정하거나, 대화를 종료해야 할 시점을 판단할 수 있습니다.

        전제 조건:
        - 사용자의 요청이 Python 사용법 및 코드 분석일 경우, 반드시 함수 호출을 실행합니다.
        - 호출 결과를 바탕으로 사용자 및 다른 에이전트에게 유용한 정보를 제공합니다.
    """,
    human_input_mode="NEVER",
    code_execution_config={
        "work_dir": "./",
        "use_docker": False,
    },
)

user_proxy.register_for_execution(name="search_documentation")(search_documentation)
user_proxy.register_for_execution(name="execute_code_analysis")(execute_code_analysis)

assistant.register_for_llm(name="execute_code_analysis", description="코드 분석 함수")(execute_code_analysis)
assistant.register_for_llm(name="search_documentation", description="문서 검색 함수")(search_documentation)

# 메시지 전송
messages = "python List 사용법에 대해서 설명해줘"

# 응답 생성
print("응답 요청 중...")

response = user_proxy.initiate_chat(
    assistant,
    message=messages
)

print("\n===== 응답 내용 =====")
print(f"응답 내용:\n{response.summary}")

print("===== 상세 로깅 AutoGen 예제 종료 =====")