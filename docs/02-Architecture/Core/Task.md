# Project NOAH Task Architecture

> Project NOAH Architecture
> Component: Task
> Architecture Version: 0.1
> Status: Blueprint
> Date: 2026-09-04
> Related Decisions: DDR-001, DDR-002, DDR-004, DDR-006

---

# 1. Purpose

이 문서는 Project NOAH의 Task Component Architecture를 정의한다.

Task는 사용자의 Goal을 NOAH가 장기간 추적하고,
계획하고, 실행하고, 검증할 수 있는 지속적인 작업 단위로 표현한다.

핵심 질문:

> **"NOAH가 무엇을 달성해야 하며, 그 목표를 여러 Session과 Runtime을 넘어 어떻게 지속적으로 추적할 것인가?"**

---

# 2. Architectural Role

Task는 User Intent와 실제 Agent Execution 사이의
지속적인 Goal Boundary다.

기본 위치:

```text
User Intent
    ↓
   Task
    ↓
Task State
    ↓
  Agent
    ↓
Execution

복잡한 Task에서는:

Task
 ↓
Orchestration
 ↓
Plan / Delegation
 ↓
Agent

으로 확장될 수 있다.

3. Core Definition

Task는 달성해야 할 Goal과 그 Goal을 제한하는 Requirements,
Constraints 및 Completion Criteria를 가진 durable work contract다.

후보:

Task
=
Goal
+
Requirements
+
Constraints
+
Completion Criteria
+
Verification Requirements
4. Core Separations

Project NOAH는 다음을 구분한다.

User Intent
≠
Task

Task
≠
Task State

Task
≠
Session

Task
≠
Plan

Task
≠
Execution

Task
≠
Runtime

Task
≠
Artifact

Task
≠
Memory

Task
≠
Conversation

이 구분은 Task Architecture의 핵심 Invariant다.

5. User Intent vs Task

User Intent는 사용자가 원하는 것을 표현한다.

Task는 그 Intent를 시스템이 추적하고 실행할 수 있는 형태로 구조화한 것이다.

User Intent
↓
Interpretation
↓
Task Formation

따라서 모든 사용자 발화가 반드시 새로운 Task를 생성하는 것은 아니다.

6. Task Formation

Task Formation 과정에서는 다음을 식별할 수 있다.

Goal

Requirements

Constraints

Priority

Deadline

Budget

Completion Criteria

Verification Requirements

Relevant Scope

정보가 부족하다면 Task 생성 전 또는 생성 후 Clarification을 요구할 수 있다.

7. Task Responsibilities

Task Component는 다음 의미를 담당한다.

Goal Definition

Requirements

Constraints

Completion Criteria

Verification Requirements

Task Identity

Task Relationship

Task Scope

Task Priority

Task Budget Reference

Task Lifecycle Semantics

Task Continuity
8. Task Non-Responsibilities

Task 자체는 다음을 직접 책임지지 않는다.

Reasoning

Planning Algorithm

Agent Execution

Runtime Lifecycle

Memory Retrieval

Knowledge Retrieval

Artifact Storage

Capability Execution

Permission Enforcement

Sandbox

Evaluation Logic

Physical State Storage
9. Task Identity

각 Task는 Stable Task ID를 가진다.

후보:

Task
├── Task ID
├── Created At
├── Created By
└── Scope

Task ID는 Session이나 Runtime ID와 독립적이다.

10. Task Lifetime

Task는 Session과 Runtime보다 오래 지속될 수 있다.

Task Lifetime
≥
Session Lifetime

그리고:

Task Lifetime
≥
Runtime Instance Lifetime

일 수 있다.

11. Long-Horizon Task

NOAH는 하루 이상의 장기 Task를 지원할 수 있어야 한다.

예:

Task
├── Day 1
│   └── Session A
├── Day 2
│   └── Session B
└── Day 7
    └── Session C

Task continuity가 Conversation continuity에 종속되어서는 안 된다.

12. Task vs Session

Session은 특정 Interaction / Execution 관계다.

Task는 지속적인 Goal이다.

Task
├── Session A
├── Session B
└── Session C

따라서:

Session End
≠
Task End

이다.

13. Task vs Conversation

Conversation은 User와 Agent 사이의 Interaction History다.

Conversation
≠
Task

하나의 Conversation에서 여러 Task가 만들어질 수 있고,
하나의 Task가 여러 Conversation 또는 Session에 걸쳐 지속될 수 있다.

14. Task vs Task State

가장 중요한 경계:

Task
= 무엇을 달성해야 하는가

Task State
= 그 Task가 현재 어떤 상태인가

예:

Task:
"NOAH Architecture Blueprint를 완성한다."

Task State:
Status = Running
Progress = Core Architecture
Current Work = Task.md
15. Task Definition vs Task State

후보 구조:

Task Definition
├── Goal
├── Requirements
├── Constraints
├── Completion Criteria
└── Verification Requirements

Task State
├── Status
├── Progress
├── Current Plan Reference
├── Completed Work
├── Pending Work
├── Blockers
└── Verification Status

Task State의 세부 Architecture는 Runtime/State.md에서 정의한다.

16. Canonical Progress Rule

Task의 현재 진행 상황에 대한 Source of Truth는:

Task State

다.

다음은 canonical progress의 대체물이 아니다.

Agent Internal State

Conversation History

Model Context

Memory

Runtime Memory

Plan
17. Goal

Goal은 Task가 달성하려는 최종 목적이다.

좋은 Goal은 가능한 경우:

Clear

Relevant

Verifiable

Bounded enough to act upon

해야 한다.

18. Goal Stability

Task 진행 중 Plan은 자주 변경될 수 있지만
Goal은 상대적으로 더 안정적이다.

Goal
→ relatively stable

Plan
→ adaptive
19. Goal Change

Goal 자체가 변경되는 경우
단순 Plan Update와 구분한다.

후보:

Goal Change Request
↓
Validate User Intent
↓
Assess Consequences
↓
Task Definition Update
↓
Task Version / Audit
20. Requirements

Requirements는 Task가 만족해야 하는 조건이다.

후보:

Functional Requirements

Output Requirements

Quality Requirements

Security Requirements

Compatibility Requirements

User Requirements
21. Constraints

Constraints는 Task 수행 범위를 제한한다.

후보:

Time

Cost

Permission

Technology

Scope

Security

Privacy

Resource

User Preference
22. Completion Criteria

Completion Criteria는 Task가 언제 완료되었다고 볼 수 있는지를 정의한다.

예:

Required Artifact exists

Required tests pass

Required state change occurred

User-requested result produced

Verification conditions satisfied
23. Completion Criteria vs Verification

Completion Criteria:

무엇이 참이어야 Task가 완료되는가?

Verification:

그것이 실제로 참인지 어떻게 확인하는가?

따라서:

Completion Criteria
≠
Verification

이다.

24. Evidence-Based Completion

Task 완료는 Agent의 자기 보고만으로 결정하지 않는다.

기본 흐름:

Execution
↓
Result
↓
Evidence
↓
Verification
↓
Completion Criteria Check
↓
Task State Transition
25. Task Completion Invariant

다음을 금지한다.

Agent:
"완료했습니다."
↓
Task = Completed

Verification이 필요한 Task에서는 실제 Evidence를 사용한다.

26. Verification Requirements

Task는 필요한 Verification 요구사항을 포함할 수 있다.

후보:

Artifact Exists

Tests Pass

Environment State Matches

User Confirmation

Independent Verification

Schema Validation
27. Verification Strength

Task Risk에 따라 Verification 강도를 달리할 수 있다.

후보:

LOW
→ basic validation

MEDIUM
→ evidence-based verification

HIGH
→ independent / deterministic verification

CRITICAL
→ verification + approval / governance

정확한 Risk Model은 Security / Evaluation Specification에서 정의한다.

28. Task Priority

Task는 Priority를 가질 수 있다.

후보:

Low

Normal

High

Critical

정확한 Priority Semantics는 Orchestration Specification에서 결정한다.

29. Task Deadline

Task는 Deadline을 가질 수 있다.

Task Deadline

과:

Capability Timeout

Execution Timeout

Agent Timeout

을 구분한다.

30. Task Budget

Task는 Resource Budget을 가질 수 있다.

후보:

Time

Tokens

Compute

Tool Calls

Network

Storage

Agent Count

External Cost
31. Budget Ownership

Task Budget은 Task-level Resource Constraint다.

Agent는 Budget을 고려할 수 있지만,
Budget Enforcement 자체를 Agent 내부 판단에만 의존하지 않는다.

32. Budget Propagation

Subtask 또는 Delegation에 Budget을 할당할 수 있다.

기본:

Child Budget
≤
Parent Remaining Budget
33. Task Scope

Task는 Scope를 가진다.

후보:

User

Project

Workspace

Repository

Artifact Set

Capability Set

Environment

Scope는 Permission과 연결되지만 동일한 개념은 아니다.

34. Scope vs Permission
Task Scope
= Task가 다루는 범위

Permission
= 해당 범위에서 무엇을 할 수 있는가

따라서:

Scope
≠
Permission

이다.

35. Task Ownership

Task에는 Logical Owner / Requester가 존재할 수 있다.

후보:

User

Project

System

Parent Task

Authorized External Actor

Ownership과 Execution Agent를 동일시하지 않는다.

36. Task Creator vs Executor

Task를 생성한 주체와 수행하는 Agent는 다를 수 있다.

User
↓
Task

Agent A
↓
Execution

또는:

Parent Task
↓
Subtask

Agent B
↓
Execution

이 가능하다.

37. Task Provenance

Task가 왜 존재하는지 추적할 수 있어야 한다.

후보:

Created By

Created At

Source Intent

Parent Task

Source Event

Request Reference
38. Task Contract

Architecture-level Task Contract 후보:

Task Contract
├── Task ID
├── Goal
├── Requirements
├── Constraints
├── Priority
├── Deadline
├── Budget
├── Scope
├── Completion Criteria
├── Verification Requirements
└── Provenance

정확한 Schema는 Specification 단계에서 결정한다.

39. Task Contract vs Task State Contract
Task Contract
= Task의 목표와 조건

Task State Contract
= 현재 Task 진행 상태

두 Contract를 개념적으로 분리한다.

실제 구현에서 하나의 aggregate로 저장할지는 Specification / PoC에서 결정한다.

40. Task Versioning

Task Goal이나 Requirements가 의미 있게 변경될 경우
Task Definition Version을 가질 수 있다.

예:

Task Definition v1
↓
Requirement Change
↓
Task Definition v2
41. Task Version vs Task State Version

다음을 구분한다.

Task Definition Version
= Goal / Requirements / Constraints 변화

Task State Revision
= Progress / Status 변화

예:

Task Definition v2

Task State Revision 37

이 가능하다.

42. Task Mutation

Task Definition의 주요 변경:

Goal

Requirements

Constraints

Completion Criteria

Scope

은 단순 State Update보다 더 높은 의미를 가진다.

43. Task Mutation Authority

중요한 Task Definition 변경은
원래 User Intent와 충돌하지 않는지 확인한다.

Agent가 임의로 사용자의 Goal을 다른 Goal로 바꾸지 않는다.

44. Task State

Task State의 세부 구현은 별도 Component가 담당하지만
Task Architecture에서는 다음 관계를 요구한다.

Task
↓
Task State

Task State는 Task ID를 통해 Task와 연결된다.

45. Task Status

Task State가 표현할 수 있는 Status 후보:

Created

Ready

Running

Waiting

Blocked

Paused

Completed

Failed

Cancelled

정확한 State Machine은 Runtime/State.md에서 정의한다.

46. Created

Task가 정의되었지만 아직 실행 준비가 끝나지 않았을 수 있다.

예:

Missing requirements

Waiting for user clarification
47. Ready

Task 실행에 필요한 최소 조건이 충족된 상태다.

Task
↓
Ready
↓
Execution eligible
48. Running

현재 Task에 대한 실행이 진행 중인 상태다.

Running이라고 해서 Runtime 하나가 계속 살아 있어야 한다는 의미는 아니다.

49. Waiting

외부 Event나 User Response 등을 기다리는 상태다.

예:

Waiting for user

Waiting for external API

Waiting for scheduled condition

Waiting for dependency
50. Blocked

현재 진행을 막는 해결되지 않은 문제가 존재하는 상태다.

예:

Permission missing

Dependency failure

Required artifact unavailable

Unresolvable conflict
51. Paused

의도적으로 실행이 중단된 상태다.

Running
↓
Pause
↓
Checkpoint
↓
Paused

Task 자체는 유지된다.

52. Completed

Task Completion Criteria가 충족되고
필요한 Verification을 통과한 상태다.

Completion Criteria
+
Verification
→ Completed
53. Failed

현재 Strategy로 Task 완료가 불가능하거나
복구 가능한 선택지가 소진된 상태일 수 있다.

Failed와 Cancelled를 구분한다.

54. Cancelled

Task 수행이 의도적으로 중단된 상태다.

후보 요청자:

User

Authorized System

Parent Task

Governance
55. Status Transition Authority

Agent가 Status Transition을 제안할 수 있지만
canonical Task State 변경은 명시적인 State Transition 경로를 사용한다.

후보:

Agent / Runtime / Verification
↓
State Transition Request
↓
Validation
↓
Task State Commit
56. Plan

Plan은 Task를 달성하기 위한 현재 전략이다.

Task
↓
Plan
↓
Execution
57. Task vs Plan

핵심:

Task
= What must be achieved

Plan
= How it may be achieved

Plan 실패가 Task 실패를 의미하지 않는다.

58. Replanning

실행 중 Plan을 수정할 수 있다.

Plan A
↓
Failure / New Information
↓
Replan
↓
Plan B

Task Goal은 그대로 유지될 수 있다.

59. Plan Persistence

장기 Task에서는 Current Plan 또는 Plan Reference를
Task State에 보존할 수 있다.

정확한 Plan representation은 Orchestration Architecture에서 정의한다.

60. Agent Relationship

Agent는 Task를 읽고 현재 Context에서 작업을 수행한다.

Task
↓
Task State
↓
Context Projection
↓
Agent

Agent가 Task 자체의 Source of Truth가 되지 않는다.

61. Agent Replacement

Task는 Agent Instance보다 오래 지속될 수 있다.

Task
↓
Agent A
↓
Failure

Task persists

↓
Agent B
↓
Resume
62. Model Replacement

Task도 Model과 독립적이다.

Task
↓
Agent
↓
Model A

이후:

Task
↓
Agent
↓
Model B

로 변경할 수 있어야 한다.

63. Runtime Relationship

Runtime은 Task를 실행하는 Lifecycle Environment다.

Task
↓
Agent / Harness
↓
Runtime
↓
Execution

Runtime이 Task를 소유하지 않는다.

64. Runtime Failure

Runtime이 실패해도 Task는 유지된다.

Runtime Failure
↓
Task persists
+
Task State persists
↓
Recovery
65. Recovery

기본 Recovery Flow:

Task
+
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
66. Context Relationship

Context는 Task 정보를 Model-facing 형태로 Projection한다.

Task
+
Task State
+
Other Information
↓
Context Manager
↓
Context
↓
Agent
67. Task Context Projection

Agent가 Task 전체 History를 항상 받을 필요는 없다.

후보:

Goal

Current Requirements

Relevant Constraints

Current Progress

Relevant Plan

Relevant Artifacts

Current Blockers

를 Projection한다.

68. Context Is Not Task
Task Context Projection
≠
Task

Context가 손실되어도 Task Store를 통해 다시 구성할 수 있어야 한다.

69. Memory Relationship

Memory는 Task 수행에 도움이 되는 과거 Experience를 제공할 수 있다.

Memory
↓
Context
↓
Task Execution

그러나:

Memory
≠
Task State

다.

70. Task Memory

Task와 직접 관련된 중요한 Experience가
Task-scoped Memory로 저장될 수 있다.

예:

Previous failure

Important user clarification

Successful strategy

Important lesson
71. Knowledge Relationship

Knowledge는 Task 해결에 필요한 사실과 정보를 제공한다.

Knowledge
↓
Context
↓
Agent
↓
Task

Task Definition 자체를 Knowledge Store에 의존시키지 않는다.

72. Artifact Relationship

Task는 여러 Artifact를 생성하거나 사용할 수 있다.

Task
├── Input Artifact
├── Working Artifact
└── Output Artifact
73. Artifact Reference

Task와 Task State에는 가능한 경우 Artifact Reference를 사용한다.

Task / Task State
↓
Artifact ID / Reference
↓
Artifact

Artifact 전체를 Task record에 복사하지 않는다.

74. Artifact Role

Task에서 Artifact 역할 후보:

Input

Intermediate

Output

Evidence

Checkpoint

Reference

Artifact Type과 Role은 동일하지 않다.

75. Capability Relationship

Task는 특정 Capability Requirement를 가질 수 있다.

Agent는 Task를 바탕으로 Capability를 선택한다.

Task
↓
Agent
↓
Capability Selection
76. Capability Requirement

특정 Task가 반드시 특정 종류의 Capability를 요구할 수 있다.

예:

Filesystem access

Code execution

Web retrieval

Document creation

하지만 구체적인 Tool implementation을 Task Contract에 과도하게 고정하지 않는다.

77. Permission Relationship

Task가 존재한다고 실행 권한이 자동 생성되지는 않는다.

Task
≠
Permission
78. Permission Scope

Task Scope는 Permission 평가의 Input이 될 수 있다.

Identity
+
Task Scope
+
Capability
+
Risk
↓
Policy
↓
Permission
79. Security Requirements

Task 자체가 Security Requirement를 가질 수 있다.

예:

No external network

Read-only filesystem

User approval before publish

No secret exposure

Restricted artifact scope
80. Sensitive Tasks

High-impact Task에서는 더 강한 통제를 사용할 수 있다.

Task
↓
Risk Classification
↓
Policy
↓
Permission
↓
Approval
↓
Execution
↓
Verification
↓
Audit
81. Orchestration Relationship

복잡한 Task는 Orchestrator가 분해할 수 있다.

Task
↓
Orchestrator
↓
Plan
↓
Subtasks / Delegations
82. Task Decomposition

큰 Task를 작은 Subtask로 분해할 수 있다.

Parent Task
├── Subtask A
├── Subtask B
└── Subtask C

모든 Step을 별도 Task로 만들어야 한다는 의미는 아니다.

83. Step vs Subtask
Plan Step
= 실행 계획의 작은 단계

Subtask
= 독립적으로 추적할 가치가 있는 Task

Subtask는 자체:

Goal
State
Completion Criteria
Verification

를 가질 수 있다.

84. Subtask Creation Criteria

Subtask 후보 기준:

Independent Completion

Independent Verification

Separate Agent Ownership

Long-running Work

Parallel Execution

Distinct Permission Scope

Failure Isolation

단순 Step은 Task로 승격하지 않는다.

85. Parent / Child Relationship

Subtask는 Parent Task를 참조한다.

Parent Task
↓
Child Task

Child Task 완료가 Parent Task 자동 완료를 의미하지 않는다.

86. Child Completion

후보:

Child A Completed
Child B Completed
Child C Completed
↓
Parent Aggregation
↓
Parent Verification
↓
Parent Completion
87. Task Dependency

Task 간 Dependency를 표현할 수 있다.

예:

Task A
↓
Task B
↓
Task C

또는:

      Task A
      /    \
 Task B   Task C
      \    /
      Task D
88. Dependency Types

후보:

Requires

Blocks

Produces For

Verifies

Depends On

정확한 Dependency Model은 Orchestration Specification에서 결정한다.

89. Parallel Tasks

독립적인 Subtask는 병렬 실행될 수 있다.

Parent Task
├── Task A
├── Task B
└── Task C

병렬 실행은 Budget, Permission 및 Shared State Conflict를 고려한다.

90. Shared State Risk

여러 Task / Agent가 동일 Artifact 또는 State를 수정하면 Conflict가 발생할 수 있다.

후보:

Versioning

Locking

Optimistic Concurrency

Branch / Merge

Serialization

정확한 전략은 후속 Architecture에서 결정한다.

91. Task Cancellation

User 또는 권한 있는 주체는 Task를 Cancel할 수 있어야 한다.

후보:

Cancellation Request
↓
Task State
↓
Orchestrator / Agent
↓
Runtime
↓
Capability Cancellation
92. Cancellation vs Rollback

Task 취소가 이미 발생한 외부 Side Effect를 자동으로 되돌린다는 의미는 아니다.

Cancel
≠
Rollback

Side Effect는 별도 Compensation이 필요할 수 있다.

93. Task Pause

Long-running Task는 Pause될 수 있다.

Running
↓
Pause Request
↓
Checkpoint
↓
Paused
94. Task Resume
Paused Task
↓
Load Task State
↓
Restore Relevant References
↓
Context Reconstruction
↓
New Agent / Runtime
↓
Resume
95. Waiting Task

Task가 외부 조건을 기다릴 수 있다.

예:

User Response

Future Time

External Event

Dependency Completion

Resource Availability

Waiting 동안 Runtime이 계속 실행될 필요는 없다.

96. Durable Task Principle

중요 원칙:

Durable Task
≠
Long-running Process

Task가 오래 지속된다고 하나의 Process를 계속 유지해야 하는 것은 아니다.

97. Task Store

Task와 Task Definition을 지속하기 위한 Logical Store를 둘 수 있다.

후보:

Task Store
├── Task Definition
├── Task Metadata
├── Relationships
├── Version References
└── State Reference

Task State Storage의 정확한 구조는 State Architecture에서 결정한다.

98. Storage Independence

Task Architecture는 특정 Storage에 종속되지 않는다.

후보:

Relational Database

Document Store

Event-backed Store

Future Durable Store

현재 특정 구현을 Contract로 고정하지 않는다.

99. Initial Storage Direction

초기 구현에서는 기존 Infrastructure와 단순성을 고려하여
PostgreSQL을 후보로 사용할 수 있다.

그러나:

Task Architecture
≠
PostgreSQL

이다.

100. Task Events

Observability를 위해 다음 Event를 사용할 수 있다.

후보:

TaskCreated

TaskReady

TaskStarted

TaskUpdated

TaskPaused

TaskResumed

TaskBlocked

TaskCompleted

TaskFailed

TaskCancelled

TaskDefinitionChanged
101. Event Log vs Task State

Event Log는 Task State를 설명하거나 재구성하는 데 도움을 줄 수 있다.

그러나 Architecture v0.1에서는:

Event Log
≠
Mandatory Canonical Event Sourcing

으로 유지한다.

102. Observability

Task의 전체 Lifecycle을 추적할 수 있어야 한다.

후보 Metadata:

Task ID

Parent Task ID

Session ID

Agent ID

Execution ID

Plan ID

Artifact References

Verification ID

Timestamp

모든 Event가 모든 ID를 포함해야 한다는 의미는 아니다.

103. Task Trace

후보:

Task
↓
Plan
↓
Agent
↓
Capability
↓
Execution
↓
Artifact
↓
Verification
↓
Evaluation

을 하나의 Trace로 연결할 수 있다.

104. Audit

다음 Task 변경은 Audit 대상이 될 수 있다.

Goal Change

Scope Expansion

Permission-sensitive Change

Cancellation

Critical Completion

Parent / Child Relationship Change

High-risk Execution
105. Evaluation Relationship

Task는 Evaluation의 기본 단위 중 하나다.

후보:

Task Success

Correctness

Safety

Cost

Latency

Recovery

Completion Quality

User Satisfaction

Long-term Utility
106. Task Success vs Execution Success
Execution Success
≠
Task Success

예:

Tool Call = Success

but

Task Goal = Not Achieved

가 가능하다.

107. Partial Success

Task가 일부만 달성될 수 있다.

예:

Required Outcomes: 5

Verified Outcomes: 3

이 경우 무조건 Completed로 처리하지 않는다.

정확한 Partial Result semantics는 Specification에서 정의한다.

108. Failure Attribution

Task 실패 원인 후보:

Invalid Task Definition

Missing Information

Planning Failure

Model Failure

Capability Failure

Permission Failure

Runtime Failure

Environment Failure

Verification Failure

Budget Exhaustion

Dependency Failure

User Cancellation
109. Task Failure Does Not Imply Agent Failure

예:

External Service unavailable
↓
Task Failed

라고 해서 Agent Architecture가 실패했다는 의미는 아니다.

Failure Attribution을 분리한다.

110. Retry

Task 자체 Retry와 Capability Retry를 구분한다.

Capability Retry
= 동일 Action 재시도

Task Retry
= Task Execution Strategy 재시작 / 재계획
111. Replanning Before Failure

하나의 Plan이 실패했다고 Task를 즉시 Failed로 만들지 않는다.

후보:

Plan Failure
↓
Evaluate
↓
Alternative Available?
├── Yes → Replan
└── No → Block / Fail / Escalate
112. Task Recovery

Recovery 시 Task Definition은 일반적으로 그대로 유지한다.

Task Definition
+
Persisted Task State
+
Artifacts
+
Execution Records
↓
Recovery
113. User Control

User는 자신의 Task에 대해 가능한 범위에서 다음 통제를 가져야 한다.

후보:

Inspect

Clarify

Modify

Pause

Resume

Cancel

Review Result
114. Task Modification

사용자가 Goal이나 Requirement를 변경한 경우
기존 Task를 수정할지 새로운 Task를 생성할지 판단할 필요가 있다.

후보 기준:

Same underlying Goal
→ modify / version existing Task

Fundamentally different Goal
→ create new Task

정확한 기준은 Specification에서 정한다.

115. Task Fork

하나의 Task에서 서로 다른 방향의 작업을 탐색해야 할 수 있다.

후보:

Task
├── Branch A
└── Branch B

이를 Task Fork로 표현할지 Plan Branch로 표현할지는
Orchestration Specification에서 결정한다.

초기에는 불필요한 Task Fork를 피한다.

116. Task Identity Continuity

Task Definition이 일부 수정되어도
같은 Goal continuity가 유지된다면 동일 Task ID를 유지할 수 있다.

근본적인 Goal 변경은 새로운 Task가 더 적절할 수 있다.

117. Task and Identity

Task는 특정 Identity에 의해 수행될 수 있지만
Task 자체가 Identity는 아니다.

Identity
↓
Agent
↓
Task Execution

Root Identity는 여러 Task에 걸쳐 지속된다.

118. Task and Relationship

User Relationship Context가 Task 수행 방식에 영향을 줄 수 있다.

예:

Preferred communication style

Known project preferences

User-confirmed constraints

그러나 Relationship이 Task Goal을 임의로 변경해서는 안 된다.

119. Instruction Authority

Task Instructions는 Context의 다른 정보와 Authority가 다를 수 있다.

특히 External Content가:

Task Goal

을 임의로 변경하지 못하도록 한다.

120. Prompt Injection Boundary

Task 수행 중 읽은 외부 Artifact나 Web Content 안의 Instruction을
Task Definition과 동일한 Authority로 취급하지 않는다.

External Content
≠
Task Authority
121. Task Integrity

Task Definition이 의도하지 않게 변경되는 것을 감지할 수 있어야 한다.

후보:

Version

Revision

Provenance

Audit

Integrity Metadata
122. Task Definition Conflict

User Intent와 현재 Task Definition 사이에 충돌이 발견되면
현재 Task를 그대로 실행하지 않고 Clarification할 수 있다.

Task Definition
vs
Verified User Intent
↓
Conflict
↓
Clarify / Correct
123. Task Security

Task 자체에도 민감한 정보가 포함될 수 있다.

예:

Private user goal

Confidential project

Sensitive artifact references

Restricted environment

따라서 Task Metadata와 State에도 Access Control을 적용할 수 있다.

124. Task Privacy

Task 정보는 필요한 Scope에만 노출한다.

특히 Multi-Agent에서:

Full Parent Task
↓
Scoped Subtask Projection
↓
Child Agent

방향을 우선한다.

125. Task Projection

Child Agent 또는 Model에 전달되는 Task 정보는 Projection일 수 있다.

후보:

Relevant Goal

Relevant Requirements

Relevant Constraints

Assigned Scope

Expected Output

Verification Requirements
126. Projection Is Not Source of Truth
Task Projection
≠
Task Definition

Projection은 canonical Task Definition에서 재생성할 수 있어야 한다.

127. Multi-Agent Task Boundary

Multi-Agent에서도 각 Agent에 필요한 Scope만 제공한다.

Parent Task
↓
Subtask A → Agent A

Parent Task
↓
Subtask B → Agent B

Agent A가 Subtask B의 전체 Context를 기본적으로 볼 필요는 없다.

128. Task Aggregation

Subtask 결과를 Parent Task로 합칠 때:

Subtask Results
↓
Evidence
↓
Aggregation
↓
Parent Verification

을 사용한다.

단순히 모든 Child가 "완료"라고 보고했다는 이유로 Parent를 완료하지 않는다.

129. Task Dependency Failure

Dependency Task가 실패하면:

Dependency Failure
↓
Affected Task
↓
Replan / Wait / Block / Fail

중 하나를 선택할 수 있다.

130. Task Scheduling

Task Scheduling은 Task Architecture의 Core Responsibility가 아니다.

Task
↓
Scheduling / Orchestration

으로 분리한다.

131. Time Semantics

Task는 다음 시간 정보를 가질 수 있다.

후보:

Created At

Deadline

Not Before

Expected Duration

Completed At

실제 Scheduling은 별도 Component가 담당한다.

132. Task Queue

Task가 많아질 경우 Queue가 필요할 수 있다.

그러나:

Task Architecture
≠
Queue Implementation

이다.

초기부터 별도의 Distributed Queue를 요구하지 않는다.

133. External Triggered Task

Task가 User Request 외의 Event로 생성될 수도 있다.

후보:

Schedule

Webhook

Environment Event

Workflow

Parent Task

Task Provenance에 Trigger를 기록한다.

134. Autonomous Task Creation

NOAH가 스스로 새로운 Task를 제안할 수 있다.

그러나:

Task Proposal
≠
Automatically Authorized Execution

이다.

특히 Side Effect가 있는 Task는 User Control / Policy를 유지한다.

135. Task Proposal

후보:

Observed Need
↓
Task Proposal
├── Goal
├── Reason
├── Expected Benefit
├── Cost
├── Risk
└── Required Permission

필요한 경우 User 또는 Governance가 승인한다.

136. Task vs Curiosity

Curiosity Engine이 새로운 질문이나 개선 기회를 발견할 수 있다.

Curiosity
↓
Candidate Question / Task Proposal

하지만 모든 curiosity를 실제 Task로 만들지 않는다.

137. Background Tasks

일부 Task는 Background 형태로 실행될 수 있다.

예:

Periodic Evaluation

Index Maintenance

Backup Verification

Knowledge Refresh

하지만 Resource Budget과 Permission을 가져야 한다.

138. Task Retention

완료된 Task를 얼마나 오래 유지할지는
Retention Policy에 따라 결정할 수 있다.

후보 고려 요소:

Importance

Evidence Value

Audit Requirement

User Preference

Project Relevance

Storage Cost
139. Completed Task vs Memory

완료된 Task 전체를 Memory로 취급하지 않는다.

Completed Task
↓
Experience / Evidence
↓
Memory Candidate

필요한 정보만 Memory로 승격한다.

140. Completed Task vs Knowledge

Task 결과에서 일반화 가능한 사실이 발견되면:

Task Result
↓
Evidence
↓
Validation
↓
Knowledge Candidate

가 될 수 있다.

141. Completed Task vs Artifact

Task의 실제 결과물은 Artifact로 지속될 수 있다.

Task
↓
Artifact

Task가 Archive되어도 Durable Artifact는 별도 Lifecycle을 가질 수 있다.

142. Task Archive

오래된 Task를 Active Task Set에서 제거하더라도
필요한 History를 Archive할 수 있다.

Completed / Cancelled Task
↓
Retention Policy
↓
Archive
143. Task Deletion

Task deletion은 Artifact / Memory / Audit deletion과 동일하지 않다.

Task Delete
≠
Artifact Delete
≠
Memory Delete
≠
Audit Delete

각각 별도의 lifecycle과 policy를 가진다.

144. Observability Invariant

Long-running Task에서는 실행 Component가 바뀌어도
동일 Task ID를 통해 관련 활동을 추적할 수 있어야 한다.

Task ID
├── Session A
├── Agent A
├── Runtime A
├── Runtime B
└── Agent B
145. Task Evaluation

Task Architecture가 잘 동작하는지 평가한다.

후보:

Goal Preservation

Completion Correctness

Recoverability

State Consistency

Traceability

User Control

Budget Compliance

Verification Quality

Long-horizon Continuity
146. Goal Preservation Evaluation

장기 Task에서 여러 Replanning과 Agent Replacement 이후에도
원래 Goal이 왜곡되지 않는지 확인한다.

Initial Goal
vs
Final Execution Goal

을 비교할 수 있다.

147. Recovery Evaluation

PoC:

Task Running
↓
Runtime Failure
↓
Task State Persisted
↓
New Runtime
↓
Resume
↓
Complete

Task continuity를 평가한다.

148. Session Continuity Evaluation
Task
↓
Session A
↓
End
↓
Session B
↓
Resume

에서 Task Definition과 Progress가 유지되어야 한다.

149. Agent Replacement Evaluation
Task
↓
Agent A
↓
Failure
↓
Agent B
↓
Resume

후에도 Goal과 Constraints가 유지되는지 확인한다.

150. Task Modification Evaluation

Task 진행 중 Requirement가 변경되는 경우:

Task v1
↓
User Change
↓
Task v2

후에도 History와 Provenance가 유지되는지 검증한다.

151. Failure Modes

주요 Task Architecture Failure 후보:

Lost Task State

Goal Drift

Invalid Completion

Duplicate Task

Broken Parent / Child Relationship

Stale Task Definition

Unauthorized Goal Change

Incorrect Cancellation

Lost Artifact Reference

Broken Recovery

Budget Overrun
152. Failure Handling

후보:

Detect

Block Transition

Restore Previous Version

Reconstruct State

Replan

Clarify

Escalate

Audit
153. Task Duplication

동일한 User Intent에서 중복 Task가 생성될 수 있다.

초기에는 복잡한 자동 Deduplication을 필수로 하지 않는다.

필요한 경우:

Potential Duplicate
↓
Compare Goal / Scope / Origin
↓
Merge / Link / Keep Separate

를 고려할 수 있다.

154. Task Merge

두 Task를 하나로 합치는 기능은 초기 필수 사항이 아니다.

Task Merge는:

DEFER

한다.

History 및 State Merge semantics가 복잡하기 때문이다.

155. Task Split

실행 중 Task가 지나치게 커졌을 경우:

Task
↓
Decomposition
├── Child Task A
└── Child Task B

를 사용할 수 있다.

원래 Parent Task는 overall Goal을 유지한다.

156. Initial Implementation Candidate

첫 PoC에서는 최소 다음을 구현한다.

Task ID

Goal

Requirements

Constraints

Completion Criteria

Basic Verification Requirements

Task Status

Task State Reference

Artifact References

Created At

Basic Provenance
157. Initial Task Store

첫 PoC에서는 Logical:

Task Repository / Task Store

를 둔다.

실제 구현은 단순한 PostgreSQL Repository로 시작할 수 있다.

중요한 것은:

Agent
≠
Task Store

경계를 유지하는 것이다.

158. Deferred Implementation

초기 PoC에서 다음은 미룰 수 있다.

Complex Task Graph

Distributed Scheduling

Advanced Task Queue

Task Merge

Automatic Deduplication

Complex Priority Scheduling

Dynamic Deadline Negotiation

Cross-device Task Federation

Advanced Task Forking

Fully Autonomous Task Creation
159. Minimal PoC Scenario
1. User Intent 입력

2. Task 생성

3. Task Definition 저장

4. Task State 생성

5. Agent 실행

6. Capability 실행

7. Artifact 생성

8. Task State Progress Update

9. Runtime 종료

10. 새로운 Runtime 시작

11. Task / State 복원

12. Context Reconstruction

13. Agent 실행 재개

14. Evidence 생성

15. Verification

16. Task Completed
160. Pause / Resume PoC
Task Running
↓
Progress Persist
↓
Pause
↓
Runtime Shutdown
↓
Later
↓
Task Load
↓
Context Reconstruction
↓
Resume

를 검증한다.

161. Failure Recovery PoC
Task
↓
Execution
↓
Runtime Crash
↓
Persisted State / Artifacts
↓
New Runtime
↓
Resume

중복 Side Effect가 발생하지 않는지도 함께 확인한다.

162. Completion PoC

Task Completion Criteria:

Artifact exists
+
Validation passes

인 Task를 만들고:

Agent Result
↓
Evidence
↓
Verification
↓
Completed

흐름을 검증한다.

163. Acceptance Criteria

Task Architecture v0.1은 최소 다음을 만족해야 한다.

Task survives Session termination.

Task survives Runtime replacement.

Task is independent from Agent Instance.

Task Definition is distinguishable from Task State.

Task Goal is distinguishable from Plan.

Task progress has a durable canonical source.

Task completion can require Evidence and Verification.

Task can reference durable Artifacts.

Task can be paused and resumed.

Task can be cancelled.

Task can recover after Runtime failure.

Task Goal cannot be silently rewritten by an Agent.

Subtasks can be scoped without exposing the full Parent Task.
164. Architecture Invariants
Task must not depend on one Session.

Task must not depend on one Runtime instance.

Task must not depend on one Agent instance.

Task State must not be replaced by Model Context.

Conversation History must not become canonical Task State.

Memory must not become canonical Task progress.

Plan changes must not silently redefine the Task Goal.

Agent self-report must not automatically complete a verified Task.

Task existence must not automatically grant Permission.

Task cancellation must not be treated as automatic rollback.

Durable Task must not require a continuously running process.
165. Stable Boundaries

현재 안정적으로 유지할 후보:

Task semantics

Task / Session separation

Task / Task State separation

Task / Plan separation

Task / Runtime separation

Task / Agent separation

Task / Artifact separation

Completion / Verification separation

Durable Task principle
166. Replaceable Implementations

다음은 교체 가능해야 한다.

Task Storage

Task Repository Implementation

Serialization

Task Scheduling

Queue Technology

Task ID Generation

Persistence Framework

State Storage Technology
167. Deferred Decisions

현재 최종 결정하지 않는다.

Exact Task Schema

Exact Task State Schema

Exact State Machine

Exact Database Schema

Exact Scheduling Algorithm

Exact Task Queue

Exact Dependency Graph Format

Exact Priority Model

Exact Budget Model

Exact Task Merge Semantics

Exact Task Fork Semantics

Exact Autonomous Task Creation Policy
168. Related Architecture

본 문서는 다음 Architecture와 연결된다.

System Architecture

Identity Architecture

Agent Architecture

Session Architecture

State Architecture

Context Architecture

Harness Architecture

Runtime Architecture

Artifact Architecture

Security Architecture

Orchestration Architecture

Evaluation Architecture
169. Related Decisions

주요 Decision:

DDR-001
Task State / Runtime Boundary

DDR-006
Orchestration Contract

추가 관련 Decision:

DDR-002
Harness Boundary

DDR-003
Memory / Knowledge Boundary

DDR-004
Artifact Architecture

DDR-005
Identity Persistence
170. Specification Questions

후속 Specification에서 결정할 질문:

What is the minimum Task schema?

What is the minimum Task State schema?

Which Task fields are immutable?

How are Goal changes versioned?

What is the exact Task lifecycle?

Who may request State transitions?

How are Completion Criteria represented?

How are Verification Requirements represented?

How are Parent / Child Tasks represented?

How are Task dependencies represented?

How are Task budgets represented?

How are Task cancellation and pause propagated?

How are Task and Artifact references stored?

How is optimistic concurrency handled?

What is persisted for recovery?
171. Architecture Boundary

본 문서는 Task의 Logical Architecture를 정의한다.

다음은 아직 정의하지 않는다.

Concrete Python Classes

Exact Database Tables

Exact API Endpoints

Exact Event Schema

Exact State Machine Code

Exact Queue

Exact Scheduler

Exact Orchestration Framework
172. Current Architecture Statement

Project NOAH의 Task는 사용자의 Goal을 여러 Session, Agent 및 Runtime을 넘어 지속적으로 추적하기 위한 durable work contract다.

Task는 Goal, Requirements, Constraints, Completion Criteria 및 Verification Requirements를 표현하며,
현재 진행 상황은 별도의 canonical Task State가 담당한다.

Plan은 Task를 달성하기 위한 변경 가능한 전략이며,
Agent와 Runtime은 Task를 수행하는 교체 가능한 실행 주체와 환경이다.

Task는 Artifact를 Reference하고 Memory와 Knowledge를 활용할 수 있지만,
어느 것도 Task 자체나 Task State를 대체하지 않는다.

Task Completion은 필요한 경우 Result가 아니라 Evidence와 Verification에 의해 결정된다.

173. Final Principle

Task는 실행 중인 Process가 아니다.

Task는 NOAH가 무엇을 달성해야 하는지를 시간에 걸쳐 보존하는 지속적인 약속이다.

Agent, Session, Plan, Context, Runtime이 바뀌더라도 그 약속과 검증 가능한 진행 상태는 계속 이어질 수 있어야 한다.