# Architecture Review — Capability & Tools

> Project NOAH Architecture Review
> Review 대상: Capability / Tools / Skills / Workflow / Protocol Architecture
> Review Version: 0.1
> Status: Review

---

# 1. Review Purpose

Project NOAH에서 Agent가 실제로 행동할 수 있도록 만드는 Capability 계층의 책임과 경계를 정의한다.

본 Review의 핵심 질문은 다음과 같다.

> **"NOAH의 Agent는 무엇을 할 수 있으며, 각각의 능력을 어떤 추상화로 표현하고 어떻게 안전하게 실행할 것인가?"**

특히 다음 개념의 경계를 검토한다.

* Tool
* Skill
* Workflow
* Protocol
* Agent Delegation
* External Service
* Capability
* Permission
* Policy
* Execution

본 Review에서는 특정 Framework나 Tool 시스템을 최종 채택하지 않는다.

---

# 2. Core Architecture Question

## Capability란 무엇인가?

초기 정의:

> Capability는 Agent가 목표를 달성하기 위해 사용할 수 있는 외부 또는 내부의 행동 능력이다.

Capability는 Agent 자신과 분리된다.

```text
Agent
  ↓
Capability
  ↓
Policy
  ↓
Execution
```

즉:

> Agent가 "무엇을 할 수 있는가"와
> Agent가 "지금 그것을 실행할 수 있는가"는 별개의 문제다.

---

# 3. Capability Taxonomy

현재까지의 Research를 기반으로 다음 다섯 가지 주요 형태를 검토한다.

```text
Capability
├── Tool
├── Skill
├── Workflow
├── Protocol
└── Agent
```

각각은 다른 수준의 추상화를 갖는다.

---

# 4. Tool

## Definition

Tool은 하나의 명확한 행동을 수행하는 실행 가능한 Capability다.

예:

```text
read_file()
write_file()
search_web()
query_database()
send_message()
run_command()
```

Tool은 일반적으로:

```text
Tool
├── Name
├── Description
├── Input Schema
├── Output Schema
├── Permission
└── Execute
```

구조를 가진다.

OpenCode V2도 Tool을 description, schema, execute, model-facing output 등의 계약으로 분리하고 있으며, Permission을 Tool과 별도의 계층에서 다루는 방향을 보여준다.

---

# 5. Tool Design Principle

Tool은 가능한 한:

* 명확한 입력
* 명확한 출력
* 제한된 책임
* 검증 가능한 실행
* 추적 가능한 실행

을 가져야 한다.

Tool 하나가 너무 많은 책임을 가지면 Agent가 사용하기 어려워지고 테스트도 어려워진다.

---

# 6. Tool vs API

API와 Tool은 동일하지 않다.

```text
API
= 시스템이 제공하는 호출 인터페이스

Tool
= Agent가 사용할 수 있도록
  API 또는 기능을 Agent-facing 형태로 감싼 실행 단위
```

예:

```text
GitHub REST API
        ↓
GitHub Tool
        ↓
Agent
```

따라서 Tool은 외부 API에 대한 Agent-oriented abstraction이 될 수 있다.

---

# 7. Tool Schema

Tool Input은 가능한 한 구조화된 Schema를 가져야 한다.

```text
Tool
├── Input Schema
├── Validation
├── Execution
└── Output
```

자유로운 문자열보다 구조화된 입력을 사용하면:

* validation
* error handling
* tool selection
* logging
* evaluation

이 쉬워진다.

MCP의 최신 Tool 명세 역시 Tool마다 이름과 schema 등의 metadata를 갖는 구조를 사용한다.

---

# 8. Tool Result

Tool의 실제 실행 결과와 Model에 보여주는 결과를 분리할 수 있어야 한다.

```text
Tool Result
   │
   ├── Full Result
   │
   └── Model-facing Projection
```

예를 들어 100MB의 파일 검색 결과를 그대로 Model에 넣지 않고:

