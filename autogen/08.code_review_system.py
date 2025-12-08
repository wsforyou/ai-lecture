from autogen import GroupChat, GroupChatManager, AssistantAgent, UserProxyAgent

class CodeReviewSystem:
    """다중 에이전트 코드 리뷰 시스템"""

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

    def __init__(self):
        self.setup_review_agents()

    def setup_review_agents(self):
        """코드 리뷰 전문 에이전트들 설정"""

        # 보안 리뷰어
        self.security_reviewer = AssistantAgent(
            name="security_specialist",
            system_message="""당신은 보안 전문가입니다.
            코드의 보안 취약점을 찾아 제거하는 것이 주 임무입니다.

            검토 항목:
            1. SQL Injection 방지
            2. XSS 방지
            3. 인증/인가 검증
            4. 입력 데이터 검증
            5. 민감 정보 노출 방지
            6. 암호화 적용 여부

            OWASP Top 10 기준으로 검토해주세요.
            """,
            llm_config=self.llm_config,
        )

        # 성능 리뷰어
        self.performance_reviewer = AssistantAgent(
            name="performance_specialist",
            system_message="""당신은 성능 최적화 전문가입니다.
            코드의 성능 이슈를 찾아 개선 방안을 제시합니다.

            검토 항목:
            1. 알고리즘 복잡도
            2. 데이터베이스 쿼리 최적화
            3. 메모리 사용량
            4. 캐싱 전략
            5. 비동기 처리 가능성
            6. 리소스 누수 방지

            구체적인 성능 개선 코드를 제공해주세요.
            """,
            llm_config=self.llm_config,
        )

        # 아키텍처 리뷰어
        self.architecture_reviewer = AssistantAgent(
            name="architecture_specialist",
            system_message="""당신은 소프트웨어 아키텍처 전문가입니다.
            코드의 구조적 품질을 평가합니다.

            검토 항목:
            1. SOLID 원칙 준수
            2. 디자인 패턴 적용
            3. 모듈화 및 결합도
            4. 확장성 및 유지보수성
            5. 레이어 분리
            6. 의존성 관리

            리팩토링 제안을 포함해주세요.
            """,
            llm_config=self.llm_config,
        )

        # 코드 품질 리뷰어
        self.quality_reviewer = AssistantAgent(
            name="quality_specialist",
            system_message="""당신은 코드 품질 전문가입니다.
            코드의 가독성과 유지보수성을 평가합니다.

            검토 항목:
            1. 네이밍 컨벤션
            2. 코드 중복 제거
            3. 메서드 길이 및 복잡도
            4. 주석 및 문서화
            5. 예외 처리
            6. 코딩 스타일 일관성

            클린 코드 원칙을 기준으로 검토해주세요.
            """,
            llm_config=self.llm_config,
        )

        # 리뷰 통합자
        self.review_coordinator = UserProxyAgent(
            name="review_coordinator",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2,
            code_execution_config=False
        )

    def comprehensive_review(self, code_content):
        """종합적인 코드 리뷰 수행"""

        print("=== 멀티 에이전트 코드 리뷰 시작 ===")

        review_results = {}

        # 각 전문가별 리뷰 수행
        reviewers = [
            ("보안", self.security_reviewer),
            ("성능", self.performance_reviewer),
            ("아키텍처", self.architecture_reviewer),
            ("품질", self.quality_reviewer)
        ]

        for review_type, reviewer in reviewers:
            print(f"\n{review_type} 리뷰 진행 중...")

            review_prompt = f"""
다음 코드를 {review_type} 관점에서 리뷰해주세요:
'''
{code_content}
'''

구체적인 개선 제안과 수정 코드를 포함해주세요.
            """

            try:
                result = self.review_coordinator.initiate_chat(
                    reviewer,
                    message=review_prompt,
                    max_turns=2
                )
                review_results[review_type] = result

            except Exception as e:
                print(f"{review_type} 리뷰 중 오류: {e}")
                review_results[review_type] = f"리뷰 실패: {e}"

        # 종합 리뷰 결과 생성
        self.generate_final_report(review_results)

        return review_results

    def generate_final_report(self, review_results):
        """최종 리뷰 보고서 생성"""

        print("\n=== 종합 리뷰 보고서 ===")

        for review_type, result in review_results.items():
            print(f"\n【{review_type} 리뷰 결과】")
            print("-" * 30)
            # 결과 요약 출력 (실제로는 result 파싱 필요)
            print(f"{review_type} 리뷰가 완료되었습니다.")

        print("\n=== 리뷰 완료 ===")

# 리뷰 시스템 사용 예시
def run_code_review_system():
    """코드 리뷰 시스템 실행 예시"""

    review_system = CodeReviewSystem()

    sample_code = """
@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<User> getUser(@PathVariable String id) {
        User user = userService.findById(id);
        if (user != null) {
            return ResponseEntity.ok(user);
        }
        return ResponseEntity.notFound().build();
    }

    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody User user) {
        User savedUser = userService.save(user);
        return ResponseEntity.ok(savedUser);
    }

    @GetMapping
    public List<User> getAllUsers() {
        return userService.findAll();
    }
}
    """

    try:
        review_system.comprehensive_review(sample_code)

    except Exception as e:
        print(f"코드 리뷰 시스템 실행 중 오류: {e}")

if __name__ == "__main__":
    run_code_review_system()
