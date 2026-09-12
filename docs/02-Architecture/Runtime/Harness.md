# Project NOAH Harness Architecture

> Project NOAH Architecture
> Component: Harness
> Architecture Version: 0.1
> Status: Blueprint
> Date: 2026-09-12
> Related Decisions: DDR-001, DDR-002, DDR-006

---

# 1. Purpose

이 문서는 Project NOAH의 Harness Architecture를 정의한다.

Harness는 Agent와 실제 Infrastructure 사이에서
실행 요청을 안전하고,
일관되고,
관찰 가능하며,
복구 가능한 방식으로 연결하기 위한
Stable Execution Boundary다.

핵심 질문:

> **"Agent가 무엇을 하기로 결정한 뒤,
> 그 결정이 실제 시스템에서 어떻게 안전하고 지속 가능하게 실행되는가?"**

---

# 2. Architectural Role

Harness는 Cognitive Decision Layer와
Execution Infrastructure 사이에 위치한다.

기본 관계:

```text
Agent
  ↓
Execution / Capability Request
  ↓
Harness
  ↓
Infrastructure
```

보다 구체적으로:

```text
Agent / Orchestrator
        ↓
Execution Request
        ↓
      Harness
        ↓
Contract Validation
        ↓
Capability Resolution
        ↓
Policy / Permission / Approval
        ↓
Runtime
        ↓
Sandbox / Credential Boundary
        ↓
Capability Execution
        ↓
Result / Evidence
```

---

# 3. Core Definition

Harness의 기본 의미:

```text
Harness
=
Stable Execution Boundary
+
Execution Mediation
+
Infrastructure Coordination
+
Safety Enforcement Integration
+
Recovery Integration
+
Observability Integration
```

Harness는 하나의 특정 Framework나 Process를 의미하지 않는다.

---

# 4. Core Separations

Project NOAH는 다음을 구분한다.

```text
Harness
≠
Agent

Harness
≠
Model

Harness
≠
Runtime

Harness
≠
Orchestrator

Harness
≠
Context Manager

Harness
≠
State Store

Harness
≠
Capability

Harness
≠
Policy

Harness
≠
Permission

Harness
≠
Sandbox

Harness
≠
Credential Store

Harness
≠
Observability Backend

Harness
≠
Verification System
```

이 구분은 Harness Architecture의 핵심 Invariant다.

---

# 5. Why Harness Exists

Agent가 Infrastructure를 직접 호출하면:

```text
Agent
├── Database
├── Filesystem
├── APIs
├── Credentials
├── Sandbox
├── Runtime
└── Tools
```

같은 구조가 만들어질 수 있다.

이 경우:

- Agent와 Infrastructure가 강하게 결합되고
- Security enforcement가 Agent 판단에 의존하며
- Runtime 교체가 어려워지고
- Side Effect 추적이 어려워지며
- Recovery 방식이 Tool마다 달라지고
- Observability가 분산되고
- Agent Framework가 Architecture를 지배할 수 있다.

따라서 Stable Harness Boundary를 둔다.

---

# 6. Harness Principle

핵심 원칙:

> **Agent는 무엇을 할지 결정한다.**
>
> **Harness는 선택된 실행이 어떻게 안전하게 수행될 수 있는지를 중재한다.**

---

# 7. Agent vs Harness

Agent:

```text
Understand

Reason

Plan

Decide

Select Capability

Interpret Result
```

Harness:

```text
Validate Request

Resolve Capability

Coordinate Policy

Coordinate Permission

Coordinate Approval

Select / Access Runtime

Mediate Execution

Track Execution

Support Recovery
```

---

# 8. Harness Does Not Reason for the Agent

Harness가 Agent의 Cognitive Decision을 대신하지 않는다.

예:

```text
Harness:
"어떤 전략이 최선인가?"
```

를 판단하는 것이 기본 책임이 아니다.

대신:

```text
Harness:
"이 요청은 실행 가능한가?"
"권한이 있는가?"
"어떤 Runtime에서 수행할 수 있는가?"
"어떻게 추적하고 복구할 것인가?"
```

를 다룬다.

---

# 9. Harness vs Runtime

중요한 경계:

```text
Harness
= stable execution boundary

Runtime
= actual execution lifecycle
```

Runtime은 다음을 담당할 수 있다.

```text
Start
Run
Pause
Resume
Cancel
Checkpoint
Recover
Terminate
```

Harness는 Runtime을 사용하지만 Runtime 자체가 아니다.

---

# 10. Runtime Replacement

후보:

```text
Harness Contract
├── Runtime Adapter A
├── Runtime Adapter B
└── Future Runtime Adapter
```

Runtime 구현이 바뀌더라도
Agent와 Harness 사이의 핵심 Contract는 가능한 한 유지한다.

---

# 11. Harness vs Orchestrator

또 하나의 중요한 경계:

```text
Orchestrator
= What / When / Who / Structure

Harness
= How selected execution happens safely
```

---

# 12. Orchestrator Responsibilities

Orchestrator 후보 책임:

```text
Task Decomposition

Planning

Delegation

Scheduling

Parallelism

Agent Selection

Aggregation

Replanning

Coordination Strategy
```

---

# 13. Harness Responsibilities

Harness 후보 책임:

```text
Execution Request Mediation

Contract Validation

Context / State Access Mediation

Capability Resolution

Policy Integration

Permission Integration

Approval Integration

Runtime Access

Credential Boundary

Sandbox Integration

Execution Tracking

Side-effect Tracking

Cancellation Propagation

Recovery Integration

Observability Integration

Verification Hooks
```

---

# 14. Harness Does Not Schedule Tasks

Harness가 Task Priority Queue나
Multi-Agent Scheduling Algorithm을 소유하지 않는다.

```text
Orchestrator
↓
Execution Request
↓
Harness
```

방향을 유지한다.

---

# 15. Harness vs Context Manager

```text
Context Manager
= construct relevant information projection

Harness
= mediate execution boundary
```

Harness는 필요할 경우 Context Interface를 통해
Context Manager를 사용한다.

---

# 16. Context Relationship

후보:

```text
Agent
↓
Harness
↓
Context Interface
↓
Context Manager
```

또는 Runtime 시작 전
이미 생성된 Context Reference를 Harness가 받을 수도 있다.

정확한 호출 방식은 Specification에서 결정한다.

---

# 17. Harness Does Not Own Context

중요:

```text
Harness
↓
Context Interface
```

이지:

```text
Harness
└── entire Context system
```

이 아니다.

---

# 18. Harness vs State

Harness는 실행을 위해 State를 읽거나
State Transition Request를 전달할 수 있다.

하지만:

```text
Harness
≠
State Authority
```

다.

---

# 19. State Access

후보:

```text
Harness
↓
State Interface
↓
Task State / Execution State
```

Harness가 canonical Task State를 직접 arbitrary overwrite하지 않는다.

---

# 20. State Mutation

실행 결과에 따라:

```text
Execution
↓
Result / Evidence
↓
State Transition Request
↓
Validation
↓
Commit
```

흐름을 사용한다.

Harness는 이 과정을 연결할 수 있지만
Task State의 의미를 소유하지 않는다.

---

# 21. Harness vs Capability

Capability는 NOAH가 수행할 수 있는 행동 또는 절차적 능력이다.

Harness는 Capability를 실행 가능하게 연결한다.

```text
Agent
↓
Capability Request
↓
Harness
↓
Capability Provider
```

---

# 22. Capability Implementation Independence

예:

```text
Capability Contract
↓
Harness
├── Local Tool
├── API Adapter
├── MCP Adapter
├── Workflow Adapter
└── Agent Delegation Adapter
```

