Architecture Review — Evaluation & Observability v0.1

Project NOAH Architecture Review
Review 대상: Evaluation / Observability / Verification / Tracing Architecture
Review Version: 0.1
Status: Review

1. Review Purpose

Project NOAH의 Agent가 실제로 올바르고 안전하게 행동하고 있는지를 측정하고 검증하기 위한 Evaluation 및 Observability Architecture를 검토한다.

본 Review의 핵심 질문은 다음과 같다.

"NOAH가 제대로 행동하고 있다는 것을 어떻게 증명할 것인가?"

그리고:

Agent가 목표를 달성했는가?
목표를 올바르게 달성했는가?
중간 과정은 안전했는가?
잘못된 Tool을 사용하지 않았는가?
Memory를 잘못 사용하지 않았는가?
권한 정책을 위반하지 않았는가?
실패 원인은 무엇인가?
동일한 실패가 다시 발생하는가?
새로운 Model이나 Capability가 기존보다 좋아졌는가?
장기간 운영할수록 Agent가 실제로 개선되고 있는가?

를 검토한다.

본 문서는 최종 Evaluation System이 아니며, NOAH의 장기 평가·관찰·검증 체계의 후보를 정의한다.

2. Core Architecture Question
Evaluation이란 무엇인가?

초기 정의:

Evaluation은 Agent의 실행이 사전에 정의된 목표·조건·정책·안전 기준을 얼마나 만족했는지를 측정하는 과정이다.

따라서 Evaluation은 단순히:

User
↓
Answer
↓
Correct / Incorrect

가 아니다.

Agent에서는:

Task
↓
Trajectory
↓
Tool Calls
↓
State Changes
↓
Environment Changes
↓
Final Result
↓
Verification
↓
Evaluation

전체를 평가해야 한다.

3. Observability란 무엇인가?

Observability는 시스템 내부에서 무슨 일이 일어났는지를 외부에서 이해할 수 있게 만드는 능력이다.

후보:

Observability
├── Logs
├── Events
├── Traces
├── Metrics
├── State Snapshots
├── Tool Calls
├── Errors
└── Decisions

Evaluation이:

"잘했는가?"

를 묻는다면,

Observability는:

"무슨 일이 일어났는가?"

를 설명한다.

둘은 함께 존재해야 한다.

4. Evaluation vs Observability vs Verification

세 개념은 구분한다.

Observability

무슨 일이 발생했는가?

Verification

실제로 요구된 상태가 되었는가?

Evaluation

그 실행이 얼마나 좋은가?

개념적으로:

Execution
   ↓
Observability
   ↓
Verification
   ↓
Evaluation
5. Completion vs Correctness

Agent가:

"완료했습니다."

라고 말하는 것과 실제 Task가 완료된 것은 다르다.

예:

Agent Claim
"Tests passed"

실제:

Tests
→ failed

따라서 Agent Self-Report를 Source of Truth로 사용하지 않는다.

6. Evidence-Based Completion

Task 완료는 가능한 경우 evidence를 요구한다.

예:

Task
 ↓
Execution
 ↓
Evidence
 ↓
Verification
 ↓
Completion

Evidence 후보:

Test Result
File Diff
Command Output
Database State
API Response
Generated Artifact
External Confirmation
Screenshot
Structured Check

최종 결과가 아니라 검증 가능한 증거를 Completion Contract의 일부로 검토한다.

7. Evaluation Layers

Evaluation을 하나의 점수로 만들지 않는다.

Evaluation
├── Task Success
├── Correctness
├── Safety
├── Reliability
├── Efficiency
├── Cost
├── Latency
├── Process Quality
├── Memory Quality
└── Long-horizon Behavior

2026년 평가 연구에서도 Agent Benchmark는 success만 보는 것보다 safety, robustness, efficiency, process quality 등을 함께 보는 다차원 평가로 확장되고 있다.

8. Task Success

가장 기본적인 평가다.

질문:

목표를 달성했는가?

예:

Task:
README 수정

Success:
README가 요구사항을 만족

단순한 문자열 일치보다 상태 기반 평가를 선호한다.

9. Correctness

성공과 정확성은 동일하지 않다.

예:

Task 완료
하지만
잘못된 코드 변경

따라서 correctness는:

내용
구조
결과
제약조건

을 함께 평가한다.