```text
Full Result
→ durable storage

Relevant Result
→ Context
```

로 분리할 수 있다.

이 원칙은 Context & State Review의 결과와도 연결된다.

---

# 9. Tool Side Effects

Tool은 크게 두 종류로 구분할 수 있다.

```text
Read-only
├── read_file
├── search
├── query
└── inspect

Mutating
├── write_file
├── delete_file
├── send_message
├── deploy
└── purchase
```

NOAH에서는 Side Effect가 있는 Tool일수록:

```text
Tool
 ↓
Policy
 ↓
Approval
 ↓
Execution
```

경로를 검토한다.

---

# 10. Skill

Skill은 Tool과 다르다.

초기 정의:

> Skill은 특정 문제를 해결하기 위한 재사용 가능한 procedural capability다.

즉 Skill은 단순 행동 하나가 아니라:

```text
Skill
├── When to use
├── Preconditions
├── Procedure
├── Allowed Tools
├── Constraints
├── Verification
└── Termination Condition
```

을 포함할 수 있다.

최근 Agentic Skills 연구에서도 Skill을 long-horizon workflow를 수행하기 위한 reusable procedural capability로 정의하고, discovery, practice, distillation, storage, composition, evaluation, update라는 lifecycle을 제안한다.

---

# 11. Skill vs Tool

```text
Tool
= 하나의 행동

Skill
= 여러 행동을 이용하여 특정 목적을 수행하는
  재사용 가능한 절차
```

예:

```text
Tool
→ git_commit()

Skill
→ Release a Project
   ├── inspect repository
   ├── run tests
   ├── update version
   ├── create commit
   ├── create tag
   └── verify release
```

---

# 12. Skill vs Prompt

Skill을 단순 Prompt 파일로만 취급하지 않는다.

최근 Skill 연구에서는 prose skill을 Model이 매 실행마다 다시 해석해야 하는 문제가 발견되었고, SIGIL은 이를 typed harness로 compile하는 방식을 제안한다. 해당 연구에서는 prose 기반 skill보다 compiled harness가 절차 준수율을 높인 결과를 보고했다.

따라서 NOAH에서는:

```text
Skill
= 설명 문서
        +
Execution Contract
        +
Verification
```

형태를 장기적으로 검토한다.

---

# 13. Skill Activation

Skill은 항상 모든 Context에 포함시키지 않는다.

```text
Task
 ↓
Skill Discovery
 ↓
Relevant?
 ↓
Load
 ↓
Execute
```

이를 Progressive Disclosure와 연결한다.

2026년 Skill-Use 연구에서는 Agent가 Skill을 실제로 찾아내고(trigger), 절차를 준수하고(compliance), 금지된 작업을 피하는(boundary) 능력을 별도로 평가하며, Skill 사용 성능이 harness에 의존한다는 결과를 보고한다.

---

# 14. Workflow

Workflow는 여러 단계의 실행 순서를 표현한다.

```text
Workflow
├── Step 1
├── Step 2
├── Step 3
└── Completion
```

Workflow는:

* deterministic
* semi-deterministic
* agent-driven

으로 나뉠 수 있다.

---

# 15. Workflow vs Skill

```text
Skill
= "무엇을 어떻게 잘 수행하는가"

Workflow
= "여러 단계가 어떤 순서로 진행되는가"
```

예:

```text
Skill
→ Analyze PostgreSQL Query

Workflow
→ Database Migration
   1. Backup
   2. Generate Migration
   3. Validate
   4. Apply
   5. Test
   6. Rollback if failed
```

둘은 결합될 수 있다.

---

# 16. Protocol

Protocol은 Agent가 다른 시스템 또는 다른 Agent와 상호작용하는 규약이다.

예:

* MCP
* ACP
* HTTP
* WebSocket
* Agent-to-Agent protocol

Protocol은 Capability 그 자체가 아니라 **Capability를 연결하는 통신 계약**에 가깝다.

