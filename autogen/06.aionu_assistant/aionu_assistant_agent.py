#aionu_assistant_agent.py
import json
import os
from autogen import ConversableAgent
from typing import Optional, List, Dict, Any, Union
from aionu_llm_client import AionuLLMClient, AionuAPIError

class AionuAssistantAgent(ConversableAgent):
    """
    AIONU Chat API를 통한 Custom Agent
    - Autogen의 ConversableAgent를 상속하여 generate_reply를 오버라이드
    - 내부적으로 AionuLLMClient 인스턴스를 유지하여 동일 세션에서 conversation_id 자동 연계
    """
    def __init__(self, name="aionu_assistant", system_message="", **kwargs):
        super().__init__(name=name, system_message=system_message, human_input_mode="NEVER", **kwargs)

        base_url = os.getenv("AIONU_BASE_URL", "https://api.abclab.ktds.com/v1")
        api_key = os.getenv("AIONU_API_KEY", "") #ABC Lab에서 본인이 만든 에이전트 API KEY
        self._user = os.getenv("AIONU_API_USER", "user")

        if not api_key:
            raise RuntimeError("AIONU_API_KEY 환경변수가 설정되어 있지 않습니다.")

        # 동일 에이전트 생명주기 동안 재사용(대화 유지)
        self._client = AionuLLMClient(base_url=base_url, api_key=api_key)

    def generate_reply(self, messages=None, sender=None, **kwargs):
        """
        Autogen이 넘겨주는 messages(OpenAI 형식)를 Aionu API의 query 문자열로 변환하여 호출
        문자열을 반환하면 Autogen이 assistant 응답으로 처리함
        """
        # Autogen이 호출 시점의 메시지 배열을 전달함
        msgs = messages or []

        parts = []
        for m in msgs:
            role = m.get("role")
            content = m.get("content", "")
            if not content:
                continue
            if role == "system":
                parts.append(f"[System]\n{content}")
            elif role == "user":
                parts.append(f"[User]\n{content}")
            elif role == "assistant":
                parts.append(f"[Assistant]\n{content}")
            else:
                parts.append(str(content))
        query = "\n\n".join(parts)

        try:
            resp = self._client.send_message(
                query=query,
                user=self._user,
                response_mode="streaming",  # timeout 방지 및 빠른 응답
                conversation_id=self._client.get_conversation_id(),
                inputs={},
                max_retries=3,
                base_timeout=30000
            )
            if isinstance(resp, dict):
                return resp.get("answer") or json.dumps(resp, ensure_ascii=False)
            return resp
        except AionuAPIError as e:
            return f"AIONU API 오류: {e.message}"
        except Exception as e:
            return f"예상치 못한 오류: {e}"