10. Constraint Compliance

Agent가 목표만 달성하고 다른 규칙을 위반하면 성공으로 보지 않는다.

예:

Goal:
파일 수정

Constraint:
API 파일은 수정하지 말 것

결과:

Goal = Success
Constraint = Violated

→ 전체 결과는 실패 또는 부분 실패.

11. Safety Evaluation

Agent가 목표를 달성하더라도 위험한 방법을 사용했다면 실패다.

예:

Task success
+
Credential leaked
=
Failure

따라서 Safety는 Task Success와 별도 metric으로 유지한다.

12. Process Quality

최종 결과뿐 아니라 과정도 평가한다.

예:

좋은 trajectory
→ 최소한의 Tool
→ 적절한 Context
→ 필요한 검증
→ 안전한 실행

반면:

나쁜 trajectory
→ 불필요한 Tool 호출
→ 잘못된 파일 수정
→ 권한 우회
→ 반복 실패

최종 결과가 같더라도 Process Quality가 다를 수 있다.

13. Trajectory Evaluation

Agent는 multi-turn system이므로 실행 trajectory를 평가 대상에 포함한다.

Trajectory
├── Turn 1
├── Tool Call
├── Observation
├── Turn 2
├── Tool Call
├── Error
├── Recovery
└── Final Result

최근 Agent 평가 연구 역시 short-horizon final-answer 평가만으로는 long-horizon agent의 실제 동작을 충분히 평가하기 어렵다고 지적한다.

14. Trace

모든 중요한 Agent 실행은 Trace로 묶을 수 있어야 한다.

Trace
├── Task
├── Session
├── Agent
├── Turn
├── Context
├── Model
├── Capability
├── Permission
├── State Change
├── Verification
└── Final Result

Trace는 Evaluation과 Debugging의 공통 기반이 된다.

15. Span

Trace 안의 세부 실행 단위를 Span으로 정의하는 것을 검토한다.

예:

Trace
 ├── Agent Turn
 │    ├── Context Build
 │    ├── Model Call
 │    ├── Tool Call
 │    ├── Tool Result
 │    └── Verification

이를 통해 latency와 failure attribution을 세밀하게 분석할 수 있다.

16. Event

모든 중요한 상태 변화를 Event로 기록한다.

후보:

TaskStarted
TaskCompleted

TurnStarted
TurnCompleted

ToolCalled
ToolCompleted
ToolFailed

PermissionRequested
PermissionGranted
PermissionDenied

MemoryRead
MemoryWrite

StateChanged

VerificationStarted
VerificationPassed
VerificationFailed

RecoveryStarted
RecoveryCompleted
17. State Snapshot

실행 중 중요한 시점의 State Snapshot을 보존하는 것을 검토한다.

예:

Checkpoint
├── Task State
├── Execution State
├── Workspace State
├── Context Metadata
└── Memory References

Snapshot은 Recovery뿐만 아니라 Evaluation에도 사용될 수 있다.

18. Context Observability

Context를 단순 문자열로만 기록하지 않는다.

가능한 경우:

Context Trace
├── Source
├── Version
├── Trust
├── Selected
├── Removed
├── Compressed
└── Token Cost

를 기록한다.

이는:

"왜 Agent가 이런 판단을 했는가?"

를 분석하는 데 필요하다.

19. Tool Observability

각 Tool 실행에:

Tool Trace
├── Tool
├── Version
├── Input
├── Permission
├── Approval
├── Start
├── End
├── Output
├── Error
├── Side Effects
└── Verification

을 기록한다.

Capability가 많아질수록 이 정보의 중요성이 증가한다.

20. Memory Observability

Memory도 관찰 대상이 된다.

예:

Memory Read
├── Query
├── Retrieved Items
├── Ranking
├── Source
└── Context Projection

Memory Write
├── Candidate
├── Reason
├── Source
├── Confidence
└── Validation

이 구조를 통해:

"왜 이 Memory를 사용했는가?"

를 추적할 수 있다.

21. Permission Observability

Permission 결정도 Trace에 포함한다.

Permission Decision
├── Agent
├── Capability
├── Resource
├── Risk
├── Policy
├── Result
├── Approver
└── Scope

Security Review와 직접 연결된다.

22. Failure Attribution

실패가 발생하면 단순히:

Task Failed

라고 기록하지 않는다.

