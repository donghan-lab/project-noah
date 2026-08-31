# DDR-006 — Orchestration Contract

> Project NOAH Architecture Decision Record
> Decision ID: DDR-006
> Status: Accepted
> Date: 2026-08-25

---

# 1. Decision

Project NOAH는 Agent와 Orchestrator 사이의 협력 및 실행을
명시적인 Contract를 통해 정의한다.

Orchestration Contract는 Task, Plan, Delegation, Agent,
Context, Capability, Result, Evidence, Verification, Budget,
Cancellation 및 Recovery의 관계를 정의한다.

핵심 원칙:

```text
Contract
=
Stable Boundary

Protocol
=
Transport / Communication Mechanism

따라서 특정 Protocol이나 Agent Framework를 Architecture Contract와
동일시하지 않는다.

2. Context

Architecture Integration Review와 Orchestration Contract Research를 통해
다음 요소들이 서로 강하게 연결되어 있음이 확인되었다.

Task
Orchestrator
Agent
Context
Capability
Runtime
Result
Evidence
Verification
Budget
Recovery

Multi-Agent 환경에서는 이러한 관계가 암묵적으로 존재하면:

Responsibility ambiguity
Context leakage
Permission escalation
Result inconsistency
Failure propagation
Budget overrun
Recovery difficulty

등의 문제가 발생할 수 있다.

따라서 명시적인 Contract Boundary를 정의한다.

3. Problem

다음과 같은 구조는 구현이 빠르지만 장기적으로 강한 결합을 만든다.

Agent A
 ↓
Agent B
 ↓
Agent C

각 Agent가 서로의 내부 구조를 직접 이해하면:

Agent 구현 변경이 다른 Agent에 영향을 미치고
Context 전달 방식이 비표준화되고
Failure 처리 방식이 달라지고
Permission이 암묵적으로 전파되고
Model / Runtime 교체가 어려워질 수 있다.

따라서 Contract를 통해 상호작용을 제한한다.

4. Decision Scope

이번 Decision에서 정의하는 Contract:

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
Cancellation Contract
Recovery Contract

이번 Decision에서는 다음을 최종 결정하지 않는다.

MCP 사용 여부
A2A 사용 여부
특정 Message Bus
특정 Agent Framework
최종 Workflow Engine
최종 Orchestrator Implementation
5. Contract Principles

Contract는 가능하면 다음을 명시한다.

Input
Output
Semantics
Scope
Permission
Failure
Verification
Lifecycle
Version
Observability

Schema만 정의하는 것이 아니라 실행 의미와 책임까지 고려한다.

6. Task Contract

Task를 Orchestrator / Agent가 이해할 수 있도록 정의한다.

후보:

Task
├── ID
├── Goal
├── Requirements
├── Constraints
├── Priority
├── Deadline
├── Budget
├── Completion Criteria
└── Verification Requirements

Task의 canonical state는 DDR-001에서 정의한 Task State를 따른다.

7. Task Contract Ownership

Task는 User 또는 상위 시스템이 생성할 수 있다.

Canonical Task State는 Task Store / State Layer에서 유지하며,
Orchestrator가 자체 Memory만으로 Task를 소유하지 않는다.

8. Plan Contract

Orchestrator가 생성하는 실행 계획을 표현한다.

후보:

Plan
├── ID
├── Version
├── Goal
├── Steps
├── Dependencies
├── Assigned Agents
├── Capabilities
├── Budget
├── Verification Strategy
└── Recovery Strategy

Plan은 Task와 동일하지 않다.

Task
→ What

Plan
→ How
9. Delegation Contract

Parent Agent가 Child Agent에게 작업을 위임하는 Contract.

Delegation
├── Parent
├── Child
├── Goal
├── Scope
├── Inputs
├── Constraints
├── Permissions
├── Budget
├── Expected Output
└── Verification
10. Delegation Permission

Child Agent의 권한은 기본적으로 Parent Agent의 권한을 초과하지 않는다.

Child Permission
⊆
Parent Permission

추가 권한이 필요한 경우 별도의 Permission / Approval 흐름을 따른다.

11. Agent Contract

Agent 자체의 Identity와 실행 특성을 표현한다.

후보:

Agent
├── ID
├── Role
├── Capabilities
├── Version
├── Status
├── Trust
├── Input Contract
└── Output Contract

Agent Contract는 Identity Persistence 및 Capability Architecture와 연결된다.

12. Agent Capability Declaration

Agent가 수행할 수 있는 Capability를 선언할 수 있다.

예:

Capabilities
├── Research
├── Coding
├── Analysis
├── Review
└── Verification

Role과 Capability는 동일하지 않다.

13. Agent Availability

Orchestrator가 Agent를 선택할 수 있도록 다음 상태를 표현할 수 있다.

Available
Busy
Unavailable
Failed
Degraded

정확한 scheduling semantics는 별도 Specification에서 정의한다.

14. Context Contract

Agent에게 제공되는 Context의 구조를 정의한다.

후보:

Context
├── Goal
├── Constraints
├── Relevant State
├── Relevant Memory
├── Relevant Knowledge
├── Artifacts
├── Capability Information
└── Security Context

Full Context를 무조건 전달하지 않는다.

15. Context Projection

Parent Context를 Child Agent에게 그대로 복사하지 않는다.

Parent Context
 ↓
Relevant Information
 ↓
Context Projection
 ↓
Child Agent

Context는 Source of Truth가 아니라 Model-facing projection이다.

16. Context Trust

Context에 포함되는 각 정보는 출처와 권위를 유지할 수 있어야 한다.

예:

System Policy
User Intent
Task State
Verified State
Memory
Knowledge
Tool Observation
External Content

더 높은 Trust가 필요한 정보는 더 강한 Verification을 요구할 수 있다.

17. Capability Contract

Agent가 Capability를 호출하기 위한 Contract.

Capability
├── ID
├── Version
├── Input Schema
├── Output Schema
├── Permission
├── Side Effects
├── Cost
├── Timeout
└── Verification

Capability의 실제 구현은 Contract와 분리한다.

18. Tool Call Contract

Tool / Capability 호출에는 최소한 다음 정보를 포함할 수 있다.

Tool Call
├── Call ID
├── Capability
├── Input
├── Context Reference
├── Permission
└── Timeout
19. Tool Result Contract

Tool 실행 결과:

Tool Result
├── Call ID
├── Status
├── Output
├── Error
├── Evidence
├── Side Effects
└── Metadata

Full Tool Output과 Model-facing Projection은 구분할 수 있다.

20. Result Contract

Agent 또는 Workflow가 Parent에게 반환하는 결과다.

후보:

Result
├── Status
├── Summary
├── Findings
├── Evidence
├── Artifacts
├── Uncertainty
├── Errors
└── Recommended Next Step
21. Result vs Evidence

Result:

Agent가 무엇을 보고하는가?

Evidence:

그 보고를 실제로 뒷받침할 수 있는가?

따라서:

Result
+
Evidence

를 별도로 취급한다.

22. Evidence Contract

Evidence는 다음 정보를 가질 수 있다.

Evidence
├── Source
├── Artifact
├── Tool Result
├── Test
├── Observation
├── Timestamp
├── Version
└── Verification
23. Verification Contract

Task / Result / Artifact가 요구사항을 만족하는지 검증한다.

Verification
├── Preconditions
├── Postconditions
├── Evidence
├── Invariants
└── Result
24. Verification Responsibility

Verification은 상황에 따라:

Executor
Parent Agent
Independent Verifier
Environment
Code-based Validator
Human

등이 수행할 수 있다.

High-risk 작업에서는 Independent Verification을 사용할 수 있다.

25. Budget Contract

Orchestration이 무제한 자원을 사용하지 않도록 Budget을 정의한다.

Budget
├── Tokens
├── Time
├── Agents
├── Tool Calls
├── Compute
├── Storage
└── Network
26. Budget Propagation

Child가 사용하는 Budget은 Parent가 가진 Budget의 범위를 초과하지 않는 방향을 기본값으로 한다.

Child Budget
≤
Parent Remaining Budget

Budget 증가에는 별도 Policy를 사용할 수 있다.

27. Cancellation Contract

User 또는 상위 Orchestrator가 Task를 취소할 수 있어야 한다.

User
 ↓
Orchestrator
 ↓
Agent
 ↓
Runtime
 ↓
Capability / Execution

취소 전파는 실행 상태에 따라 Graceful / Immediate 방식을 지원할 수 있다.

28. Pause / Resume Contract

Long-running Task에서는:

Pause
 ↓
Checkpoint
 ↓
Resume

가 가능해야 한다.

Task State / Runtime Boundary의 DDR-001과 연결된다.

29. Failure Contract

Failure를 자유로운 문자열로만 전달하지 않는다.

후보:

Failure
├── Code
├── Category
├── Message
├── Recoverable
├── Retryable
├── Evidence
├── Partial Result
└── Recommended Action
30. Failure Categories

초기 분류:

Invalid Input
Permission Denied
Capability Failure
Timeout
Environment Failure
Verification Failure
Resource Exhaustion
Policy Violation
Agent Failure
External Service Failure

Failure taxonomy는 이후 Evaluation Architecture와 연계한다.

31. Retry Contract

Retry 가능한 작업은:

Retryable
Max Attempts
Backoff
Idempotency

등을 명시할 수 있다.

Side Effect가 있는 Capability는 retry policy를 더욱 엄격하게 관리한다.

32. Recovery Contract

Recovery 후보:

Retry
Reassign
Fallback
Replan
Resume
Escalate
Abort

Recovery 선택은 Task, Failure, Budget 및 Policy를 고려한다.

33. Artifact Contract

Agent 사이에 Artifact를 전달할 때는 Reference 중심으로 한다.

Artifact
├── ID
├── Type
├── Version
├── URI / Reference
├── Hash
├── Provenance
└── Permissions

Artifact의 실제 lifecycle은 DDR-004에서 정의한 Artifact Architecture를 따른다.

34. Memory Contract

Agent가 Memory를 사용하는 경우:

Memory Query
├── Scope
├── Task
├── Query
├── Relevance
└── Permission

결과:

Memory Result
├── Content
├── Source
├── Confidence
├── Timestamp
└── Provenance

를 후보로 사용한다.

35. Knowledge Contract

Knowledge는 별도의 semantics를 유지한다.

Knowledge Query
├── Domain
├── Query
├── Source Requirements
└── Freshness Requirement

Memory와 Knowledge의 경계는 DDR-003을 따른다.

36. Security Contract

Orchestration Request에 다음 Security Context를 유지할 수 있다.

Identity
Role
Scope
Permission
Risk
Approval

Agent 간 위임 과정에서도 Permission을 암묵적으로 확장하지 않는다.

37. Trust Contract

Agent 협력에서:

Identity
Trust
Provenance
Capability
Permission

을 확인할 수 있어야 한다.

Trust는 단순 Agent self-report를 기준으로 하지 않는다.

38. Identity Contract

Agent를 식별하기 위한 기본 정보:

Agent ID
Parent ID
Role
Version
Trust
Identity Reference

Identity Persistence는 DDR-005를 따른다.

39. Session Contract

Agent가 Session 안에서 실행되는 경우:

Session ID
Task ID
Agent ID
State Reference
Context Reference

등을 전달할 수 있다.

Session과 Task의 관계는 DDR-001을 따른다.

40. Runtime Contract

Orchestrator / Harness가 Runtime에 요구할 수 있는 최소 실행 기능:

Start
Pause
Resume
Cancel
Retry
Checkpoint
Recover
Observe

실제 Runtime API는 구현 단계에서 결정한다.

41. Orchestrator Contract

Orchestrator Input:

Task
Available Agents
Available Capabilities
Budget
Policy
Constraints

Orchestrator Output:

Plan
Assignments
Dependencies
Budget Allocation
Verification Strategy
Recovery Strategy
42. Plan Contract

Plan은:

Plan
├── ID
├── Version
├── Goal
├── Steps
├── Dependencies
├── Agents
├── Capabilities
├── Budget
├── Verification
└── Recovery

를 가질 수 있다.

43. DAG / Dependency Contract

복잡한 Task에서는:

       A
      / \
     B   C
      \ /
       D

와 같은 Dependency Graph를 표현할 수 있다.

DAG가 항상 필요한 것은 아니며 단순 Task에서는 선형 실행으로 처리할 수 있다.

44. Parallel Execution Contract

병렬 실행 Group:

Parallel Group
├── Tasks
├── Shared Inputs
├── Independent Outputs
├── Synchronization
└── Aggregation

를 사용한다.

Unlimited Parallelism은 허용하지 않는다.

45. Aggregation Contract

여러 Agent 결과를 통합한다.

Aggregation
├── Inputs
├── Evidence
├── Conflicts
├── Ranking
├── Synthesis
└── Final Verification

단순 Majority Vote를 Truth Source로 취급하지 않는다.

46. Conflict Contract

Agent 결과가 충돌할 경우:

Agent A → X
Agent B → Y

다음 요소를 비교한다.

Evidence
Source Authority
Task Goal
Policy
Verification
47. Uncertainty Contract

불확실성은 결과에 포함할 수 있어야 한다.

Uncertainty
├── Confidence
├── Unknowns
├── Assumptions
├── Alternatives
└── Evidence Gaps

Agent가 불확실성을 숨기도록 유도하지 않는다.

48. Handoff Contract

Handoff에는:

Current Agent
Next Agent
Reason
Goal
Context Projection
State Reference
Permissions
Expected Output

등을 포함할 수 있다.

49. Agent-as-Tool Contract

Agent-as-Tool:

Parent Agent
 ↓
Child Agent
 ↓
Result
 ↓
Parent Agent

에서 Parent Agent가 계속 Control을 가진다.

Handoff와 구분한다.

50. Shared State Contract

여러 Agent가 동일한 Task State를 사용하는 경우:

Read
Write
Version
Lock / Optimistic Concurrency

등의 규칙을 정의할 수 있다.

51. Concurrency Contract

동시 변경 시:

Version
Revision
Conflict
Merge

를 관리할 수 있어야 한다.

52. Idempotency Contract

Capability / Tool의 side effect 재실행 가능성을 나타낸다.

Idempotent
Non-idempotent
Unknown

Unknown인 경우 Retry를 보수적으로 처리한다.

53. Timeout Contract

Timeout은 여러 수준으로 나눌 수 있다.

Connect
Execution
Tool
Agent
Task
54. Deadline Contract

Task / Subtask에:

Deadline
Remaining Time

을 전달할 수 있다.

55. Cost Contract

Orchestration은 비용을 추적할 수 있어야 한다.

Estimated Cost
Actual Cost
Remaining Budget

Cost는 Token만이 아니라 Compute, Tool, Storage 등을 포함할 수 있다.

56. Observability Contract

모든 중요한 Orchestration Event가 다음 ID를 공유할 수 있어야 한다.

Trace ID
Span ID
Task ID
Session ID
Agent ID
Capability ID
57. Audit Contract

다음은 Audit 대상이 될 수 있다.

Delegation
Permission
Approval
Plan
Execution
Verification
Recovery
58. Contract Versioning

Contract 자체도 Version을 가진다.

예:

Task Contract v1
Agent Contract v1
Result Contract v1

Versioning policy는 Compatibility를 고려한다.

59. Compatibility

서로 다른 Contract Version을 사용하는 Component 사이에서는:

Adapter
Negotiation
Fallback

등을 사용할 수 있다.

60. Protocol Mapping

Contract는 여러 Protocol로 전달될 수 있다.

예:

Internal
MCP
A2A
HTTP
Message Queue

Contract와 Protocol은 동일하지 않다.

61. Contract vs Protocol
Contract
= 무엇을 약속하는가

Protocol
= 그 약속을 어떻게 전달하는가

NOAH Architecture는 Contract를 Protocol보다 상위 개념으로 둔다.

62. Contract vs Schema

Schema는 데이터 구조를 표현한다.

Contract는:

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

까지 포함할 수 있다.

63. Contract Governance

중요 Contract 변경:

Proposal
 ↓
Review
 ↓
Compatibility Check
 ↓
Version
 ↓
Migration

을 따른다.

64. Contract Testing

Producer / Consumer가 Contract를 준수하는지 확인한다.

Producer
 ↕
Contract
 ↕
Consumer

Contract Test를 PoC / CI 단계에서 활용할 수 있다.

65. Contract Evaluation

Contract 품질:

Clarity
Completeness
Compatibility
Observability
Recoverability
Security

등으로 평가한다.

66. Historical / Foundational References

참고 원칙:

RPC
Message Passing
Actor Model
Workflow Contracts
Distributed Transactions
API Design
Type Systems
Interface Contracts
Capability-based Security

구현을 그대로 채택하지 않고 Contract 관점의 원칙을 추출한다.

67. Current References

현재 Agent Architecture에서 참고할 수 있는 요소:

MCP
A2A
Agent Handoff
Tool Contracts
Agent Harness
Durable Execution
Multi-Agent Orchestration
Structured Agent Communication

Protocol 자체를 최종 Architecture로 고정하지 않는다.

68. Emerging Directions

향후 연구 대상:

Contract-aware Routing
Dynamic Schema Negotiation
Self-describing Capabilities
Adaptive Delegation
Learned Orchestration
Contract-aware Evaluation
69. Candidate Contract Stack
Task Contract
      │
Plan Contract
      │
Delegation Contract
      │
Agent Contract
      │
Context Contract
      │
Capability Contract
      │
Security Contract
      │
Execution Contract
      │
Result Contract
      │
Evidence Contract
      │
Verification Contract
      │
Evaluation Contract

Budget / Recovery / Cancellation은 실행 lifecycle과 함께 연결한다.

70. Candidate End-to-End Flow
User
 ↓
Task Contract
 ↓
Orchestrator
 ↓
Plan Contract
 ↓
Delegation Contract
 ↓
Agent
 ↓
Context Contract
 ↓
Capability
 ↓
Security
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
Evaluation
71. Candidate Delegation Example
Task:
"Analyze Project Architecture"

Parent Agent
 ↓
Delegation Contract
 ↓
Research Agent

Research Agent
 ↓
Context Projection
 ↓
Read Artifacts
 ↓
Result Contract
 ↓
Evidence

Parent Agent
 ↓
Aggregation
 ↓
Verification
72. Candidate Parallel Example
Task
 ↓
Parallel Group
 ├── Research Agent
 ├── Security Agent
 └── Implementation Agent
        ↓
    Aggregator
        ↓
    Verification

각 Worker에는 필요한 Scope만 전달한다.

73. Candidate Recovery Example
Parent Agent
 ↓
Child Agent
 ↓
Failure
 ↓
Failure Contract
 ↓
Recovery Policy
 ↓
Retry / Reassign / Replan
 ↓
Continue
74. Stable vs Replaceable
Stable
Task Contract
Plan Contract
Delegation Contract
Agent Contract
Context Contract
Result Contract
Evidence Contract
Verification Contract
Budget Contract
Recovery Contract
Replaceable
Protocol
Transport
Message Bus
Orchestrator Implementation
Agent Framework
Runtime Framework
75. Consequences
Positive
Agent 간 책임 명확화
Protocol 독립성
Model / Runtime 교체 가능성 증가
Failure handling 표준화
Security boundary 명확화
Verification / Evaluation 연결 용이
Multi-Agent interoperability 향상
Negative
Contract 수 증가
Schema evolution 부담
Version compatibility 관리
Contract validation 비용
지나친 abstraction 가능성
76. Alternatives Considered
Alternative A — Agent-to-Agent Direct Calls

Rejected as default.

Agent 간 내부 구현 의존성이 강해진다.

Alternative B — Protocol = Architecture Contract

Rejected.

MCP / A2A / HTTP 등의 protocol이 변경될 경우 Architecture까지 변경될 수 있다.

Alternative C — Schema Only

Rejected.

Schema만으로는 lifecycle, permission, failure, verification을 설명하기 어렵다.

Alternative D — No Formal Contracts

Rejected.

Long-term Multi-Agent coordination을 안정적으로 유지하기 어렵다.

77. Relationship to Previous Decisions
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

와 연결된다.

특히:

Task
 ↓
Orchestrator
 ↓
Agent
 ↓
Harness
 ↓
Capability
 ↓
Runtime

의 모든 주요 경계가 Contract로 연결된다.

78. Implementation Implications

향후 다음 Logical Components를 고려한다.

TaskContract
PlanContract
DelegationContract
AgentContract
ContextContract
CapabilityContract
ResultContract
EvidenceContract
VerificationContract
BudgetContract
RecoveryContract

구체적인 Schema 및 Protocol Mapping은 Specification 단계에서 결정한다.

79. Validation Plan

최소 PoC:

1. Task 생성
2. Plan 생성
3. Agent 선택
4. Delegation
5. Context Projection
6. Capability 실행
7. Result 반환
8. Evidence 생성
9. Verification
10. Evaluation

실패 PoC:

Permission Denied
Timeout
Agent Failure
Runtime Failure
Verification Failure
Budget Exhaustion

을 각 Contract가 올바르게 전달하는지 확인한다.

80. Acceptance Criteria
☐ Task Contract가 명확하다.
☐ Plan Contract가 명확하다.
☐ Delegation Scope와 Permission이 명확하다.
☐ Agent Contract가 정의되어 있다.
☐ Context Projection을 지원한다.
☐ Capability Contract가 side effect를 표현할 수 있다.
☐ Result와 Evidence를 구분한다.
☐ Verification을 Contract로 표현할 수 있다.
☐ Budget이 전달된다.
☐ Cancellation / Recovery가 정의된다.
☐ Contract Versioning이 가능하다.
☐ Protocol과 Contract가 분리된다.
☐ Contract violation을 탐지할 수 있다.
81. Decision Status
Status: Accepted
Confidence: Medium

PoC 결과와 향후 Protocol / Agent ecosystem 변화에 따라 재검토할 수 있다.

82. Review Conditions

다음 상황에서 재검토한다.

새로운 Agent communication standard 등장
Contract versioning 문제 발생
Multi-Agent scale 증가
Dynamic orchestration 도입
Distributed execution 도입
새로운 Capability protocol 등장
83. Final Decision

Project NOAH는 Agent와 Orchestrator, Capability, Runtime 및 Verification 사이의 핵심 상호작용을 명시적인 Contract로 정의한다.

Contract는 데이터 Schema를 넘어 semantics, permission, lifecycle, failure, verification 및 observability를 포함할 수 있다.

Contract는 특정 Protocol이나 Agent Framework와 독립적으로 유지한다.

이를 통해 NOAH는 서로 다른 Model, Agent, Runtime, Capability 및 Communication Protocol이 교체되더라도 상호운용 가능한 Architecture Boundary를 유지한다.

Orchestration의 목적은 Agent 간 통신 자체가 아니라, Task를 안전하고 검증 가능하며 통제된 방식으로 수행하는 것이다.