# Architecture Review — Agent

> Project NOAH Architecture Review
> Review 대상: Agent Architecture
> Review Version: 0.1
> Review Scope: Agent Identity, Role, Capability, Policy, Context, Runtime, Memory, Orchestration, Sandbox, Evaluation
> Status: Review

---

# 1. Review Purpose

Project NOAH에서 정의해야 할 "Agent"의 역할과 책임 범위를 결정하기 위한 Architecture Review를 수행한다.

본 리뷰의 목적은 특정 프로젝트의 구조를 채택하는 것이 아니다.

OpenCode, Grok Build, Connect AI와 최신 Agent research 및 production architecture를 비교하여:

* Agent가 무엇이어야 하는가?
* 무엇을 Agent 내부에 둘 것인가?
* 무엇을 Agent 외부 subsystem으로 분리할 것인가?
* 어느 수준까지 Agent를 자율적으로 만들 것인가?
* 어떻게 안전성과 설명 가능성을 확보할 것인가?
* 장기적으로 Agent가 경험을 통해 개선될 수 있는가?

를 판단한다.

본 문서의 결과는 최종 Architecture가 아니며, 필요한 최종 결정은 Decision/DDR 단계에서 기록한다.

---

# 2. Core Architecture Question

## "NOAH에서 Agent란 무엇인가?"

초기 가설:

> Agent는 LLM 그 자체가 아니라, Model을 중심으로 Context, Capability, Policy, Runtime, State를 조합하여 목표를 달성하는 실행 주체다.

2026년의 Agent 설계에서는 모델 자체보다 이를 둘러싼 harness/runtime이 실제 행동을 결정하는 중요한 계층으로 다뤄지고 있다. 최근 Agent Systems survey는 Agent를 reasoning, planning, memory, tool use, orchestration, evaluation을 결합하는 시스템으로 분류하며, latency·autonomy·reliability·cost 사이의 trade-off를 핵심 설계 문제로 제시한다.

따라서 NOAH는 Agent를 단순한 "LLM wrapper"로 정의하지 않는 방향을 우선 검토한다.

---

# 3. Review Inputs

## 3.1 Reference Implementations

### OpenCode

주요 관찰:

* Primary Agent / Subagent
* Agent별 Model
* Permission
* Tool abstraction
* Session / Execution 분리
* Context Epoch
* Tool settlement
* Compaction
* Runtime loop

OpenCode는 Agent를 Session, Tool, Permission, Context, Runtime과 연결된 실행 단위로 모델링한다.

---

### Grok Build

주요 관찰:

* MvpAgent
* Session Registry
* Session Actor
* Command / Event loop
* Turn execution
* Skill / Workflow
* Persistence
* Approval / Resume
* ACP
* Memory / MCP / Plugin 연결

Grok Build는 Agent 자체보다 Agent를 둘러싼 Session Runtime과 Lifecycle orchestration이 강하게 드러나는 구조를 보여준다.

---

### Connect AI

주요 관찰:

* Agent Registry
* Role
* Specialty
* Persona
* CEO / Specialist 구조
* Local LLM
* Action-based capability
* Second Brain
* IDE integration

Connect AI는 Runtime abstraction보다 Agent의 역할/전문성/Persona와 Knowledge 중심의 조직 모델을 보여준다.

---

# 4. Frontier Review — 2026

현재 Agent 설계에서 Reference 프로젝트만 보는 것은 충분하지 않다.

최근 공개 자료를 보면 Agent architecture는 다음 방향으로 확장되고 있다.

## 4.1 Agent Harness

최근 연구는 Agent Harness를 base model을 executable agent로 변환하는 외부 control layer로 정의하며, context, tools, orchestration, memory, decoding, output handling까지 포함하는 계층으로 보고 있다. 2026년 7월 공개된 MemoHarness는 실행 경험을 축적해 harness 자체를 case별로 적응시키는 방향을 제안한다.

### NOAH 질문

> Agent와 Agent Harness를 동일한 개념으로 볼 것인가?

초기 판단:

**분리하는 방향을 우선 검토한다.**

```text
Model
  ↓
Agent
  ↓
Agent Harness
  ├── Context
  ├── Tools
  ├── Policy
  ├── Memory
  ├── Orchestration
  └── Evaluation
```

