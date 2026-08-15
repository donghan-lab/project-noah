# Architecture Review — Context & State

> Project NOAH Architecture Review
> Review 대상: Context & State Architecture
> Review Version: 0.1
> Status: Review

---

# 1. Review Purpose

Project NOAH에서 Context와 State의 의미와 책임을 정의하고, Conversation, Task, Memory, Environment, Execution State와의 경계를 정하기 위한 Architecture Review를 수행한다.

본 Review의 핵심 질문은 다음과 같다.

> **"NOAH가 보유한 전체 상태 중 현재 Agent에게 어떤 정보를 어떤 형태로 제공해야 하는가?"**

그리고 다음 질문을 함께 검토한다.

* State와 Context는 같은 것인가?
* Memory와 State는 무엇이 다른가?
* Task State는 어디에 존재하는가?
* Environment State는 어떻게 표현하는가?
* Context는 누가 구성하는가?
* Context는 얼마나 오래 유지되는가?
* 무엇을 durable하게 저장해야 하는가?
* 현재 Context와 canonical state가 불일치하면 어떻게 하는가?
* 미래 Runtime으로 교체되어도 State를 유지할 수 있는가?

본 문서는 최종 Blueprint가 아니며, Context/State Architecture의 후보와 경계를 검토하기 위한 문서다.

---

# 2. Core Architecture Question

## Context란 무엇인가?

초기 정의:

> Context는 Agent가 현재 작업을 수행하기 위해 필요한 정보를 실행 시점에 선택하고 구성한 Model-facing information set이다.

따라서 Context는 시스템이 보유한 전체 정보와 동일하지 않다.

```text
System State
     ↓
Context Selection
     ↓
Context Assembly
     ↓
Model Context
```

---

# 3. State란 무엇인가?

State는 시스템이 실제로 유지해야 하는 canonical information이다.

후보:

```text
State
├── Identity State
├── Conversation State
├── Task State
├── Execution State
├── Environment State
├── Workspace State
├── Memory State
├── Policy State
└── Approval State
```

State는 원칙적으로 Context보다 오래 존재할 수 있다.

---

# 4. Context vs State

가장 중요한 기본 구분:

```text
State
= 시스템이 실제로 보유하는 정보

Context
= 현재 실행에 필요한 State의 일부를
  Model이 이해할 수 있는 형태로 조립한 것
```

즉:

```text
Durable State
     ↓
Selection
     ↓
Transformation
     ↓
Context
     ↓
Model
```

이 구조를 기본 후보로 둔다.

---

# 5. Conversation vs Session vs Task vs State

다음 개념을 구분한다.

## Conversation

사용자와 Agent 사이에서 발생한 상호작용의 기록.

## Session

특정 실행 관계를 지속적으로 관리하는 논리적 컨테이너.

## Task

달성하려는 목표와 그 진행 상태.

## State

시스템이 현재 canonical하게 보유하고 있는 정보.

개념적으로:

```text
Session
├── Conversation
├── Task Reference
├── Execution
└── State References
```

Task가 Session보다 오래 지속될 가능성도 고려한다.

```text
Session 1
   ↓
Checkpoint
   ↓
Session 2
   ↓
Same Task continues
```

---

# 6. Task State

Long-horizon Agent에서는 Task의 상태를 Context만으로 유지하는 방식에 한계가 있다.

최근 연구들은 작업 상태를 외부에 명시적으로 유지하고, 실행기가 현재 상태를 읽어 다음 행동을 수행하는 구조를 제안한다.

따라서:

```text
Task State
├── Goal
├── Requirements
├── Constraints
├── Progress
├── Current Step
├── Completed Steps
├── Blockers
├── Verification
└── Next Action
```

을 별도 개념으로 관리하는 것을 검토한다.

---

# 7. Environment State

Environment State는 Agent가 작업하는 실제 환경의 상태다.

예:

```text
Environment State
├── Files
├── Repository
├── Processes
├── Installed Dependencies
├── Network State
├── External Services
└── Runtime Resources
```

Environment State는 Context의 일부가 될 수 있지만 Context 그 자체는 아니다.

```text
Environment State
      ↓
Relevant Observation
      ↓
Context
```

---

# 8. Workspace State

Workspace는 Environment의 일부지만 Agent 작업에서 중요하므로 별도로 관리하는 것을 검토한다.

예:

```text
Workspace
├── Source Files
├── Generated Files
├── Artifacts
├── Test Results
├── Git State
└── Temporary Files
```

Workspace State는 가능한 경우 직접 Context에 모두 넣지 않고, 필요할 때 observation 또는 tool result로 제공한다.

---

# 9. Memory vs State

Memory와 State를 동일한 개념으로 취급하지 않는다.

초기 구분:

```text
State
= 현재 시스템의 canonical condition

Memory
= 과거 경험이나 지식 중
  미래 판단에 사용할 수 있도록 보존된 information
```

예:

```text
Current Task State
= "현재 README 수정 단계"

Memory
= "이 프로젝트에서 README는
  이전에 이런 구조를 사용했다."
```

Memory는 과거를 저장하고 State는 현재를 표현한다.

---

# 10. Memory vs Context

Memory도 Context와 동일하지 않다.

```text
Memory
   ↓
Retrieval / Selection
   ↓
Context
   ↓
Model
```

모든 Memory가 Context로 들어가는 것이 아니라 현재 작업에 필요한 Memory만 선택한다.

---

# 11. Context Sources

NOAH Context의 후보 Source:

```text
Context
├── System Instructions
├── Agent Identity
├── Agent Role
├── Current User Input
├── Conversation History
├── Task State
├── Retrieved Memory
├── Knowledge
├── Tool Results
├── Environment Observations
├── Workspace Information
├── Skill Instructions
├── Policy / Permission Constraints
└── Previous Execution Summary
```

이 모든 정보를 항상 Context에 포함시키지 않는다.

---

# 12. Context Selection

Context는 단순 concatenation이 아니라 selection problem으로 본다.

후보 기준:

```text
Relevance
Recency
Authority
Reliability
Task Importance
Cost
Risk
Dependency
```

Context budget도 중요한 제약 조건으로 본다.

---

# 13. Context Hierarchy

Context를 여러 레이어로 나누는 것을 검토한다.

```text
Context
├── Core Context
│   ├── Identity
│   ├── Role
│   └── Policy
│
├── Task Context
│   ├── Goal
│   ├── Progress
│   └── Constraints
│
├── Working Context
│   ├── Recent Conversation
│   ├── Tool Results
│   └── Current Observations
│
└── Retrieved Context
    ├── Memory
    ├── Knowledge
    └── External Data
```

이 구조는 미래의 Context optimization에 대응하기 위한 후보 구조다.

---

# 14. Context Management

Context Manager의 역할 후보:

```text
Context Manager
├── Select
├── Rank
├── Assemble
├── Compress
├── Validate
├── Prioritize
└── Budget
```

Agent 자체가 Context를 직접 구성하기보다 별도의 Context Management 계층을 두는 방향을 검토한다.

---

# 15. Context Budget

Context에는 비용이 존재한다.

비용:

```text
Token
Latency
Money
Attention
Noise
```

따라서 Context Manager는:

```text
Maximum Context Budget
       ↓
Selection
       ↓
Compression
       ↓
Final Context
```

구조를 사용해야 한다.

---

# 16. Context Compression

현재 연구와 OpenCode/Anthropic의 long-horizon 설계를 고려하면 Context Compression은 중요한 Runtime 기능이다. Anthropic은 장기 실행 Agent에서 compaction과 structured memory를 context-management 전략으로 사용하고 있다.

후보:

