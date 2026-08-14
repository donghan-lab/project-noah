# Architecture Review — Session & Runtime

> Project NOAH Architecture Review
> Review 대상: Session & Runtime Architecture
> Review Version: 0.1
> Status: Review

---

# 1. Review Purpose

Project NOAH에서 Agent가 단일 응답을 넘어 장시간 작업을 수행할 수 있도록 Session과 Runtime의 책임과 경계를 정의하기 위한 Architecture Review를 수행한다.

본 리뷰의 핵심 질문은 다음과 같다.

> **"NOAH가 장시간 작업을 수행할 때 무엇을 지속적으로 보존하고, 무엇을 실행 상태로 관리하며, 무엇을 복구할 수 있어야 하는가?"**

본 리뷰는 OpenCode, Grok Build, Connect AI 및 최신 Agent Runtime 연구를 비교하여 NOAH에 적합한 Session / Runtime Architecture의 방향을 도출한다.

최종 구현은 아직 결정하지 않는다.

---

# 2. Core Architecture Question

## Session이란 무엇인가?

초기 후보:

> Session은 사용자와 Agent 사이의 모든 지속적인 상호작용과 그 실행 상태를 관리하는 논리적 단위다.

그러나 Session은 단순한 Conversation History와 동일하지 않을 가능성이 높다.

현재 검토해야 할 상태:

```text
Session
├── Conversation State
├── Task State
├── Execution State
├── Context State
├── Approval State
├── Environment State
├── Workspace State
├── Memory References
└── Recovery State
```

---

# 3. Runtime이란 무엇인가?

Runtime은 Agent를 실제로 실행하고 상태를 변화시키는 계층이다.

후보 책임:

```text
Runtime
├── Agent Execution
├── Turn Management
├── Tool Execution
├── State Transition
├── Cancellation
├── Retry
├── Pause / Resume
├── Persistence
├── Event Handling
├── Recovery
└── Lifecycle Management
```

따라서 Session은 "지속되는 논리적 상태", Runtime은 "그 상태를 변화시키는 실행 환경"으로 분리하는 방향을 검토한다.

---

# 4. Current Reference Findings

## OpenCode

OpenCode V2는 Session과 SessionExecution / SessionRunner를 분리한다.

주요 개념:

```text
Session
 ↓
SessionExecution
 ↓
SessionRunner
 ↓
Context
 ↓
LLM
 ↓
Tool
 ↓
Settlement
 ↓
Next Turn
```

또한 durable inbox, Context Epoch, compaction, tool settlement 등의 개념을 사용하여 장기 실행 상태를 관리한다.

---

## Grok Build

Grok Build는 Agent Runtime 아래에 Session Registry와 Session Actor를 두고, Session Actor가 Command / Event / Chat State 등을 지속적으로 조정하는 구조를 보여준다.

```text
MvpAgent
 ↓
SessionRegistry
 ↓
SessionActor
 ↓
Run Loop
 ↓
Turn
```

Session Lifecycle 자체가 approval, resume, background tasks, memory flush, cleanup 등의 실행 흐름과 연결된다.

---

## Connect AI

Connect AI는 OpenCode와 Grok Build보다 Session/Runtime을 상대적으로 가볍게 구성하고, VS Code Extension의 Chat State와 Local Persistence에 더 강하게 결합되어 있다.

이는 장기 실행 Agent Runtime보다는 개인용 IDE Agent와 Knowledge System에 초점을 둔 구조로 볼 수 있다.

---

# 5. Frontier Research — Long-Horizon Agents

최근 Agent 시스템은 몇 분짜리 task보다 수시간, 수일에 걸친 long-horizon task를 처리하는 방향으로 발전하고 있다.

Anthropic은 long-running agent에서 context window 사이의 작업 연속성을 유지하기 위해 initializer agent와 coding agent, 명확한 persistent artifacts 등을 사용한다.

2026 Agentic Coding Trend에서도 Agent가 여러 work session에 걸쳐 계획하고, 반복하고, 실패를 복구하고, 일관된 state를 유지하는 방향이 강조되고 있다.

### NOAH Question

> Session은 단순히 대화를 보존하는 단위인가, 아니면 장기 작업의 연속성을 보존하는 단위인가?