Agent는 "무엇을 할 것인가"에 가깝고, Harness는 "그것을 어떻게 실행할 것인가"에 가깝게 정의할 가능성이 있다.

---

# 5. Frontier Review — Sandbox / Compute Separation

OpenAI의 2026 Agents SDK evolution은 Agent loop와 sandbox execution을 명시적으로 분리하는 방향을 취한다.

Agent는 instructions, tools, approvals, tracing, handoffs, resume bookkeeping 등을 담당하고, Sandbox는 파일, 명령, 패키지, artifact 및 격리된 실행 환경을 제공한다. 또한 sandbox state의 snapshot/rehydration을 통해 실행 중단 이후 복구하는 구조가 제시된다.

### NOAH 질문

> Agent가 실행 환경 자체를 소유해야 하는가?

초기 판단:

**Agent와 Compute/Workspace를 분리하는 방향이 강하게 유리하다.**

```text
Agent
  │
  ▼
Execution Policy
  │
  ▼
Sandbox / Workspace
```

이렇게 해야 자격 증명 보호, prompt injection 대응, 장기 실행, 복구 및 병렬 실행을 설계하기 쉬워진다. OpenAI도 harness와 compute를 분리하면 모델 생성 코드가 실행되는 환경에서 credentials를 분리하고, 상태를 외부화하여 sandbox 장애 이후 실행을 복구할 수 있다고 설명한다.

---

# 6. Frontier Review — Context Engineering

Anthropic의 최근 production guidance는 long-horizon agent에서:

* compaction
* structured memory
* subagent architecture
* just-in-time retrieval
* token-efficient tools

같은 Context Engineering 패턴을 중요하게 다룬다.

OpenCode의 Context Epoch와 Compaction 역시 같은 문제를 다른 방식으로 해결하려는 사례다.

### NOAH 질문

> Context는 Agent의 내부 상태인가, 독립 subsystem인가?

초기 판단:

**독립 Context Management Layer로 분리하는 방향을 검토한다.**

```text
Agent
   ↓
Context Manager
   ├── Instructions
   ├── Recent State
   ├── Memory Retrieval
   ├── Tools
   ├── Environment
   └── Working Context
```

Agent가 Context를 직접 "소유"하기보다 Context Manager가 현재 실행에 필요한 정보를 조립하는 구조가 장기적으로 더 유리할 가능성이 높다.

---

# 7. Frontier Review — Memory

2026년의 최신 memory survey는 Agent Memory를 단순 vector retrieval이 아니라:

```text
Write
 ↓
Manage
 ↓
Read
```

의 생명주기로 다루는 방향을 제시한다.

또한 temporal scope, representation, control policy를 기준으로 memory를 분류하고, consolidation, contradiction handling, forgetting, privacy governance를 핵심 문제로 제시한다.

### NOAH 질문

> Memory를 Agent의 내부 기능으로 둘 것인가?

초기 판단:

**NOAH에서는 Memory를 독립 subsystem으로 두는 쪽이 강하게 유력하다.**

```text
Agent
  ↓
Memory Interface
  ↓
Memory System
  ├── Working
  ├── Episodic
  ├── Semantic
  ├── Knowledge
  └── Experience
```

단, 이것은 현재 Agent Review에서 최종 결정하지 않는다.

Memory는 별도의 Architecture Review 대상이다.

---

# 8. Frontier Review — Multi-Agent

Anthropic의 최근 guidance는 Multi-Agent가 항상 좋은 것이 아니며, 특히 다음과 같은 경우에 가치가 커진다고 설명한다.

* Context isolation
* Parallel execution
* Specialization

반대로 불필요한 Multi-Agent는 시스템 복잡성만 증가시킬 수 있다.

### NOAH 질문

> NOAH는 처음부터 Multi-Agent인가?

초기 판단:

**아니다.**

NOAH는:

```text
Single Agent
    ↓
Specialist 필요
    ↓
Subagent
    ↓
Parallel / Isolated Agent
    ↓
Multi-Agent
```

처럼 **복잡도를 필요할 때만 증가시키는 구조**를 우선 검토한다.