---

# 17. MCP

MCP는 Tool을 Agent Runtime에 연결하는 중요한 표준 후보이다.

2026년 MCP Roadmap은 단순 Tool 연결을 넘어:

* transport scalability
* agent communication
* governance
* enterprise readiness

를 주요 방향으로 다루고 있다.

따라서 NOAH에서는 MCP를:

```text
Capability
   ↓
Protocol Adapter
   ↓
External Server
```

로 취급하는 방향을 검토한다.

---

# 18. Agent Delegation

Agent 자신도 Capability가 될 수 있다.

예:

```text
Primary Agent
    ↓
Delegate
    ↓
Research Agent
```

OpenCode의 Subagent 구조와 OpenAI의 handoff / agent-as-tool 패턴 모두 이 방향의 Reference가 된다. OpenAI는 Agent handoff를 핵심 orchestration primitive로 제공하고 있다.

하지만 Agent delegation은 일반 Tool 호출보다 큰 상태와 비용을 발생시킨다.

따라서:

```text
Tool
< Skill
< Agent Delegation
```

처럼 점점 더 큰 실행 단위로 볼 수 있다.

---

# 19. Capability Hierarchy

초기 후보 계층:

```text
Capability
│
├── Atomic
│   └── Tool
│
├── Procedural
│   └── Skill
│
├── Orchestration
│   └── Workflow
│
├── Communication
│   └── Protocol
│
└── Cognitive
    └── Agent Delegation
```

이 구조는 아직 Candidate Architecture다.

---

# 20. Capability Composition

Capability는 서로 조합될 수 있어야 한다.

```text
Skill
 ├── Tool A
 ├── Tool B
 └── Tool C
```

또는:

```text
Workflow
 ├── Skill A
 ├── Tool B
 └── Agent C
```

따라서 Capability 사이에 명확한 interface가 필요하다.

---

# 21. Capability Contract

모든 Capability가 최소한 다음 정보를 제공하는 방향을 검토한다.

```text
Capability
├── Identity
├── Description
├── Input Contract
├── Output Contract
├── Preconditions
├── Permissions
├── Side Effects
├── Cost
├── Timeout
└── Verification
```

이런 계약이 있으면 Tool, Skill, Workflow, Agent를 서로 다른 실행 단위로 유지하면서도 공통적으로 다룰 수 있다.

---

# 22. Capability Discovery

Agent가 어떤 Capability를 사용할 수 있는지 모두 Context에 넣지 않는다.

```text
Capability Registry
        ↓
Discovery
        ↓
Relevant Capabilities
        ↓
Context
        ↓
Agent
```

이 방식은 Context 크기를 줄이고 Skill/Tool 수가 늘어날 때 확장성을 높일 수 있다.

---

# 23. Capability Registry

후보 구조:

```text
Capability Registry
├── Tools
├── Skills
├── Workflows
├── Protocols
└── Agents
```

각 Capability에는:

```text
ID
Version
Description
Schema
Permission
Availability
Provider
```

같은 metadata가 연결될 수 있다.

---

# 24. Capability Versioning

Capability도 버전이 바뀔 수 있다.

```text
Tool v1
Tool v2

Skill v1
Skill v2
```

특히 Memory나 Workflow가 Skill을 참조하고 있다면 Versioning이 중요하다.

따라서:

```text
Capability
→ Version
→ Dependency
→ Compatibility
```

를 관리할 필요가 있다.

---

# 25. Capability Permissions

Capability와 Permission은 분리한다.

```text
Capability
= 무엇을 할 수 있는가

Permission
= 누가 언제 어떤 조건에서 실행할 수 있는가
```

예:

```text
Capability
→ filesystem.write

Policy
→ ask

Condition
→ only inside project workspace
```

---

# 26. Policy Layer

Policy는 Capability 실행의 조건을 정의한다.

후보:

```text
Policy
├── Identity
├── Scope
├── Environment
├── Resource
├── Risk
├── Approval
└── Time
```