초기 판단:

**Long-horizon Task State를 Session과 분리하여 명시적으로 관리할 필요가 있다.**

---

# 6. Session vs Conversation vs Task

세 개념을 분리하는 것을 검토한다.

```text
Conversation
= 사용자와 Agent의 대화 기록

Task
= 달성해야 하는 목표와 진행 상태

Session
= 특정 작업을 지속적으로 실행하기 위한 논리적 컨테이너
```

예:

```text
Session
├── Conversation
├── Task
│   ├── Goal
│   ├── Progress
│   ├── Current Step
│   └── Verification
└── Runtime State
```

이 구분이 장기 실행에서 중요할 가능성이 높다.

---

# 7. Externalized Task State

최근 연구에서는 긴 작업에서 모든 상태를 Context 안에 계속 유지하는 대신 **명시적인 외부 Task State**를 사용하는 방향이 연구되고 있다.

이는 Context와 Task State를 분리하여 fresh-context executor가 현재 상태를 다시 읽고 작업하도록 만드는 접근이다.

### NOAH Question

> Task State를 LLM Context에만 의존해도 되는가?

초기 판단:

**아니다.**

Task State는 가능하면 외부의 구조화된 상태로 보존하고 Context에는 필요한 부분만 투입하는 방향을 검토한다.

---

# 8. Proposed State Taxonomy

현재 Review에서 가장 중요한 후보 중 하나다.

```text
State
├── Conversation State
├── Task State
├── Execution State
├── Context State
├── Environment State
├── Workspace State
├── Memory State
└── Approval / Policy State
```

각 State는 서로 다른 수명과 저장 요구사항을 가진다.

---

# 9. Execution State

Runtime이 현재 수행 중인 작업 상태.

후보:

```text
Execution State
├── Current Turn
├── Active Tool Calls
├── Pending Approval
├── Retry Count
├── Cancellation State
├── Current Agent
└── Execution Checkpoint
```

이 상태는 Session의 영속 상태와 구분될 필요가 있다.

---

# 10. Durable Execution

OpenAI의 2026 Agents SDK는 Agent harness와 compute를 분리하고, sandbox 상태를 snapshot / rehydration하여 실행 환경이 사라져도 Agent state를 유지하고 계속 실행할 수 있는 구조를 제공한다.

### NOAH Question

> 프로세스나 Sandbox가 종료되어도 작업을 계속할 수 있어야 하는가?

초기 판단:

**장기 목표에서는 Yes.**

단, 초기 구현에서는 단순한 persistence부터 시작하고 checkpoint/rehydration은 단계적으로 발전시키는 것이 적절하다.

---

# 11. Pause / Resume

Agent 작업은 항상 연속적으로 실행되지 않는다.

예:

```text
Running
 ↓
Waiting for Approval
 ↓
Paused
 ↓
Resume
 ↓
Continue
```

또는:

```text
Running
 ↓
Environment Failure
 ↓
Checkpoint
 ↓
New Runtime
 ↓
Resume
```

Grok Build의 Plan Approval / Resume 구조와 OpenCode의 durable session 구조는 이 문제를 서로 다른 방식으로 다룬다.

---

# 12. Cancellation

Runtime은 작업을 중단할 수 있어야 한다.

그러나 단순히 process를 kill하는 것으로 충분하지 않을 수 있다.

중단 시:

* 현재 Tool 상태
* Persistence
* Memory write
* Partial output
* External side effect
* Sandbox state

를 고려해야 한다.

### NOAH Question

> Cancellation은 Runtime control인가, Session state인가?

초기 판단:

**Runtime이 cancellation을 수행하고 결과는 Session / Execution state에 기록하는 구조를 검토한다.**

---

# 13. Retry

모든 실패를 자동 재시도하면 안 된다.

실패 유형:

```text
Transient
├── Network
├── Provider
└── Temporary Resource

Deterministic
├── Invalid Input
├── Permission
└── Tool Contract

Semantic
├── Wrong Plan
├── Wrong Tool
└── Wrong Assumption

External Side Effect
├── Already Applied
└── Partially Applied
```

따라서 Retry Policy를 Runtime의 독립적인 정책으로 관리하는 방향을 검토한다.

