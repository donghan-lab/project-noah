Research Date: 2026-08-14
OpenCode Branch: dev

# OpenCode Research

> Project NOAH Reference Research
> Research 대상: OpenCode
> Repository: https://github.com/anomalyco/opencode
> Branch: `dev`
> Research Status: Active / Initial Research

---

# 1. Research Purpose

OpenCode를 Project NOAH의 Reference로 분석한다.

본 연구의 목적은 OpenCode의 전체 구현을 복제하는 것이 아니라, AI Agent Runtime을 구성하는 핵심 Architecture와 설계 원칙을 이해하고 Project NOAH의 향후 Architecture Review에 활용할 수 있는 정보를 수집하는 것이다.

본 문서에서는 OpenCode의 구조와 구현에서 관찰되는 사실을 기록한다.

OpenCode의 구조를 그대로 채택할지 여부는 본 문서에서 결정하지 않는다.

---

# 2. Research Scope

이번 1차 연구에서는 다음 영역을 중심으로 OpenCode를 조사했다.

* Agent Architecture
* Primary Agent / Subagent
* Agent Configuration
* Session Architecture
* Session Execution
* Context Management
* Context Epoch
* Model / Provider Resolution
* Tool Architecture
* Tool Registry
* Tool Permission
* Tool Execution
* Tool Result / Settlement
* Runtime Execution Loop
* Compaction
* Event / Persistence
* V2 Session Architecture

이번 연구에서는 UI, Frontend, 설치 시스템, 모든 Plugin 구현 등 Runtime과 직접 관련되지 않은 영역은 우선 범위에서 제외한다.

---

# 3. Research Sources

주요 조사 자료:

## Repository

https://github.com/anomalyco/opencode

## Documentation

https://github.com/anomalyco/opencode/blob/dev/README.ko.md

https://github.com/anomalyco/opencode/blob/dev/packages/web/src/content/docs/agents.mdx

https://github.com/anomalyco/opencode/blob/dev/packages/web/src/content/docs/ko/agents.mdx

## Agent Example

https://github.com/anomalyco/opencode/blob/dev/.opencode/agent/triage.md

https://github.com/anomalyco/opencode/blob/dev/.opencode/agent/duplicate-pr.md

## Tool Example

https://github.com/anomalyco/opencode/blob/dev/.opencode/tool/github-triage.ts

## V2 Specifications

https://github.com/anomalyco/opencode/blob/dev/specs/v2/session.md

https://github.com/anomalyco/opencode/blob/dev/specs/v2/tools.md

## Runtime Implementation

https://github.com/anomalyco/opencode/blob/dev/packages/core/src/session/runner/index.ts

https://github.com/anomalyco/opencode/blob/dev/packages/core/src/session/runner/model.ts

https://github.com/anomalyco/opencode/blob/dev/packages/core/src/session/runner/llm.ts

---

# 4. OpenCode Overview

OpenCode는 오픈소스 AI Coding Agent다.

단순한 대화형 LLM 인터페이스가 아니라 Agent, Session, Model, Tool, Permission, Runtime 등의 구성 요소를 사용하여 실제 작업을 수행하는 Agent 시스템으로 구성되어 있다.

OpenCode의 Architecture를 연구하는 핵심 이유는 모델 자체보다 Agent가 실제 작업을 수행하기 위해 필요한 Runtime 구조를 확인할 수 있기 때문이다.

---

# 5. Agent Architecture

OpenCode는 Agent를 하나의 단일 개념으로 사용하지 않고 역할과 실행 방식에 따라 구분한다.

주요 Agent 유형:

```text
Primary Agent
├── Build
└── Plan

Subagent
├── General
├── Explore
└── Scout

Internal / Hidden Agent
├── Compaction
├── Title
└── Summary
```

Primary Agent는 사용자와 직접 상호작용하며 주요 작업을 수행한다.

Subagent는 특정 작업을 위임받아 수행한다.

Internal Agent는 일반적인 사용자 작업이 아니라 Runtime 내부의 특정 기능을 수행하기 위해 사용된다.

---

# 6. Agent Configuration

