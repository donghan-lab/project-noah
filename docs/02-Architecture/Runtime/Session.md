# Project NOAH Session Architecture

> Project NOAH Architecture
> Component: Session
> Architecture Version: 0.1
> Status: Blueprint
> Date: 2026-09-04
> Related Decisions: DDR-001, DDR-002, DDR-005, DDR-006

---

# 1. Purpose

이 문서는 Project NOAH의 Session Component Architecture를 정의한다.

Session은 일정 기간 동안 발생하는 User, Agent, Task,
Runtime 및 Conversation 사이의 상호작용을 연결하고 추적하기 위한
bounded interaction / execution continuity boundary다.

핵심 질문:

> **"NOAH와 사용자가 일정 기간 상호작용하는 동안 무엇을 하나의 실행 관계로 묶고, 무엇은 Session보다 오래 지속되어야 하는가?"**

---

# 2. Architectural Role

Session은 장기적으로 지속되는 Identity / Task와
짧게 생성되고 교체될 수 있는 Agent / Runtime 사이의 중간 Lifecycle Boundary다.

기본 관계:

```text
Identity
   ↓
Session
   ↓
Agent Instance
   ↓
Runtime

Task 관점에서는:

Task
├── Session A
├── Session B
└── Session C

와 같은 관계를 가질 수 있다.

3. Core Definition

Session은 특정 시간 범위에서 발생하는 Interaction과 Execution을
연결하기 위한 논리적 Container다.

후보 의미:

Session
=
Interaction Boundary
+
Execution Continuity Reference
+
Conversation Reference
+
Task References
+
Agent / Runtime References
+
Observability Scope

Session 자체가 Task나 Runtime의 Source of Truth는 아니다.

4. Core Separations

Project NOAH는 다음을 구분한다.

Session
≠
Task

Session
≠
Task State

Session
≠
Conversation

Session
≠
Turn

Session
≠
Context

Session
≠
Agent

Session
≠
Agent Instance

Session
≠
Runtime

Session
≠
Identity

Session
≠
Memory

이 구분은 Session Architecture의 핵심 Invariant다.

5. Session vs Task

Task:

무엇을 달성해야 하는가?

Session:

일정 기간 어떤 Interaction / Execution 관계 안에서 작업이 이루어졌는가?

따라서:

Task
≠
Session

이다.

6. Task Can Outlive Session

하나의 Task는 여러 Session에 걸쳐 지속될 수 있다.

Task
├── Session A
├── Session B
├── Session C
└── Session D

따라서:

Session End
≠
Task End

이다.

7. Session Can Reference Multiple Tasks

하나의 Interaction Session에서 여러 Task를 다룰 수도 있다.

예:

Session A
├── Task 1
├── Task 2
└── Task 3

따라서 Task와 Session을 고정된 1:1 관계로 정의하지 않는다.

8. Task / Session Relationship

기본적으로:

Task
↔
Session

은 Reference Relationship이다.

Task는 Session을 소유하지 않고,
Session도 Task를 canonical하게 소유하지 않는다.

정확한 데이터 모델은 Specification 단계에서 결정한다.

9. Session vs Conversation

Conversation은 User와 Agent 사이에서 발생한
Message / Interaction Content다.

Session은 그 Conversation을 포함하거나 참조할 수 있는 Lifecycle Boundary다.

Session
↓
Conversation
↓
Messages / Turns

따라서:

Session
≠
Conversation

이다.

10. Why Session Is Not Conversation

Conversation History만으로는 다음을 충분히 표현하기 어렵다.

Agent Instance

Runtime Instance

Task References

Execution IDs

Context Versions

Capability Calls

Recovery

Session Lifecycle

Security Scope

따라서 Session은 Conversation보다 넓은 Architecture 개념이다.

11. Session vs Turn

Turn은 하나의 Interaction Step이다.

예:

Session
├── Turn 1
├── Turn 2
├── Turn 3
└── Turn 4

따라서:

Turn
⊂
Session

일 수 있지만,
Turn 자체가 Session은 아니다.

12. Session vs Context

Context는 현재 Model 호출을 위한 Information Projection이다.

Session
├── Context v1
├── Context v2
├── Context v3
└── Context v4

하나의 Session에서도 Context는 계속 달라질 수 있다.

13. Context Is Not Session State

중요:

Context
≠
Session Source of Truth

Context는 Model-facing Projection이며,
Session 전체 정보를 항상 포함하지 않는다.

14. Session vs Runtime

Runtime은 실제 Execution Lifecycle을 수행한다.

Session은 Runtime보다 상위의 Interaction Boundary다.

Session
├── Runtime A
└── Runtime B

Runtime이 교체되어도 동일 Session을 유지할 수 있다.

15. Runtime Replacement Inside Session

예:

Session
↓
Runtime A
↓
Failure
↓
Runtime B
↓
Continue Session

이 구조가 가능해야 한다.

16. Session vs Agent Instance

Agent Instance 역시 Session과 동일하지 않다.

Session
├── Agent Instance A
└── Agent Instance B

Agent Instance가 실패하거나 교체되어도
Session 자체가 반드시 종료될 필요는 없다.

17. Session vs Identity

Identity는 Session보다 훨씬 장기적으로 지속된다.

Identity
├── Session A
├── Session B
├── Session C
└── Session D

따라서:

Identity
≠
Session

이다.

18. Identity Continuity

Session이 종료되어도 Root Identity는 유지된다.

Session A
↓
End

Identity persists

↓
Session B

Session B에서 필요한 Identity Projection을 다시 생성한다.

19. Session Responsibilities

Session Component는 다음 의미를 담당한다.

Session Identity

Lifecycle

Interaction Boundary

Task References

Conversation Reference

Agent Instance References

Runtime References

Context Lineage References

Execution References

Workspace Reference where applicable

Observability Correlation

Session-level Metadata
20. Session Non-Responsibilities

Session은 다음을 직접 소유하지 않는다.

Task Goal

Canonical Task Progress

Identity Core

Memory Store

Knowledge Store

Artifact Store

Capability Implementation

Permission Authority

Runtime Implementation

Model

Evaluation Logic
21. Session Identity

각 Session은 Stable Session ID를 가진다.

후보:

Session
├── Session ID
├── Created At
├── Created By
└── Scope

Session ID는 Task ID, Runtime ID, Agent ID와 독립적이다.

22. Session Contract

Architecture-level Session Contract 후보:

Session Contract
├── Session ID
├── Identity / Principal Reference
├── Task References
├── Conversation Reference
├── Status
├── Created At
├── Updated At
├── Agent Instance References
├── Runtime References
├── Execution References
├── Context References
└── Scope

정확한 Schema는 Specification 단계에서 결정한다.

23. Session Lifecycle

후보 Lifecycle:

Created
↓
Active
↓
Idle
↓
Closed
↓
Archived

특수 상황:

Paused
Expired
Failed

등을 사용할 수 있다.

정확한 State Machine은 Specification에서 결정한다.

24. Created

Session이 생성되었지만 아직 실제 Interaction이 시작되지 않은 상태일 수 있다.

Session Created
↓
Ready for interaction
25. Active

User 또는 Agent Interaction이 현재 진행되는 상태다.

Session
→ Active

Active Session 안에서도 Runtime이 항상 실행 중일 필요는 없다.

26. Idle

일정 기간 Interaction이 없는 상태다.

Active
↓
No interaction
↓
Idle

Idle은 Closed와 다르다.

27. Paused

특정 Execution 또는 Interaction을 의도적으로 중지할 수 있다.

Active
↓
Pause
↓
Paused

Task가 반드시 Paused 상태가 되는 것은 아니다.

28. Closed

Session의 Interaction Boundary를 종료한다.

Session
↓
Closed

그러나:

Session Closed
≠
Task Completed

이다.

29. Expired

정책 또는 TTL에 의해 Session을 종료할 수 있다.

Idle
↓
Expiration Policy
↓
Expired

Expired Session이 존재하더라도 Task는 지속될 수 있다.

30. Archived

오래된 Session을 Active Set에서 제거하고
History로 보존할 수 있다.

Closed
↓
Retention
↓
Archived
31. Session Failure

Session 자체에서 복구 불가능한 상태가 발생할 수 있다.

하지만 대부분의 Runtime / Agent Failure를
즉시 Session Failure로 승격하지 않는다.

Runtime Failure
≠
Session Failure
32. Session Status vs Task Status

두 Status를 혼합하지 않는다.

예:

Session = Closed

Task = Running

또는:

Session = Active

Task A = Completed
Task B = Running

이 가능하다.

33. Session Lifetime

일반적으로:

Identity Lifetime
>
Session Lifetime

그리고 Task와 Session Lifetime은 고정적인 포함 관계를 갖지 않는다.

다만 Long-horizon Task에서는 흔히:

Task Lifetime
>
Individual Session Lifetime

이 된다.

34. Session Persistence

Session 전체 Runtime Memory를 영속화할 필요는 없다.

장기적으로 필요한 것은 후보적으로:

Session Metadata

Task References

Conversation Reference

Execution References

Agent / Runtime References

Important Lifecycle Events

Context Lineage Metadata

등이다.

35. Session Store

Session Metadata를 지속하기 위한 Logical Store를 둘 수 있다.

Session Store
├── Session Metadata
├── Lifecycle
├── References
└── Relationship Metadata
36. Storage Independence

Session Architecture는 특정 Storage 구현에 종속되지 않는다.

후보:

Relational Database

Document Store

Event-backed Store

Future Session Store
37. Initial Storage Direction

초기 PoC에서는 기존 Infrastructure와 단순성을 고려하여
PostgreSQL 기반 Repository를 사용할 수 있다.

하지만:

Session Architecture
≠
PostgreSQL

이다.

38. Session State

Session은 자신의 Lifecycle과 Interaction 상태를 가질 수 있다.

후보:

Session State
├── Status
├── Active Task References
├── Current Agent Reference
├── Current Runtime Reference
├── Last Interaction At
└── Current Conversation Reference

이 상태를 Task State와 동일하게 취급하지 않는다.

39. Session State vs Task State
Session State
= 현재 Session의 Interaction / Lifecycle 상태

Task State
= Task의 canonical progress

둘은 서로 다른 semantics를 가진다.

40. Session State vs Execution State

Execution State는 Runtime-level 실행 상태다.

Session
↓
Runtime
↓
Execution State

Session이 Execution State 전체를 직접 소유하지 않는다.

41. Session and Conversation History

Session은 Conversation History를 참조할 수 있다.

Session
↓
Conversation Reference
↓
Messages

Conversation 자체가 Session Metadata Store에 모두 포함되어야 하는 것은 아니다.

42. Conversation Persistence

Conversation History를 얼마나 오래 보존할지는
Memory나 Task State와 별도의 Retention Policy를 가질 수 있다.

Conversation Retention
≠
Memory Retention
43. Conversation Is Not Memory

중요:

Conversation History
≠
Long-term Memory

Conversation에서 중요한 정보만 Memory Candidate가 될 수 있다.

44. Session to Memory Flow

후보:

Session Experience
↓
Candidate Extraction
↓
Validation
↓
Memory

Session 전체를 자동으로 Memory로 복사하지 않는다.

45. Session to Knowledge Flow

Session에서 검증된 일반적 정보가 발견되면:

Session Finding
↓
Evidence
↓
Validation
↓
Knowledge Candidate

가 될 수 있다.

46. Session and Artifact

Session 동안 Artifact를 생성하거나 사용할 수 있다.

Session
├── Artifact A
├── Artifact B
└── Artifact C

그러나 Artifact Lifecycle은 Session에 종속되지 않는다.

47. Artifact Persistence
Session Closed
↓
Durable Artifact persists

가 가능해야 한다.

Session 삭제가 Artifact 자동 삭제를 의미하지 않는다.

48. Session and Workspace

Session은 Workspace Reference를 가질 수 있다.

Session
↓
Workspace Reference

하지만:

Session
≠
Workspace

이다.

49. Workspace Lifetime

Workspace가 Session보다 오래 또는 짧게 지속될 수 있다.

예:

Project Workspace
├── Session A
├── Session B
└── Session C

또는 Temporary Workspace는 하나의 Session 안에서만 존재할 수도 있다.

50. Session and Context

하나의 Session은 많은 Context Projection을 생성한다.

Session
├── Context Projection 1
├── Context Projection 2
├── Context Projection 3
└── Context Projection N
51. Context Version Reference

중요한 실행에서 어떤 Context가 사용되었는지 추적하기 위해:

Context Reference

Context Version

Projection Metadata

를 기록할 수 있다.

Full Context 전체를 반드시 영구 저장한다는 의미는 아니다.

52. Context Reconstruction

새 Runtime 또는 Agent Instance가 시작될 경우
Session Memory를 그대로 복사하는 대신 Context를 재구성한다.

Task State
+
Identity Projection
+
Memory
+
Knowledge
+
Artifacts
+
Relevant Conversation
+
Environment
+
Policy
↓
Context Reconstruction
53. Session Resume

Session Resume와 Task Resume를 구분한다.

Session Resume
= 같은 Interaction Boundary를 다시 활성화

Task Resume
= 지속되는 Task Execution을 다시 시작
54. New Session Task Resume

Task를 이어가기 위해 이전 Session을 반드시 다시 열 필요는 없다.

Task
↓
Session A
↓
Closed

Later

Task
↓
Session B
↓
Resume Task

이 구조를 기본적으로 지원한다.

55. Session Continuity vs Task Continuity
Session continuity
= optional

Task continuity
= durable requirement

Long-running Task의 지속성이 Session 복원 여부에 의존해서는 안 된다.

56. Session and Agent

Session 안에서 Agent Instance를 생성할 수 있다.

Session
↓
Agent Instance

Agent Instance는 Identity Projection과 Context를 받아 실행된다.

57. Agent Replacement
Session
↓
Agent A
↓
Failure
↓
Agent B

와 같이 동일 Session 안에서도 Agent Instance를 교체할 수 있다.

58. Model Replacement

Session 진행 중 Model이 변경될 수도 있다.

Session
↓
Agent
↓
Model A

then

Session
↓
Agent
↓
Model B

Session continuity를 특정 Model에 종속시키지 않는다.

59. Session and Harness

Session은 Harness를 통해 Runtime과 Infrastructure에 연결될 수 있다.

Session
↓
Agent
↓
Harness
↓
Runtime

Harness 자체를 Session이 소유하지 않는다.

60. Session and Runtime

Session에서 하나 이상의 Runtime Instance가 사용될 수 있다.

후보:

Session
├── Runtime Instance 1
├── Runtime Instance 2
└── Runtime Instance 3
61. Runtime Lifetime

Runtime은 Session보다 짧게 존재할 수 있다.

Session
↓
Runtime A
↓
Terminate
↓
Runtime B
62. Runtime Failure

Runtime Failure 시:

Runtime Failure
↓
Execution Record
+
Task State
+
Artifacts
↓
Recovery
↓
New Runtime

Session은 계속 유지하거나 새 Session으로 전환할 수 있다.

63. Session Does Not Own Recovery

Recovery Strategy는 Runtime / Harness / Task State Architecture와 연결된다.

Session은:

Recovery Context / References

를 제공할 수 있지만 Recovery Engine 자체가 아니다.

64. Session and Capability

Capability 호출은 Session과 연결하여 추적할 수 있다.

예:

Session ID
Task ID
Execution ID
Capability Call ID
65. Capability Permission

Session에 Capability가 노출되어 있다는 사실이
Permission을 의미하지 않는다.

Available in Session
≠
Authorized
66. Session Security Context

Session은 현재 Security Context에 대한 Reference를 가질 수 있다.

후보:

Principal

Role

Scope

Current Approval References

Policy Context

그러나 Permission의 canonical authority를 Session에 저장하지 않는다.

67. Permission Revalidation

장기 Session에서는 Permission이 변경될 수 있다.

따라서 중요한 실행 전에:

Old Session Permission Context
≠
Guaranteed Current Permission

이다.

필요한 Permission은 실행 시 다시 평가할 수 있어야 한다.

68. Session and Credentials

Credential을 Session Context 또는 Conversation에 직접 저장하지 않는다.

Session
↓
Capability Request
↓
Credential Broker

방향을 유지한다.

69. Session Isolation

서로 다른 Session 사이의 정보가
암묵적으로 섞이지 않도록 한다.

Session A
≠
Session B

정보 공유는:

Task

Memory

Knowledge

Artifact

Explicit References

같은 상위 Persistence Domain을 통해 이루어진다.

70. Cross-Session Leakage

다음을 방지해야 한다.

Session A private context
↓
unintended
↓
Session B

특히 Multi-user 또는 Multi-project 환경에서 중요하다.

71. Session Scope

후보:

User Scope

Project Scope

Workspace Scope

Task Scope

Temporary Scope

Session Scope와 Permission Scope를 동일시하지 않는다.

72. Session Ownership

Session의 Logical Owner / Principal을 기록할 수 있다.

후보:

User

Project

Authorized System

External Integration
73. User Session

가장 일반적인 경우:

User
↓
Session
↓
NOAH

이다.

74. System Session

Background 또는 scheduled operation에서
User Interaction 없이 Session-like execution boundary가 필요할 수 있다.

후보:

System Trigger
↓
Session
↓
Task Execution

실제로 이를 Session으로 표현할지는 PoC에서 검증한다.

75. Session vs Execution Run

자동화 환경에서는 단순 Execution Run이
대화형 Session보다 적합할 수도 있다.

따라서:

Session
≠
Execution Run

으로 구분할 가능성을 유지한다.

76. Interactive vs Non-Interactive Execution

후보:

Interactive
→ Session-centered

Non-interactive
→ Task / Execution-centered

NOAH의 모든 실행에 Session을 강제로 요구하지 않는 방향을 고려한다.

77. Optional Session Principle

장기적으로 중요한 원칙 후보:

Every Task may have Sessions

but

Not every Execution must require an interactive Session

정확한 규칙은 Runtime Specification에서 확정한다.

78. Session Observability

Session은 Observability Correlation Boundary로 사용될 수 있다.

후보 식별자:

Session ID

Task ID

Agent ID

Runtime ID

Execution ID

Context Reference

Capability Call ID
79. Session Trace

하나의 Session Trace:

Session
├── Turn
├── Context
├── Agent
├── Capability Call
├── Execution
├── Result
└── Verification

를 연결할 수 있다.

80. Cross-Session Task Trace

Long-running Task에서는:

Task ID
├── Session A
│   └── Executions
├── Session B
│   └── Executions
└── Session C
    └── Executions

형태로 추적할 수 있다.

81. Session Events

후보:

SessionCreated

SessionActivated

SessionIdle

SessionPaused

SessionResumed

SessionClosed

SessionExpired

SessionArchived

AgentAttached

AgentDetached

RuntimeAttached

RuntimeDetached

TaskLinked

TaskUnlinked
82. Event Log

Session Event는 Observability / Audit에 사용할 수 있다.

하지만:

Session Event Log
≠
Full Event Sourcing Requirement

이다.

83. Audit

다음 Session Operation은 Audit 대상이 될 수 있다.

Sensitive Session Creation

Scope Change

Principal Change

High-risk Task Link

Cross-session Data Access

Security Context Change

Session Deletion
84. Session Privacy

Session에는 다음 민감 정보가 포함될 수 있다.

User Conversation

Task References

Artifact References

Behavioral Context

Private Project Information

따라서 Access Control과 Retention이 필요하다.

85. Data Minimization

Session Metadata에 모든 정보를 복사하지 않는다.

Reference
>
Duplication

원칙을 우선한다.

예:

Artifact Reference

를 저장하고 Artifact 전체를 Session Store에 복제하지 않는다.

86. Session Retention

Session Retention은 별도 Policy를 가질 수 있다.

고려 요소:

User Preference

Privacy

Audit Requirement

Task Relevance

Project Policy

Storage Cost
87. Session Archive vs Delete

다음을 구분한다.

Archive
= active use에서 제거하지만 기록 유지

Delete
= Session record 제거
88. Session Delete Does Not Cascade Automatically

중요:

Delete Session
≠
Delete Task

Delete Session
≠
Delete Artifact

Delete Session
≠
Delete Memory

Delete Session
≠
Delete Identity

Delete Session
≠
Delete Audit

각 Domain은 별도 Lifecycle을 가진다.

89. Conversation Delete

Session 삭제와 Conversation 삭제도 동일하지 않을 수 있다.

Session Metadata
≠
Conversation Content

Privacy Policy에서 정확한 semantics를 정의한다.

90. Session Replay

과거 Session을 분석 목적으로 Replay할 수 있다.

후보:

Session Events
+
Conversation
+
Execution Records
↓
Replay / Inspection
91. Replay Does Not Re-execute

매우 중요한 원칙:

Session Replay
≠
Capability Re-execution

과거 Session을 열어본다고 External Side Effect가 다시 실행되어서는 안 된다.

92. Session Recovery

Session Metadata 자체가 손상된 경우:

Task References

Conversation Reference

Execution Records

Observability Events

등을 활용해 일부 관계를 복구할 수 있다.

정확한 Recovery 방식은 Specification에서 결정한다.

93. Session Consistency

Session이 참조하는 Resource가 사라질 수 있다.

예:

Artifact deleted

Task archived

Runtime gone

Agent instance terminated

Reference 상태를 명확하게 처리해야 한다.

94. Stale References

Session은 오래된 Reference를 가질 수 있다.

후보 처리:

Active

Unavailable

Archived

Deleted

Unknown

Reference가 stale하다고 Session 전체를 invalid로 만들 필요는 없다.

95. Context Staleness

과거 Session Context를 그대로 재사용하지 않는다.

Old Context
↓
Do not blindly restore

대신 현재 Source of Truth에서 재구성한다.

96. Environment Changes

Session이 유지되는 동안 Environment가 변경될 수 있다.

예:

File changed

Repository updated

API state changed

Permission changed

따라서 과거 Observation을 현재 Environment State로 간주하지 않는다.

97. Session Resume Validation

오래된 Session을 재개할 경우:

Session Metadata
+
Current Task State
+
Current Environment
+
Current Policy
↓
Validation
↓
Resume

방향을 고려한다.

98. Idle Timeout

Session에는 Idle Timeout이 존재할 수 있다.

하지만:

Session Timeout
≠
Task Deadline

이다.

99. Session Expiration vs Task Deadline
Session Expiration
= Interaction lifecycle policy

Task Deadline
= Goal completion time constraint

둘을 분리한다.

100. Session Cancellation

Session 자체를 종료하는 것과
Task Cancellation도 구분한다.

Close Session
≠
Cancel Task
101. Session Pause vs Task Pause

마찬가지로:

Session Pause
≠
Task Pause

Session Interaction을 중단해도
Background Task는 계속될 수 있다.

102. Background Task

예:

User Session
↓
Task Created
↓
Session Closed

Task
↓
Background Execution
↓
Completion

이 구조를 가능하게 유지한다.

103. Notification Relationship

Background Task가 완료되면
새로운 Session 또는 User-facing Notification을 통해 결과를 전달할 수 있다.

Session 자체가 Notification System은 아니다.

104. Session and Orchestration

Orchestrator는 Session 정보를 Context / User Interaction Scope로 사용할 수 있다.

하지만:

Orchestrator
≠
Session Manager

이다.

105. Multi-Agent Session

하나의 Session 안에서 여러 Agent가 사용될 수 있다.

Session
├── Agent A
├── Agent B
└── Agent C

하지만 모든 Agent가 전체 Session Context를 공유할 필요는 없다.

106. Multi-Agent Context Isolation

기본:

Session Context
↓
Scoped Projection
├── Agent A Context
├── Agent B Context
└── Agent C Context

를 사용한다.

107. Session Memory Isolation

Temporary Agent-specific working information을
Session-wide Memory로 자동 공유하지 않는다.

Agent Working State
≠
Shared Session Memory
108. Shared Session Information

명시적으로 공유할 수 있는 후보:

Task Goal

Current verified Task State

Shared Artifact References

Approved User Instructions

Verified Results
109. Session and Handoff

Agent Handoff가 Session 안에서 발생할 수 있다.

Session
↓
Agent A
↓
Handoff
↓
Agent B

Session이 바뀌지 않아도 Control Agent는 변경될 수 있다.

110. Session and Delegation

Delegation에서도 Parent / Child Agent가 동일 Session에 있을 수도,
별도 Execution Scope를 사용할 수도 있다.

정확한 Multi-Agent Session semantics는 Orchestration Specification에서 결정한다.

111. Session Contract Versioning

Session Contract도 향후 Version을 가질 수 있다.

Session Contract v1
↓
Session Contract v2

Storage Schema와 Architecture Contract Version을 구분한다.

112. Session Schema Version
Session Contract Version
≠
Session Record Revision
≠
Storage Schema Version

을 구분한다.

113. Session Revision

Session Metadata가 변경될 때 Revision을 가질 수 있다.

예:

Session Revision 1

Session Revision 2

정확한 concurrency model은 Specification에서 결정한다.

114. Concurrent Session Updates

여러 Runtime / Agent가 동일 Session Metadata를 수정할 경우:

Optimistic Concurrency

Revision Check

Conflict Detection

등을 사용할 수 있다.

초기 구현에서는 가능한 한 Session Metadata mutation을 최소화한다.

115. Failure Attribution

Session 관련 Failure 후보:

Session Store Failure

Invalid Session Reference

Unauthorized Session Access

Broken Conversation Reference

Stale Context Reference

Runtime Attachment Failure

Agent Attachment Failure

Scope Leakage

Invalid Lifecycle Transition
116. Session Failure vs Task Failure
Session Failure
≠
Task Failure

예:

Interactive Session unavailable
↓
Task continues in background

가 가능하다.

117. Session Evaluation

Session Architecture 품질 후보:

Continuity

Isolation

Recoverability

Traceability

Privacy

Reference Integrity

Runtime Replaceability

Agent Replaceability

Task Independence

Context Reconstruction
118. Session Continuity Evaluation

PoC:

Session
↓
Agent A
↓
Runtime A
↓
Runtime Failure
↓
Runtime B
↓
Agent B
↓
Continue Session

가능 여부를 확인한다.

119. Cross-Session Task Evaluation
Task
↓
Session A
↓
Closed

Task persists

↓
Session B
↓
Resume

후에도 Goal과 Task State가 유지되는지 평가한다.

120. Context Reconstruction Evaluation
Session
↓
Context A
↓
Runtime End

Later

Task State
+
Memory
+
Knowledge
+
Artifacts
+
Current Environment
↓
Context B

를 구성하고 작업을 이어갈 수 있어야 한다.

121. Privacy Isolation Evaluation

Session A의 private information이
권한 없는 Session B로 전달되지 않는지 확인한다.

122. Initial Implementation Candidate

첫 PoC에서 Session은 최소 다음만 구현해도 된다.

Session ID

Status

Principal / Identity Reference

Created At

Updated At

Task References

Conversation Reference

Current / Recent Agent Reference

Runtime / Execution References

Basic Scope
123. Minimal Session Store

후보:

Session Repository

는 Session Metadata만 관리한다.

Task State, Memory, Artifact를 복제하지 않는다.

124. Deferred Implementation

초기 PoC에서 다음은 미룰 수 있다.

Complex Session Branching

Distributed Session Coordination

Cross-device Live Session Sync

Advanced Session Replay

Persistent Multi-Agent Session Graph

Complex Session Merge

Automatic Session Deduplication

Sophisticated Session TTL Policies
125. Minimal PoC Scenario
1. Session 생성

2. User Intent 입력

3. Task 생성 / 연결

4. Agent Instance 생성

5. Context Projection 생성

6. Runtime 시작

7. Capability 실행

8. Session / Task Trace 기록

9. Runtime 종료

10. 새 Runtime 생성

11. 동일 Session 재연결

12. Context 재구성

13. Agent 실행 계속

14. Session 종료

15. Task는 유지
126. Cross-Session PoC
1. Task 생성

2. Session A에서 작업

3. Task State 저장

4. Session A 종료

5. Session B 생성

6. 동일 Task 연결

7. Task State 로드

8. Context 재구성

9. 작업 계속

10. Verification

11. Task 완료
127. Multi-Task Session PoC

후속:

Session A
├── Task 1
└── Task 2

두 Task의 State가 서로 섞이지 않는지 검증한다.

128. Runtime Replacement PoC
Session A
↓
Runtime 1
↓
Failure
↓
Runtime 2
↓
Continue

Session Metadata와 Task State가 유지되는지 확인한다.

129. Agent Replacement PoC
Session A
↓
Agent 1
↓
Terminate
↓
Agent 2
↓
Continue

Identity와 Task continuity가 유지되어야 한다.

130. Acceptance Criteria

Session Architecture v0.1은 최소 다음을 만족해야 한다.

Session is independent from Task identity.

Task can survive Session termination.

A Task can span multiple Sessions.

A Session can reference multiple Tasks.

Session is distinguishable from Conversation.

Session is distinguishable from Context.

Session is distinguishable from Runtime.

Session is distinguishable from Agent Instance.

Runtime can be replaced without necessarily ending the Session.

Agent Instance can be replaced without necessarily ending the Session.

Session closure does not automatically complete or cancel Tasks.

Context can be reconstructed rather than blindly restored.

Session deletion does not automatically delete durable Artifacts, Memory, Tasks, or Identity.

Cross-session information sharing requires explicit durable references or scoped information.
131. Architecture Invariants
Session must not become the Task source of truth.

Session must not become the Task State source of truth.

Conversation History must not be treated as Session itself.

Session must not depend on one Agent Instance.

Session must not depend on one Runtime Instance.

Session must not depend on one Model.

Session closure must not imply Task completion.

Session timeout must not imply Task deadline expiration.

Session context must not be blindly reused as current truth.

Session must not grant Permission by itself.

Credentials must not be stored directly in Session Context.

Session deletion must not automatically cascade across persistent domains.
132. Stable Boundaries

현재 안정적으로 유지할 후보:

Session semantics

Session / Task separation

Session / Conversation separation

Session / Context separation

Session / Runtime separation

Session / Agent separation

Session / Identity separation

Cross-session Task continuity

Session lifecycle independence
133. Replaceable Implementations

다음은 교체 가능해야 한다.

Session Storage

Session Repository

Conversation Backend

Session ID Generation

Session TTL Implementation

Session Serialization

Session Transport

Session Manager Framework
134. Deferred Decisions

현재 최종 결정하지 않는다.

Exact Session Schema

Exact Session State Machine

Exact Session-to-Task Cardinality Storage Model

Exact Conversation Storage

Exact Session TTL

Exact Session Resume Policy

Exact Session Archive Policy

Exact Session Replay Format

Exact Non-interactive Execution Relationship

Exact Background Session Semantics

Exact Multi-Agent Session Model
135. Related Architecture

본 문서는 다음 Architecture와 연결된다.

System Architecture

Identity Architecture

Agent Architecture

Task Architecture

State Architecture

Context Architecture

Harness Architecture

Runtime Architecture

Memory Architecture

Security Architecture

Orchestration Architecture

Observability Architecture
136. Related Decisions

주요 Decision:

DDR-001
Task State / Runtime Boundary

DDR-002
Harness Boundary

DDR-006
Orchestration Contract

추가 관련 Decision:

DDR-003
Memory / Knowledge Boundary

DDR-004
Artifact Architecture

DDR-005
Identity Persistence
137. Specification Questions

후속 Specification에서 결정해야 할 질문:

What is the minimum Session schema?

What exactly creates a Session?

Can non-interactive execution omit a Session?

How are Task references represented?

How are Conversation references represented?

What constitutes Session closure?

When does a Session expire?

Can a Closed Session be reopened?

When should a new Session be created instead?

Which Session metadata is durable?

How are Agent and Runtime references tracked?

How is Context lineage represented?

How are Security Context references represented?

How are cross-session references authorized?

How are concurrent Session updates handled?
138. Architecture Boundary

본 문서는 Session의 Logical Architecture를 정의한다.

다음은 아직 정의하지 않는다.

Concrete Python Classes

Exact Database Tables

Exact API Endpoints

Exact WebSocket / HTTP Protocol

Exact Session Manager

Exact Conversation Implementation

Exact Runtime Framework

Exact UI Session Model
139. Initial Design Preference

v0.1에서는 Session을 지나치게 중요한 중앙 상태 객체로 만들지 않는다.

Session은:

Interaction Boundary

References

Lifecycle

Observability Scope

에 집중한다.

Task, Identity, Memory, Artifact 등의 Durable Domain을
Session 내부로 흡수하지 않는다.

140. Why Session Should Stay Lightweight

Session이 모든 것을 소유하면:

Session
├── Task State
├── Memory
├── Artifacts
├── Runtime
├── Agent
└── Context

Runtime replacement와 Long-horizon Task가 Session Lifecycle에 종속된다.

따라서 NOAH는 Session을 가능한 한 Lightweight Boundary로 유지한다.

141. Session Architecture Candidate

현재 후보:

                    SESSION
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   Conversation    Task Refs    Execution Refs
        │             │             │
        │             │        Agent / Runtime
        │             │
        │        Task State
        │        (external)
        │
 Context Lineage
   (references)

Session은 이 Domain을 연결하지만
각 Domain의 Source of Truth를 소유하지 않는다.

142. Current Architecture Statement

Project NOAH의 Session은 Task나 Conversation 자체가 아니라,
일정 기간 발생하는 User, Agent, Runtime 및 Task 사이의 상호작용을 연결하는 bounded interaction / execution continuity boundary다.

Task는 여러 Session을 넘어 지속될 수 있으며,
하나의 Session에서도 여러 Task를 다룰 수 있다.

Session은 Task State, Identity, Memory, Artifact 또는 Runtime의 Source of Truth가 아니며,
이들을 Stable Reference를 통해 연결하고 실행 및 관찰의 상관관계를 제공한다.

Runtime이나 Agent Instance가 교체되어도 Session을 유지할 수 있고,
Session이 종료되어도 Durable Task와 Artifact, Memory 및 Identity는 독립적으로 지속될 수 있다.

143. Final Principle

Session은 NOAH의 기억이나 목표를 담는 상자가 아니다.

Session은 일정 시간 동안 서로 다른 지속적·일시적 Component가 함께 작업할 수 있도록 연결해 주는 경계다.

Session이 끝나도 Task와 Identity는 끝나지 않아야 하며, 새로운 Session에서도 필요한 지속성을 다시 이어갈 수 있어야 한다.