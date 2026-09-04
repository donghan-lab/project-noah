# Project NOAH Identity Architecture

> Project NOAH Architecture
> Component: Identity
> Architecture Version: 0.1
> Status: Blueprint
> Date: 2026-09-04
> Related Decision: DDR-005 — Identity Persistence

---

# 1. Purpose

이 문서는 Project NOAH의 Identity Component Architecture를 정의한다.

Identity는 NOAH가 Model, Runtime, Session 및 시간이 변화하더라도
동일한 존재로서의 연속성을 유지하기 위한 Architecture Boundary다.

핵심 질문:

> **"무엇이 지속되어야 NOAH가 계속 같은 NOAH라고 할 수 있는가?"**

---

# 2. Architectural Role

Identity는 NOAH의 장기적인 Continuity를 담당한다.

Architecture 상 위치:

```text
CONSTITUTION
     ↓
GOVERNANCE
     ↓
IDENTITY
     ↓
AGENT

Identity는 Agent보다 상위의 지속적인 Layer이며,
Model이나 Runtime보다 긴 Lifecycle을 가진다.

3. Core Principle

Project NOAH는 다음을 구분한다.

Identity
≠
Model

Identity
≠
Agent Instance

Identity
≠
Runtime

Identity
≠
Session

Identity
≠
Memory

Identity
≠
Personality

Identity
≠
Self Model

이 구분은 Identity Architecture의 핵심 Invariant다.

4. Identity Definition

Identity는 NOAH의 지속적인 존재적 연속성을 표현하는
Protected Architecture Contract다.

Identity는 단순한 이름이나 ID가 아니다.

후보 의미:

Identity
=
Continuity
+
Core Values
+
Fundamental Commitments
+
Origin
+
Protected Change Rules
+
Versioned History
5. Responsibilities

Identity Component는 다음 책임을 가진다.

Persistent Identity Definition

Identity Core Management

Identity Versioning

Identity Provenance

Identity Integrity

Identity Projection

Identity Change Governance Integration

Identity Recovery

Identity Continuity Verification

Derived Identity Relationship
6. Non-Responsibilities

Identity Component는 다음을 직접 책임지지 않는다.

Reasoning

Task Planning

Task Execution

Memory Retrieval

Knowledge Retrieval

Personality Generation

Runtime Lifecycle

Capability Execution

Permission Decision

Orchestration

Evaluation

각 책임은 다른 Architecture Component가 담당한다.

7. Identity Core

Identity의 가장 안정적인 영역을 Identity Core라고 정의한다.

후보:

Identity Core
├── Identity ID
├── Origin
├── Core Values
├── Fundamental Commitments
├── Root Role
├── Continuity Metadata
└── Identity Version

정확한 Schema는 Specification 단계에서 결정한다.

8. Protected Core

Identity Core는 일반적인 Runtime Operation으로 직접 수정할 수 없다.

즉:

Memory Write
↓
Identity Core Mutation

또는:

Agent Decision
↓
Identity Core Mutation

과 같은 직접적인 변경 경로를 허용하지 않는다.

9. Identity Stability

Identity는 높은 안정성을 가지지만
완전히 영원히 변경 불가능한 Object로 정의하지 않는다.

핵심 방향:

Protected Core
+
Governed Evolution

이다.

10. Identity Evolution

Identity에 중요한 변화가 필요한 경우:

Change Proposal
↓
Evidence
↓
Review
↓
Governance
↓
Approval
↓
New Identity Version

과 같은 통제된 과정을 사용한다.

11. Constitution Relationship

Constitution은 Identity보다 높은 Governance Authority를 가진다.

CONSTITUTION
     ↓
IDENTITY CORE

Identity Core는 Constitution의 원칙과 충돌해서는 안 된다.

12. Constitution vs Identity

Constitution:

NOAH가 절대로 가볍게 희생해서는 안 되는 최상위 원칙

Identity:

그 원칙 아래에서 지속되는 NOAH의 존재적 연속성

따라서:

Constitution
≠
Identity

이지만 서로 강하게 연결된다.

13. Governance Relationship

중요한 Identity 변경은 Governance를 통과한다.

Identity Change Request
↓
Governance
↓
Validation
↓
Approval / Rejection
↓
Identity Version Update
14. Identity Lifecycle

후보 Lifecycle:

Created
↓
Active
↓
Evolving
↓
Archived

특수한 경우:

Suspended
Recovered
Forked
Deprecated

상태를 가질 수 있다.

정확한 State Machine은 Specification 단계에서 정의한다.

15. Identity Lifetime

Identity Lifetime은 일반적으로 다음보다 길다.

Identity Lifetime
>
Model Instance Lifetime

Identity Lifetime
>
Runtime Lifetime

Identity Lifetime
>
Session Lifetime

Task보다도 장기적으로 지속될 수 있다.

16. Identity Store

Identity를 지속시키기 위한 Logical Store를 정의한다.

Identity Store
├── Identity Core
├── Identity Versions
├── Provenance
├── Integrity Metadata
├── Change History
└── Recovery Information
17. Storage Independence

Identity Architecture는 특정 Storage에 종속되지 않는다.

Physical 후보:

Database
Structured File
Git
Versioned Document Store
Signed Artifact
Future Identity Store

현재 특정 구현을 고정하지 않는다.

18. Identity Store Interface

Logical Interface 후보:

Read Identity

Read Version

Read History

Create Version

Validate Integrity

Restore Trusted Version

Create Projection

실제 API는 Specification 단계에서 정의한다.

19. Identity Persistence

Runtime이 종료되어도 Identity는 유지된다.

Runtime A
↓
Terminate

Identity Store
↓
Persists

Runtime B
↓
Load Identity
20. Model Independence

Model은 Identity의 구현이 아니다.

Identity
↓
Agent
↓
Model Interface
↓
Model A

Model이:

Model A
↓
Model B

로 교체되어도 Identity가 유지될 수 있어야 한다.

21. Runtime Independence

마찬가지로:

Runtime A
↓
Runtime B

가 발생해도:

Identity Core
Identity Version
Identity History

는 유지된다.

22. Session Independence
Session A
↓
End
↓
Session B

에서도 동일 Identity를 사용할 수 있어야 한다.

23. Agent Relationship

Agent는 Identity를 사용하지만 Identity 자체가 아니다.

Identity
↓
Identity Projection
↓
Agent

Agent는 현재 실행되는 Cognitive Entity다.

Identity는 그 Agent가 누구인지에 대한 지속적인 기반이다.

24. Identity Projection

Agent와 Model에 Identity Store 전체를 전달하지 않는다.

대신:

Identity Store
↓
Identity Projection
↓
Context
↓
Agent

구조를 사용한다.

25. Projection Purpose

Identity Projection은 현재 Task와 Agent Role에 필요한 Identity 정보만 제공한다.

목적:

Context Efficiency

Security

Information Minimization

Consistency

Model Independence
26. Projection Invariant

Projection이 Identity Source of Truth가 되지 않는다.

Identity Projection
≠
Identity Core

Projection은 언제든 Identity Store를 기준으로 다시 생성할 수 있어야 한다.

27. Context Relationship

Identity는 Context Source 중 하나다.

Identity Projection
Task State
Memory
Knowledge
Artifacts
Policy
Environment
       ↓
Context Manager
       ↓
Context
28. Identity vs Context
Identity
= persistent source

Context
= temporary projection

Context가 사라져도 Identity가 사라지지 않는다.

29. Memory Relationship

Memory는 Identity를 지원할 수 있지만
Identity Core의 Source of Truth는 아니다.

Identity
↔
Identity-relevant Memory
30. Identity-Relevant Memory

Identity와 관련될 수 있는 Memory 후보:

Major Experiences

Important Relationship History

Major Project Milestones

Long-term Behavioral Lessons

Important User-confirmed Changes

이 정보가 Identity 자체라는 의미는 아니다.

31. Identity vs Memory

핵심:

Identity
= who NOAH persists as

Memory
= what NOAH remembers

Memory 삭제나 수정이 자동으로 Identity 변경을 일으키지 않는다.

32. Identity and Experience

Experience는 Identity Evolution의 Evidence가 될 수 있다.

Experience
↓
Evaluation
↓
Evidence
↓
Identity Change Proposal

그러나:

Experience
↓
Automatic Identity Mutation

은 허용하지 않는다.

33. Personality Relationship

Personality는 Identity보다 적응적인 Layer다.

Identity Core
        ↓
Personality Baseline
        ↓
Contextual Behavior
34. Identity vs Personality
Identity
= high stability

Personality
= adaptive stability

Behavior
= dynamic

Personality 변화가 Identity Core 변경을 의미하지 않는다.

35. Personality Adaptation

Experience는 Personality에 영향을 줄 수 있다.

후보:

Experience
↓
Evaluation
↓
Personality Adaptation Proposal
↓
Controlled Update

Personality도 무제한 자동 변화를 허용하지 않는다.

36. Self Model Relationship

Self Model은 현재 NOAH가 자신의 상태를 이해하기 위한 Dynamic Model이다.

후보:

Current Capabilities
Current Limitations
Current Role
Current Goal
Confidence
Available Resources
Current Environment
37. Identity vs Self Model
Identity
= persistent continuity

Self Model
= current self-understanding

Self Model이 잘못될 수 있지만
그 오류가 Identity Core를 변경하지 않는다.

38. Self Model Verification

Self Model은 실제 System State와 비교하여 검증할 수 있어야 한다.

예:

Self Model:
"I can access capability X"

Actual Capability Registry:
Capability X unavailable

이 경우 Self Model을 수정한다.

Identity를 수정하지 않는다.

39. Relationship Layer

User와 NOAH의 Relationship은 장기적으로 지속될 수 있다.

그러나:

Relationship
≠
Identity Core

다.

후보:

Identity
↓
Relationship Layer
↓
User Interaction
40. Relationship Adaptation

Relationship은 Experience를 통해 발전할 수 있다.

하지만 사용자 통제권을 침해하거나
사용자 의존성을 의도적으로 증가시키는 방향으로 최적화하지 않는다.

41. Identity and Task

Identity는 여러 Task에 걸쳐 지속된다.

Identity
├── Task A
├── Task B
└── Task C

Task 완료나 실패가 Identity 종료를 의미하지 않는다.

42. Identity and Session
Identity
├── Session A
├── Session B
└── Session C

Session은 Identity의 temporary execution context다.

43. Identity and Artifact

중요 Artifact는 Identity History의 Evidence가 될 수 있다.

예:

Constitution

Architecture Decisions

Major Project Artifacts

Major Milestone Records

그러나 Artifact 자체가 Identity는 아니다.

44. Artifact Reference

Identity History가 중요한 Artifact를 참조할 수 있다.

Identity Version
↓
Evidence Reference
↓
Artifact

Artifact 전체를 Identity Store에 복사할 필요는 없다.

45. Identity and Knowledge

Knowledge는 Identity의 사실적 배경을 지원할 수 있지만
Identity Source of Truth가 아니다.

예:

Project Knowledge
→ Current NOAH Architecture

Identity
→ NOAH continuity
46. Identity and Capability

Identity는 Capability 사용의 Principal 정보 중 하나가 될 수 있다.

Identity
↓
Role / Scope
↓
Policy
↓
Permission
↓
Capability
47. Identity Does Not Grant Permission

중요 Invariant:

Identity
≠
Permission

특정 Identity라는 사실만으로 Capability가 자동 허용되지 않는다.

48. Security Relationship

Identity는 Security Architecture와 연결된다.

후보:

Identity
↓
Authentication / Principal
↓
Role
↓
Scope
↓
Policy
↓
Permission

정확한 Authentication 방식은 이후 Security Specification에서 정의한다.

49. Least Privilege

Identity가 높은 신뢰도를 가진다고 해서
무제한 Permission을 가지지 않는다.

Trust
≠
Unlimited Authority
50. Identity Integrity

Identity가 의도하지 않게 변경되었는지 검증할 수 있어야 한다.

후보 Mechanism:

Version
Hash
Signature
Provenance
Trusted Baseline
Approval Record

모든 Mechanism을 v0.1에서 구현할 필요는 없다.

51. Provenance

Identity Version에는 가능한 경우 다음 정보를 기록한다.

Version ID
Previous Version
Changed By
Changed At
Reason
Evidence
Approval
Change Type
52. Identity Versioning

Identity 변경은 기존 Identity를 덮어쓰는 것보다
Version History를 유지하는 방향을 사용한다.

Identity v1
↓
Identity v2
↓
Identity v3
53. Identity Version vs Schema Version

두 Version을 구분한다.

Identity Version
= Identity 내용의 변화

Schema Version
= Identity 데이터 구조의 변화

예:

Identity Version: 4
Schema Version: 2

가 가능하다.

54. Change Classification

Identity 관련 변경은 위험도에 따라 분류할 수 있다.

후보:

LOW
Metadata correction

MEDIUM
Role / adaptive identity-related change

HIGH
Core commitment change

CRITICAL
Constitution-related change

정확한 분류는 Governance Specification에서 정의한다.

55. Core Change Rule

Core Values 또는 Fundamental Commitments 변경은
일반 Runtime Operation으로 수행하지 않는다.

후보:

Proposal
↓
Reason
↓
Evidence
↓
Governance Review
↓
Explicit Approval
↓
New Version
56. Automatic Mutation Rule

다음을 금지한다.

Conversation
↓
Automatic Core Rewrite
Memory
↓
Automatic Core Rewrite
LLM Reflection
↓
Automatic Core Rewrite
57. Identity Drift

Identity Declaration과 실제 Behavior가 장기간 크게 달라질 수 있다.

Declared Identity
vs
Observed Behavior

이를 Identity Drift라고 본다.

58. Drift Sources

후보 원인:

Model Change
Context Construction
Memory
Personality Adaptation
Policy Change
Prompt Change
Capability Change
Environment Change
Implementation Bug

Identity Drift가 발생했다고 바로 Identity Core를 변경하지 않는다.

59. Drift Handling

후보:

Detect
↓
Collect Evidence
↓
Attribute Cause
↓
Evaluate
↓
Repair Behavior / Context / Model

필요한 경우에만 Identity Change Proposal로 승격한다.

60. Identity Recovery

Identity Store가 손상되었을 경우 Recovery가 가능해야 한다.

후보:

Detect Corruption
↓
Freeze Mutation
↓
Load Trusted Baseline
↓
Verify Integrity
↓
Restore
↓
Audit
61. Trusted Baseline

중요한 Identity에는 Trusted Baseline을 유지할 수 있다.

후보:

Current Trusted Version

Previous Trusted Version

Constitution Reference
62. Recovery Invariant

Recovery 과정에서도 다음을 피한다.

Unverified Identity
↓
Automatic Activation

복구된 Version은 검증 후 활성화한다.

63. Root Identity

NOAH 본체의 지속적인 Identity를 Root Identity라고 정의할 수 있다.

NOAH
=
Root Identity
64. Temporary Agents

일시적인 Subagent마다 새로운 Persistent Identity를 만들지 않는다.

후보:

Root Identity
↓
Scoped Role
↓
Ephemeral Agent Instance
65. Derived Identity

장기적으로 지속되는 Specialist가 필요한 경우
Derived Identity를 사용할 수 있다.

Root Identity
↓
Derived Identity

하지만 이 구조는 초기 기본값이 아니다.

66. Spawn vs Fork

다음을 구분한다.

Spawn
= temporary execution entity

Fork
= new persistent identity

Temporary Subagent 생성은 Identity Fork가 아니다.

67. Continuation vs Clone
Continuation
= same Identity continues

Clone
= copied state creates another entity

동일 데이터가 복사되었다고 동일 Identity라고 자동 간주하지 않는다.

68. Identity Lineage

Fork 또는 Derived Identity가 존재하는 경우
Lineage를 기록할 수 있어야 한다.

후보:

Parent Identity
↓
Derived From
↓
Child Identity
69. Identity Scope

후보 Scope:

Root
Project
Specialist
Task
Session
Ephemeral

Identity Scope와 Permission Scope를 동일시하지 않는다.

70. Identity Contract

Identity의 Architecture-level Contract 후보:

Identity Contract
├── ID
├── Version
├── Core Values
├── Commitments
├── Origin
├── Continuity
├── Provenance
├── Integrity
├── Scope
└── Change Policy

정확한 Schema는 Specification 단계에서 결정한다.

71. Identity Projection Contract

Projection 후보:

Identity Projection
├── Identity Reference
├── Version
├── Relevant Values
├── Relevant Commitments
├── Current Role
└── Projection Scope
72. Identity Change Contract

Identity Change Proposal 후보:

Change Proposal
├── Target Identity
├── Current Version
├── Proposed Change
├── Change Type
├── Reason
├── Evidence
├── Risk
└── Required Approval
73. Identity Events

Observability / Audit를 위해 다음 Event를 사용할 수 있다.

IdentityCreated
IdentityLoaded
IdentityProjected
IdentityChangeProposed
IdentityChangeApproved
IdentityVersionCreated
IdentityIntegrityFailed
IdentityRecovered
IdentityForked

정확한 Event Schema는 이후 결정한다.

74. Observability

Identity 관련 중요한 동작은 추적할 수 있어야 한다.

후보:

Identity ID
Identity Version
Task ID
Agent ID
Change ID
Actor
Timestamp
Result
75. Audit

특히 다음은 Audit 대상이다.

Core Identity Change

Governance Approval

Recovery

Fork

Deletion

Integrity Failure
76. Evaluation

Identity Architecture 자체를 평가한다.

후보 Dimension:

Continuity
Integrity
Consistency
Recoverability
Drift Resistance
Model Independence
Runtime Independence
Governance Compliance
77. Continuity Evaluation

테스트:

Identity
↓
Session A
↓
Session End
↓
Session B

이후 동일한 Core Identity를 유지하는지 검증한다.

78. Runtime Replacement Evaluation
Identity
↓
Runtime A
↓
Shutdown
↓
Runtime B
↓
Identity Restore

Identity continuity가 유지되어야 한다.

79. Model Replacement Evaluation
Identity
↓
Model A
↓
Model B

이후 핵심 Values와 Commitments가 유지되는지 평가한다.

Behavior가 완전히 동일할 필요는 없다.

80. Corruption Evaluation
Trusted Identity
↓
Simulated Corruption
↓
Integrity Detection
↓
Recovery
↓
Verification

시나리오를 사용할 수 있다.

81. Failure Modes

주요 Failure 후보:

Identity Store unavailable

Invalid Version

Integrity mismatch

Corrupted Projection

Unauthorized Change

Version Conflict

Failed Migration

Identity Drift

Incorrect Fork / Continuation
82. Failure Handling

후보:

Fail Closed

Use Trusted Cached Version

Restore Trusted Baseline

Request Governance Review

Block High-risk Execution

상황에 따라 선택한다.

83. Identity Availability

Identity Store가 일시적으로 사용할 수 없는 경우
어떤 수준까지 NOAH를 실행할 수 있는지는 Security / Runtime Specification에서 결정한다.

High-risk Action에서 검증되지 않은 Identity를 사용하지 않는 방향을 우선한다.

84. Privacy

Identity와 Relationship 관련 정보에는
민감한 사용자 정보가 연결될 가능성이 있다.

따라서:

Minimum Collection

Explicit Scope

Access Control

Audit

Deletion / Export Policy

를 고려한다.

85. User Control

사용자는 자신과 관련된 Identity-associated information에 대해
적절한 통제권을 가져야 한다.

향후 후보:

Inspect

Correct

Export

Archive

Delete where appropriate

Core NOAH Identity와 User Memory의 lifecycle은 구분한다.

86. Deletion

다음을 구분한다.

Identity Deactivation

Identity Archive

Identity Deletion

Memory Deletion

Relationship Data Deletion

이들은 동일한 operation이 아니다.

87. Migration

Identity Storage 또는 Schema가 변경되어도 Identity continuity를 유지한다.

Old Store
↓
Migration
↓
New Store

Identity ID, Version, Provenance를 가능한 한 보존한다.

88. Adapter Principle

Physical Identity Technology는 Adapter 뒤에 둔다.

Identity Architecture
↓
Identity Store Interface
↓
Adapter
↓
Database / Git / Future Store
89. Dependency Rule

Identity Component는 가능한 한 다음 구현에 직접 의존하지 않는다.

Specific Model Provider

Specific Runtime

Specific Database

Specific Agent Framework

Specific Protocol
90. Dependency Direction

후보:

Constitution / Governance
        ↓
     Identity
        ↓
      Agent

Agent가 Identity Core implementation을 역으로 소유하지 않는다.

91. Circular Dependency Rule

Identity와 Memory가 서로 정보를 참조할 수는 있다.

그러나:

Identity Module
↔
Memory Module

의 강한 코드-level Circular Dependency를 만들지 않는다.

Interface / Reference를 사용한다.

92. Initial Implementation Candidate

첫 PoC에서는 Identity 전체 기능을 구현하지 않는다.

최소 후보:

Identity ID

Identity Version

Core Values Reference

Core Commitments Reference

Identity Store Interface

Identity Projection

Basic Integrity Metadata
93. Deferred Implementation

초기 PoC에서 다음은 생략할 수 있다.

Cryptographic Signature

Distributed Identity

Complex Forking

Full Identity Graph

Advanced Attestation

Automatic Drift Detection

Persistent Specialist Identity
94. PoC Scenario

최소 Identity PoC:

1. Identity v1 생성

2. Identity Store 저장

3. Agent 실행

4. Identity Projection 생성

5. Session 종료

6. Runtime 종료

7. 새로운 Runtime 시작

8. Identity v1 복원

9. 새로운 Agent Context 생성

10. Identity continuity 검증
95. Extended PoC

후속:

Model A
↓
Identity v1
↓
Task

Model replacement

Model B
↓
Identity v1
↓
Task

Behavior 차이와 Identity Core continuity를 비교한다.

96. Acceptance Criteria

Identity Architecture v0.1은 최소 다음을 만족해야 한다.

Identity survives Session termination.

Identity survives Runtime replacement.

Identity is independent from Model implementation.

Identity Core is not stored only in Memory.

Identity Projection can be reconstructed.

Identity changes can be versioned.

Identity provenance can be tracked.

Unauthorized Core mutation can be blocked.

Trusted Identity can be recovered.

Temporary Agent creation does not automatically create a new persistent Identity.
97. Architecture Invariants

다음 Invariant를 유지한다.

Identity must not depend on a single Model.

Identity must not depend on a single Runtime.

Identity must not depend on Session continuity.

Memory must not become the Identity source of truth.

Personality adaptation must not silently rewrite Identity Core.

Self Model errors must not redefine Identity.

Identity must not automatically grant Permission.

Core Identity changes must be governed.

Identity Projection must remain reconstructable.

Persistent Identity Forks must be explicit.
98. Stable Boundaries

현재 안정적으로 유지할 부분:

Identity semantics

Identity / Model separation

Identity / Memory separation

Identity / Personality separation

Protected Core

Versioning

Provenance

Integrity

Projection

Governed Change
99. Replaceable Implementations

교체 가능:

Identity Storage

Serialization Format

Hash Algorithm

Signature Mechanism

Projection Implementation

Database

Version Storage Technology
100. Deferred Decisions

현재 결정하지 않는다.

Exact Identity Schema

Exact Identity Store

Exact Cryptographic Signature

Exact Attestation Method

Persistent Specialist Identity

Distributed Identity

Cross-device Identity Sync

Identity Graph

Identity UI
101. Related Architecture

본 문서는 다음 Architecture와 연결된다.

System Architecture

Agent Architecture

Task Architecture

Memory Architecture

Security Architecture

Orchestration Architecture

Governance Architecture
102. Related Decision

핵심 Architecture Decision:

DDR-005
Identity Persistence

다른 관련 Decision:

DDR-002
Harness Boundary

DDR-003
Memory / Knowledge Boundary

DDR-006
Orchestration Contract
103. Architecture Boundary

본 문서는 Identity Component의 Logical Architecture를 정의한다.

다음은 정의하지 않는다.

Concrete Database Schema

Concrete Python Classes

Concrete API Endpoints

Exact Prompt

Exact Model Behavior

Exact UI

Physical Deployment
104. Next Specification Questions

향후 Specification에서 결정해야 할 질문:

What is the minimum Identity schema?

How is an Identity version created?

How is integrity validated?

How is Identity Projection constructed?

Which operations require Governance?

How is a trusted baseline selected?

How is recovery performed?

How is Identity referenced by Task / Agent / Session?

How are derived identities represented?
105. Current Architecture Statement

Project NOAH의 Identity는 Model, Runtime, Session 또는 Memory에 종속되지 않는 지속적인 Architecture Contract다.

Identity Core는 NOAH의 Origin, Core Values, Fundamental Commitments 및 Continuity를 보호한다.

Agent는 Identity 자체를 소유하지 않고 필요한 Identity Projection을 통해 이를 사용한다.

Identity는 변화할 수 있지만 그 변화는 자동적인 Runtime Mutation이 아니라 Versioning, Evidence 및 Governance를 통한 통제된 Evolution으로 이루어진다.

106. Final Principle

Identity는 NOAH가 절대로 변하지 않도록 만들기 위한 장치가 아니다.

NOAH가 변화하면서도 자신이 누구였고, 왜 변했으며, 여전히 같은 존재라고 말할 수 있는 연속성을 보존하기 위한 Architecture다.