가능한 원인:

Failure
├── Model
├── Context
├── Memory
├── Tool
├── Permission
├── Environment
├── External Service
├── Planning
├── Verification
└── Human Decision

를 분리한다.

AI Harness Engineering 연구에서도 failure attribution을 harness의 핵심 책임 중 하나로 다룬다.

23. Failure Taxonomy

예:

Model Failure
→ reasoning / generation failure

Context Failure
→ missing / misleading context

Memory Failure
→ wrong retrieval / stale memory

Tool Failure
→ execution failure

Policy Failure
→ incorrect permission decision

Environment Failure
→ unavailable resource

Verification Failure
→ result not verifiable

Recovery Failure
→ unable to continue

이 분류는 이후 개선 대상을 결정하는 데 사용한다.

24. Evaluation Granularity

평가는 여러 수준에서 가능해야 한다.

Micro
→ Tool

Meso
→ Turn

Macro
→ Task

Long-term
→ Session / User / Agent lifetime

하나의 metric으로 모든 수준을 평가하지 않는다.

25. Model Evaluation

Model 변경 시:

Model A
vs
Model B

를 같은 Harness에서 비교한다.

평가:

Success
Correctness
Safety
Cost
Latency
Tool Efficiency

를 함께 측정한다.

Anthropic 역시 새 Model이 제품 성능을 실제로 개선했는지를 Agent-level eval로 확인하는 것이 중요하다고 강조한다.

26. Harness Evaluation

Model만 바뀌는 것이 아니다.

Harness가 바뀔 수도 있다.

Harness V1
vs
Harness V2

비교:

Context
Tool Routing
Memory
Verification
Cost
Recovery

최근 연구 역시 agent 성능이 모델만이 아니라 model–harness–environment system의 결과라는 관점을 강조한다.

27. Capability Evaluation

Tool / Skill / Workflow도 독립 평가한다.

예:

Skill
→ discovery
→ compliance
→ execution
→ boundary
→ outcome

Skill을 사용할 줄 아는 것과 Skill을 제대로 수행하는 것은 구분한다.

28. Memory Evaluation

Memory는:

Recall
Precision
Freshness
Contradiction
Forgetting
Task Utility

등으로 평가한다.

예:

Old Memory
↓
Current Fact changed
↓
Agent should not use obsolete fact

처럼 temporal correctness까지 포함한다.

29. Long-Horizon Evaluation

NOAH의 장기 목표상 가장 중요한 평가 영역 중 하나다.

단기:

5 steps

와:

100 steps

의 신뢰성은 다를 수 있다.

Long-horizon 평가에는:

Goal Persistence
State Consistency
Recovery
Memory Usage
Tool Efficiency
Error Accumulation
Safety

를 포함한다.

2026년 benchmark review도 20+ step을 장기 horizon으로 보고, 정적인 benchmark보다 interactive / stochastic environment에서의 평가가 필요하다고 지적한다.

30. Open-World Evaluation

정해진 benchmark만으로는 부족할 수 있다.

Princeton SAgE 연구 그룹은 frontier Agent 평가에서 open-world, long-horizon real-world task가 전통적인 benchmark를 보완해야 한다는 방향을 연구하고 있다.

NOAH도 장기적으로:

Synthetic Eval
+
Controlled Eval
+
Real-world Eval

을 결합하는 방향을 검토한다.

31. Regression Evaluation

새로운 변경이 과거 기능을 깨뜨리지 않았는지 확인한다.

Change
 ↓
Regression Suite
 ↓
Compare
 ↓
Pass / Fail

대상:

Model
Prompt
Context
Memory
Tool
Skill
Runtime
Security Policy

모두 가능하다.

32. Continuous Evaluation

Evaluation을 Release 시점에만 하지 않는다.

Development
 ↓
CI Evaluation
 ↓
PoC Evaluation
 ↓
Staging
 ↓
Production / Real Use
 ↓
Continuous Monitoring

Evaluation을 Development Lifecycle에 포함한다.

Anthropic 역시 Agent eval을 개발 과정 초기에 통합해 production에서만 실패를 발견하는 reactive loop를 피할 것을 강조한다.

33. CI Evaluation Gates

품질이 일정 수준 이하로 내려가면 Merge / Deploy를 차단할 수 있다.

예:

Task Success >= threshold
Safety = 100%
Regression = 0 critical
Cost <= budget
Latency <= limit

최근 readiness-harness 연구도 evaluation과 observability를 CI quality gate와 결합해 unsafe regression을 배포 전에 차단하는 방향을 보여준다.

34. Evaluation Dataset

Evaluation Dataset은 실제 실패를 통해 성장해야 한다.

Production Failure
 ↓
Sanitize
 ↓
Evaluation Case
 ↓
Regression Suite

즉:

실패가 버려지는 것이 아니라 다음 버전을 검증하는 자산이 된다.

35. Failure Replay

가능한 경우 과거 실패를 다시 실행할 수 있어야 한다.

Failed Trace
 ↓
Replay
 ↓
New Model / Harness
 ↓
Compare

이 기능은:

Debugging
Regression
Model Comparison
Harness Optimization

에 활용된다.

36. Deterministic vs Stochastic Evaluation

LLM Agent는 완전히 deterministic하지 않다.

따라서:

Deterministic Check
+
Repeated Runs

을 함께 고려해야 한다.

예:

Test A
10 runs
→ 9 success
→ 1 failure

단일 실행 결과만으로 Agent 품질을 판단하지 않는다.

37. Evaluation Confidence

결과에 confidence를 부여할 수 있다.

Evaluation
├── Score
├── Sample Count
├── Variance
├── Confidence
└── Evidence

특히 stochastic Agent에서는 중요하다.

38. Judge / Evaluator

Evaluation에는 evaluator가 필요하다.

후보:

Rule-based
Code-based
Model-based
Human-based
Environment-based

하나에 의존하지 않는다.

예:

Code Test
+
Rule Check
+
LLM Judge
+
Human Review

를 조합할 수 있다.

39. LLM-as-Judge

LLM Judge는 유용하지만 Source of Truth로 취급하지 않는다.

문제:

evaluator bias
evaluator hallucination
correlated failures
instruction sensitivity

때문이다.

따라서 가능하면:

Objective Evidence
>
Deterministic Test
>
Structured Evaluator
>
LLM Judge

순으로 신뢰하는 구조를 검토한다.

40. Verification Hierarchy

후보:

Level 0
Self Report

Level 1
LLM Judge

Level 2
Rule-based Verification

Level 3
Execution Evidence

Level 4
Environment State Verification

Level 5
Independent Verification

중요한 Task일수록 높은 수준의 Verification을 사용한다.

41. Independent Auditor

장기적으로 Agent가 실행하고 별도의 Auditor/Verifier가 검증하는 구조도 검토할 수 있다.

Agent
 ↓
Execute
 ↓
Independent Auditor
 ↓
Pass / Fail

이는 Agent 자체의 self-reporting bias를 줄일 수 있다.

일부 최신 long-horizon harness 연구도 executor와 auditor를 분리하는 구조를 제안한다.

42. Evidence Package

하나의 Agent Run을 재현 가능한 package로 저장하는 것을 검토한다.

Episode
├── Task
├── Initial State
├── Context Metadata
├── Model
├── Agent
├── Tools
├── Permissions
├── Actions
├── Observations
├── State Changes
├── Errors
├── Recovery
├── Evidence
├── Verification
└── Final Outcome

AI Harness Engineering 연구의 auditable episode package 개념과 직접 연결되는 후보 구조다.

43. Cost Observability

Agent 비용은 Token만이 아니다.

Cost
├── Input Tokens
├── Output Tokens
├── Tool Calls
├── Sandbox Runtime
├── Compute
├── Storage
├── Network
└── Human Review

최근 harness 연구에서도 orchestration 설계가 token economics에 큰 영향을 미칠 수 있다고 분석한다.

44. Efficiency Metrics

효율성은:

Task Success / Cost
Task Success / Time
Task Success / Tool Calls

등의 방식으로 볼 수 있다.

하지만 단순히 적은 Token을 사용하는 것이 좋은 것은 아니다.

필요한 비용으로 안정적으로 성공하는 것

을 목표로 한다.

45. Quality vs Cost Frontier

Agent 설정은 하나의 최적점이 아니라 여러 trade-off를 가진다.

Quality
  ↑
  │       ●
  │    ●
  │  ●
  │●
  └────────────→ Cost

따라서 Model / Harness / Memory configuration을 Pareto frontier 관점에서 비교할 수 있다.