Harness가 특정 Capability Framework에 종속되지 않도록 한다.

---

# 23. Harness vs Policy

Policy:

> 어떤 행동이 허용될 수 있는가?

Harness:

> 실행 요청이 Policy evaluation을 거치도록 보장하는 실행 경계

따라서:

```text
Harness
≠
Policy Engine
```

이다.

---

# 24. Harness vs Permission

Permission:

> 특정 Principal이 특정 Scope에서 해당 Action을 수행할 권한이 있는가?

Harness는 Permission을 자체적으로 발명하지 않는다.

```text
Harness
↓
Permission Service / Policy
↓
Allow / Ask / Deny
```

---

# 25. Enforcement Boundary

Security-critical 실행에서는
Agent가 단순히:

```text
"권한이 있다고 판단했다."
```

는 이유로 실행하지 않는다.

Harness execution path에서 실제 authorization을 확인한다.

---

# 26. Execution Path Invariant

Side Effect가 있는 Capability는 기본적으로:

```text
Agent Request
↓
Harness
↓
Policy / Permission
↓
Runtime
↓
Execution
```

같은 통제된 Boundary를 통과해야 한다.

---

# 27. Pure Reasoning Exception

모든 내부 연산이 Harness를 필요로 하는 것은 아니다.

예:

```text
Reasoning

Local formatting

Pure transformation

Planning
```

과 같은 Side-effect-free Cognitive Operation은
Harness execution boundary를 거치지 않을 수 있다.

---

# 28. Boundary Focus

Harness가 특히 강하게 적용되는 영역:

```text
External Side Effect

Filesystem Mutation

Network Mutation

Credential Use

Artifact Mutation

External Publish

Destructive Operation

Runtime Lifecycle

Sandboxed Code Execution
```

---

# 29. Execution Request

Architecture-level Execution Request 후보:

```text
Execution Request
├── Request ID
├── Task Reference
├── Agent Reference
├── Capability ID
├── Capability Version
├── Input
├── Context Reference
├── Scope
├── Budget
├── Deadline
├── Permission Envelope
├── Approval Reference
├── Idempotency Information
└── Expected Result / Evidence
```

정확한 Schema는 Specification에서 결정한다.

---

# 30. Request ID

각 실행 요청은 가능한 경우 Stable Request ID를 가진다.

목적:

```text
Traceability

Retry

Idempotency

Recovery

Audit
```

---

# 31. Execution ID

Execution Request와 실제 Execution Attempt를 구분한다.

```text
Request ID
↓
Execution Attempt 1
↓
Execution ID 1
```

재시도하면:

```text
Request ID
├── Execution ID 1
└── Execution ID 2
```

가 가능하다.

---

# 32. Request vs Attempt

```text
Execution Request
= 수행하려는 logical operation

Execution Attempt
= 실제 수행 시도
```

둘을 동일시하지 않는다.

---

# 33. Execution Envelope

Harness가 실제 Runtime으로 전달하는 실행 정보를
Execution Envelope라고 표현할 수 있다.

후보:

```text
Execution Envelope
├── Execution ID
├── Task Reference
├── Capability Contract
├── Validated Input
├── Projected Context
├── Effective Permission
├── Budget
├── Deadline
├── Sandbox Profile
├── Credential Handles
├── Trace Context
└── Recovery Metadata
```

---

# 34. Effective Permission

Execution Envelope에 들어가는 Permission은
Agent가 주장한 Permission이 아니라
실제 Policy evaluation 결과여야 한다.

---

# 35. Permission Envelope

Delegation이나 Subagent에서는:

```text
Child Permission
⊆
Parent Effective Permission
```

원칙을 유지한다.

Harness는 Scope 확대를 자동 허용하지 않는다.

---

# 36. Permission Escalation Attempt

예:

```text
Parent:
read-only

Child Request:
write
```

이면 기본적으로:

```text
Reject
or
Explicit new approval path
```

를 사용한다.

---

# 37. Approval

Approval은 특정 Action에 대한 별도 실행 권위다.

```text
Capability
≠
Permission
≠
Approval
```

---

# 38. Approval Binding

Approval은 가능한 경우 다음과 결합된다.

```text
Action

Target

Scope

Principal

Time

Request

Risk
```

과거의 포괄적인 Approval을
무제한 재사용하지 않는다.

---

# 39. Approval Freshness

장기 Task에서는 Approval이 만료되거나
상황이 변경될 수 있다.

Critical execution 전에 유효성을 확인한다.

---

# 40. Fail Closed

High-risk Action에서:

```text
Permission unknown

Approval unavailable

Policy evaluation failed
```

상황은 기본적으로:

```text
Deny / Block / Ask
```

쪽으로 처리한다.

---

# 41. Capability Resolution

Agent가 요청한 Capability를 실제 Provider와 연결한다.

```text
Capability ID
↓
Capability Resolver
↓
Provider
```

---

# 42. Capability Resolver

후보 책임:

```text
Find Provider

Check Version

Validate Compatibility

Inspect Availability

Load Contract

Resolve Adapter
```

Harness가 이를 조정할 수 있다.

---

# 43. Capability Availability

Capability가 Registry에 존재한다고
현재 실행 가능하다는 의미는 아니다.

```text
Registered
≠
Available
≠
Authorized
```

---

# 44. Capability Contract Validation

실행 전 후보 검증:

```text
Input Schema

Required Scope

Side Effects

Timeout

Retryability

Idempotency

Runtime Requirements

Verification Requirements
```

---

# 45. Input Validation

Model Output을 바로 Infrastructure에 전달하지 않는다.

```text
Model Output
↓
Structured Request
↓
Contract Validation
↓
Execution
```

방향을 사용한다.

---

# 46. Invalid Request

Request가 Contract를 위반하면:

```text
Reject

Repair

Request clarification

Ask Agent to regenerate
```

중 하나를 선택한다.

---

# 47. Validation Is Not Authorization

```text
Valid Request
≠
Authorized Request
```

Schema가 맞아도 Permission이 없으면 실행하지 않는다.

---

# 48. Runtime Selection

필요한 경우 Capability에 맞는 Runtime을 선택한다.

후보:

```text
Local Python Runtime

Container Runtime

Shell Runtime

Browser Runtime

Remote Worker

Workflow Runtime
```

실제 선택 알고리즘은 Runtime Architecture에서 정의한다.

---

# 49. Runtime Adapter

Harness는 Runtime Interface를 사용한다.

```text
Harness
↓
Runtime Interface
↓
Runtime Adapter
↓
Runtime Implementation
```

---

# 50. Runtime Capabilities

Harness가 기대할 수 있는 Runtime-level operation 후보:

```text
Start

Execute

Observe

Pause

Resume

Cancel

Checkpoint

Terminate

Recover
```

---

# 51. Runtime Does Not Own Task

Harness와 Runtime 모두
Task Definition이나 canonical Task Progress를 소유하지 않는다.

```text
Task State
→ external durable authority
```

---

# 52. Sandbox Integration

위험한 Execution은 Sandbox를 사용할 수 있다.

```text
Harness
↓
Sandbox Profile
↓
Runtime
↓
Execution
```

---

# 53. Sandbox Profile

후보:

```text
Filesystem Scope

Network Scope

Process Limits

CPU

Memory

Time

Environment Variables

Credential Access

Write Permission
```

정확한 구현은 Security Architecture에서 결정한다.

---

# 54. Sandbox Is Not Harness

```text
Harness
≠
Sandbox
```

Harness는 Sandbox를 선택하거나
적용하도록 조정할 수 있다.

---

# 55. Credential Boundary

