Architecture Integration Review — v0.1

Project NOAH Architecture Review
Review 대상: 전체 Architecture Integration
Review Version: 0.1
Status: Review

1. Review Purpose

지금까지 Project NOAH의 각 Architecture 영역을 독립적으로 연구하고 검토했다.

이번 Integration Review의 목적은 개별 Architecture가 실제로 하나의 시스템으로 결합될 수 있는지 검증하는 것이다.

본 Review의 핵심 질문은 다음과 같다.

"지금까지 설계한 모든 구성요소가 하나의 일관된 NOAH를 구성할 수 있는가?"

그리고 다음을 확인한다.

Architecture 간 책임이 중복되지 않는가?
서로 충돌하는 경계가 존재하는가?
빠진 핵심 계층이 있는가?
순환 의존이 발생하는가?
State / Memory / Context가 일관되게 연결되는가?
Agent / Runtime / Orchestration의 책임이 겹치지 않는가?
Capability / Permission / Security 경계가 일관적인가?
Identity가 시스템 전체에서 지속되는가?
Evaluation이 모든 중요한 실행을 관찰할 수 있는가?
Experience가 Memory와 Learning을 통해 다시 시스템 개선으로 연결되는가?
현재 설계가 특정 Model / Runtime / Framework에 종속되어 있지 않은가?
미래 Architecture가 등장해도 핵심 경계를 유지할 수 있는가?

본 문서는 최종 Blueprint가 아니다.

이번 단계에서는 통합 가능성, 경계, 의존성, 충돌 및 누락을 발견하는 것을 목표로 한다.

2. Integration Principle

전체 Architecture를 하나의 거대한 시스템으로 만들기보다 명확한 책임 경계를 가진 독립적인 subsystem들의 조합으로 설계한다.

기본 원칙:

Stable Boundary
        +
Replaceable Implementation
        +
Explicit Contract

즉:

❌ 특정 Framework를 Architecture에 고정

✅ Framework와 무관한 책임과 Interface를 정의
3. Current Architecture Inventory

현재까지 검토된 주요 영역:

01. Identity & Personality
02. Agent
03. Session & Runtime
04. Context & State
05. Memory
06. Capability & Tools
07. Permission & Security
08. Orchestration & Multi-Agent
09. Evaluation & Observability

이들을 하나의 Architecture로 연결한다.

4. High-Level Candidate Architecture

현재까지의 Review를 통합하면 다음 구조를 후보로 둘 수 있다.

                              NOAH
                                │
                         Identity / Values
                                │
                              Agent
                                │
                       Session / Task
                                │
                         Orchestration
                                │
                         Context / State
                                │
                ┌───────────────┼────────────────┐
                │               │                │
             Memory        Capability        Environment
                │               │                │
                │           Policy / Security   │
                │               │                │
                └───────────────┼────────────────┘
                                │
                             Runtime
                                │
                            Execution
                                │
                   ┌────────────┴────────────┐
                   │                         │
                Sandbox                 External Systems
                   │                         │
                   └────────────┬────────────┘
                                │
                         Verification
                                │
                       Observability
                                │
                         Evaluation
                                │
                          Experience
                                │
                             Learning
                                │
                    Controlled Adaptation
                                │
                    ┌───────────┴───────────┐
                    │                       │
                Memory Update          Skill / Policy
                    │                       │
                    └───────────┬───────────┘
                                │
                         Future Execution

이 구조는 Candidate Architecture다.

5. Architecture Layers

전체 시스템을 다음과 같은 논리적 Layer로 구분하는 것을 검토한다.

Layer 0
Constitution / Governance

Layer 1
Identity

Layer 2
Agent

Layer 3
Task / Session / Orchestration

Layer 4
Context / State / Memory

Layer 5
Capability / Policy / Security

Layer 6
Runtime / Execution / Environment

Layer 7
Observability / Verification / Evaluation

Layer 8
Experience / Learning / Adaptation

각 Layer는 다른 Layer의 구현 세부사항을 직접 소유하지 않는 방향을 우선 검토한다.

6. Constitution Boundary

Constitution은 전체 Architecture보다 상위의 원칙이다.

Constitution
        ↓
Architecture
        ↓
Implementation

Constitution이 정의하는:

Human Before Technology
Trust
Growth
Honesty
Responsibility
Explainability

등은 일반 Runtime State나 Memory에 의해 임의로 수정되지 않는다.

7. Governance Boundary

Governance는 Constitution과 Implementation 사이의 정책 계층이다.

예:

Constitution
    ↓
Governance
    ↓
Policy
    ↓
Implementation

Governance 후보:

Development rules
Security policy
Change approval
Identity change governance
Evaluation standards
Architecture decision process
8. Identity Boundary

Identity는 Model이나 Runtime과 독립된 지속성 계층으로 본다.

Identity
≠ Model
≠ Runtime
≠ Session
≠ Memory
≠ Personality

Identity는 가능한 한 Session/Runtime이 교체되어도 유지된다.

9. Identity → Agent

Identity는 Agent가 어떤 존재로 행동해야 하는지에 대한 상위 기준을 제공한다.

Identity
   ↓
Role / Personality / Values
   ↓
Agent Behavior

그러나 Identity가 Agent의 모든 현재 상태를 소유하지는 않는다.

10. Agent Boundary

Agent는:

목표 이해
판단
계획
Capability 선택
Context 사용
행동 결정

을 수행하는 실행 주체로 본다.

Agent는 다음의 직접적인 구현을 소유하지 않는 방향을 검토한다.

Storage
Sandbox
Permission Engine
Telemetry Backend
Memory Database
11. Agent vs Harness

이번 Integration에서 가장 중요한 경계 중 하나다.

후보:

Agent
= 판단하고 행동하려는 주체

Harness
= Agent가 안정적으로 행동할 수 있도록
  Context / Tools / Policy / Memory / Runtime / Evaluation을 조정하는 실행 계층

구조:

Agent
   ↓
Harness
   ├── Context
   ├── Capability
   ├── Policy
   ├── Memory Interface
   ├── Runtime
   ├── Security
   └── Evaluation

이 경계는 최종 확정 전에 더 검증이 필요하다.

12. Session Boundary

Session은 지속적인 실행 관계를 표현한다.