OpenCode의 Agent는 단순 Prompt만으로 정의되지 않는다.

Agent 구성에는 다음과 같은 요소들이 포함될 수 있다.

* mode
* model
* prompt
* permission
* steps
* visibility
* execution constraints

Agent 정의는 Markdown 및 설정 구조를 통해 구성할 수 있다.

즉 Agent는 다음과 같은 실행 단위로 볼 수 있다.

```text
Agent
├── Role / Instructions
├── Model
├── Permissions
├── Tool Access
└── Execution Constraints
```

---

# 7. Primary Agent and Subagent

OpenCode는 Primary Agent와 Subagent를 분리한다.

Primary Agent는 사용자의 주요 작업을 처리한다.

Subagent는 특정 문제를 독립적으로 처리하거나 Primary Agent의 작업을 보조한다.

Primary Agent는 Task mechanism을 통해 Subagent에 작업을 위임할 수 있다.

Subagent는 Child Session과 연결된 실행 흐름을 가질 수 있다.

개념적으로:

```text
Primary Agent
      │
      ├── Tool
      │
      └── Task
           │
           ▼
        Subagent
           │
           ▼
       Child Session
```

이 구조는 Agent 간 책임과 실행 컨텍스트를 분리하는 역할을 한다.

---

# 8. Agent Permission

OpenCode는 Agent의 작업 권한을 세밀하게 제어한다.

권한의 기본적인 형태는 다음과 같다.

* allow
* ask
* deny

권한의 대상에는 다음과 같은 작업이 포함될 수 있다.

* read
* edit
* bash
* task
* webfetch
* websearch
* lsp
* skill

또한 특정 Tool이나 Bash 명령에 대해 보다 세밀한 정책을 적용할 수 있다.

따라서 Agent가 어떤 작업을 할 수 있는지는 Agent의 역할뿐 아니라 Permission 정책에 의해 결정된다.

---

# 9. Agent Example — Triage

`triage.md`는 OpenCode 프로젝트 내부에서 특정 목적을 수행하도록 정의된 Agent의 실제 사례다.

주요 특징:

```text
mode
primary

hidden
true

model
opencode/gpt-5.4-mini

tool
github-triage
```

Agent의 역할과 판단 규칙은 Instructions에 정의되어 있으며, 실제 GitHub Issue를 특정 팀으로 분류하는 작업을 수행한다.

이를 통해 OpenCode에서는 특정 작업을 전담하는 Agent를 별도로 구성할 수 있음을 확인할 수 있다.

---

# 10. Tool Architecture

OpenCode V2의 Tool은 공통적인 Tool Definition 구조를 가진다.

주요 구성:

```text
Tool
├── Description
├── Input Schema
├── Output Schema
├── Execute
└── Model Output Projection
```

Tool은 단순 함수가 아니라 입력과 출력이 정의된 실행 가능한 시스템 구성 요소로 다뤄진다.

Built-in Tool, Application Tool, Plugin Tool 역시 동일한 Tool 계약을 사용할 수 있도록 설계되어 있다.

---

# 11. Tool Registry

Tool과 Tool Registry는 분리되어 있다.

Registry는 현재 사용할 수 있는 Tool을 관리하고 Tool의 이름과 실제 Definition을 연결한다.

Tool이 어느 Registry Layer에 등록되었는지에 따라 동일한 이름의 Tool이 overlay 방식으로 재정의될 수 있다.

이를 통해 Runtime에서 Tool을 조합하고 확장할 수 있다.

---

# 12. Tool Context

Tool 실행 시 Session Runtime에서 다음과 같은 실행 컨텍스트가 전달된다.

```text
sessionID
agent
assistantMessageID
toolCallID
```

Tool이 필요한 실행 컨텍스트를 직접 추론하는 것이 아니라 Session Runner가 이를 제공한다.

이를 통해 Tool 실행을 특정 Session 및 Agent 실행과 연결할 수 있다.

---

# 13. Tool Permission

Tool의 실행 권한은 Tool 자체와 분리된 Permission 계층을 통해 관리된다.

개념적으로:

```text
Agent
  ↓
Tool
  ↓
Permission Service
  ↓
Policy / Approval
  ↓
Execution
```

Tool Registry 자체가 권한 판정을 담당하는 것이 아니라 Permission 계층이 별도의 책임을 갖는다.

---

# 14. Tool Execution

실제 Tool 실행은 Agent가 직접 외부 시스템을 호출하는 방식이 아니라 Tool 계층을 통해 수행된다.

예:

```text
Triage Agent
    ↓
github-triage
    ↓
GitHub API
    ↓
Issue Assignee Update
```

Agent는 판단과 Tool 호출을 담당하고, 외부 시스템과의 실제 통신은 Tool이 담당한다.

---

# 15. Tool Result and Model Output

Tool 실행 결과와 모델에 전달되는 결과는 동일할 필요가 없다.

OpenCode는 실행 결과 자체와 모델에게 보여주는 결과를 분리할 수 있는 구조를 사용한다.

개념적으로:

```text
Tool Execution
      │
      ├── Full / Durable Result
      │
      └── Model-facing Output
```

이를 통해 Runtime은 필요한 전체 결과를 보존하면서도 모델 Context에는 필요한 정보만 전달할 수 있다.

---

# 16. Session Architecture

OpenCode V2에서는 Session과 실제 실행을 분리한다.

개념적으로:

```text
Session
   ↓
SessionExecution
   ↓
SessionRunner
```

Session은 지속적인 대화와 실행 상태를 관리하는 단위이고, SessionExecution / SessionRunner는 실제 실행을 담당한다.

이러한 분리는 지속적인 상태와 일시적인 실행을 분리하기 위한 것으로 보인다.

---

# 17. Durable Inbox

V2 Session Architecture에서는 사용자 입력을 즉시 대화 기록에 반영하는 대신 `session_input`과 같은 영속적인 입력 구조를 사용한다.

개념적으로:

```text
User Input
    ↓
Admission
    ↓
PromptAdmitted
    ↓
Execution
    ↓
Prompted
    ↓
Session History
```

입력의 수용과 실제 실행/기록 반영이 분리된다.

---

# 18. Context Epoch

OpenCode는 현재 모델에 제공되는 System Context의 상태를 Context Epoch라는 개념으로 관리한다.

환경 정보, instructions, skills 등의 Context Source가 변화하면 이를 다음 안전한 Provider Turn에 반영하는 구조를 사용한다.

개념적으로:

```text
Context Source
     ↓
Context State
     ↓
Context Epoch
     ↓
Provider Turn
```

이를 통해 Context 변화가 실행 중간에 임의로 발생하는 것을 방지하고 특정 실행 시점의 Context 상태를 관리할 수 있다.

---

# 19. Session Runner

실제 Runtime 실행은 Session Runner가 담당한다.

현재 구조에는 다음 구성 요소가 분리되어 있다.

```text
session/runner/
├── index.ts
├── model.ts
├── llm.ts
├── max-steps.ts
├── publish-llm-event.ts
└── to-llm-message.ts
```

각 파일은 Runner의 인터페이스, Model Resolution, LLM 실행, Step 제한, Event 발행, Message 변환 등의 책임을 나누어 가진다.

---

# 20. Model Resolution

`runner/model.ts`에서는 Session이 사용할 Model을 resolve한다.

Model Resolution 과정에서 다음 요소들이 고려된다.

* Provider
* Model
* Credential
* Endpoint
* Headers
* Request Configuration
* Context / Output Limits
* Variant

따라서 Runner 자체와 Model / Provider 계층이 분리되어 있다.

개념적으로:

```text
SessionRunner
      ↓
Model Resolver
      ↓
Provider / Credential / Model
      ↓
LLM
```

---

# 21. LLM Execution Loop

`runner/llm.ts`에서는 실제 Provider Turn과 Tool Continuation을 오케스트레이션한다.

전체적인 흐름은 다음과 같이 정리할 수 있다.

```text
Session
   ↓
Agent
   ↓
Context Epoch
   ↓
Model Resolution
   ↓
Session History
   ↓
Tool Materialization
   ↓
LLM Request
   ↓
Provider Stream
   ↓
Tool Call?
   ├── No → Response Completion
   │
   └── Yes
        ↓
     Tool Execution
        ↓
     Tool Settlement
        ↓
     Next Turn
```

