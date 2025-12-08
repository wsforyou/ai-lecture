import asyncio
import os
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StreamableHttpMcpToolAdapter, StreamableHttpServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from datetime import timedelta
import logging
from autogen_agentchat import EVENT_LOGGER_NAME, TRACE_LOGGER_NAME

# Trace 로그 (디버깅용)
trace_logger = logging.getLogger(TRACE_LOGGER_NAME)
trace_logger.addHandler(logging.StreamHandler())
trace_logger.setLevel(logging.DEBUG)

# 이벤트 로그 (구조화 메시지)
event_logger = logging.getLogger(EVENT_LOGGER_NAME)
event_logger.addHandler(logging.StreamHandler())
event_logger.setLevel(logging.DEBUG)

async def setup_mcp_tools():
    """MCP 서버에서 도구들을 설정"""
    server_params = StreamableHttpServerParams(
        url="http://127.0.0.1:8000/mcp",

        terminate_on_close=True
    )

    tools = await mcp_server_tools(server_params)
    #tools = []
    #tool_names = ["get_weather", "calculate", "get_file_info", "list_tools"]

    #for tool_name in tool_names:
    #    try:
    #        adapter = await StreamableHttpMcpToolAdapter.from_server_params(
    #            server_params, tool_names
    #        )
    #        tools.append(adapter)
    #        print(f"✅ {tool_name} 도구 연결 성공")
    #    except Exception as e:
    #        print(f"❌ {tool_name} 도구 연결 실패: {e}")

    return tools

async def setup_azure_client():
    """Azure OpenAI 클라이언트 설정"""
    try:

        model_client = OpenAIChatCompletionClient(
            model="gpt-4o",
            api_key= "", # 실제 키 사용 시 주의
            base_url="https://api.openai.com/v1"
            )

        print("✅ Azure OpenAI 클라이언트 설정 완료 (표준 모델명)")
        return model_client
    except Exception as e:
        print(f"⚠️ 표준 모델명 설정 실패, 커스텀 모델 정보로 재시도: {e}")

async def main():
    print("🚀 Autogen MCP 클라이언트 시작\n")

    try:
        # 1. MCP 도구 설정
        print("🔧 MCP 도구 연결 중...")
        tools = await setup_mcp_tools()

        if not tools:
            print("❌ MCP 도구를 찾을 수 없습니다. MCP 서버가 실행되고 있는지 확인하세요.")
            return

        # 2. Azure OpenAI 클라이언트 설정
        print("\n🤖 Azure OpenAI 클라이언트 설정 중...")
        model_client = await setup_azure_client()

        # 3. Assistant Agent 생성
        print("\n👨‍💼 Assistant Agent 생성 중...")
        agent = AssistantAgent(
            name="versatile_assistant",
            model_client=model_client,
            tools=tools,
            system_message="""You are a versatile assistant with access to weather, calculation, and file information tools.

Available tools:
- get_weather(location): Get weather information for a location
- calculate(expression): Perform mathematical calculations
- get_file_info(filename): Get information about files
- list_tools(): Show all available tools

Always use the appropriate tools when asked to perform tasks that match their capabilities.
Provide clear, helpful responses and explain what tools you're using."""
        )

        # 4. 작업 실행
        print("\n🎯 작업 실행 중...\n")
        await Console(
            agent.run_stream(
                task="""안녕하세요! 다음 작업들을 도와주세요:

1. 123223 + 456789를 계산해주세요
2. 'ag2' 파일의 정보를 조회해주세요
3. Seoul의 현재 날씨를 알려주세요
4. 사용 가능한 모든 도구 목록을 보여주세요

각 작업에 적절한 도구를 사용해서 수행해주세요.""",
                cancellation_token=CancellationToken()
            )
        )

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n🔧 문제 해결 방법:")
        print("1. MCP 서버가 실행되고 있는지 확인 (python mcp_server.py)")
        print("2. 환경변수가 올바르게 설정되어 있는지 확인")
        print("3. Azure OpenAI 배포명과 엔드포인트 확인")


if __name__ == "__main__":
    asyncio.run(main())