Session
├── Conversation
├── Task Reference
├── Execution Reference
└── State References

Session은 Conversation과 동일하지 않다.

13. Task Boundary

Task는 Session보다 오래 지속될 수 있는 목표 단위다.

Task
├── Goal
├── Requirements
├── Constraints
├── Progress
├── Verification
└── Next Step

후보 구조:

Session
   ↓
Task
   ↓
Execution
14. Orchestration Boundary

Orchestration은 Agent가 직접 모든 협업을 관리하지 않고:

Decomposition
Routing
Delegation
Scheduling
Parallelism
Aggregation
Recovery

를 담당하는 계층으로 둔다.

Task
   ↓
Orchestrator
   ↓
Agent / Skill / Capability
15. Single-Agent Default

통합 관점에서도 원칙은 유지한다.

Task
 ↓
Single Agent

을 기본으로 사용하고,

Need detected
 ↓
Subagent / Multi-Agent

로 확장한다.

Multi-Agent는 Architecture의 기본 구조가 아니라 필요에 의해 생성되는 execution strategy로 본다.

16. Context Boundary

Context는 Model-facing projection이다.

System State
      ↓
Context Selection
      ↓
Context Assembly
      ↓
Model

Context는 Source of Truth가 아니다.

17. State Boundary

State는 시스템의 canonical condition이다.

후보:

State
├── Task State
├── Execution State
├── Environment State
├── Workspace State
├── Policy State
└── Approval State

State는 Context보다 오래 유지될 수 있다.

18. Memory Boundary

Memory는 과거의 경험과 지식을 미래 행동에 재사용하기 위한 독립 subsystem이다.

Memory
≠ Context
≠ State
≠ Knowledge Base
≠ Vector DB

Memory는:

Write
Manage
Read
Revise
Forget
Evaluate

를 수행할 수 있어야 한다.

19. State ↔ Memory

두 계층은 연결되지만 동일하지 않다.

Current State
      ↓
Experience
      ↓
Memory

반대로:

Memory
      ↓
Retrieval
      ↓
Context
      ↓
Future State / Action

이 가능하다.

20. Context ↔ Memory

Memory가 모든 Context로 들어가는 것이 아니다.

Memory
 ↓
Retrieval
 ↓
Ranking
 ↓
Context Projection
 ↓
Agent

Context Budget과 Relevance를 고려해야 한다.

21. Capability Boundary

Capability는 Agent가 수행할 수 있는 행동의 상위 개념이다.

Capability
├── Tool
├── Skill
├── Workflow
├── Protocol
└── Agent Delegation
22. Capability ↔ Agent

Agent는 Capability를 소유하기보다 Capability를 선택하고 요청하는 주체로 보는 방향을 검토한다.

Agent
 ↓
Capability Request
 ↓
Policy
 ↓
Execution
23. Capability ↔ Permission

Capability와 Permission은 분리한다.

Capability
= What can be done?

Permission
= Is it allowed now?

이 경계는 Security Architecture의 핵심이다.

24. Policy Boundary

Policy는:

Scope
Risk
Identity
Environment
Approval
Resource

를 종합하여 실행 허용 여부를 판단한다.

Capability
   ↓
Policy
   ↓
Permission
25. Security Boundary

Security는 별도의 하나의 기능이 아니라 여러 경계에 분산된 방어 구조로 본다.

Identity
 ↓
Capability
 ↓
Policy
 ↓
Permission
 ↓
Credential
 ↓
Sandbox
 ↓
Execution
 ↓
Verification
 ↓
Audit
26. Sandbox Boundary

Execution Environment는 Agent와 분리한다.

Agent
 ↓
Policy
 ↓
Sandbox
 ↓
Tool
 ↓
Environment

Sandbox는:

Filesystem
Process
Network
Credentials
Resources

등을 제한할 수 있다.

27. Runtime Boundary

Runtime은 실제 Agent execution을 관리한다.

Runtime
├── Turn
├── Tool Execution
├── State Transition
├── Retry
├── Pause
├── Resume
├── Cancellation
├── Persistence
└── Recovery

Runtime은 Orchestrator와 동일하지 않다.

28. Orchestrator vs Runtime

이 구분이 중요하다.

Orchestrator
= 무엇을 실행할 것인가?

Runtime
= 선택된 실행을 어떻게 지속적으로 수행할 것인가?

예:

Orchestrator
→ Research Agent + Coding Agent

Runtime
→ Agent A 실행
→ Tool 호출
→ State 저장
→ Pause
→ Resume
→ Recovery
29. Execution Boundary

실제 외부 Side Effect는 Execution Boundary를 통과한다.

Agent Decision
 ↓
Capability
 ↓
Policy
 ↓
Permission
 ↓
Execution

Agent가 직접 외부 환경을 변경하는 구조는 피한다.

30. Verification Boundary

Execution과 성공은 동일하지 않다.

Execution
 ↓
Result
 ↓
Verification
 ↓
State Commit

즉:

"실행됐다."

와

"원하는 상태가 되었다."

를 구분한다.

31. Observability Boundary

Observability는 모든 중요한 실행의 증거를 수집한다.

Execution
 ↓
Trace
Event
Metric
State Snapshot
32. Evaluation Boundary

Evaluation은 관찰된 실행을 평가한다.

Trace
 ↓
Evidence
 ↓
Verification
 ↓
Evaluation

평가는:

Success
Correctness
Safety
Cost
Latency
Process
Recovery
Long-term Utility

등을 포함한다.

33. Evaluation ↔ Learning

Evaluation 결과는 단순 점수로 버리지 않는다.

Evaluation
 ↓
Failure Attribution
 ↓
Experience
 ↓
Memory
 ↓
Learning
34. Experience Boundary

Experience는 실행 결과와 그 의미를 장기적인 Learning Cycle에 연결한다.

Execution
 ↓
Outcome
 ↓
Experience

Experience는 Raw Evidence와 Consolidated Lesson으로 나눌 수 있다.

35. Learning Boundary

Learning은:

Memory에서 무엇을 기억하는가?

보다 한 단계 위에서:

경험을 통해 미래의 행동을 어떻게 개선할 것인가?

를 담당한다.

후보:

Experience
 ↓