---

# 14. Event-Driven Runtime

Grok Build의 Session Actor 구조는 Command / Event 중심으로 Session Lifecycle을 관리한다.

OpenCode 역시 Session Event와 Tool Settlement를 통해 실행 상태를 기록한다.

### 후보 구조

```text
Event
├── PromptAccepted
├── TurnStarted
├── ToolCalled
├── ToolCompleted
├── ApprovalRequested
├── ApprovalGranted
├── StateCheckpointed
├── TurnCompleted
├── TaskCompleted
└── SessionClosed
```

이 구조는 Observability, Recovery, Audit, Replay에 도움이 될 수 있다.

---

# 15. Event Sourcing vs Event Logging

모든 Event를 시스템의 진실 원천(source of truth)으로 사용할 필요는 없다.

후보:

### Event Logging

현재 상태는 별도로 저장하고 Event는 관찰/감사/디버깅에 사용.

### Event Sourcing

Event 자체가 상태의 진실 원천이 되고 필요할 때 상태를 재구성.

초기 NOAH에서는 **Event Logging을 우선 검토**하고 Full Event Sourcing은 필요성이 확인될 때 추가 연구한다.

---

# 16. Context vs State

Context와 State를 동일한 개념으로 취급하지 않는다.

```text
State
= 시스템이 실제로 유지하는 정보

Context
= 현재 Model Turn에 필요한 State의 일부
```

즉:

```text
Durable State
      ↓
Context Selection
      ↓
Model Context
```

구조를 우선 검토한다.

---

# 17. Context Compaction

Anthropic은 long-horizon agent에서 compaction을 중요한 전략으로 사용하고 있으며, OpenCode도 Context Epoch 및 compaction 구조를 가지고 있다.

NOAH에서는:

```text
Full State
 ↓
Relevant State Selection
 ↓
Context Compression
 ↓
Current Context
```

처럼 전체 상태와 현재 Context를 분리하는 것을 검토한다.

---

# 18. Session Boundary

Session은 언제 끝나는가?

후보:

* User termination
* Task completion
* Explicit close
* Timeout
* Resource limit
* Fatal failure

그러나 장기 Agent에서는 Session 종료와 Task 완료를 동일하게 취급하지 않는 것이 중요할 수 있다.

예:

```text
Session 1
 ↓
Checkpoint
 ↓
Session 2
 ↓
Task continues
```

---

# 19. Workspace / Environment State

Workspace는 Session과 동일하지 않다.

```text
Session
     ↓
Execution Environment
     ↓
Workspace
     ├── Files
     ├── Processes
     ├── Dependencies
     └── Artifacts
```

OpenAI의 최신 Agent SDK 역시 Agent harness와 실제 compute 환경을 분리하는 방향을 강조한다.

---

# 20. Sandbox

Agent가 파일, shell, network 등을 사용할 수 있다면 Runtime과 Sandbox 경계가 중요하다.

Anthropic은 Agent의 capability가 높아질수록 blast radius를 제한하기 위한 containment가 중요해진다고 설명한다.

### NOAH Candidate

```text
Agent
 ↓
Policy
 ↓
Sandbox
 ↓
External Environment
```

Agent가 직접 host 권한을 소유하는 구조는 기본값으로 두지 않는다.

---

# 21. Resource Management

Agent Runtime은 LLM token만 소비하지 않는다.

2026년 Agent-serving 연구에서는 persistent context와 sandboxed tool execution 때문에 기존 token-centric metric만으로는 실제 병목을 설명하기 어렵다고 지적하며, tool sandbox의 idle/burst 패턴과 state management 비용도 중요한 문제로 보고 있다.

NOAH는 장기적으로:

```text
Cost
Latency
Token
CPU
Memory
Storage
Sandbox Time
Tool Time
```

을 함께 관측할 수 있는 구조를 고려해야 한다.

---

# 22. Observability

Runtime은 최소한 다음을 추적할 수 있어야 한다.

```text
Task
Session
Turn
Agent
Model
Tool
Permission
State Change
Latency
Cost
Error
Recovery
```

이를 하나의 Trace / Episode로 묶는 방향을 검토한다.

