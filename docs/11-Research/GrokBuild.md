# Grok Build Research

> Project NOAH Reference Research
> Research 대상: Grok Build
> Repository: https://github.com/xai-org/grok-build
> Branch: `main`
> Research Status: Initial Research

---

# 1. Research Purpose

Grok Build를 Project NOAH의 Reference로 분석한다.

본 연구의 목적은 Grok Build의 전체 구현을 복제하는 것이 아니라, AI Agent Runtime을 구성하는 핵심 Architecture와 실제 실행 흐름을 이해하고 Project NOAH의 향후 Architecture Review에 활용할 수 있는 정보를 수집하는 것이다.

본 문서는 Grok Build에서 관찰되는 구조와 구현을 기록한다.

Grok Build의 구조를 그대로 채택할지 여부는 본 문서에서 결정하지 않는다.

---

# 2. Research Scope

이번 1차 연구에서는 다음 영역을 중심으로 Grok Build를 조사했다.

* Agent Runtime
* Agent Model
* MvpAgent
* Session Registry
* Session Actor
* Session Lifecycle
* Run Loop
* Turn Execution
* Prompt / Context Assembly
* Model / Sampling
* Tool / Skill / Workflow
* Subagent
* ACP
* Persistence
* Approval / Resume
* Memory 관련 Runtime 연결

UI와 전체 Tool 구현 등 Runtime과 직접적인 관계가 없는 영역은 이번 1차 연구 범위에서 제외한다.

---

# 3. Research Sources

## Repository

https://github.com/xai-org/grok-build

## Main Runtime

https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-shell/README.md

https://github.com/xai-org/grok-build/tree/main/crates/codegen/xai-grok-shell/src

## Agent

https://github.com/xai-org/grok-build/tree/main/crates/codegen/xai-grok-shell/src/agent

https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-shell/src/agent/mod.rs

https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-shell/src/agent/mvp_agent/mod.rs

## Session Runtime

https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-shell/src/session/acp_session_impl/run_loop.rs

https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-shell/src/session/acp_session_impl/turn.rs

## Related Test

https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager-pty-harness/tests/plan_approval_resume.rs

---

# 4. Grok Build Overview

Grok Build는 터미널 중심의 AI coding agent 및 agentic harness를 제공한다.

`xai-grok-shell`은 Grok Agent Runtime의 핵심 영역이며 interactive TUI, headless 실행, ACP 기반 Agent Mode 등의 실행 방식을 지원한다.

Repository 구조는 Agent Runtime, Tool, Workspace, UI 및 외부 연결 계층을 서로 다른 crate와 module로 나누는 방향을 보여준다.

---

# 5. Agent Runtime Architecture

Grok Build에서 Agent Runtime의 상위 객체로 `MvpAgent`가 존재한다.

`MvpAgent`는 단순히 하나의 LLM 호출을 수행하는 객체가 아니라 다음과 같은 여러 Runtime 요소와 연결된다.

```text
MvpAgent
├── Activity
├── Session Registry
├── Gateway
├── Agent Configuration
├── Authentication
├── Model Management
├── Chat Modes
├── Session State
├── Memory-related State
├── MCP-related State
├── Plugin-related State
├── Workspace-related State
└── Subagent-related State
```

실제 `MvpAgent` 구조체에는 `activity`, `session_registry`, `gateway`, `cfg`, authentication 및 model 관련 상태 등이 포함되어 있으며, Agent가 Session과 다른 Runtime 구성 요소를 조정하는 상위 계층으로 기능한다.

---

# 6. Session Registry

`MvpAgent`는 `SessionRegistry`를 소유한다.

이를 통해 Agent Runtime은 여러 Session을 관리할 수 있으며 Session의 생성, 등록, 조회 및 종료와 같은 Lifecycle을 상위 Agent Runtime과 연결할 수 있다.

개념적으로:

```text
MvpAgent
    ↓
SessionRegistry
    ↓
Session
```

Session은 단순한 일회성 LLM 호출보다 지속적인 Runtime 단위로 취급된다.

---

# 7. Session Actor Architecture

Grok Build의 Session Runtime에서는 `SessionActor`가 중심적인 실행 단위로 사용된다.

Session Actor는 다양한 명령과 이벤트를 비동기적으로 수신하고 처리하는 형태로 구성되어 있다.

개념적으로:

```text
                 SessionActor
                      │
        ┌─────────────┼─────────────┐
        │             │             │
      Commands      Events       Chat State
        │             │             │
        └─────────────┼─────────────┘
                      │
                 Session Runtime
```