Evaluation
 ↓
Lesson
 ↓
Skill / Policy / Harness Improvement
36. Controlled Adaptation

Learning이 모든 시스템을 직접 변경하지 않는다.

변경 수준:

Low
→ Skill / Procedure

Medium
→ Personality / Routing

High
→ Policy / Identity

고위험 변경은 Governance를 거친다.

37. Identity ↔ Learning

Identity는 Learning의 결과로 무조건 변경되지 않는다.

Learning
 → Behavior Improvement

이 기본이다.

Identity Core 변화는:

Proposal
 ↓
Evidence
 ↓
Review
 ↓
Governance
 ↓
Version

이 필요하다.

38. Personality ↔ Learning

Personality는 Identity보다 더 유연하게 변화할 수 있다.

Experience
 ↓
Learning
 ↓
Behavioral Adaptation
 ↓
Personality Update

다만 Core Values와 Constitution은 그대로 유지한다.

39. Memory ↔ Learning

Memory와 Learning은 순환한다.

Experience
 ↓
Memory
 ↓
Reflection
 ↓
Learning
 ↓
Better Behavior
 ↓
New Experience

이것은 NOAH의 장기적인 성장 구조 후보이다.

40. Capability ↔ Learning

Capability도 경험으로 개선될 수 있다.

예:

Tool usage
 ↓
Failure Pattern
 ↓
Lesson
 ↓
Skill Improvement
 ↓
Better Tool Selection

장기적으로 Skill Evolution을 검토한다.

41. Orchestration ↔ Learning

Orchestration도 경험으로 개선될 수 있다.

Task
 ↓
Plan
 ↓
Execution
 ↓
Evaluation
 ↓
Successful Strategy
 ↓
Orchestration Memory
 ↓
Future Routing

그러나 learned routing은 현재 Research Further로 유지한다.

42. Security ↔ Learning

Security도 경험으로 개선될 수 있다.

Attack / Failure
 ↓
Detection
 ↓
Evaluation
 ↓
Lesson
 ↓
Policy / Defense Improvement

단, Security Policy의 자동 변경은 높은 Governance 수준이 필요하다.

43. Cross-Architecture Feedback Loop

전체적인 장기 Loop:

                        ┌───────────────┐
                        │    Identity   │
                        └───────┬───────┘
                                │
                                ▼
                             Agent
                                │
                                ▼
                         Task / Session
                                │
                                ▼
                         Orchestration
                                │
                                ▼
                       Context / State
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
             Memory        Capability        Environment
                │               │               │
                └───────────────┼───────────────┘
                                │
                             Runtime
                                │
                             Execute
                                │
                       Verification
                                │
                         Observability
                                │
                          Evaluation
                                │
                           Experience
                                │
                            Learning
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
             Memory         Skill /        Behavior
             Update          Routing        Adaptation
                │               │               │
                └───────────────┼───────────────┘
                                │
                                ▼
                           Future Task
44. Critical Architecture Boundaries

현재 통합에서 가장 중요한 경계 후보:

Identity
≠ Personality

Agent
≠ Model

Session
≠ Conversation

Task
≠ Session

State
≠ Context

Memory
≠ State

Memory
≠ Knowledge Base

Capability
≠ Permission

Policy
≠ Permission

Orchestrator
≠ Runtime

Execution
≠ Verification

Verification
≠ Evaluation

Experience
≠ Memory

Learning
≠ Memory

Identity
≠ Consciousness

이 경계들은 Integration Review에서 핵심적으로 유지한다.

45. Potential Boundary Conflicts

현재 의심해야 할 충돌:

Context vs Working Memory

Working Memory가 Context와 별도 시스템이어야 하는가?

Task State vs Orchestration State

둘을 어디까지 분리해야 하는가?

Memory vs Knowledge

Long-term Semantic Memory와 Knowledge Base의 경계는 어디인가?

Skill vs Workflow

절차와 실행 순서의 차이를 어떻게 유지할 것인가?

Agent vs Persistent Specialist

언제 Specialist가 독립 Agent가 되는가?

Harness vs Runtime

Runtime이 Harness의 일부인가?

Identity vs Root Agent

Identity가 Agent와 별도 Layer로 존재해야 하는가?

46. Potential Missing Architecture

현재 문서들을 통합하면 몇 가지 후보가 나타난다.

Task State Management
Event / State Store
Artifact Management
Knowledge System
Credential Broker
Capability Registry
Identity Store
Evaluation Dataset
Experiment Tracking

하지만 필요하다고 즉시 새로운 subsystem으로 추가하지 않는다.

기존 책임으로 충분히 설명할 수 있는지 먼저 검토한다.

47. Artifact Boundary

Long-running Agent에서는 파일, 코드, 보고서, 데이터와 같은 Artifact가 중요한 지속 상태가 될 수 있다.

후보:

Artifact
├── File
├── Code
├── Dataset
├── Report
├── Test Result
└── Generated Output

Artifact는 Context에 직접 저장하지 않고 durable resource로 관리하는 방향을 검토한다.

48. Artifact ↔ Memory

Artifact와 Memory는 다르다.

Artifact
= 실제 생성/변경된 결과물

Memory
= 그 결과물에 대해 미래에 사용할 정보

예:

Artifact
→ architecture.md

Memory
→ "Architecture v1은 이 구조로 결정되었다."

Artifact 자체도 Evidence가 될 수 있다.

49. Knowledge Boundary

Knowledge를 Memory와 구분한다.

후보:

Knowledge
= 외부 또는 구조화된 정보

Memory
= 경험과 지속적인 개인/프로젝트 정보

하지만 실제 저장소 일부는 공유할 수 있다.

50. Knowledge ↔ Context

Knowledge도 직접 Model Context에 전부 들어가지 않는다.

Knowledge
 ↓
Retrieval
 ↓
Ranking
 ↓
Context

Memory와 비슷한 projection pipeline을 가질 수 있다.

51. Event Boundary

Event는 여러 subsystem을 연결하는 공통 관찰 언어가 될 수 있다.

예:

TaskStarted
ToolCalled
MemoryRetrieved
PermissionDenied
AgentSpawned
StateChanged
VerificationPassed
EvaluationFailed

