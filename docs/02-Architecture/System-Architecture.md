# Project NOAH System Architecture

> Project NOAH Architecture
> Document: System Architecture
> Architecture Version: 0.1
> Status: Blueprint
> Date: 2026-09-01

---

# 1. Purpose

이 문서는 Project NOAH의 전체 Logical System Architecture를 정의한다.

Research 문서가 다음 질문을 다뤘다면:

> 왜 이런 구조를 검토했는가?

Architecture Decision Record가 다음 질문을 다뤘다면:

> 무엇을 선택했는가?

본 문서는 다음 질문에 답한다.

> **현재 Project NOAH는 어떻게 구성되는가?**

---

# 2. Architecture Scope

본 문서는 NOAH의 전체 Architecture를 구성하는 주요 영역과
각 영역 사이의 책임 및 관계를 정의한다.

주요 영역:

```text
Governance
Identity
Agent
Task
Session
Orchestration
Harness
State
Context
Memory
Knowledge
Artifact
Capability
Policy
Permission
Runtime
Sandbox
Environment
Execution
Result
Evidence
Verification
Observability
Evaluation
Experience
Learning
Controlled Adaptation
3. Architecture Goals

Project NOAH의 Architecture는 다음 목표를 가진다.

Long-term Continuity
Replaceability
Modularity
Recoverability
Explainability
Security
Observability
Verifiability
User Control
Controlled Adaptation
Maintainability
4. Architecture Philosophy

NOAH의 Architecture는 특정 기술을 중심으로 설계하지 않는다.

핵심 방향:

Stable Principles
+
Explicit Contracts
+
Replaceable Implementations

현재 기술이 변경되더라도 핵심 Architecture Boundary가 유지될 수 있어야 한다.

5. Constitution

NOAH Architecture의 최상위에는 Constitution이 존재한다.

CONSTITUTION
     ↓
Architecture
     ↓
Implementation

어떠한 Architecture Decision이나 구현도 Constitution보다 높은 우선순위를 가지지 않는다.

6. Governance

Governance는 NOAH의 중요한 변경을 통제한다.

특히:

Identity Core
Policy
High-risk Adaptation
Architecture Decision
Security Boundary

등의 중요한 변경에 적용된다.

Governance는 일반적인 Runtime Execution과 구분한다.

# 7. Top-Level Architecture

현재 NOAH의 Logical Architecture는
하나의 단순한 Pipeline이 아니라 여러 Architecture Plane이 연결되는 구조다.

## Governance / Identity

```text
CONSTITUTION
     ↓
GOVERNANCE
     ↓
IDENTITY CORE
     ↓
   AGENT
Information / Cognitive Flow
TASK STATE
MEMORY
KNOWLEDGE
ARTIFACTS
CONVERSATION
ENVIRONMENT OBSERVATION
IDENTITY PROJECTION
POLICY CONTEXT
        │
        ↓
  CONTEXT MANAGER
        │
        ↓
     CONTEXT
        │
        ↓
      AGENT
Execution / Control Flow
AGENT
 ↓
CAPABILITY REQUEST
 ↓
POLICY
 ↓
PERMISSION
 ↓
APPROVAL if required
 ↓
HARNESS
 ↓
RUNTIME
 ↓
SANDBOX
 ↓
ENVIRONMENT
 ↓
EXECUTION
Result / Verification Flow
EXECUTION
 ↓
RESULT
 ↓
EVIDENCE
 ↓
VERIFICATION
 ↓
TASK STATE TRANSITION
 ↓
EVALUATION
Learning / Adaptation Flow
EVALUATION
 ↓
EXPERIENCE
 ↓
MEMORY CANDIDATE
 ↓
VALIDATION
 ↓
MEMORY
 ↓
REFLECTION / LEARNING
 ↓
IMPROVEMENT PROPOSAL
 ↓
EVALUATION / GOVERNANCE
 ↓
CONTROLLED ADAPTATION

이 Diagram들은 Logical Architecture를 표현한다.

각 Component가 반드시 독립적인 Process, Package,
Container 또는 Service라는 의미는 아니다.

8. Logical vs Physical Architecture

NOAH는 Logical Architecture와 Physical Architecture를 분리한다.

Logical Component
≠
Package
≠
Process
≠
Container
≠
Service

현재 Architecture Version 0.1에서는 Logical Boundary를 우선 정의한다.

9. Initial Physical Direction

초기 구현은 다음 방향을 우선한다.

Modular Monolith

즉:

NOAH Process
├── Core
├── Runtime
├── Information
├── Capability
├── Security
├── Artifacts
├── Orchestration
└── Evaluation

정도의 Module Boundary를 유지하면서 하나의 시스템으로 시작한다.

10. Core Architecture Principles

NOAH의 핵심 Architecture 원칙:

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

Learning ≠ Automatic Core Mutation
11. Stable vs Replaceable
Stable

가능한 한 장기적으로 유지할 Architecture Boundary:

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
Contract
Replaceable

교체 가능해야 하는 구현:

LLM
Model Provider
Agent Framework
Runtime Framework
Orchestrator Implementation
Memory Backend
Knowledge Backend
Retrieval Engine
Artifact Storage
Sandbox
Telemetry Backend
Protocol
Transport
12. Identity Architecture

Identity는 NOAH의 지속적인 존재적 연속성을 표현한다.

Identity
≠
Model
≠
Runtime
≠
Session
≠
Memory

Identity는 별도의 Protected Identity Contract를 가진다.

13. Identity Core

Identity Core 후보:

Identity Core
├── ID
├── Origin
├── Core Values
├── Fundamental Commitments
├── Root Role
├── Continuity
└── Version

Identity Core는 일반 Learning이나 Memory Update로 직접 수정되지 않는다.

14. Identity Persistence

Identity는 Session과 Runtime보다 오래 지속된다.

Identity
├── Session A
├── Session B
└── Session C

Runtime이 교체되어도 같은 Identity를 사용할 수 있어야 한다.

15. Identity Store

Logical Identity Store:

Identity Store
├── Identity Core
├── Version
├── Provenance
├── Integrity
└── Change History

Physical Storage는 Architecture에서 고정하지 않는다.

16. Identity Projection

Agent가 실행될 때 전체 Identity Store를 Context에 넣지 않는다.

Identity Store
↓
Identity Projection
↓
Context
↓
Agent

현재 Task와 Role에 필요한 Identity 정보만 Projection한다.

17. Identity Evolution

Identity는 완전히 변화하지 않는 Object가 아니다.

원칙:

Protected Core
+
Governed Evolution

하지만:

Automatic Uncontrolled Mutation

은 허용하지 않는다.

18. Personality

Personality는 Identity Core보다 더 적응적인 Layer다.

Identity Core
→ Highly Stable

Personality
→ Adaptive

Behavior
→ Context-dependent

Self Model
→ Dynamic
19. Self Model

Self Model은 NOAH가 현재 자신의 상태를 표현하는 모델이다.

후보:

Capabilities
Limitations
Current Role
Current Goal
Confidence
Available Resources
Current State

Self Model은 실제 System State와 일치하는지 평가될 수 있어야 한다.

20. Agent

Agent는 NOAH의 Cognitive Decision Entity다.

주요 책임:

Understand
Reason
Plan
Decide
Select Capability
Interpret Results
21. Agent Does Not Own Infrastructure

Agent는 다음 구현을 직접 소유하지 않는다.

Database
Credential Store
Task Store
Artifact Storage
Sandbox
Telemetry Backend
Memory Backend

Agent는 Interface / Contract를 통해 이들을 사용한다.

22. Model Independence

Agent와 Model을 동일한 것으로 취급하지 않는다.

Agent
↓
Model Interface
↓
Model

Model은 교체 가능한 Cognitive Engine이다.

23. Task

Task는 사용자의 목표를 지속적으로 표현한다.

후보:

Task
├── ID
├── Goal
├── Requirements
├── Constraints
├── Priority
├── Budget
├── Completion Criteria
└── Verification Requirements
24. Task Lifetime

Task는 Session보다 오래 지속될 수 있다.

Task Lifetime
≥
Session Lifetime

예:

Task
├── Session A
├── Session B
└── Session C
25. Task State

Task State는 Task의 canonical progress를 표현한다.

Task State
├── Status
├── Progress
├── Current Plan
├── Completed Work
├── Pending Work
├── Blockers
├── Artifact References
└── Verification Status
26. Canonical Task State

Task의 현재 진행 상태에 대한 Source of Truth:

Task State

다음은 Task State를 대신하지 않는다.

Context
Conversation History
Memory
Agent Reasoning
Runtime Memory
27. Session

Session은 특정 Interaction / Execution 관계다.

후보:

Session
├── ID
├── Task Reference
├── Agent Reference
├── Runtime Reference
└── Conversation / Interaction State

Session 종료가 Task 종료를 의미하지 않는다.

28. State Architecture

NOAH는 State를 하나의 모호한 개념으로 취급하지 않는다.

주요 State 후보:

Task State
Execution State
Environment State
Workspace State
Orchestration State

모든 State가 반드시 별도 Store를 필요로 하는 것은 아니다.

29. Execution State

Runtime의 현재 실행 상태:

Execution State
├── Current Step
├── Current Capability
├── Retry State
├── Approval State
├── Runtime Instance
├── Checkpoint
└── Error State

Execution State는 Task State와 분리한다.

30. Context

Context는 현재 Model 실행을 위해 구성된 Information Projection이다.

Context
≠
Source of Truth
31. Context Sources

Context 후보 입력:

Identity Projection
Task State
Memory
Knowledge
Artifacts
Conversation
Environment Observation
Capability Information
Policy
32. Context Projection
State
Memory
Knowledge
Artifacts
Conversation
Environment
Policy
      ↓
Context Manager
      ↓
Relevant Projection
      ↓
Agent / Model

Full Information Store를 무조건 Context에 넣지 않는다.

33. Context Reconstruction

Runtime이 종료되더라도 Context를 다시 구성할 수 있어야 한다.