Agent나 Model이 Credential 자체를 직접 받지 않도록 한다.

```text
Agent
↓
Capability Request
↓
Harness
↓
Credential Broker
↓
External System
```

---

# 56. Credential Handle

Execution Envelope에는 Secret 값 대신
Credential Handle 또는 Capability-scoped reference를 사용할 수 있다.

---

# 57. Secret Exposure Rule

다음을 기본적으로 피한다.

```text
Secret
↓
Model Context
```

Credentials는 실행 계층에서 필요한 순간에만 사용한다.

---

# 58. Credential Scope

Credential 사용은 가능한 경우:

```text
Capability

Target

Scope

Duration

Principal
```

에 제한한다.

---

# 59. Environment

Runtime은 실제 Environment와 상호작용한다.

```text
Harness
↓
Runtime
↓
Sandbox
↓
Environment
```

Harness가 Environment State 전체를 소유하지 않는다.

---

# 60. Pre-execution Observation

Side Effect가 중요한 Action에서는
현재 Environment를 다시 확인할 수 있다.

예:

```text
Delete File

Publish Artifact

Modify Repository

Send External Message
```

---

# 61. Optimistic Assumption Risk

과거 Context에서:

```text
Target exists
```

라고 되어 있어도 실행 시점에는 바뀌었을 수 있다.

필요할 경우 precondition을 재검증한다.

---

# 62. Preconditions

Capability Contract가 Preconditions를 정의할 수 있다.

예:

```text
Expected Artifact Version

Expected File Hash

Expected Task Revision

Expected Repository Branch
```

---

# 63. Preconditions Prevent Stale Execution

예:

```text
Agent read Artifact v3

Meanwhile Artifact becomes v4

Agent attempts update based on v3
```

이면 Conflict를 탐지할 수 있어야 한다.

---

# 64. Execution Lifecycle

후보:

```text
Requested
↓
Validated
↓
Authorized
↓
Prepared
↓
Running
↓
Succeeded / Failed / Cancelled
↓
Verified if required
↓
Recorded
```

정확한 State Machine은 Specification에서 결정한다.

---

# 65. Prepared State

Prepared 단계에서는 후보적으로:

```text
Capability resolved

Permission checked

Approval validated

Runtime selected

Sandbox prepared

Credential handles prepared
```

가 완료된다.

---

# 66. Running

실제 Runtime이 Capability를 수행하는 상태다.

Running 상태에서도 Cancellation이나 Timeout이 발생할 수 있다.

---

# 67. Succeeded

Runtime Execution이 기술적으로 성공한 상태다.

하지만:

```text
Execution Succeeded
≠
Task Completed
```

이다.

---

# 68. Execution Success vs Verification

예:

```text
File write call succeeds
```

해도 요구한 내용이 실제 올바른지는
별도 Verification이 필요할 수 있다.

---

# 69. Failed

Execution Failure는 구조화된 Failure를 반환해야 한다.

후보:

```text
Failure
├── Category
├── Code
├── Message
├── Retryable
├── Recoverable
├── Partial Result
├── Side-effect Status
└── Evidence
```

---

# 70. Cancelled

Cancellation은 실패와 구분한다.

```text
Cancelled
≠
Failed
```

---

# 71. Timeout

Timeout도 별도 Failure 원인으로 추적한다.

후보:

```text
Preparation Timeout

Runtime Timeout

Capability Timeout

External Service Timeout
```

---

# 72. Cancellation

Harness는 Cancellation Request를 Runtime까지 전달할 수 있어야 한다.

```text
User / Orchestrator
↓
Cancellation
↓
Harness
↓
Runtime
↓
Capability
```

---

# 73. Cooperative Cancellation

가능한 경우 Runtime / Capability가
안전한 지점에서 종료하도록 한다.

---

# 74. Hard Termination

안전한 cooperative cancellation이 불가능하거나
위험이 커질 경우 Hard Termination이 필요할 수 있다.

그러나 이미 발생한 Side Effect는 사라지지 않는다.

---

# 75. Cancellation vs Rollback

```text
Cancel
≠
Rollback
```

이다.

---

# 76. Cancellation Evidence

Cancellation 이후에도:

```text
What executed?

What did not execute?

What side effects occurred?
```

를 추적할 수 있어야 한다.

---

# 77. Retry

Harness는 Retry를 수행하거나
상위 Agent / Orchestrator에 Retryable Failure를 반환할 수 있다.

---

# 78. Blind Retry Is Not Default

다음을 피한다.

```text
Failure
↓
Retry forever
```

Retry는:

```text
Retryability

Idempotency

Budget

Failure Type

Side-effect Status
```

를 고려한다.

---

# 79. Idempotency

Capability Contract에는 가능한 경우:

```text
Idempotent

Non-idempotent

Unknown
```

정보를 가진다.

---

# 80. Idempotency Key

외부 Service가 지원하는 경우
Logical Request에 Idempotency Key를 사용할 수 있다.

```text
Request ID
↓
Idempotency Key
↓
External API
```

---

# 81. Exactly-Once

Harness는 일반적인 외부 Side Effect에 대해
쉽게:

```text
Exactly Once
```

를 보장한다고 주장하지 않는다.

---

# 82. At-least-once Risk

Retry 과정에서 동일 Action이 두 번 실행될 수 있다.

따라서 Side-effect Record와
Environment reconciliation이 필요하다.

---

# 83. Side-effect Record

후보:

```text
Side-effect Record
├── Operation ID
├── Request ID
├── Execution ID
├── Capability
├── Target
├── Started At
├── Completed At
├── Outcome
├── Idempotency Key
├── Evidence
└── Compensation Status
```

---

# 84. Side-effect Record Ownership

Harness가 Side-effect tracking을 조정할 수 있지만
실제 Durable Record Store가 Harness 내부에 있어야 한다는 의미는 아니다.

---

# 85. Compensation

이미 발생한 Side Effect를 상쇄해야 할 수 있다.

예:

```text
Create temporary resource
↓
Later failure
↓
Delete temporary resource
```

---

# 86. Compensation Is Not Universal

모든 Side Effect가 되돌릴 수 있는 것은 아니다.

예:

```text
Email sent

External message published
```

따라서 실행 전 Approval과 Verification이 중요하다.

---

# 87. Recovery

Harness는 Runtime Failure 이후
복구 흐름을 연결한다.

후보:

```text
Runtime Failure
↓
Execution Record
+
Task State
+
Checkpoint
+
Artifacts
+
Side-effect Records
↓
Recovery Decision
↓
New Runtime
↓
Resume / Retry / Replan
```

---

# 88. Harness Does Not Own Recovery Strategy

Recovery Strategy 자체는
Task / Runtime / Orchestrator와 함께 결정될 수 있다.

Harness는 필요한 execution-level recovery mechanism을 제공한다.

---

# 89. Recovery vs Replanning

```text
Recovery
= execution continuity restoration

Replanning
= strategy change
```

둘을 구분한다.

---

# 90. Checkpoint Integration

Harness는 Runtime에 Checkpoint 생성을 요청하거나
Checkpoint Reference를 기록할 수 있다.

---

# 91. Checkpoint Contents

후보:

```text
Execution ID

Task State Reference

Current Step

Artifact References

Workspace Reference

Completed Operations

Pending Operations

Side-effect Records
```

---

# 92. Checkpoint Is Not Full Runtime Serialization

```text
Checkpoint
≠
Entire process memory dump
```

새 Runtime에서 재구성 가능한 최소 durable information을 우선한다.

---

# 93. Runtime Crash

예:

```text
Runtime A
↓
Crash
↓
Harness detects failure
↓
Execution record updated
↓
Task State preserved
↓
Recovery
↓
Runtime B
```