Event는 모든 subsystem의 source of truth가 되어야 하는 것은 아니다.

52. Event Log vs Canonical State

현재 방향:

Canonical State
= 실제 현재 상태

Event Log
= 상태 변화와 실행을 추적하는 기록

Full Event Sourcing은 필요성이 확인될 때까지 Defer한다.

53. Dependency Direction

Architecture 의존성은 가능하면:

High-level Intent
        ↓
Stable Contracts
        ↓
Implementations

방향을 따른다.

예:

Agent
 ↓
Capability Interface
 ↓
Tool Implementation

이지:

Agent
 ↓
Specific Tool SDK

가 아니다.

54. Implementation Independence

다음 요소는 교체 가능한 구현으로 본다.

Model
Runtime
Vector DB
Graph DB
SQL DB
Sandbox
Workflow Engine
Orchestrator
Evaluation Framework
Protocol

NOAH는 이 구현을 교체해도 상위 Architecture 계약을 유지할 수 있어야 한다.

55. Current Technology vs Stable Principle

예:

Current technology:
MCP

Stable principle:
External Capability Interoperability
Current technology:
Specific Vector DB

Stable principle:
Semantic Retrieval
Current technology:
Specific Agent Runtime

Stable principle:
Durable Execution Contract
Current technology:
Current Context Window

Stable principle:
Context Selection / Projection
56. Historical Ideas Integration

오래된 아이디어도 동일한 기준으로 평가한다.

Historical Idea
 ↓
Problem it solved
 ↓
Core principle
 ↓
What changed?
 ↓
Still useful?
 ↓
NOAH Candidate

예:

Actor Model
→ isolated state + message passing

Blackboard
→ shared workspace coordination

Global Workspace
→ selective information broadcasting

Planner / Executor
→ planning / execution separation

MapReduce
→ parallelization + aggregation

구현을 그대로 가져오는 것이 아니라 원칙을 추출한다.

57. Current Frontier Integration

최신 연구에서도 마찬가지다.

New Research
 ↓
What problem?
 ↓
What is fundamentally new?
 ↓
Temporary implementation?
 ↓
Stable principle?
 ↓
NOAH Candidate

최신 기술이라는 이유만으로 Architecture에 포함하지 않는다.

58. Future Resilience

Integration Architecture는 미래의 기술 변화에 견딜 수 있어야 한다.

예:

Model 2026
 ↓
Model 2028
 ↓
Model 2030

Architecture는 유지.

Runtime A
 ↓
Runtime B

Architecture는 유지.

Memory Technology A
 ↓
Memory Technology B

Memory contract는 유지.

59. Stable Contracts

통합 단계에서 장기적으로 유지할 후보 Contract:

Identity Contract
Agent Contract
Task Contract
Session Contract
State Contract
Memory Contract
Capability Contract
Permission Contract
Execution Contract
Verification Contract
Evaluation Contract
Experience Contract
Learning Contract

이 Contract들이 최종 Blueprint의 핵심이 될 가능성이 높다.

60. Contract Hierarchy

후보:

Constitution
      ↓
Identity
      ↓
Task / Agent
      ↓
Execution Contracts
      ↓
Capability / Security
      ↓
State / Memory
      ↓
Evaluation

단, 실제 dependency는 완전히 선형이 아니라 graph 형태일 수 있다.

61. Circular Dependencies

현재 가장 중요한 순환:

Experience
 ↓
Memory
 ↓
Learning
 ↓
Behavior
 ↓
Experience

이것은 의도된 feedback loop다.

반면:

Memory
 ↔
State

또는:

Identity
 ↔
Agent

가 구현 의존성까지 직접 순환하면 문제가 될 수 있다.

Logical feedback loop와 implementation dependency cycle을 구분한다.

62. Data Flow vs Control Flow

Architecture를 두 종류의 흐름으로 나눈다.

Data Flow
Memory
Context
Tool Result
State
Artifact
Control Flow
Agent
Orchestrator
Runtime
Policy
Verification

이 둘을 구분하면 Architecture를 이해하기 쉬워진다.

63. Proposed Data Flow
Environment
 ↓
Observation
 ↓
State
 ↓
Memory / Knowledge Retrieval
 ↓
Context
 ↓
Agent

반대 방향:

Agent
 ↓
Capability
 ↓
Execution
 ↓
Environment Change
 ↓
Observation
64. Proposed Control Flow
Task
 ↓
Agent / Orchestrator
 ↓
Capability Request
 ↓
Policy
 ↓
Permission
 ↓
Runtime
 ↓
Execution
 ↓
Verification
 ↓
Evaluation
65. Overall NOAH Loop

이를 통합하면:

Task
 ↓
Understand
 ↓
Retrieve
 ↓
Plan
 ↓
Select Capability
 ↓
Authorize
 ↓
Execute
 ↓
Observe
 ↓
Verify
 ↓
Evaluate
 ↓
Learn
 ↓
Remember
 ↓
Adapt
 ↓
Next Task

이것이 현재 NOAH의 가장 중요한 시스템 Loop 후보이다.

66. Long-Horizon Loop

장기 작업에서는:

Task
 ↓
Progress
 ↓
Checkpoint
 ↓
Execute
 ↓
Verify
 ↓
Update State
 ↓
Continue

를 반복한다.

Session이 끝나더라도 Task가 계속될 수 있어야 한다.

67. Identity Continuity Loop

장기적으로:

Session
 ↓
Experience
 ↓
Memory
 ↓
Self Model
 ↓
Future Session

을 통해 Identity Continuity를 유지한다.

하지만 Core Identity는 별도의 protected boundary를 유지한다.

68. Security Loop
Capability Request
 ↓
Risk
 ↓
Policy
 ↓
Permission
 ↓
Sandbox
 ↓
Execution
 ↓
Verification
 ↓
Audit

이것은 모든 중요한 side-effecting action에 적용할 수 있는 공통 Security path 후보이다.

69. Evaluation Loop
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
Failure Attribution
 ↓
Experience
70. Learning Loop
Experience
 ↓
Memory
 ↓
Reflection
 ↓
Lesson
 ↓
Skill / Routing / Personality Update
 ↓
Future Execution

고위험 변경은 Governance를 통과한다.