이 원칙은 Anthropic의 "단순한 구조부터 시작하고 복잡성을 필요에 따라 추가"하는 접근과도 방향이 맞는다.

---

# 9. Frontier Review — Evaluation

Agent는 여러 번의 tool call과 state change를 수행하므로 단일 final answer만으로 평가하기 어렵다.

Anthropic의 2026 Agent eval guidance는 Agent가 multi-turn으로 동작하고 intermediate state를 바꾸기 때문에 평가 복잡도가 증가한다고 설명하며, eval을 개발 lifecycle에 일찍 통합할 것을 강조한다.

### NOAH 질문

> Evaluation은 개발 후 별도 작업인가?

초기 판단:

**아니다. Agent Architecture에 Evaluation을 연결할 수 있어야 한다.**

```text
Agent
 ↓
Execution
 ↓
Trace
 ↓
Evaluation
 ↓
Failure Analysis
 ↓
Improvement
```

단, Evaluation은 실행 시마다 모든 경로에 개입할 필요는 없으며, 환경에 따라 sampling / offline evaluation / regression evaluation을 조합하는 방향을 검토한다.

---

# 10. Frontier Review — Trust and Security

Agent가 파일, 명령, 외부 API 등을 직접 실행하면 Prompt Injection과 권한 오용이 핵심 위험이 된다.

Anthropic은 2026년 trustworthiness 연구에서 Agent의 자율성이 커질수록 의도 오해와 prompt injection으로 인한 unintended action 위험이 증가한다고 설명한다.

### NOAH 질문

> Agent에게 capability를 주는 것과 permission을 주는 것을 동일하게 취급해야 하는가?

초기 판단:

**분리해야 한다.**

```text
Capability
= 무엇을 할 수 있는가?

Policy / Permission
= 언제 그것을 할 수 있는가?
```

그리고 다음 계층을 검토한다.

```text
Agent
 ↓
Intent
 ↓
Policy
 ↓
Permission
 ↓
Sandbox / Tool
 ↓
Execution
```

---

# 11. Proposed Agent Model

현재까지의 Research를 종합하면 NOAH Agent는 다음 요소로 분해하는 것이 유력하다.

```text
                         NOAH AGENT
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
   Identity                 Role                Capability
       │                      │                      │
       │                      │             ┌────────┼────────┐
       │                      │             │        │        │
       │                      │           Tools    Skills  Workflows
       │                      │
       └──────────────┬───────┘
                      ▼
                    Policy
                      │
                      ▼
                   Context
                      │
                      ▼
                   Runtime
                      │
        ┌─────────────┼───────────────┐
        │             │               │
      Memory       Sandbox        Orchestration
        │             │               │
        └─────────────┼───────────────┘
                      ▼
                  Execution
                      │
                      ▼
                   Trace
                      │
                      ▼
                 Evaluation
```

중요한 점:

**이 그림은 현재 NOAH Blueprint가 아니다.**

Architecture Review에서 검증할 **candidate architecture**다.

---

# 12. Identity

Agent의 Identity는 "누구인가"를 정의한다.

예:

* Agent ID
* Name
* Origin
* Persistent identity
* Identity metadata

Identity는 Persona와 동일하지 않다.

---

# 13. Role

Role은 Agent가 **무슨 책임을 갖는가**를 정의한다.

예:

* Planner
* Researcher
* Developer
* Reviewer
* Coordinator

Role은 특정 Model에 종속되어서는 안 된다.

---

# 14. Capability

Capability는 Agent가 **무엇을 할 수 있는가**를 정의한다.

예:

```text
Capability
├── Tool
├── Skill
├── Workflow
├── Protocol
└── External Service
```

여기서 Tool / Skill / Workflow / Protocol을 같은 개념으로 합칠지는 후속 Review가 필요하다.

---

# 15. Policy / Permission

Permission은 Capability와 분리한다.

예:

```text
Agent
 ├── Capability: filesystem.write
 └── Policy: ask
```

즉 "할 수 있음"과 "지금 허용됨"은 다른 개념이다.

이 원칙은 NOAH Constitution의 Trust / Responsibility와 직접 연결된다.

---

# 16. Context

Agent에게 필요한 현재 실행 정보를 조립한다.

후보 Context Source:

```text
Instructions
User Input
Session
Working State
Memory
Retrieved Knowledge
Tool Results
Environment
Skills
Policies
```

Context는 단순 Prompt String이 아니라 **Runtime Input Assembly**로 보는 것이 유력하다.

---

# 17. Runtime

Runtime은 Agent를 실제로 실행한다.

최소한 다음을 관리할 수 있어야 한다.

```text
Turn
State
Tool Calls
Tool Results
Cancellation
Retry
Pause
Resume
Persistence
Events
```

OpenCode의 Runner와 Grok Build의 Session Actor가 이 문제를 서로 다른 방식으로 해결하고 있다.

---

# 18. Memory and Experience

Memory는 Agent 내부 필드가 아니라 독립적인 subsystem 후보로 둔다.

특히 NOAH의 장기 목표를 고려하면:

```text
Experience
 ↓
Capture
 ↓
Summarize
 ↓
Consolidate
 ↓
Knowledge / Memory
 ↓
Retrieve
 ↓
Future Action
```

이라는 feedback loop를 장기적으로 검토한다.

이는 최근 Agent Memory 연구에서 제시되는 write–manage–read 관점과도 연결된다.

---

# 19. Sandbox / Workspace

Agent는 실행 환경과 분리한다.

```text
Agent
 ↓
Execution Policy
 ↓
Sandbox
 ├── Files
 ├── Commands
 ├── Dependencies
 └── Artifacts
```

Workspace가 존재하는 경우에도 Agent가 직접 OS 권한을 가지는 구조는 피하는 방향을 우선 검토한다.

---

# 20. Orchestration

Orchestration은 Agent 자체와 별도 계층으로 보는 것을 검토한다.

책임 후보:

* Agent 선택
* Task decomposition
* Delegation
* Parallel execution
* Specialist routing
* Result aggregation
* Retry / fallback

초기에는 Single Agent를 기본값으로 하고 필요한 작업에서만 Specialist / Subagent를 호출하는 구조를 우선 검토한다.

---

# 21. Evaluation

Agent 실행 결과뿐 아니라 과정도 평가 가능해야 한다.

예:

```text
Task
 ↓
Trajectory
 ↓
Tool Calls
 ↓
State Changes
 ↓
Final Result
 ↓
Evaluation
```

평가 지표 후보:

* Task success
* Correctness
* Constraint compliance
* Safety
* Cost
* Latency
* Tool efficiency
* Recovery success
* Memory usefulness

최근 Agent research는 non-determinism, long-horizon credit assignment, tool/environment variability, retries와 context growth 등의 숨은 비용 때문에 evaluation이 어려워진다고 지적한다.

---

# 22. Experience-Driven Improvement

2026년의 중요한 연구 방향 중 하나는 **Agent가 사용하는 Harness 자체를 경험으로 개선하는 것**이다.

MemoHarness는 execution experience를 저장하고, case별 diagnosis와 global pattern을 활용해 harness configuration을 적응시키는 접근을 제안한다.

이는 NOAH 장기 비전과 매우 가까운 영역이다.

후속 질문:

> NOAH가 Agent를 학습시키는 것과 별개로, NOAH의 Harness 자체가 경험을 통해 개선될 수 있는가?

후속 Research 필요.

---

# 23. Capability Taxonomy — Initial Proposal

현재까지의 분석을 기반으로 Capability를 다음처럼 분류하는 것을 검토한다.

```text
Capability
├── Tool
│   └── 즉각적인 기능 실행
│
├── Skill
│   └── 재사용 가능한 전문 행동
│
├── Workflow
│   └── 여러 단계의 정형화된 절차
│
├── Protocol
│   └── 외부 시스템과의 상호작용 규약
│
└── Agent
    └── 독립된 판단/실행 주체
```

이 구조는 아직 가설이며 별도 Review가 필요하다.

---

# 24. Agent vs Agent Harness

현재 Review에서 중요한 구분:

```text
Agent
= 목표를 이해하고 판단하는 실행 주체

Harness
= Agent가 안정적으로 행동하도록 실행 환경과 정책을 제공하는 계층
```

Harness 후보 책임:

* Context
* Tools
* Policies
* Memory Interface
* Orchestration
* Evaluation
* Execution coordination
* Recovery

