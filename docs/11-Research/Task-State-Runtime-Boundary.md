Task State / Runtime Boundary Research v0.1
# Task State / Runtime Boundary Research

> Project NOAH Research
> Research 대상: Task State / Runtime Boundary
> Research Version: 0.1
> Priority: P0
> Status: Research

---

# 1. Research Purpose

Project NOAH의 Task State와 Runtime의 책임 및 경계를 정의하기 위한 연구를 수행한다.

핵심 질문:

> Task State는 무엇인가?
> Runtime은 무엇을 책임지는가?
> Task와 Session은 어떻게 다른가?
> Runtime이 종료되어도 무엇이 유지되어야 하는가?

본 문서는 최종 Architecture를 결정하지 않는다.

---

# 2. Why This Research Matters

현재 Architecture Integration Review에서 다음 개념의 경계가 아직 완전히 확정되지 않았다.

- Session
- Task
- Task State
- Execution State
- Context
- Memory
- Runtime
- Environment State
- Workspace State

이 경계가 불명확하면:

- Durable Execution
- Pause / Resume
- Recovery
- Long-horizon Task
- Context Management
- Memory
- Evaluation
- Orchestration

모두 영향을 받는다.

따라서 이 문제를 P0 Research로 지정한다.

---

# 3. Current NOAH Hypothesis

현재 가설:

Task는 목표를 가진 지속적인 작업 단위다.

Session은 특정 실행 관계를 담는 논리적 컨테이너다.

Runtime은 Task를 실제로 실행하는 실행 계층이다.

Task State는 Task의 현재 canonical progress를 나타낸다.

Execution State는 현재 실행 중인 Runtime의 상태를 나타낸다.

이 가설은 본 Research에서 검증한다.

---

# 4. Terminology

## Conversation

사용자와 Agent 사이의 상호작용 기록.

## Session

하나의 지속적인 실행 관계를 관리하는 논리적 컨테이너.

## Task

달성해야 하는 목표 단위.

## Task State

Task가 현재 어느 상태에 있는지를 표현하는 durable / canonical state.

## Execution State

현재 Runtime에서 진행 중인 실행의 상태.

## Context

현재 Model 실행에 제공되는 정보의 projection.

## Runtime

Task / Agent를 실제로 실행하는 시스템.

## Environment State

Agent가 작업하고 있는 실제 외부 환경의 상태.

## Workspace State

Agent 작업에 사용되는 파일/프로세스/산출물 등의 상태.

---

# 5. Task vs Session

현재 가장 중요한 구분 중 하나다.

Candidate:

Task는 Session보다 오래 지속될 수 있다.

예:

Session 1
→ Task 시작

Session 종료

Session 2
→ 동일 Task 재개

따라서:

Task lifecycle
≠
Session lifecycle

이라는 가설을 검토한다.

---

# 6. Task Lifecycle

후보:

Created
→ Planned
→ Running
→ Blocked
→ Waiting
→ Paused
→ Resuming
→ Completed
→ Failed
→ Cancelled
→ Archived

모든 상태를 반드시 구현해야 한다는 뜻은 아니다.

---

# 7. Task State

Task State의 후보:

- Goal
- Requirements
- Constraints
- Plan
- Progress
- Current Step
- Completed Steps
- Pending Steps
- Blockers
- Verification
- Artifacts
- Next Action
- Task Metadata

이 중 어떤 것이 canonical state인지 검증한다.

---

# 8. Execution State

Execution State의 후보:

- Current Turn
- Active Tool
- Pending Tool Result
- Retry Count
- Approval State
- Cancellation State
- Runtime Instance
- Checkpoint
- Error State

Task State와 Execution State를 동일하게 저장하지 않는 방향을 검토한다.

---

# 9. Task State vs Execution State

핵심 구분:

```text
Task State
= "무엇을 어디까지 했는가?"

Execution State
= "지금 실행이 어디에 있는가?"

예:

Task State:

Task:
Runtime PoC 완료

Execution State:

현재:
Test execution 중
PID / Tool / Retry

Runtime이 죽어도 Task State는 남아야 할 가능성이 높다.

10. Runtime Responsibility

Runtime이 담당할 후보:

Turn execution
Tool execution
Retry
Cancellation
Pause
Resume
Checkpoint
Persistence coordination
Event emission
Recovery

Runtime은 Task의 목표 자체를 정의하지 않는다.

11. Task Responsibility

Task subsystem의 책임 후보:

Goal
Constraints
Progress
Completion Criteria
Verification Status
Artifacts
Plan Reference

Task는 Runtime implementation과 독립적이어야 한다.

12. Context Responsibility

Context는:

Task State
+
Memory
+
Recent Conversation
+
Environment Observation
+
Tool Result
+
Policy

등에서 현재 실행에 필요한 정보만 선택하여 구성한다.

즉:

Task State
      ↓
Context Projection
      ↓
Model

이다.

13. Task State vs Context

현재 가설:

Task State
= canonical

Context
= projection

따라서:

Context lost
→ Task State survives

가 가능해야 한다.

14. Task State vs Memory

Task State:

현재 작업의 canonical progress.

Memory:

과거 경험과 지식.

예:

Task State:

"README 수정 완료"

Memory:

"과거 README 구조를 변경할 때 이 방식에서 문제가 발생했다."

둘을 혼합하지 않는다.

15. Task State vs Workspace State

Workspace State는 실제 환경의 현재 상태다.

예:

Task State:

"테스트를 완료했다."

Workspace State:

"테스트 결과 파일이 존재한다."

두 상태가 불일치할 수 있다.

따라서 Task completion은 Workspace / Environment verification을 필요로 할 수 있다.

16. Canonical State

가장 중요한 질문:

무엇이 Truth Source인가?

후보:

Task Store
Runtime State
Workspace
Event Log
Database

현재 가설:

Task의 canonical state는 외부 durable store에 존재한다.

Workspace는 observation source이고 Runtime은 execution source다.

이 가설을 검증한다.

17. Durable State

Runtime이 종료되어도 남아야 할 후보:

Task identity
Goal
Progress
Constraints
Completion state
Artifacts references
Verification status
Important checkpoints
18. Ephemeral State

Runtime 종료 시 사라져도 되는 후보:

Active process
Temporary cache
Current model context
Temporary tool output
In-memory execution object

단, 복구에 필요한 정보는 checkpoint 또는 durable state로 승격할 수 있어야 한다.

19. Checkpoint

Checkpoint의 목적:

현재 작업을 나중에 다시 시작할 수 있는 충분한 상태를 보존한다.

후보:

Task State
+
Execution Metadata
+
Workspace Reference
+
Context Reference

전체 Context를 무조건 snapshot할 필요는 없다.

20. Pause / Resume

후보 흐름:

Running
 ↓
Checkpoint
 ↓
Paused
 ↓
New Runtime
 ↓
Restore
 ↓
Resume

Resume 시 기존 Model Context를 그대로 복원해야 하는지, State에서 새 Context를 재구성해야 하는지 비교한다.

현재는:

State에서 fresh Context를 재구성하는 방향

을 유력 후보로 둔다.

21. Failure Recovery

Runtime failure:

Runtime Crash
 ↓
Persisted Task State
 ↓
Recovery
 ↓
New Runtime
 ↓
Resume

Task 자체를 잃지 않는 것이 목표다.

22. Tool Side Effects

가장 어려운 문제 중 하나다.

예:

Tool
→ send_email
→ external mutation

Runtime이 죽은 뒤 재시도하면 중복 실행될 수 있다.

따라서:

Idempotency
Execution Record
Side Effect Tracking
Compensation

을 연구한다.

23. Exactly Once vs At Least Once

Agent Tool execution은:

At-most-once
At-least-once
Exactly-once

중 무엇을 보장할 수 있는지 검토한다.

외부 side effect에서는 현실적으로 exactly-once 보장이 어렵기 때문에 idempotency와 compensation이 중요할 가능성이 높다.

24. Event Log

Event Log 후보:

TaskCreated
TaskUpdated
ExecutionStarted
ToolCalled
ToolCompleted
CheckpointCreated
ApprovalRequested
ExecutionPaused
ExecutionResumed
VerificationPassed
TaskCompleted

Event Log를 canonical state 자체로 사용할지는 아직 결정하지 않는다.

25. Event Sourcing

Full Event Sourcing을 사용할 것인지 검토한다.

장점:

Replay
Audit
State reconstruction

단점:

Complexity
Storage
Schema evolution
Recovery complexity

현재는 Defer 후보.

26. Long-Horizon Task

NOAH는 장기 작업을 지원해야 한다.

후보:

Hours
Days
Weeks

동안 Task State가 유지되어야 한다.

따라서 Session lifetime보다 Task lifetime이 길어질 수 있다.

27. Task Identity

Task에는 stable ID가 필요하다.

Task ID
Created At
Owner
Goal
Version
Status

Session과 Runtime이 바뀌어도 Task ID는 유지된다.

28. Task Versioning

Task 목표가 변경될 수 있다.

예:

Task v1
→ Original Goal

Task v2
→ Requirements changed

변경 history를 유지할 필요성을 검토한다.

29. Task Mutation

Task State는 Agent가 자유롭게 변경하는 Memory와 다르다.

예:

Agent Proposal
 ↓
Validation
 ↓
Task State Mutation

중요한 변경에는 verification을 요구한다.

30. Task Completion

Task completion은:

Agent Claim

만으로 결정하지 않는다.

후보:

Postconditions
+
Evidence
+
Verification
+
State Update

로 결정한다.

31. Task Reopening

완료된 Task가 다시 열릴 수 있다.

예:

Completed
 ↓
New Requirement
 ↓
Reopened
 ↓
Running

따라서 Completed가 항상 terminal state인지 검토한다.

32. Task vs Workflow

Workflow는 실행 절차다.

Task는 목표다.

Task
→ "Release Project"

Workflow
→ backup
→ test
→ build
→ deploy

하나의 Task가 여러 Workflow를 사용할 수 있다.

33. Task vs Plan

Plan은 Task를 달성하기 위한 전략이다.

Task
 ↓
Plan
 ↓
Execution

Plan은 변경될 수 있지만 Task Goal은 유지될 수 있다.

34. Replanning

계획이 실패하면:

Task
 ↓
Plan A
 ↓
Failure
 ↓
Plan B

가 가능하다.

Task State에는 현재 Plan Reference를 저장하고, 과거 Plan은 History로 남기는 방향을 검토한다.

35. Task State and Orchestration

Orchestrator는 Task State를 읽고:

분해
Delegation
Replanning
Budget allocation

을 수행한다.

하지만 Task State 자체를 Orchestrator 내부 memory로만 두지 않는다.

36. Runtime State and Orchestration State

Orchestration State:

Active agents
Dependencies
Plan
Pending work

Runtime State:

Current execution
Tool
Turn
Retry
Pause

둘의 경계를 분리할 필요가 있다.

37. Task State and Memory

Memory가 Task의 canonical state를 대신하지 않는다.

Memory:

"과거에 이 Task에서 이런 문제가 있었다."

Task State:

"현재 Task가 Blocked 상태다."
38. Task State and Evaluation

Evaluation 결과 중 일부는 Task State를 변경할 수 있다.

Verification Failed
 ↓
Task State
→ blocked

즉 Evaluation은 Task State mutation을 trigger할 수 있다.

39. Task State and Identity

Task State는 Identity보다 낮은 계층이다.

Identity
 ↓
Agent
 ↓
Task

Task가 실패해도 Identity가 변경되는 것은 아니다.

40. Task State and User

User는 Task를:

create
inspect
modify
pause
resume
cancel
reopen

할 수 있어야 할 가능성이 높다.

특히 long-running Task에서 중요하다.

41. User Control

Candidate:

Pause
Resume
Cancel
Approve
Modify
Reprioritize
Replan

을 지원한다.

단, Security / Permission 정책을 통과해야 한다.

42. Task State Visibility

User에게 모든 내부 state를 보여줄 필요는 없다.

Candidate:

Task Summary
Progress
Current Step
Blockers
Next Step
Last Verification

정도를 User-facing projection으로 제공한다.

43. Runtime Independence

Runtime을 교체할 수 있어야 한다.

Runtime A
→ Runner-based

Runtime B
→ Actor-based

Runtime C
→ Distributed

Task State Contract는 유지.

44. Durable Execution Research

최신 Agent runtime들은 점점:

checkpoint
resume
sandbox snapshot
externalized state

를 강조하고 있다.

OpenAI는 최신 Agents SDK에서 harness와 sandbox/compute를 분리하고 snapshot / rehydration을 통해 실행을 이어가는 방향을 공개했다. 이 자료는 NOAH가 Runtime과 durable state의 경계를 연구할 때 중요한 현재 reference다.

45. Historical / Foundational Ideas

오래된 아이디어도 함께 검토한다.

Actor Model

독립적인 실행 단위와 Message-based state.

Workflow Engines

Long-running stateful execution.

Distributed Systems

Durability
Failure recovery
Idempotency
Consistency

Database Transactions

State mutation
Commit
Rollback

Event Sourcing

Event-based state reconstruction

Checkpoint / Restart

Long-running computation recovery

이 중 NOAH에 여전히 유효한 원칙을 추출한다.

46. Current Frontier

현재 연구에서 집중할 영역:

Durable Agent Execution
Task State Externalization
Checkpoint / Resume
Sandbox State
Long-Horizon Agent
Execution Recovery
Externalized Context
State-aware Runtime
Agent Harness
47. Candidate State Model

현재 연구 후보:

Task
│
├── Goal
├── Constraints
├── Plan
├── Progress
├── Verification
├── Artifacts
├── Status
└── History

Runtime:

Execution
│
├── Turn
├── Tool
├── Retry
├── Approval
├── Checkpoint
└── Events
48. Candidate Boundary
Task Store
    │
    ├── Task State
    │
    └── Task History

Runtime
    │
    └── Execution State

Context Manager
    │
    └── Context Projection

이 구조를 가장 먼저 검증한다.

49. Candidate Flow
User
 ↓
Task
 ↓
Task State
 ↓
Orchestrator
 ↓
Runtime
 ↓
Execution
 ↓
Environment
 ↓
Observation
 ↓
Verification
 ↓
Task State Update
50. Candidate Recovery Flow
Task State
 ↓
Runtime A
 ↓
Crash
 ↓
Persisted State
 ↓
Runtime B
 ↓
Context Reconstruction
 ↓
Resume
51. Candidate Context Reconstruction

Resume 시:

Task State
+
Memory
+
Relevant History
+
Environment Observation
+
Workspace State
+
Policy
        ↓
New Context

로 재구성할 수 있다.

이 구조가 Model Context 자체를 checkpoint하는 것보다 미래에 더 유연할 가능성을 검토한다.

52. Candidate Architecture
                         TASK
                          │
                    Canonical State
                          │
                    Orchestration
                          │
                      Runtime
                          │
              ┌───────────┼───────────┐
              │           │           │
           Context      Execution   Events
              │           │           │
              └───────────┼───────────┘
                          │
                       Sandbox
                          │
                     Environment
                          │
                     Verification
                          │
                    State Update
53. Risks
State Duplication

Task State가 Runtime, Memory, Context에 중복 저장될 수 있다.

Stale State

Persisted Task State와 실제 Environment가 달라질 수 있다.

Recovery Ambiguity

Tool side effect 이후 어디에서 resume해야 하는지 불명확할 수 있다.

Consistency

Task State와 Workspace State가 서로 다른 상태일 수 있다.

Complexity

Durable execution을 지나치게 일찍 도입하면 시스템이 복잡해질 수 있다.

54. Open Questions
Task State의 canonical storage는 어디인가?
Task Store가 별도 subsystem이어야 하는가?
Session은 Task State를 직접 소유하는가?
Execution State와 Orchestration State의 정확한 경계는?
Runtime crash 후 어느 시점부터 재개해야 하는가?
Tool side effect를 어떻게 추적하는가?
Checkpoint는 언제 만드는가?
Context를 snapshot할 것인가, 재구성할 것인가?
Workspace State를 어떻게 검증하는가?
Task 완료를 누가 최종 승인하는가?
Task State mutation을 Agent가 직접 수행할 수 있는가?
Event Log를 Source of Truth로 사용해야 하는가?
Task versioning이 필요한 수준은?
여러 Session이 하나의 Task를 동시에 실행할 수 있는가?
Multi-Agent가 동일 Task State를 공유하면 어떻게 lock/coordination하는가?
Task State가 Memory와 얼마나 연결되어야 하는가?
Long-running Task의 TTL / retention은?
Task가 수개월 지속될 때 어떤 state를 유지해야 하는가?
55. Research Findings

이 부분은 실제로 조사하면서 채운다.

구조:

Reference
Problem
Approach
Strengths
Weaknesses
NOAH Relevance
Stable Principle
Implementation-specific Detail

Reference 후보:

OpenCode
Grok Build
OpenAI Agents SDK
Anthropic long-running agents
Durable execution systems
Actor Model
Workflow engines
Distributed systems research
최근 long-horizon agent 연구
56. Historical / Current / Emerging Comparison
시대/출처	핵심 아이디어	현재 유효성
Actor Model	독립 실행 + 메시지	High
Workflow Engine	Durable workflow state	High
Distributed Systems	Failure / Recovery	High
Event Sourcing	State reconstruction	Conditional
OpenCode	Session / Runner	High
Grok Build	Actor / Turn	High
OpenAI SDK	Harness / Sandbox / Rehydration	Emerging / High
Long-horizon research	External Task State	Emerging / High

구체적인 판단은 Research 후 확정한다.

57. Stable Principles vs Replaceable Implementations

현재 가설:

Stable
Task Identity
Task State
Execution Contract
Recovery Contract
Verification Contract
Replaceable
Runtime Framework
Storage
Checkpoint Mechanism
Sandbox
Event Infrastructure
Model
58. Future Resilience

미래에 Runtime이 완전히 달라져도:

Task
Goal
Progress
Verification

이 유지된다면 NOAH는 계속 작업을 이어갈 수 있어야 한다.

즉:

Runtime은 교체 가능하지만 Task는 지속적이다.

가 핵심 후보 원칙이다.

59. Preliminary Recommendation

현재까지의 지식만으로는:

Task State를 Runtime과 분리하고, Task State를 durable canonical state로 관리하며, Runtime은 execution state를 담당하고, Context는 필요한 상태를 projection하는 구조

를 가장 유력한 후보로 둔다.

Task Store
   ↓
Task State
   ↓
Runtime
   ↓
Execution
   ↓
Verification
   ↓
Task State Update

단, 이것은 Preliminary Recommendation이며, 추가 Research 이후 변경될 수 있다.

60. What This Research Must Decide

이번 Research가 끝나면 다음 질문에 답할 수 있어야 한다.

1. Task State란 정확히 무엇인가?
2. Task는 Session과 어떻게 다른가?
3. Runtime은 정확히 어디까지 책임지는가?
4. Execution State는 어디에 존재하는가?
5. Canonical State는 무엇인가?
6. Checkpoint는 무엇을 보존하는가?
7. Recovery는 어떻게 이루어지는가?
8. Context는 State에서 어떻게 재구성되는가?
9. Tool Side Effect는 어떻게 추적되는가?
10. 미래 Runtime으로 교체해도 Task가 유지되는가?
61. Research Completion Criteria

이번 P0 Research는 다음 조건을 만족하면 완료한다.

☐ Task / Session 경계 설명 가능
☐ Task State / Execution State 경계 설명 가능
☐ Canonical State 결정
☐ Durable / Ephemeral State 구분
☐ Checkpoint 전략 후보
☐ Recovery 전략 후보
☐ Context reconstruction 전략 후보
☐ Tool side effect 전략 후보
☐ Runtime replacement 가능성 검증
☐ 주요 Open Question 정리
62. Next Step

이번 Research가 끝난 뒤:

Task State / Runtime Research
        ↓
Finding
        ↓
Integration Review Update
        ↓
Harness Boundary Research

로 넘어간다.

즉 이번 단계에서는 아직:

DDR 작성 ❌
Blueprint 수정 ❌
실제 Runtime 구현 ❌

이다.

63. Final Research Goal

이번 연구의 최종 목적은:

"NOAH가 작업을 잊지 않고 이어갈 수 있는 최소한의 Durable Task Model을 정의하는 것"

이다.