최근 readiness harness 연구도 품질·비용·지연 등을 하나의 숫자로 억지로 합치기보다 Pareto frontier를 사용하는 방향을 제안한다.

46. Observability Data Retention

모든 Trace를 영원히 저장하면 비용이 커진다.

후보:

Critical
→ Full Trace

Normal
→ Summary Trace

Low-value
→ Metrics only

또는 중요도에 따라 retention policy를 적용한다.

47. Privacy-aware Observability

Trace에 민감정보가 포함될 수 있다.

예:

User Message
Credential
Private File
Memory
Personal Data

따라서 Observability에도:

Redaction
Access Control
Retention
Encryption

이 필요하다.

48. Explainability

NOAH가 중요 결정을 했을 때:

왜 그렇게 결정했는가?

를 가능한 범위에서 설명할 수 있어야 한다.

다만 내부 CoT를 저장/노출하는 것과 결정 근거를 제공하는 것은 다른 문제다.

NOAH가 저장해야 할 후보:

Decision Evidence
├── Relevant Context
├── Policy
├── Capability
├── Tool Result
├── Verification
└── Outcome
49. Learning From Evaluation

Evaluation 결과는 버리지 않는다.

Evaluation Failure
 ↓
Failure Analysis
 ↓
Lesson
 ↓
Memory
 ↓
Harness / Skill / Policy Improvement
 ↓
New Evaluation

이 구조가 NOAH의 장기 Self-Improvement loop 후보가 된다.

50. Evaluation-driven Development

Development Cycle 자체에 Evaluation을 넣는다.

Research
 ↓
Design
 ↓
Implementation
 ↓
Evaluation
 ↓
Failure Analysis
 ↓
Iteration

이는 지금 우리가 NOAH를 만드는 Development Workflow와도 연결된다.

51. Evaluation Levels

NOAH에서는 평가를 다음 네 수준으로 나누는 것을 검토한다.

L1 Component
Tool / Skill / Memory

L2 Agent
Agent behavior

L3 Task
Task completion

L4 System
Long-term user-level behavior
52. System-level Evaluation

최종적으로 NOAH 전체를 평가해야 한다.

예:

User
 ↓
Task
 ↓
Agent
 ↓
Memory
 ↓
Tools
 ↓
Runtime
 ↓
Environment
 ↓
Outcome

System Evaluation은 단일 Agent score보다 훨씬 복잡하다.

53. Personal AI Evaluation

NOAH는 일반 Coding Agent와 달리 Personal AI이므로:

Personalization
Trust
Memory usefulness
Continuity
Consistency
Respect for user intent
Autonomy appropriateness

도 평가해야 한다.

예:

NOAH가 사용자의 과거 선호를 기억했는가?

보다:

기억한 선호를 현재 상황에 적절하게 적용했는가?

가 더 중요하다.

54. Longitudinal Evaluation

NOAH가 몇 개월 또는 몇 년 동안 운영된다면:

Day 1
↓
Month 1
↓
Month 6
↓
Year 1

의 변화를 평가해야 한다.

평가:

Memory Quality
Trust
Consistency
Adaptability
Failure Rate
Safety
Personalization
55. Drift Detection

Model / Memory / Skill / User / Environment가 변하면 시스템의 behavior도 바뀐다.

Drift
├── Model Drift
├── Prompt Drift
├── Memory Drift
├── Skill Drift
├── Policy Drift
├── Environment Drift
└── User Preference Drift

NOAH는 이러한 Drift를 감지하는 구조를 장기적으로 검토한다.

56. Canary Evaluation

새로운 Model / Skill / Harness를 모든 사용자에게 즉시 적용하지 않는 방향을 검토한다.

New Version
 ↓
Canary
 ↓
Evaluation
 ↓
Compare
 ↓
Expand / Rollback

Personal AI인 NOAH에서도 Runtime을 크게 바꾸는 경우 유용하다.

57. Benchmark Limitations

Benchmark score가 실제 성능을 완전히 표현하지 못할 수 있다.

문제:

benchmark overfitting
contamination
static environment
limited horizon
synthetic tasks
missing safety
missing process quality

최근 comprehensive benchmark review 역시 benchmark 성능과 실제 deployment 사이의 gap을 주요 문제로 지적한다.