Task State
+
Memory
+
Knowledge
+
Artifacts
+
Relevant History
+
Environment Observation
+
Policy
↓
New Context

이 구조를 통해 Runtime 교체가 가능해진다.

34. Memory

Memory는 과거의 경험과 지속적인 사용자 / 프로젝트 맥락을 관리한다.

후보:

Episodic Memory
Semanticized Experience
Project Memory
User-related Memory
Lessons
35. Memory Lifecycle
Experience
↓
Candidate
↓
Validation
↓
Memory
↓
Retrieval
↓
Use
↓
Revision / Archive / Forget

모든 Experience를 자동으로 Memory로 저장하지 않는다.

36. Memory Utility

Memory의 목표는 많은 정보를 저장하는 것이 아니다.

핵심 질문:

미래의 판단과 행동을 개선하는가?

Memory Quality는 future utility를 기준으로 평가한다.

37. Knowledge

Knowledge는 사실, 정보, 문서 및 구조화된 지식을 관리한다.

후보:

External Knowledge
Project Knowledge
Research
Documentation
Structured Facts
Verified Information
38. Memory vs Knowledge
Memory
= Experience / Continuity

Knowledge
= Facts / Information

두 의미를 구분한다.

39. Shared Information Infrastructure

Memory와 Knowledge는 공통 Infrastructure를 사용할 수 있다.

Memory ─────┐
            ├── Information / Retrieval Interface
Knowledge ──┘

하지만:

Shared Interface
≠
Shared Semantics

이다.

40. Information Metadata

Memory와 Knowledge 모두 다음 Metadata를 가질 수 있다.

Source
Provenance
Timestamp
Confidence
Scope
Ownership
Trust
Version
Temporal Validity
41. Artifact

Artifact는 지속적인 semantic work object다.

Artifact
≠
File

File은 Artifact의 Physical Representation 중 하나다.

42. Artifact Types

후보:

Document
Source Code
Dataset
Image
Audio
Video
Configuration
Build Result
Test Result
Evaluation Result
Evidence Artifact
Model / Binary
Generated Output
43. Artifact Identity

Artifact는 Stable Identity를 가질 수 있다.

Artifact
├── ID
├── Type
├── Version
├── Owner
├── Scope
├── Provenance
└── Integrity

Path 변경이 Artifact Identity 변경을 의미하지 않는다.

44. Artifact and Task State
Task State
↓
Artifact Reference
↓
Artifact

Task State 내부에 Artifact 전체를 저장하지 않는다.

45. Artifact and Memory
Artifact
= 실제 결과물

Memory
= Artifact와 관련된 경험

Artifact 생성 이유나 중요한 변화는 Memory가 될 수 있다.

46. Artifact and Knowledge

Artifact는 Knowledge Source가 될 수 있다.

Artifact
↓
Extraction
↓
Validation
↓
Knowledge

Artifact 자체를 자동으로 Knowledge라고 간주하지 않는다.

47. Artifact and Evidence
Artifact
→ Evidence가 될 수 있음

Evidence
→ 반드시 Artifact는 아님
48. Artifact Storage

Physical Storage 후보:

Filesystem
Git
Database
Object Storage
External Repository

현재 Architecture에서는 특정 Storage를 고정하지 않는다.

49. Artifact Persistence

Durable Artifact는 Runtime보다 오래 지속될 수 있다.

Runtime Failure
↓
Artifact persists
↓
Task resumes
50. Capability

Capability는 NOAH가 수행할 수 있는 행동 또는 절차적 능력을 의미한다.

후보:

Capability
├── Tool
├── Skill
├── Workflow
└── Agent Delegation

Protocol은 Capability와 구분한다.

51. Tool

Tool은 비교적 Atomic한 Action이다.

예:

Read File
Write File
Search
Execute Command
Call API
Send Message
52. Skill

Skill은 반복 가능한 절차적 Capability다.

Skill
=
Reusable Procedure

Skill은 하나 이상의 Tool을 조합할 수 있다.

53. Workflow

Workflow는 여러 Step과 Capability를 연결하는 실행 구조다.

Step A
↓
Step B
↓
Step C

n8n 등의 Workflow 구현은 Architecture Contract와 분리한다.

54. Capability Contract

Capability는 최소한 다음 정보를 표현할 수 있어야 한다.

ID
Version
Description
Input
Output
Preconditions
Permissions
Side Effects
Cost
Timeout
Retry
Verification
Provenance
55. Capability Registry

향후 Capability가 많아질 경우 Registry를 사용할 수 있다.

Capability Registry

그러나 초기부터 별도 Registry Service를 만들지는 않는다.

56. Capability Discovery

모든 Capability를 항상 Context에 넣지 않는다.

후보:

Task
↓
Relevant Capability Discovery
↓
Capability Projection
↓
Agent
57. Policy

Policy는 어떤 행동이 허용 가능한지를 판단하는 규칙이다.

Policy
≠
Permission
58. Permission

Permission은 특정 Identity / Role / Scope가
어떤 Capability를 사용할 수 있는지 표현한다.

후보:

Allow
Ask
Deny
59. Approval

Approval은 현재 특정 Execution에 대한 승인이다.