---

# 94. Partial Failure

Capability 실행 일부만 완료될 수 있다.

예:

```text
Step 1 succeeded

Step 2 succeeded

Step 3 failed
```

Harness는 Partial Result를 버리지 않는다.

---

# 95. Partial Result

후보:

```text
Completed operations

Generated artifacts

Observed side effects

Failure point

Remaining work
```

를 구조화해 반환한다.

---

# 96. Result Contract

Harness가 상위 Agent / Orchestrator에 전달하는 결과 후보:

```text
Execution Result
├── Request ID
├── Execution ID
├── Status
├── Output
├── Artifact References
├── Evidence References
├── Side-effect Records
├── Failure
├── Retryability
├── Runtime Metadata
└── Provenance
```

---

# 97. Raw Result vs Agent-facing Result

Capability Raw Output 전체를
Model Context에 그대로 넣을 필요는 없다.

```text
Raw Execution Result
↓
Result Projection
↓
Agent
```

을 사용할 수 있다.

---

# 98. Evidence

Harness는 실행 중 Evidence를 수집하거나
Evidence Reference를 연결할 수 있다.

예:

```text
Exit Code

File Hash

API Response Metadata

Artifact Version

Test Result

Environment Observation
```

---

# 99. Harness Does Not Decide Truth Alone

Harness가 실행 결과를 수집했다고
Task 요구사항이 만족되었다는 의미는 아니다.

```text
Execution Result
↓
Evidence
↓
Verification
```

흐름을 유지한다.

---

# 100. Verification Hook

Capability 또는 Task가 Verification을 요구하면
Harness는 Verification 호출 지점을 제공할 수 있다.

```text
Execution
↓
Evidence
↓
Verification Hook
↓
Verifier
```

---

# 101. Harness vs Verification

```text
Harness
≠
Verifier
```

Harness는 Verification을 호출하거나
결과를 전달할 수 있다.

---

# 102. Verification Failure

Execution은 성공했지만 Verification이 실패할 수 있다.

```text
Execution = Success

Verification = Fail
```

이 경우 Task를 완료로 처리하지 않는다.

---

# 103. Inconclusive Verification

Verification 결과는:

```text
Pass

Fail

Inconclusive
```

를 가질 수 있다.

Inconclusive를 억지로 Pass로 바꾸지 않는다.

---

# 104. Observability

Harness는 실행 Boundary이므로
Observability의 중요한 지점이다.

후보:

```text
Trace ID

Task ID

Session ID

Agent ID

Request ID

Execution ID

Capability ID

Runtime ID

Artifact IDs

Verification ID
```

---

# 105. Execution Trace

후보:

```text
Agent
↓
Request
↓
Harness
↓
Policy
↓
Permission
↓
Runtime
↓
Capability
↓
Result
↓
Verification
```

을 하나의 Trace로 연결한다.

---

# 106. Trace Propagation

Harness가 새 Runtime이나 Adapter를 호출해도
Trace Context를 가능한 범위에서 유지한다.

---

# 107. Logging

중요 Event 후보:

```text
ExecutionRequested

ExecutionValidated

ExecutionAuthorized

ExecutionStarted

ExecutionSucceeded

ExecutionFailed

ExecutionCancelled

ExecutionRecovered

CapabilityResolved

PermissionDenied

ApprovalRequired

SideEffectRecorded
```

---

# 108. Logging vs State

Log가 canonical Execution State 자체는 아니다.

```text
Log
≠
State
```

---

# 109. Audit

특히 다음은 Audit 대상이 될 수 있다.

```text
High-risk Capability

Permission Decision

Approval

Credential Use

External Publish

Destructive Action

Side Effect

Recovery

Privilege Escalation Attempt
```

---

# 110. Audit Integrity

중요 Audit Record는 일반 Agent가 임의로 삭제하거나
변경할 수 없도록 제한할 수 있다.

---

# 111. Metrics

Harness-level Metric 후보:

```text
Execution Count

Success Rate

Failure Rate

Permission Denial Rate

Retry Count

Recovery Rate

Latency

Capability Latency

Runtime Startup Time

Cancellation Success

Side-effect Reconciliation Count
```

---

# 112. Harness Evaluation

Harness 품질 후보:

```text
Reliability

Security

Recoverability

Replaceability

Observability

Contract Compliance

Failure Isolation

Latency

Operational Complexity
```

---

# 113. Security Evaluation

확인할 질문:

```text
Can Agent bypass permission?

Can Agent access raw credentials?

Can unauthorized capability execute?

Can stale approval be reused?

Can child permission exceed parent?

Can external content alter execution policy?
```

---

# 114. Recovery Evaluation

후보:

```text
Runtime crash

Tool crash

Network failure

Partial side effect

State commit failure

Verification failure
```

상황을 시뮬레이션한다.

---

# 115. Harness and Context Security

Harness는 Agent가 요청하는 추가 Context / Artifact access가
Scope를 벗어나지 않는지 확인할 수 있다.

하지만 Context filtering semantics 자체는 Context Architecture가 담당한다.

---

# 116. Harness and State Security

Agent가:

```text
Task = Completed
```

로 직접 overwrite 요청하는 것을 허용하지 않는다.

State Transition Contract를 사용한다.

---

# 117. Harness and Artifact Security

Artifact Operation 후보:

```text
Read

Create

Modify

Delete

Publish

Share
```

각각 별도 Permission을 요구할 수 있다.

---

# 118. Harness and Network

Network Access를 Capability / Sandbox Policy로 제한할 수 있다.

예:

```text
No Network

Allowlisted Domains

Read-only Network

External Mutation Allowed
```

---

# 119. Harness and Filesystem

Filesystem 접근도 Scope를 제한할 수 있다.

예:

```text
Read-only workspace

Specific project directory

Temporary sandbox only
```

---

# 120. Harness and Process Execution

Shell / Code Execution은 높은 위험을 가질 수 있다.

따라서:

```text
Capability Contract

Sandbox

Resource Limits

Permission

Observability
```

를 결합한다.

---

# 121. Resource Budget

Harness는 Runtime Execution Budget을 전달하거나 Enforcement를 지원한다.

후보:

```text
Time

CPU

Memory

Network

Tool Calls

External Cost

Storage
```

---

# 122. Budget Enforcement

Agent가 Budget을 인식하더라도
실제 Enforcement는 execution layer에서도 수행한다.

```text
Agent awareness
+
Harness / Runtime enforcement
```

---

# 123. Deadline

Execution Request는 Deadline을 가질 수 있다.

```text
Task Deadline
≠
Execution Timeout
```

둘을 구분한다.

---

# 124. Timeout Enforcement

Runtime / Capability마다 Timeout을 적용할 수 있다.

Timeout 발생 후 Side Effect가 존재하는지 확인해야 한다.

---

# 125. Rate Limits

External Capability가 Rate Limit을 가질 수 있다.

Harness 또는 Provider Adapter가:

```text
Backoff

Retry-after

Budget accounting
```

을 지원할 수 있다.

---

# 126. Provider Failure

External Provider가 실패하면:

```text
Provider Failure
↓
Structured Failure
↓
Retry / Fallback / Replan
```

로 처리한다.

---

# 127. Provider Fallback

동일 Capability에 여러 Provider가 있을 수 있다.

```text
Capability
├── Provider A
└── Provider B
```

하지만 Fallback이 semantic equivalence를 보장한다고 가정하지 않는다.

---

# 128. Compatibility Check

Provider 변경 전:

```text
Input compatibility

Output semantics

Permission

Side effects

Verification
```