```text
Full History
   ↓
Summarization
   ↓
Structured Summary
   ↓
Recent Context
   ↓
Model
```

하지만 요약만으로 모든 정보를 대체해서는 안 된다.

원본 State와 History는 가능한 경우 durable하게 보존한다.

---

# 17. Context Epoch / Versioning

OpenCode는 Context Epoch를 통해 특정 실행 시점에 사용된 Context 상태를 관리한다.

NOAH에서도 Context 변경을 추적할 필요가 있는지 검토한다.

후보:

```text
Context Version
    ↓
Sources
    ↓
Changes
    ↓
Current Context
```

목적:

* Reproducibility
* Debugging
* Recovery
* Evaluation
* Audit

---

# 18. Canonical State

최근 State-aware runtime 연구는 Model이 생성한 결과와 시스템의 canonical state를 분리하고, 상태 변경 전에 validation과 commit/rollback을 두는 방향을 제안한다. 이는 아직 초기 연구 영역이지만 NOAH의 장기 Runtime 설계에서 중요한 후보 개념이다.

후보:

```text
Model Proposal
      ↓
Validation
      ↓
State Mutation
      ↓
Commit
      │
      ├── Success
      └── Rollback / Compensation
```

Agent가 "이렇게 됐다"고 말하는 것과 실제 시스템 State가 바뀌는 것을 동일하게 취급하지 않는다.

---

# 19. State Mutation

State를 변경하는 작업은 read-only observation과 구분한다.

```text
Read
= State를 관찰

Propose
= State 변경을 제안

Validate
= 변경이 허용되는지 확인

Commit
= 실제 State 변경

Audit
= 변경 결과 기록
```

이는 Tool Execution과 State Management를 연결하는 중요한 경계가 될 수 있다.

---

# 20. Memory Write Boundary

Memory도 무조건 State 변경 직후 자동 기록하지 않는다.

후보:

```text
Experience
   ↓
Candidate Memory
   ↓
Validation / Filtering
   ↓
Memory Write
```

2026년 Memory survey는 write-path filtering, contradiction handling, privacy governance를 실제 Memory 시스템의 중요한 엔지니어링 문제로 지적한다.

따라서 Memory Write는 독립적인 정책을 가질 필요가 있다.

---

# 21. Memory Poisoning / Trust

Persistent Memory는 새로운 보안 경계를 만든다.

최근 보안 연구와 실제 사례 분석에서는 공격자가 외부 콘텐츠를 통해 지속 Memory에 잘못된 정보를 주입하는 memory poisoning 문제가 중요한 위험으로 부상하고 있다.

따라서:

```text
External Data
   ↓
Memory Candidate
   ↓
Trust / Risk Assessment
   ↓
Memory
```

구조를 검토해야 한다.

Memory에 저장되었다는 이유만으로 "사실"로 취급하지 않는다.

---

# 22. Memory Lifecycle

Memory 자체는 별도 Architecture Review 대상이지만, Context/State Review에서 lifecycle boundary를 정의한다.

```text
Experience
 ↓
Candidate
 ↓
Validate
 ↓
Write
 ↓
Manage
 ↓
Retrieve
 ↓
Use
 ↓
Update
 ↓
Forget / Archive
```

2026년 Memory 연구는 이 write–manage–read lifecycle을 명시적으로 다루고 있으며, 일부 연구는 memory operation 자체를 Agent Action으로 학습시키는 접근까지 제안한다.

NOAH에서는 당장 학습 기반 memory management를 채택하지 않는다.

---

# 23. Working Memory

Working Memory는 현재 Task와 직접 관련된 단기 상태다.

예:

```text
Working Memory
├── Current Plan
├── Recent Observations
├── Active Constraints
├── Recent Tool Results
└── Temporary Conclusions
```

Working Memory는 Context와 밀접하지만 반드시 동일한 저장 구조일 필요는 없다.

---

# 24. Long-Term Memory

