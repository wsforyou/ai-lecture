from autogen import AssistantAgent, UserProxyAgent

class CodeGenerationPipeline:
    """코드 생성을 위한 전문화된 파이프라인"""
    config_list_azure = [
        {
            "model": "gpt-4o",
            "api_key": "", # 실제 키 사용 시 주의
            "base_url": "https://api.openai.com/v1"
        },
    ]
    llm_config = {
        "cache_seed": None, # 임의의 시드값
        "temperature": 0.8, # LLM 응답의 다양성 제어
        "config_list" : config_list_azure
    }

    def __init__(self):
        self.setup_agents()

    def setup_agents(self):

        # 실행 에이전트
        self.executor = UserProxyAgent(
            name="code_executor",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=3,
            code_execution_config={
                "work_dir": "./workspace",
                "use_docker": False,
                "timeout": 120,
                "last_n_messages": 5,
            },
        )

    def generate_code(self, requirements):
        """코드 생성 파이프라인 실행"""

        print("=== 코드 생성 파이프라인 시작 ===")

        # 각 단계별로 별도 에이전트 생성하되 컨텍스트 주입
        accumulated_context = f"=== 프로젝트 요구사항 ===\n{requirements}\n\n"

        # 1단계: 요구사항 분석
        print("\n1단계: 요구사항 분석")
        analyst = self._create_context_agent("requirements_analyst", accumulated_context)

        stage1_result = self.executor.initiate_chat(
            analyst,
            message="요구사항 분석을 수행해주세요.",
            max_turns=2
        )

        stage1_content = self._extract_response_content(stage1_result)
        accumulated_context += f"=== 1단계: 요구사항 분석 결과 ===\n{stage1_content}\n\n"

        # 2단계: 아키텍처 설계
        print("\n2단계: 아키텍처 설계")
        architect = self._create_context_agent("system_architect", accumulated_context)

        stage2_result = self.executor.initiate_chat(
            architect,
            message="앞의 요구사항 분석을 바탕으로 시스템 아키텍처를 설계해주세요.",
            max_turns=2
        )

        stage2_content = self._extract_response_content(stage2_result)
        accumulated_context += f"=== 2단계: 아키텍처 설계 결과 ===\n{stage2_content}\n\n"

        # 3단계: 코드 구현
        print("\n3단계: 코드 구현")
        coder = self._create_context_agent("senior_developer", accumulated_context)

        stage3_result = self.executor.initiate_chat(
            coder,
            message="""앞의 설계를 바탕으로 완전한 코드를 구현해주세요.
            소스코드는 간단해야 합니다.
            실행을 위한 Python 가상환경은 만들지 않습니다.
            """,
            max_turns=2
        )

        stage3_content = self._extract_response_content(stage3_result)
        accumulated_context += f"=== 3단계: 코드 구현 결과 ===\n{stage3_content}\n\n"

        # 4단계: 코드 리뷰
        print("\n4단계: 코드 리뷰")
        reviewer = self._create_context_agent("code_reviewer", accumulated_context)

        stage4_result = self.executor.initiate_chat(
            reviewer,
            message="구현된 코드를 리뷰하고 개선점을 제시해주세요.",
            max_turns=2
        )

        stage4_content = self._extract_response_content(stage4_result)
        accumulated_context += f"=== 4단계: 코드 리뷰 결과 ===\n{stage4_content}\n\n"

        # 5단계: 테스트 작성
        print("\n5단계: 테스트 작성")
        tester = self._create_context_agent("test_engineer", accumulated_context)

        stage5_result = self.executor.initiate_chat(
            tester,
            message="최종 코드에 대한 포괄적인 테스트케이스를 작성해주세요.",
            max_turns=2
        )

        print("\n=== 컨텍스트 주입 방식 완료 ===")

        return {
            "analysis": stage1_result,
            "design": stage2_result,
            "code": stage3_result,
            "review": stage4_result,
            "tests": stage5_result,
            "full_context": accumulated_context
        }

    def _create_context_agent(self, role: str, context: str):
        """컨텍스트가 주입된 에이전트 생성"""

        role_prompts = {
            "requirements_analyst": """당신은 소프트웨어 요구사항 분석 전문가입니다.
            주어진 컨텍스트를 바탕으로 요구사항을 분석합니다.""",

            "system_architect": """당신은 시스템 아키텍트입니다.
            주어진 요구사항 분석 결과를 바탕으로 시스템 아키텍처를 설계합니다.""",

            "senior_developer": """당신은 10년 경력의 시니어 개발자입니다.
            주어진 설계를 바탕으로 완전한 코드를 구현합니다.
            """,

            "code_reviewer": """당신은 코드 리뷰 전문가입니다.
            주어진 코드를 검토하고 개선점을 제시합니다.""",

            "test_engineer": """당신은 테스트 엔지니어입니다.
            주어진 코드에 대한 포괄적인 테스트를 작성합니다."""
        }

        system_message = f"""
        {role_prompts.get(role, "전문가")}

        === 현재까지의 프로젝트 컨텍스트 ===
        {context}

        위 컨텍스트를 바탕으로 작업을 수행해주세요.
        이전 단계의 결과를 반드시 참고하여 일관성 있는 결과를 제공하세요.
        """

        return AssistantAgent(
            name=role,
            system_message=system_message,
            llm_config=self.llm_config
        )

    def _extract_response_content(self, chat_result):
        """채팅 결과에서 응답 내용 추출"""
        try:
            if hasattr(chat_result, 'chat_history') and chat_result.chat_history:
                # 가장 마지막 AI 응답 찾기
                for message in reversed(chat_result.chat_history):
                    if message.get('role') == 'assistant':
                        return message.get('content', '')
            return str(chat_result)
        except:
            return str(chat_result)

# 파이프라인 사용 예시
def run_code_generation_pipeline():
    """코드 생성 파이프라인 실행 예시"""

    pipeline = CodeGenerationPipeline()

    sample_requirements = """
    KT 내부 직원용 간단한 할일 관리 시스템을 개발해주세요.

    기능 요구사항:
    1. 사용자 인증 (로그인/로그아웃)
    2. 할일 CRUD (생성, 조회, 수정, 삭제)
    3. 할일 카테고리 분류
    4. 마감일 설정 및 알림
    5. 할일 상태 관리 (대기, 진행중, 완료)
    6. 간단한 대시보드

    기술 요구사항:
    - Language : Python
    - Backend: Fast Api
    - Database: H2 (개발용)
    - API: RESTful API
    - Operation System: Linux

    비기능 요구사항:
    - 응답시간 < 200ms
    - 동시 사용자 100명 지원
    - 보안 등급: 중간
    """

    try:
        results = pipeline.generate_code(sample_requirements)
        print("\n파이프라인 실행이 완료되었습니다.")

    except Exception as e:
        print(f"파이프라인 실행 중 오류: {e}")

if __name__ == "__main__":
    run_code_generation_pipeline()
