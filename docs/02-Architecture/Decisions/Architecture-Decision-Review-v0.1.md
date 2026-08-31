# Architecture Decision Review

> Project NOAH Architecture Decision Review
> Review 대상: DDR-001 ~ DDR-006
> Review Version: 0.1
> Status: Review
> Date: 2026-09-01

---

# 1. Review Purpose

Project NOAH의 첫 번째 Architecture Decision Set인
DDR-001부터 DDR-006까지를 하나의 Architecture로 통합했을 때
각 Decision 사이에 모순, 책임 중복, 누락 또는 불필요한 결합이 존재하는지 검토한다.

핵심 질문:

> "DDR-001 ~ DDR-006은 하나의 일관된 NOAH Architecture를 구성할 수 있는가?"

이번 Review는 새로운 Architecture 영역을 무분별하게 추가하기 위한 문서가 아니다.

목적은 지금까지의 Decision을:

- KEEP
- REFINE
- MERGE
- SPLIT
- DEFER
- CONFLICT

관점에서 평가하고,
실제 `02-Architecture` Blueprint로 전환할 수 있는지를 판단하는 것이다.

---

# 2. Review Inputs

이번 Review의 직접적인 대상:

```text
DDR-001
Task State / Runtime Boundary

DDR-002
Harness Boundary

DDR-003
Memory / Knowledge Boundary

DDR-004
Artifact Architecture

DDR-005
Identity Persistence

DDR-006
Orchestration Contract

관련 Research 및 Integration Review는 근거 자료로 사용하지만,
이번 Review의 직접적인 검토 대상은 Architecture Decision이다.

3. Review Classification

각 Decision 또는 Boundary를 다음 상태로 분류한다.

KEEP
→ 현재 Decision을 유지한다.

REFINE
→ 핵심 방향은 유지하지만 표현이나 책임을 명확하게 한다.

MERGE
→ 별도의 Decision보다 다른 Decision과 통합하는 것이 적절하다.

SPLIT
→ 하나의 Decision에 너무 많은 책임이 포함되어 분리가 필요하다.

DEFER
→ 현재 결정하지 않고 PoC 또는 추가 Evidence 이후 결정한다.

CONFLICT
→ 다른 Decision과 직접 충돌하여 해결이 필요하다.
4. Current Decision Set

현재 Architecture Decision 흐름:

Identity
   ↓
Agent
   ↓
Task
   ↓
Orchestration
   ↓
Harness
   ↓
Runtime
   ↓
Execution

정보 영역:

Task State
    │
    ├── Memory
    ├── Knowledge
    └── Artifact
          ↓
       Context
          ↓
        Agent

실행 통제:

Capability
   ↓
Policy
   ↓
Permission
   ↓
Runtime
   ↓
Execution
   ↓
Evidence
   ↓
Verification
5. High-Level Review Result

현재 DDR-001 ~ DDR-006 사이에는
Architecture 전체를 무효화할 정도의 직접적인 Conflict는 발견되지 않았다.

초기 판정:

DDR-001 → KEEP / REFINE
DDR-002 → KEEP / REFINE
DDR-003 → KEEP
DDR-004 → KEEP
DDR-005 → KEEP / REFINE
DDR-006 → KEEP / REFINE

핵심 Architecture 방향은 유지한다.

다만 Blueprint 이전에 몇 가지 책임과 용어를 명확히 할 필요가 있다.

6. DDR-001 Review
Decision

Task State와 Runtime을 분리한다.

Task State
≠
Runtime

Task State는 durable canonical progress를 유지하며,
Runtime은 execution lifecycle을 담당한다.

Review

판정:

KEEP

이 Decision은 Long-running Task, Recovery, Pause / Resume 및
Runtime replacement를 위해 필요한 핵심 Boundary다.

7. DDR-001 Strengths

DDR-001을 통해 다음이 명확해졌다.

Task ≠ Session
Task State ≠ Execution State
Task State ≠ Context
Runtime ≠ Task

특히:

Runtime Failure
↓
Task State survives
↓
New Runtime
↓
Context Reconstruction
↓
Resume

구조가 NOAH의 장기 실행 Architecture와 잘 맞는다.

8. DDR-001 Refinement

Task State가 모든 종류의 State를 의미하지 않도록 주의한다.

향후 Architecture에서는 최소한:

Task State
Execution State
Environment State
Workspace State
Orchestration State

를 의미적으로 구분할 필요가 있다.

그러나 모든 State를 독립적인 Store로 구현해야 한다는 의미는 아니다.

판정:

REFINE semantics
DEFER physical implementation
9. Canonical State Rule

Task의 진행 상태에 대한 Source of Truth는 Task State다.

Task State
= canonical task progress

다음은 Task State의 대체물이 아니다.

Context
Memory
Agent internal reasoning
Runtime memory
Conversation history

이 원칙을 유지한다.

10. State Mutation Refinement

State 변경의 책임을 특정 Agent나 Evaluation component가 직접 소유하는 구조는 피한다.

후보 흐름:

Execution
↓
Observation / Evidence
↓
Verification
↓
State Transition Decision
↓
Task State Commit

Evaluation은 품질을 평가할 수 있지만
Task State의 Storage 또는 mutation authority 자체를 소유하지 않는다.

11. DDR-002 Review
Decision

Agent와 Infrastructure 사이에 Logical Harness Boundary를 둔다.

판정:

KEEP

Harness는 NOAH Architecture의 중요한 안정 경계로 유지한다.

12. Harness Core Meaning

Harness의 핵심 의미는:

Agent와 Infrastructure 사이의 Stable Execution Contract

로 유지한다.

Harness는 거대한 모든 기능의 소유자가 아니다.

13. Harness Ownership Refinement

DDR-002에서 Harness는 다음을 연결한다.

Context
Capability
Policy
Runtime
Memory Access
Recovery
Observability
Verification

그러나:

Harness coordinates/accesses
≠
Harness owns everything

으로 명확히 한다.

예:

Harness
↓
Memory Interface
↓
Memory System

이지:

Harness
└── Memory Database

를 의미하지 않는다.

판정:

REFINE
14. Harness vs Runtime

다음 경계를 유지한다.

Harness
= stable execution boundary

Runtime
= execution lifecycle implementation

후보:

Agent
↓
Harness
↓
Runtime
↓
Execution

Runtime은 교체 가능하며,
Harness Contract는 가능한 한 안정적으로 유지한다.

15. Harness vs Orchestrator

가장 중요한 책임 구분 중 하나다.

Orchestrator
= What should happen?

Harness
= How selected execution can happen safely and persistently

보다 구체적으로:

Orchestrator
├── Decomposition
├── Planning
├── Delegation
├── Scheduling
├── Replanning
└── Aggregation

Harness
├── Context access
├── Capability access
├── Policy enforcement integration
├── Runtime access
├── Recovery integration
└── Observability integration

로 정리한다.

16. Orchestrator Ownership Rule

Orchestrator는 다음을 직접적인 Source of Truth로 소유하지 않는다.

Task State
Memory
Knowledge
Artifact
Identity

Orchestrator는 이들을 Interface를 통해 사용한다.

17. Harness Physical Boundary

Harness를 처음부터 별도의 Service로 구현하지 않는다.

판정:

DEFER

초기 후보:

Modular Monolith

내부의 Logical Boundary로 구현한다.

Physical separation은 PoC와 실제 요구사항 이후 검토한다.

18. DDR-003 Review
Decision

Memory와 Knowledge를 의미적으로 분리한다.

Memory
≠
Knowledge

그러나 공통 Information / Retrieval Infrastructure를 공유할 수 있다.

판정:

KEEP
19. Memory Definition Review

Memory는 기본적으로:

Experience
Personal continuity
Project continuity
Important historical context
Learned lessons

을 다룬다.

Memory의 가치 기준은 단순 저장량이 아니라:

미래의 판단과 행동을 실제로 개선하는가?

이다.

20. Knowledge Definition Review

Knowledge는:

Facts
External information
Project information
Research
Documentation
Structured knowledge

등을 다룬다.

특히 Knowledge는:

Source Authority
Freshness
Version
Provenance

가 중요하다.

21. Memory / Knowledge Physical Storage

의미적 구분이 Physical Storage 분리를 강제하지 않는다.

가능:

Memory ─────┐
            ├── Shared Infrastructure
Knowledge ──┘

또는:

Memory Store
Knowledge Store

둘 다 허용한다.

판정:

DEFER physical storage
22. Unified Information Interface

현재 후보:

Memory
     ↘
      Information / Retrieval Interface
     ↗
Knowledge

이 Interface는 Semantic Layer의 차이를 숨기지 않는다.

즉:

Unified Interface
≠
Unified Meaning

이다.

23. State vs Memory vs Knowledge

최종 의미 구분:

State
= 현재 canonical condition

Memory
= 경험과 지속성

Knowledge
= 사실과 정보

이 경계를 Architecture Blueprint에서도 유지한다.

24. DDR-004 Review
Decision

Artifact를 semantic work object로 정의한다.

Artifact
≠
File

판정:

KEEP
25. Artifact Core Meaning

Artifact는:

NOAH의 작업이 현실 세계에 남긴 지속적인 결과물

로 본다.

예:

Document
Code
Dataset
Media
Build
Test Result
Evaluation Result
Configuration
Evidence
26. Artifact vs Task State

다음 구조를 유지한다.

Task State
↓
Artifact Reference
↓
Artifact

Task State에 Artifact 전체를 저장하지 않는다.

27. Artifact vs Workspace
Workspace
= 작업 환경

Artifact
= 지속적인 작업 대상 / 결과물

Workspace가 삭제되어도 Durable Artifact는 유지될 수 있다.

28. Artifact vs Memory
Artifact
= 실제 결과물

Memory
= 그 결과물을 만들거나 사용한 경험

예:

Artifact:
Architecture document

Memory:
왜 이 Architecture를 선택했는지에 대한 경험
29. Artifact vs Knowledge

Artifact는 Knowledge Source가 될 수 있다.

Artifact
↓
Extraction / Validation
↓
Knowledge

그러나 Artifact 자체를 자동으로 Knowledge라고 취급하지 않는다.

30. Artifact vs Evidence

Artifact와 Evidence 역시 동일하지 않다.

Artifact
→ Evidence가 될 수 있음

Evidence
→ 반드시 Artifact일 필요는 없음

Evidence는 다음도 될 수 있다.

Observation
Tool Result
Test Result
Environment State
External Source

판정:

REFINE terminology
31. Artifact Storage

Artifact의 Physical Storage는 현재 결정하지 않는다.

후보:

Filesystem
Git
Database
Object Storage
External Repository

판정:

DEFER

Stable한 것은 Artifact Contract이며,
Storage 구현은 Replaceable하다.

32. DDR-005 Review
Decision

Identity를 Protected Identity Contract로 관리한다.

Identity
≠
Model
≠
Runtime
≠
Session
≠
Memory

판정:

KEEP
33. Identity Core Review

Identity Core 후보:

ID
Origin
Core Values
Fundamental Commitments
Root Role
Continuity
Version

특히 Constitution과 Core Values는 일반 Learning에 의해 자동 수정되지 않는다.

34. Identity vs Constitution

Architecture상:

Constitution
↓
Identity Core
↓
Agent

방향을 유지한다.

Constitution은 Identity보다 높은 Governance Layer로 본다.

35. Identity Change Refinement

Identity를 완전한 Immutable Object로 만들지는 않는다.

대신:

Protected Core
+
Governed Evolution

을 채택한다.

즉:

Automatic uncontrolled mutation
→ Reject

Explicit governed evolution
→ Allow

이다.

판정:

REFINE
36. Identity vs Personality
Identity Core
= 높은 안정성

Personality
= 적응 가능

Behavior
= Context에 따라 동적

Self Model
= 현재 능력과 상태에 따라 동적

이 계층을 혼합하지 않는다.

37. Identity vs Memory

Memory가 Identity의 역사적 연속성을 지원할 수 있다.

Identity
↔
Identity-relevant Memory

그러나:

Memory
≠
Identity Source of Truth

이다.

38. Identity vs Permission

Identity를 Permission 자체로 사용하지 않는다.

후보:

Identity
↓
Principal / Role / Scope
↓
Policy
↓
Permission

Identity만 확인되었다고 권한이 자동 부여되는 구조는 사용하지 않는다.

판정:

REFINE security relationship
39. Root vs Derived Identity

Multi-Agent 구조:

NOAH Root Identity
        │
        ├── Specialist Role
        └── Temporary Worker

를 기본 후보로 유지한다.

Temporary Subagent를 매번 새로운 Persistent Identity로 만들지 않는다.

40. Forking

다음을 구분한다.

Spawn
→ 같은 시스템 안의 temporary execution entity

Continuation
→ 같은 Identity의 지속

Fork / Clone
→ 새로운 Persistent Identity

Fork는 별도 Governance 대상이다.

41. DDR-006 Review
Decision

Orchestration의 핵심 상호작용을 명시적인 Contract로 정의한다.

판정:

KEEP
42. Contract Core Principle

다음을 유지한다.

Contract
≠
Protocol

Contract
≠
Schema

Contract:

Schema
+
Semantics
+
Permission
+
Lifecycle
+
Failure
+
Verification

Protocol:

How the contract is transported
43. Contract vs Implementation

Stable Contract와 구현을 분리한다.

예:

Delegation Contract
↓
MCP Adapter

Delegation Contract
↓
A2A Adapter

Delegation Contract
↓
Internal Function Call

Future Protocol이 등장해도 Contract 자체를 유지할 수 있어야 한다.

44. Contract Explosion Risk

DDR-006에는 다음 Contract 후보가 존재한다.

Task
Plan
Delegation
Agent
Context
Capability
Result
Evidence
Verification
Budget
Cancellation
Recovery
Security
Runtime
...

Conceptual Contract를 모두 독립적인 코드 Object 또는 Service로 구현하면
Architecture가 과도하게 복잡해질 수 있다.

판정:

REFINE
45. Conceptual Contract vs Implemented Schema

다음을 명확히 구분한다.

Conceptual Contract
= Architecture-level responsibility agreement

Implemented Schema
= 실제 코드에서 표현하는 concrete structure

모든 Conceptual Contract가 반드시 독립 Schema가 될 필요는 없다.

46. Minimum Contract Set Candidate

첫 번째 PoC에서 필요한 최소 Contract 후보:

Task
Execution Request
Capability
Result
Evidence
Verification

Orchestration PoC가 추가되면:

Plan
Delegation
Budget
Recovery

를 확장할 수 있다.

정확한 v0.1 Schema는 Specification 단계에서 결정한다.

47. Multi-Agent Default Review

Multi-Agent는 기본 실행 방식이 아니다.

기본:

Task
↓
Single Agent
↓
Harness
↓
Execution

필요할 때만:

Task
↓
Orchestrator
↓
Multiple Agents

를 사용한다.

판정:

KEEP
48. Delegation vs Handoff

Architecture Blueprint에서 다음 차이를 유지한다.

Delegation
= 일부 작업을 다른 Agent에 맡김

Agent-as-Tool
= Child 결과가 Parent에게 반환됨

Handoff
= 실행 Control 자체가 다른 Agent로 이동

이들을 동일한 orchestration primitive로 취급하지 않는다.

49. Permission Propagation

기본 원칙:

Child Permission
⊆
Parent Permission

를 유지한다.

추가 Permission이 필요한 경우:

Request
↓
Policy
↓
Approval if required
↓
Granted Scope

를 거친다.

50. Budget Propagation

기본:

Child Budget
≤
Parent Remaining Budget

를 유지한다.

Budget은 단순 Token뿐 아니라:

Time
Tool Calls
Compute
Storage
Network
Agent Count

등을 포함할 수 있다.

51. Result vs Evidence vs Verification

다음 세 가지를 분리한다.

Result
= 무엇이 수행되었다고 보고되는가

Evidence
= 그 결과를 뒷받침하는 무엇이 존재하는가

Verification
= Evidence를 통해 요구사항 충족 여부를 확인하는 과정

이 구분은 핵심 Architecture Boundary로 유지한다.

52. Verification vs Evaluation

다음 역시 분리한다.

Verification
= 요구된 상태가 실제로 달성되었는가?

Evaluation
= 수행 과정과 결과의 품질은 어떠했는가?

예:

File exists
→ Verification

File quality = 8/10
→ Evaluation
53. Execution Completion Rule

Agent의 self-report만으로 Task를 Completed로 변경하지 않는다.

기본 후보:

Agent Result
↓
Evidence
↓
Verification
↓
Completion Decision
↓
Task State

High-impact 작업일수록 Verification 요구를 강화한다.

54. Cross-DDR Dependency Review

현재 Dependency:

DDR-005 Identity
        ↓
      Agent
        ↓
DDR-006 Orchestration
        ↓
DDR-002 Harness
        ↓
DDR-001 Runtime
        ↓
     Execution

이 흐름에서 직접적인 순환 Dependency는 필요하지 않다.

55. Information Dependency Review

정보 흐름:

Task State
Memory
Knowledge
Artifacts
Conversation
Environment
Policy
    ↓
Context Projection
    ↓
Agent

Context가 다시 Source of Truth가 되는 구조를 사용하지 않는다.

56. Execution Dependency Review

실행 흐름:

Agent
↓
Capability Request
↓
Policy
↓
Permission
↓
Harness
↓
Runtime
↓
Sandbox / Environment
↓
Execution

실제 구현에서 Harness와 Policy의 호출 순서는 달라질 수 있지만
Security enforcement가 Agent 판단만으로 우회되지 않아야 한다.

57. Result Dependency Review
Execution
↓
Observation
↓
Result / Evidence
↓
Verification
↓
Task State Transition
↓
Evaluation

Evaluation은 State Storage를 소유하지 않는다.

58. Recovery Dependency Review
Runtime Failure
↓
Task State
+
Checkpoint
+
Artifacts
+
Execution Record
↓
New Runtime
↓
Context Reconstruction
↓
Resume

Recovery가 이전 Model Context 전체의 완벽한 복원을 요구하지 않도록 한다.

59. Identity Continuity Review
Identity Store
↓
Identity Projection
↓
Agent
↓
Session / Task

Runtime 또는 Session이 종료되어도 Identity Store는 지속된다.

60. Learning Dependency Review

현재 후보:

Execution
↓
Evidence
↓
Evaluation
↓
Experience
↓
Memory
↓
Learning
↓
Improvement Proposal

중요한 점:

Learning
≠
Automatic Core Mutation

이다.

61. Controlled Adaptation

위험도에 따라 변경 authority를 다르게 한다.

후보:

LOW
Skills / Procedures

MEDIUM
Routing / Preferences / Personality

HIGH
Policy / Identity Core / Governance

High-risk 변경은 자동 적용하지 않는다.

62. Circular Dependency Review

논리적 Feedback Loop와 코드-level Circular Dependency를 구분한다.

예:

Memory
→ Context
→ Agent
→ Experience
→ Memory

는 정상적인 Feedback Loop다.

하지만 코드 구조가:

Memory Module
imports Agent

Agent Module
imports Memory

처럼 강한 순환 의존성을 가져야 한다는 의미는 아니다.

63. Logical Architecture vs Physical Architecture

현재 DDR은 Logical Architecture를 정의한다.

Logical Component
≠
Process
≠
Container
≠
Microservice

초기에는 Physical Architecture를 최소화한다.

64. Initial Physical Direction

초기 후보:

NOAH
└── Modular Monolith

내부에 Logical Modules를 둔다.

예:

Core
Runtime
Harness
Information
Artifacts
Capability
Security
Evaluation
Orchestration

정확한 Package 구조는 Blueprint 및 Specification 단계에서 결정한다.

65. Premature Distribution Review

현재 다음을 별도 Microservice로 만들 근거는 충분하지 않다.

Identity Service
Memory Service
Artifact Service
Orchestration Service
Harness Service

판정:

DEFER

실제 Scalability / Isolation / Deployment 요구가 확인된 이후 판단한다.

66. Technology Lock-in Review

현재 DDR은 다음 구현을 요구하지 않는다.

Specific LLM
Specific Agent Framework
Specific Vector DB
Specific Graph DB
Specific SQL Database
Specific Workflow Engine
Specific Sandbox
Specific Protocol

이 상태를 유지한다.

67. Stable Architecture Contracts

현재 높은 수준에서 유지할 후보:

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
Result
Evidence
Verification
Evaluation

그리고 이들을 연결하는:

Harness
Orchestration
Contract

이다.

68. Replaceable Implementations

다음은 교체 가능해야 한다.

Model
Model Provider
Runtime Framework
Agent Framework
Orchestrator Implementation
Memory Backend
Knowledge Backend
Retrieval Engine
Artifact Storage
Sandbox
Telemetry Backend
Protocol
Transport
69. Protocol Position

Protocol은 Capability 자체나 Core Architecture가 아니다.

후보:

Architecture Contract
↓
Protocol Adapter
↓
Transport

예:

Contract
├── Internal Adapter
├── MCP Adapter
├── A2A Adapter
└── Future Adapter
70. Capability Position

Capability는 NOAH가 수행할 수 있는 행동 또는 절차적 기능을 표현한다.

후보:

Tool
Skill
Workflow
Agent Delegation

Protocol은 Capability와 구분한다.

Capability
≠
Protocol
71. Security Boundary Review

현재 Security 흐름:

Input
↓
Instruction / Trust Analysis
↓
Capability Request
↓
Policy
↓
Permission
↓
Approval if required
↓
Credential Broker
↓
Sandbox / Execution Boundary
↓
Execution
↓
Verification
↓
Audit

Agent가 Credential 자체를 직접 소유하지 않는 방향을 유지한다.

72. Least Privilege

모든 Capability 실행의 기본 원칙:

Minimum required scope
+
Minimum required duration
+
Minimum required capability

을 지향한다.

73. Default Deny

Sensitive 또는 High-impact Capability의 경우:

Unknown permission
→ Deny / Ask

를 기본으로 한다.

Agent의 추론 능력이 증가하더라도 Permission이 자동 증가하지 않는다.

74. Observability Review

다음 식별자가 가능한 한 연결될 수 있어야 한다.

Trace ID
Task ID
Session ID
Agent ID
Execution ID
Capability Call ID
Artifact ID
Verification ID

모든 Component가 모든 ID를 항상 포함해야 한다는 의미는 아니다.

75. Evidence Package

중요 Task에서는 Episode 단위 Evidence를 구성할 수 있다.

후보:

Task
Plan
Capability Calls
Artifacts
Observations
State Changes
Verification
Evaluation
Errors
Recovery

이를 통해 이후 Failure Attribution과 Learning에 활용한다.

76. Failure Attribution

실패의 원인을 단순히 "Agent가 실패했다"로 기록하지 않는다.

후보 분류:

Model
Context
Memory
Knowledge
Tool
Capability
Policy
Permission
Runtime
Environment
Planning
Verification
Human Input
77. Architecture Conflict Matrix
Boundary	Result
Task State vs Runtime	No conflict
Harness vs Runtime	No conflict, responsibility refinement required
Harness vs Orchestrator	No conflict, ownership clarification required
Memory vs Knowledge	No conflict
Memory vs Identity	No conflict
Artifact vs Memory	No conflict
Artifact vs Knowledge	No conflict
Artifact vs Evidence	No conflict, semantic refinement required
Identity vs Permission	No conflict, security relationship refinement required
Contract vs Protocol	No conflict
Verification vs Evaluation	No conflict, state mutation refinement required
78. Decision Classification Summary
DDR-001
KEEP
+
REFINE State Mutation semantics
DDR-002
KEEP
+
REFINE Harness ownership semantics
DDR-003
KEEP
DDR-004
KEEP
+
REFINE Artifact / Evidence distinction
DDR-005
KEEP
+
REFINE Identity change and security relationship
DDR-006
KEEP
+
REFINE Conceptual Contract vs Implemented Schema
79. Decisions That Remain Accepted

이번 Review의 Refinement는 기존 DDR의 핵심 결정을 뒤집지 않는다.

따라서:

DDR-001 → Accepted
DDR-002 → Accepted
DDR-003 → Accepted
DDR-004 → Accepted
DDR-005 → Accepted
DDR-006 → Accepted

상태를 유지한다.

80. DDR Amendment Policy

현재 Refinement 수준은 기존 DDR을 즉시 다시 작성할 정도의
Decision reversal로 보지 않는다.

Architecture Blueprint에서 정제된 의미를 사용한다.

향후:

Decision 자체가 변경되거나
핵심 Alternative 선택이 바뀌거나
중요한 Consequence가 뒤집히는 경우

해당 DDR을:

Superseded
Amended
Deprecated

등으로 관리한다.

81. No New DDR Required Yet

현재 Review에서 새 DDR이 즉시 필요한 Critical Conflict는 발견되지 않았다.

따라서:

DDR-007

을 지금 바로 만들지 않는다.

새 Decision은 실제 Blueprint 또는 PoC에서
새로운 Architecture Choice가 발생했을 때 만든다.

82. Deferred Decisions

다음은 의도적으로 결정하지 않는다.

Final Model
Final Runtime Framework
Final Agent Framework
Task State Storage
Memory Backend
Knowledge Backend
Vector Database
Graph Database
Artifact Storage
Identity Storage
Sandbox Technology
Telemetry Stack
Workflow Engine
MCP / A2A adoption
Message Bus
Microservice decomposition
Event Sourcing
83. Event Architecture

Event는:

Observability
Audit
Recovery
State Transition
Integration

에 중요할 가능성이 높다.

그러나 현재:

Event Log
≠
Event Sourcing

으로 구분한다.

Full Event Sourcing 채택은:

DEFER

한다.

84. Registry Architecture

향후 다음 Registry 후보가 존재한다.

Capability Registry
Artifact Registry
Agent Registry
Contract Registry

그러나 초기부터 각각 별도의 시스템을 만들지 않는다.

필요성이 검증될 때 도입한다.

85. Architecture Readiness

현재 평가:

Conceptual Architecture
→ High readiness

Logical Boundaries
→ High readiness

Decision Consistency
→ High readiness

Contract Details
→ Medium readiness

Physical Architecture
→ Low readiness by design

Implementation Details
→ Intentionally open
86. Blueprint Readiness

다음 조건을 검토한다.

☑ Major boundaries defined
☑ P0 research completed
☑ P1 research completed
☑ Integration review completed
☑ DDR-001 ~ DDR-006 completed
☑ Cross-DDR conflicts reviewed
☑ Critical contradictions absent
☑ Stable vs replaceable elements identified
☑ Deferred decisions documented
☑ Initial PoC direction exists

따라서:

Architecture Blueprint
→ READY

로 판단한다.

87. Blueprint Objective

다음 단계의 Architecture 문서는:

"왜 이렇게 결정했는가?"

를 다시 장황하게 설명하는 문서가 아니다.

그 질문의 답은 Research와 DDR에 있다.

Blueprint는:

"현재 NOAH Architecture가 실제로 어떻게 구성되어 있는가?"

를 설명해야 한다.

88. Research / DDR / Architecture Separation
11-Research
→ Why did we investigate this?
→ What did we discover?

02-Architecture/Decisions
→ What did we decide?

02-Architecture
→ What is the current architecture?

이 경계를 유지한다.

89. Candidate Blueprint Structure

후보:

docs/02-Architecture/
│
├── README.md
├── System-Architecture.md
├── Architecture-Principles.md
│
├── Core/
│   ├── Identity.md
│   ├── Agent.md
│   └── Task.md
│
├── Runtime/
│   ├── Session.md
│   ├── State.md
│   ├── Context.md
│   ├── Harness.md
│   └── Runtime.md
│
├── Information/
│   ├── Memory.md
│   ├── Knowledge.md
│   └── Retrieval.md
│
├── Artifacts/
│   └── Artifact.md
│
├── Capability/
│   ├── Capability.md
│   ├── Tool.md
│   ├── Skill.md
│   └── Workflow.md
│
├── Security/
│   ├── Policy.md
│   ├── Permission.md
│   └── Execution-Security.md
│
├── Orchestration/
│   └── Orchestration.md
│
├── Evaluation/
│   ├── Verification.md
│   ├── Observability.md
│   └── Evaluation.md
│
└── Decisions/
    ├── DDR-001...
    ├── DDR-002...
    ├── DDR-003...
    ├── DDR-004...
    ├── DDR-005...
    ├── DDR-006...
    └── Architecture-Decision-Review-v0.1.md

실제 Folder 구조는 Blueprint 작성 과정에서 단순화할 수 있다.

90. Avoid Architecture Explosion

후보 Folder 또는 Component가 존재한다고 해서
모두 실제 Package / Class / Service로 만들어서는 안 된다.

핵심 원칙:

Conceptual Boundary
≠
Implementation Unit

초기 구현은 가능한 한 단순하게 유지한다.

91. Candidate System Architecture

현재 Decision Set을 반영한 Logical Architecture 후보:

                         CONSTITUTION
                              │
                       GOVERNANCE
                              │
                       IDENTITY CORE
                              │
                            AGENT
                              │
                             TASK
                              │
                       ORCHESTRATION
                              │
                           HARNESS
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
     CONTEXT                STATE               CAPABILITY
        │                     │                     │
        │          ┌──────────┼──────────┐          │
        │          │          │          │          │
        │       MEMORY    KNOWLEDGE   ARTIFACT      │
        │                                           │
        └─────────────────────┬─────────────────────┘
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
                           RESULT
                              │
                          EVIDENCE
                              │
                       VERIFICATION
                              │
                       OBSERVABILITY
                              │
                         EVALUATION
                              │
                         EXPERIENCE
                              │
                           MEMORY
                              │
                          LEARNING
                              │
                    CONTROLLED ADAPTATION

이 Diagram은 Logical Architecture 후보이며
Physical deployment를 의미하지 않는다.

92. Candidate Primary Flow

일반적인 Task:

User Intent
↓
Task
↓
Task State
↓
Agent
↓
Context Projection
↓
Decision
↓
Capability Request
↓
Policy / Permission
↓
Harness
↓
Runtime
↓
Execution
↓
Result
↓
Evidence
↓
Verification
↓
Task State Update
↓
Evaluation
93. Candidate Recovery Flow
Execution
↓
Runtime Failure
↓
Persisted Task State
+
Artifacts
+
Checkpoint / Execution Record
↓
New Runtime
↓
Context Reconstruction
↓
Resume
94. Candidate Information Flow
State
Memory
Knowledge
Artifacts
Conversation
Environment
     ↓
Information Selection
     ↓
Context Projection
     ↓
Agent
95. Candidate Learning Flow
Task Execution
↓
Evidence
↓
Evaluation
↓
Experience
↓
Memory Candidate
↓
Validation
↓
Memory
↓
Reflection
↓
Lesson
↓
Improvement Proposal
↓
Evaluation / Governance
↓
Controlled Adaptation
96. Candidate Identity Flow
Constitution
↓
Identity Store
↓
Identity Core
↓
Identity Projection
↓
Agent
↓
Behavior

Experience may influence:

Personality
Preferences
Relationship
Self Model

but does not directly rewrite the Protected Identity Core.

97. Candidate Orchestration Flow

Single Agent default:

Task
↓
Agent
↓
Harness
↓
Execution

When necessary:

Task
↓
Orchestrator
↓
Plan
↓
Delegation
├── Agent A
├── Agent B
└── Agent C
     ↓
Results
     ↓
Evidence
     ↓
Aggregation
     ↓
Verification
98. Initial PoC Principle

첫 PoC에서 전체 Architecture를 완벽하게 구현하지 않는다.

목적:

Decision이 실제 시스템에서도 의미 있는 Boundary인지 검증한다.

99. Initial PoC Candidate

첫 통합 PoC 후보:

User
↓
Task
↓
Task State
↓
Single Agent
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

최소 Identity와 Harness Boundary를 함께 연결한다.

100. PoC Expansion Order

후보 순서:

PoC 1
Single Agent Execution

PoC 2
Durable Task State

PoC 3
Runtime Recovery

PoC 4
Harness Boundary

PoC 5
Artifact Persistence

PoC 6
Memory / Knowledge Retrieval

PoC 7
Permission / Security

PoC 8
Verification / Evaluation

PoC 9
Orchestration / Delegation

PoC 10
Identity Continuity

실제 순서는 Dependency에 따라 조정할 수 있다.

101. PoC Evaluation

PoC는 최소 다음을 평가한다.

Correctness
Reliability
Recoverability
Security
Observability
Maintainability
Replaceability
Context Quality
Memory Utility
Artifact Integrity
Identity Continuity
Cost
Latency
102. Architecture Revision Rule

PoC가 DDR과 다른 결과를 보여주면
구현을 억지로 DDR에 맞추지 않는다.

대신:

Evidence
↓
Review
↓
DDR Amendment / Superseding DDR
↓
Architecture Revision

을 따른다.

103. Current Risks
Over-Abstraction

Architecture 개념이 실제 구현보다 지나치게 많아질 위험.

Contract Explosion

모든 의미적 Contract가 코드 Object가 되는 위험.

Harness Centralization

Harness가 모든 책임을 흡수하는 위험.

State Complexity

다양한 State가 과도하게 분리되는 위험.

Memory Complexity

Memory / Knowledge / Artifact 관계가 지나치게 복잡해지는 위험.

Identity Rigidity

Identity 보호가 변화와 학습을 막는 위험.

Premature Multi-Agent

필요하지 않은 상황에서 Agent 수가 늘어나는 위험.

Premature Distribution

Logical Module을 Microservice로 오해하는 위험.

104. Risk Mitigation Principles
Simple first

Logical before physical

Contract before framework

Evidence before optimization

Single Agent before Multi-Agent

Explicit permission before autonomy

Verification before completion

Protected identity before uncontrolled adaptation

Replaceable implementation before technology lock-in
105. Decision Set Coherence

현재 DDR-001 ~ DDR-006은 다음 하나의 방향으로 수렴한다.

Persistent Identity
+
Durable Task
+
Explicit State
+
Projected Context
+
Memory / Knowledge
+
Persistent Artifacts
+
Controlled Capabilities
+
Permissioned Execution
+
Replaceable Runtime
+
Explicit Contracts
+
Verification
+
Evaluation
106. NOAH Architecture Character

현재 Decision Set에 따르면 NOAH는 단순:

Chatbot

도 아니고:

LLM Wrapper

도 아니며:

Tool Calling Agent

만도 아니다.

현재 Candidate:

Persistent, contract-driven, capability-based Agent System with durable task execution, protected identity, explicit information boundaries, controlled execution, verification, evaluation and governed adaptation.

107. What Is Stable

현재 Review 기준 높은 confidence:

Identity ≠ Model
Task ≠ Session
Task State ≠ Runtime
Context ≠ State
Memory ≠ Knowledge
Artifact ≠ Memory
Artifact ≠ Task State
Capability ≠ Permission
Harness ≠ Runtime
Harness ≠ Orchestrator
Result ≠ Evidence
Verification ≠ Evaluation
Contract ≠ Protocol
Learning ≠ Automatic Identity Mutation
108. What Is Intentionally Open

다음은 아직 열어둔다.

Physical storage
Physical services
Concrete APIs
Concrete schemas
Runtime framework
Agent framework
LLM provider
Retrieval engine
Memory implementation
Knowledge implementation
Artifact backend
Identity backend
Protocol
Sandbox technology
Event architecture
Deployment topology
109. Architecture Transition Decision

현재 Decision Review 결과:

Critical Conflict
→ None identified

Major Boundary Instability
→ None identified

Minor Refinements
→ Present

Physical Unknowns
→ Expected

PoC Questions
→ Present

따라서:

Research Phase
→ sufficiently complete for first Blueprint

Architecture Blueprint
→ APPROVED TO PROCEED

로 판단한다.

110. Next Step

다음 단계:

Architecture Decision Review v0.1
        ↓
System Architecture Blueprint v0.1
        ↓
Component Architecture
        ↓
Contract / Interface Specification
        ↓
Integrated PoC
        ↓
Evaluation
        ↓
DDR / Architecture Revision
111. First Blueprint Document

가장 먼저 작성할 문서:

docs/02-Architecture/System-Architecture.md

이 문서는 NOAH 전체의 Logical Architecture를 정의하는
첫 번째 Architecture Blueprint가 된다.

112. Blueprint Writing Principle

System Architecture에서는 Research History를 반복하지 않는다.

다음 질문에 집중한다.

What components exist?

What does each component own?

What does each component not own?

How do components interact?

Where are the stable boundaries?

What is replaceable?

What is persisted?

What is verified?

What remains deferred?
113. Review Outcome

DDR-001 ~ DDR-006은 현재 Project NOAH의 첫 Architecture Decision Set으로
함께 사용할 수 있다고 판단한다.

일부 의미적 Refinement는 필요하지만
새로운 Research Cycle로 돌아갈 정도의 Critical Conflict는 발견되지 않았다.

따라서 다음 단계에서는:

Research
↓
Decision
↓
Architecture

전환을 진행한다.

114. Final Principle

Architecture Decision은 미래의 모든 구현을 미리 결정하기 위한 것이 아니다.

변하지 않아야 할 경계와, 자유롭게 바뀔 수 있어야 할 구현을 구분하기 위한 것이다.

Project NOAH의 첫 번째 Decision Set은 이 경계를 정의하기 위한 출발점으로 채택한다.