71. Integrated Self-Improvement Loop

전체를 연결하면:

                     ┌──────────────┐
                     │    NOAH      │
                     └──────┬───────┘
                            │
                         Execute
                            │
                         Observe
                            │
                         Evaluate
                            │
                        Experience
                            │
                         Memory
                            │
                         Learning
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
      Skills            Routing            Personality
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                       Future Behavior
                            │
                            └──────→ NOAH

Identity Core는 이 Loop의 무조건적인 자동 변경 대상이 아니다.

72. What Integration Reveals

현재 통합을 통해 중요한 사실이 드러난다.

첫째

NOAH는 단순 Agent가 아니다.

Agent
+
Memory
+
Runtime
+
Security
+
Evaluation
+
Learning

의 시스템이다.

둘째

Memory는 단순 저장소가 아니다.

셋째

Evaluation은 마지막 테스트 단계가 아니다.

넷째

Identity는 Personality보다 상위이며 Memory와 연결된다.

다섯째

Multi-Agent는 핵심 정체성이 아니라 Orchestration 전략이다.

73. Potential Architecture Simplification

현재 구조는 많은 계층을 가지고 있다.

따라서 통합 단계에서 다음 질문을 해야 한다.

"이 모든 계층을 실제 코드에서 독립된 서비스로 만들어야 하는가?"

답은:

아니다.

Logical Boundary와 Physical Service Boundary는 다를 수 있다.

예:

Logical:
Memory Manager

Physical:
같은 Python process 내부 module

로 시작할 수 있다.

74. Logical vs Physical Architecture
Logical Architecture
= 책임과 경계

Physical Architecture
= 실제 process / service / container

NOAH는 Logical Architecture를 먼저 안정화하고 Physical Architecture는 구현 단계에서 결정한다.

75. Avoid Premature Distribution

모든 subsystem을 처음부터 별도 Microservice로 만들지 않는다.

Identity Service
Memory Service
Agent Service
Runtime Service
...

를 모두 분리하는 것은 초기에는 과도할 가능성이 높다.

Single Process / Modular Monolith에서 시작해 필요할 때 분리한다.

76. Modularity

물리적 분리 대신:

modules/
├── identity
├── agent
├── session
├── context
├── memory
├── capability
├── security
├── runtime
├── evaluation
└── orchestration

과 같은 논리적 모듈 분리를 우선 검토한다.

77. Integration Candidate Module Map

현재 후보:

NOAH
├── identity/
├── agent/
├── task/
├── session/
├── context/
├── state/
├── memory/
├── capability/
├── security/
├── orchestration/
├── runtime/
├── environment/
├── evaluation/
└── learning/

이는 실제 Repository 구조를 확정하는 것이 아니라 Logical Module Map이다.

78. Integration Risks
Boundary Explosion

계층이 지나치게 많아질 수 있다.

Circular Dependency

논리적 feedback과 구현 dependency가 섞일 수 있다.

Coordination Complexity

Orchestrator가 지나치게 많은 것을 담당할 수 있다.

Over-Abstraction

아직 필요하지 않은 Interface가 너무 많아질 수 있다.

Performance

모든 경계를 통과하면서 overhead가 증가할 수 있다.

State Consistency

State가 여러 subsystem에서 동시에 변경될 수 있다.

Identity Drift

Learning cycle이 Identity까지 자동으로 변경할 수 있다.

Security Complexity

Permission과 Policy가 지나치게 복잡해질 수 있다.

79. Missing Information

현재 Integration Review만으로는 확정할 수 없는 부분:

Task Data Model
Canonical State Store
Memory Storage
Event Model
Capability Contract
Policy Language
Identity Schema
Runtime API
Evaluation Schema

이들은 아직 Research / Specification / PoC가 더 필요하다.

80. Architecture Decisions Not Yet Made

아직 최종적으로 결정하지 않는다.

Runtime Framework
Memory Technology
Graph / Vector / SQL composition
Sandbox Technology
Orchestrator Implementation
Protocol
Identity Storage
Evaluation Stack

이들은 DDR 이전까지 열어둔다.

81. Candidate Stable Core

현재 Integration에서 가장 안정적으로 보이는 핵심은:

Identity
Task
State
Context
Memory
Capability
Policy
Execution
Verification
Evaluation
Experience

이다.

구현 기술이 바뀌어도 이 개념들은 일정 기간 유지될 가능성이 높다.

82. Candidate Replaceable Layer

반대로 다음은 빠르게 바뀔 가능성이 높다.

LLM Provider
Runtime Framework
Memory Database
Embedding Model
Vector DB
Graph DB
Sandbox Runtime
Orchestration Framework
Evaluation Framework
Protocol

따라서 이들을 상위 Architecture 계약에서 분리한다.

83. Historical / Foundational Integration

오래된 개념 중 현재 통합에 가치가 있는 것:

Actor Model
→ Runtime / Isolation / Messaging

Blackboard
→ Shared Knowledge / Coordination

Planner-Executor
→ Orchestration

HTN
→ Task Decomposition

Global Workspace
→ Selective Information Broadcasting

MapReduce
→ Parallel Execution / Aggregation

Cognitive Architecture
→ Modular Cognition

이것들은 특정 구현으로 채택하지 않고 원칙 Reference로 유지한다.

84. Current Frontier Integration

현재의 Frontier 방향에서 통합에 중요한 개념:

Agent Harness
Durable Execution
Externalized Task State
Context Engineering
Structured Memory
Sandbox / Compute Separation
Tool / Skill systems
Risk-based Authorization
Agent Evaluation
Long-horizon Orchestration
Experience-driven Improvement
Persistent Identity

이 역시 구현 자체가 아니라 Architecture 문제를 해결하는 원칙으로 추상화한다.

85. Future Architecture Scenario

미래에 더 강력한 Model이 등장했다고 가정한다.

Future Model
    ↓
Same Agent Contract
    ↓
Same Identity
    ↓
Same Memory
    ↓
New Context Strategy
    ↓
New Runtime

Architecture가 유지되어야 한다.

86. Future Runtime Scenario

새로운 Runtime이 등장:

Runtime A
→ traditional loop

Runtime B
→ event-driven

Runtime C
→ distributed durable execution

NOAH의:

