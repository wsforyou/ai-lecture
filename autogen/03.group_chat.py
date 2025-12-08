# 03.group_chat.py

from autogen import GroupChat, GroupChatManager, AssistantAgent, UserProxyAgent

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

# 다양한 역할의 에이전트들 생성
agents_list = []

# 1. 요구사항 분석가
requirement_analyst = AssistantAgent(
    name="requirement_analyst",
    system_message="""당신은 요구사항 분석 전문가입니다.
    사용자의 요구사항을 명확히 분석하고 구체적인 기능 명세를 작성합니다.
    기술적 제약사항과 비즈니스 요구사항을 모두 고려합니다.""",
    llm_config=llm_config,
)
agents_list.append(requirement_analyst)

# 2. 아키텍트
architect = AssistantAgent(
    name="architect",
    system_message="""당신은 소프트웨어 아키텍트입니다.
    시스템 설계와 기술 스택 선택을 담당합니다.
    확장 가능하고 유지보수가 용이한 아키텍처를 설계합니다.""",
    llm_config=llm_config,
)
agents_list.append(architect)

# 3. 개발자
developer = AssistantAgent(
    name="developer",
    system_message="""당신은 풀스택 개발자입니다.
    Python을 주로 사용하며,
    클린 코드와 테스트 가능한 코드 작성에 중점을 둡니다.
    실제 코드를 작성해 주세요.""",
    llm_config=llm_config,
)
agents_list.append(developer)

# 4. 테스터
tester = AssistantAgent(
    name="tester",
    system_message="""당신은 QA 테스터입니다.
    코드의 품질을 검증하고 다양한 테스트 케이스를 작성합니다.
    단위 테스트, 통합 테스트, 성능 테스트를 담당합니다.""",
    llm_config=llm_config,
)
agents_list.append(tester)

# 5. UserProxyAgent (실행자)
executor = UserProxyAgent(
    name="executor",
    system_message="코드 실행과 결과 검증을 담당합니다.",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=2,
    code_execution_config={
        "work_dir": "./",
        "use_docker": False,
        "timeout": 60,
    },
)
agents_list.append(executor)

print(f"총 {len(agents_list)}개의 에이전트가 생성되었습니다.")

# GroupChat 생성
group_chat = GroupChat(
    agents=agents_list,
    messages=[],
    max_round=20,  # 최대 20라운드 대화
    speaker_selection_method="auto",
    admin_name="Project_Manager",  # 프로젝트 매니저 역할
)

# GroupChatManager 생성
chat_manager = GroupChatManager(
    groupchat=group_chat,
    name="chat_manager",
    llm_config=llm_config,
    system_message="""당신은 프로젝트 매니저입니다.
    팀원들의 대화를 조율하고 프로젝트가 효율적으로 진행되도록 관리합니다.
    각 에이전트의 전문성을 최대한 활용하여 최적의 결과를 도출합니다."""
)

print("GroupChat과 ChatManager가 성공적으로 생성되었습니다.")

def run_group_project():
    """그룹 에이전트들이 협력하여 프로젝트 수행"""

    project_description = """
    KT 내부용 직원 출입 관리 시스템을 개발해주세요.

    요구사항:
    1. 직원 정보 관리 (CRUD)
    2. 출입 기록 저장 및 조회
    3. 실시간 출입 현황 모니터링
    4. 보안 등급별 접근 제어
    5. REST API 제공
    6. 관리자 대시보드

    기술 제약사항:
    - Backend: Python 사용
    - Database: PostgreSQL
    - 인증: JWT 토큰 기반
    - 문서화: Swagger UI 포함

    각 팀원은 자신의 전문 분야에서 기여해주세요.
    """

    try:
        # 프로젝트 시작
        executor.initiate_chat(
            chat_manager,
            message=project_description
        )

    except Exception as e:
        print(f"그룹 프로젝트 실행 중 오류: {e}")

# 실행
if __name__ == "__main__":
    run_group_project()