2026년 연구와 Agent SDK의 방향에서 Harness를 별도의 설계 계층으로 취급하는 사례가 증가하고 있다.

---

# 25. Candidate Architecture Decisions

현재 Review 단계의 잠정 판단:

| 주제                        | 초기 판단             | 근거                                |
| ------------------------- | ----------------- | --------------------------------- |
| Agent ≠ Model             | Adopt             | 전체 Reference 공통 방향                |
| Agent Harness 분리          | Adapt             | 최신 Agent 시스템 방향                   |
| Agent Identity 분리         | Adopt             | 장기 Personal AI에 필요                |
| Role 분리                   | Adopt             | OpenCode / Connect AI             |
| Capability 추상화            | Adapt             | Tool / Skill / Workflow 확장성       |
| Permission 분리             | Adopt             | OpenCode + Trust 요구               |
| Context 독립 계층             | Adapt             | OpenCode + 최신 Context Engineering |
| Memory 독립 subsystem       | Research Further  | 최신 Memory 연구                      |
| Sandbox 분리                | Research Further  | OpenAI 최신 SDK 방향                  |
| Single Agent 기본           | Adopt             | 복잡도 최소화                           |
| Specialist / Subagent     | Adopt             | 필요 시 확장                           |
| Multi-Agent 기본            | Reject as default | 복잡성 증가                            |
| Event/Trace               | Adapt             | Runtime + Evaluation              |
| Experience-driven Harness | Research Further  | 최신 Harness 연구                     |
| Self-modifying Agent      | Defer             | 안전성 / 검증 문제                       |

---

# 26. What NOAH Should Not Do

이번 Review에서는 다음 방향을 기본값으로 두지 않는다.

### 26.1 Agent = LLM

Reject.

### 26.2 Everything is a Multi-Agent

Reject.

### 26.3 Memory inside Agent

Reject as default.

### 26.4 Agent directly controls OS

Reject as default.

### 26.5 Every capability is a tool

Reject.

Skill / Workflow / Protocol / Agent 간 구분이 필요하다.

### 26.6 Static Harness forever

Research Further.

경험을 통해 Harness가 개선되는 가능성을 연구한다.

---

# 27. Architecture Risks

## Complexity Risk

Agent를 Identity, Role, Capability, Policy, Context, Runtime, Memory, Sandbox, Evaluation 등으로 과도하게 쪼개면 오히려 관리 비용이 증가할 수 있다.

## Coordination Risk

Subagent / Multi-Agent가 늘어나면 Context와 상태 동기화가 어려워진다.

## Permission Risk

Capability가 늘어날수록 권한 정책이 복잡해진다.

## Memory Risk

잘못된 Memory가 장기간 유지되면 이후 판단을 지속적으로 오염시킬 수 있다.

## Harness Drift

Harness가 경험을 통해 자동 개선되기 시작하면 변경된 행동을 설명하고 검증하기 어려워질 수 있다.

## Evaluation Risk

Agent의 성공을 단순 final answer로 평가하면 Tool misuse, side effect, cost, latency 등을 놓칠 수 있다.

---

# 28. NOAH-Specific Direction

현재까지의 Review를 기반으로 한 NOAH의 방향은 다음과 같다.

NOAH는:

> **단일 모델을 중심으로 한 Chat Agent가 아니라, 모델을 교체할 수 있고, 기억과 실행 환경을 분리하며, 능력과 정책을 독립적으로 관리하고, 경험을 통해 Harness를 개선할 수 있는 장기 실행형 Agent System**

을 목표로 하는 것이 유력하다.

단, 이 문장은 아직 최종 Blueprint가 아니다.

---

# 29. Adopt / Adapt / Reject / Defer / Research Further

Architecture Review의 최종 판단 체계:

## Adopt

NOAH에 큰 수정 없이 적용 가능한 원칙.

## Adapt

외부 구조를 NOAH 철학에 맞게 변형하여 적용.

## Reject

NOAH 원칙과 맞지 않거나 장기적으로 불리한 구조.

## Defer

아이디어는 유효하지만 현재 Sprint에서 결정하지 않는다.

## Research Further

근거가 부족하거나 기술 발전이 빠르므로 추가 연구가 필요하다.