을 확인할 수 있다.

---

# 129. Adapter Principle

Harness Architecture는 Adapter를 통해 외부 구현과 연결한다.

```text
Harness Contract
↓
Adapter
↓
Technology
```

---

# 130. Adapter Candidates

후보:

```text
Runtime Adapter

Capability Adapter

MCP Adapter

Workflow Adapter

Sandbox Adapter

Credential Adapter

Observability Adapter
```

---

# 131. Protocol Independence

Harness는 특정 Protocol을 Core Architecture로 고정하지 않는다.

예:

```text
Internal Calls

HTTP / RPC

MCP

Message Queue

Future Protocol
```

---

# 132. Contract vs Protocol

```text
Harness Contract
= semantic execution obligations

Protocol
= how requests are transported
```

---

# 133. Local Execution

초기 Modular Monolith에서는:

```text
Agent
↓
In-process Harness Interface
↓
Runtime Adapter
```

처럼 단순하게 시작할 수 있다.

---

# 134. Distributed Execution

향후 필요할 경우:

```text
Harness
↓
Queue / RPC
↓
Remote Runtime
```

으로 확장할 수 있다.

하지만 초기부터 Distributed Harness를 요구하지 않는다.

---

# 135. Logical vs Physical Harness

중요:

```text
Logical Harness Boundary
≠
One Harness Service
```

Harness는 여러 Interface / Guard / Adapter의 조합으로 구현될 수 있다.

---

# 136. Avoid God Harness

다음을 피한다.

```text
Harness
├── owns Memory
├── owns Database
├── owns Policy
├── owns Runtime
├── owns Artifacts
├── owns Identity
└── owns Orchestration
```

Harness는 이들을 **조정하고 연결**한다.

---

# 137. Harness as Boundary, Not Container

핵심:

> Harness는 모든 시스템을 담는 Container가 아니라,
> Agent가 Infrastructure를 사용할 때 반드시 지켜야 하는 Stable Boundary다.

---

# 138. Ports Candidate

Logical Port 후보:

```text
ContextPort

StatePort

CapabilityPort

PolicyPort

PermissionPort

ApprovalPort

RuntimePort

CredentialPort

ArtifactPort

ObservabilityPort

VerificationPort
```

실제 구현에서 모두 별도 Interface가 되어야 한다는 의미는 아니다.

---

# 139. Interface Explosion Risk

너무 많은 Port / Adapter를 만들면
v0.1 구현이 불필요하게 복잡해질 수 있다.

따라서:

```text
Conceptual Boundary
≠
One interface per concept
```

원칙을 유지한다.

---

# 140. Initial Harness Surface

첫 PoC에서는 최소한:

```text
Execute Capability

Validate Request

Authorize Execution

Track Execution

Cancel Execution

Recover Execution
```

정도의 작은 Interface로 시작할 수 있다.

---

# 141. Candidate Harness Interface

개념적 후보:

```text
execute(request)

cancel(execution_id)

status(execution_id)

recover(execution_id)
```

정확한 API는 Specification 단계에서 결정한다.

---

# 142. Internal Pipeline Candidate

`execute()` 내부의 logical flow 후보:

```text
Validate
↓
Resolve
↓
Authorize
↓
Prepare
↓
Execute
↓
Record
↓
Return
```

필요한 경우:

```text
Verify
```

를 추가한다.

---

# 143. Harness and Multi-Agent

모든 Agent는 동일한 execution safety boundary를 사용한다.

```text
Root Agent
↓
Harness

Child Agent
↓
Harness
```

Child Agent가 별도의 우회 실행 경로를 가지지 않는다.

---

# 144. Delegation

Orchestrator 또는 Parent Agent가 Child Agent를 사용할 경우:

```text
Delegation Contract
↓
Child Agent
↓
Capability Request
↓
Harness
```

형태를 유지한다.

---

# 145. Child Execution Envelope

Child에는:

```text
Scoped Context

Scoped Capability Set

Scoped Permission

Scoped Budget

Scoped Artifact Access
```

만 제공한다.

---

# 146. Parent Authority

Parent Agent 자체가 실제 Security Authority라는 의미는 아니다.

Parent가 Child에게 권한을 위임하더라도
Harness / Policy가 최종 Effective Permission을 검증한다.

---

# 147. Agent-as-Tool

Agent-as-Tool 패턴에서도
Child의 actual capability execution은 Harness를 통과한다.

```text
Parent
↓
Child Agent
↓
Harness
↓
Capability
```

---

# 148. Handoff

Agent Handoff가 발생해도
새 Agent가 동일한 execution boundary를 사용한다.

Harness Contract는 Agent identity 변경과 독립적이다.

---

# 149. Harness and Identity

Harness는 Identity / Principal Reference를
Authorization에 사용할 수 있다.

하지만:

```text
Harness
≠
Identity Store
```

이다.

---

# 150. Identity Projection vs Principal

Agent Context에 제공된 Identity Projection과
Security Principal을 구분할 수 있다.

```text
Identity Projection
= model-facing identity context

Principal
= authorization identity
```

둘이 연관되지만 동일한 representation일 필요는 없다.

---

# 151. Identity Does Not Grant Unlimited Authority

Root Identity라고 해서:

```text
Allow Everything
```

을 의미하지 않는다.

Policy와 Permission을 유지한다.

---

# 152. Harness and Session

Session ID는 Trace / Interaction Scope로 사용할 수 있다.

그러나 Harness 실행은 항상 Session을 요구하지 않을 수 있다.

---

# 153. Background Execution

Background Task:

```text
Task
↓
Harness
↓
Runtime
```

처럼 Interactive Session 없이 실행될 가능성을 유지한다.

정확한 Session requirement는 Runtime Specification에서 결정한다.

---

# 154. Harness and Task

Harness는 Task Reference를 실행의 correlation과 constraints에 사용한다.

하지만 Task Goal 해석은 Agent / Orchestrator가 담당한다.

---

# 155. Task State Revalidation

Critical execution 직전:

```text
Expected Task Revision
vs
Current Task Revision
```

을 비교할 수 있다.

Stale Task 기반 실행을 방지한다.

---

# 156. Harness and Artifact

Artifact mutation은 가능한 경우:

```text
Artifact ID

Expected Version

Operation

Scope
```

를 명시한다.

---

# 157. Artifact Concurrency

예:

```text
Agent read Artifact v3
↓
Artifact becomes v4
↓
Agent requests write based on v3
```

이면 Version Conflict를 탐지할 수 있어야 한다.

---

# 158. Harness and Knowledge / Memory

일반적인 Memory / Knowledge Retrieval은
Context Manager를 통해 이루어지는 것을 우선한다.

Harness가 Retrieval semantics를 직접 결정하지 않는다.

---

# 159. Direct Retrieval Capability

Memory / Knowledge 조회 자체가 Capability로 제공될 수도 있다.

그 경우에도 Scope / Permission을 적용한다.

---

# 160. Harness and Learning

Harness는 execution evidence를 Learning pipeline에 제공할 수 있다.

```text
Execution
↓
Observability / Evidence
↓
Evaluation
↓
Learning
```

하지만 Harness가 스스로 Policy나 Architecture를 변경하지 않는다.

---

# 161. Self-modification Boundary

Harness 구현을 Agent가 직접 수정하고 즉시 적용하는 구조를 기본적으로 허용하지 않는다.

후보:

```text
Improvement Proposal
↓
Evaluation
↓
Governance
↓
Deployment
```

를 거친다.

---

# 162. Harness Versioning

Harness Contract는 Version을 가질 수 있다.

```text
Harness Contract v1
↓
Harness Contract v2
```

---