예:

```text
write_file
→ allowed

write_file outside workspace
→ deny

delete_file
→ ask

send_payment
→ explicit approval
```

---

# 27. Approval

모든 Tool에 Approval을 요구하면 UX가 나빠진다.

반대로 모든 Tool을 자동 허용하면 위험하다.

따라서 Risk-aware approval을 검토한다.

```text
Risk
├── Low
│   └── Auto
├── Medium
│   └── Policy-dependent
└── High
    └── Explicit Approval
```

OpenAI의 최신 Agents SDK 역시 approvals와 guardrails를 Agent harness의 중요한 primitive로 포함한다.

---

# 28. Capability Risk

Capability는 위험도를 가질 수 있다.

예:

```text
Risk
├── Read
├── Local Mutation
├── External Mutation
├── Financial
├── Identity / Auth
└── Irreversible
```

이 Risk 정보를 Policy와 연결한다.

---

# 29. Side Effect Classification

Capability는 Side Effect를 metadata로 가져갈 수 있다.

```text
Side Effect
├── None
├── Local
├── External
├── Reversible
└── Irreversible
```

이를 기반으로 Approval 및 Evaluation을 달리할 수 있다.

---

# 30. Tool Execution Boundary

Agent가 Tool implementation을 직접 호출하지 않는다.

```text
Agent
 ↓
Capability Request
 ↓
Policy
 ↓
Executor
 ↓
Tool
 ↓
Environment
```

이렇게 실행 경계를 두면:

* permission
* tracing
* retry
* timeout
* sandbox
* audit

를 중앙에서 관리할 수 있다.

---

# 31. Sandbox Integration

Capability 실행은 필요에 따라 Sandbox에서 수행한다.

```text
Agent
 ↓
Capability
 ↓
Policy
 ↓
Sandbox
 ↓
Tool
 ↓
Environment
```

OpenAI의 2026 Agents SDK도 harness와 compute를 분리하여 agent tools, skills, memory를 sandbox와 연결하는 구조를 제공하고 있다.

---

# 32. External Service Integration

External Service는 Capability의 구현 대상이 될 수 있다.

```text
Capability
 ↓
Tool / Protocol Adapter
 ↓
External Service
```

예:

* GitHub
* Google Calendar
* Gmail
* Discord
* Notion
* Database
* NAS

중요한 것은 외부 서비스 자체가 NOAH Architecture에 직접 침투하지 않도록 adapter boundary를 갖는 것이다.

---

# 33. Protocol vs Tool

예:

```text
MCP
= Protocol

filesystem.read
= Tool

research.skill
= Skill

release.workflow
= Workflow
```

따라서 하나의 Protocol이 여러 Tool을 노출할 수 있다.

---

# 34. Capability vs Plugin

Plugin은 Capability의 구현 또는 확장 mechanism일 수 있다.

```text
Plugin
 ↓
Registers
 ├── Tool
 ├── Skill
 ├── Workflow
 └── Protocol Adapter
```

Plugin 자체를 Capability로 정의하지 않고 **Capability를 공급하는 확장 메커니즘**으로 보는 방향을 검토한다.

---

# 35. Capability Lifecycle

Capability도 lifecycle을 가진다.

```text
Discover
 ↓
Register
 ↓
Validate
 ↓
Enable
 ↓
Use
 ↓
Evaluate
 ↓
Update
 ↓
Disable
 ↓
Archive
```

Skill 연구에서도 skill discovery, storage, composition, evaluation, update lifecycle이 중요하게 다뤄지고 있다.

---

# 36. Skill Lifecycle

Skill에 대해서는 보다 구체적으로:

```text
Experience
 ↓
Candidate Procedure
 ↓
Review
 ↓
Skill
 ↓
Evaluate
 ↓
Version
 ↓
Improve
```

를 검토한다.

장기적으로 NOAH가 경험에서 Skill을 생성할 수 있는 가능성을 고려한다.

