#pip install fastapi uvicorn jinja2

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import autogen
from autogen import UserProxyAgent, AssistantAgent

config_list_azure = [
    {
        "model": "gpt-4o",
        "api_key": "", # 실제 키 사용 시 주의
        "base_url": "https://api.openai.com/v1"
    }
]

llm_config = {
    "cache_seed": None, # 임의의 시드값
    "temperature": 0.8, # LLM 응답의 다양성 제어
    "config_list" : config_list_azure
}

class SimpleChatbotManager:
    """간단한 채팅봇 Agent 관리 클래스"""

    def __init__(self):
        self.user_proxy = None
        self.assistant = None
        self._initialize_agents()

    def _initialize_agents(self):
        """Agent 초기화"""
        try:
            # UserProxy Agent 생성
            # 사용자의 입력을 받고 대화를 관리하는 역할
            self.user_proxy = UserProxyAgent(
                name="UserProxy",
                system_message="""
                당신은 사용자와 AI 어시스턴트 간의 대화를 중재하는 역할을 합니다.
                사용자의 질문을 정확히 이해하고 적절한 응답을 요청하세요.
                Assistant의 답변은 가공하지 말고 그대로 답변해 주세요.
                """.strip(),
                human_input_mode="NEVER",
                max_consecutive_auto_reply=3,
                code_execution_config=False,  # 코드 실행 비활성화
                # llm_config=llm_config
            )

            # Assistant Agent 생성
            # 실제 AI 응답을 생성하는 역할
            self.assistant = AssistantAgent(
                name="Assistant",
                system_message="""
                당신은 도움이 되는 AI 어시스턴트입니다.
                사용자의 질문에 정확하고 친절하게 답변하세요.

                응답 원칙:
                1. 명확하고 이해하기 쉬운 한국어로 답변
                2. 질문의 의도를 정확히 파악하여 적절한 정보 제공
                3. 불확실한 정보는 추측하지 말고 모른다고 솔직히 답변
                4. 필요시 추가 질문을 통해 더 나은 답변 제공
                """.strip(),
                llm_config=llm_config,
                max_consecutive_auto_reply=3
            )

            print("✅ AutoGen Agents 초기화 완료")

        except Exception as e:
            print(f"❌ Agent 초기화 실패: {str(e)}")
            raise

    async def get_response(self, user_message: str) -> str:
        """
        사용자 메시지에 대한 AI 응답 생성

        Args:
            user_message (str): 사용자 입력 메시지

        Returns:
            str: AI 응답 메시지
        """
        try:
            print(f"🔄 메시지 처리 시작: {user_message[:50]}...")

            # 비동기 방식으로 대화 시작
            # initiate_chat 메서드를 통해 UserProxy가 Assistant와 대화 시작
            chat_result = await self.user_proxy.a_initiate_chat(
                self.assistant,
                message=user_message,
                silent=False
            )

            print("chat_result", chat_result)

            # 대화 결과에서 마지막 응답 추출
            if hasattr(chat_result, 'chat_history') and chat_result.chat_history:
                # 마지막 메시지가 Assistant의 응답
                last_message = chat_result.chat_history[-2]
                response = last_message.get('content', '응답을 생성할 수 없습니다.')
            else:
                # chat_history가 없는 경우 대화 기록에서 추출
                messages = self.user_proxy.chat_messages.get(self.assistant, [])
                if messages:
                    response = messages[-2].get('content', '응답을 생성할 수 없습니다.')
                else:
                    response = "죄송합니다. 응답을 생성할 수 없습니다."

            print(f"✅ 응답 생성 완료: {len(response)}자")
            return response

        except Exception as e:
            error_msg = f"메시지 처리 중 오류가 발생했습니다: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

    def reset_conversation(self):
        """대화 기록 초기화"""
        try:
            # 각 Agent의 대화 기록 초기화
            if hasattr(self.user_proxy, 'chat_messages'):
                self.user_proxy.chat_messages.clear()
            if hasattr(self.assistant, 'chat_messages'):
                self.assistant.chat_messages.clear()

            print("🔄 대화 기록 초기화 완료")

        except Exception as e:
            print(f"❌ 대화 기록 초기화 실패: {str(e)}")

    def get_agent_info(self) -> Dict[str, Any]:
        """Agent 정보 반환"""
        return {
            "user_proxy": {
                "name": self.user_proxy.name if self.user_proxy else None,
                "status": "활성" if self.user_proxy else "비활성"
            },
            "assistant": {
                "name": self.assistant.name if self.assistant else None,
                "status": "활성" if self.assistant else "비활성"
            },
        }

# 전역 Agent 관리자 인스턴스
chatbot_manager = None

def get_chatbot_manager() -> SimpleChatbotManager:
    """싱글톤 패턴으로 Agent 관리자 반환"""
    global chatbot_manager
    if chatbot_manager is None:
        chatbot_manager = SimpleChatbotManager()
    return chatbot_manager