Capability
≠
Permission
≠
Approval
60. Security Execution Flow

기본 흐름:

Capability Request
↓
Risk Analysis
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
61. Least Privilege

기본 원칙:

Minimum Capability
+
Minimum Scope
+
Minimum Duration

을 사용한다.

62. Child Permission

Subagent의 기본 권한:

Child Permission
⊆
Parent Permission

추가 Permission은 별도의 승인 경로를 요구한다.

63. Credentials

Agent가 Credential 자체를 직접 보유하는 구조를 피한다.

후보:

Agent
↓
Capability Request
↓
Credential Broker
↓
External Service
64. Harness

Harness는 Agent와 Infrastructure 사이의 Stable Execution Boundary다.

Agent
↓
Harness
↓
Infrastructure
65. Harness Responsibilities

Harness는 다음 영역에 대한 접근과 실행을 조정한다.

Context Access
State Access
Capability Access
Policy Integration
Runtime Access
Memory / Knowledge Access
Recovery Integration
Observability Integration
Verification Hooks
66. Harness Ownership Rule

중요:

Harness coordinates / exposes / mediates
≠
Harness owns all systems

예:

Harness
↓
Memory Interface
↓
Memory System
67. Harness vs Runtime
Harness
= Stable Execution Boundary

Runtime
= Execution Lifecycle

Runtime 구현은 교체 가능하다.

68. Harness vs Orchestrator
Orchestrator
= What should happen?

Harness
= How selected execution happens safely and persistently
69. Runtime

Runtime은 실제 Execution Lifecycle을 담당한다.

후보:

Start
Run
Pause
Resume
Cancel
Retry
Checkpoint
Recover
Observe
70. Runtime Replacement
Runtime A
↓
Runtime B

로 변경되어도:

Identity
Task
Task State
Memory
Knowledge
Artifacts

는 유지될 수 있어야 한다.

71. Checkpoint

Checkpoint는 Runtime Recovery를 위해 필요한 Execution Information이다.

후보:

Task State Reference
Execution Metadata
Artifact References
Workspace Reference
Pending Operations
Side-effect Records
72. Recovery

기본 Recovery Flow:

Runtime Failure
↓
Persisted Task State
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
73. Side Effects

External Side Effect를 가진 Capability는 별도로 추적한다.

예:

Send Email
Delete File
Publish Artifact
External API Mutation
74. Idempotency

Capability는 가능하면 다음 정보를 표현한다.

Idempotent
Non-idempotent
Unknown

Unknown 또는 Non-idempotent 작업은 Retry를 보수적으로 수행한다.

75. Sandbox

Sandbox는 실행을 Environment로부터 격리하거나 제한하는 Security Boundary다.

후보 제한 영역:

Filesystem
Network
Process
Resources
Environment Variables
Credentials

구체적인 Sandbox 구현은 아직 결정하지 않는다.

76. Environment

Environment는 NOAH 외부의 실제 세계 상태다.

예:

Filesystem
Operating System
External APIs
Network
Databases
User Applications
Repositories

Environment Observation과 Internal State를 동일하게 취급하지 않는다.

77. Execution

Execution은 Capability가 실제 Environment에 영향을 주는 과정이다.

Decision
↓
Capability Request
↓
Permission
↓
Runtime
↓
Execution
78. Result

Result는 Agent 또는 Capability가 보고하는 실행 결과다.

후보:

Status
Summary
Findings
Artifacts
Errors
Uncertainty
Recommended Next Step
79. Evidence

Evidence는 Result를 뒷받침하는 실제 근거다.

후보:

Tool Output
Artifact
Test
Observation
Environment State
External Source
80. Result vs Evidence
Result
= What is reported

Evidence
= What supports the report

두 개념을 분리한다.

81. Verification

Verification은 요구된 상태가 실제로 충족되었는지 확인한다.

Expected State
vs
Observed State
82. Verification Contract

후보:

Preconditions
Postconditions
Invariants
Evidence
Verification Result
83. Evidence-Based Completion

Agent의 self-report만으로 Task를 완료 처리하지 않는다.

기본 흐름:

Agent Result
↓
Evidence
↓
Verification
↓
Completion Decision
↓
Task State
84. Evaluation

Evaluation은 Execution과 Result의 품질을 평가한다.

후보:

Correctness
Safety
Reliability
Process Quality
Cost
Latency
Recovery
Memory Utility
Long-term Utility
85. Verification vs Evaluation
Verification
= Did it actually happen?

Evaluation
= How good was it?

둘을 분리한다.

86. Observability

NOAH는 실행 과정을 추적할 수 있어야 한다.

후보 식별자:

Trace ID
Task ID
Session ID
Agent ID
Execution ID
Capability Call ID
Artifact ID
Verification ID
87. Trace

Trace는 다음 영역을 연결할 수 있다.

Task
Agent
Context
Capability
Permission
Runtime
Execution
Artifact
Verification
Evaluation
Recovery
88. Audit

Security 또는 중요 Decision에 대해서는 Audit Trail을 유지한다.

후보:

Permission
Approval
Delegation
Execution
Identity Change
Artifact Publish/Delete
Verification
Recovery
89. Failure Attribution

Failure를 단순히 "Agent Failure"로 처리하지 않는다.

후보:

Model
Context
Memory
Knowledge
Planning
Capability
Tool
Permission
Runtime
Environment
Verification
Human Input
90. Experience

Experience는 실제 Task Execution에서 발생한 사건과 결과다.

Execution
↓
Outcome
↓
Experience

Experience 자체가 자동으로 Memory는 아니다.

91. Learning

Learning은 Experience와 Evaluation에서 개선 가능성을 추출하는 과정이다.

Experience
↓
Evaluation
↓
Reflection
↓
Lesson
↓
Improvement Proposal
92. Learning Loop
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
Reflection
↓
Learning
↓
Improvement Proposal
93. Controlled Adaptation

Learning 결과는 위험도에 따라 적용된다.

후보:

LOW
→ Skills / Procedures

MEDIUM
→ Routing / Preferences / Personality

HIGH
→ Policy / Identity Core / Governance
94. No Automatic Core Mutation
Learning
≠
Automatic Identity Core Mutation

High-risk 변경은 별도의 Governance를 요구한다.

95. Orchestration

Orchestration은 복잡한 Task의 Planning, Delegation 및 Coordination을 담당한다.

주요 책임:

Task Decomposition
Planning
Agent Selection
Delegation
Scheduling
Parallelism
Aggregation
Replanning
Recovery Strategy
Budget Allocation
96. Single-Agent Default

Multi-Agent를 기본값으로 사용하지 않는다.

기본:

Task
↓
Single Agent
↓
Harness
↓
Execution

필요한 경우에만:

Task
↓
Orchestrator
↓
Multiple Agents

로 확장한다.

97. Multi-Agent Criteria

Multi-Agent 사용 후보:

Specialization
Parallelism
Context Isolation
Independent Verification
Large Task Decomposition
Failure Isolation

Coordination Cost가 이점보다 클 경우 Single Agent를 유지한다.

98. Delegation

Delegation:

Parent Agent
↓
Scoped Task
↓
Child Agent
↓
Result
↓
Parent Agent
99. Delegation Contract

후보:

Parent
Child
Goal
Scope
Context Projection
Permissions
Budget
Constraints
Expected Output
Verification
100. Agent-as-Tool

Agent-as-Tool:

Parent
↓
Child
↓
Result
↓
Parent

Parent가 Execution Control을 유지한다.

101. Handoff

Handoff는 Control 자체가 다른 Agent로 이동하는 구조다.

Agent A
↓
Handoff
↓
Agent B

Delegation과 구분한다.

102. Orchestration Context Isolation

Child Agent에 Parent Context 전체를 전달하지 않는다.

Parent Context
↓
Relevant Projection
↓
Child Context
103. Orchestration Budget

Budget 후보:

Tokens
Time
Tool Calls
Compute
Storage
Network
Agent Count

기본:

Child Budget
≤
Parent Remaining Budget
104. Contract Architecture

NOAH의 주요 Component Interaction은 Contract 기반으로 정의한다.

Contract
≠
Protocol
105. Contract Meaning

Contract는 단순 Schema보다 넓다.

Contract
=
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
106. Contract Stack

Logical Contract 후보:

Task Contract
Plan Contract
Delegation Contract
Agent Contract
Context Contract
Capability Contract
Execution Contract
Result Contract
Evidence Contract
Verification Contract
Budget Contract
Recovery Contract

모든 Contract가 독립적인 코드 Object가 될 필요는 없다.

107. Protocol

Protocol은 Contract를 전달하는 방식이다.

Contract
↓
Protocol Adapter
↓
Transport
108. Protocol Candidates

향후:

Internal Calls
HTTP
MCP
A2A
Message Queue
Future Protocol

등을 사용할 수 있다.

현재 특정 Protocol을 Architecture에 고정하지 않는다.

109. Contract Versioning

Contract가 변경되면 Versioning을 지원할 수 있어야 한다.

후보:

Contract v1
↓
Contract v2

필요한 경우:

Adapter
Negotiation
Migration
Fallback

을 사용할 수 있다.

110. End-to-End Task Flow

일반 Task의 Candidate Flow:

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
Reasoning / Decision
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
↓
Experience
111. Recovery Flow
Execution
↓
Failure
↓
Failure Classification
↓
Task State / Checkpoint / Artifacts
↓
Recovery Strategy
↓
New Runtime or Retry
↓
Context Reconstruction
↓
Resume
112. Information Flow
State
Memory
Knowledge
Artifacts
Conversation
Environment
Identity
Policy
      ↓
Information Selection
      ↓
Context Projection
      ↓
Agent
113. Learning Flow
Task
↓
Execution
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
114. Identity Continuity Flow
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
Task / Session

Experience는:

Personality
Preferences
Relationship
Self Model

에 영향을 줄 수 있지만,
Protected Identity Core를 직접 수정하지 않는다.

115. Security Flow
Input
↓
Trust / Instruction Analysis
↓
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
Credential Broker
↓
Sandbox
↓
Execution
↓
Verification
↓
Audit
116. Primary Persistence Domains

