# Architecture Integration Review

> Project NOAH Architecture Review
> Review 대상: 전체 Architecture Integration
> Review Version: 0.3
> Status: Review

---

# 1. Review Purpose

v0.2 이후 수행한 P1 Research 결과를 전체 Architecture에 반영한다.

이번 Review의 핵심 질문:

> "현재까지의 Research를 반영했을 때 NOAH의 핵심 Architecture Boundary와 Contract가 충분히 안정되었는가?"

이번 단계에서는 새로운 개념을 무분별하게 추가하지 않는다.

---

# 2. Research Inputs

이번 Integration에 반영되는 Research:

## P0

- Task State / Runtime Boundary
- Harness Boundary
- Memory / Knowledge Boundary

## P1

- Artifact Architecture
- Identity Persistence
- Orchestration Contract

---

# 3. Architecture Inventory

현재 핵심 Architecture 영역:

Identity
Agent
Task
Session
Orchestration
Harness
Context
State
Memory
Knowledge
Artifact
Capability
Policy
Permission
Runtime
Sandbox
Environment
Verification
Observability
Evaluation
Experience
Learning

---

# 4. Stable Boundary Summary

현재까지 상대적으로 안정된 경계:

```text
Identity ≠ Model
Identity ≠ Memory
Task ≠ Session
Task State ≠ Context
State ≠ Memory
Memory ≠ Knowledge
Memory ≠ Artifact
Artifact ≠ Workspace
Capability ≠ Permission
Policy ≠ Permission
Harness ≠ Agent
Harness ≠ Runtime
Orchestrator ≠ Runtime
Execution ≠ Verification
Verification ≠ Evaluation
Experience ≠ Memory
Learning ≠ Memory
5. Identity Boundary

Identity는:

Protected Core
Values
Commitments
Continuity
Version
Provenance

을 가진 durable contract 후보로 정의한다.

Identity는 Model / Runtime / Session 교체와 독립적으로 유지된다.

6. Identity Persistence

Identity는 일반 Memory보다 높은 보호 수준을 갖는다.

후보:

Identity Core
↓
Identity Store
↓
Version / Integrity / Provenance
↓
Runtime Projection
7. Task Boundary

Task는 장기 Goal과 진행 상태를 표현한다.

Task
├── Goal
├── Requirements
├── Constraints
├── Progress
├── Verification
└── Artifact References
8. Session Boundary

Session은 특정 실행 관계다.

하나의 Task가 여러 Session을 가질 수 있다.

Task
├── Session A
├── Session B
└── Session C
9. Runtime Boundary

Runtime은 실제 execution lifecycle을 관리한다.

Runtime
├── Turn
├── Tool Execution
├── Retry
├── Pause
├── Resume
├── Cancellation
├── Checkpoint
└── Recovery
10. Task State

Task State는 Runtime과 독립된 durable canonical state 후보로 정의한다.

Task State
├── Goal
├── Progress
├── Status
├── Plan Reference
├── Artifact References
├── Verification
└── History
11. Execution State

Execution State는 Runtime-dependent state다.

Execution State
├── Current Turn
├── Active Capability
├── Retry
├── Approval
├── Checkpoint
└── Runtime Instance

Task State와 동일하게 취급하지 않는다.

12. Context Boundary

Context는 Model-facing projection이다.

Task State
+
Memory
+
Knowledge
+
Artifact
+
Conversation
+
Environment Observation
+
Policy
↓
Context Manager
↓
Current Context

Context는 Source of Truth가 아니다.

13. Memory Boundary

Memory는:

Experience
User / Project continuity
Important past information
Lessons

등을 관리한다.

14. Knowledge Boundary

Knowledge는:

External information
Structured facts
Project knowledge
Verified information

등을 관리한다.

Memory와 Knowledge는 의미적으로 구분하지만 공통 Retrieval infrastructure를 공유할 가능성을 유지한다.

15. Memory / Knowledge Relationship

현재 후보:

Memory System
Knowledge System
       ↓
Shared Information Interface
       ↓
Context Manager

완전 통합도, 완전 분리도 아직 최종 결정하지 않는다.

16. Artifact Boundary

Artifact는 실제 작업의 지속적인 결과물이다.

Artifact
├── Source
├── Document
├── Code
├── Data
├── Build
├── Evaluation
└── Evidence

Artifact는 File과 동일한 개념이 아니다.

17. Artifact Relationship
Task
 ↓
Artifact
 ↓
Verification
 ↓
Evidence

또한:

Artifact
 ↕
Memory
 ↕
Knowledge

관계를 가진다.

18. Artifact Persistence

Artifact는:

Version
Provenance
Integrity
Ownership
Scope
Lifecycle

을 가질 수 있다.

19. Capability Boundary

Capability:

Tool
Skill
Workflow
Protocol
Agent Delegation

을 포함하는 상위 개념이다.

20. Permission Boundary

Capability와 Permission을 분리한다.

Capability
↓
Policy
↓
Permission
↓
Execution
21. Harness Boundary

Harness는 Agent와 Infrastructure 사이의 Stable Execution Boundary 후보로 정의한다.

Agent
↓
Harness Contract
├── Context
├── Capability
├── Policy
├── Runtime
├── Memory Access
├── Recovery
└── Observability

논리적 Boundary이며 반드시 물리적으로 하나의 Service일 필요는 없다.

22. Harness vs Runtime

현재 방향:

Harness
↓
Runtime

Harness:

Agent가 안정적으로 실행될 수 있도록 필요한 infrastructure와 control을 조정한다.

Runtime:

실제 execution lifecycle을 수행한다.

23. Harness vs Orchestrator
Orchestrator
= What should happen?

Harness
= How should it execute safely and persistently?

중복 책임을 최소화한다.

24. Orchestration Boundary

Orchestrator는:

Task decomposition
Agent selection
Delegation
Scheduling
Parallelism
Aggregation
Replanning
Recovery strategy

를 담당한다.

25. Orchestration Contract

Orchestration은 명시적인 Contract 위에서 동작한다.

후보:

Task Contract
Plan Contract
Delegation Contract
Agent Contract
Context Contract
Capability Contract
Result Contract
Evidence Contract
Verification Contract
Budget Contract
Recovery Contract
26. Delegation

Child Agent는 Parent보다 더 많은 권한을 기본적으로 가지지 않는다.

Child Permission
⊆
Parent Permission
27. Result Contract

Agent 결과에는:

Status
Summary
Findings
Evidence
Artifacts
Uncertainty
Errors
Recommended Next Step

등을 포함할 수 있다.

28. Verification Contract
Preconditions
Postconditions
Evidence
Invariants
Result

을 통해 실행 결과를 검증한다.

29. Execution Boundary

실행 경계:

Agent Decision
↓
Capability
↓
Policy
↓
Permission
↓
Runtime
↓
Sandbox
↓
Execution

Agent가 직접 Environment를 변경하지 않는다.

30. Verification Boundary
Execution
↓
Evidence
↓
Verification
↓
State Commit

실행 성공과 Task 성공을 분리한다.

31. Observability Boundary

Trace:

Task
Session
Agent
Harness
Capability
Permission
Runtime
State
Verification
Result

를 연결할 수 있어야 한다.

32. Evaluation Boundary

Evaluation:

Success
Correctness
Safety
Cost
Latency
Process Quality
Recovery
Long-term Utility

를 평가한다.

33. Experience Boundary
Execution
↓
Outcome
↓
Experience

Experience는 Raw Evidence와 Learned Lesson을 모두 연결할 수 있다.

34. Learning Boundary
Evaluation
↓
Experience
↓
Memory
↓
Lesson
↓
Skill / Routing / Personality Improvement

Learning이 Core Identity를 자동으로 수정하지 않는다.

35. Controlled Adaptation

변경 위험:

Low
→ Skill / Procedure

Medium
→ Routing / Personality

High
→ Policy / Identity

Higher-risk adaptation에는 Governance가 필요하다.

36. Integrated Candidate Architecture
                         CONSTITUTION
                              │
                         IDENTITY CORE
                              │
                            AGENT
                              │
                       TASK / SESSION
                              │
                       ORCHESTRATION
                              │
                           HARNESS
                              │
                 ┌────────────┼────────────┐
                 │            │            │
              CONTEXT       STATE        MEMORY
                 │            │            │
                 │            │        KNOWLEDGE
                 │            │            │
                 └────────────┼────────────┘
                              │
                         CAPABILITY
                              │
                            POLICY
                              │
                          PERMISSION
                              │
                           RUNTIME
                              │
                           SANDBOX
                              │
                         ENVIRONMENT
                              │
                          EXECUTION
                              │
                        VERIFICATION
                              │
                       OBSERVABILITY
                              │
                         EVALUATION
                              │
                         EXPERIENCE
                              │
                          LEARNING
                              │
                     CONTROLLED ADAPTATION
37. Integrated Data Flow
Environment
↓
Observation
↓
State
↓
Memory / Knowledge / Artifact
↓
Context Projection
↓
Agent

그리고:

Agent
↓
Capability
↓
Policy
↓
Permission
↓
Runtime
↓
Environment
38. Integrated Control Flow
Task
↓
Orchestrator
↓
Plan
↓
Delegation
↓
Harness
↓
Runtime
↓
Execution
↓
Verification
↓
Evaluation
39. Integrated Feedback Loop
Execution
↓
Observation
↓
Evaluation
↓
Experience
↓
Memory
↓
Learning
↓
Skill / Routing / Personality Improvement
↓
Future Execution
40. Identity Continuity Loop
Session
↓
Experience
↓
Memory
↓
Self Model
↓
Future Session

Core Identity는 별도의 protected persistence를 유지한다.

41. Security Loop
Capability Request
↓
Risk
↓
Policy
↓
Permission
↓
Approval
↓
Sandbox
↓
Execution
↓
Verification
↓
Audit
42. Contract Stack

최종 Candidate Contract hierarchy:

Identity Contract
Task Contract
Session Contract
State Contract
Context Contract
Harness Contract
Capability Contract
Permission Contract
Execution Contract
Result Contract
Evidence Contract
Verification Contract
Evaluation Contract
43. Logical vs Physical Architecture

Logical boundaries를 먼저 확정하고,
Physical decomposition은 이후 결정한다.

초기에는:

Modular Monolith

를 우선 검토한다.

44. Replaceable Implementations

다음은 교체 가능해야 한다.

Model
Runtime Framework
Orchestrator
Memory Backend
Knowledge Backend
Artifact Storage
Sandbox
Telemetry
Protocol
45. Stable Principles

장기적으로 유지할 후보:

Identity
Task
State
Context
Memory
Knowledge
Artifact
Capability
Permission
Execution
Verification
Evaluation
Experience
Contract
46. Current / Historical / Emerging

모든 Architecture 결정은:

Historical Principle
+
Current Evidence
+
Emerging Research

를 비교한다.

최신 기술 자체가 Architecture의 목적이 아니다.

47. Remaining Architecture Questions

P1 이후에도 남는 핵심 질문:

Harness Contract의 최소 API는?
Task State Store의 실제 구현은?
Memory / Knowledge unified retrieval을 어떻게 할 것인가?
Artifact Registry가 필요한 규모는?
Identity Store는 어떻게 구현하는가?
Orchestration Contract를 어떤 Schema로 만들 것인가?
Event System의 책임은?
Physical service decomposition은 언제 필요한가?
48. Architecture Readiness

현재 상태를 평가한다.

Conceptual Boundaries
→ High confidence

Stable Contracts
→ Medium confidence

Physical Architecture
→ Low confidence

Implementation Details
→ Intentionally open
49. What Is Now Stable

다음 영역은 v0.3 기준으로 상당히 명확해졌다고 본다.

Task / Session distinction
Task / Runtime distinction
Context / State distinction
Memory / Knowledge distinction
Artifact semantics
Capability / Permission distinction
Harness concept
Orchestration Contract concept
Identity persistence concept
Verification / Evaluation distinction
50. What Remains Experimental
Learned Orchestration
Adaptive Harness
Identity Evolution
Memory / Knowledge Unified Storage
Artifact Graph
Persistent Specialist Identity
Automatic Self-improvement
51. What Should Not Be Decided Yet
Specific Database
Specific Vector DB
Specific Graph DB
Specific Agent Framework
Specific Runtime Framework
Specific Model Provider
Specific Sandbox
Specific Protocol
52. Architecture Risks
Over-Abstraction

Architecture could become more complicated than the problem.

Boundary Explosion

Too many modules.

Contract Explosion

Too many interfaces and schemas.

Premature Distribution

Too many physical services.

Future Lock-in

Current technology becoming permanent architecture.

Feedback Complexity

Memory / Learning / Identity loops becoming difficult to control.

53. Research-to-Architecture Transition

현재부터는:

Research
↓
Integration
↓
Decision
↓
Architecture

로 전환할 준비가 되어 있다.

54. DDR Candidates

다음 Architecture Decision Records 후보:

DDR-001
Task State / Runtime Boundary

DDR-002
Harness Boundary

DDR-003
Memory / Knowledge Boundary

DDR-004
Artifact Contract

DDR-005
Identity Persistence

DDR-006
Orchestration Contract

번호와 정확한 제목은 실제 DDR 생성 시 확정한다.

55. DDR Requirement

각 DDR에서는:

Problem
Context
Options
Decision
Reasoning
Trade-offs
Consequences
Alternatives

를 기록한다.

56. Blueprint Preparation

DDR가 완료된 후:

02-Architecture

를 업데이트한다.

현재 Research 문서를 그대로 Architecture 문서로 복사하지 않는다.

57. First Physical Architecture Candidate

아직 확정하지 않지만:

NOAH
├── Core
│   ├── Identity
│   ├── Agent
│   └── Task
│
├── Runtime
│   ├── Session
│   ├── Context
│   ├── State
│   └── Harness
│
├── Cognitive
│   ├── Memory
│   ├── Knowledge
│   └── Learning
│
├── Capability
│   ├── Tools
│   ├── Skills
│   └── Workflows
│
├── Security
│   ├── Policy
│   ├── Permission
│   └── Sandbox
│
├── Orchestration
│
├── Evaluation
│
└── Artifacts

정도의 Modular Monolith를 PoC 후보로 검토한다.

58. First Integrated PoC

최소 PoC:

User
↓
Task
↓
Agent
↓
Context
↓
Capability
↓
Permission
↓
Runtime
↓
Artifact
↓
Verification
↓
Evaluation
↓
Memory

Identity와 Harness는 최소 구현으로 연결한다.

59. PoC Expansion

순서:

PoC 1
Single Agent

PoC 2
Durable Task State

PoC 3
Harness Boundary

PoC 4
Memory / Knowledge

PoC 5
Artifact Management

PoC 6
Security / Permission

PoC 7
Evaluation / Recovery

PoC 8
Orchestration / Subagent

PoC 9
Identity Continuity
60. Integration Evaluation

통합 구조는:

Correctness
Safety
Reliability
Recovery
Observability
Memory Utility
Artifact Integrity
Identity Continuity
Cost
Latency
Maintainability
Replaceability

로 평가한다.

61. Decision Readiness

DDR로 넘어가기 위한 최소 조건:

☐ Major boundaries defined
☐ P0 research completed
☐ P1 research completed
☐ Major conflicts identified
☐ Remaining uncertainty documented
☐ Candidate contracts defined
☐ Implementation independence preserved
☐ PoC scope identified
62. Current Recommendation

현재 가장 유력한 방향:

NOAH는 Protected Identity를 중심으로 장기 Task를 수행하는 Agent System이며, Harness와 Runtime을 통해 Context / State / Memory / Knowledge / Artifact / Capability를 사용하고, Policy와 Permission을 통해 실행을 통제하며, Verification과 Evaluation을 통해 행동을 검증하고, Experience를 Learning으로 연결한다.

63. What NOAH Is Becoming

단순:

LLM

도 아니고:

Chatbot

도 아니며:

Tool-using Agent

만도 아니다.

현재 Architecture Candidate는:

Persistent Identity
+
Agent
+
Durable Task Execution
+
Memory
+
Knowledge
+
Artifacts
+
Capabilities
+
Security
+
Orchestration
+
Evaluation
+
Learning

의 조합이다.

64. Long-Term Philosophy

최신 기술을 사용하는 것이 목적이 아니다.

과거의 좋은 원리를 잃지 않고, 현재 검증된 기술을 활용하며, 미래의 더 나은 기술을 받아들일 수 있는 Architecture를 만드는 것이 목적이다.

65. Review Boundary

이번 Review에서도 최종적으로 확정하지 않는다.

Final Model
Final Runtime
Final Memory Backend
Final Knowledge Backend
Final Artifact Store
Final Harness Implementation
Final Orchestrator
Final Identity Storage
Final Physical Deployment

이들은 DDR과 PoC를 통해 결정한다.

66. Next Step
Architecture Integration Review v0.3
        ↓
DDR
        ↓
02-Architecture
        ↓
Integrated PoC
        ↓
Evaluation
        ↓
Architecture Revision
67. Review Outcome

현재 시점에서 논리적 Architecture Boundary와 핵심 Contract가 상당 부분 정리되었다.

따라서 다음 단계에서는 새로운 개념을 계속 추가하기보다:

Research → Decision → Architecture → PoC

로 전환하는 것이 적절하다.

68. Final Principle

좋은 Architecture는 미래를 정확히 예측하는 Architecture가 아니라, 미래가 현재의 가정을 깨뜨렸을 때도 다시 성장할 수 있는 Architecture다.