즉 OpenCode의 Agent Runtime은 단일 LLM 호출로 끝나는 구조가 아니라 LLM Turn과 Tool Continuation을 반복하는 실행 루프를 가진다.

---

# 22. Tool Settlement

Tool 실행 이후 결과를 Session Runtime에 반영하는 별도의 Settlement 단계가 존재한다.

이 구조는 Tool 실행 중 발생한 상태와 결과를 Session 및 Event 흐름과 연결하는 역할을 한다.

중단된 실행을 무조건 다시 실행하지 않고 실행 상태를 처리하는 정책도 Session Runtime에 포함되어 있다.

---

# 23. Compaction

Context Window가 부족해질 경우 OpenCode는 전체 Transcript를 삭제하는 방식으로 처리하지 않는다.

전체 Transcript는 지속적으로 보존하면서 모델에 제공되는 활성 Context를 축약한다.

개념적으로:

```text
Full Transcript
      │
      ├── Durable History
      │
      └── Active Context
             ├── Rolling Summary
             └── Recent Messages
```

따라서 저장되는 전체 대화와 모델에게 현재 제공되는 Context는 서로 다른 개념이다.

---

# 24. Event and Persistence

Session Runtime에서는 실행 상태와 Tool 상태를 Event 및 Session History와 연결한다.

이를 통해 실행 과정에서 발생한 중요한 상태 변화를 지속적으로 기록할 수 있다.

또한 실행 재개, Tool Settlement, Prompt 상태 등의 처리도 Session 상태와 연결된다.

---

# 25. Observed Runtime Architecture

현재까지 조사한 내용을 하나의 흐름으로 정리하면 다음과 같다.

```text
                         OpenCode Runtime

                              User
                               │
                               ▼
                           Session
                               │
                               ▼
                         SessionExecution
                               │
                               ▼
                         SessionRunner
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
          Agent            Context Epoch     Model Resolver
             │                 │                 │
             │                 │                 ▼
             │                 │              Provider
             │                 │                 │
             └─────────────────┴─────────────────┘
                               │
                               ▼
                          LLM Request
                               │
                               ▼
                         Provider Stream
                               │
                         ┌─────┴─────┐
                         │           │
                       Text       Tool Call
                                     │
                                     ▼
                              Permission
                                     │
                                     ▼
                                Tool Execute
                                     │
                                     ▼
                               Tool Result
                                     │
                                     ▼
                             Tool Settlement
                                     │
                                     ▼
                              Next LLM Turn
                                     │
                                     └───────────────┐
                                                     ▼
                                                  Session
```

---

# 26. Strengths Observed

## 26.1 Separation of Concerns

Agent, Session, Model, Tool, Permission, Context, Runtime의 책임이 비교적 명확하게 분리되어 있다.

## 26.2 Agent Specialization

Primary Agent와 Subagent를 분리하여 작업을 전문화할 수 있다.

## 26.3 Permission-aware Execution

Agent와 Tool의 권한을 세밀하게 제어할 수 있다.

## 26.4 Durable Session

대화와 실행 상태를 장기적으로 보존할 수 있는 구조를 지향한다.

## 26.5 Context Management

Context Epoch와 Compaction을 통해 모델의 Context와 실제 전체 History를 분리한다.

## 26.6 Model / Provider Independence

Runtime과 실제 Provider / Model Resolution을 분리한다.

## 26.7 Tool Abstraction

Tool을 Schema + Execute + Output Projection을 가진 독립적인 실행 단위로 추상화한다.

---

# 27. Observed Limitations / Trade-offs

현재 Research 단계에서 확인되는 구조적 비용과 주의점:

## 27.1 Complexity

Session, Execution, Runner, Context, Tool, Permission, Event 등 여러 계층으로 분리되어 있어 전체 Runtime을 이해하기 위한 진입 장벽이 높다.

## 27.2 State Coordination