장기적으로 지속되어야 할 주요 정보:

Identity
Task State
Memory
Knowledge
Artifacts
Important Audit / Evidence

Runtime Context 전체를 반드시 영속화할 필요는 없다.

117. Ephemeral Domains

기본적으로 재구성 가능하거나 일시적인 영역:

Current Model Context
Runtime Internal State
Temporary Workspace Data
Temporary Agent Instances
Intermediate Reasoning State

필요한 일부 정보만 Checkpoint 또는 Evidence 형태로 보존한다.

118. Architecture Dependency Rule

Component는 가능한 한 직접 구현에 의존하지 않는다.

예:

Agent
↓
Memory Interface
↓
Memory Implementation

이지:

Agent
↓
Specific Vector Database

로 연결하지 않는다.

119. Circular Dependency Rule

Feedback Loop는 허용하지만 코드-level Circular Dependency는 피한다.

예:

Memory
→ Context
→ Agent
→ Experience
→ Memory

는 Architecture Feedback Loop다.

그러나 Module 간 직접적인 순환 import를 의미하지 않는다.

120. Architecture Modules Candidate

초기 Logical Module 후보:

NOAH
│
├── Core
│   ├── Identity
│   ├── Agent
│   └── Task
│
├── Runtime
│   ├── Session
│   ├── State
│   ├── Context
│   ├── Harness
│   └── Execution Runtime
│
├── Information
│   ├── Memory
│   ├── Knowledge
│   └── Retrieval
│
├── Artifacts
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
│   ├── Verification
│   ├── Observability
│   └── Evaluation
│
└── Governance

이 구조는 실제 Source Folder를 확정하는 것이 아니다.

121. External Integrations

NOAH는 External System과 Adapter를 통해 연결한다.

후보:

LLM Provider
Local Model
Database
Filesystem
Git
External APIs
Messaging
Browser
Workflow Engine
MCP
A2A
122. Adapter Principle
NOAH Core Contract
↓
Adapter
↓
External Technology

External Technology가 Core Architecture에 직접 침투하지 않도록 한다.

123. Storage Architecture

현재 Storage는 Logical Interface만 정의한다.

후보 Persistence:

Task Store
Identity Store
Memory Store
Knowledge Store
Artifact Store
Audit Store

실제로 모두 별도 Database를 가져야 하는 것은 아니다.

124. Initial Storage Direction

초기 PoC에서는 단순성을 우선한다.

후보:

PostgreSQL
+
Filesystem / Git where appropriate

하지만 이 선택이 장기적인 Architecture Contract가 되지는 않는다.

125. Event Architecture

Event는 다음에 사용할 수 있다.

Observability
Audit
Recovery
State Transition
Integration

후보 Events:

TaskCreated
ExecutionStarted
CapabilityCalled
ArtifactCreated
VerificationCompleted
TaskCompleted
ExecutionFailed
RecoveryStarted
126. Event Log vs Event Sourcing
Event Log
≠
Event Sourcing

Full Event Sourcing은 현재 Architecture v0.1에서 요구하지 않는다.

127. Registry Candidates

확장 시 다음 Registry를 고려할 수 있다.

Capability Registry
Artifact Registry
Agent Registry
Contract Registry

초기 구현에서는 필요할 때만 도입한다.

128. Progressive Disclosure

NOAH는 모든 정보를 한 번에 Model Context에 제공하지 않는다.

예:

Artifact Metadata
↓
Relevant Section
↓
Full Artifact

또는:

Capability Summary
↓
Relevant Capability
↓
Full Schema

를 사용할 수 있다.

129. Trust and Provenance

중요 정보에는 가능한 경우:

Source
Authority
Provenance
Timestamp
Version
Confidence
Verification

를 유지한다.

130. User Control

NOAH의 Architecture는 User가 최종적인 통제권을 유지하도록 설계한다.

특히:

Sensitive Action
High-impact Action
Identity Core Change
External Publishing
Destructive Operation

에는 적절한 Permission / Approval / Governance를 적용한다.

131. Explainability

중요한 Decision은 가능한 경우 다음을 설명할 수 있어야 한다.

What was decided?
Why?
What information was used?
What capability was executed?
What evidence supports the result?
What uncertainty remains?
132. Failure Handling

Failure 후보 처리:

Retry
Fallback
Reassign
Replan
Resume
Escalate
Abort

무조건 Retry하지 않는다.

133. Failure Contract

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
134. Timeout

Timeout 후보:

Connection Timeout
Capability Timeout
Agent Timeout
Runtime Timeout
Task Deadline

각 Lifecycle에 따라 다르게 관리할 수 있다.

135. Cancellation
User
↓
Task Cancellation
↓
Orchestrator / Agent
↓
Runtime
↓
Capability

가능한 범위에서 Cancellation을 전파한다.

136. Pause / Resume

Long-running Task:

Run
↓
Pause
↓
Checkpoint
↓
Resume

을 지원할 수 있어야 한다.

137. Concurrency