58. Evaluation Environment

Evaluation Environment도 통제해야 한다.

Model
+
Harness
+
Tools
+
Sandbox
+
Dataset
+
Environment

중 하나라도 달라지면 결과가 달라질 수 있다.

따라서 Evaluation은 가능한 경우 환경 version을 포함해야 한다.

59. Reproducibility

Evaluation 결과를 재현할 수 있어야 한다.

필요 정보:

Model Version
Harness Version
Prompt / Instruction Version
Tool Version
Skill Version
Memory Snapshot
Environment
Dataset
Seed where applicable
60. Experiment Tracking

실험마다:

Experiment
├── Hypothesis
├── Configuration
├── Dataset
├── Environment
├── Runs
├── Metrics
├── Failures
└── Conclusion

을 기록할 수 있어야 한다.

이는 NOAH의 Research → PoC → Evaluation workflow와 연결된다.

61. Model Comparison

Model을 교체할 때:

Same Task
Same Harness
Same Memory
Same Capability

조건에서 비교하는 것을 기본으로 한다.

그래야:

"Model이 좋아졌다."

와:

"Harness가 좋아졌다."

를 구분할 수 있다.

62. Harness Comparison

반대로:

Same Model
Same Task
Same Capability

조건에서 Harness를 비교한다.

이는 NOAH의 핵심 연구 방향이 될 수 있다.

최근 연구 역시 model scaling만큼 harness/system scaling이 중요해질 수 있다고 주장한다.

63. Evaluation Matrix

후보:

Dimension	Measure
Success	Task completion
Correctness	Requirement satisfaction
Safety	Policy violations
Reliability	Repeat success
Efficiency	Tool / token / time
Cost	Resource usage
Memory	Retrieval utility
Recovery	Failure recovery
Process	Trajectory quality
Trust	User confidence
Long-term	Longitudinal performance
64. Candidate Evaluation Architecture
                         NOAH EVALUATION
                               │
                           Observability
                               │
              ┌────────────────┼────────────────┐
              │                │                │
            Trace            Events           Metrics
              │                │                │
              └────────────────┼────────────────┘
                               │
                         Evidence Package
                               │
                     ┌─────────┴─────────┐
                     │                   │
                 Verification          Judge
                     │                   │
                     └─────────┬─────────┘
                               │
                           Evaluation
                               │
              ┌────────────────┼────────────────┐
              │                │                │
           Success          Safety           Cost
              │                │                │
              └────────────────┼────────────────┘
                               │
                         Failure Analysis
                               │
                         Learning / Memory
                               │
                       Harness Improvement
65. Evaluation Contract

모든 중요한 Task가 최소한 다음을 정의하도록 하는 방향을 검토한다.

Evaluation Contract
├── Goal
├── Success Criteria
├── Constraints
├── Evidence Requirements
├── Safety Requirements
├── Cost Budget
├── Time Budget
└── Failure Conditions

이 계약이 있으면 Agent가 "잘했다"는 기준을 실행 전에 정의할 수 있다.

66. Verification Contract

Evaluation과 별도로 Verification 조건을 정의할 수 있다.

Verification Contract
├── Preconditions
├── Postconditions
├── Evidence
├── Invariants
└── External Confirmation
67. Reward vs Evaluation

Evaluation Score를 곧바로 Agent reward로 사용하지 않는다.

Evaluation
= 시스템 품질 측정

Reward
= 학습 신호

이 둘을 섞으면 잘못된 proxy optimization이 발생할 수 있다.

NOAH에서는 초기에는 Evaluation과 Learning Signal을 분리한다.

68. Goodhart Risk

Agent가 metric을 최적화하면서 실제 목적을 놓칠 수 있다.

예:

Metric:
→ minimize tool calls

Agent:
→ tool을 충분히 사용하지 않음

또는:

Metric:
→ maximize task success

Agent:
→ unsafe shortcuts

따라서 Evaluation은 하나의 metric에 의존하지 않는다.

69. Multi-objective Evaluation

NOAH의 평가 목적은:

Success
+
Safety
+
Correctness
+
Efficiency
+
Trust
+
Long-term Utility

의 균형으로 보는 방향을 검토한다.

70. Evaluation Governance

Evaluation 기준 자체도 변경될 수 있다.

따라서:

Evaluation Spec v1
Evaluation Spec v2