Session
Task
State
Execution Contract

은 유지되어야 한다.

87. Future Memory Scenario

미래에는 Vector RAG를 대체하는 새로운 Memory architecture가 등장할 수 있다.

Memory v1
→ vector retrieval

Memory v2
→ temporal graph

Memory v3
→ learned state policy

Future Memory
→ unknown

Memory Contract:

Write
Manage
Read
Revision
Forget
Evidence

를 유지한다.

88. Future Identity Scenario

미래 Model이 훨씬 강한 self-modeling 능력을 갖게 되더라도:

Model Self-model
≠
NOAH Identity Core

원칙을 유지한다.

Model capability가 증가해도 Identity Governance가 사라지는 것은 아니다.

89. Future Autonomy Scenario

NOAH의 자율성이 증가하더라도:

More Intelligence
≠
Unlimited Permission

으로 유지한다.

Capability가 증가하면:

Policy
Verification
Containment
Evaluation

도 함께 발전해야 한다.

90. Integrated Candidate Architecture

현재 모든 Review를 하나로 합친 후보:

                               CONSTITUTION
                                    │
                                    ▼
                            IDENTITY / VALUES
                                    │
                                    ▼
                                  AGENT
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                       TASK                SESSION
                         │                     │
                         └──────────┬──────────┘
                                    │
                             ORCHESTRATION
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
               CONTEXT            STATE            MEMORY
                  │                 │                 │
                  └─────────────────┼─────────────────┘
                                    │
                             CAPABILITY
                                    │
                                POLICY
                                    │
                              PERMISSION
                                    │
                            APPROVAL / RISK
                                    │
                                 RUNTIME
                                    │
                              SANDBOX
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
                     ┌──────────────┼──────────────┐
                     │              │              │
                   MEMORY         SKILL        ORCHESTRATION
                  UPDATE         UPDATE          UPDATE
                     │              │              │
                     └──────────────┼──────────────┘
                                    │
                           CONTROLLED ADAPTATION
                                    │
                              FUTURE EXECUTION

이 구조는 Integration Candidate이며 최종 Architecture가 아니다.

91. Integrated Boundary Table
영역	책임	직접 소유하지 않는 것
Identity	지속성 / 핵심 원칙	Runtime 구현
Agent	판단 / 행동 선택	Storage / Sandbox
Task	목표 / 진행 상태	Model
Session	실행 관계	장기 Memory 전체
Orchestration	분해 / 위임 / 통합	Tool 구현
Context	Model-facing projection	Canonical State
State	현재 canonical condition	Model prompt
Memory	과거 정보 / 경험 관리	Current Runtime
Capability	행동 능력	Authorization
Policy	허용 조건	실제 Execution
Permission	실행 권한	Capability 정의
Runtime	실행 Lifecycle	Task Strategy
Sandbox	실행 격리	Agent 판단
Verification	실제 상태 검증	목표 생성
Observability	실행 증거	품질 판정 자체
Evaluation	품질 / 안전 판단	Runtime control
Learning	미래 행동 개선	Constitution 무단 변경
92. Dependency Matrix

초기 원칙:

Identity
→ Agent

Task
→ Agent / Orchestration

Context
→ State / Memory / Task / Policy

Capability
→ Policy

Runtime
→ Task / Agent / Capability

Verification
→ Execution / State

Evaluation
→ Observability / Evidence

Learning
→ Evaluation / Experience / Memory

직접적인 양방향 의존은 최소화한다.

93. Logical Feedback vs Structural Dependency

허용:

Experience
→ Memory
→ Learning
→ Future Behavior
→ New Experience

주의:

Memory Module
↔
State Module

처럼 코드 수준에서 서로 직접 호출하는 구조는 피한다.

가능하면 Interface를 통해 연결한다.

94. Contract-first Architecture

통합 단계의 핵심 원칙:

구현보다 Contract를 먼저 고정한다.

예:

Memory Interface
Capability Contract
Execution Contract
Verification Contract
Evaluation Contract
Identity Contract

구현은 이후 교체 가능하도록 한다.

95. PoC Boundary

이 통합 구조 전체를 한 번에 구현하지 않는다.

PoC는:

Task
 ↓
Agent
 ↓
Context
 ↓
Capability
 ↓
Policy
 ↓
Runtime
 ↓
Verification
 ↓
Evaluation

정도로 작게 시작할 수 있다.

Memory와 Identity는 최소한의 persistence만 연결한다.

96. First Integrated PoC

예:

"NOAH가 작은 repository 작업 하나를 끝까지 수행한다."

Flow:

Task
 ↓
Identity Projection
 ↓
Agent
 ↓
Context
 ↓
Tool Selection
 ↓
Permission
 ↓
Execution
 ↓
Verification
 ↓
Evaluation
 ↓
Experience

이 하나가 전체 통합 구조의 가장 작은 실험이 될 수 있다.

97. Integrated PoC Expansion

PoC 1:

Single Agent

PoC 2:

Persistent State

PoC 3:

Memory

PoC 4:

Security / Approval

PoC 5:

Evaluation / Recovery

PoC 6:

Subagent / Orchestration

PoC 7:

Identity Continuity

순으로 확장할 수 있다.

98. Integration Evaluation

통합 시스템은 다음으로 평가한다.

Correctness
Safety
Boundary Integrity
State Consistency
Recovery
Observability
Memory Utility
Identity Continuity
Cost
Latency
Maintainability
Replaceability
99. Integration Success Criteria

Integration Review가 성공했다고 보기 위한 조건:

1. 책임 경계가 설명 가능하다.
2. 주요 계층의 중복이 없다.
3. 순환 dependency가 통제된다.
4. State / Context / Memory가 분리된다.
5. Capability / Permission / Execution이 분리된다.
6. Agent / Orchestrator / Runtime이 분리된다.
7. Verification / Evaluation이 구분된다.
8. Identity가 Runtime / Model과 독립된다.
9. 미래 구현 교체가 가능하다.
10. 최소 PoC로 구조를 검증할 수 있다.
100. Architecture Quality Criteria

최종 Candidate Architecture를 다음 기준으로 평가한다.

Simplicity
Modularity
Replaceability
Explainability
Security
Reliability
Observability
Recoverability
Scalability
Long-term Maintainability
Future Resilience
101. What Integration Reveals About NOAH

