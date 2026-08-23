Harness Boundary Research v0.1
# Harness Boundary Research

> Project NOAH Research
> Research 대상: Agent Harness Boundary
> Research Version: 0.1
> Priority: P0
> Status: Research

---

# 1. Research Purpose

Project NOAH에서 Agent와 그 주변 실행 시스템의 책임을 분리하고,
Harness가 어떤 기능을 소유해야 하는지 정의하기 위한 연구를 수행한다.

핵심 질문:

> "Agent가 직접 담당해야 하는 것과 Harness가 대신 담당해야 하는 것은 무엇인가?"

본 문서는 최종 Architecture를 결정하지 않는다.

---

# 2. Why This Research Matters

Architecture Integration Review에서 다음 경계가 아직 명확하게 정의되지 않았다.

- Agent
- Harness
- Runtime
- Orchestrator
- Context Manager
- Memory
- Capability
- Policy
- Evaluation

특히 다음 문제가 존재한다.

- Agent가 너무 많은 책임을 가지면 복잡성이 증가한다.
- Harness가 너무 많은 책임을 가지면 Agent 자체가 단순한 Model wrapper로 축소될 수 있다.
- Runtime과 Harness가 동일해질 가능성이 있다.
- Orchestrator와 Harness가 중복될 가능성이 있다.
- Context / Memory / Tool / Security가 어디까지 Harness에 속하는지 불명확하다.

따라서 Harness Boundary를 P0 Research로 지정한다.

---

# 3. Current NOAH Hypothesis

현재 가설:

> Harness는 Agent가 안정적이고 재현 가능하며 안전하게 행동하도록 지원하는 실행 환경 및 제어 계층이다.

후보 책임:

```text
Harness
├── Context Management
├── Capability Management
├── Tool Execution Coordination
├── Memory Access
├── Policy Enforcement
├── State Management
├── Runtime Integration
├── Observability
├── Verification
└── Recovery

이 가설을 Research에서 검증한다.

4. Agent vs Harness

가장 중요한 구분.

Agent
Understand
Reason
Plan
Decide
Act
Harness
Provide Context
Provide Capabilities
Enforce Policy
Execute
Observe
Recover
Evaluate

초기 후보:

Agent
↓
Decision

Harness
↓
Execution Environment
5. Agent Is Not The Whole System

LLM 또는 Agent가 다음을 직접 소유하는 구조는 피한다.

Database
Sandbox
Credential
Permission Engine
Telemetry Backend
Task Store
Memory Storage

대신 Interface를 통해 Harness가 제공한다.

6. Harness vs Runtime

현재 가장 중요한 경계 중 하나.

Runtime

실제 Execution Lifecycle.

Turn
Tool
Retry
Pause
Resume
Cancellation
Recovery
Harness

Agent가 Runtime을 포함한 시스템을 이용하도록 조정하는 상위 execution substrate.

후보:

Harness
└── Runtime

그러나:

Harness = Runtime

일 가능성도 연구한다.

7. Harness vs Orchestrator
Orchestrator
What should happen next?
Which agent?
Which strategy?
Harness
How can the selected execution happen safely?

후보:

Task
 ↓
Orchestrator
 ↓
Harness
 ↓
Agent / Runtime / Capability

이 경계를 검증한다.

8. Harness vs Context Manager

Context Manager가 Harness의 subsystem인지 독립 layer인지 검토한다.

후보:

Harness
└── Context Manager

또는:

Agent
 ↓
Context Manager

둘의 장단점을 비교한다.

9. Harness vs Memory

Memory 자체와 Memory Access를 구분한다.

Memory System
= 실제 Memory lifecycle

Harness
= Agent에게 Memory를 제공하고 사용하는 방법

후보:

Harness
 ↓
Memory Interface
 ↓
Memory System
10. Harness vs Capability

Capability를 Harness가 직접 소유하는지 검토한다.

후보:

Harness
 ↓
Capability Registry
 ↓
Tool / Skill / Workflow

또는 Capability System을 독립 subsystem으로 두고 Harness가 adapter 역할만 수행하는 구조를 비교한다.

11. Harness vs Security

Security enforcement는 Model에게 맡기지 않는다.

후보:

Agent
 ↓
Harness
 ↓
Policy
 ↓
Permission
 ↓
Sandbox

Harness가 Security enforcement의 일부를 담당할 가능성을 검토한다.

12. Harness vs Evaluation

Evaluation도 Harness의 일부로 볼 수 있다.

후보:

Harness
├── Execution
├── Observability
└── Evaluation

또는:

Harness
 ↓
Execution
 ↓
Evaluation System

둘을 비교한다.

13. Harness Responsibilities

현재 후보 책임:

1. Context orchestration
2. Capability exposure
3. Policy enforcement
4. Runtime coordination
5. State access
6. Memory access
7. Execution control
8. Observability
9. Verification
10. Recovery

모든 항목을 최종적으로 Harness가 소유한다는 의미는 아니다.

14. Harness Non-Responsibilities

Harness가 직접 소유하지 않는 것이 좋을 수 있는 것:

Identity Core
Core Values
Model Weights
Long-term Memory Storage
External Service implementation
Business-specific Tool Logic
User-owned Data

이 경계를 검토한다.

15. Harness as Execution Substrate

하나의 중요한 가설:

Harness는 Agent가 사고하는 공간이 아니라 Agent가 안정적으로 행동할 수 있는 substrate다.

개념적으로:

Agent
 ↓
Harness
 ├── Context
 ├── Tools
 ├── State
 ├── Memory
 ├── Policy
 ├── Runtime
 └── Evaluation
16. Harness and Long-Horizon Tasks

장기 작업에서 Harness가 담당할 후보:

Task State
Context Reset
Memory Retrieval
Checkpoint
Recovery
Tool State
Artifact State
Observability

즉 Agent가 하나의 Context Window에 모든 작업을 유지하지 않아도 계속 작업할 수 있게 한다.

17. Harness and Context Windows

Context Window가 증가하더라도 Harness의 역할이 사라지는 것은 아니다.

100K context
1M context
10M context
Future unknown

에서도:

Context Selection
State Management
Tool Execution
Recovery
Verification

는 여전히 필요할 수 있다.

18. Harness and State

현재 가설:

Harness
 ↓
State Access

하지만:

Harness owns State

와

State System is independent

를 비교해야 한다.

현재는 후자를 우선 검토한다.

19. Harness and Memory

Memory도 마찬가지.

Harness
 ↓
Memory Interface
 ↓
Memory

를 기본 후보로 둔다.

Harness가 특정 Vector DB나 Graph DB를 직접 알아서는 안 된다.

20. Harness and Capability Discovery

Agent가 사용할 수 있는 모든 Tool을 Context에 넣지 않고:

Task
 ↓
Harness
 ↓
Capability Discovery
 ↓
Relevant Capabilities
 ↓
Agent

를 검토한다.

21. Harness and Policy

Policy는 deterministic enforcement가 필요한 부분을 담당한다.

Agent Request
 ↓
Harness
 ↓
Policy
 ↓
Permission
 ↓
Execute

Prompt에만 Security를 의존하지 않는다.

22. Harness and Sandbox

Sandbox는 Harness가 관리할 수 있는 대표적인 execution boundary다.

Harness
 ↓
Sandbox
 ↓
Environment

하지만 Sandbox implementation 자체는 Harness의 교체 가능한 dependency로 둔다.

23. Harness and Observability

Harness는 모든 중요한 실행을 trace할 수 있어야 할 가능성이 높다.

Harness
 ↓
Trace
 ├── Context
 ├── Capability
 ├── Permission
 ├── Runtime
 ├── State
 └── Verification
24. Harness and Verification

Harness가 독립적인 Verification을 호출할 수 있다.

Agent
 ↓
Execute
 ↓
Harness
 ↓
Verifier
 ↓
State Commit

Agent self-report만으로 완료를 결정하지 않는다.

25. Harness and Recovery

Harness는:

Failure
 ↓
Checkpoint
 ↓
Recovery
 ↓
Resume

를 관리하는 역할을 가질 수 있다.

26. Harness and Agent Replacement

Agent Model 또는 Agent implementation이 바뀌더라도 Harness가 Task State / Memory / Capability / Policy를 유지할 수 있는 구조를 검토한다.

Agent A
 ↓
Harness
 ↓
Agent B

이 가능해야 한다.

27. Harness as Stable Boundary

미래 기술 변화에도:

Agent
 ↕
Harness Contract
 ↕
Infrastructure

를 유지할 수 있어야 한다.

Agent가:

Model A
Model B
Future Model

로 바뀌어도 Harness Contract를 유지한다.

28. Harness vs Framework

Framework와 Harness를 구분한다.

Framework
= implementation toolkit

Harness
= execution environment + contracts + controls

특정 Framework를 채택한다고 Harness가 자동으로 정의되는 것은 아니다.

29. OpenCode Reference

OpenCode의 Session Runner, Tool system, Context handling, Permission, Agent 구조에서 Harness에 가까운 여러 기능을 확인한다.

Research 질문:

어떤 기능이 Agent logic인가?
어떤 기능이 runtime substrate인가?
어떤 기능이 policy enforcement인가?
어떤 기능이 execution infrastructure인가?
30. Grok Build Reference

Grok Build의:

SessionRegistry
SessionActor
Run Loop
Turn
Tool
Permission
Sandbox / Pager

구조를 Harness boundary 관점에서 분석한다.

특히 Actor와 Runtime의 관계를 살펴본다.

31. OpenAI Agents SDK Reference

최신 Agents SDK의:

Agent
Harness
Sandbox
Tools
Skills
Memory
Approvals
Tracing
Handoffs

분리 방식을 연구한다.

특히:

Agent harness와 compute를 분리하는 이유

를 중심으로 분석한다.

32. Anthropic Reference

Long-running Agent와 Harness 관련 연구에서:

context management
compaction
subagents
persistent artifacts
evaluator
verification

이 어떤 계층에 위치하는지 분석한다.

33. Historical / Foundational References

오래된 아이디어도 비교한다.

Operating Systems

Process / runtime / resource isolation.

Actor Model

Message passing / isolation / lifecycle.

Workflow Engines

Durable state / long-running execution.

Distributed Systems

Failure recovery / consistency / checkpoint.

Middleware

Application과 infrastructure 사이의 stable abstraction.

Cognitive Architectures

Cognition과 supporting infrastructure의 분리.

34. Harness Evolution

Harness가 고정된 시스템일 필요는 없다.

초기:

Rule-based Harness

중간:

Adaptive Harness

장기:

Learning Harness

로 발전할 가능성을 검토한다.

35. Static vs Adaptive Harness
Static
Fixed policy
Fixed routing
Fixed context strategy
Adaptive
Task
 ↓
Context strategy selection
 ↓
Tool selection
 ↓
Execution strategy

장기적으로 Adaptive Harness를 연구한다.

36. Harness Learning

최근 Harness 연구에서는 Agent 실행 결과를 기반으로 Harness 자체를 개선하는 접근이 나타난다.

후보:

Execution
 ↓
Evaluation
 ↓
Harness Failure
 ↓
Improvement
 ↓
New Harness

NOAH에서는 이를 장기 목표로 고려한다.

37. Harness Self-Modification

하지만 Harness가 자기 자신을 직접 수정하는 것은 위험하다.

초기 원칙:

Harness
 ↓
Improvement Proposal
 ↓
Evaluation
 ↓
Governance
 ↓
Deploy

자동 무조건 업데이트를 허용하지 않는다.

38. Harness as Meta-System

장기적으로 Harness는 Agent를 운영하는 시스템이 될 수 있다.

Agent
 ↓
Harness
 ↓
Execution
 ↓
Evaluation
 ↓
Harness Improvement

이것이 NOAH Development System과 연결될 가능성을 검토한다.

39. Harness and NOAH Development System

NOAH를 만드는 시스템과 NOAH를 실행하는 Harness를 혼동하지 않는다.

NOAH Development System
= NOAH를 만드는 방법

NOAH Harness
= NOAH가 실행되는 방법

둘은 서로 영향을 받을 수 있지만 동일하지 않다.

40. Harness Boundary Candidates

후보 A:

Agent
↓
Harness
├── Runtime
├── Context
├── Capability
├── Security
└── Evaluation

후보 B:

Agent
↓
Harness
↓
Runtime

Context
Memory
Capability
Security
Evaluation

후보 C:

Agent
↓
Agent Runtime
       ├── Context
       ├── Tools
       ├── Memory
       └── Security

어떤 구조가 가장 유지보수성이 좋은지 검토한다.

41. Responsibility Matrix
Component	Candidate Responsibility
Agent	Reasoning / Decision
Harness	Execution coordination
Runtime	Execution lifecycle
Orchestrator	Strategy / Delegation
Context Manager	Context selection
Memory	Persistent experience
Capability	Actions
Policy	Authorization
Sandbox	Isolation
Verification	State validation
Evaluation	Quality measurement

이번 Research에서 이 표를 검증한다.

42. Stable vs Replaceable
Stable
Agent Contract
Harness Contract
Task Contract
Execution Contract
State Contract
Capability Contract
Verification Contract
Replaceable
Runtime Framework
Memory Backend
Sandbox
Model
Orchestrator
Telemetry
Database
43. Risks
Responsibility Explosion

Harness가 모든 것을 담당할 수 있다.

Harness Monolith

모든 subsystem이 Harness 하나에 결합될 수 있다.

Agent Over-Simplification

Agent가 단순 Model wrapper가 될 수 있다.

Runtime Duplication

Harness와 Runtime이 같은 일을 할 수 있다.

Orchestration Duplication

Harness와 Orchestrator의 책임이 겹칠 수 있다.

Performance Overhead

모든 실행이 너무 많은 abstraction layer를 통과할 수 있다.

44. Open Questions
Harness의 최소 책임은 무엇인가?
Harness와 Runtime의 정확한 경계는?
Harness와 Orchestrator는 어디에서 분리하는가?
Context Manager는 Harness의 내부인가?
Memory Interface는 Harness가 소유하는가?
Capability Registry는 Harness 내부인가?
Policy Engine은 Harness에 속하는가?
Evaluation이 Harness의 일부가 되어야 하는가?
Harness가 Task State를 직접 관리해야 하는가?
Harness는 State Store에 의존하는가?
Harness가 Sandbox lifecycle을 관리해야 하는가?
Harness가 Model을 직접 호출해야 하는가?
Harness는 Model-independent해야 하는가?
여러 Agent가 하나의 Harness를 공유할 수 있는가?
Agent마다 별도 Harness를 만들어야 하는가?
Harness는 persistent한 존재인가 ephemeral한 runtime인가?
Harness가 학습될 수 있는가?
Harness가 자기 자신을 수정할 수 있어야 하는가?
Harness와 NOAH Development System은 어떤 관계인가?
가장 작은 구현 가능한 Harness는 무엇인가?
45. Research Findings

각 Reference에서:

Reference
Problem
Harness-like Components
Boundary
Strengths
Weaknesses
Stable Principle
NOAH Relevance

형태로 기록한다.

46. Historical / Current / Emerging
Category	Example	Value
Historical	OS / Actor / Workflow	Stable execution principles
Current	OpenCode / OpenAI / Anthropic	Current implementation patterns
Emerging	Learned Harness / Adaptive Harness	Future possibility
47. Preliminary Hypothesis

현재까지의 정보로는:

Harness를 하나의 거대한 subsystem으로 만들기보다, Agent와 Infrastructure 사이의 stable execution contract로 보는 것이 유력하다.

즉:

Agent
 ↓
Harness Contract
 ↓
Runtime / Context / Capability / Security / Evaluation

형태를 우선 검토한다.

48. Another Hypothesis

Harness가 실제 구현에서는 여러 모듈로 구성될 수 있다는 점도 중요하다.

Logical Harness
├── Context
├── Capability
├── Runtime
├── Security
├── Observability
└── Recovery

하지만 이것들이 반드시 하나의 물리적 Package/Service일 필요는 없다.

49. Research Completion Criteria
☐ Agent vs Harness 정의
☐ Harness vs Runtime 정의
☐ Harness vs Orchestrator 정의
☐ Harness vs Context 정의
☐ Harness vs Memory 정의
☐ Harness vs Capability 정의
☐ Harness vs Security 정의
☐ Harness vs Evaluation 정의
☐ Stable Harness Contract 후보 정의
☐ Current / Historical / Emerging 비교
☐ 최소 Harness PoC 후보 정의
50. Next Step

이번 연구가 끝난 뒤:

Harness Boundary Research
        ↓
Findings
        ↓
Integration Review v0.2
        ↓
Memory / Knowledge Boundary Research
        ↓
Artifact Research
        ↓
DDR
        ↓
02-Architecture

로 진행한다.

51. Final Research Goal

이번 Research의 최종 목적:

"Agent가 바뀌어도 NOAH의 실행 환경과 핵심 시스템 계약이 유지될 수 있는가?"

를 확인하는 것이다.

52. Final Principle

현재 연구의 가장 중요한 후보 원칙:

Agent는 생각하고 결정한다. Harness는 Agent가 안전하고 지속적으로 행동할 수 있도록 실행 환경을 제공한다.

단, 여기서 Harness가 모든 것을 소유한다는 의미는 아니다.

Harness는 여러 독립적인 subsystem을 연결하는 stable execution boundary일 가능성이 높다.