여러 Agent 또는 Execution이 동일 State / Artifact를 수정하는 경우:

Version
Revision
Conflict Detection
Lock / Optimistic Concurrency
Merge

등을 사용할 수 있다.

정확한 전략은 PoC에서 검증한다.

138. Multi-Agent Shared State

Shared State를 기본값으로 만들지 않는다.

기본:

Scoped Context
Scoped State Access
Scoped Memory Access

필요한 정보만 공유한다.

139. Multi-Agent Memory

Memory도 기본적으로 범위를 가진다.

Private Agent Memory
Task Memory
Project Memory
Shared Memory

Shared Memory는 명시적인 Scope와 Policy를 사용한다.

140. Evaluation Dimensions

NOAH Architecture 평가 후보:

Task Success
Correctness
Safety
Reliability
Recoverability
Observability
Maintainability
Replaceability
Context Quality
Memory Utility
Knowledge Quality
Artifact Integrity
Identity Continuity
Cost
Latency
141. Architecture Evaluation

Architecture 자체도 평가 대상이다.

질문:

Are boundaries useful?

Can components be replaced?

Can failures recover?

Can actions be verified?

Can decisions be explained?

Is complexity justified?

Does the architecture improve long-term capability?
142. Architecture Evolution

NOAH Architecture는 고정된 최종 설계가 아니다.

Architecture
↓
PoC
↓
Evidence
↓
Evaluation
↓
Decision Review
↓
DDR Amendment / New DDR
↓
Architecture Revision

의 과정을 따른다.

143. Versioning

Architecture 자체도 Version을 가진다.

현재:

System Architecture v0.1

향후 중요한 Decision 변화 시:

v0.2
v0.3
...

로 발전한다.

144. Decision Traceability

Architecture의 중요한 Boundary는 DDR로 추적할 수 있어야 한다.

현재:

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
145. Architecture Decision Relationship
DDR-005 Identity
        ↓
      Agent
        ↓
DDR-006 Orchestration
        ↓
DDR-002 Harness
        ↓
DDR-001 Runtime

정보 측면:

DDR-003 Memory / Knowledge
        │
DDR-004 Artifact
        │
      Context
        │
      Agent
146. Implementation Independence

본 문서에서 정의하는 Architecture는 다음을 강제하지 않는다.

Specific Model
Specific Agent Framework
Specific Runtime
Specific Vector DB
Specific Graph DB
Specific Workflow Engine
Specific Protocol
Specific Sandbox
Specific Deployment Platform
147. Deferred Decisions

현재 의도적으로 열어둔 영역:

Concrete Package Structure
Concrete APIs
Concrete Schemas
Database Schema
Memory Backend
Knowledge Backend
Artifact Backend
Identity Backend
Runtime Framework
Agent Framework
Sandbox Technology
Event Sourcing
Microservices
Message Bus
MCP / A2A Adoption
148. First Implementation Boundary

첫 구현에서는 Architecture 전체를 완벽하게 구현하지 않는다.

최소:

Task
Task State
Agent
Context
Capability
Permission
Runtime
Artifact
Verification
Evaluation
Memory

을 연결한다.

Identity와 Harness는 최소 Contract 형태로 포함한다.

149. Integrated PoC Candidate
User
↓
Task
↓
Task State
↓
Agent
↓
Context
↓
Capability
↓
Permission
↓
Harness
↓
Runtime
↓
Artifact / Environment
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
↓
Memory
150. PoC Expansion

후보:

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
Security / Permission

PoC 8
Verification / Evaluation

PoC 9
Orchestration / Delegation

PoC 10
Identity Continuity
151. Simplicity Rule

Architecture에 개념이 존재한다는 이유만으로
구현 Component를 추가하지 않는다.

Conceptual Boundary
≠
Implementation Unit

초기에는 가능한 한 단순하게 구현한다.

152. Technology Adoption Rule

새로운 기술을 도입할 때:

What problem does it solve?

Why is current architecture insufficient?

What trade-offs does it introduce?

Does it violate existing boundaries?

Can it be replaced later?

How will it be evaluated?

를 확인한다.

153. Historical and Future Compatibility

NOAH는 최신 기술만을 기준으로 설계하지 않는다.

Architecture Decision에는:

Foundational Principles
+
Current Evidence
+
Emerging Ideas

를 함께 고려한다.

154. Current Architecture Character

Project NOAH v0.1은 다음과 같이 정의할 수 있다.

A persistent, contract-driven, capability-based agent system with durable task execution, protected identity, explicit information boundaries, controlled execution, verification, evaluation, and governed adaptation.

155. What NOAH Is Not

NOAH는 단순:

LLM Wrapper

가 아니다.

단순:

Chatbot

도 아니다.

단순:

Tool Calling Agent

만도 아니다.

156. What NOAH Is

현재 Architecture에서 NOAH는:

Persistent Identity
+
Agent
+
Durable Task
+
Explicit State
+
Projected Context
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
Runtime
+
Orchestration
+
Verification
+
Evaluation
+
Learning

으로 구성되는 장기적인 Agent System이다.

157. Architecture Invariants