`run_loop.rs`에서는 이러한 입력들을 하나의 Session Runtime 안에서 조정한다.

---

# 8. Session Run Loop

`run_loop.rs`는 Session Actor의 중심 실행 루프를 담당한다.

여기에서는 Session Command, 이벤트, Chat State 관련 신호 등을 비동기적으로 처리한다.

따라서 Session은 단순한 순차 함수 호출보다 **이벤트와 명령을 지속적으로 처리하는 Actor-like Runtime**에 가까운 구조를 가진다.

개념적으로:

```text
SessionActor
    ↓
Run Loop
    ├── Command
    ├── Event
    ├── Chat State
    ├── Background Task
    └── Lifecycle Event
```

---

# 9. User Prompt Admission

Session Runtime에서는 사용자 Prompt가 곧바로 실행되는 것이 아니라 Admission 과정이 존재한다.

실제 `run_loop.rs`의 Prompt 처리에서는 입력의 admission 여부를 확인하고, 승인되지 않은 Prompt를 제거하거나 실행하지 않는다.

개념적으로:

```text
User Prompt
    ↓
Admission
    ↓
Accepted?
 ┌──┴──┐
No    Yes
 │      │
Drop    ↓
      Session Runtime
```

이는 사용자 입력의 수용과 실제 실행을 구분하는 구조로 볼 수 있다.

---

# 10. Turn Execution

`turn.rs`는 하나의 Agentic Turn에서 수행되는 주요 작업을 담당한다.

Turn에서는 사용자 입력을 처리하고, 명령 및 Skill을 해석하고, 필요한 Context와 Prompt를 구성한 뒤 실제 모델 실행으로 연결되는 과정을 관리한다.

개념적으로:

```text
Prompt
  ↓
Command / Skill Resolution
  ↓
Prompt Construction
  ↓
Context Preparation
  ↓
Model / Sampling
  ↓
Agentic Execution
```

---

# 11. Prompt Processing

Turn 처리 과정에서는 단순 문자열 전달보다 여러 단계의 Prompt preprocessing이 이루어진다.

예를 들어:

* Slash command 처리
* Skill resolution
* Workflow resolution
* Prompt origin 확인
* 이미지 처리
* 특수 Prompt framing
* 사용자 메시지 persistence
* Hook dispatch

등이 실행된다.

특히 `turn.rs`에서는 Prompt를 해석하는 과정에서 Skill과 named workflow를 조회하고, Slash Command를 실제 실행 구조로 변환하는 흐름이 존재한다.

---

# 12. Skills and Workflows

Grok Build는 Agent 실행에 Skill과 Workflow를 결합한다.

Turn 처리 과정에서 Slash Command가 Skill 또는 Plugin에서 제공되는 기능으로 해석될 수 있으며, 활성화된 Skill에 대한 telemetry와 Hook 이벤트가 기록된다.

개념적으로:

```text
User Prompt
    ↓
Command Parser
    ↓
Skill / Workflow Resolution
    ↓
Prompt / Execution Context
    ↓
Agent Turn
```

이는 Prompt를 단순 텍스트로 처리하는 것보다 **실행 가능한 Capability를 Context와 결합하는 구조**로 볼 수 있다.

---

# 13. Model and Sampling

Grok Build의 Agent Runtime은 Session 및 Agent 상태와 Model 관련 설정을 연결한다.

`MvpAgent`에는 Model Manager와 Sampling Configuration 등이 존재하며, 실제 Turn 실행은 이러한 구성과 연결된다.

개념적으로:

```text
Session
   ↓
Agent Configuration
   ↓
Model Configuration
   ↓
Sampling
   ↓
Model Execution
```

Model 자체와 Agent Runtime의 책임을 분리하는 구조가 관찰된다.

---

# 14. Session Lifecycle

Grok Build는 Session 생성뿐만 아니라 Session의 Lifecycle을 별도의 구조로 관리한다.

Session Runtime에서는:

* Session 시작
* Prompt 처리
* Turn 실행
* 대기 상태
* Resume
* 종료
* Cleanup

과 같은 상태 변화를 처리한다.

특히 Plan Approval과 Resume 관련 테스트가 별도로 존재하며, 승인 대기 상태가 Session Lifecycle의 일부로 취급되는 것을 확인할 수 있다.

---

# 15. Plan Approval and Resume

`plan_approval_resume.rs`는 Plan Mode의 승인 대기와 Resume을 별도의 통합 테스트로 검증한다.

개념적으로:

```text
Plan
 ↓
Approval Required
 ↓
Session Wait
 ↓
Resume
 ↓
Approval Restored
 ↓
Continue Execution
```