# 163. Contract Version vs Implementation Version

```text
Harness Contract Version
≠
Harness Implementation Version
≠
Runtime Version
```

을 구분한다.

---

# 164. Backward Compatibility

가능한 경우 additive change를 우선한다.

Breaking change는 explicit version bump와 migration을 요구한다.

---

# 165. Runtime Compatibility

새 Runtime Adapter는 기존 Harness Contract를 만족하는지
Contract Test를 수행할 수 있다.

---

# 166. Capability Compatibility

새 Capability Provider 역시:

```text
Input semantics

Output semantics

Side-effect declaration

Permission requirements

Failure semantics
```

을 만족하는지 검증할 수 있다.

---

# 167. Contract Testing

후보:

```text
Harness
↕
Runtime Adapter Contract Test
```

```text
Harness
↕
Capability Adapter Contract Test
```

를 사용한다.

---

# 168. Failure Categories

Harness-level Failure 후보:

```text
Invalid Request

Capability Not Found

Capability Incompatible

Permission Denied

Approval Required

Approval Expired

Runtime Unavailable

Sandbox Failure

Credential Failure

Execution Failure

Timeout

Cancellation

Side-effect Conflict

Verification Failure

Recovery Failure

Unknown
```

---

# 169. Structured Failure

Failure를 단순 문자열로만 반환하지 않는다.

```text
Failure
├── Type
├── Code
├── Message
├── Request ID
├── Execution ID
├── Retryable
├── Recoverable
├── Partial Result
├── Side-effect Status
└── Evidence References
```

---

# 170. Failure Attribution

다음을 구분할 수 있어야 한다.

```text
Agent Request Error

Capability Error

Policy Error

Permission Error

Runtime Error

Environment Error

Provider Error

Verification Error

Harness Error
```

---

# 171. Harness Failure

Harness 자체가 실패할 수도 있다.

예:

```text
Contract validation bug

Execution record unavailable

Adapter routing failure

Authorization integration failure
```

Harness를 "절대 실패하지 않는 Layer"로 가정하지 않는다.

---

# 172. Harness Failure Isolation

Harness 일부 Adapter failure가
다른 unrelated execution에 영향을 주지 않도록 한다.

초기 Modular Monolith에서도 logical isolation을 유지한다.

---

# 173. Degraded Mode

일부 Infrastructure가 unavailable한 경우
제한된 Capability만 사용할 수 있다.

예:

```text
Network unavailable
↓
Local read-only capabilities remain
```

정확한 degraded-mode policy는 추후 결정한다.

---

# 174. Safe Failure

High-risk capability에서 Harness uncertainty가 발생하면
안전하게 실패하는 방향을 우선한다.

```text
Unsure
→ Do not mutate
```

---

# 175. Observability Failure

Telemetry Backend 장애가 발생했다고
모든 low-risk execution을 반드시 중지해야 하는지는 Policy에 따라 달라질 수 있다.

하지만 Critical Audit가 요구되는 Action은
Audit 기록 불가능 시 Block할 수 있다.

---

# 176. Audit-required Execution

예:

```text
Destructive action

External publish

Identity-related change

Permission-sensitive action
```

은 required audit availability를 Preconditions로 둘 수 있다.

---

# 177. Harness Privacy

Execution Request와 Result에는 민감 정보가 포함될 수 있다.

따라서:

```text
Minimize logs

Redact secrets

Reference large artifacts

Scope observability access
```

원칙을 사용한다.

---

# 178. Sensitive Input

Capability Input에 Secret이 필요하다면
Secret Handle 방식 등을 우선한다.

Raw Secret을 Execution Trace에 남기지 않는다.

---

# 179. Result Redaction

External Provider가 민감한 정보를 반환할 수 있다.

Agent-facing Result Projection 전에
Policy 기반 filtering을 적용할 수 있다.

---

# 180. Harness Retention

Execution Record retention은:

```text
Recovery

Audit

Debugging

Evaluation

Privacy

Storage cost
```

를 고려한다.

---

# 181. Execution Record

Durable Execution Record 후보:

```text
Execution Record
├── Execution ID
├── Request ID
├── Task ID
├── Agent ID
├── Capability ID
├── Runtime ID
├── Status
├── Started At
├── Ended At
├── Result References
├── Evidence References
├── Side-effect References
├── Failure
└── Trace Reference
```

---

# 182. Execution Record vs Execution State

```text
Execution State
= current execution condition

Execution Record
= durable historical / recovery record
```

로 구분할 수 있다.

---

# 183. Execution Record Persistence

Execution Record는 Runtime memory보다 오래 지속될 수 있어야 한다.

Recovery와 Audit에서 사용한다.

---

# 184. Harness Recovery Source

Recovery 후보 Source:

```text
Task State

Execution Record

Checkpoint

Artifact References

Side-effect Records

Current Environment Observation
```

---

# 185. Recovery Authority

Recovery 과정에서 이전 Agent의 자연어 설명만을
Source of Truth로 사용하지 않는다.

Durable evidence와 State를 우선한다.

---

# 186. Recovery Decision

후보:

```text
Resume

Retry

Re-execute

Compensate

Replan

Escalate

Abort
```

Harness는 execution feasibility를 지원하고
상위 Agent / Orchestrator가 strategy를 결정할 수 있다.

---

# 187. Recovery Safety

재실행 전 반드시:

```text
Did side effect already occur?

Is request idempotent?

Has target changed?

Is permission still valid?
```

를 확인할 수 있어야 한다.

---

# 188. Harness In-process Candidate

초기 Modular Monolith 후보:

```text
Agent Module
    ↓
Harness Interface
    ↓
Application Services
    ↓
Adapters
    ↓
Infrastructure
```

---

# 189. No Mandatory Harness Microservice

초기에는:

```text
Harness Service
```

를 별도 network service로 만들 필요가 없다.

Logical Boundary만 유지한다.

---

# 190. Future Physical Separation

다음 요구가 생길 경우 분리를 검토한다.

```text
Remote execution

Strong process isolation

Independent scaling

Security isolation

Multiple runtime workers

Cross-device execution
```

---

# 191. Harness Centralization Risk

Harness를 너무 중앙화하면:

```text
God Object

Performance bottleneck

Complex dependency graph

Large blast radius

Hard testing
```

문제가 생길 수 있다.

---

# 192. Centralization Mitigation

Harness는 하나의 거대한 Class보다:

```text
Stable Facade / Contract
+
Focused Services
+
Adapters
```

방향을 고려한다.

---

# 193. Policy Enforcement Must Not Be Optional

구현이 분산되더라도
Agent가 Infrastructure로 우회할 수 있는
비인가 path를 만들지 않는다.

---

# 194. Bypass Prevention

예:

```text
Agent
↓
Direct filesystem library
```

를 임의로 호출하는 구조보다:

```text
Agent
↓
Capability
↓
Harness Boundary
↓
Filesystem Adapter
```

를 사용한다.

---

# 195. Trusted Internal Components

모든 internal code가 같은 security level이라고 가정하지 않는다.

Component 간에도 명시적 responsibility boundary를 유지한다.

---

# 196. Testability

Harness는 외부 Infrastructure를 Adapter 뒤에 두므로
Test Double을 사용할 수 있다.

예:

```text
Fake Runtime

Fake Capability

Fake Permission Service

Fake Environment
```

---

# 197. Deterministic Harness Tests

Model 없이도 다음을 테스트할 수 있어야 한다.

```text
Invalid request rejected

Permission denial enforced

Timeout handled

Retry constrained

Cancellation propagated

Side-effect record created

Runtime replacement works
```

---

# 198. Security Regression Tests