최근 AI Harness 연구도 Agent 실행 전체를 auditable episode package로 남기고 task specification, context selection, tool access, memory, observability, verification 등을 함께 기록하는 방향을 제안한다.

---

# 23. Verification

Agent가 "완료했다"고 말하는 것과 실제로 Task가 완료된 것은 다르다.

### Candidate

```text
Agent claims completion
        ↓
Verification
        ↓
Evidence
        ↓
Task completion
```

검증 증거:

* Test
* File Diff
* Command Output
* Artifact
* State Check
* External Confirmation

2026년 최신 연구에서도 Agent safety를 runtime contract와 evidence chain의 문제로 보는 방향이 제안되고 있다.

---

# 24. Recovery

Recovery는:

```text
Failure
 ↓
Diagnose
 ↓
Checkpoint
 ↓
Restore
 ↓
Resume
```

의 구조를 가져야 한다.

단순 Retry와 Recovery는 구분한다.

```text
Retry
= 같은 실행을 다시 시도

Recovery
= 저장된 상태에서 새로운 실행을 시작
```

---

# 25. Session and Runtime Candidate Architecture

현재 Review를 종합하면 다음 구조가 후보가 된다.

```text
                           NOAH
                             │
                           Agent
                             │
                     ┌───────┴───────┐
                     │               │
                  Session           Task
                     │               │
                     └───────┬───────┘
                             │
                        Runtime
                             │
              ┌──────────────┼──────────────┐
              │              │              │
           Context        Execution      Policy
              │              │              │
              │         ┌────┼─────┐        │
              │         │    │     │        │
              │       Turn  Tool  Event     │
              │         │    │     │        │
              └─────────┼────┼─────┼────────┘
                        │
                     Sandbox
                        │
                   Environment
                        │
                   Persistence
                        │
                     Recovery
```

이 역시 **Candidate Architecture**이며 최종 Blueprint가 아니다.

---

# 26. Future Resilience

이번 Review에서는 현재 기술보다 **미래 변화에 견디는 경계**를 중요하게 평가한다.

검토 기준:

```text
현재 구현에 종속되어 있는가?
          ↓
무엇이 바뀌면 깨지는가?
          ↓
Interface를 어디에 둘 것인가?
          ↓
미래 Runtime 교체가 가능한가?
```

예:

```text
❌ OpenCode-style Runner를 그대로 고정

✅ SessionExecution Interface 정의
   ↓
OpenCode-like Runtime
Grok-like Runtime
Future Runtime
```

구현을 교체해도 Session의 상위 계약은 유지되도록 설계한다.

---

# 27. Stable vs Replaceable Boundaries

## Stable

* Session identity
* Task identity
* State model
* Event contract
* Execution contract
* Recovery contract

## Replaceable

* LLM Provider
* Runner implementation
* Tool runtime
* Sandbox implementation
* Storage implementation
* Context compaction algorithm

이 구분은 앞으로 NOAH가 특정 Agent Framework나 Model Runtime에 종속되는 것을 막기 위한 핵심 후보 원칙이다.

---

# 28. Candidate Decisions

| 영역                             | 초기 판단            |
| ------------------------------ | ---------------- |
| Session ≠ Conversation         | Adopt            |
| Task를 Session과 분리              | Adapt            |
| Execution State 분리             | Adopt            |
| Context ≠ State                | Adopt            |
| Durable State                  | Adopt            |
| Event Logging                  | Adopt            |
| Full Event Sourcing            | Defer            |
| Pause / Resume                 | Adopt            |
| Cancellation                   | Adopt            |
| Typed Retry Policy             | Adapt            |
| Recovery                       | Adopt            |
| Sandbox 분리                     | Research Further |
| Externalized Task State        | Research Further |
| Context Compaction             | Adopt            |
| Trace / Observability          | Adopt            |
| Evidence-based Verification    | Adapt            |
| Runtime 구현 교체 가능성              | Adopt            |
| Multi-node distributed runtime | Defer            |
| Agent Runtime과 Compute 분리      | Research Further |

---

# 29. Architecture Risks

## Complexity Risk

State 종류와 Runtime 계층이 지나치게 많아질 수 있다.

## Persistence Cost

모든 상태를 영속화하면 storage / performance 비용이 증가한다.

## Recovery Complexity