---

# 37. Skill Evolution

Skill은 단순 정적 문서가 아니라 개선 가능한 자산이 될 수 있다.

최근 HASP는 Skill을 executable program function으로 확장하여 Agent loop에 직접 개입하는 방식과 skill library evolution을 제안한다.

NOAH에서는:

```text
Skill
 ↓
Execution
 ↓
Evaluation
 ↓
Failure / Success
 ↓
Skill Revision
```

을 장기 연구 대상으로 둔다.

단, **자동 Skill 수정은 즉시 허용하지 않는다.**

---

# 38. Capability Evaluation

Capability 자체도 평가 대상이 된다.

## Tool

* 정확성
* schema compliance
* error handling
* latency
* side effect correctness

## Skill

* Trigger
* Procedure compliance
* Boundary compliance
* Task success

## Workflow

* Completion
* Recovery
* Determinism
* Side effect safety

Skill-Use 연구는 skill 자체의 품질뿐 아니라 Agent가 skill을 발견하고 준수하는 능력을 별도로 평가해야 한다고 제안한다.

---

# 39. Capability Observability

각 Capability 실행을 추적할 수 있어야 한다.

```text
Capability Trace
├── Agent
├── Capability
├── Version
├── Input
├── Policy Decision
├── Approval
├── Execution
├── Output
├── Side Effects
├── Cost
├── Latency
└── Verification
```

이 정보는 Evaluation과 Debugging에 연결된다.

---

# 40. Capability Failure

Failure는 단순히 "Tool failed"가 아니다.

후보:

```text
Failure
├── Invalid Input
├── Permission Denied
├── Timeout
├── Network
├── Environment
├── Capability Logic
├── Model Misuse
├── Policy Violation
└── Verification Failure
```

Failure Type에 따라 Retry / Recovery 정책이 달라질 수 있다.

---

# 41. Capability Retry

Retry는 Capability metadata를 이용할 수 있다.

```text
Retry Policy
├── Retryable
├── Max Attempts
├── Backoff
├── Idempotency
└── Compensation
```

특히 외부 side effect를 가진 Tool은 idempotency 및 compensation이 중요하다.

---

# 42. Capability Idempotency

예:

```text
send_email()
```

을 재시도하면 같은 이메일이 두 번 갈 수 있다.

반면:

```text
read_file()
```

은 일반적으로 안전하게 재시도할 수 있다.

따라서 Capability Contract에:

```text
Idempotency
```

를 넣는 것을 검토한다.

---

# 43. Capability Transactions

모든 Capability를 transaction으로 만들 수는 없다.

그러나 일부 State-changing Capability는:

```text
Prepare
 ↓
Validate
 ↓
Commit
 ↓
Compensate
```

구조를 가질 수 있다.

이는 Context & State Review의 Canonical State 개념과 연결된다.

---

# 44. Capability Boundaries

Capability의 책임을 지나치게 크게 만들지 않는다.

```text
❌ "Do Everything"

✅ filesystem.write
✅ git.commit
✅ deploy_service
✅ analyze_database
```

큰 기능은 Skill / Workflow / Agent 계층으로 올린다.

---

# 45. Capability Composition Example

```text
Goal:
"Project release"

Workflow:
Release Project
    │
    ├── Skill: Release Preparation
    │      ├── Tool: git.status
    │      ├── Tool: run_tests
    │      └── Tool: version_update
    │
    ├── Tool: git.commit
    ├── Tool: git.tag
    └── Skill: Release Verification
```

이 구조에서는 각 계층의 책임이 분리된다.

---

# 46. Capability Discovery and Progressive Disclosure

Capability가 많아질수록 모두 Model Context에 넣을 수 없다.

후보 구조:

```text
Capability Registry
       ↓
Short Metadata
       ↓
Discovery
       ↓
Detailed Schema / Skill
       ↓
Execution
```