Long-Term Memory는 현재 실행을 넘어 유지할 가치가 있는 정보다.

예:

```text
Long-Term Memory
├── Facts
├── Preferences
├── Experiences
├── Lessons
└── Knowledge
```

Long-Term Memory는 Context에 직접 포함되지 않고 필요할 때 retrieval을 통해 사용한다.

---

# 25. Externalized State vs In-Context State

NOAH에서는 다음 구분을 선호한다.

```text
Externalized
├── Task State
├── Canonical State
├── Memory
├── Workspace State
└── Execution Checkpoints

In Context
├── Relevant Task State
├── Retrieved Memory
├── Current Observations
└── Immediate Working Information
```

즉 Context는 State의 source of truth가 아니다.

---

# 26. Context Freshness

Context가 항상 최신이라고 가정하지 않는다.

예:

```text
Context Created
      ↓
Environment Changed
      ↓
Context Stale
      ↓
Refresh / Re-observe
      ↓
Updated Context
```

특히 파일, 프로세스, 외부 API, Database 등 변할 수 있는 환경에서는 Context freshness를 고려해야 한다.

---

# 27. Context Authority

모든 Context Source가 동일하게 신뢰할 수 있는 것은 아니다.

후보 우선순위:

```text
System / Policy
    >
Canonical State
    >
Verified Task State
    >
Trusted Memory
    >
Recent Observation
    >
External Retrieved Data
    >
Unverified Model Assumption
```

이 우선순위는 Prompt Injection 및 Memory Poisoning 대응에도 중요하다.

---

# 28. Context Provenance

Context Source마다 출처를 추적할 수 있어야 한다.

예:

```text
Context Item
├── Source
├── Timestamp
├── Version
├── Trust Level
└── Transformation History
```

이 정보는 이후:

* Debugging
* Evaluation
* Citation
* Audit
* Security

에서 활용할 수 있다.

---

# 29. State Conflict

서로 다른 State Source가 충돌할 수 있다.

예:

```text
Memory
= "프로젝트는 Python 3.12"

Environment
= Python 3.13

Project Config
= Python 3.13
```

NOAH는 단순히 가장 최근에 읽은 값으로 결정하지 않는다.

후보:

```text
Conflict
 ↓
Source Authority
 ↓
Freshness
 ↓
Verification
 ↓
Resolution
 ↓
Canonical State
```

---

# 30. State Transition

State 변경을 명시적인 Transition으로 표현하는 것을 검토한다.

```text
State A
   ↓
Proposal
   ↓
Validation
   ↓
State B
```

이를 통해:

* 변경 추적
* Rollback
* Audit
* Recovery
* Replay

를 단순화할 수 있다.

---

# 31. State-Aware Runtime

현재 연구에서 중요한 후보 개념:

```text
Model
 ↓
Proposal
 ↓
State-Aware Runtime
 ├── Validate
 ├── Commit
 ├── Rollback
 ├── Audit
 └── Recover
 ↓
Canonical State
```

이는 2026년의 초기 State-Aware Runtime 연구와 방향이 맞으며, 아직 표준적인 Architecture라고 보기는 어렵다.

따라서 NOAH에서는 **Research Further** 상태로 둔다.

---

# 32. Future Resilience

Context/State 설계는 특정 LLM Context Window에 종속되어서는 안 된다.

예:

```text
❌ "Model은 1M tokens를 지원한다."

✅ "Context Manager는 현재 Model의 budget을 보고
   필요한 State를 선택한다."
```

Model Context Window가:

* 100K
* 1M
* 10M
* Unknown Future

로 변화해도 Context Manager의 책임은 유지되어야 한다.

---

# 33. Candidate Architecture

현재 Review의 후보 구조:

```text
                         NOAH State System
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
         Canonical State     Memory           Environment
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                           State Access
                                │
                        Context Manager
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
          Select              Rank             Compress
             │                  │                  │
             └──────────────────┼──────────────────┘
                                │
                          Current Context
                                │
                              Agent
                                │
                             Runtime
```