현재 v0.1에서 가능한 한 유지해야 할 Invariant:

Runtime failure must not destroy durable Task State.

Context must not become the canonical source of truth.

Memory must not replace Task State.

Knowledge must not silently become Memory.

Artifacts must remain independently identifiable from file paths.

Capabilities must not imply permission.

Agents must not receive unrestricted credentials by default.

Child agents must not automatically exceed parent permissions.

Agent self-report alone must not define successful completion.

Learning must not automatically rewrite protected Identity Core.

Protocols must remain replaceable behind stable Contracts.
158. Architecture Risks

현재 주요 위험:

Over-Abstraction
Contract Explosion
Harness Centralization
State Complexity
Memory Complexity
Identity Rigidity
Permission Complexity
Premature Multi-Agent
Premature Distribution
Technology Lock-in
159. Risk Mitigation
Simple First

Single Agent First

Logical Before Physical

Contract Before Framework

Evidence Before Optimization

Explicit Permission Before Autonomy

Verification Before Completion

Protected Core Before Automatic Adaptation

Replaceable Implementation Before Technology Lock-in
160. Architecture Readiness

현재:

Conceptual Architecture
→ High

Logical Boundaries
→ High

Architecture Decisions
→ High

Contract Details
→ Medium

Physical Architecture
→ Intentionally Low

Implementation Details
→ Intentionally Open
161. Next Architecture Documents

System Architecture 이후 각 영역을 상세화한다.

후보:

Core/
├── Identity.md
├── Agent.md
└── Task.md

Runtime/
├── Session.md
├── State.md
├── Context.md
├── Harness.md
└── Runtime.md

Information/
├── Memory.md
├── Knowledge.md
└── Retrieval.md

Artifacts/
└── Artifact.md

Capability/
├── Capability.md
├── Tool.md
├── Skill.md
└── Workflow.md

Security/
├── Policy.md
├── Permission.md
└── Execution-Security.md

Orchestration/
└── Orchestration.md

Evaluation/
├── Verification.md
├── Observability.md
└── Evaluation.md
162. Component Documentation Rule

각 Component Architecture 문서는 최소한 다음을 설명한다.

Purpose
Responsibilities
Non-Responsibilities
Inputs
Outputs
State
Persistence
Dependencies
Contracts
Security
Failure
Observability
Evaluation
Replaceable Implementations
Open Questions
163. Specification Boundary

Component Architecture가 정리된 이후:

Architecture
↓
Contract / Interface Specification

으로 넘어간다.

그때 실제:

Schema
API
Interface
Event
State Transition
Error Type

등을 구체화한다.

164. Implementation Boundary

Specification이 존재한다고 바로 전체 구현으로 넘어가지 않는다.

Architecture
↓
Specification
↓
PoC
↓
Evaluation
↓
Implementation

순서를 기본으로 한다.

165. Architecture Evolution Rule

실험 결과가 현재 Architecture Decision과 다를 경우:

PoC Evidence
↓
Review
↓
DDR Amendment / New DDR
↓
Architecture Update

를 사용한다.

Architecture를 정답으로 가정하고 Evidence를 무시하지 않는다.

166. Current Architecture Boundary

System Architecture v0.1에서는 다음을 최종 결정하지 않는다.

Exact Class Design
Exact Source Folder Layout
Exact Database Schema
Exact Runtime Framework
Exact Agent Framework
Exact Model
Exact Protocol
Exact Storage
Exact Deployment
Exact UI

이는 이후 Component Architecture / Specification / PoC에서 다룬다.

167. Next Step
System Architecture v0.1
        ↓
Component Architecture
        ↓
Contract / Interface Specification
        ↓
Integrated PoC
        ↓
Evaluation
        ↓
Architecture Revision
168. First Component Architecture

System Architecture 이후 가장 먼저 상세화할 후보:

Core
↓
Identity
Agent
Task

그 후:

Runtime
↓
Session
State
Context
Harness
Runtime

순으로 진행한다.

169. Final Architecture Statement

Project NOAH는 하나의 Model이나 Framework에 의해 정의되지 않는다.

NOAH는 지속되는 Identity와 Task를 중심으로,
State와 Context를 분리하고,
Memory와 Knowledge를 활용하며,
Artifact를 현실 세계의 지속적인 작업 결과로 관리하고,
Capability를 Policy와 Permission 아래에서 실행하며,
Harness와 Runtime을 통해 교체 가능한 실행 환경을 제공한다.

실행 결과는 Evidence를 통해 Verification되고,
전체 과정은 Observability와 Evaluation을 통해 분석된다.

Experience는 Memory와 Learning으로 이어질 수 있지만,
중요한 변화는 Governance와 Evaluation을 통해 통제된다.

이러한 Boundary는 특정 기술을 고정하기 위한 것이 아니라
미래의 더 나은 구현을 받아들이면서도 NOAH의 핵심 구조와 신뢰를 유지하기 위해 존재한다.

170. Final Principle

NOAH의 Architecture는 기술을 중심에 두지 않는다.

지속되어야 하는 것은 경계와 원칙이고, 교체되어야 하는 것은 구현이다.