따라서 사용자 승인이 필요한 작업을 단순 UI 이벤트가 아니라 지속 가능한 Session 상태와 연결하는 방향을 관찰할 수 있다.

---

# 16. Persistence

Turn 처리 과정에서 사용자 메시지와 상태를 Persistence Layer에 반영하는 로직이 존재한다.

예를 들어 사용자 메시지가 Chat State에 반영된 후 persistence flush 및 acknowledgement를 기다리는 흐름이 존재한다.

개념적으로:

```text
User Input
    ↓
Chat State
    ↓
Persistence
    ↓
Flush / Ack
    ↓
Committed State
```

이는 Runtime 상태와 저장 상태를 분리하면서도 필요한 지점에서 명시적으로 동기화하는 구조로 볼 수 있다.

---

# 17. Hooks and Telemetry

Grok Build의 Turn 처리에는 Hook 및 Telemetry가 Runtime의 일부로 연결된다.

예를 들어 사용자 Prompt 제출, Skill 활성화, Plugin 사용 등의 이벤트가 기록된다.

개념적으로:

```text
Runtime Event
    ├── Hook
    ├── Telemetry
    └── Session State
```

이는 Agent 실행을 단순한 요청/응답 구조가 아니라 **관찰 가능한 Event Stream**으로 취급하는 방향을 보여준다.

---

# 18. Subagent

Agent 영역에는 `subagent` 관련 모듈이 별도로 존재한다.

또한 `MvpAgent` 및 Session Runtime은 Subagent와 관련된 상태와 이벤트를 관리한다.

현재 1차 조사에서는 Subagent의 전체 실행 흐름까지는 분석하지 않았으며, 다음 조사에서 별도의 분석 대상으로 다룬다.

---

# 19. ACP

`xai-grok-shell`은 Agent Client Protocol 기반 실행 모드를 지원한다.

이를 통해 Agent Runtime을 TUI에만 종속시키지 않고 외부 Client와 연결할 수 있는 구조를 제공한다.

개념적으로:

```text
External Client
      ↓
     ACP
      ↓
Grok Agent Runtime
      ↓
Session
      ↓
Turn
```

이 구조는 Runtime과 사용자 인터페이스 또는 외부 Client의 분리를 가능하게 한다.

---

# 20. Observed Runtime Flow

현재까지 조사한 내용을 하나의 흐름으로 정리하면 다음과 같다.

```text
                         MvpAgent
                             │
                             ▼
                      SessionRegistry
                             │
                             ▼
                       SessionActor
                             │
                       ┌─────┴─────┐
                       │           │
                  Commands      Events
                       │           │
                       └─────┬─────┘
                             ▼
                         Run Loop
                             │
                         User Prompt
                             │
                         Admission
                             │
                             ▼
                           Turn
                             │
                 ┌───────────┼───────────┐
                 │           │           │
               Skills     Workflow    Context
                 │           │           │
                 └───────────┼───────────┘
                             ▼
                     Model / Sampling
                             │
                             ▼
                       Agent Execution
                             │
                    ┌────────┴────────┐
                    │                 │
                  Tool            Further Turn
                    │                 │
                    └────────┬────────┘
                             ▼
                      Persistence
                             │
                             ▼
                      Session State
```

---

# 21. Strengths Observed

## 21.1 Session-centered Runtime

Session을 단순 대화 기록이 아니라 지속적인 Runtime 객체로 취급한다.

## 21.2 Actor-like Coordination

Session Actor가 여러 Command와 Event를 하나의 Runtime 흐름에서 조정한다.

## 21.3 Clear Runtime Boundaries

Agent, Session, Turn, Model, Tool, Skill 등의 책임이 별도 계층으로 나타난다.

## 21.4 Capability Integration

Skill, Workflow, Plugin 등이 Agent Turn에 통합된다.

## 21.5 Persistent State

Prompt와 Session 상태를 저장하고 필요한 시점에 명시적으로 flush/acknowledgement를 수행한다.

## 21.6 Interrupt / Resume

Approval이나 특정 대기 상태를 Session Lifecycle과 연결하여 재개할 수 있는 구조를 가진다.

## 21.7 Extensibility

ACP, MCP, Plugin, Skill 등을 통해 Runtime 외부와 연결할 수 있다.

## 21.8 Observability

Hook과 Telemetry를 Runtime Event에 연결한다.

---

# 22. Potential Trade-offs

이번 1차 연구에서 관찰되는 잠재적인 비용과 Trade-off는 다음과 같다.

## 22.1 Runtime Complexity