후보:

```text
Privilege escalation blocked

Credential not exposed

Expired approval rejected

Cross-scope artifact access blocked

Child permission bounded

Direct bypass prevented
```

---

# 199. Recovery Regression Tests

후보:

```text
Crash before execution

Crash during execution

Crash after side effect

Crash before state commit

Crash after artifact creation
```

을 각각 검증한다.

---

# 200. Initial Implementation Candidate

첫 PoC에서는 Harness 전체 기능을 구현하지 않는다.

최소:

```text
ExecutionRequest

Harness.execute()

Capability Resolution

Input Validation

Permission Check

Runtime Adapter

Execution Record

Structured Result

Basic Cancellation

Basic Recovery Metadata

Trace ID
```

정도로 시작한다.

---

# 201. Initial Security Candidate

최소 Security:

```text
Allow / Ask / Deny

Capability Scope

Basic Approval

No raw credentials in model context

Filesystem scope
```

정도로 시작할 수 있다.

---

# 202. Initial Runtime Candidate

첫 PoC에서는 하나의 Local Runtime만 사용할 수 있다.

중요한 것은:

```text
Harness
≠
Local Runtime
```

경계를 코드로 유지하는 것이다.

---

# 203. Initial Capability Candidate

단순 Capability 후보:

```text
Read Artifact

Write Artifact

Run deterministic validation
```

정도로 Harness Contract를 먼저 검증할 수 있다.

---

# 204. Minimal Harness PoC

```text
1. Task 생성

2. Agent가 Capability Request 생성

3. Harness가 Request 수신

4. Contract Validation

5. Capability Resolution

6. Permission Check

7. Runtime 준비

8. Capability 실행

9. Execution Record 생성

10. Result / Evidence 반환

11. Verification

12. Task State Transition
```

---

# 205. Permission Denial PoC

```text
Agent requests write
↓
Permission = read-only
↓
Harness blocks execution
↓
Structured PermissionDenied
```

을 검증한다.

---

# 206. Invalid Contract PoC

```text
Malformed Capability Request
↓
Harness validation
↓
Rejected
↓
Infrastructure never called
```

을 검증한다.

---

# 207. Credential Isolation PoC

```text
Agent
↓
Capability Request
↓
Harness
↓
Credential Handle
↓
External Provider
```

에서 Agent / Model Context에 Raw Secret이 노출되지 않는지 확인한다.

---

# 208. Runtime Replacement PoC

```text
Agent
↓
Harness
↓
Runtime A
```

를:

```text
Agent
↓
Harness
↓
Runtime B
```

로 바꿔도 Agent Contract가 유지되는지 검증한다.

---

# 209. Runtime Crash PoC

```text
Execution
↓
Runtime Crash
↓
Execution Record
+
Task State
↓
New Runtime
↓
Recovery
```

를 검증한다.

---

# 210. Side-effect Crash PoC

중요 시나리오:

```text
External Action succeeds
↓
Runtime crashes before Task State commit
↓
Recovery
↓
Side-effect detection
↓
Duplicate action prevented
```

를 검증한다.

---

# 211. Cancellation PoC

```text
Long-running Execution
↓
Cancel Request
↓
Harness
↓
Runtime cancellation
↓
Execution Record = Cancelled
```

을 검증한다.

---

# 212. Verification Failure PoC

```text
Execution = Success
↓
Verification = Fail
↓
Task must not become Completed
```

를 확인한다.

---

# 213. Child Permission PoC

```text
Parent Permission = read

Child requests write

↓
Harness / Policy
↓
Denied
```

를 검증한다.

---

# 214. Stale State PoC

```text
Request expects Task Revision 5

Current Revision = 6

↓
Harness detects stale precondition
↓
Execution blocked / refreshed
```

를 검증한다.

---

# 215. Artifact Version Conflict PoC

```text
Expected Artifact v2

Current Artifact v3

↓
Mutation request
↓
Conflict
```

를 검증한다.

---

# 216. Approval Expiration PoC

```text
Approval granted

Time / scope changes

Execution attempted later

↓
Approval invalid
↓
Block / re-request
```

를 확인한다.

---

# 217. Harness Evaluation Metrics

초기 후보:

```text
Execution success rate

Contract rejection rate

Permission denial correctness

Recovery success rate

Duplicate side-effect rate

Cancellation latency

Runtime replacement success

Trace completeness

Security violations

Harness overhead
```

---

# 218. Acceptance Criteria

Harness Architecture v0.1은 최소 다음을 만족해야 한다.

```text
Agent does not directly own Infrastructure.

Harness is distinguishable from Agent.

Harness is distinguishable from Runtime.

Harness is distinguishable from Orchestrator.

Harness does not own canonical Task State.

Harness does not own Identity Core.

Harness can validate structured execution requests.

Harness can resolve Capabilities through stable contracts.

Capability availability does not imply Permission.

Execution-time Permission can be enforced outside Agent reasoning.

Raw Credentials are not exposed to the Model by default.

Runtime implementations can be replaced behind a stable interface.

Important Executions can be traced.

Runtime failure does not destroy durable Task State.

Side Effects can be tracked for recovery.

Cancellation can propagate to Runtime.

Verification remains distinct from Execution success.

Child Agent permissions cannot silently exceed Parent permissions.

Harness does not require a separate microservice in v0.1.
```

---

# 219. Architecture Invariants

```text
Harness must not become the Agent.

Harness must not become the Orchestrator.

Harness must not become the Runtime.

Harness must not become the Policy authority.

Harness must not become the Identity source of truth.

Harness must not become the Task State source of truth.

Agent must not bypass critical execution enforcement.

Capability discovery must not imply execution authorization.

Valid input must not imply authorized execution.

Permission must be revalidated when required.

Raw credentials must not be passed to the Model by default.

Runtime-specific implementation must remain replaceable.

Execution success must not automatically equal Task completion.

Side effects must remain observable across Runtime failure.

Retry must not ignore idempotency and side-effect state.

Child permissions must not exceed effective delegated authority.

Harness must remain a logical boundary rather than a mandatory God Service.
```

---

# 220. Stable Boundaries

현재 안정적으로 유지할 후보:

```text
Agent / Infrastructure boundary

Harness / Runtime separation

Harness / Orchestrator separation

Execution Request contract

Capability resolution boundary

Policy / Permission enforcement integration

Runtime abstraction

Credential boundary

Side-effect tracking

Recovery integration

Observability integration

Verification separation
```

---

# 221. Replaceable Implementations

다음은 교체 가능해야 한다.

```text
Runtime implementation

Capability framework

Tool framework

Sandbox technology

Credential broker

Policy engine

Permission backend

Approval backend

Observability backend

Transport

Protocol

Queue

Execution worker

Harness internal implementation
```

---

# 222. Deferred Decisions

현재 최종 결정하지 않는다.

```text
Exact Harness API

Exact Execution Request Schema

Exact Execution Result Schema

Exact Runtime Interface

Exact Capability Registry

Exact Policy Engine

Exact Permission Model

Exact Approval UI

Exact Sandbox

Exact Credential Broker

Exact Retry Policy

Exact Timeout Policy

Exact Recovery Engine

Exact Checkpoint Schema

Exact Execution Record Schema

Exact Side-effect Schema

Exact Transport

MCP adoption

A2A adoption

Remote worker architecture

Distributed Harness topology

Separate Harness Service
```

---

# 223. Related Architecture

본 문서는 다음 Architecture와 연결된다.

```text
System Architecture

Identity Architecture

Agent Architecture

Task Architecture

Session Architecture

State Architecture

Context Architecture

Runtime Architecture

Capability Architecture

Artifact Architecture

Security Architecture

Orchestration Architecture

Verification Architecture

Observability Architecture

Evaluation Architecture
```