현재까지의 연구를 통합하면 NOAH는 단순:

LLM
+
Prompt

가 아니다.

또한 단순:

Agent
+
Memory

도 아니다.

더 정확하게는:

Identity
+
Cognition
+
Memory
+
Capability
+
Execution
+
Security
+
Evaluation
+
Learning

으로 구성되는 장기 시스템으로 볼 수 있다.

102. NOAH as a System

현재 후보 정의:

Project NOAH는 지속적인 Identity를 유지하면서 환경과 상호작용하고, 경험을 기억하고, 자신의 행동을 평가하며, 경험을 통해 미래 행동을 개선하는 Modular Cognitive Agent System이다.

이 문장은 최종 Vision이 아니라 Integration Review에서 나온 현재 Architecture 해석이다.

103. NOAH vs Current Agent

일반적인 Agent:

Prompt
 ↓
LLM
 ↓
Tool
 ↓
Result

현재 NOAH Candidate:

Identity
 ↓
Task
 ↓
Context / Memory
 ↓
Agent
 ↓
Capability
 ↓
Policy / Security
 ↓
Runtime
 ↓
Environment
 ↓
Verification
 ↓
Evaluation
 ↓
Experience
 ↓
Learning

즉 NOAH는 단일 실행 Agent보다 훨씬 넓은 시스템을 목표로 한다.

104. Long-Term System Loop
                        ┌─────────────┐
                        │   Identity  │
                        └──────┬──────┘
                               │
                               ▼
                             Agent
                               │
                               ▼
                              Task
                               │
                               ▼
                           Execution
                               │
                               ▼
                            Outcome
                               │
                     ┌─────────┴─────────┐
                     │                   │
                  Evaluation          Experience
                     │                   │
                     └─────────┬─────────┘
                               │
                             Memory
                               │
                            Learning
                               │
                     ┌─────────┼─────────┐
                     │         │         │
                   Skill     Routing   Personality
                     │         │         │
                     └─────────┼─────────┘
                               │
                         Future Behavior
                               │
                               └──────→ Agent
105. Core Philosophy Emerging from Integration

현재 Integration에서 자연스럽게 도출되는 원칙:

Principle 1

Model is replaceable.

Principle 2

Memory is externalized.

Principle 3

Capability is controlled by policy.

Principle 4

Execution is observable and verifiable.

Principle 5

Multi-Agent is optional.

Principle 6

Identity is persistent but not immutable in every detail.

Principle 7

Learning changes behavior before it changes identity.

Principle 8

Future technology should replace implementations, not architectural contracts.

106. Historical + Current + Future Synthesis

NOAH의 Architecture는 세 종류의 지식을 함께 사용한다.

Historical
→ enduring principles

Current
→ proven implementations

Future
→ emerging possibilities

그리고:

Historical + Current + Future
           ↓
     NOAH Principle
           ↓
   Candidate Boundary
           ↓
        PoC
           ↓
      Evaluation

의 흐름으로 검증한다.

107. Research Classification

앞으로 모든 아이디어를 다음처럼 분류할 수 있다.

FOUNDATIONAL
→ 오래된 원칙이 지금도 유효

CURRENT
→ 현재 효과적으로 사용되는 구조

EMERGING
→ 아직 검증되지 않았지만 가능성이 높음

EXPERIMENTAL
→ PoC 필요

DEFERRED
→ 지금은 필요하지 않음

REJECTED
→ NOAH와 맞지 않음

이 분류는 "최신이라서 채택"하는 문제를 막는 데 도움이 된다.

108. Integration Review — Current Decisions

현재까지의 통합 판단:

✅ Stable Concept Boundaries

Identity
Agent
Task
State
Context
Memory
Capability
Permission
Runtime
Verification
Evaluation
Experience
🟡 Requires Further Research

Harness boundary
Knowledge boundary
Artifact management
Persistent specialists
Adaptive orchestration
Learned routing
Identity memory
Relationship model
State-aware runtime
🔵 Defer

Distributed microservices
Full event sourcing
Fully learned orchestration
Automatic identity evolution
Automatic self-modification
109. Integration Review — Rejected Directions

현재 NOAH 방향과 맞지 않는 후보:

Agent = LLM
Memory = Vector DB
Context = Source of Truth
Capability = Permission
Multi-Agent by Default
Approval-only Security
Sandbox-only Security
Evaluation = Final Answer
Identity = Prompt
Personality = Tone
Identity = Consciousness
110. Critical Unresolved Questions
Harness의 정확한 범위는 어디까지인가?
Task State는 독립 subsystem이어야 하는가?
Knowledge와 Memory는 어디에서 분리되는가?
Artifact는 별도 subsystem이어야 하는가?
Identity는 어디에 저장되는가?
Relationship은 Memory의 일부인가?
Runtime과 Harness의 경계는 무엇인가?
Orchestrator는 Harness의 일부인가?
Evaluation은 Runtime에 어느 정도 개입하는가?
Learning은 어느 계층을 변경할 수 있는가?
Self Model은 Context State인가 Identity State인가?
Personality는 Memory에서 직접 파생되는가?
Identity Core의 정확한 governance는 무엇인가?
Capability Registry는 어디에 속하는가?
Event System은 공통 Infrastructure인가?
Canonical State의 Source of Truth는 무엇인가?
Long-horizon Task State를 어떻게 보존하는가?
Multi-Agent에서 Identity를 어떻게 계승하는가?
어느 지점부터 물리적 service 분리가 필요한가?
어떤 Boundary를 v0.1 PoC에서 검증해야 하는가?
111. Integration Research Priorities

현재 미해결 문제의 우선순위:

P0
Task / State / Runtime Boundary
P0
Harness Boundary
P0
Memory / Knowledge Boundary
P1
Artifact Management
P1
Identity Persistence
P1
Orchestration Contract
P2
Adaptive / Learned Systems
112. Proposed Next Research

Integration 결과에 따라 다음 Research를 수행한다.

1. Task State
2. Harness Architecture
3. Knowledge / Memory Boundary
4. Artifact Architecture
5. Identity Persistence

그 후 최종 Candidate Architecture를 다시 갱신한다.