Session Actor, Command Channel, Event Channel, Background Task, Persistence, Hook, Telemetry 등을 하나의 Runtime에 결합하므로 구조를 이해하는 데 필요한 복잡도가 높아질 수 있다.

## 22.2 Centralized Session Coordination

Session Actor가 많은 책임을 조정하기 때문에 장기적으로 Session Runtime의 책임 범위를 지나치게 확장하지 않는지 검토할 필요가 있다.

## 22.3 State Management

실행 상태, Persistence 상태, Approval 상태, Background Task 상태 등을 동시에 관리해야 하므로 상태 전이와 복구 설계가 중요해진다.

## 22.4 Capability Surface

Skill, Workflow, Plugin, Tool, MCP 등이 동시에 Runtime에 연결될 경우 Capability 관리와 Permission 정책이 복잡해질 수 있다.

---

# 23. Implementation vs Design Status

Research에서는 다음을 구분한다.

### Observed / Implemented

실제 `main` branch 코드에서 확인된 구조.

### Designed

README 또는 구조적 문서에서 설계 의도로 확인되는 개념.

### Partial

일부 기능만 확인되거나 추가 구현이 필요한 영역.

### Not Yet Investigated

현재 1차 Research 범위에서 충분히 분석하지 않은 영역.

특히 Subagent, Tool Dispatch, Permission Architecture, Memory Architecture는 이번 문서에서 전체 구현을 다루지 않았다.

---

# 24. NOAH-Relevant Questions

아래 항목은 Research에서 발견한 질문이며 아직 NOAH의 최종 설계 결정이 아니다.

## Agent

* Agent Runtime의 상위 관리자와 실제 Agent 실행을 분리할 것인가?
* Agent와 Session의 책임 경계는 어디에 둘 것인가?
* Subagent는 별도의 Session을 가져야 하는가?

## Session

* Session을 Actor-like Runtime으로 구성할 필요가 있는가?
* Session과 Execution State를 분리할 것인가?
* Approval / Pause / Resume을 Session Lifecycle에 포함할 것인가?

## Context

* Prompt preprocessing과 Context Assembly를 어느 계층에 둘 것인가?
* Skill / Workflow가 Context에 직접 들어가는가?
* Context와 Memory는 어떻게 분리할 것인가?

## Capability

* Tool, Skill, Workflow, Plugin, MCP를 하나의 Capability Model로 추상화할 것인가?
* Capability와 Permission을 어떻게 연결할 것인가?

## Runtime

* Event-driven Session Runtime이 NOAH에 적합한가?
* 중앙 Session Actor 구조가 장기적으로 유리한가?
* Persistence와 Runtime State를 어느 수준까지 분리해야 하는가?

---

# 25. Research Boundary

이번 Research에서는 아직 다음을 결정하지 않았다.

* NOAH가 Grok Build 구조를 채택할지 여부
* NOAH의 Session Architecture
* NOAH의 Agent Architecture
* NOAH의 Runtime Loop
* NOAH의 Capability Architecture
* NOAH의 Permission Architecture
* NOAH의 Memory Architecture
* NOAH의 Event Architecture

외부 Reference는 NOAH 설계를 위한 증거이며, NOAH의 구조를 직접 정의하지 않는다.

---

# 26. Next Research

다음 단계에서는 Grok Build를 무한히 확장해서 분석하지 않는다.

현재 Runtime Architecture에서 아직 중요한 비교 대상은 다음과 같다.

1. OpenCode
2. Grok Build
3. Connect AI

이후 세 Reference에서 확인한 구조를 Architecture Review 단계에서 비교한다.

---

# 27. Research Conclusion

Grok Build의 Runtime은 단순한 LLM request/response 구조보다 복합적인 Session-centered Agent Runtime에 가깝다.

현재 관찰된 핵심 구조는 다음과 같다.

```text
MvpAgent
   +
Session Registry
   +
Session Actor
   +
Run Loop
   +
Turn Execution
   +
Model / Sampling
   +
Tool / Skill / Workflow
   +
Persistence
   +
Lifecycle
```

특히 Session Actor 중심의 Event / Command 조정, Turn 단계의 Prompt 및 Capability 처리, Persistence와 Resume을 Runtime Lifecycle에 포함하는 구조가 본 연구에서 중요한 관찰 대상이다.

그러나 이러한 구조가 NOAH에 적합하다는 결정은 아직 이루어지지 않았다.

이 문서는 Research 결과를 보존하는 문서이며, 최종 Architecture 결정은 이후 Architecture Review와 Decision 과정을 통해 수행한다.
