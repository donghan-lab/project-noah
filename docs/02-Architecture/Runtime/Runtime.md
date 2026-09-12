# Project NOAH Runtime Architecture

> Project NOAH Architecture
> Component: Runtime
> Architecture Version: 0.1
> Status: Blueprint
> Date: 2026-09-12
> Related Decisions: DDR-001, DDR-002, DDR-004, DDR-006

---

# 1. Purpose

이 문서는 Project NOAH의 Runtime Architecture를 정의한다.

Runtime은 Agent 또는 Harness가 선택한 실행을
실제 Infrastructure 위에서 시작하고,
수행하고,
관찰하고,
중단하고,
복구하기 위한 Execution Lifecycle Boundary다.

핵심 질문:

> **"NOAH의 실행은 실제로 어디에서 살아 움직이며,
> 그 실행 환경이 실패하거나 교체되어도 Task를 어떻게 지속할 것인가?"**

---

# 2. Architectural Role

Runtime은 Harness와 실제 Execution Environment 사이에 위치한다.

기본 관계:

```text
Agent / Orchestrator
        ↓
Execution Request
        ↓
      Harness
        ↓
      Runtime
        ↓
Sandbox / Workspace
        ↓
   Environment
        ↓
    Execution

Runtime은 Execution을 실제로 살아 있게 만드는
Lifecycle Mechanism이다.

3. Core Definition

Runtime의 기본 의미:

Runtime
=
Execution Lifecycle
+
Execution Environment Coordination
+
Resource Boundary
+
Runtime State
+
Cancellation
+
Checkpoint / Recovery Support
+
Execution Observation

Runtime은 특정 Process,
Container,
Framework 또는 Worker 구현과 동일하지 않다.

4. Core Separations

Project NOAH는 다음을 구분한다.

Runtime
≠
Agent

Runtime
≠
Model

Runtime
≠
Harness

Runtime
≠
Orchestrator

Runtime
≠
Task

Runtime
≠
Task State

Runtime
≠
Session

Runtime
≠
Capability

Runtime
≠
Sandbox

Runtime
≠
Workspace

Runtime
≠
Environment

Runtime
≠
Worker

Runtime
≠
Execution Record

이 구분은 Runtime Architecture의 핵심 Invariant다.

5. Why Runtime Exists

실행 Lifecycle을 Agent 또는 Tool 구현 자체에 넣으면:

Agent / Tool
├── Start
├── Retry
├── Timeout
├── Cancel
├── Resource Control
├── Checkpoint
├── Recovery
└── Cleanup

와 같이 각 구현이 서로 다른 실행 semantics를 가지게 될 수 있다.

그 결과:

Runtime 교체가 어려워지고
Recovery 방식이 구현마다 달라지고
Cancellation semantics가 일관되지 않고
Resource control이 분산되며
Observability가 일관되지 않고
Task continuity가 실행 Framework에 종속될 수 있다.

따라서 Runtime을 명시적인 Architecture Boundary로 둔다.

6. Runtime Principle

핵심 원칙:

Runtime은 Task를 지속시키는 것이 아니라 Execution을 지속시킨다.

Task continuity는 Runtime continuity보다 상위에 존재한다.

7. Runtime Responsibilities

Runtime의 후보 책임:

Prepare Execution Environment

Start Execution

Run Execution Unit

Observe Execution

Report Runtime State

Enforce Runtime Resource Limits

Pause where supported

Resume where supported

Cancel

Timeout

Checkpoint where supported

Recover where supported

Terminate

Cleanup

Expose Execution Metadata
8. Runtime Non-Responsibilities

Runtime은 다음을 직접 책임지지 않는다.

User Intent Interpretation

Task Goal Definition

Task Planning

Orchestration Strategy

Agent Reasoning

Canonical Task Progress

Identity Core

Memory Lifecycle

Knowledge Lifecycle

Artifact Semantics

Permission Authority

Policy Definition

Verification Decision

Evaluation
9. Runtime vs Harness

가장 중요한 경계:

Harness
= safe and stable execution boundary

Runtime
= concrete execution lifecycle mechanism

관계:

Harness
↓
Runtime Interface
↓
Runtime Implementation
10. Harness Owns the Boundary, Runtime Owns the Lifecycle

Harness는:

Validate

Authorize

Resolve

Prepare execution request

Track high-level execution

를 조정한다.

Runtime은:

Start

Run

Observe

Pause

Resume

Cancel

Terminate

를 실제 실행 계층에서 수행한다.

11. Runtime vs Agent

Agent:

무엇을 해야 하는가를 판단한다.

Runtime:

선택된 실행이 실제로 동작하도록 한다.

따라서:

Agent
≠
Runtime

이다.

12. Runtime Does Not Reason

Runtime은 기본적으로:

Should we change strategy?

What does the user really want?

Should we delegate to another specialist?

와 같은 Cognitive Decision을 수행하지 않는다.

이런 판단은 Agent / Orchestrator 책임이다.

13. Runtime vs Task

Task:

What must be achieved?

Runtime:

Where and how is this execution attempt running?

이다.

14. Runtime Failure Is Not Task Failure

핵심:

Runtime Failure
≠
Task Failure

예:

Task = Running

Runtime A = Failed

↓
Recovery

Runtime B = Running

Task = Running

이 가능해야 한다.

15. Runtime vs Task State

Runtime은 Task State를 읽거나
Execution Result를 통해 Transition을 유도할 수 있다.

하지만:

Runtime
≠
Task State Authority

다.

16. Runtime vs Session

Runtime은 Session보다 짧게 존재할 수 있다.

Session
├── Runtime A
├── Runtime B
└── Runtime C

Session이 없어도 Background Execution에
Runtime이 사용될 가능성을 유지한다.

17. Runtime vs Sandbox

Sandbox는 Execution을 격리하는 Security Boundary다.

Runtime은 Sandbox를 사용하거나 그 안에서 실행될 수 있다.

Runtime
↓
Sandbox
↓
Execution

따라서:

Runtime
≠
Sandbox

이다.

18. Runtime vs Workspace

Workspace:

작업에 필요한 files, repository, temporary data가 존재하는 공간

Runtime:

실행 lifecycle

따라서:

Runtime
↓
Workspace Reference

관계를 가질 수 있지만 둘은 동일하지 않다.

19. Runtime vs Environment

Environment는 Runtime 외부의 실제 실행 대상 또는 세계다.

예:

Filesystem

Operating System

Database

Repository

External API

Browser

Remote Service

Runtime은 Environment와 상호작용하지만 이를 소유하지 않는다.

20. Runtime vs Worker

Worker는 Runtime execution을 실제로 수행하는
Physical / Logical compute executor일 수 있다.

Runtime
↓
Worker

그러나:

Runtime
≠
Worker Process

이다.

21. Execution Unit

Runtime은 하나의 Execution Unit을 실행한다.

후보:

Capability Invocation

Code Execution

Process Execution

Workflow Step

Agent Invocation

Validation

Transformation
22. Execution Unit Does Not Define Runtime Semantics

Runtime Architecture는 특정 Execution Type 하나에 종속되지 않는다.

예:

Runtime Contract
├── Tool Runtime
├── Code Runtime
├── Browser Runtime
├── Workflow Runtime
└── Future Runtime

형태를 허용한다.

23. Agent Invocation

향후 Agent Invocation 자체도
Runtime lifecycle 아래에서 실행될 수 있다.

예:

Agent Invocation
↓
Model Call
↓
Tool Decision

하지만 Runtime이 Agent의 Cognitive semantics를 소유하는 것은 아니다.

24. Initial Runtime Scope

첫 PoC에서는 Runtime을 지나치게 일반화하지 않는다.

초기에는:

Capability Execution

Code / Process Execution

정도를 중심으로 Runtime Contract를 검증할 수 있다.

25. Runtime Instance

실제로 생성된 실행 환경을 Runtime Instance라고 한다.

후보:

Runtime Instance
├── Runtime Instance ID
├── Runtime Type
├── Provider
├── Status
├── Created At
├── Resource Profile
├── Sandbox Reference
├── Workspace Reference
└── Version
26. Runtime Instance vs Runtime Architecture
Runtime Architecture
= logical execution lifecycle contract

Runtime Instance
= concrete running instance

이다.

27. Runtime Instance Lifetime

Runtime Instance는 필요에 따라:

Single Execution

Multiple Executions

Session-scoped

Task-scoped

Worker-scoped

일 수 있다.

초기에는 가장 단순한 lifecycle을 우선한다.

28. Runtime Reuse

Runtime Instance를 여러 Execution에서 재사용할 수도 있다.

하지만 재사용은:

Performance
vs
Isolation

Trade-off가 존재한다.

29. Runtime Isolation

High-risk Execution에서는 Runtime reuse보다
새로운 isolated runtime을 선호할 수 있다.

정확한 policy는 Security Architecture에서 결정한다.

30. Execution Request

Harness에서 Runtime으로 전달되는
validated execution information이 존재한다.

후보:

Runtime Execution Request
├── Request ID
├── Execution ID
├── Execution Kind
├── Capability / Operation
├── Input
├── Workspace Reference
├── Sandbox Profile
├── Resource Limits
├── Deadline
├── Credential Handles
├── Trace Context
└── Recovery Metadata
31. Request ID vs Execution ID
Request ID
= logical requested operation

Execution ID
= one concrete attempt

이다.

32. Retry Creates a New Attempt

예:

Request R1
├── Execution E1
└── Execution E2

동일 Logical Request를
여러 Execution Attempt가 수행할 수 있다.

33. Runtime Instance vs Execution Attempt

하나의 Runtime Instance가 여러 Attempt를 처리할 수 있고,

하나의 Request가 Runtime 교체를 통해
여러 Runtime Instance에 걸칠 수도 있다.

Request R1
├── Attempt E1 → Runtime A
└── Attempt E2 → Runtime B
34. Execution Attempt

Execution Attempt는 실제 한 번의 실행 시도다.

후보:

Execution Attempt
├── Execution ID
├── Request ID
├── Runtime Instance ID
├── Attempt Number
├── Status
├── Started At
├── Ended At
├── Result Reference
├── Failure
└── Side-effect Status
35. Runtime Profile

Runtime 구현의 특성을 Runtime Profile로 표현할 수 있다.

후보:

Runtime Profile
├── Runtime Type
├── OS
├── Isolation Level
├── Supported Execution Kinds
├── Network Capability
├── Filesystem Capability
├── GPU Availability
├── Resource Limits
└── Recovery Support
36. Runtime Requirement

Capability 또는 Execution Request가
필요한 Runtime Requirement를 정의할 수 있다.

예:

Python required

Browser required

GPU required

Network prohibited

Strong isolation required

Specific OS required
37. Runtime Resolution

후보:

Execution Requirements
↓
Runtime Resolver
↓
Compatible Runtime

Runtime selection 자체는 Harness가 조정할 수 있다.

38. Runtime Resolver

후보 판단 요소:

Compatibility

Availability

Security

Isolation

Cost

Latency

Resource Need

Recovery Support

정확한 알고리즘은 Specification에서 결정한다.

39. Runtime Registry

Runtime implementation이 많아질 경우
Registry를 사용할 수 있다.

후보:

Runtime Registry
├── Local Runtime
├── Container Runtime
├── Browser Runtime
└── Remote Runtime

초기부터 별도 Registry Service를 만들지는 않는다.

40. Runtime Adapter

External Runtime 구현은 Adapter 뒤에 둔다.

Harness
↓
Runtime Interface
↓
Runtime Adapter
↓
Runtime Provider
41. Runtime Provider

후보:

Local Process

Docker

Virtual Machine

Remote Worker

Browser Environment

Workflow Engine

Future Compute Platform

현재 특정 Provider를 Core Architecture에 고정하지 않는다.

42. Runtime Interface

Logical Runtime Interface 후보:

prepare()

execute()

status()

observe()

cancel()

checkpoint()

recover()

terminate()

정확한 API는 Specification 단계에서 결정한다.

43. Small Runtime Contract

초기에는 Runtime Contract를 가능한 한 작게 유지한다.

핵심:

Prepare

Execute

Observe

Cancel

Terminate

부터 시작할 수 있다.

Checkpoint / Recover는 지원 Runtime에서 확장한다.

44. Capability Negotiation

모든 Runtime이 모든 operation을 지원하지 않는다.

따라서:

Runtime Feature
= Supported / Unsupported

를 명시적으로 표현할 수 있다.

45. Optional Runtime Features

후보:

Pause

Resume

Checkpoint

Streaming

Interactive Input

GPU

Network Isolation

Persistent Workspace

Optional Capability로 둘 수 있다.

46. Runtime Lifecycle

Runtime Instance 후보 Lifecycle:

Created
↓
Preparing
↓
Ready
↓
Running / Busy
↓
Idle
↓
Stopping
↓
Stopped

Failure:

Failed

상태를 가질 수 있다.

정확한 State Machine은 Specification에서 결정한다.

47. Created

Runtime Instance metadata가 생성된 상태다.

Physical Resource가 아직 준비되지 않았을 수 있다.

48. Preparing

Runtime이 Execution을 위해 준비되는 단계다.

예:

Allocate resources

Prepare sandbox

Attach workspace

Resolve environment

Inject credential handles
49. Ready

Execution을 시작할 수 있는 상태다.

50. Running

Runtime에서 Execution Attempt가 실제 동작하는 상태다.

51. Idle

Runtime Instance가 살아 있지만
현재 Execution이 없는 상태일 수 있다.

Runtime reuse 시 유용할 수 있다.

52. Stopping

Graceful shutdown이 진행 중인 상태다.

53. Stopped

Runtime Resource가 종료된 상태다.

54. Failed Runtime

Runtime 자체가 정상 execution lifecycle을 유지할 수 없는 상태다.

Runtime Failed
≠
Task Failed

이다.

55. Execution Attempt Lifecycle

Execution Attempt는 Runtime Instance와 별도 lifecycle을 가진다.

후보:

Created
↓
Prepared
↓
Running
├── Waiting
├── Paused
├── Succeeded
├── Failed
├── Cancelled
└── Timed Out
56. Execution State

Execution State는 현재 Attempt의 condition을 표현한다.

후보:

Execution State
├── Execution ID
├── Status
├── Current Step
├── Runtime Reference
├── Attempt
├── Started At
├── Deadline
├── Error
├── Checkpoint Reference
└── Side-effect Status
57. Execution State vs Execution Record
Execution State
= current execution condition

Execution Record
= durable execution history

로 구분한다.

58. Runtime State vs Task State
Runtime / Execution State
= runtime-specific condition

Task State
= durable task progress

Runtime State를 Task State로 사용하지 않는다.

59. Ephemeral Runtime State

후보:

Process Handle

Socket

Memory Buffer

Temporary PID

Open File Descriptor

Worker Thread

Runtime-local Cache

는 일반적으로 Ephemeral하다.

60. Durable Runtime Metadata

Recovery에 필요한 일부 정보는 durable하게 보존할 수 있다.

후보:

Execution ID

Attempt Number

Runtime Type

Capability Version

Started At

Result Status

Checkpoint Reference

Side-effect Record

Failure Metadata
61. Persistence Boundary

Runtime 전체를 영속화하려고 하지 않는다.

Runtime Memory
≠
Durable Task Continuity

이다.

62. Checkpoint

Checkpoint는 Execution을 이어가기 위해 필요한
최소한의 durable recovery information이다.

후보:

Checkpoint
├── Execution ID
├── Logical Step
├── Completed Operations
├── Pending Operations
├── Artifact References
├── Workspace Reference
├── Side-effect References
└── Created At
63. Checkpoint Is Not Runtime Snapshot

중요:

Checkpoint
≠
Full Process Memory Dump

가능하면 새 Runtime에서도 이해할 수 있는
portable recovery information을 우선한다.

64. Portable Checkpoint

좋은 Checkpoint는 특정 Runtime implementation에
과도하게 종속되지 않는다.

예:

Docker-specific container memory dump

만 존재하는 것보다:

Completed step
Artifact references
Pending operation

같은 semantic information을 우선한다.

65. Runtime-specific Checkpoint

필요한 경우 Runtime-specific checkpoint도 사용할 수 있다.

하지만 이를 Task continuity의 유일한 기반으로 만들지 않는다.

66. Checkpoint Frequency

Checkpoint frequency는 다음 Trade-off를 가진다.

More checkpoints
→ better recovery
→ more overhead

Fewer checkpoints
→ lower overhead
→ more lost work

정확한 정책은 Runtime / Task 특성에 따라 정한다.

67. Checkpoint Trigger

후보:

Major step completed

Before high-risk action

After artifact creation

Before runtime shutdown

Periodic interval

User pause

Orchestrator request
68. Pause

Runtime이 Pause를 지원하는 경우:

Running
↓
Pause Request
↓
Checkpoint
↓
Paused

흐름을 사용할 수 있다.

69. Pause Is Optional

모든 Runtime이 실제 process-level Pause를 지원해야 하는 것은 아니다.

대신:

Safe stop
+
Checkpoint
+
Later reconstruction

으로 의미적인 Pause를 구현할 수도 있다.

70. Resume

Resume는 기존 logical execution을 이어가는 것이다.

Checkpoint
↓
Runtime
↓
Resume
71. Resume vs Retry

중요:

Resume
= continuation from known progress

Retry
= new attempt of an operation

둘을 구분한다.

72. Restart vs Resume
Runtime Restart
= Runtime Instance replacement

Execution Resume
= logical execution continuation

이다.

73. Retry

Retry는 새로운 Execution Attempt를 만들 수 있다.

Request R1

Attempt E1 = Failed

↓ Retry

Attempt E2
74. Re-execution

처음부터 operation을 다시 실행하는 것은
Checkpoint Resume와 구분한다.

Re-execute
≠
Resume
75. Replan
Replan
≠
Retry
≠
Resume

Replan은 실행 전략 자체를 바꾸는
Agent / Orchestrator-level operation이다.

76. Recovery

Recovery는 Runtime Failure 이후
안전하게 execution continuity를 복원하는 과정이다.

77. Recovery Flow

후보:

Runtime Failure
↓
Detect Failure
↓
Load Task State
↓
Load Execution Record
↓
Load Checkpoint
↓
Inspect Side Effects
↓
Observe Current Environment
↓
Choose Recovery Action
↓
New Runtime
↓
Resume / Retry / Escalate
78. Recovery Inputs

후보:

Task State

Execution Record

Checkpoint

Artifact References

Side-effect Records

Workspace Reference

Current Environment Observation

Permission State
79. Recovery Does Not Restore the Past Exactly

중요:

Recovery
≠
Exact recreation of all prior runtime memory

목표는:

Task를 안전하게 계속 수행할 수 있는 실행 상태를 재구성하는 것

이다.

80. Recovery Runtime Replacement
Runtime A
↓
Failure

Runtime B
↓
Load recovery information
↓
Continue

가 가능해야 한다.

81. Unknown Outcome

가장 위험한 Failure 중 하나는
Execution 결과를 알 수 없는 상태다.

예:

External API request sent
↓
Connection lost
↓
Did mutation happen?
Unknown
82. Unknown Is Not Failed

중요:

Unknown Outcome
≠
Failed

실패라고 가정하고 즉시 Retry하면
Side Effect가 중복될 수 있다.

83. Unknown Outcome Handling

후보:

Inspect Side-effect Record

Query External System

Check Idempotency Key

Observe Environment

Ask Provider

Escalate

를 사용한다.

84. Side Effects

Runtime은 실제 Execution 과정에서 발생한
Side Effect를 추적할 수 있어야 한다.

예:

File written

Repository changed

API mutation

Message sent

Artifact published
85. Runtime Does Not Define Side-effect Semantics

Capability가:

What side effect does this action cause?

를 정의한다.

Runtime은 실제 attempt에서
그 Side Effect가 어떻게 발생했는지를 추적한다.

86. Side-effect Record

후보:

Operation ID

Request ID

Execution ID

Capability ID

Target

Status

Idempotency Key

Observed Result

Evidence

Compensation Status
87. Crash After Side Effect

중요 시나리오:

External mutation succeeds
↓
Runtime crashes
↓
Internal State not committed

이 경우 Recovery가 operation을 무조건 재실행해서는 안 된다.

88. Reconciliation

후보:

Execution Record
+
Side-effect Record
+
Current Environment
↓
Reconciliation

을 수행한다.

89. Idempotency

Runtime은 Capability의 Idempotency 정보를 고려한다.

Idempotent

Non-idempotent

Unknown
90. Runtime Does Not Invent Idempotency

Runtime이 operation semantics를 모르는 상태에서
임의로 Idempotent라고 가정하지 않는다.

91. Idempotency Key

External Provider가 지원할 경우:

Logical Request ID
↓
Idempotency Key

를 사용할 수 있다.

92. Exactly-Once Limitation

Runtime은 External Environment까지 포함하여
일반적인:

Exactly Once Execution

을 쉽게 보장한다고 주장하지 않는다.

93. Cancellation

Runtime은 실행 중인 Attempt를 취소할 수 있어야 한다.

후보:

Cancel Request
↓
Runtime
↓
Execution
94. Cooperative Cancellation

Capability가 cancellation을 지원하면
안전한 지점에서 종료하도록 할 수 있다.

95. Hard Termination

필요한 경우:

Terminate Process

Terminate Container

Kill Worker

등의 강제 종료를 사용할 수 있다.

96. Hard Termination Risk

Hard Termination은:

Partial Files

Open Transaction

External Side Effects

Corrupt Workspace

를 남길 수 있다.

따라서 종료 후 Reconciliation이 필요할 수 있다.

97. Cancellation vs Rollback
Cancellation
≠
Rollback

이미 발생한 External Side Effect는 별도로 처리한다.

98. Timeout

Runtime은 실행에 Timeout을 적용할 수 있다.

후보:

Startup Timeout

Execution Timeout

Idle Timeout

External Call Timeout

Shutdown Timeout
99. Task Deadline vs Runtime Timeout
Task Deadline
= Goal-level time constraint

Runtime Timeout
= Execution lifecycle constraint

이다.

100. Timeout Outcome

Timeout이 발생했다고 operation이 반드시 실행되지 않은 것은 아니다.

External request가 이미 전달되었다면
Unknown Outcome일 수 있다.

101. Resource Boundary

Runtime은 Resource Limit을 적용할 수 있다.

후보:

CPU

Memory

GPU

Disk

Network

Process Count

Execution Time

File Size

Concurrency
102. Resource Profile

후보:

Runtime Resource Profile
├── CPU Limit
├── Memory Limit
├── Storage Limit
├── GPU Requirement
├── Network Limit
└── Process Limit
103. Resource Enforcement

Agent가 Budget을 알고 있더라도
실제 Resource Enforcement는 Runtime / Sandbox level에서도 수행한다.

104. Resource Exhaustion

예:

Out of Memory

Disk Full

GPU unavailable

Process limit reached

를 Structured Runtime Failure로 반환한다.

105. Sandbox Relationship

Runtime은 Security Architecture가 정의한 Sandbox Profile을 적용한다.

Harness
↓
Sandbox Profile
↓
Runtime
106. Isolation Levels

후보:

In-process

Process

Container

Virtual Machine

Remote Isolated Worker

정확한 Level은 Risk와 Capability에 따라 선택한다.

107. Isolation Is Not Absolute

Container 또는 Sandbox를 사용한다고
완벽한 Security가 보장된다고 가정하지 않는다.

Defense in Depth를 유지한다.

108. Filesystem Scope

Runtime은:

Read-only

Read-write

Specific directories

Temporary workspace only

같은 Filesystem Scope를 적용할 수 있다.

109. Network Scope

후보:

No network

Allowlist

Read-only external access

Full network where explicitly allowed

정확한 semantics는 Security Architecture에서 정의한다.

110. Process Scope

Code Execution에서는:

Allowed executables

Child process limits

Privilege level

등을 제한할 수 있다.

111. Workspace Attachment

Runtime은 Workspace를 attach할 수 있다.

Runtime
↓
Workspace Reference
112. Workspace Is External to Runtime Identity

Runtime Instance가 종료되어도
Workspace가 반드시 삭제되는 것은 아니다.

또는 Temporary Workspace라면
Runtime 종료와 함께 제거할 수도 있다.

113. Workspace Modes

후보:

Ephemeral Workspace

Checkpointed Workspace

Task Workspace

Project Workspace
114. Workspace Recovery

필요한 경우:

Repository Reference

Artifact References

Checkpoint

Task State
↓
Workspace Reconstruction

을 사용할 수 있다.

115. Artifact Relationship

Runtime은 Artifact를 직접 semantic하게 소유하지 않는다.

Execution 결과로 Artifact가 생성되면:

Runtime
↓
Artifact Operation
↓
Artifact System

으로 연결된다.

116. Artifact Version

Artifact mutation에서는:

Expected Artifact Version

을 Runtime request에 포함할 수 있다.

117. Artifact Conflict

예:

Expected v4

Current v5

↓
Mutation blocked

를 사용할 수 있다.

118. Environment Observation

Runtime은 실행 중 Environment를 관찰할 수 있다.

예:

File exists

Process exit code

API response

Repository revision

Observation은 Evidence가 될 수 있다.

119. Observation Metadata

후보:

Observed At

Source

Runtime ID

Execution ID

Method

Version

Evidence Reference
120. Environment Drift

Long-running Runtime 동안
Environment가 변경될 수 있다.

따라서 과거 Observation을 영구적인 current truth로 취급하지 않는다.

121. Credential Relationship

Runtime은 Credential Handle을 전달받아
필요한 실행에서 사용할 수 있다.

Harness
↓
Credential Handle
↓
Runtime
↓
External Provider
122. Raw Credential Rule

Runtime이 Secret을 사용할 수 있더라도:

Runtime Secret
↓
Model Context

로 유출되지 않도록 한다.

123. Credential Lifetime

Credential은 가능한 경우 Execution 범위에 제한한다.

후보:

One call

One capability

One execution

Short-lived token
124. Credential Cleanup

Execution 종료 후 Temporary Credential이나 Token을
가능한 경우 폐기한다.

125. Runtime Environment Variables

Secret을 Environment Variable로 전달해야 하는 Runtime도 있을 수 있다.

이 경우:

Redaction

Scope

Lifecycle

Logging protection

을 적용한다.

126. Runtime Configuration

Runtime Configuration 후보:

Runtime Type

Version

Resource Profile

Sandbox Profile

Workspace

Environment Variables

Network Policy

Execution Mode

Recovery Policy
127. Configuration Is Versioned

중요 Execution에서는 어떤 Runtime Configuration을 사용했는지
추적할 수 있어야 한다.

128. Reproducibility

Recovery와 Reproducibility를 구분한다.

Recovery
= continue safely

Reproducibility
= repeat under equivalent conditions
129. Reproducibility Metadata

후보:

Runtime Version

Capability Version

Container Image Digest

Dependency Manifest

Environment Metadata

Artifact Version

Configuration
130. Reproducibility Is Not Determinism

동일 Runtime 환경이어도:

External API

Current environment

Model output

Time

Randomness

때문에 동일 결과가 나오지 않을 수 있다.

131. Deterministic Execution

가능한 Capability에서는
Deterministic Execution을 선호할 수 있다.

예:

Schema validation

Hash computation

Pure transformation
132. Non-deterministic Execution

예:

LLM call

Web retrieval

External API

Concurrent environment

는 동일 Input에서도 결과가 달라질 수 있다.

133. Runtime Observability

Runtime은 Execution lifecycle을 관찰할 수 있어야 한다.

후보:

Runtime ID

Execution ID

Request ID

Status

Started At

Ended At

Resource Usage

Exit Code

Failure

Checkpoint

Worker Reference
134. Trace Propagation

Harness에서 전달받은 Trace Context를 Runtime에서도 유지한다.

Task
↓
Request
↓
Harness
↓
Runtime
↓
Capability

를 연결한다.

135. Runtime Logs

후보 Event:

RuntimeCreated

RuntimePrepared

RuntimeReady

ExecutionStarted

ExecutionPaused

ExecutionResumed

ExecutionSucceeded

ExecutionFailed

ExecutionCancelled

ExecutionTimedOut

CheckpointCreated

RuntimeStopping

RuntimeStopped

RuntimeFailed
136. Logs Are Not Runtime State
Log
≠
Current State

이다.

137. Runtime Metrics

후보:

Startup Latency

Execution Latency

CPU

Memory

GPU Usage

Network Usage

Failure Rate

Crash Rate

Cancellation Latency

Checkpoint Cost

Recovery Time

Runtime Reuse Rate
138. Resource Usage Accounting

Resource usage를 Task / Execution Budget에 연결할 수 있다.

Execution Resource Usage
↓
Budget Accounting
139. Runtime Health

Runtime Provider는 Health 상태를 제공할 수 있다.

후보:

Healthy

Degraded

Unavailable
140. Runtime Health Is Not Execution Success

Runtime Provider가 Healthy여도
개별 Capability Execution은 실패할 수 있다.

141. Heartbeat

Remote Runtime에서는
Heartbeat 또는 Lease가 필요할 수 있다.

초기 Local Runtime에서는 필수로 하지 않는다.

142. Lost Worker

Remote Worker와 연결이 끊기면:

Worker lost
↓
Execution outcome?

를 확인해야 한다.

즉시 Failed로 단정하지 않는다.

143. Runtime Security

Runtime은 실제 Execution Environment에 가까우므로
중요한 Security Boundary다.

위험 후보:

Arbitrary code execution

Filesystem escape

Network abuse

Credential leakage

Resource exhaustion

Cross-task leakage

Process persistence
144. Least Privilege Runtime

Runtime은 필요한 범위의 Resource와 Access만 가진다.

Minimum filesystem

Minimum network

Minimum credentials

Minimum lifetime

Minimum compute
145. Runtime Privilege

가능한 경우 elevated system privilege를 기본값으로 사용하지 않는다.

146. Cross-Task Isolation

Task A Runtime의 Temporary Data가
Task B로 암묵적으로 노출되지 않도록 한다.

147. Runtime Cleanup

Execution / Runtime 종료 후:

Temporary files

Processes

Credential handles

Network sessions

Temporary mounts

등을 정리한다.

148. Cleanup Failure

Cleanup 자체도 실패할 수 있다.

예:

Temporary process remains

Workspace lock remains

Remote resource remains

이를 Observability / Recovery에 기록한다.

149. Runtime Leakage

Runtime이 종료되었다고 생각했지만
Background Process가 계속 실행될 수 있다.

Sandbox / process isolation에서 이를 검증해야 한다.

150. Concurrency

Runtime은 여러 Execution을 동시에 처리할 수 있다.

하지만 concurrency를 무조건 최대화하지 않는다.

151. Runtime Concurrency vs Orchestration Parallelism
Orchestration Parallelism
= which work should run concurrently

Runtime Concurrency
= how much execution this runtime can host

둘을 구분한다.

152. Capacity

Runtime Provider는 현재 Capacity를 표현할 수 있다.

후보:

Available Slots

CPU availability

GPU availability

Memory availability
153. Runtime Does Not Own Global Scheduling

Runtime이 capacity 정보를 제공할 수는 있지만
전체 Task Scheduling Strategy는 Orchestrator 책임이다.

154. Backpressure

Runtime Capacity가 부족한 경우:

Queue

Reject

Wait

Alternative runtime

등을 사용할 수 있다.

정확한 scheduling policy는 Runtime 자체에 고정하지 않는다.

155. Worker Pool

향후:

Runtime Adapter
↓
Worker Pool
├── Worker A
├── Worker B
└── Worker C

형태가 가능하다.

156. Initial Runtime Is Local

첫 PoC에서는:

Local Runtime

하나로 시작하는 것이 적절하다.

분산 실행은 초기 요구사항이 아니다.

157. Modular Monolith Runtime

초기 후보:

NOAH Process
↓
Harness
↓
Local Runtime Adapter
↓
Local Execution

으로 시작할 수 있다.

158. Container Runtime

격리가 필요한 경우:

Harness
↓
Container Runtime Adapter
↓
Container

로 확장할 수 있다.

159. Remote Runtime

향후:

Harness
↓
Remote Runtime Adapter
↓
Remote Worker

도 가능하다.

160. Runtime Location Transparency

Agent는 가능한 한:

Local?

Container?

Remote?

같은 Physical Runtime 위치를 직접 알 필요가 없다.

161. Location-sensitive Capability

다만 일부 Capability는 특정 Device / Environment를 요구할 수 있다.

예:

Local file access

Specific GPU

User desktop interaction

이 경우 Runtime Requirement로 표현한다.

162. Runtime Versioning

Runtime Contract와 Implementation Version을 구분한다.

Runtime Contract Version
≠
Runtime Implementation Version
≠
Provider Version
163. Runtime Contract Compatibility

새 Runtime Adapter는 기존 Contract를 만족하는지 검증한다.

164. Runtime Contract Test

후보:

Prepare works

Execute works

Cancel behaves correctly

Timeout semantics correct

Structured Failure returned

Cleanup occurs

Trace preserved

를 테스트한다.

165. Optional Feature Contract Test

Checkpoint 지원 Runtime이라면:

Checkpoint

Recover

Resume

semantics를 별도로 검증한다.

166. Runtime Failure Categories

후보:

Preparation Failure

Startup Failure

Resource Failure

Sandbox Failure

Workspace Failure

Credential Failure

Execution Failure

Provider Failure

Timeout

Cancellation Failure

Checkpoint Failure

Recovery Failure

Cleanup Failure

Unknown Outcome
167. Structured Runtime Failure

후보:

Runtime Failure
├── Category
├── Code
├── Message
├── Runtime ID
├── Execution ID
├── Retryable
├── Recoverable
├── Side-effect Status
├── Partial Result
└── Evidence
168. Failure Attribution

다음을 구분한다.

Runtime Failure

Capability Failure

Environment Failure

Provider Failure

Permission Failure

Agent Request Failure

Verification Failure

모두 Runtime 실패로 뭉개지 않는다.

169. Runtime Failure Isolation

하나의 Runtime Instance Failure가
가능한 한 unrelated Task / Execution에 영향을 주지 않도록 한다.

170. Blast Radius

Runtime reuse가 많아질수록
한 Runtime Failure의 blast radius도 커질 수 있다.

Security / performance와 함께 고려한다.

171. Degraded Runtime

일부 기능만 사용할 수 있는 상태가 존재할 수 있다.

예:

GPU unavailable

Network unavailable

Read-only filesystem

Runtime Profile을 갱신하거나
Harness에 degraded 상태를 알린다.

172. Runtime Selection After Failure

Runtime A가 실패했다면
Runtime B로 Fallback할 수 있다.

하지만 semantic compatibility를 먼저 확인한다.

173. Runtime Fallback
Runtime A
↓
Unavailable
↓
Runtime B

로 바꿀 때:

Capability support

Isolation

Environment access

Workspace

Credentials

Checkpoint compatibility

를 확인한다.

174. Recovery Compatibility

Runtime B가 Runtime A의 proprietary checkpoint를
읽지 못할 수 있다.

따라서 semantic durable recovery information이 중요하다.

175. Runtime and Verification

Runtime은 Verification에 필요한
Execution Evidence를 제공할 수 있다.

예:

Exit Code

Artifact Hash

Process Result

Observed File State

API Response Metadata
176. Runtime Does Not Verify Task Goal
Runtime Execution Success
≠
Verification Pass

Runtime은 execution outcome을 보고한다.

Verifier가 요구사항 충족 여부를 판단한다.

177. Runtime and Evaluation

Runtime 자체도 평가한다.

후보:

Reliability

Crash rate

Recovery rate

Latency

Isolation

Resource efficiency

Compatibility

Observability
178. Runtime Choice Evaluation

여러 Runtime Implementation이 있을 경우:

Correctness

Security

Performance

Cost

Recovery

Maintainability

를 비교할 수 있다.

179. Runtime and Learning

반복되는 Runtime Failure는
Learning / Architecture Improvement의 Evidence가 될 수 있다.

하지만 Runtime이 스스로 자신의 Architecture를 자동 수정하지 않는다.

180. Self-modification Boundary

후보:

Runtime Failure Patterns
↓
Evaluation
↓
Improvement Proposal
↓
Governance / Engineering
↓
Deployment
181. Runtime Record

Durable Runtime / Execution Record 후보:

Execution Record
├── Request ID
├── Execution ID
├── Runtime Instance ID
├── Runtime Type
├── Runtime Version
├── Capability Version
├── Status
├── Started At
├── Ended At
├── Result Reference
├── Evidence References
├── Side-effect References
├── Checkpoint Reference
├── Resource Usage
└── Failure
182. Runtime Record Is Not the Runtime
Execution Record
≠
Runtime Instance

Runtime가 종료되어도 Record는 남을 수 있다.

183. Execution History

한 Request에 대해:

Request R1
├── E1 Failed
├── E2 Unknown
└── E3 Succeeded

와 같은 Attempt History를 추적할 수 있다.

184. Attempt History and Recovery

Recovery는 가장 최근 Attempt만 보지 않고
필요한 경우 전체 Attempt / Side-effect History를 확인한다.

185. Observability Retention

Runtime log와 Execution Record의 Retention은
서로 다를 수 있다.

Verbose Runtime Log
→ shorter retention

Critical Execution Record
→ longer retention

같은 전략이 가능하다.

186. Privacy

Runtime Log에 다음이 노출될 수 있다.

File path

User data

External payload

Credential-related metadata

Artifact content

따라서 Redaction과 Access Control을 적용한다.

187. Secret Logging Rule

Raw Credential 또는 Secret을 Runtime Log에 남기지 않는다.

188. Artifact Logging Rule

큰 Artifact Content 전체를 Log에 복제하지 않는다.

Reference를 우선한다.

189. Runtime Retention

고려 요소:

Recovery

Audit

Debugging

Evaluation

Privacy

Storage Cost
190. Runtime Cleanup vs Record Retention
Delete Runtime Resource
≠
Delete Execution Record

이다.

191. Runtime Deletion

Runtime Instance가 종료되고 제거되어도:

Task State

Artifacts

Execution Records

Evidence

Audit

는 각자의 Lifecycle에 따라 지속될 수 있다.

192. Runtime Availability

Runtime Provider unavailable 시
해당 Execution은 Waiting / Blocked / Failed가 될 수 있다.

Task 전체 Failure 여부는 상위 Strategy가 판단한다.

193. Runtime Readiness

Execution 시작 전:

Provider available

Resources available

Sandbox ready

Workspace attached

Credentials resolvable

등을 확인할 수 있다.

194. Runtime Preparation Failure

Preparation 단계가 실패하면
실제 Side Effect가 발생하기 전에 종료할 수 있는 경우가 많다.

Structured Failure를 반환한다.

195. Runtime Contract Boundary

Runtime Interface는 Infrastructure-specific detail을
상위 Agent / Harness Contract에서 숨긴다.

예:

Docker container ID

같은 detail을 Agent가 반드시 알 필요는 없다.

196. Escape Hatch

Debugging 또는 specialized execution에서는
Runtime-specific metadata가 필요할 수 있다.

그 경우 explicit metadata / diagnostic interface를 사용한다.

Core Contract를 provider-specific detail로 오염시키지 않는다.

197. Runtime Abstraction Leakage

피해야 할 예:

Agent:
"docker container abc123에서 실행해"

가 Core Task semantics에 박히는 것.

대신:

Execution Requirement:
isolated Linux runtime

같은 semantic requirement를 우선한다.

198. Runtime Portability

가능한 Execution은 Runtime A에서 B로 옮길 수 있어야 한다.

하지만 모든 Execution이 portable한 것은 아니다.

199. Non-portable Execution

예:

Specific desktop state

Hardware device

Local-only file

GPU-specific session

은 Runtime Location에 종속될 수 있다.

이를 명시적으로 표현한다.

200. Runtime Affinity

특정 Execution이 특정 Runtime / Workspace와 affinity를 가질 수 있다.

후보:

Workspace affinity

Device affinity

GPU affinity

Session affinity

초기에는 복잡한 affinity scheduler를 만들지 않는다.

201. Interactive Runtime

일부 Execution은 interactive input을 요구할 수 있다.

예:

Terminal

Browser

Desktop control
202. Non-interactive Runtime

많은 Background Capability는:

Request
↓
Execute
↓
Result

의 단순 lifecycle이면 충분하다.

초기 Runtime은 이 형태를 우선한다.

203. Streaming Result

일부 Runtime은 진행 중 Output streaming을 지원할 수 있다.

후보:

Logs

Progress

Partial Results

Token stream
204. Streaming Is Not Completion

Partial Output을 받았다는 사실이
Execution completion을 의미하지 않는다.

205. Progress

Runtime은 Execution Progress를 보고할 수 있다.

예:

0%

Step 3 / 10

Waiting for provider

하지만 이것이 canonical Task Progress와 동일하지 않다.

206. Runtime Progress vs Task Progress
Runtime Progress
= execution attempt progress

Task Progress
= durable overall task progress

이다.

207. Runtime and Session

Interactive Session은 Runtime Reference를 가질 수 있다.

하지만 Runtime은 Session Store를 소유하지 않는다.

208. Runtime and Orchestration

Orchestrator는 Runtime availability / capacity를
Scheduling Input으로 사용할 수 있다.

하지만 Runtime은 Orchestration Strategy를 소유하지 않는다.

209. Runtime and Harness

Runtime은 Harness를 우회해
Agent로부터 arbitrary execution을 받아들이지 않는 방향을 우선한다.

210. Authorized Runtime Entry

실제 mutable execution은
validated Harness path에서 시작되도록 한다.

211. Internal Trusted Operations

일부 internal low-level maintenance operation이
Harness facade와 다른 내부 경로를 사용할 수 있다.

그 경우에도 동일한 Security / Audit invariants를 깨지 않아야 한다.

212. Runtime Manager

여러 Runtime Instance의 lifecycle을 관리하기 위해
Logical Runtime Manager가 존재할 수 있다.

후보 책임:

Create

Track

Stop

Health

Capacity

Cleanup
213. Runtime Manager Is Not Orchestrator
Runtime Manager
= manages execution environments

Orchestrator
= manages work coordination

이다.

214. Runtime Manager Is Optional

첫 PoC에서 하나의 Local Runtime만 있다면
별도 Runtime Manager abstraction이 필요하지 않을 수 있다.

215. Avoid Runtime Manager Explosion

다음 구조를 초기부터 만들 필요는 없다.

Runtime Manager
↓
Scheduler
↓
Worker Manager
↓
Resource Broker
↓
Cluster Manager

실제 필요성이 확인될 때 확장한다.

216. Initial Runtime Components

첫 PoC 후보:

RuntimeInterface

LocalRuntime

RuntimeExecution

ExecutionState

ExecutionRecord

RuntimeResult

RuntimeFailure

Checkpoint는 필요할 경우 추가한다.

217. Initial Local Runtime

초기 구현 후보:

Local Runtime
↓
Controlled subprocess / application execution

로 시작할 수 있다.

구체적인 Python library는 Specification / Implementation에서 결정한다.

218. Docker Role

Docker는 초기 Infrastructure에서 사용 중일 수 있지만:

Runtime Architecture
≠
Docker

이다.

필요한 Capability의 격리 Runtime Provider 중 하나가 될 수 있다.

219. n8n Role

n8n Workflow 역시:

Workflow Runtime Adapter

후보가 될 수 있다.

하지만 Runtime Architecture를 n8n에 종속시키지 않는다.

220. Model Infrastructure Relationship

Ollama 또는 External LLM Provider도
Agent execution의 Model Infrastructure로 사용될 수 있다.

하지만:

NOAH Runtime
≠
Ollama

이다.

Model Interface / Runtime relationship은 후속 Specification에서 구체화한다.

221. First PoC Scope

첫 Runtime PoC에서는:

One local runtime

One or two deterministic capabilities

Execution ID

Structured Result

Timeout

Cancellation

Execution Record

Basic Recovery

정도로 충분하다.

222. Minimal Runtime PoC
1. Harness receives Execution Request

2. Runtime selected

3. Runtime prepared

4. Execution Attempt created

5. Capability executed

6. Runtime State observed

7. Result produced

8. Execution Record persisted

9. Runtime terminated / returned to idle

10. Verification performed
223. Runtime Failure PoC
1. Task = Running

2. Runtime A starts Execution

3. Runtime A fails

4. Task State survives

5. Execution Record = Failed

6. Runtime B created

7. Context / execution reconstructed

8. Execution resumed or retried

9. Task continues
224. Runtime Replacement PoC
Harness
↓
Runtime A

에서:

Harness
↓
Runtime B

로 교체한 뒤에도
Execution Request / Result Contract가 유지되는지 검증한다.

225. Cancellation PoC
Long-running Execution
↓
Cancel
↓
Runtime
↓
Execution stopped
↓
Cleanup
↓
Structured Cancelled result

를 검증한다.

226. Timeout PoC
Execution exceeds timeout
↓
Runtime stops / marks timed out
↓
Side-effect status checked
↓
Structured result

를 검증한다.

227. Checkpoint PoC
Execution Step A complete
↓
Checkpoint
↓
Runtime shutdown
↓
New Runtime
↓
Resume from Step B

를 검증한다.

228. Crash Before Side Effect PoC
Runtime crash
↓
External mutation not started
↓
Safe retry

를 확인한다.

229. Crash After Side Effect PoC
External mutation succeeded
↓
Runtime crashed before state commit
↓
Recovery
↓
External state observed
↓
Duplicate operation avoided

를 검증한다.

230. Unknown Outcome PoC
External request sent
↓
Connection lost
↓
Outcome unknown
↓
No blind retry
↓
Reconciliation

을 검증한다.

231. Resource Limit PoC
Execution exceeds memory / time limit
↓
Runtime enforcement
↓
Structured ResourceFailure

를 확인한다.

232. Sandbox PoC

Runtime이 허용되지 않은:

Filesystem path

Network destination

에 접근하려 할 때 차단되는지 검증한다.

233. Workspace Recovery PoC
Temporary Runtime lost
↓
Task State
+
Artifact References
+
Repository
↓
New Workspace
↓
New Runtime
↓
Continue

를 검증한다.

234. Runtime Observability PoC

Execution 하나에 대해:

Task ID

Request ID

Execution ID

Runtime ID

Capability ID

가 하나의 Trace로 연결되는지 확인한다.

235. Runtime Contract Test

다른 Runtime Adapter를 만들어:

prepare

execute

cancel

result

semantics가 동일하게 유지되는지 테스트한다.

236. Acceptance Criteria

Runtime Architecture v0.1은 최소 다음을 만족해야 한다.

Runtime is distinguishable from Harness.

Runtime is distinguishable from Agent.

Runtime is distinguishable from Task.

Runtime is distinguishable from Session.

Runtime is distinguishable from Sandbox and Workspace.

Runtime failure does not destroy durable Task State.

Runtime-specific State is not required for Task continuity.

Execution Request is distinguishable from Execution Attempt.

Retries can create distinct Execution Attempts.

Runtime implementation can be replaced behind a stable interface.

Execution can be cancelled.

Execution can time out.

Runtime Resource limits can be enforced.

Important Execution metadata can survive Runtime termination.

Checkpoints can support recovery where needed.

Unknown Side-effect outcomes are not blindly retried.

Execution success does not automatically complete a Task.

Runtime can provide Evidence without becoming the Verifier.

Raw Credentials are not exposed to the Model by default.

Initial architecture does not require distributed workers or a Runtime microservice.
237. Architecture Invariants
Runtime must not become the Task source of truth.

Runtime must not become the Task State source of truth.

Runtime must not become the Agent.

Runtime must not become the Orchestrator.

Runtime must not become the Policy authority.

Runtime failure must not imply Task failure.

Runtime restart must not imply Task restart.

Runtime progress must not silently become Task progress.

Execution success must not imply Task completion.

Runtime-specific process memory must not be required for durable continuity.

Cancellation must not be treated as rollback.

Timeout must not automatically mean no side effect occurred.

Unknown execution outcome must not be treated as confirmed failure.

Retry must not ignore idempotency and side-effect history.

Runtime implementation details must not leak into stable Task semantics.

Sandbox use must not be confused with complete security.

Credentials must not be exposed to the Model by default.

Runtime replacement must remain possible where execution requirements allow.
238. Stable Boundaries

현재 안정적으로 유지할 후보:

Runtime / Harness separation

Runtime / Task separation

Runtime / Session separation

Runtime / Sandbox separation

Runtime / Workspace separation

Execution Request / Attempt separation

Runtime Instance semantics

Runtime lifecycle

Durable / Ephemeral Runtime State distinction

Cancellation

Timeout

Checkpoint / Recovery boundary

Side-effect awareness

Runtime replaceability
239. Replaceable Implementations

다음은 교체 가능해야 한다.

Runtime Provider

Local Process implementation

Container technology

Remote worker technology

Browser runtime

Workflow runtime

Resource monitor

Runtime Manager

Checkpoint backend

Runtime logging backend

Worker pool

Transport

Serialization
240. Deferred Decisions

현재 최종 결정하지 않는다.

Exact Runtime Interface

Exact Runtime State Machine

Exact Execution Attempt Schema

Exact Runtime Record Schema

Exact Checkpoint Schema

Exact Resource Profile

Exact Runtime Resolver Algorithm

Exact Runtime Registry

Exact Runtime Reuse Policy

Exact Isolation Level Policy

Exact Worker Model

Exact Remote Runtime Protocol

Exact Heartbeat / Lease Model

Exact Backpressure Strategy

Exact Runtime Pool

Exact Cleanup Policy

Exact Container Runtime

Exact Browser Runtime

Exact Workflow Runtime Adapter

Exact Model Runtime Relationship

Exact Runtime Persistence

Exact Checkpoint Frequency

Distributed Runtime Architecture
241. Related Architecture

본 문서는 다음 Architecture와 연결된다.

System Architecture

Agent Architecture

Task Architecture

Session Architecture

State Architecture

Context Architecture

Harness Architecture

Artifact Architecture

Capability Architecture

Security Architecture

Orchestration Architecture

Verification Architecture

Observability Architecture

Evaluation Architecture
242. Related Decisions

핵심 Decision:

DDR-001
Task State / Runtime Boundary

DDR-002
Harness Boundary

강하게 연결되는 Decision:

DDR-006
Orchestration Contract

추가 관련 Decision:

DDR-004
Artifact Architecture
243. Specification Questions

후속 Specification에서 결정해야 할 질문:

What is the minimum Runtime interface?

What is a Runtime Instance?

What is an Execution Attempt?

What Runtime lifecycle states are required?

What Execution Attempt states are required?

Which Runtime features are mandatory?

Which features are optional?

How are Runtime requirements represented?

How is a Runtime implementation selected?

How are Runtime IDs generated?

How are Attempt numbers represented?

What Runtime State is durable?

What Runtime State is ephemeral?

What information belongs in an Execution Record?

What constitutes a Checkpoint?

Which checkpoints must be portable?

How is Resume different from Retry in the API?

How is Runtime cancellation propagated?

How are Timeouts represented?

How is Unknown Outcome represented?

How are Side Effects reconciled?

How are Resource Limits represented?

How is Sandbox configuration attached?

How is Workspace attached?

How are Credential Handles provided?

How is Runtime cleanup verified?

How is Runtime health represented?

How are Runtime capabilities advertised?

How are Runtime Adapter contract tests defined?

When should a Runtime be reused?

When should it be isolated per Execution?

When would remote workers become justified?
244. Architecture Boundary

본 문서는 Runtime의 Logical Architecture를 정의한다.

다음은 아직 정의하지 않는다.

Concrete Python Classes

Exact subprocess library

Exact Docker integration

Exact worker implementation

Exact RPC Protocol

Exact Database Schema

Exact queue

Exact Kubernetes architecture

Exact VM technology

Exact browser automation framework

Exact resource monitoring library
245. Initial Design Preference

Runtime Architecture v0.1에서는 다음을 우선한다.

Local First

Simple Lifecycle

Explicit Execution IDs

Structured Results

Runtime Replaceability

Durable Execution Metadata

Minimal Checkpoints

Safe Cancellation

Explicit Timeouts

Side-effect Awareness

Recoverable Failure

No Distributed Runtime Until Needed
246. What Runtime Architecture Must Avoid

특히 다음을 피한다.

Task progress stored only in Runtime memory
One Runtime process kept alive for the entire lifetime of a long Task
Runtime implementation coupled directly to Agent semantics
Runtime failure automatically marks Task failed
Retry after unknown side effect without reconciliation
Checkpoint implemented only as provider-specific memory dump
Container treated as the definition of Runtime
Workspace treated as Runtime identity
Execution success treated as verified Task completion
Distributed worker architecture before a real requirement exists
247. Candidate Runtime Flow
                    HARNESS
                       │
                       ↓
               EXECUTION REQUEST
                       │
                       ↓
                RUNTIME RESOLUTION
                       │
                       ↓
                 RUNTIME INSTANCE
                       │
                       ↓
                    PREPARE
                       │
                       ↓
               EXECUTION ATTEMPT
                       │
                       ↓
                     RUN
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ↓              ↓              ↓
     RESULT          FAILURE       CANCEL
        │              │              │
        └──────────────┼──────────────┘
                       ↓
               EXECUTION RECORD
                       │
                       ↓
                    EVIDENCE
                       │
                       ↓
                 VERIFICATION
248. Candidate Runtime / State Boundary
                    TASK STATE
                    (durable)
                        │
                        │ reference
                        ↓
                 EXECUTION STATE
                        │
                        ↓
                     RUNTIME
                        │
                        ↓
                    EXECUTION

Runtime termination removes neither
Task Definition nor durable Task State.

249. Candidate Recovery Flow
                 RUNTIME A
                     │
                     ↓
                  EXECUTION
                     │
                     X
                   CRASH
                     │
                     ↓
           ┌─────────────────────┐
           │     TASK STATE      │
           │  EXECUTION RECORD   │
           │     CHECKPOINT      │
           │   ARTIFACT REFS     │
           │ SIDE-EFFECT RECORDS │
           └──────────┬──────────┘
                      ↓
                RECONCILIATION
                      ↓
                 RUNTIME B
                      ↓
              RESUME / RETRY
                      ↓
                   CONTINUE
250. Candidate Runtime Provider Boundary
                    RUNTIME CONTRACT
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ↓               ↓               ↓
       LOCAL           CONTAINER         REMOTE
      RUNTIME           RUNTIME          RUNTIME
           │               │               │
           └───────────────┼───────────────┘
                           ↓
                       EXECUTION

Runtime Contract는 Provider보다 안정적으로 유지한다.

251. Candidate Runtime Responsibility Boundary
ORCHESTRATOR
└── decides coordination and scheduling strategy

AGENT
└── decides what action is desirable

HARNESS
└── validates and mediates the execution request

RUNTIME
└── manages the actual execution lifecycle

SANDBOX
└── constrains the execution environment

CAPABILITY
└── defines and performs the operation

TASK STATE
└── preserves durable task progress

VERIFICATION
└── determines whether required outcome is satisfied
252. Current Architecture Statement

Project NOAH의 Runtime은 Task, Agent 또는 Harness 자체가 아니라
선택된 Execution을 실제 Infrastructure 위에서 살아 움직이게 하는
Execution Lifecycle Boundary다.

Runtime은 Execution을 준비하고 시작하며,
실행 상태를 관찰하고,
Resource Limit, Timeout, Cancellation 및 필요한 경우 Checkpoint와 Recovery를 지원한다.

Runtime-specific State는 일시적일 수 있으며,
Runtime Failure나 교체가 Durable Task State를 파괴해서는 안 된다.

하나의 Logical Execution Request는 여러 Execution Attempt를 가질 수 있고,
Runtime Failure 이후에도 Execution Record, Checkpoint,
Artifact 및 Side-effect Evidence를 사용해 새 Runtime에서 안전하게 이어갈 수 있어야 한다.

Runtime은 Sandbox, Workspace, Credential 및 Environment와 연결되지만
어느 것도 Runtime 그 자체가 아니다.

Runtime 구현은 Local Process, Container, Remote Worker 또는 미래의 다른 실행 기술로
교체 가능해야 하며, 초기 NOAH에서는 단순한 Local Runtime부터 시작한다.

253. Final Principle

Runtime은 NOAH의 목표를 기억하는 장소가 아니다.

Runtime은 그 목표를 향한 한 번의 실행이 실제로 존재하는 장소다.

실행 환경은 죽고, 교체되고, 다시 만들어질 수 있다.

하지만 Task의 지속성은 그 실행 환경과 함께 죽어서는 안 된다.