이는 최근 Skill-Use 연구에서 평가하는 progressive disclosure와도 연결된다.

---

# 47. Capability Security

Capability는 security boundary가 된다.

위험:

* prompt injection
* malicious tool descriptions
* confused deputy
* credential exposure
* privilege escalation
* unsafe side effects

따라서 Capability metadata와 Policy를 신뢰 경계의 일부로 취급한다.

---

# 48. Capability Provenance

Capability 자체도 출처를 가질 수 있다.

```text
Capability
├── Source
├── Author
├── Version
├── Signature
├── Trust Level
└── Dependencies
```

특히 외부 Plugin / Skill / MCP server를 추가하는 경우 중요하다.

---

# 49. Externalized Capabilities

2026년 연구는 memory, skills, protocols, harness를 모두 **외부화된 cognitive infrastructure**로 보는 관점을 제안한다.

NOAH에서는 이 관점에 따라:

```text
Model
   ↓
Agent
   ↓
External Cognitive Infrastructure
   ├── Memory
   ├── Skills
   ├── Tools
   ├── Protocols
   └── Harness
```

구조를 검토한다.

---

# 50. Capability vs Intelligence

Capability가 많다고 Agent가 반드시 똑똑해지는 것은 아니다.

```text
More Tools
≠
Better Agent
```

오히려:

* capability discovery 실패
* 잘못된 tool 선택
* 불필요한 호출
* tool overload
* context pollution

이 발생할 수 있다.

따라서 Capability 수보다 **Capability selection quality**를 중요하게 본다.

---

# 51. Capability Selection

Agent는:

```text
Goal
 ↓
Candidate Capabilities
 ↓
Rank
 ↓
Policy Filter
 ↓
Select
 ↓
Execute
```

과정을 수행할 수 있다.

장기적으로 Capability Router를 별도 subsystem으로 둘지 검토한다.

---

# 52. Capability Router

후보:

```text
Capability Router
├── Goal Analysis
├── Capability Discovery
├── Ranking
├── Policy Check
├── Cost Check
└── Selection
```

다만 Router 자체가 새로운 복잡도를 만들 수 있으므로 필요성이 검증될 때 추가한다.

---

# 53. Human-in-the-Loop

Capability가 위험할수록 Human approval이 필요하다.

```text
Capability
 ↓
Risk Assessment
 ↓
Policy
 ↓
Human Approval?
 ├── No → Execute
 └── Yes → Wait
             ↓
           Approve / Reject
```

OpenAI의 Agent infrastructure에서도 approvals, guardrails, tracing을 중요한 Agent primitives로 취급한다.

---

# 54. Capability Contracts and Future Resilience

미래에 새로운 AI 시스템이 등장해도:

```text
Tool Implementation
Skill Engine
Workflow Engine
Agent Framework
Protocol
```

가 교체될 수 있어야 한다.

따라서 안정적으로 유지할 것은:

```text
Capability Contract
Policy Contract
Execution Contract
Result Contract
```

로 두는 방향을 검토한다.

---

# 55. Candidate Architecture

현재 Review의 종합 후보:

```text
                         NOAH CAPABILITY SYSTEM
                                  │
                           Capability Registry
                                  │
       ┌───────────────┬──────────┼───────────┬───────────────┐
       │               │          │           │               │
      Tool           Skill    Workflow     Protocol       Agent
       │               │          │           │               │
       └───────────────┴──────────┼───────────┴───────────────┘
                                  │
                            Capability Router
                                  │
                              Policy Layer
                                  │
                              Approval
                                  │
                              Executor
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                 Sandbox      External       Local
                 /Workspace   Service        Runtime
                    │             │             │
                    └─────────────┼─────────────┘
                                  │
                               Result
                                  │
                            Verification
                                  │
                               Trace
                                  │
                          State / Memory
```

이것은 Candidate Architecture이며 최종 Blueprint가 아니다.

---

# 56. Candidate Contract