Tool이 외부 side effect를 발생시킨 경우 단순 checkpoint 복원이 충분하지 않을 수 있다.

## Consistency Risk

Context, Task State, Workspace State, Memory가 서로 다른 시점에 업데이트될 수 있다.

## Event Growth

모든 실행을 기록할 경우 Event와 Trace가 매우 커질 수 있다.

## Sandbox Cost

격리된 실행 환경은 security를 높이지만 startup, storage, snapshot 비용을 증가시킬 수 있다.

---

# 30. Open Questions

1. Session과 Task의 정확한 경계는 무엇인가?
2. 하나의 Session에서 여러 Task를 실행할 수 있는가?
3. Task State는 어떤 데이터 모델을 가져야 하는가?
4. Runtime State 중 반드시 durable해야 하는 것은 무엇인가?
5. Context Epoch와 Task State versioning은 같은 개념인가?
6. Tool side effect를 어떻게 transactionally 추적할 것인가?
7. Checkpoint는 어느 시점에 생성하는가?
8. Sandbox snapshot을 사용해야 하는가?
9. Memory write는 Runtime과 동기적으로 실행해야 하는가?
10. Event Log는 replay 가능한가?
11. Recovery 후 Agent가 자신의 이전 상태를 어떻게 이해하는가?
12. Task가 여러 Session으로 이어질 때 identity는 어떻게 유지되는가?
13. Agent가 바뀌어도 Task State를 계속 사용할 수 있는가?
14. Runtime 구현이 완전히 교체되어도 Session State를 유지할 수 있는가?

---

# 31. Current Recommendation

현재 근거로는 다음 방향을 우선 검토한다.

> **NOAH는 Conversation 중심 Session보다 Task 중심의 Durable Session/Runtime을 지향한다.**

그리고:

```text
Session
  ↓
Task
  ↓
Execution
  ↓
State
  ↓
Context
  ↓
Model / Tools
```

을 기본적인 계층으로 둔다.

Runtime은:

* pause
* resume
* cancellation
* retry
* persistence
* recovery
* observability

를 제공한다.

실행 환경은 Sandbox / Workspace와 분리하며, Model이나 Runtime 구현은 교체 가능하게 유지한다.

---

# 32. Review Boundary

이번 Review에서는 다음을 확정하지 않는다.

* 최종 Session data model
* 최종 Runtime framework
* 최종 Event schema
* 최종 Sandbox
* 최종 Storage
* 최종 Context Manager
* 최종 Memory Architecture

이 항목들은 후속 Architecture Review와 PoC에서 검증한다.

---

# 33. Review Outcome

현재까지의 Research에서 확인되는 공통 방향은 다음과 같다.

Agent가 발전할수록 단순 대화 Session보다:

* Durable State
* Long-Horizon Task
* Context Management
* Tool Execution
* Sandbox
* Recovery
* Observability
* Verification

의 중요성이 증가한다. Anthropic은 2026년 long-running agent와 context engineering에서 structured memory, compaction, subagents와 같은 패턴을 강조하고 있으며, OpenAI는 sandbox와 compute를 분리하고 snapshot/rehydration을 통한 durable execution을 지원하는 방향으로 Agents SDK를 확장했다.

또한 최신 연구에서는 Agent Harness를 task specification, context, tools, memory, task state, observability, verification, permissions까지 포함하는 runtime substrate로 보는 관점이 등장하고 있다.

따라서 NOAH Runtime은 단순한 Agent Loop 구현보다 **장기 실행 가능한 상태 관리와 검증 가능한 실행 환경**을 중심으로 설계해야 할 가능성이 높다.

---

# 34. Next Step

이번 Review 후 바로 Blueprint를 수정하지 않는다.

다음 순서:

```text
Session & Runtime Review
          ↓
Open Questions 정리
          ↓
필요한 추가 Research
          ↓
Candidate Architecture
          ↓
DDR
          ↓
02-Architecture
          ↓
Runtime PoC
          ↓
Evaluation
```

다음 Architecture Review에서는 **Context & State Management**를 별도로 검토한다.

특히:

```text
Context
Memory
Task State
Environment State
Conversation
```

의 경계를 결정하는 것을 목표로 한다.