를 versioning하고 중요한 변경을 기록한다.

Evaluation의 변화도 Agent 성능 변화의 원인이 될 수 있기 때문이다.

71. Security Evaluation

Permission & Security Review와 연결된다.

Security Evaluation:

Prompt Injection
Tool Poisoning
Memory Poisoning
Credential Leakage
Privilege Escalation
Sandbox Escape

를 정기적으로 검사한다.

72. Memory Evaluation

Memory Review와 연결된다.

Recall
Freshness
Contradiction
Forgetting
Provenance
Utility

를 평가한다.

73. Capability Evaluation

Capability Review와 연결된다.

Tool correctness
Skill compliance
Workflow completion
Protocol reliability
Agent delegation

을 평가한다.

74. Runtime Evaluation

Session / Runtime Review와 연결된다.

Recovery
Pause / Resume
Cancellation
Retry
Persistence
State consistency

를 평가한다.

75. Evaluation Feedback Loop

NOAH의 장기 발전 방향:

Execution
 ↓
Trace
 ↓
Evaluation
 ↓
Failure Attribution
 ↓
Lesson
 ↓
Memory
 ↓
Policy / Skill / Harness Improvement
 ↓
New Execution

이것이 NOAH의 핵심 self-improvement architecture 후보 중 하나다.

76. Future Resilience

Evaluation Architecture는 향후 어떤 Model이나 Agent Framework가 등장해도 유지될 수 있어야 한다.

Specific Benchmark
        ↓
Replaceable

Evaluation Contract
        ↓
Stable

즉 특정 Model output format에 종속된 평가보다:

Goal
Evidence
Outcome
Policy
State
Trajectory

를 중심으로 평가한다.

77. Candidate Decisions
주제	초기 판단
Observability 독립 계층	Adopt
Trace	Adopt
Event	Adopt
Evidence Package	Adopt
Verification ≠ Evaluation	Adopt
Task-level Evaluation	Adopt
Trajectory Evaluation	Adopt
Long-horizon Evaluation	Adopt
Safety Evaluation	Adopt
Cost / Latency Evaluation	Adopt
Memory Evaluation	Adopt
Capability Evaluation	Adopt
Runtime Evaluation	Adopt
Model Comparison	Adopt
Harness Comparison	Adopt
Regression Evaluation	Adopt
CI Quality Gates	Adapt
Open-world Evaluation	Research Further
Independent Auditor	Research Further
LLM-as-Judge	Adapt
Deterministic Verification	Adopt
Continuous Evaluation	Adopt
Longitudinal Evaluation	Research Further
Drift Detection	Research Further
Canary Evaluation	Research Further
Reward = Evaluation	Reject
Single Metric Optimization	Reject
78. What NOAH Should Not Do
Final Answer Only

Reject.

Single Score

Reject.

LLM Judge Only

Reject.

Offline Benchmark Only

Reject.

Log Everything Forever

Reject.

Evaluation Only After Failure

Reject.

Metric = Goal

Reject.

Model Evaluation Without Harness

Reject.

Harness Evaluation Without Environment

Reject.

79. Risks
Observability Overhead

Trace가 커지면 storage와 latency가 증가할 수 있다.

Evaluation Cost

장기 Agent를 여러 번 실행하면 비용이 빠르게 증가할 수 있다.

Judge Bias

LLM Judge가 잘못된 평가를 할 수 있다.

Benchmark Overfitting

Agent가 benchmark만 잘하도록 최적화될 수 있다.

Metric Gaming

Agent/Harness가 측정 지표를 최적화하면서 실제 사용자 가치가 감소할 수 있다.

Privacy

Trace와 Evaluation 데이터에 민감한 정보가 포함될 수 있다.

False Confidence

높은 benchmark score가 실제 품질을 보장하지 않을 수 있다.