---

# 30. Open Questions

현재 중요한 미해결 질문:

1. Agent Identity와 Memory Identity는 어떻게 연결되는가?
2. Agent Role과 Capability를 어디까지 독립시킬 것인가?
3. Agent Harness의 책임 범위를 어디까지 둘 것인가?
4. Context Manager와 Memory Manager는 어떻게 협력하는가?
5. Sandbox가 없는 Agent도 동일한 Runtime Interface를 사용할 것인가?
6. Subagent는 별도 Session을 갖는가?
7. Agent 간 공유 Memory는 허용하는가?
8. Experience가 Harness를 자동으로 수정할 수 있는가?
9. 어떤 결정부터 사용자의 승인을 요구하는가?
10. Agent의 행동을 어디까지 Trace해야 하는가?
11. Agent의 "성격"과 "역할"은 architecture 상 분리해야 하는가?
12. Multiple Model routing은 Agent의 책임인가 Harness의 책임인가?

---

# 31. Current Recommendation

현재까지의 근거만으로는 NOAH Agent를 다음 방향으로 설계하는 것이 가장 합리적이라고 판단한다.

```text
                     NOAH Agent
                         │
                 ┌───────┴───────┐
                 │               │
              Identity          Role
                 │               │
                 └───────┬───────┘
                         ▼
                    Capability
                         │
                     Policy
                         │
                     Context
                         │
                     Harness
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       Runtime         Memory         Sandbox
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                     Execution
                         │
                       Trace
                         │
                    Evaluation
                         │
                   Experience
                         │
                         └────────→ Harness Improvement
```

이 구조는 현재 **Candidate Architecture**이며 아직 최종 Blueprint로 확정하지 않는다.

---

# 32. Final Review Judgment

### Strong candidates

* Agent와 Model의 분리
* Identity / Role의 분리
* Capability 추상화
* Permission / Policy 독립화
* Context 관리의 독립성
* Session / Runtime 분리
* Tool 실행과 Agent 판단의 분리
* Evaluation / Trace 연결
* 필요할 때만 Subagent 사용
* Sandbox / Workspace 분리 검토

### Strong rejection candidates

* Agent = LLM
* 항상 Multi-Agent
* Agent가 직접 OS 권한을 소유
* Memory를 Agent 내부 state로만 관리
* 모든 Capability를 단일 Tool abstraction으로 통합

### Further Research

* Adaptive Harness
* Experience-driven optimization
* Learned Memory policies
* Sandbox checkpoint / restore
* Multi-agent context isolation
* Agent identity persistence
* Long-horizon evaluation

---

# 33. Review Outcome

이번 Architecture Review는 다음을 확인했다.

OpenCode는 Runtime / Session / Tool / Permission 측면에서 강한 Reference다.

Grok Build는 Session Actor, Lifecycle, Event-driven execution 및 long-running Runtime 측면에서 강한 Reference다.

Connect AI는 Role, Specialist, Persona, Local LLM, Knowledge 중심의 Agent 모델을 보여준다.

최신 2026 Agent 연구 및 제품 방향은 이들 Reference를 넘어:

* Agent Harness
* Sandbox / Compute Separation
* Context Engineering
* Durable Execution
* Experience-driven Harness Improvement
* Memory Lifecycle
* Evaluation
* Trust / Security

를 중요한 Architecture 영역으로 확장하고 있다.

따라서 NOAH의 Agent Architecture는 특정 Reference의 복제가 아니라 이 요소들을 **단순성, 교체 가능성, 신뢰성, 설명 가능성, 장기 유지보수성이라는 NOAH Constitution의 기준으로 재구성하는 방향**이 적절하다.

---

# 34. Next Step

현재 단계에서는 아직 `02-Architecture`를 수정하지 않는다.

다음 단계:

```text
Architecture Review — Agent
          ↓
Open Questions 정리
          ↓
필요한 추가 Research
          ↓
Candidate Architecture 확정
          ↓
Decision / DDR
          ↓
02-Architecture 반영
          ↓
Agent PoC
```

Agent Review 이후에는 Session / Runtime / Context / Tool / Memory를 별도의 Architecture Review 대상으로 분리하여 순차적으로 검토한다.