Durable Session과 Runtime Execution을 함께 관리하기 때문에 상태 동기화와 복구에 대한 복잡성이 증가한다.

## 27.3 Context Management Complexity

Context Epoch와 Compaction을 도입하면 단순한 Conversation History보다 훨씬 강력한 Context 관리가 가능하지만 Runtime의 복잡성도 함께 증가한다.

## 27.4 V2 Incompleteness

V2 Specification과 구현에는 완료된 부분과 미완성 또는 후속 작업으로 남아있는 부분이 함께 존재한다.

따라서 V2 문서의 내용 전체를 현재의 완성된 OpenCode 구현이라고 해석해서는 안 된다.

---

# 28. Implementation Status

현재 연구에서 다음을 구분해야 한다.

### Observed / Implemented

실제 코드에서 확인된 구조.

### Designed

V2 Specification에 정의되어 있지만 현재 구현 상태와 별도로 설계된 구조.

### Partial

일부 구현된 기능.

### Missing / Follow-up

명세상 존재하지만 후속 작업 또는 미완성으로 표시된 기능.

OpenCode V2를 분석할 때 이 네 가지를 구분하여 기록해야 한다.

---

# 29. NOAH-Relevant Observations

다음 내용은 아직 NOAH의 채택 결정이 아니다.

현재 OpenCode 연구를 통해 다음과 같은 Architecture Questions가 도출되었다.

### Agent

* NOAH도 Primary Agent와 Specialist Agent를 분리해야 하는가?
* Agent의 역할과 Permission을 분리해야 하는가?
* Agent가 다른 Agent를 호출할 수 있어야 하는가?

### Session

* Conversation과 Execution State를 분리해야 하는가?
* Durable Session이 필요한가?
* Child Session 구조가 필요한가?

### Context

* Context를 별도 Runtime Layer로 관리해야 하는가?
* Context와 Memory를 분리해야 하는가?
* Context Epoch와 유사한 Context Versioning이 필요한가?

### Tool

* Tool을 독립적인 실행 단위로 만들어야 하는가?
* Tool Result와 Model-facing Output을 분리해야 하는가?
* Permission을 Tool과 독립된 Service로 두어야 하는가?

### Runtime

* LLM Turn과 Tool Continuation을 하나의 Runtime Loop로 관리해야 하는가?
* 실행 상태를 Event 기반으로 기록해야 하는가?
* 중단된 Tool Execution을 어떻게 처리해야 하는가?

---

# 30. Research Boundary

이번 OpenCode 연구에서는 다음을 아직 결정하지 않았다.

* NOAH가 OpenCode의 구조를 그대로 사용할지 여부
* NOAH Runtime Architecture
* NOAH Memory Architecture
* NOAH Agent Hierarchy
* NOAH Permission Model
* NOAH Context Architecture
* NOAH Tool Architecture

위 항목들은 이후 Architecture Review와 다른 Reference 비교를 통해 결정한다.

---

# 31. Next Research Targets

OpenCode 단독 분석을 무한히 확장하지 않는다.

현재 확보한 Runtime 흐름을 기반으로 다음 Reference와 비교한다.

### Primary References

1. OpenCode
2. Grok Build
3. Connect AI

비교 대상은 Runtime Architecture에 필요한 범위로 제한한다.

---

# 32. Research Conclusion

OpenCode는 단순한 Coding Agent가 아니라 Session, Agent, Model, Context, Tool, Permission, Event, Runtime을 결합한 복합적인 Agent Runtime Architecture를 보여준다.

특히 다음 구조가 본 연구에서 가장 중요한 관찰 대상이다.

```text
Agent
+
Session
+
Context
+
Model / Provider
+
Tool
+
Permission
+
Runtime Loop
+
Persistence
```

OpenCode의 구조는 Project NOAH의 최종 Architecture를 결정하기 위한 하나의 중요한 Reference가 될 수 있다.

그러나 OpenCode의 구조를 그대로 채택하는 결정은 아직 이루어지지 않았다.

본 문서는 Research 결과를 기록하는 문서이며, 최종 Architecture 결정은 별도의 Architecture Review 및 Decision 과정을 통해 수행한다.