모든 Capability가 공유할 수 있는 최소 계약 후보:

```text
Capability
├── Identity
├── Version
├── Description
├── Input Schema
├── Output Schema
├── Preconditions
├── Permissions
├── Side Effects
├── Cost
├── Timeout
├── Retry Policy
├── Verification
└── Provenance
```

Capability 유형에 따라 일부 필드는 선택적일 수 있다.

---

# 57. What NOAH Should Not Do

## Everything = Tool

Reject.

## Skill = Prompt File Only

Reject as long-term architecture.

## Workflow = Agent

Reject.

## Protocol = Capability

Reject.

Protocol은 Capability를 연결할 수 있는 통신 규약이다.

## Capability = Permission

Reject.

Capability와 Permission은 분리한다.

## 모든 Capability를 Context에 항상 노출

Reject.

Discovery / Progressive Disclosure를 사용한다.

## 모든 Capability를 자동 승인

Reject.

Risk-aware Policy가 필요하다.

## 자동 Skill Evolution을 즉시 허용

Reject for initial implementation.

---

# 58. Candidate Decisions

| 주제                              | 초기 판단            |
| ------------------------------- | ---------------- |
| Capability 독립 계층                | Adopt            |
| Tool                            | Adopt            |
| Skill                           | Adopt            |
| Workflow                        | Adopt            |
| Protocol                        | Adopt            |
| Agent Delegation                | Adapt            |
| Capability Registry             | Adapt            |
| Capability Contract             | Adopt            |
| Progressive Discovery           | Adopt            |
| Policy 분리                       | Adopt            |
| Approval                        | Adopt            |
| Risk Classification             | Adapt            |
| Side Effect Metadata            | Adopt            |
| Idempotency Metadata            | Adapt            |
| Verification Contract           | Adopt            |
| Capability Provenance           | Research Further |
| Skill Versioning                | Adopt            |
| Skill Evolution                 | Research Further |
| Executable Skill / Harness      | Research Further |
| Capability Router               | Research Further |
| Multi-Agent-as-Capability       | Adapt            |
| Plugin as Capability Provider   | Adopt            |
| MCP Adapter                     | Adapt            |
| Automatic Capability Generation | Defer            |

---

# 59. Risks

## Capability Explosion

Capability가 늘어나면 Agent가 무엇을 사용할지 어려워진다.

## Tool Overload

너무 많은 Tool을 Model Context에 제공하면 선택 품질이 떨어질 수 있다.

## Skill Drift

Skill의 절차가 실제 시스템과 달라질 수 있다.

## Workflow Rigidity

Workflow가 지나치게 고정되면 Agent의 판단 능력을 제한할 수 있다.

## Permission Complexity

Capability 수가 많아질수록 Policy가 복잡해진다.

## External Dependency Risk

MCP / Plugin / External Service의 안정성과 보안에 영향을 받는다.

## Hidden Side Effects

Tool 설명에는 없지만 실제 실행에서 부작용이 발생할 수 있다.

## Capability Poisoning

악의적 또는 잘못된 Skill / Tool / Plugin이 Agent 행동을 조작할 가능성이 있다.

---

# 60. Open Questions

1. Tool과 Skill의 정확한 경계는 어디인가?
2. Skill과 Workflow는 어떻게 구분해야 하는가?
3. Protocol은 Capability Registry에 들어가야 하는가?
4. Agent Delegation은 Tool인가 Capability인가?
5. Capability Contract를 얼마나 엄격하게 표준화해야 하는가?
6. Capability Router가 실제로 필요한가?
7. Tool/Skill discovery는 Model이 직접 수행해야 하는가?
8. Capability selection을 deterministic하게 만들 수 있는가?
9. Skill을 executable harness로 compile하는 방향이 NOAH에 필요한가?
10. Skill Versioning은 어떻게 관리하는가?
11. Capability provenance를 어떻게 검증하는가?
12. External MCP server를 어느 trust level까지 허용하는가?
13. Capability가 생성한 side effect를 어떻게 검증하는가?
14. Capability 실패 후 어떤 recovery policy를 사용하는가?
15. Capability selection의 quality를 어떻게 평가하는가?
16. Capability 자체가 Memory를 생성하거나 수정할 수 있는가?
17. Skill이 경험으로부터 자동으로 생성될 수 있는가?
18. Workflow와 Agent가 결합될 때 경계는 어디인가?
19. Model이 Tool을 선택하는 것과 Capability Router가 선택하는 것 중 어떤 상황에 무엇을 사용할 것인가?
20. Capability가 미래의 NOAH Harness에 어떻게 학습 신호를 제공할 것인가?