이것은 Candidate Architecture이며 최종 Blueprint가 아니다.

---

# 34. Candidate State Taxonomy

현재 기준으로 다음 분류를 검토한다.

| State        | 수명                | Source of Truth | Context 포함 |
| ------------ | ----------------- | --------------- | ---------- |
| Conversation | Session 이상        | History         | 선택         |
| Task         | Session 이상        | Task Store      | 선택         |
| Execution    | Runtime           | Runtime State   | 필요 시       |
| Workspace    | Environment       | Workspace       | 관찰 형태      |
| Environment  | 외부                | Environment     | 관찰 형태      |
| Memory       | 장기                | Memory System   | Retrieval  |
| Policy       | 장기                | Policy Store    | 필요한 제약만    |
| Approval     | Execution/Session | Approval State  | 필요 시       |

---

# 35. Candidate Decisions

| 주제                                | 초기 판단            |
| --------------------------------- | ---------------- |
| Context ≠ State                   | Adopt            |
| Memory ≠ State                    | Adopt            |
| Context ≠ Memory                  | Adopt            |
| Session ≠ Task                    | Adapt            |
| Externalized Task State           | Adopt            |
| Context Manager 분리                | Adapt            |
| Canonical State 개념                | Adopt            |
| State Mutation Validation         | Research Further |
| Context Versioning                | Research Further |
| Context Provenance                | Adapt            |
| Source Authority                  | Adopt            |
| Context Freshness                 | Adopt            |
| Memory Write Filtering            | Research Further |
| Memory Poisoning Defense          | Research Further |
| Learned Memory Policy             | Defer            |
| Full State Event Sourcing         | Defer            |
| Future Model Context Independence | Adopt            |

---

# 36. What NOAH Should Not Do

## Context를 Source of Truth로 사용하지 않는다.

Context가 사라져도 canonical state는 남아 있어야 한다.

## 모든 Memory를 Context에 넣지 않는다.

Retrieval과 Selection을 통해 필요한 정보만 가져온다.

## Model의 Memory를 시스템의 Memory로 간주하지 않는다.

Model 내부 추론과 NOAH의 persistent memory는 다른 개념이다.

## Tool Output을 무조건 State로 승격하지 않는다.

관찰 결과와 검증된 canonical state는 다르다.

## 가장 최신 정보가 항상 가장 정확하다고 가정하지 않는다.

Authority와 Verification이 필요하다.

---

# 37. Architecture Risks

## Context Explosion

Context source가 계속 늘어날 수 있다.

## State Fragmentation

State가 여러 storage에 분산되면 consistency 문제가 발생할 수 있다.

## Stale Context

실제 환경과 Context가 불일치할 수 있다.

## Memory Contamination

잘못된 정보가 persistent memory에 들어갈 수 있다.

## State Mutation Risk

Agent가 제안한 변경을 잘못 commit할 수 있다.

## Provenance Overhead

모든 Context item의 provenance를 추적하면 저장/처리 비용이 증가한다.

## Over-Engineering

State를 지나치게 세분화하면 Runtime이 불필요하게 복잡해질 수 있다.

---

# 38. Open Questions

1. Canonical State의 정확한 범위는 어디까지인가?
2. Task State는 자체 database가 필요한가?
3. Conversation History와 Task State는 어떻게 연결하는가?
4. Context Version은 어떤 granularity를 가져야 하는가?
5. Context item의 provenance를 반드시 저장해야 하는가?
6. Source Authority를 정적으로 정의할 것인가?
7. Memory Confidence와 State Confidence는 분리해야 하는가?
8. Agent가 Memory를 직접 write할 것인가?
9. Memory write는 별도 policy engine을 통과해야 하는가?
10. Tool Output은 언제 canonical state가 되는가?
11. Environment observation의 freshness는 어떻게 검증하는가?
12. State conflict resolution은 Runtime 책임인가 State Manager 책임인가?
13. State-Aware Runtime이 실제로 필요한 수준의 복잡성을 감수할 가치가 있는가?
14. 미래의 초장문 Context Model이 등장하면 Context Manager의 역할은 어떻게 바뀌는가?
15. Context Manager가 학습 가능한 policy가 되는 것이 장기적으로 유리한가?

