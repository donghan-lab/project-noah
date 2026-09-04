# Project NOAH Agent Architecture

> Project NOAH Architecture
> Component: Agent
> Architecture Version: 0.1
> Status: Blueprint
> Date: 2026-09-04
> Related Decisions: DDR-002, DDR-005, DDR-006

---

# 1. Purpose

이 문서는 Project NOAH의 Agent Component Architecture를 정의한다.

Agent는 현재 Goal과 Context를 바탕으로 상황을 이해하고,
판단하고, 계획하며, 필요한 Capability를 선택하고,
결과를 해석하는 Cognitive Decision Entity다.

핵심 질문:

> **"NOAH에서 실제로 이해하고 판단하며 행동을 결정하는 주체는 무엇인가?"**

---

# 2. Architectural Role

Agent는 Identity와 실행 Infrastructure 사이에서
Cognitive Decision Making을 담당한다.

Architecture 상 기본 위치:

```text
CONSTITUTION
     ↓
GOVERNANCE
     ↓
IDENTITY
     ↓
   AGENT
     ↓
   TASK

Execution 측면에서는:

Agent
 ↓
Capability Request
 ↓
Harness
 ↓
Runtime
 ↓
Execution

으로 연결된다.

3. Core Definition

Agent는 다음을 수행하는 논리적 Entity다.

Agent
=
Understanding
+
Reasoning
+
Planning
+
Decision Making
+
Capability Selection
+
Result Interpretation

Agent 자체를 특정 LLM 또는 Framework와 동일시하지 않는다.

4. Core Separations

Project NOAH는 다음을 명확히 구분한다.

Agent
≠
Identity

Agent
≠
Model

Agent
≠
Runtime

Agent
≠
Harness

Agent
≠
Session

Agent
≠
Task

Agent
≠
Orchestrator

Agent
≠
Capability

Agent
≠
Workflow

이 구분은 Agent Architecture의 핵심 Invariant다.

5. Agent vs Identity

Identity:

NOAH가 시간에 걸쳐 누구로 지속되는가?

Agent:

현재 Context에서 이해하고 판단하는 Cognitive Entity

관계:

Identity
↓
Identity Projection
↓
Agent

Agent Instance가 종료되어도 Root Identity는 지속될 수 있다.

6. Agent vs Model

Model은 Agent의 Cognitive Engine으로 사용될 수 있다.

Agent
↓
Model Interface
↓
Model

그러나:

Agent
≠
Model

이다.

7. Why Agent Is Not the Model

Agent에는 Model 이외에도 다음 Architecture Context가 필요할 수 있다.

Identity Projection
Task
Context
Capabilities
Policies
Execution Results
State References
Memory / Knowledge Access

따라서 Model 교체가 Agent Architecture 전체의 교체를 의미해서는 안 된다.

8. Model Replacement

후보:

Agent
↓
Model Interface
├── Model A
├── Model B
├── Local Model
└── Future Model

Model 교체 이후에도 Agent Contract와 다른 Architecture Boundary를
가능한 한 유지한다.

9. Agent Responsibilities

Agent의 주요 책임:

Understand Goal

Interpret Context

Identify Relevant Constraints

Reason About Possible Actions

Create or Refine Local Plans

Select Capabilities

Make Decisions

Interpret Capability Results

Recognize Uncertainty

Recognize Need for More Information

Request Verification

Produce Structured Results
10. Agent Non-Responsibilities

Agent는 다음 Infrastructure를 직접 소유하지 않는다.

Task Store

Identity Store

Memory Store

Knowledge Store

Artifact Store

Credential Store

Runtime Lifecycle

Sandbox

Telemetry Backend

Permission Store

Database

External Service Credentials
11. Infrastructure Ownership Rule

Agent는 Infrastructure를 직접 구현하거나 소유하기보다
Contract / Interface를 통해 사용한다.

예:

Agent
↓
Memory Interface
↓
Memory System

이지:

Agent
↓
Specific Vector Database

가 아니다.

12. Agent Input

Agent가 판단하기 위한 주요 Input 후보:

Task Goal

Current Context

Relevant Identity Projection

Constraints

Current State Projection

Available Capability Information

Policy / Permission Information

Previous Results

Uncertainty / Failure Information
13. Agent Output

Agent의 주요 Output 후보:

Decision

Plan

Capability Request

Clarification Request

Delegation Request

Result Interpretation

Uncertainty

Failure Report

Recommended Next Step
14. Agent Contract

Architecture-level Agent Contract 후보:

Agent Contract
├── Agent ID / Instance ID
├── Identity Reference
├── Role
├── Input
├── Context Reference
├── Available Capabilities
├── Constraints
├── Budget
├── Output
├── Status
└── Version

정확한 Schema는 Specification 단계에서 결정한다.

15. Agent Instance

Agent Architecture와 실제 Agent Instance를 구분한다.

Agent Architecture
↓
Agent Instance

Agent Instance는 특정 Task / Session / Runtime 안에서
생성되고 종료될 수 있다.

16. Agent Lifetime

Agent Instance의 Lifetime은 Root Identity보다 짧을 수 있다.

Identity
├── Agent Instance A
├── Agent Instance B
└── Agent Instance C

Agent Instance 종료가 Identity 종료를 의미하지 않는다.

17. Agent State

Agent가 실행 중 일시적인 상태를 가질 수 있다.

후보:

Current Goal

Current Local Plan

Current Step

Current Uncertainty

Current Capability Selection

Temporary Working Information

이 상태를 canonical Task State와 동일하게 취급하지 않는다.

18. Agent Internal State vs Task State
Agent Internal State
= temporary cognitive / execution-facing state

Task State
= durable canonical task progress

Agent 내부 정보만을 Task Progress의 Source of Truth로 사용하지 않는다.

19. Context Relationship

Agent는 Context를 직접 Source of Truth로 간주하지 않는다.

State
Memory
Knowledge
Artifacts
Identity
Environment
Policy
      ↓
Context Manager
      ↓
Context
      ↓
Agent
20. Context Consumption

Agent는 현재 Context를 이용해 판단한다.

그러나 Context에는:

Missing Information

Stale Information

Untrusted Information

Conflicting Information

Compressed Information

이 존재할 수 있다는 점을 전제로 한다.

21. Context Trust

Agent가 Context의 모든 내용을 동일한 Authority로 취급하지 않도록 한다.

후보:

Constitution / System Rules

Verified User Intent

Task State

Verified Environment State

Trusted Memory

Knowledge

Tool Observation

External Content

Untrusted Content

의 Source / Trust Metadata를 활용할 수 있다.

22. Context Reconstruction

Agent Instance가 교체되어도 Context를 재구성할 수 있다.

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
Identity Projection
+
Environment
+
Policy
↓
Context Reconstruction
↓
New Agent Instance
23. Reasoning

Reasoning은 Agent의 핵심 기능 중 하나다.

목적:

Understand Situation

Compare Options

Identify Constraints

Estimate Consequences

Recognize Missing Information

Select Next Action
24. Reasoning Persistence Rule

Agent의 모든 내부 추론 과정을 영속화할 필요는 없다.

장기적으로 보존해야 하는 것은 필요에 따라:

Decision

Plan

Evidence

Result

Assumptions

Uncertainty

Important Rationale

등이다.

Model 내부의 일시적인 reasoning representation에
Architecture를 종속시키지 않는다.

25. Decision

Agent는 현재 Goal과 Context를 바탕으로 다음 행동을 결정한다.

후보:

Answer

Ask

Observe

Retrieve

Use Capability

Create Artifact

Modify Artifact

Delegate

Wait

Pause

Abort
26. Decision Boundary

Decision과 Execution을 구분한다.

Agent
↓
Decision
↓
Capability Request
↓
Execution System

Agent가 행동을 결정했다는 사실이
실제 Environment 변화가 발생했다는 의미는 아니다.

27. Planning

Agent는 Task 수행을 위한 Local Plan을 만들 수 있다.

예:

Goal
↓
Step A
↓
Step B
↓
Step C
28. Plan vs Task
Task
= What must be achieved

Plan
= How the Agent currently intends to achieve it

Plan은 변경될 수 있다.

Task Goal은 Plan 변경으로 자동 변경되지 않는다.

29. Local Planning vs Orchestration

Agent의 Local Planning과 Orchestrator를 구분한다.

Agent Local Planning
= 자신의 실행 방향 결정

Orchestrator
= 복수 Agent / Subtask / Dependency coordination

모든 Task에 Orchestrator가 필요한 것은 아니다.

30. Single-Agent Default

기본 실행 방식:

Task
↓
Agent
↓
Harness
↓
Execution

Multi-Agent는 필요한 경우에만 사용한다.

31. Multi-Agent Escalation

다음 상황에서 Orchestration을 요청할 수 있다.

Specialization Required

Parallel Work Beneficial

Context Isolation Needed

Independent Verification Needed

Task Too Large

Failure Isolation Needed
32. Capability Selection

Agent는 Goal을 달성하기 위해 필요한 Capability를 선택할 수 있다.

Task
↓
Context
↓
Relevant Capability Discovery
↓
Agent
↓
Capability Selection
33. Capability Information

Agent가 Capability를 선택하기 위해 필요한 정보 후보:

Capability ID

Description

Input / Output

Preconditions

Expected Side Effects

Cost

Timeout

Permission Requirement

Verification Method
34. Progressive Capability Disclosure

모든 Capability Schema를 항상 Context에 포함하지 않는다.

Capability Summary
↓
Relevant Capability Selection
↓
Detailed Contract

방식을 사용할 수 있다.

35. Capability Request

Agent는 직접 Environment를 변경하기보다
Capability Request를 생성한다.

Agent
↓
Capability Request
↓
Policy
↓
Permission
↓
Harness / Runtime
↓
Execution
36. Capability Does Not Imply Permission

Agent가 Capability를 알고 있거나 선택할 수 있다는 사실이
사용 권한을 의미하지 않는다.

Capability Availability
≠
Permission
37. Policy Relationship

Agent는 Policy를 고려해 Decision을 내릴 수 있다.

그러나 Security-critical Policy Enforcement를
Agent 판단에만 의존하지 않는다.

Agent
↓
Request
↓
Policy Enforcement
38. Permission Relationship

Permission은 실행 계층에서 독립적으로 검증된다.

Agent Request
↓
Permission Check
↓
Allow / Ask / Deny

Agent가 자신의 Permission을 임의로 확장하지 않는다.

39. Approval Relationship

사용자 Approval이 필요한 경우 Agent는
실행 대신 Approval Request를 생성할 수 있다.

Agent
↓
Sensitive Action
↓
Approval Required
↓
User / Authorized Authority
40. Credential Rule

Agent가 Secret / Credential 자체를 Model Context에 직접 전달받는 구조를 피한다.

Agent
↓
Capability Request
↓
Credential Broker
↓
External Service
41. Harness Relationship

Harness는 Agent와 Infrastructure 사이의 안정된 실행 경계다.

Agent
↓
Harness Contract
↓
Infrastructure

Agent는 Harness를 통해 필요한 Infrastructure 기능에 접근한다.

42. Harness Does Not Reason for Agent

Harness:

Access

Execution Coordination

Policy Integration

Runtime Integration

Recovery Integration

Observability

Agent:

Understanding

Reasoning

Decision

핵심 책임을 구분한다.

43. Runtime Relationship

Runtime은 Agent Execution Lifecycle을 관리한다.

Agent
↓
Harness
↓
Runtime

Runtime이 담당하는 후보:

Start

Run

Pause

Resume

Cancel

Retry

Checkpoint

Recover
44. Runtime Replacement

Agent Architecture가 특정 Runtime Framework에 종속되지 않도록 한다.

Runtime A
Runtime B
Future Runtime
     ↓
Stable Agent / Harness Contract
45. Memory Relationship

Agent는 Memory를 읽거나 Memory Candidate를 만들 수 있다.

Memory
↓
Retrieval
↓
Context
↓
Agent

그리고:

Agent Experience
↓
Memory Candidate

가 가능하다.

46. Memory Write Rule

Agent가 생성한 모든 내용을 자동으로 Long-term Memory에 저장하지 않는다.

Agent Output
↓
Memory Candidate
↓
Validation / Policy
↓
Memory
47. Knowledge Relationship

Agent는 Knowledge를 검색하고 사용한다.

Knowledge
↓
Retrieval
↓
Context
↓
Agent

Agent가 생성한 추론을 검증 없이 확정 Knowledge로 저장하지 않는다.

48. Knowledge Creation

후보:

Agent Finding
↓
Evidence
↓
Validation
↓
Knowledge Candidate
↓
Knowledge
49. Artifact Relationship

Agent는 Artifact를 생성하거나 변경하도록 요청할 수 있다.

Agent
↓
Capability
↓
Artifact Operation

Artifact lifecycle 자체는 Artifact Architecture가 담당한다.

50. Artifact Reference

Agent Context에는 가능한 한 전체 Artifact 대신:

Artifact Reference

Metadata

Relevant Section

Summary

를 사용한다.

필요할 때 Full Artifact를 조회한다.

51. Result Interpretation

Capability 실행 이후 Agent는 Result를 해석한다.

Execution
↓
Result
↓
Agent Interpretation

그러나 Agent의 Interpretation이 Evidence 자체를 대체하지 않는다.

52. Result vs Evidence
Result
= What is reported

Evidence
= What supports the report

Agent는 둘을 구분해서 다룬다.

53. Verification Relationship

Agent는 Verification을 요청하거나
Verification 결과를 해석할 수 있다.

그러나 Agent self-report만으로
Task Completion을 결정하지 않는다.

Agent Result
↓
Evidence
↓
Verification
↓
Task State Transition
54. Independent Verification

High-risk 또는 중요한 결과에서는
실행 Agent와 Verification 주체를 분리할 수 있다.

Agent
↓
Execution
↓
Independent Verification
55. Evaluation Relationship

Agent의 행동은 Evaluation 대상이다.

후보:

Task Success

Correctness

Decision Quality

Capability Selection

Safety

Efficiency

Recovery

Uncertainty Calibration

Evidence Quality
56. Uncertainty

Agent는 불확실성을 표현할 수 있어야 한다.

후보:

Confidence

Unknowns

Assumptions

Alternatives

Evidence Gaps

불확실성을 숨기는 방향으로 최적화하지 않는다.

57. Missing Information

Agent가 충분한 정보 없이 행동하는 것보다
추가 정보를 요청하는 것이 적절한 경우가 있다.

Insufficient Context
↓
Clarification / Retrieval / Observation
58. Assumptions

중요한 Assumption은 가능한 경우 명시적으로 표현한다.

Decision
├── Known Facts
├── Assumptions
└── Unknowns

High-impact Decision일수록 Assumption 검증을 우선한다.

59. Failure Recognition

Agent는 실패 가능성을 인식할 수 있어야 한다.

후보:

Capability Failure

Invalid Result

Permission Denied

Timeout

Insufficient Information

Verification Failure

Conflicting Evidence

Budget Exhaustion
60. Failure Response

후보 행동:

Retry

Alternative Capability

Retrieve More Information

Replan

Delegate

Ask User

Pause

Escalate

Abort

무조건 Retry하지 않는다.

61. Retry Awareness

Agent는 Capability의:

Idempotency

Side Effects

Retry Policy

Previous Attempts

등을 고려할 수 있어야 한다.

62. Recovery Relationship

Runtime Failure 이후 새 Agent Instance가 Task를 이어받을 수 있다.

Task State
+
Checkpoint
+
Artifacts
+
Relevant Memory
↓
Context Reconstruction
↓
New Agent Instance
↓
Resume
63. Agent Continuity

Agent Instance Continuity와 Identity Continuity를 구분한다.

Agent Instance A
↓
Failure
↓
Agent Instance B

가 발생해도:

Root Identity

는 동일하게 유지될 수 있다.

64. Cancellation

Agent는 Task / Execution Cancellation을 받아들일 수 있어야 한다.

Cancellation
↓
Agent
↓
Stop New Decisions
↓
Runtime Cancellation

이미 발생한 Side Effect는 별도로 처리한다.

65. Budget

Agent Execution은 Budget 아래에서 동작할 수 있다.

후보:

Tokens

Time

Capability Calls

Compute

Storage

Network

Delegation Count
66. Budget Awareness

Agent는 남은 Budget에 따라 전략을 조정할 수 있다.

예:

High Budget
→ broader exploration

Low Budget
→ prioritize critical steps

하지만 Budget Enforcement 자체를 Agent만 담당하지 않는다.

67. Role

Agent는 현재 Task에서 Role을 가질 수 있다.

예:

General Agent

Research Role

Coding Role

Review Role

Verification Role

Role은 Identity와 동일하지 않다.

68. Role vs Identity
Identity
= persistent who

Role
= current responsibility

동일한 Identity가 여러 Role을 수행할 수 있다.

69. Temporary Specialist

필요한 경우 Temporary Specialist Agent를 생성할 수 있다.

Root Agent
↓
Delegation
↓
Temporary Specialist

Temporary Specialist마다 Persistent Identity를 생성하지 않는다.

70. Delegation

Agent가 다른 Agent에 작업을 위임할 때
Delegation Contract를 사용한다.

후보:

Goal

Scope

Context Projection

Permission

Budget

Constraints

Expected Output

Verification Requirement
71. Child Permission

기본:

Child Permission
⊆
Parent Permission

을 유지한다.

72. Agent-as-Tool

Agent-as-Tool 패턴:

Parent Agent
↓
Child Agent
↓
Structured Result
↓
Parent Agent

Parent가 Control을 유지한다.

73. Handoff

Handoff는 Control 자체를 다른 Agent에게 넘긴다.

Agent A
↓
Handoff
↓
Agent B

Delegation / Agent-as-Tool과 구분한다.

74. Structured Agent Result

Agent가 상위 Component에 반환하는 결과 후보:

Status

Summary

Findings

Evidence References

Artifact References

Uncertainty

Errors

Recommended Next Step
75. Observability

Agent Execution을 추적할 수 있어야 한다.

후보 Metadata:

Agent Instance ID

Identity Reference

Task ID

Session ID

Execution ID

Model Reference

Context Version / Reference

Capability Calls

Result

Timestamp
76. Decision Observability

중요 Decision에 대해 가능한 경우:

Decision

Relevant Inputs

Selected Capability

Constraints

Evidence References

Uncertainty

를 추적한다.

Model의 모든 내부 reasoning trace를 저장해야 한다는 의미는 아니다.

77. Audit

다음 Agent Action은 Audit 대상이 될 수 있다.

Delegation

High-risk Capability Request

Approval Request

External Publish Request

Destructive Action Request

Identity Change Proposal

Policy-sensitive Decision
78. Agent Evaluation

Agent Quality 후보:

Goal Understanding

Decision Correctness

Plan Quality

Tool Selection

Evidence Usage

Uncertainty Calibration

Recovery Quality

Efficiency

Safety

User Alignment
79. Model Evaluation vs Agent Evaluation

Model 품질과 Agent System 품질을 구분한다.

Model Evaluation
≠
Agent Evaluation

Agent Failure의 원인이 항상 Model인 것은 아니다.

80. Failure Attribution

후보 원인:

Model

Context

Task Definition

Memory

Knowledge

Planning

Capability

Permission

Runtime

Environment

Verification

Agent Architecture
81. Learning Relationship

Agent Experience는 Learning에 사용될 수 있다.

Agent Execution
↓
Evidence
↓
Evaluation
↓
Experience
↓
Learning
82. Agent Self-Improvement Boundary

Agent가 자신의 Core Architecture를 자동으로 변경하지 않는다.

Agent Reflection
↓
Improvement Proposal

까지는 가능하지만:

Improvement Proposal
↓
Automatic Core Replacement

은 기본적으로 허용하지 않는다.

83. Skill Improvement

낮은 위험도의 개선:

Experience
↓
Skill Improvement Proposal
↓
Evaluation
↓
Adoption

등은 향후 Controlled Adaptation 영역에서 검토한다.

84. Personality Relationship

Agent Behavior는 Personality의 영향을 받을 수 있다.

Identity
↓
Personality
↓
Context
↓
Agent Behavior

Personality가 Reasoning correctness나 Security Rule을 무시하는 근거가 되지 않는다.

85. User Relationship

Agent는 User Relationship Context를 사용할 수 있다.

하지만:

Relationship Optimization
≠
User Dependency Optimization

이다.

User의 판단과 통제권을 지원하는 방향을 유지한다.

86. Instruction Authority

Agent는 여러 Instruction Source가 충돌할 수 있음을 전제로 한다.

후보:

Constitution

System Policy

User Intent

Task Instructions

Memory

External Content

Tool Output

External Content가 상위 Authority의 Instruction을 임의로 대체하지 않도록 한다.

87. Prompt Injection Awareness

External Content가 Instruction처럼 보일 수 있다.

Agent Architecture는:

Data
≠
Trusted Instruction

이라는 원칙을 유지한다.

실제 enforcement는 Security / Context Architecture와 함께 수행한다.

88. Model Failure

Model 호출이 실패할 수 있다.

후보:

Timeout

Provider Failure

Invalid Output

Context Limit

Rate Limit

Safety Refusal

Malformed Structured Output

Agent Architecture는 하나의 Model 호출 성공을 전제로 하지 않는다.

89. Model Fallback

필요한 경우:

Primary Model
↓
Failure
↓
Fallback Policy
↓
Alternative Model

을 사용할 수 있다.

정확한 Model Routing은 후속 Specification에서 결정한다.

90. Model Capability Differences

모든 Model이 동일한 Capability를 가지지 않는다.

예:

Context Window

Tool Calling

Structured Output

Multimodality

Latency

Cost

Reasoning Quality

Agent Contract가 특정 Model 특성에 과도하게 종속되지 않도록 한다.

91. Structured Output

Agent와 Infrastructure 사이의 중요한 Communication은
가능한 경우 Structured Output을 사용한다.

예:

Capability Request

Delegation

Result

Failure

Verification Request

Natural Language만으로 Infrastructure Control을 표현하지 않는 방향을 우선한다.

92. Contract Validation

Agent Output이 Contract를 위반하는 경우:

Agent Output
↓
Validation
↓
Valid
or
Repair / Retry / Reject

흐름을 사용할 수 있다.

93. Agent Architecture Flow

일반 Candidate Flow:

Task
↓
Task State
↓
Context Projection
↓
Agent
↓
Understand
↓
Reason
↓
Plan / Decide
↓
Capability Request
↓
Policy / Permission
↓
Harness / Runtime
↓
Execution
↓
Result / Evidence
↓
Agent Interpretation
↓
Verification
↓
Task State Update
94. Agent Recovery Flow
Agent Instance A
↓
Failure
↓
Persisted Task State
+
Artifacts
+
Execution Records
↓
Context Reconstruction
↓
Agent Instance B
↓
Resume
95. Initial Implementation Candidate

첫 Agent PoC에서는 최소한 다음을 구현한다.

Agent Interface

Model Interface

Context Input

Task Reference

Capability Selection

Structured Capability Request

Structured Result

Basic Uncertainty

Basic Failure Handling
96. Initial Model Strategy

첫 PoC에서는 하나의 Model로 시작해도 된다.

중요한 것은:

Agent Architecture
≠
Chosen Model

경계를 코드에서 유지하는 것이다.

Multi-model Routing은 초기 필수 사항이 아니다.

97. Deferred Implementation

초기 PoC에서 다음은 미룰 수 있다.

Complex Multi-Agent

Learned Routing

Automatic Agent Generation

Persistent Specialist Agents

Dynamic Role Creation

Advanced Model Ensemble

Agent Debate

Autonomous Architecture Modification

Full Self-improvement
98. PoC Scenario

최소 Agent PoC:

1. Task 생성

2. Task State 로드

3. Context 구성

4. Agent Instance 생성

5. Model 호출

6. Agent가 Capability 선택

7. Structured Capability Request 생성

8. Capability 실행

9. Result / Evidence 반환

10. Agent가 Result 해석

11. Verification

12. Task State Update
99. Replacement PoC

후속 검증:

Agent Contract
↓
Model A

Model A 제거

Agent Contract
↓
Model B

이후 Task Flow가 유지되는지 확인한다.

100. Recovery PoC
Task Running
↓
Agent / Runtime Failure
↓
Persisted State
↓
New Agent Instance
↓
Context Reconstruction
↓
Resume

를 검증한다.

101. Acceptance Criteria

Agent Architecture v0.1의 최소 기준:

Agent is independent from a specific Model.

Agent does not own durable Task State.

Agent does not directly own infrastructure storage.

Agent consumes projected Context.

Agent can select Capabilities through explicit Contracts.

Capability selection does not imply Permission.

Agent Result is distinguishable from Evidence.

Agent self-report alone does not complete a Task.

Agent can express uncertainty and failure.

Agent Instance can be replaced without destroying Identity or Task continuity.
102. Architecture Invariants
Agent must not become the Identity source of truth.

Agent must not become the Task State source of truth.

Agent must not treat Context as canonical state.

Agent must not directly bypass Permission enforcement.

Agent must not receive unrestricted Credentials by default.

Agent must not silently promote generated claims into verified Knowledge.

Agent must not automatically write every Experience into Memory.

Agent self-report must not replace Verification.

Agent replacement must not destroy durable Task continuity.

Model replacement must not require redesigning the Agent architecture.
103. Stable Boundaries

현재 안정적으로 유지할 후보:

Agent semantics

Agent / Model separation

Agent / Identity separation

Agent / Runtime separation

Agent / Harness separation

Agent / Orchestrator separation

Decision / Execution separation

Result / Evidence separation

Capability / Permission separation
104. Replaceable Implementations
Model

Model Provider

Agent Framework

Prompt Strategy

Reasoning Strategy

Planning Algorithm

Model Router

Structured Output Library

는 교체 가능해야 한다.

105. Deferred Decisions

현재 결정하지 않는다.

Exact Agent Class Design

Exact Prompt Format

Exact Model

Exact Model Router

Exact Planning Algorithm

Exact Reasoning Strategy

Exact Agent Framework

Exact Retry Strategy

Exact Multi-Agent Implementation

Exact Agent Persistence Format
106. Related Architecture
System Architecture

Identity Architecture

Task Architecture

Context Architecture

Harness Architecture

Runtime Architecture

Capability Architecture

Security Architecture

Orchestration Architecture

Evaluation Architecture
107. Related Decisions
DDR-002
Harness Boundary

DDR-005
Identity Persistence

DDR-006
Orchestration Contract

추가 관련 Decision:

DDR-001
Task State / Runtime Boundary

DDR-003
Memory / Knowledge Boundary

DDR-004
Artifact Architecture
108. Specification Questions

후속 Specification에서 결정할 질문:

What is the minimum Agent interface?

How is Agent input represented?

How are Capability Requests structured?

How is Model output validated?

How is uncertainty represented?

How are Agent failures classified?

How is an Agent Instance identified?

How is Model replacement performed?

How are Context references passed?

How are Agent results represented?

What information is persisted between Agent Instances?
109. Architecture Boundary

본 문서는 Agent의 Logical Architecture를 정의한다.

다음은 정의하지 않는다.

Concrete Python Class

Concrete Package

Concrete API

Exact Prompt

Exact Model

Exact Database

Exact Runtime Framework

Exact Multi-Agent Framework
110. Current Architecture Statement

Project NOAH의 Agent는 특정 LLM이나 Framework 그 자체가 아니라,
현재 Goal과 Context를 이해하고 판단하여 다음 행동을 결정하는 Cognitive Decision Entity다.

Agent는 Identity를 사용하지만 Identity를 소유하지 않고,
Task State를 사용하지만 Task State의 Source of Truth가 아니며,
Capability를 선택하지만 Permission을 부여하지 않고,
Execution을 요청하지만 Infrastructure를 직접 소유하지 않는다.

Model, Runtime 및 Agent Framework는 교체 가능하며,
Agent는 Stable Contract를 통해 다른 Architecture Component와 협력한다.

111. Final Principle

Agent의 지능은 얼마나 많은 것을 직접 소유하는가에서 나오지 않는다.

Agent의 역할은 필요한 정보를 이해하고, 가능한 행동을 판단하며, 명확한 Contract를 통해 시스템의 다른 능력을 올바르게 사용하는 것이다.