---

# 61. Current Recommendation

현재까지의 Research를 기반으로:

> **NOAH는 Capability를 단일 Tool 개념으로 축소하지 않는다.**

Capability는 다음 계층을 포함하는 상위 개념으로 본다.

```text
Capability
├── Tool
├── Skill
├── Workflow
├── Protocol
└── Agent Delegation
```

그리고:

```text
Capability
    ↓
Policy
    ↓
Approval
    ↓
Execution
    ↓
Verification
    ↓
Trace
    ↓
State / Memory
```

라는 공통 실행 경계를 두는 방향이 유력하다.

---

# 62. Future Direction

Capability는 장기적으로 단순히 외부에서 공급받는 기능이 아니라 NOAH의 경험으로부터 발전할 가능성이 있다.

후보:

```text
Experience
 ↓
Failure / Success Pattern
 ↓
Candidate Skill
 ↓
Validation
 ↓
Skill
 ↓
Evaluation
 ↓
Skill Evolution
```

HASP는 Skill을 Agent loop에 직접 개입할 수 있는 executable program function으로 확장하는 방향을 제안하고 있으며, SIGIL은 prose skill을 typed executable harness로 컴파일하는 방향을 제안한다.

따라서 NOAH의 장기 목표에서도:

> **Experience → Skill → Better Execution**

이라는 경로를 연구할 가치가 있다.

---

# 63. Review Boundary

이번 Review에서는 다음을 최종 확정하지 않는다.

* Tool API
* Skill File Format
* Workflow Engine
* MCP implementation
* Capability Router implementation
* Permission Policy Language
* Sandbox implementation
* Skill learning algorithm
* Automatic Skill generation

이들은 후속 Specification / PoC에서 검증한다.

---

# 64. Review Outcome

현재까지의 Research를 종합하면:

```text
Tool
= Atomic capability

Skill
= Reusable procedural capability

Workflow
= Multi-step execution structure

Protocol
= Inter-system interaction contract

Agent
= Independent cognitive/execution entity
```

그리고 이들을:

```text
Capability Registry
        ↓
Discovery
        ↓
Policy
        ↓
Execution
        ↓
Verification
        ↓
State / Memory
```

로 연결하는 구조가 장기적으로 가장 유연한 후보로 보인다.

특히 최신 연구는 **skills가 단순 prompt보다 더 강한 procedural abstraction으로 발전하고 있으며, executable skill/harness 방향이 나타나고 있고, capability의 성능이 model만이 아니라 harness와 execution environment에 의해 결정된다**는 점을 보여준다.

---

# 65. Next Step

이번 Capability & Tools Review 이후 다음 Architecture Review에서:

**Permission & Security**

를 검토한다.

특히:

```text
Capability
    ↓
Risk
    ↓
Policy
    ↓
Permission
    ↓
Approval
    ↓
Sandbox
    ↓
Execution
    ↓
Verification
```

이라는 경계를 집중적으로 검토한다.

그 다음:

```text
Evaluation & Observability
        ↓
Orchestration / Multi-Agent
        ↓
Identity / Personality
        ↓
Integrated Architecture Review
        ↓
DDR
        ↓
02-Architecture
        ↓
PoC
```

순으로 진행한다.
