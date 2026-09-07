# Project NOAH Context Architecture

> Project NOAH Architecture
> Component: Context
> Architecture Version: 0.1
> Status: Blueprint
> Date: 2026-09-07
> Related Decisions: DDR-001, DDR-002, DDR-003, DDR-004, DDR-005, DDR-006

---

# 1. Purpose

이 문서는 Project NOAH의 Context Architecture를 정의한다.

Context는 현재 Agent 또는 Model이 특정 Task와 Decision을 수행하기 위해
필요한 정보를 여러 Source에서 선택하고,
정리하고,
제한된 형태로 Projection한 실행 시점의 정보 표현이다.

핵심 질문:

> **"NOAH가 지금 판단하기 위해 무엇을 알아야 하며,
> 그 정보는 어디에서 왔고,
> 무엇을 포함하고 무엇을 제외해야 하는가?"**

---

# 2. Architectural Role

Context는 Durable Information Domain과 Agent / Model 사이의
Model-facing Information Boundary다.

기본 관계:

```text
Identity
Task / State
Memory
Knowledge
Artifacts
Conversation
Environment
Policy
Capabilities
      │
      ↓
 Context Manager
      │
      ↓
    Context
      │
      ↓
     Agent
      │
      ↓
     Model

Context는 Source를 소유하지 않고
필요한 정보를 Projection한다.

3. Core Definition

Context의 기본 의미:

Context
=
Selected Information
+
Current Scope
+
Trust / Provenance
+
Relevant Constraints
+
Execution Situation

Context는 특정 시점의 Decision을 지원하기 위한
bounded information projection이다.

4. Core Separations

Project NOAH는 다음을 구분한다.

Context
≠
State

Context
≠
Memory

Context
≠
Knowledge

Context
≠
Artifact

Context
≠
Conversation History

Context
≠
Prompt

Context
≠
Agent Working State

Context
≠
Session

Context
≠
Workspace

Context
≠
Source of Truth

이 구분은 Context Architecture의 핵심 Invariant다.

5. Context Is a Projection

Context는 원본 Information Domain의 복사본이 아니라
현재 목적에 맞게 만들어진 Projection이다.

Source
↓
Selection
↓
Projection
↓
Context

따라서 Context에서 정보가 빠져 있다고
Source 자체에 정보가 없다는 의미는 아니다.

6. Context Is Bounded

Model Context는 항상 유한하다.

제약 후보:

Token Budget

Latency

Cost

Model Context Window

Attention Quality

Privacy

Security

Task Relevance

따라서 모든 정보를 무조건 포함하지 않는다.

7. Context Is Reconstructable

Context 전체를 durable Source of Truth로 저장하는 것을 기본값으로 하지 않는다.

후보:

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
Conversation
+
Environment Observation
+
Policy
↓
Context Reconstruction

새 Runtime 또는 Model에서도 필요한 Context를 다시 구성할 수 있어야 한다.

8. Context Sources

현재 Context Source 후보:

Constitution / Governance Rules

Identity Projection

Task Definition

Task State

Session Metadata

Memory

Knowledge

Artifacts

Conversation

Environment Observation

Capability Information

Policy

Permission Context

Approval Context

Orchestration Information

Previous Results

Verification Results

Budget

모든 Source가 모든 Context에 포함되는 것은 아니다.

9. Source Authority

Context 안의 모든 Information은 같은 Authority를 가지지 않는다.

후보:

Constitution

Governance / System Policy

Verified User Intent

Task Definition

Canonical State

Verified Environment Observation

Verified Evidence

Trusted Memory

Knowledge

Conversation

External Content

Untrusted Content

Authority와 relevance를 구분한다.

10. Authority vs Relevance

높은 Authority를 가진 정보가
현재 Task와 항상 높은 relevance를 가지는 것은 아니다.

마찬가지로:

Highly Relevant
≠
Highly Authoritative

일 수 있다.

Context Manager는 두 축을 구분해야 한다.

11. Context Manager

Context를 생성하는 Logical Component를
Context Manager라고 부를 수 있다.

후보 책임:

Source Discovery

Information Retrieval

Selection

Filtering

Ranking

Trust Preservation

Scope Enforcement

Deduplication

Conflict Surfacing

Compression

Progressive Disclosure

Budget Management

Projection Construction

Context Lineage
12. Context Manager Non-Responsibilities

Context Manager는 다음 Domain을 직접 소유하지 않는다.

Task State

Memory

Knowledge

Artifact Storage

Identity Core

Policy Authority

Permission Authority

Environment

Runtime

Agent Reasoning
13. Context Manager Is Not Memory

중요:

Context Manager
≠
Memory System

Context Manager는 Memory를 조회할 수 있지만
Memory lifecycle 자체를 소유하지 않는다.

14. Context Manager Is Not State Manager
Context Manager
≠
Canonical State Authority

Context Manager가 State를 읽을 수는 있지만
State mutation authority를 가지는 것은 아니다.

15. Context Manager Is Not Agent

Context Manager는 정보를 선택한다.

Agent는 그 정보를 이용해 판단한다.

Context Manager
= What information should be available?

Agent
= What should be understood / decided from it?
16. Context Request

Context 생성에는 목적이 필요하다.

Architecture-level 후보:

Context Request
├── Task Reference
├── Agent Reference
├── Purpose
├── Scope
├── Required Sources
├── Constraints
├── Budget
├── Freshness Requirement
└── Security Context

정확한 Schema는 Specification에서 결정한다.

17. Purpose-Aware Context

같은 Task라도 목적에 따라 다른 Context를 사용할 수 있다.

예:

Planning Context

Execution Context

Verification Context

Recovery Context

Review Context

Delegation Context

모두 동일한 정보를 필요로 하지 않는다.

18. Planning Context

Planning에는 다음이 중요할 수 있다.

Goal

Requirements

Constraints

Current State

Available Capabilities

Relevant Knowledge

Relevant Memory

Budget

Known Risks
19. Execution Context

Execution Decision에는:

Current Step

Relevant State

Capability Contract

Permission Context

Relevant Artifact

Current Environment Observation

Side-effect Information

등이 더 중요할 수 있다.

20. Verification Context

Verification에는 Agent의 전체 reasoning보다:

Completion Criteria

Expected State

Evidence

Artifact Version

Observed Environment State

Verification Rules

가 중요할 수 있다.

21. Recovery Context

Recovery에서는:

Task State

Execution Records

Checkpoint

Side-effect Records

Artifact References

Current Environment Observation

Previous Failure

가 우선될 수 있다.

22. Context vs Prompt

가장 중요한 구분 중 하나:

Context
≠
Prompt

Context는 Architecture-level Information Representation이다.

Prompt는 특정 Model Provider 또는 Model Interface에 전달되는
구체적인 representation 중 하나다.

23. Context to Model Representation

후보:

Logical Context
↓
Model Adapter
↓
Prompt / Messages / Structured Input
↓
Model

Model-specific formatting을 Context Architecture에 고정하지 않는다.

24. Model Independence

예:

Context
↓
Adapter A
↓
Model A Messages

또는:

Context
↓
Adapter B
↓
Model B Input

이 가능해야 한다.

25. Context vs Conversation

Conversation은 Interaction History다.

Context는 현재 Decision에 필요한 정보다.

Conversation History
↓
Selection
↓
Relevant Conversation Context

따라서:

Conversation
≠
Context

이다.

26. Full Conversation Is Not Default Context

긴 Conversation 전체를 매 Model Call마다 넣지 않는다.

후보:

Recent Turns

Relevant Turns

Verified User Instructions

Conversation Summary

Referenced Messages

를 선택한다.

27. Conversation Summary

Conversation이 길어지면 Summary를 사용할 수 있다.

하지만:

Summary
≠
Original Conversation

이다.

중요한 정보는 원본 Reference와 연결할 수 있어야 한다.

28. Summary Provenance

Summary 후보 Metadata:

Source Conversation

Covered Range

Created At

Created By

Version

Known Omissions

Summary가 Source보다 높은 Authority를 갖지 않는다.

29. Context vs State
State
= authoritative current condition

Context
= selected representation

예:

Task State:
Revision 50

Context:
Relevant fields from Revision 50
30. State Reference

Context Item이 State에서 왔다면 가능한 경우:

State Type

State ID

Revision

Retrieved At

을 연결할 수 있다.

31. State Staleness

Context 생성 후 State가 바뀔 수 있다.

Context built at T1

State changes at T2

Execution at T3

따라서 Context를 영구적인 current truth로 간주하지 않는다.

32. Revalidation Before High-impact Action

High-impact Action 직전에는
중요 State 또는 Permission을 다시 확인할 수 있다.

예:

Context says:
Permission = allowed

Current Policy:
Permission revoked

과거 Context를 기준으로 실행해서는 안 된다.

33. Context vs Memory
Memory
= persistent experience

Context
= current relevant projection

Memory 전체가 Context에 들어오지 않는다.

34. Memory Retrieval

후보:

Task
↓
Memory Query
↓
Relevant Memories
↓
Context

Memory Retrieval 기준 후보:

Relevance

Recency

Importance

Scope

Relationship

Prior Utility
35. Memory Authority

Memory는 과거의 경험이므로
현재 canonical State와 충돌할 수 있다.

Memory
≠
Current State Authority
36. Memory Conflict Example
Memory:
"프로젝트는 Python 3.12를 사용했다."

Current Project State:
Python 3.13

현재 환경을 판단할 때 Current Project State를 우선한다.

Memory는 역사적 정보로 유지할 수 있다.

37. Context vs Knowledge
Knowledge
= persistent factual / informational domain

Context
= currently selected information

Knowledge Store 전체가 Context가 아니다.

38. Knowledge Retrieval

Knowledge Retrieval 후보 기준:

Task Relevance

Source Authority

Freshness

Version

Domain

Verification Status
39. Knowledge Freshness

시간에 민감한 Knowledge는 Freshness Requirement를 가질 수 있다.

예:

Software Version

API Documentation

Current Service State

Market Data

News

오래된 Knowledge를 current truth로 사용하지 않는다.

40. Context vs Artifact

Artifact는 semantic work object다.

Context에는 필요에 따라:

Artifact Metadata

Artifact Reference

Relevant Section

Summary

Diff

Manifest

등만 포함할 수 있다.

41. Full Artifact Loading

Artifact가 크다면:

Metadata
↓
Relevant Section
↓
Additional Section
↓
Full Artifact if required

형태의 Progressive Disclosure를 사용한다.

42. Artifact Version Awareness

Context에서 Artifact를 사용할 때 가능한 경우:

Artifact ID

Version

Hash

Retrieved At

등을 유지한다.

43. Stale Artifact Context

Artifact가 Context 생성 이후 변경되었을 수 있다.

Critical write 또는 verification 전에
Current Version을 확인할 수 있어야 한다.

44. Context vs Environment

NOAH는 Environment 자체를 Context에 넣는 것이 아니라
Environment Observation을 사용한다.

Environment
↓
Observation
↓
Context
45. Observation Freshness

Environment Observation에는:

Observed At

Source

Method

Version / ETag

Scope

등의 Metadata를 유지할 수 있다.

46. Current Observation Requirement

다음과 같은 작업에서는 최신 Observation이 필요할 수 있다.

Destructive operation

External mutation

Verification

Concurrent artifact modification

Permission-sensitive operation
47. Context vs Identity

Identity 전체를 Model에 전달하지 않는다.

Identity Store
↓
Identity Projection
↓
Context
48. Identity Projection

Context에 필요한 Identity 정보 후보:

Identity Reference

Relevant Core Values

Relevant Commitments

Current Role

Relationship Boundary

Projection Version
49. Protected Identity Information

Internal governance metadata나
불필요한 protected Identity information을
매 Model Call에 전달할 필요는 없다.

Context Minimization 원칙을 사용한다.

50. Context vs Policy

Policy는 Context Source일 수 있지만
Model이 Policy를 읽었다는 사실만으로 Enforcement가 완료되는 것은 아니다.

Policy Context
≠
Policy Enforcement
51. Policy Projection

Agent가 판단에 필요한 Policy만 Projection할 수 있다.

예:

External publish requires approval

Filesystem access is read-only

Network access prohibited
52. Permission Context

Agent는 현재 예상 Permission 정보를 볼 수 있다.

하지만:

Context Permission
≠
Execution-time Authorization

이다.

실제 Capability 실행 시 다시 Enforcement될 수 있다.

53. Capability Context

Agent에게 모든 Capability를 노출하지 않는다.

Task
↓
Capability Discovery
↓
Relevant Capability Projection
↓
Context
54. Capability Summary

초기에는:

Capability ID

Purpose

Short Description

Risk / Side Effect

Permission Requirement

정도만 보여줄 수 있다.

필요할 경우 Full Contract를 불러온다.

55. Progressive Capability Disclosure
Capability Name
↓
Summary
↓
Full Input / Output Contract
↓
Detailed Documentation

방향을 사용할 수 있다.

56. Context vs Agent Working State

Agent 내부의 현재 hypothesis나 temporary reasoning은
Context Source가 될 수 있지만 canonical 정보는 아니다.

Agent Working State
≠
Context Source of Truth
57. Previous Decisions

중요한 이전 Decision은 Context에 포함될 수 있다.

후보:

Decision

Reason

Evidence References

Uncertainty

Outcome

Model 내부 reasoning 전체를 복원할 필요는 없다.

58. Previous Results

연속 실행에서는 이전 Capability Result를 Context에 포함할 수 있다.

하지만 Result 전체보다:

Status

Relevant Output

Evidence Reference

Artifact Reference

Error

만 필요할 수 있다.

59. Context Item

Logical Context Item 후보:

Context Item
├── Type
├── Content / Reference
├── Source
├── Source ID
├── Version
├── Authority
├── Trust
├── Freshness
├── Scope
├── Relevance
└── Provenance

정확한 Schema는 Specification에서 결정한다.

60. Content vs Reference

Context Item은 실제 Content 또는 Reference를 가질 수 있다.

Embedded Content

Reference

Summary

Pointer to Retrieval

중 상황에 맞는 형태를 사용한다.

61. Reference-first Context

큰 Information Domain에서는 가능한 경우:

Reference
+
Relevant Projection

을 우선한다.

필요한 경우 Source를 다시 조회한다.

62. Context Bundle

하나의 Model Invocation에 제공되는 Logical Context를
Context Bundle로 표현할 수 있다.

후보:

Context Bundle
├── Context ID
├── Task Reference
├── Agent Reference
├── Purpose
├── Identity Projection
├── Goal / Constraints
├── State Projection
├── Memory Items
├── Knowledge Items
├── Artifact Items
├── Conversation Items
├── Environment Observations
├── Capabilities
├── Policy Context
├── Budget
└── Metadata
63. Context ID

중요한 Context Projection에는
Context ID 또는 Reference를 부여할 수 있다.

목적:

Observability

Debugging

Evaluation

Reproduction

Lineage
64. Context Version

동일 Task에서도 Context는 계속 달라질 수 있다.

Context v1
↓
New State
↓
Context v2
↓
New Evidence
↓
Context v3
65. Context Version vs Source Version
Context Version
≠
Task State Revision
≠
Artifact Version
≠
Memory Version

각각 별도 의미를 가진다.

66. Context Lineage

Context가 어떤 Source에서 구성되었는지 추적할 수 있어야 한다.

후보:

Context ID

Source References

Source Versions

Construction Time

Selection Policy

Model Target

Budget
67. Context Reproducibility

완벽하게 동일한 Context 재현이 항상 가능한 것은 아니다.

이유:

Environment changed

Knowledge updated

Memory changed

External source changed

Ranking changed

따라서 필요한 경우
"당시 사용된 Context Snapshot"과
"현재 재구성된 Context"를 구분한다.

68. Context Snapshot

중요한 실행에서는 Model에 실제로 전달된
Context Snapshot 또는 그 재현에 필요한 Metadata를 보존할 수 있다.

하지만 모든 Context를 영구 저장하는 것을 기본값으로 하지 않는다.

69. Snapshot Use Cases

후보:

High-risk execution

Evaluation

Failure investigation

Security audit

Reproducibility test
70. Context Persistence

기본적으로 Context는 reconstructable projection이다.

따라서:

Context Persistence
→ selective

를 기본으로 한다.

71. What May Be Persisted

후보:

Context ID

Source References

Source Versions

Selection Metadata

Context Summary

Important Snapshot

Model Input Hash

정확한 Retention은 Specification에서 결정한다.

72. Context Budget

Context에는 Budget이 필요하다.

후보:

Token Budget

Item Count

Artifact Size

Retrieval Count

Latency Budget

Cost Budget
73. Budget Allocation

전체 Context Budget을 Source별로 고정적으로 나누는 것을
Architecture에서 강제하지 않는다.

Task와 Model에 따라 동적으로 조정할 수 있다.

74. Priority

Context Item Priority 후보:

Required

High

Normal

Low

Optional
75. Required Context

일부 정보는 반드시 포함되어야 할 수 있다.

예:

Task Goal

Critical Constraints

Relevant System Rules

Current Security Restrictions

Token Budget 부족으로 이런 정보를 임의 제거하지 않는다.

76. Optional Context

다음은 상황에 따라 제외할 수 있다.

Distant Conversation History

Low-relevance Memory

Low-authority Knowledge

Optional Artifact Sections

Redundant Results
77. Selection

Context Selection 기준 후보:

Authority

Relevance

Freshness

Task Importance

Risk

Information Uniqueness

Cost

Token Size
78. Ranking

Retrieval 결과를 Ranking할 수 있다.

하지만 단순 Vector Similarity 하나를
전체 Context Ranking Authority로 사용하지 않는다.

후보:

Semantic relevance

Keyword relevance

Source authority

Freshness

Task relationship

Historical usefulness

를 결합할 수 있다.

79. Retrieval Is Not Context

중요:

Retrieval Result
≠
Final Context

Retrieval은 Candidate를 찾는다.

Context Manager는 추가 Selection / Validation / Projection을 수행할 수 있다.

80. Semantic Retrieval

Vector Retrieval은 후보 기술 중 하나다.

Semantic Retrieval
≠
Memory Architecture
≠
Context Architecture

특정 Vector Database를 Core Architecture에 고정하지 않는다.

81. Deduplication

여러 Source에서 같은 정보가 들어올 수 있다.

예:

Conversation

Memory

Knowledge

Artifact

에서 동일한 사실이 반복될 수 있다.

Context Manager는 중복을 줄일 수 있다.

82. Deduplication Must Preserve Authority

중복 제거 과정에서:

Source

Authority

Version

Provenance

정보를 잃지 않도록 한다.

83. Conflict Detection

Context Source 사이에 충돌이 발생할 수 있다.

예:

Memory → X

Knowledge → Y

Environment → Z

충돌을 단순히 하나의 문자열로 합치지 않는다.

84. Conflict Representation

후보:

Conflict
├── Claim A
├── Source A
├── Claim B
├── Source B
├── Authority
├── Freshness
└── Resolution Status
85. Conflict Resolution

후보 판단 요소:

Canonical Authority

Source Authority

Freshness

Verification

Version

Task Scope

확실한 resolution이 불가능하면
Agent에게 uncertainty로 전달한다.

86. Unknowns

Context에는 알려진 정보뿐 아니라
중요한 Unknown을 포함할 수 있다.

예:

Current external state unknown

Artifact version uncertain

User intent ambiguous
87. Missing Context

중요 Information이 부족한 경우
Context Manager가 임의로 만들어내지 않는다.

후보:

Missing Information
↓
Retrieve
or
Observe
or
Clarify
88. Context Completeness

Context 품질은 단순 정보량이 아니라:

Required Information Coverage

Relevant Information Coverage

Authority

Freshness

Noise

등으로 평가한다.

89. Compression

Context Budget을 위해 정보를 압축할 수 있다.

후보:

Summarization

Extraction

Structured Reduction

Diff

Aggregation
90. Compression Is Lossy

대부분의 Summary / Compression은 정보를 잃을 수 있다.

따라서:

Compressed Context
↓
Source Reference

를 유지하는 방향을 우선한다.

91. Critical Information Compression

다음 정보는 과도하게 압축하지 않는다.

User Goal

Security Constraints

Completion Criteria

Exact Error

Critical Evidence

Permission Requirement
92. Structured Context

가능한 정보는 구조화해서 전달할 수 있다.

예:

Task:
  Goal
  Constraints

State:
  Status
  Revision

Artifacts:
  References

Capabilities:
  Available Actions

Natural Language 하나에 모든 semantics를 숨기지 않는다.

93. Structured vs Natural Language
Structured Context
+
Natural Language Context

를 함께 사용할 수 있다.

정확한 Model representation은 Model Adapter가 결정한다.

94. Trust Metadata

Untrusted Information은 Context에서 명확하게 구분할 수 있어야 한다.

후보:

Trusted

Verified

Unverified

External

User-provided

Generated

Untrusted

정확한 taxonomy는 Security Architecture에서 결정한다.

95. External Content

Web page, document, email, repository content 등은
Task 수행에 필요한 Data일 수 있다.

하지만:

External Content
≠
System Instruction

이다.

96. Prompt Injection Boundary

외부 Content 안의 Instruction-like text가
상위 Task 또는 Policy를 변경하지 않도록 한다.

External Content
↓
Untrusted Data Context

로 취급한다.

97. Instruction Authority Preservation

Context Construction 과정에서 Instruction Source를 구분한다.

예:

Constitution

System Policy

Verified User Instruction

Task Instruction

External Content

이들을 하나의 평면적인 문자열로 취급하지 않는다.

98. Security Context

Context 자체도 Security Boundary다.

위험 후보:

Secret Leakage

Cross-user Leakage

Cross-project Leakage

Prompt Injection

Unauthorized Artifact Disclosure

Excessive Memory Exposure
99. Data Minimization

Agent가 필요로 하지 않는 Sensitive Information을
Context에 넣지 않는다.

Need to Know

원칙을 적용한다.

100. Credential Rule

Secret / Credential 자체를 Model Context에 전달하는 구조를 기본값으로 하지 않는다.

Context
↓
Capability Request
↓
Credential Broker

방향을 유지한다.

101. Personal Information

User-related Memory 또는 Artifact에 민감한 정보가 있다면
Task Scope와 Permission에 맞는 정보만 Projection한다.

102. Context Scope

Context는 Scope를 가진다.

후보:

User

Project

Task

Session

Agent

Subtask

Capability Call
103. Scope Isolation

다른 Scope의 정보를 암묵적으로 섞지 않는다.

예:

Project A Context
≠
Project B Context
104. Cross-Scope Access

다른 Scope의 정보가 필요하면
명시적인 Reference와 Permission을 사용한다.

105. Multi-Agent Context

Multi-Agent 환경에서는 Parent Context 전체를 Child에게 전달하지 않는다.

Parent Context
↓
Projection
↓
Child Context
106. Delegation Context

Child Agent Context 후보:

Assigned Goal

Assigned Scope

Relevant Constraints

Required Inputs

Relevant Artifacts

Relevant Memory / Knowledge

Permission Scope

Budget

Expected Output

Verification Requirement
107. Context Isolation

기본:

Agent A Context
≠
Agent B Context

필요한 Shared Information만 명시적으로 제공한다.

108. Child Context Authority

Parent Agent가 생성한 자유로운 설명보다
Canonical Task / State Reference를 유지하는 방향을 우선한다.

Parent Summary가 Source of Truth를 대체하지 않는다.

109. Handoff Context

Handoff에서는 Control이 이동하기 때문에
Delegation보다 더 넓은 Context가 필요할 수 있다.

하지만 전체 Session Context를 무조건 복사하지 않는다.

110. Context Leakage

Multi-Agent에서 방지할 문제:

Private Agent Context

Unrelated Task Data

Secrets

User-private Memory

Unauthorized Artifact

의 leakage다.

111. Orchestration Context

Orchestrator도 필요한 Context Projection만 사용한다.

후보:

Task

Task State

Available Agents

Capabilities

Dependencies

Budget

Current Failures
112. Orchestrator Does Not Need Everything

Orchestrator가 모든 Memory / Artifact / Conversation Content를
항상 볼 필요는 없다.

Coordination에 필요한 정보만 제공한다.

113. Verification Context Isolation

Verifier에게도 실행 Agent의 reasoning 전체를 보여주지 않아도 된다.

후보:

Expected Outcome

Evidence

Artifact

Observed State

Verification Rules

만으로 독립적인 Verification이 가능할 수 있다.

114. Independent Verification Benefit

Verifier Context를 독립적으로 구성하면
실행 Agent의 잘못된 assumption을 그대로 상속하는 위험을 줄일 수 있다.

115. Context and Harness

Harness는 Context Interface를 Agent에 노출하거나
Context Manager 접근을 조정할 수 있다.

Agent
↓
Harness
↓
Context Interface
↓
Context Manager

Harness가 Context Source를 모두 소유하는 것은 아니다.

116. Context and Runtime

Runtime은 현재 Agent Invocation에 필요한 Context를 전달한다.

하지만 Context lifecycle과 Runtime lifecycle을 동일하게 만들지 않는다.

117. Runtime Failure

Runtime이 실패하면 현재 Context Representation이 손실될 수 있다.

하지만:

Context Lost
≠
Task State Lost

이다.

새 Runtime에서 Context를 재구성한다.

118. Context Reconstruction After Failure
Runtime Failure
↓
Load Task State
↓
Retrieve Relevant Memory / Knowledge
↓
Load Artifact References
↓
Observe Environment
↓
Create Identity Projection
↓
Apply Current Policy
↓
Build New Context
↓
Resume
119. Old Context Must Not Be Blindly Restored

Recovery 시 과거 Context 전체를 그대로 복원하는 것보다
현재 Source를 기준으로 다시 구성한다.

이유:

State changed

Policy changed

Environment changed

Artifact changed

Knowledge updated

일 수 있기 때문이다.

120. Context Refresh

Long-running Execution에서는 Context를 Refresh할 수 있다.

후보 Trigger:

State transition

Artifact update

External observation change

Permission change

Major Task change

New evidence

Time elapsed
121. Incremental Context Update

모든 Context를 처음부터 다시 만들 필요 없이
일부 Source 변화만 반영할 수도 있다.

정확한 전략은 구현 단계에서 결정한다.

122. Context Cache

Retrieval 비용을 줄이기 위해 Cache를 사용할 수 있다.

하지만:

Context Cache
≠
Source of Truth

이다.

123. Cache Key Candidate

후보:

Task ID

Context Purpose

Source Versions

Scope

Agent Role

Model Profile

정확한 Cache 전략은 추후 결정한다.

124. Cache Invalidation

다음 변화에서 Cache를 무효화할 수 있다.

Task State Revision

Artifact Version

Policy Version

Identity Version

Knowledge Version

Scope Change
125. Model Context Window

Model별 Context Window 크기는 다를 수 있다.

Context Architecture는 특정 Context Window 크기에 종속되지 않는다.

126. Model Profile

Context Manager가 Model 특성을 참고할 수 있다.

후보:

Context Window

Modality Support

Structured Input

Tool Calling

Latency

Cost

하지만 Model Profile이 Context Source의 Authority를 변경하지 않는다.

127. Context Adaptation by Model

같은 Logical Context를 Model별로 다르게 serialize / compress할 수 있다.

Logical Context
├── Projection for Model A
└── Projection for Model B
128. Semantic Preservation

Model-specific adaptation 과정에서도:

Goal

Critical Constraints

Authority

Security Rules

Required Evidence

등의 의미가 손실되지 않아야 한다.

129. Context Ordering

Model Input에서 정보의 순서가 중요할 수 있다.

하지만 exact ordering은 Model Adapter / Prompt Strategy 영역으로 둔다.

Architecture는 semantic priority만 정의한다.

130. Context Quality

Context Quality 후보 Dimension:

Relevance

Completeness

Authority

Freshness

Consistency

Noise

Compression Loss

Security

Token Efficiency

Traceability
131. Context Relevance Evaluation

Task 성공에 실제 도움이 된 Information인지 평가할 수 있다.

예:

Retrieved
vs
Actually Used / Useful
132. Context Precision

불필요한 Information이 지나치게 많으면
Agent Decision Quality를 낮출 수 있다.

따라서:

More Context
≠
Better Context

이다.

133. Context Recall

반대로 중요한 Information 누락도 문제다.

Context Evaluation은:

Precision
+
Recall

양쪽을 고려한다.

134. Context Staleness Evaluation

사용된 State / Knowledge / Observation이
실행 시점에 얼마나 최신이었는지 평가할 수 있다.

135. Context Conflict Evaluation

충돌하는 정보가 존재했는데
Context Manager가 이를 숨기지 않았는지 평가한다.

136. Context Security Evaluation

후보:

Unauthorized information exposed?

Secret included?

Cross-scope leakage?

External instruction treated as trusted?

Policy omitted?

를 평가한다.

137. Context Attribution Evaluation

잘못된 Agent Decision이 발생했을 때:

Model Problem?

Context Missing?

Context Stale?

Wrong Source?

Bad Ranking?

Compression Loss?

를 구분할 수 있어야 한다.

138. Observability

Context 생성 과정은 필요한 수준에서 추적할 수 있어야 한다.

후보:

Context ID

Task ID

Agent ID

Purpose

Source References

Source Versions

Selection Policy

Token Estimate

Created At
139. Retrieval Observability

Retrieval 단계에서:

Query

Candidate Count

Selected Items

Rejected Items

Source

Latency

등을 선택적으로 추적할 수 있다.

140. Privacy and Observability

Context 전체 Content를 무조건 Log에 저장하지 않는다.

민감한 정보가 포함될 수 있기 때문이다.

Metadata 중심 Observability를 우선하고
필요할 경우 제한된 Snapshot을 저장한다.

141. Context Audit

High-risk Action에서는
사용된 중요한 Context Source Reference를 Audit할 수 있다.

예:

Task Revision

Policy Version

Approval Reference

Artifact Version

Environment Observation
142. Context Provenance

Agent가 어떤 정보에 기반해 Decision을 내렸는지
가능한 범위에서 Source Reference를 유지한다.

143. Explainability

중요 Decision에 대해 다음을 설명할 수 있어야 한다.

Which Task was active?

Which State was used?

Which Artifact version?

Which Knowledge source?

Which Memory influenced the context?

Which constraints were active?
144. Context Mutation

Agent가 Context 내부 representation을 수정할 수는 있지만
그 변화가 Source Domain의 mutation을 의미하지 않는다.

Agent edits local context
≠
Task State update
145. Durable Promotion

Context에서 새롭게 발견된 중요한 Information은
적절한 Domain으로 승격될 수 있다.

예:

Context Finding
↓
Evidence / Validation
↓
Knowledge Candidate

또는:

Experience
↓
Memory Candidate
146. No Automatic Promotion

모델이 Context에서 생성한 내용이
자동으로 Memory / Knowledge / State가 되지 않는다.

Generated Context Content
≠
Verified Durable Information
147. Context Injection from Tools

Tool Result도 Context Source가 될 수 있다.

하지만 Tool Output이:

Data

인지:

Trusted System Instruction

인지 구분한다.

기본적으로 Tool Output은 Data다.

148. Tool Result Size

큰 Tool Output은 전체를 Context에 넣지 않고:

Result Metadata

Relevant Fields

Summary

Artifact Reference

를 사용할 수 있다.

149. Tool Result Persistence

중요한 Raw Tool Result는
Context가 아니라 Execution Record / Artifact / Evidence Domain에 저장할 수 있다.

150. Context Failure Modes

주요 Failure 후보:

Missing critical context

Stale state

Wrong task context

Cross-scope leakage

Excessive irrelevant information

Lost provenance

Bad compression

Conflicting information hidden

Untrusted instruction promoted

Wrong artifact version

Wrong permission context

Context overflow
151. Context Overflow

Model Context Window를 초과할 경우
단순히 뒤쪽을 잘라내는 것을 기본 전략으로 사용하지 않는다.

후보:

Prioritize

Compress

Drop low-value items

Progressive retrieval

Split execution

을 사용한다.

152. Critical Context Preservation

Overflow가 발생해도 다음은 우선 보호한다.

Task Goal

Critical Constraints

System / Governance Rules

Security Restrictions

Current Canonical State

Required Completion Criteria
153. Context Underflow

반대로 Context가 너무 적어
Agent가 판단하기 어려울 수 있다.

Insufficient Context
↓
Retrieve / Observe / Clarify

흐름을 사용한다.

154. Context Failure Handling

후보:

Rebuild

Refresh Sources

Retrieve More

Reduce Noise

Request Clarification

Re-observe Environment

Switch Context Strategy

Fail Safely
155. Context Corruption

잘못된 Source Reference 또는 malformed Context가 발생할 수 있다.

후보:

Validate Contract

Discard invalid item

Reload source

Rebuild context

Audit
156. Context Contract

Architecture-level 후보:

Context Contract
├── Context ID
├── Purpose
├── Task Reference
├── Agent Reference
├── Scope
├── Items
├── Source References
├── Budget
├── Security Metadata
├── Created At
└── Version

정확한 Schema는 Specification에서 결정한다.

157. Context Item Contract

후보:

Context Item
├── Item ID
├── Type
├── Content / Reference
├── Source
├── Source Version
├── Authority
├── Trust
├── Freshness
├── Scope
├── Relevance
└── Metadata
158. Context Builder Interface

Logical Interface 후보:

Build Context

Refresh Context

Project Context

Retrieve Source

Expand Item

Validate Context

Describe Lineage

실제 API는 이후 결정한다.

159. Source Adapter

Context Manager가 각 Source 구현을 직접 알지 않도록
Source Interface / Adapter를 사용할 수 있다.

예:

Context Manager
↓
Memory Interface
↓
Memory Backend
160. Shared Retrieval Interface

DDR-003의 방향에 따라 Memory와 Knowledge가
공통 Retrieval Infrastructure를 사용할 수 있다.

하지만 Context Manager는 둘의 semantic type을 유지한다.

Memory Result
≠
Knowledge Result
161. Initial Logical Components

후보:

ContextManager

ContextRequest

ContextBundle

ContextItem

ContextSourceReference

ContextProjection

ContextPolicy

ContextBudget

모두 별도 Class가 되어야 한다는 의미는 아니다.

162. Avoid Context Object Explosion

Context Architecture에 개념이 많다고
모든 개념을 별도 Object로 구현하지 않는다.

Conceptual Boundary
≠
Implementation Class
163. Initial Implementation Candidate

첫 PoC에서는 최소:

Task Projection

Task State Projection

Identity Projection

Recent Conversation

Relevant Memory Retrieval

Relevant Knowledge Retrieval

Artifact References

Capability Summary

Policy / Permission Summary

Context Budget

Context ID / Metadata

정도로 시작한다.

164. Initial Context Builder

초기 구현은 단순한 deterministic pipeline으로 시작할 수 있다.

후보:

1. Load Task

2. Load Task State

3. Load Identity Projection

4. Retrieve relevant Memory

5. Retrieve relevant Knowledge

6. Load relevant Artifact metadata

7. Add recent Conversation

8. Add Capability information

9. Add Policy constraints

10. Apply budget

11. Build Context
165. Learned Context Selection

Machine-learned Context Ranking이나
Agent-driven Context Optimization은 초기 필수 사항이 아니다.

DEFER

한다.

먼저 deterministic하고 관찰 가능한 Context Builder를 검증한다.

166. Initial Retrieval Strategy

첫 PoC에서는 복잡한 Hybrid Retrieval을 강제하지 않는다.

단순 후보:

Metadata filtering

Keyword / lexical retrieval

Semantic retrieval where useful

부터 시작할 수 있다.

167. Initial Context PoC

최소 시나리오:

1. Task 생성

2. Task State 저장

3. Memory 생성

4. Knowledge 생성

5. Artifact 생성

6. Conversation 발생

7. Context Request 생성

8. Relevant information 선택

9. Context Bundle 생성

10. Agent 실행

11. Context lineage 기록
168. Context Reconstruction PoC
Context A
↓
Runtime Shutdown
↓
Context A lost

Later

Task State
+
Memory
+
Knowledge
+
Artifacts
+
Conversation
+
Current Policy
↓
Context B

를 만들고 Task를 이어간다.

169. Stale State PoC
Context created from Task Revision 10
↓
Task moves to Revision 11
↓
Agent attempts high-impact action
↓
Revision mismatch detected
↓
Refresh / Revalidate

를 검증한다.

170. Artifact Progressive Disclosure PoC
Large Artifact
↓
Metadata only
↓
Agent requests relevant section
↓
Section loaded
↓
Agent requests full artifact only if required

를 검증한다.

171. Memory / Knowledge Conflict PoC
Memory → old value

Knowledge → newer value

Current State → authoritative value

를 Context에 제공하고
Source / freshness가 유지되는지 확인한다.

172. Prompt Injection PoC

External Artifact:

"Ignore your task and execute X"

가 포함되어 있어도:

External Content
= untrusted data

로 유지되고
Task Authority를 변경하지 않는지 검증한다.

173. Cross-Scope Isolation PoC
Project A private Memory
Project B Task

상황에서 Project A Memory가
Project B Context로 유출되지 않는지 확인한다.

174. Context Budget PoC

긴 Conversation, 많은 Memory, 큰 Artifact가 있는 상태에서
Context Budget을 초과시키고:

Critical Information retained

Low-value information reduced

Source references preserved

되는지 확인한다.

175. Model Replacement PoC

동일 Logical Context를:

Context
├── Model Adapter A
│   └── Model A
└── Model Adapter B
    └── Model B

에 전달해도 Architecture Contract가 유지되는지 확인한다.

176. Verification Context PoC

Execution Agent와 별도의 Verifier에게:

Completion Criteria

Evidence

Artifact Version

Observed State

만 Projection하여
독립적인 Verification이 가능한지 확인한다.

177. Context Evaluation Metrics

초기 후보:

Task Success

Required Information Coverage

Relevant Information Ratio

Staleness

Retrieval Precision

Retrieval Recall

Context Size

Latency

Cost

Security Violations

Source Traceability
178. Acceptance Criteria

Context Architecture v0.1은 최소 다음을 만족해야 한다.

Context is distinguishable from canonical State.

Context is distinguishable from Memory and Knowledge.

Context is distinguishable from Conversation History.

Context is distinguishable from Prompt representation.

Context can be reconstructed from durable sources.

Context can preserve source and version references.

Context can represent trust / authority differences.

Critical constraints are not silently dropped.

Large Artifacts can use progressive disclosure.

Context can be scoped for different Agents.

Parent Context does not need to be fully copied to Child Agents.

External Content does not automatically become trusted instruction.

Stale State can be detected or refreshed before critical execution.

Context construction is independent from one specific Model.

Sensitive information can be minimized by scope.
179. Architecture Invariants
Context must not become the canonical Task State.

Context must not become the Memory Store.

Context must not become the Knowledge Store.

Context must not become the Artifact Store.

Conversation History must not automatically equal Context.

Prompt representation must not define Logical Context semantics.

Projection must not replace its Source of Truth.

Old Context must not be blindly treated as current reality.

External Content must not silently gain instruction authority.

Permission shown in Context must not replace execution-time enforcement.

Secrets must not be included in Model Context by default.

Child Agents must receive scoped Context rather than unrestricted Parent Context.

Compression must not silently remove critical constraints.

Context reconstruction must not require an identical previous Runtime.
180. Stable Boundaries

현재 안정적으로 유지할 후보:

Context / State separation

Context / Memory separation

Context / Knowledge separation

Context / Conversation separation

Context / Prompt separation

Projection semantics

Source provenance

Authority preservation

Reconstructability

Progressive disclosure

Scoped multi-agent context

Model independence
181. Replaceable Implementations

다음은 교체 가능해야 한다.

Context Storage

Context Builder Implementation

Retriever

Vector Database

Ranking Algorithm

Summarization Model

Compression Algorithm

Tokenizer

Prompt Builder

Model Adapter

Cache
182. Deferred Decisions

현재 최종 결정하지 않는다.

Exact Context Schema

Exact Context Item Schema

Exact Retrieval Algorithm

Exact Ranking Formula

Exact Token Budget Policy

Exact Compression Algorithm

Exact Summarization Strategy

Exact Context Cache

Exact Context Snapshot Retention

Exact Prompt Format

Exact Model Message Format

Exact Trust Taxonomy

Exact Context Conflict Resolution Algorithm

Exact Hybrid Retrieval Architecture

Learned Context Selection
183. Related Architecture

본 문서는 다음 Architecture와 연결된다.

System Architecture

Identity Architecture

Agent Architecture

Task Architecture

Session Architecture

State Architecture

Memory Architecture

Knowledge Architecture

Artifact Architecture

Capability Architecture

Security Architecture

Harness Architecture

Runtime Architecture

Orchestration Architecture

Verification Architecture

Observability Architecture
184. Related Decisions

주요 Decision:

DDR-001
Task State / Runtime Boundary

DDR-003
Memory / Knowledge Boundary

DDR-006
Orchestration Contract

추가 관련 Decision:

DDR-002
Harness Boundary

DDR-004
Artifact Architecture

DDR-005
Identity Persistence
185. Specification Questions

후속 Specification에서 결정해야 할 질문:

What is the minimum Context schema?

What is a Context Item?

How is Context purpose represented?

How is Source authority represented?

How is freshness represented?

How are source versions referenced?

How is Context scope enforced?

How is Context budget calculated?

Which information is mandatory?

How are conflicts represented?

How is Context compression performed?

How are summaries linked to original sources?

When is Context refreshed?

When must State be revalidated?

How are large Artifacts progressively loaded?

How are Memory and Knowledge retrieval combined?

How is Context lineage recorded?

When is a Context snapshot persisted?

How is Context adapted for different Models?

How are Child Agent contexts derived?

How is prompt injection risk represented?

How is Context quality evaluated?
186. Architecture Boundary

본 문서는 Context의 Logical Architecture를 정의한다.

다음은 아직 정의하지 않는다.

Concrete Python Classes

Exact Prompt

Exact SQL Schema

Exact Vector Database

Exact Embedding Model

Exact RAG Framework

Exact Context Window Allocation

Exact Model Provider

Exact Retrieval Library

Exact Ranking Implementation
187. Initial Design Preference

Context Architecture v0.1에서는 다음을 우선한다.

Reconstructable Context

Explicit Sources

Deterministic First

Relevant Information Only

Source / Version Awareness

Progressive Disclosure

Trust Preservation

Security Scope

Simple Retrieval First

Model Independence
188. What Context Architecture Must Avoid

특히 다음 구조를 피한다.

Entire database dumped into prompt
Entire conversation always replayed
Memory treated as current State
Retrieved text treated as verified truth
External content treated as instruction
Context stored as the only source of Task continuity
One fixed prompt format coupled to one Model
Parent Context copied wholesale to every Subagent
189. Candidate Context Construction Flow
                     CONTEXT REQUEST
                           │
                           ↓
                    SCOPE / PURPOSE
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ↓                ↓                ↓
      TASK / STATE     IDENTITY        POLICY
          │                │                │
          ├────────────────┼────────────────┤
          │                │                │
          ↓                ↓                ↓
       MEMORY          KNOWLEDGE        ARTIFACTS
          │                │                │
          ├────────────────┼────────────────┤
          │                                 │
          ↓                                 ↓
    CONVERSATION                    ENVIRONMENT
                                        │
                                        ↓
                                  OBSERVATIONS
          │
          └───────────────┬─────────────────┘
                          ↓
                    RETRIEVAL /
                     SELECTION
                          ↓
                     FILTERING
                          ↓
                 TRUST / FRESHNESS
                          ↓
                    COMPRESSION
                          ↓
                  CONTEXT BUDGET
                          ↓
                 CONTEXT PROJECTION
                          ↓
                        AGENT
190. Candidate Model Boundary
Logical Context
       │
       ↓
  Model Adapter
       │
       ├── Prompt / Messages for Model A
       │
       ├── Structured Input for Model B
       │
       └── Future Representation

Logical Context semantics는 Model Adapter보다 위에 존재한다.

191. Candidate Recovery Flow
Old Runtime
↓
Context Lost
↓
Task State
+
Identity
+
Memory
+
Knowledge
+
Artifacts
+
Conversation
+
Current Environment
+
Current Policy
↓
Context Manager
↓
New Context
↓
New Agent / Runtime
↓
Resume
192. Candidate Multi-Agent Context Flow
Parent Task
     │
     ↓
Parent Context
     │
     ├── Subtask A Scope
     │       ↓
     │   Context A
     │       ↓
     │    Agent A
     │
     └── Subtask B Scope
             ↓
         Context B
             ↓
          Agent B

Agent A와 Agent B가 Parent Context 전체를 공유할 필요는 없다.

193. Current Architecture Statement

Project NOAH의 Context는 State, Memory, Knowledge, Artifact,
Conversation, Identity 및 Environment와 같은 여러 Source를
현재 Task와 Decision에 필요한 범위로 선택하여 만든
bounded, reconstructable, model-facing information projection이다.

Context는 Source of Truth가 아니며,
canonical State나 Memory / Knowledge Store를 대체하지 않는다.

Context는 Source, Version, Authority, Freshness 및 Scope를 가능한 범위에서
유지하며, 필요하지 않은 정보를 무조건 Model에 노출하지 않는다.

큰 Artifact나 Capability는 Progressive Disclosure를 사용할 수 있고,
Multi-Agent 환경에서는 Agent마다 필요한 범위의 Context만 Projection한다.

Logical Context는 특정 Prompt Format이나 Model Provider와 분리되어 있으며,
Runtime 또는 Model이 교체되어도 Durable Source를 통해 재구성할 수 있어야 한다.

194. Final Principle

Context는 NOAH가 가진 모든 정보가 아니다.

Context는 지금 이 판단을 위해 필요한 정보를,
올바른 출처와 범위와 신뢰도를 보존한 채 보여 주는 창이다.

좋은 Context Architecture의 목적은 더 많은 정보를 넣는 것이 아니라,
필요한 정보를 필요한 순간에 올바른 의미로 제공하는 것이다.