---

# 224. Related Decisions

핵심 Decision:

```text
DDR-002
Harness Boundary
```

강하게 연결되는 Decision:

```text
DDR-001
Task State / Runtime Boundary

DDR-006
Orchestration Contract
```

추가 관련 Decision:

```text
DDR-003
Memory / Knowledge Boundary

DDR-004
Artifact Architecture

DDR-005
Identity Persistence
```

---

# 225. Specification Questions

후속 Specification에서 결정해야 할 질문:

```text
What is the minimum Harness interface?

What is the minimum Execution Request schema?

What is the Execution Result schema?

How are Request ID and Execution ID represented?

How is Capability resolution performed?

Where exactly is Policy evaluated?

How is effective Permission represented?

How are Approvals bound to Actions?

How are Credentials represented without exposing secrets?

What Runtime interface does Harness require?

How is Sandbox configuration represented?

What is an Execution Record?

Which Execution metadata must be durable?

How are Side Effects recorded?

How is idempotency represented?

When may Harness automatically retry?

When must recovery escalate to Agent or Orchestrator?

How is cancellation propagated?

How are checkpoints requested and stored?

How are stale State and Artifact versions detected?

How are Trace IDs propagated?

Which operations require Audit?

How are Child permissions constrained?

Which execution paths must pass through Harness?

Can read-only Information retrieval bypass the Harness facade while preserving the same security boundary?

When would Harness justify physical service separation?
```

---

# 226. Architecture Boundary

본 문서는 Harness의 Logical Architecture를 정의한다.

다음은 아직 정의하지 않는다.

```text
Concrete Python Classes

Exact Package Layout

Exact Database Tables

Exact API Endpoints

Exact Runtime Framework

Exact Tool Framework

Exact Sandbox

Exact Policy Library

Exact Queue

Exact RPC Protocol

Exact Deployment Topology
```

---

# 227. Initial Design Preference

Harness Architecture v0.1에서는 다음을 우선한다.

```text
Small Stable Interface

Structured Execution Request

Contract Validation

Explicit Permission

Simple Runtime Adapter

Observable Execution

Durable Execution Metadata

Side-effect Awareness

Recoverable Failure

No Raw Credentials in Model Context

Modular Monolith
```

---

# 228. What Harness Architecture Must Avoid

특히 다음 구조를 피한다.

```text
Agent directly calls arbitrary infrastructure
```

```text
Harness owns every subsystem
```

```text
Permission is only a prompt instruction
```

```text
Raw credentials are injected into Model Context
```

```text
Runtime implementation leaks into Agent contract
```

```text
Tool success automatically completes Task
```

```text
Blind retry after unknown side effect
```

```text
One giant Harness class with every responsibility
```

```text
Child Agent gets unrestricted Parent authority
```

```text
Separate microservice before there is a real need
```

---

# 229. Candidate Harness Flow

```text
                  AGENT / ORCHESTRATOR
                          │
                          ↓
                  EXECUTION REQUEST
                          │
                          ↓
                       HARNESS
                          │
                          ↓
                 CONTRACT VALIDATION
                          │
                          ↓
                CAPABILITY RESOLUTION
                          │
                          ↓
               POLICY / PERMISSION
                          │
                          ↓
                   APPROVAL CHECK
                   if required
                          │
                          ↓
                   RUNTIME SELECT
                          │
                          ↓
                  SANDBOX / CREDS
                          │
                          ↓
                      EXECUTION
                          │
             ┌────────────┴────────────┐
             │                         │
             ↓                         ↓
          RESULT                  SIDE EFFECT
             │                         │
             └────────────┬────────────┘
                          ↓
                       EVIDENCE
                          │
                          ↓
                    VERIFICATION
                          │
                          ↓
               STATE TRANSITION REQUEST
```

---

# 230. Candidate Responsibility Boundary

```text
AGENT
└── decides what action is desirable

ORCHESTRATOR
└── decides coordination structure

HARNESS
└── mediates selected execution

POLICY / PERMISSION
└── determines whether execution is allowed

RUNTIME
└── manages execution lifecycle

SANDBOX
└── constrains execution environment

CAPABILITY
└── performs the actual operation

VERIFICATION
└── determines whether required outcome is satisfied
```

---

# 231. Candidate Recovery Flow

```text
Execution
   ↓
Runtime Failure
   ↓
Harness detects failure
   ↓
Execution Record
+
Side-effect Record
+
Task State
+
Checkpoint
+
Artifact References
   ↓
Reconciliation
   ↓
Recovery Decision
   ├── Resume
   ├── Retry
   ├── Replan
   ├── Compensate
   └── Escalate
```

---

# 232. Candidate Multi-Agent Flow

```text
Parent Agent
     │
     ↓
Orchestrator
     │
     ↓
Delegation Contract
     │
     ↓
Child Agent
     │
     ↓
Scoped Execution Request
     │
     ↓
Harness
     │
     ↓
Policy / Permission
     │
     ↓
Runtime
```

Child Agent 역시 Harness Boundary를 우회하지 않는다.

---

# 233. Candidate Physical Architecture v0.1

초기에는:

```text
NOAH Modular Monolith
│
├── Agent
│
├── Harness Interface
│
├── Application Services
│   ├── Capability
│   ├── Permission
│   ├── State
│   └── Execution
│
└── Infrastructure Adapters
    ├── Runtime
    ├── Filesystem
    ├── Database
    └── External API
```

정도로 시작할 수 있다.

이는 실제 Source Folder를 확정하는 Diagram이 아니다.

---

# 234. Evolution Direction

향후 필요하다면:

```text
In-process Harness
        ↓
Remote Runtime Adapter
        ↓
Worker Pool
```

또는:

```text
Harness Boundary
↓
Execution Gateway
↓
Distributed Runtimes
```

로 발전할 수 있다.

Stable Contract가 유지된다면
Agent Architecture는 크게 바뀌지 않아야 한다.

---

# 235. Current Architecture Statement

> Project NOAH의 Harness는 Agent와 Infrastructure 사이의
> Stable Execution Boundary다.
>
> Agent나 Orchestrator가 선택한 실행 요청을 받아
> Contract를 검증하고,
> Capability를 resolve하며,
> Policy, Permission 및 Approval을 거치도록 하고,
> 적절한 Runtime과 Sandbox를 통해 실제 실행으로 연결한다.
>
> Harness는 Context, State, Policy, Permission, Runtime,
> Credential, Observability 및 Verification과 연결되지만
> 이 시스템들의 Source of Truth나 소유자가 아니다.
>
> Execution은 Request와 Attempt를 구분하여 추적하고,
> Side Effect, Cancellation, Retry, Checkpoint 및 Recovery를
> 명시적으로 다룰 수 있어야 한다.
>
> Harness는 특정 Agent Framework, Runtime, Protocol 또는 Tool System보다
> 안정적인 Architecture Boundary로 유지되며,
> 초기에는 Modular Monolith 내부의 논리적 경계로 구현한다.

---

# 236. Final Principle

> **Harness는 NOAH가 무엇을 생각해야 하는지를 결정하는 두뇌가 아니다.**
>
> **Harness는 NOAH가 결정한 행동이 실제 세계와 만나는 순간,
> 그 행동이 허용되고, 추적되고, 제한되고, 실패해도 복구될 수 있도록 만드는 실행의 경계다.**
>
> **좋은 Harness는 모든 것을 소유하지 않는다.**
>
> **대신 중요한 실행이 그 경계를 우회하지 못하도록 한다.**