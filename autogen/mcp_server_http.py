# pip
# pip install fastapi_mcp
from typing import List
from mcp.server.fastmcp import FastMCP
import json
import logging
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,  # 로그 레벨: DEBUG, INFO, WARNING 등
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("mcp-server")

# MCP 서버 생성
mcp = FastMCP("WeatherAndUtils", debug=True)

@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather information for a specific location."""
    # 실제 날씨 API 대신 시뮬레이션된 데이터 반환
    weather_data = {
        "seoul": "서울: 맑음, 22°C, 습도 60%",
        "new york": "뉴욕: 흐림, 18°C, 습도 75%",
        "tokyo": "도쿄: 비, 16°C, 습도 85%",
        "london": "런던: 안개, 12°C, 습도 90%"
    }

    location_lower = location.lower()
    if location_lower in weather_data:
        return weather_data[location_lower]
    else:
        return f"{location}: 날씨 정보를 찾을 수 없습니다. 사용 가능한 도시: Seoul, New York, Tokyo, London"

@mcp.tool()
async def calculate(expression: str) -> str:
    """Calculate mathematical expressions safely."""
    try:
        # 안전한 계산을 위해 eval 대신 간단한 파싱 사용
        allowed_chars = set('0123456789+-*/(). ')
        if not all(c in allowed_chars for c in expression):
            return "오류: 허용되지 않는 문자가 포함되어 있습니다."

        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"계산 오류: {str(e)}"

@mcp.tool()
async def get_file_info(filename: str) -> str:
    """Get information about a file (simulated)."""
    # 실제 파일 시스템 대신 시뮬레이션된 파일 정보
    file_info = {
        "ag2": {
            "type": "directory",
            "description": "AutoGen 2.0 프로젝트 디렉토리",
            "contents": ["src/", "tests/", "docs/", "requirements.txt", "README.md"],
            "size": "15.2 MB"
        },
        "config.json": {
            "type": "file",
            "description": "설정 파일",
            "contents": "JSON 형식의 애플리케이션 설정",
            "size": "2.1 KB"
        },
        "main.py": {
            "type": "file",
            "description": "메인 애플리케이션 파일",
            "contents": "Python 메인 실행 코드",
            "size": "8.5 KB"
        }
    }

    if filename in file_info:
        info = file_info[filename]
        return json.dumps(info, ensure_ascii=False, indent=2)
    else:
        return f"파일 '{filename}'을 찾을 수 없습니다. 사용 가능한 파일: {list(file_info.keys())}"

@mcp.tool()
async def list_tools() -> str:
    """List all available tools in this MCP server."""
    tools = [
        "get_weather(location): 특정 위치의 날씨 정보 조회",
        "calculate(expression): 수학 계산 수행",
        "get_file_info(filename): 파일 정보 조회",
        "list_tools(): 사용 가능한 도구 목록 표시"
    ]
    return "사용 가능한 도구들:\n" + "\n".join(f"- {tool}" for tool in tools)

if __name__ == "__main__":
    print("🚀 MCP 서버 시작 중...")
    print("📍 서버 주소: http://127.0.0.1:8000/mcp")
    print("🛠️  사용 가능한 도구: get_weather, calculate, get_file_info, list_tools")
    mcp.run(transport="streamable-http")