---

# 39. Current Recommendation

현재 근거로는 다음 방향을 가장 유력한 후보로 둔다.

> **NOAH는 Context를 State의 source of truth로 사용하지 않는다.**

> **NOAH는 Conversation, Task, Execution, Memory, Environment를 서로 다른 상태 개념으로 관리하고, Context Manager가 현재 실행에 필요한 정보만 선택하여 Model에 제공한다.**

> **State는 가능한 한 externalized / durable하게 유지하고, Context는 ephemeral projection으로 취급한다.**

개념적으로:

```text
Canonical State
      ↓
State Access
      ↓
Context Selection
      ↓
Context Assembly
      ↓
Model
      ↓
Proposal
      ↓
Validation
      ↓
Canonical State Update
```

이 구조를 NOAH의 장기적인 Context/State 방향으로 검토한다.

---

# 40. Future Architecture Direction

미래의 NOAH에서는 Context Manager 자체가 정적 규칙이 아니라:

```text
Context Manager
      ↓
Observe
      ↓
Select
      ↓
Compress
      ↓
Evaluate
      ↓
Improve
```

의 형태로 발전할 가능성도 있다.

최근 Memory research에서는 memory operation 자체를 Agent policy가 결정하도록 학습하는 접근도 등장하고 있어, 장기적으로 Context/Memory Management가 단순 deterministic middleware를 넘어 학습 가능한 policy가 될 가능성을 고려한다.

다만 이는 현재 NOAH의 구현 대상으로 확정하지 않는다.

---

# 41. Review Boundary

이번 Review에서는 다음을 최종 확정하지 않는다.

* Memory Architecture
* Retrieval Architecture
* Vector / Graph Storage
* Task Database
* State Store
* Context Compression Algorithm
* Context Learning Policy
* State-Aware Runtime 구현 방식

이들은 후속 Review 또는 PoC에서 검증한다.

---

# 42. Review Outcome

현재까지의 Research를 종합하면:

```text
Conversation
     ≠
Session
     ≠
Task
     ≠
Execution
     ≠
State
     ≠
Context
     ≠
Memory
     ≠
Environment
```

로 구분하는 방향이 장기적으로 가장 유연하다.

특히 2026년 최신 연구와 시스템 설계는 **State의 지속성, Memory의 관리, Context의 선택, 실행 환경의 분리, 검증 가능한 상태 변화**를 Agent Architecture의 핵심 문제로 다루는 방향으로 이동하고 있다.

따라서 NOAH의 Context & State는 단순 Prompt Management가 아니라 **Agent가 현실 세계와 지속적으로 상호작용하기 위한 State Management Layer**로 발전시키는 방향이 유력하다.

---

# 43. Next Step

이번 Review 후 바로 Memory 구현에 들어가지 않는다.

다음 순서:

```text
Context & State Review
          ↓
Open Questions
          ↓
필요한 추가 Research
          ↓
DDR
          ↓
Blueprint
          ↓
PoC
```

다음 Architecture Review에서는:

> **Memory Architecture**

를 독립적으로 검토한다.

특히 다음을 집중적으로 다룬다.

* Working Memory
* Episodic Memory
* Semantic Memory
* Procedural Memory
* Knowledge
* Experience
* Memory Write / Manage / Read
* Consolidation
* Retrieval
* Forgetting
* Contradiction
* Trust / Provenance
* Privacy
* Memory Evaluation