80. Open Questions
NOAH의 최소 Trace 단위는 무엇인가?
모든 Agent 실행을 Full Trace로 보존해야 하는가?
Evidence Package의 최소 Schema는 무엇인가?
Evaluation Contract는 Task 생성 시 만들어야 하는가?
Verification은 Agent 내부에서 수행하는가, 외부 Auditor가 수행하는가?
LLM Judge를 어디까지 허용할 것인가?
Agent trajectory를 어떤 수준까지 저장할 것인가?
Cost와 Quality를 어떻게 비교할 것인가?
Long-horizon Task를 몇 단계부터 장기 작업으로 분류할 것인가?
어떤 실패를 Regression Test로 승격할 것인가?
Production Trace를 Evaluation Dataset으로 사용할 때 개인정보를 어떻게 제거할 것인가?
Memory quality를 Task success와 어떻게 연결할 것인가?
Harness 변경과 Model 변경의 영향을 어떻게 분리할 것인가?
Evaluation spec 자체의 변경을 어떻게 기록할 것인가?
Agent가 평가 결과를 자기 개선에 직접 사용할 수 있게 할 것인가?
자동 Self-improvement가 Evaluation Gaming으로 이어지는 것을 어떻게 막을 것인가?
81. Current Recommendation

현재까지의 Research를 종합하면:

NOAH는 Agent의 최종 응답만 평가하지 않는다.

대신:

Task
 ↓
Trajectory
 ↓
State Changes
 ↓
Tool Usage
 ↓
Verification
 ↓
Evidence
 ↓
Outcome

전체를 평가한다.

그리고 Observability를:

Evaluation의 입력이 되는 실행 증거 시스템

으로 취급한다.

82. Long-term Feedback Architecture

NOAH의 장기 목표와 연결하면:

Execution
   ↓
Observation
   ↓
Evaluation
   ↓
Failure Attribution
   ↓
Experience
   ↓
Memory
   ↓
Learning
   ↓
Skill / Policy / Harness Improvement
   ↓
Future Execution

이 구조를 핵심 장기 Architecture 후보로 둔다.

즉 NOAH가 단순히:

"대답을 잘하는 AI"

에서 끝나는 것이 아니라,

"자신의 행동 결과를 관찰하고, 실패를 이해하고, 경험을 축적하고, 다음 실행을 더 좋게 만드는 시스템"

으로 발전할 수 있는 기반을 만든다.

단, 자동 Self-Modification은 현재 단계에서는 확정하지 않는다.

83. Future Resilience

현재 Benchmark나 Evaluation Framework가 바뀌더라도 다음 계약은 유지할 수 있어야 한다.

Evaluation Contract
├── Goal
├── Evidence
├── Outcome
├── Constraints
├── Verification
└── Metrics

구체적인 evaluator나 benchmark는 교체 가능하게 한다.

84. Review Boundary

이번 Review에서는 다음을 최종 결정하지 않는다.

최종 Trace Schema
최종 Telemetry Stack
최종 Evaluation Framework
OpenTelemetry 적용 여부
LLM Judge 모델
Benchmark Suite
Production Monitoring Stack
Automated Self-improvement
Longitudinal Evaluation Infrastructure

이들은 후속 Specification과 PoC에서 검증한다.

85. Review Outcome

현재까지의 Research를 종합하면:

Observability
= What happened?

Verification
= Did the required state actually occur?

Evaluation
= How good was the behavior?

Learning
= What should change next?

의 네 가지 경계를 유지하는 것이 유력하다.

그리고:

Execution
 ↓
Trace
 ↓
Evidence
 ↓
Verification
 ↓
Evaluation
 ↓
Failure Analysis
 ↓
Experience
 ↓
Improvement

의 Feedback Loop를 NOAH의 장기 Architecture 후보로 둔다.

이는 현재 Agent 연구의 중요한 방향과도 맞는다. Anthropic은 Agent eval을 multi-turn behavior와 intermediate state까지 포함하는 문제로 보고 있고, AI Harness Engineering 연구는 run 전체를 auditable episode로 평가하는 방향을 제안하며, 최근 연구는 harness 자체의 설계가 비용과 성능을 좌우할 수 있다고 본다.

86. Next Step

이번 Review 후 바로 Evaluation 시스템을 구현하지 않는다.

다음 순서:

Evaluation & Observability Review
          ↓
Open Questions
          ↓
추가 Research
          ↓
DDR
          ↓
02-Architecture
          ↓
Evaluation PoC
          ↓
Integration

다음 Architecture Review에서는:

Orchestration & Multi-Agent

를 검토한다.

특히:

Agent
 ↓
Delegation
 ↓
Subagent
 ↓
Parallel Execution
 ↓
Shared / Isolated Context
 ↓
Result Aggregation
 ↓
Verification

의 경계를 정의한다.