113. DDR Preparation

Integration Review에서 나온 주요 결정은 아직 최종 결정이 아니다.

향후 DDR 후보:

DDR-000X
Task State Architecture

DDR-000X
Agent Harness Boundary

DDR-000X
Memory / Knowledge Boundary

DDR-000X
Identity Persistence

DDR-000X
Orchestration Strategy

각 DDR에는:

Context
Candidates
Decision
Reason
Trade-offs
Impact
Alternatives

를 기록한다.

114. Blueprint Preparation

DDR가 끝난 후에야:

02-Architecture

를 수정한다.

Integration Review가 바로 Blueprint가 되는 것은 아니다.

Review
 ↓
Decision
 ↓
DDR
 ↓
Blueprint

의 순서를 유지한다.

115. First Integrated Blueprint Candidate

아직 확정하지 않지만 현재 가장 유력한 형태:

                    ┌─────────────────────┐
                    │     Constitution    │
                    └──────────┬──────────┘
                               │
                         Identity Core
                               │
                              Agent
                               │
                     ┌─────────┴─────────┐
                     │                   │
                   Task               Session
                     │                   │
                     └─────────┬─────────┘
                               │
                         Orchestration
                               │
                    ┌──────────┼──────────┐
                    │          │          │
                 Context      State     Memory
                    │          │          │
                    └──────────┼──────────┘
                               │
                           Capability
                               │
                            Policy
                               │
                          Permission
                               │
                           Runtime
                               │
                        Sandbox / Env
                               │
                           Execution
                               │
                         Verification
                               │
                        Observability
                               │
                          Evaluation
                               │
                         Experience
                               │
                           Learning
                               │
                    Controlled Adaptation

다시 강조하지만 Candidate Blueprint다.

116. PoC Strategy

통합 구조를 검증하기 위한 최소 PoC:

NOAH가 하나의 실제 작업을 장기적으로 수행하고, 작업을 완료하며, 결과를 검증하고, 경험을 저장한다.

최소 Flow:

User Goal
 ↓
Task
 ↓
Identity Projection
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
Sandbox
 ↓
Execution
 ↓
Verification
 ↓
Evaluation
 ↓
Experience
 ↓
Memory
117. PoC Success Criteria
Task Success
State Consistency
Permission Correctness
Execution Recovery
Verification Accuracy
Trace Completeness
Memory Utility
Identity Continuity
Cost
Latency
118. Integration Review Outcome

현재까지의 Architecture Review를 통합하면 Project NOAH는:

지속적인 Identity를 가진 Agent가 Task를 수행하고, Context와 Memory를 통해 과거와 현재의 정보를 활용하며, Capability를 안전하게 실행하고, Runtime을 통해 장기 작업을 지속하고, Verification과 Evaluation을 통해 자신의 행동을 검증하며, Experience를 Memory와 Learning으로 연결해 미래의 행동을 개선하는 Modular Cognitive System

으로 정의하는 것이 가장 유력하다.

하지만 이 정의도 최종 Vision이나 Blueprint가 아니다.

119. Final Principle of Integration

이번 Review에서 가장 중요한 원칙:

NOAH의 Architecture는 미래의 정답을 예측하려는 것이 아니라, 더 나은 정답이 등장했을 때 받아들일 수 있는 구조를 만드는 것이다.

따라서:

Current Best Practice
        +
Historical Wisdom
        +
Emerging Research
        ↓
Stable Architecture Boundary
        ↓
Replaceable Implementation
        ↓
PoC
        ↓
Evaluation
        ↓
Iteration

을 NOAH의 장기 Architecture 운영 원칙으로 검토한다.

120. What We Are Building

최종적으로 우리가 만들고 있는 것은 단순히:

NOAH

하나가 아니다.

현재 Project의 구조적 관점에서는:

NOAH
+
NOAH Development System

이다.

NOAH Development System은:

Research
 ↓
Review
 ↓
Decision
 ↓
Blueprint
 ↓
PoC
 ↓
Implementation
 ↓
Evaluation
 ↓
Experience
 ↓
Iteration

의 반복을 가능하게 한다.

121. Project-level Feedback Loop
External Research
        ↓
Architecture Review
        ↓
Integration Review
        ↓
DDR
        ↓
Blueprint
        ↓
PoC
        ↓
Evaluation
        ↓
Experience
        ↓
Development System Improvement
        ↓
Future Research

즉:

프로젝트를 운영하는 방식 자체도 NOAH가 장기적으로 기억하고 배우는 방식과 닮아간다.

122. Review Boundary

이번 Integration Review에서는 다음을 최종 확정하지 않는다.

Final Blueprint
Final Runtime
Final Memory
Final Identity
Final Orchestrator
Final Capability system
Final Security implementation
Final Evaluation stack
Final Physical deployment architecture

이들은 다음 단계에서 결정한다.

123. Review Status

Current status:

Architecture Research
        ✅ Complete for v0.1 scope

Individual Reviews
        ✅ Complete

Integration
        🟡 Review

Major Conflicts
        🟡 Under investigation

DDR
        ⏳ Pending

Blueprint
        ⏳ Pending

PoC
        ⏳ Pending
124. Next Step

Integration Review 이후:

Architecture Integration Review
        ↓
Identify Conflicts
        ↓
Prioritized Research
        ↓
Resolve Boundaries
        ↓
DDR
        ↓
02-Architecture
        ↓
Integrated PoC
        ↓
Evaluation

으로 진행한다.

현재 가장 먼저 검토할 후보:

P0 — Task State / Runtime Boundary
P0 — Harness Boundary
P0 — Memory / Knowledge Boundary
P1 — Artifact Architecture
P1 — Identity Persistence
P1 — Orchestration Contract
125. Final Statement

NOAH는 현재의 기술을 모방하기 위해 만들어지는 시스템이 아니다.

과거의 좋은 아이디어를 잃지 않고, 현재의 가장 유용한 기술을 활용하며, 미래의 더 나은 기술을 받아들일 수 있도록 설계되는 시스템이다.

따라서 NOAH의 Architecture에서 가장 오래 살아남아야 하는 것은 특정 Model이나 Framework가 아니라, 책임의 경계와 그것을 연결하는 Contract다.