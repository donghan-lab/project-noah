# Orchestration Contract Research

> Project NOAH Research
> Research 대상: Orchestration Contract / Delegation Contract / Agent Coordination
> Research Version: 0.1
> Priority: P1
> Status: Research

---

# 1. Research Purpose

Project NOAH에서 Task, Orchestrator, Agent, Capability, Context, Result, Verification이
서로 안정적으로 연결될 수 있도록 필요한 Contract를 연구한다.

핵심 질문:

> "Orchestrator와 Agent가 서로 무엇을 약속해야 안정적으로 협력할 수 있는가?"

본 문서는 최종 Orchestration Architecture를 결정하지 않는다.

---

# 2. Why This Research Matters

현재 Architecture Integration Review에서 다음 요소의 관계는 정의되어 있다.

Task
Orchestrator
Agent
Capability
Context
Runtime
Verification
Evaluation

그러나 실제 구현을 위해서는 이들 사이의 명시적인 Contract가 필요하다.

특히:

- Task를 어떻게 전달하는가?
- Agent에게 어떤 Context를 전달하는가?
- 권한을 어떻게 전달하는가?
- Agent가 어떤 결과를 반환해야 하는가?
- 실패를 어떻게 보고하는가?
- 취소를 어떻게 전파하는가?
- Budget을 어떻게 관리하는가?
- Verification을 어디에서 수행하는가?
- Subagent가 Parent Agent에게 무엇을 돌려줘야 하는가?

를 연구한다.

---

# 3. Current NOAH Hypothesis

현재 가설:

> Orchestration은 Agent 내부의 암묵적 기능이 아니라 명시적인 Contract를 통해 이루어져야 한다.

후보:

```text
Task Contract
Delegation Contract
Agent Contract
Context Contract
Capability Contract
Result Contract
Evidence Contract
Verification Contract
Budget Contract
Cancellation Contract
Recovery Contract
4. Contract Principles

모든 Contract는 다음 원칙을 만족하는 방향을 검토한다.

명확한 입력
명확한 출력
명확한 책임
명확한 실패
명확한 권한
versioning
observability
verification 가능성
5. Task Contract

Task를 Orchestrator 또는 Agent에게 전달하는 Contract.

후보:

Task
├── ID
├── Goal
├── Requirements
├── Constraints
├── Priority
├── Deadline
├── Budget
├── Completion Criteria
└── Verification Requirements
6. Task Contract Ownership

Task의 Source of Truth는 어디인가?

후보:

Task Store
Orchestrator
Session
User

현재 Task State / Runtime Research 결과와 연결하여 결정한다.

7. Task Status Contract

후보:

Created
Planned
Running
Blocked
Waiting
Paused
Completed
Failed
Cancelled

Status 변경 권한과 전이를 정의할 필요성을 검토한다.

8. Delegation Contract

Parent Agent가 Subagent에게 작업을 위임할 때의 Contract.

Delegation
├── Parent
├── Child
├── Goal
├── Context
├── Scope
├── Permissions
├── Budget
├── Constraints
├── Expected Output
└── Verification
9. Delegation Scope

Subagent가 어디까지 작업할 수 있는지 정의한다.

Scope
├── Task
├── Files
├── Network
├── Tools
├── Memory
├── Time
└── Resource
10. Delegation Permission

기본 원칙:

Child Permission
⊆
Parent Permission

추가 권한이 필요한 경우 explicit escalation을 요구한다.

11. Agent Contract

Agent가 Orchestrator 또는 다른 Agent에게 제공하는 기본 Contract.

후보:

Agent
├── ID
├── Role
├── Capabilities
├── Version
├── Status
├── Trust
├── Input Contract
└── Output Contract
12. Agent Capability Declaration

Agent가 무엇을 할 수 있는지 명시적으로 표현한다.

Capabilities
├── Research
├── Coding
├── Analysis
├── Review
└── Verification

실제 Capability와 Agent Role을 혼동하지 않는다.

13. Agent Availability

Orchestrator가 Agent 선택을 위해:

Available
Busy
Unavailable
Failed
Degraded

등의 상태를 확인할 수 있는 구조를 검토한다.

14. Context Contract

Agent에게 전달되는 Context의 구조를 정의한다.

후보:

Context
├── Goal
├── Constraints
├── Relevant State
├── Relevant Memory
├── Relevant Knowledge
├── Artifacts
├── Tool Information
└── Security Context

Full Context를 무조건 전달하지 않는다.

15. Context Projection

Parent Context:

Full Context

를 그대로 전달하지 않고:

Relevant Projection

만 전달하는 구조를 기본 후보로 둔다.

16. Context Trust

Context 내부 정보도 authority를 가진다.

System Policy
User Intent
Task State
Verified State
Memory
Knowledge
Tool Observation
External Content

Subagent에 전달할 때 source authority를 유지해야 한다.

17. Capability Contract

Agent가 사용할 Capability의 호출 Contract.

후보:

Capability
├── ID
├── Version
├── Input Schema
├── Output Schema
├── Permission
├── Side Effects
├── Cost
├── Timeout
└── Verification
18. Tool Call Contract

Tool 호출의 최소 구조:

Tool Call
├── Call ID
├── Capability
├── Input
├── Context
├── Permission
└── Timeout
19. Tool Result Contract
Tool Result
├── Call ID
├── Status
├── Output
├── Error
├── Evidence
├── Side Effects
└── Metadata

Full Tool Result과 Model-facing projection을 구분한다.

20. Result Contract

Subagent 또는 Workflow가 Parent에게 돌려주는 결과.

후보:

Result
├── Status
├── Summary
├── Findings
├── Evidence
├── Artifacts
├── Uncertainty
├── Errors
└── Recommended Next Step
21. Result vs Evidence

Result는 Agent가 무엇을 보고하는가.

Evidence는 실제로 그 결과를 뒷받침하는 증거다.

Result
+
Evidence

를 분리한다.

22. Evidence Contract

Evidence의 후보:

Evidence
├── Source
├── Artifact
├── Tool Result
├── Test
├── Observation
├── Timestamp
├── Version
└── Verification
23. Verification Contract

Task 또는 Result의 성공 여부를 검증한다.

Verification
├── Preconditions
├── Postconditions
├── Evidence
├── Invariants
└── Result
24. Verification Responsibility

누가 검증하는지 명시한다.

후보:

Agent
Parent Agent
Independent Verifier
Environment
Code-based Validator
Human
25. Independent Verification

High-risk 또는 High-impact Task에서는:

Executor
↓
Independent Verifier

구조를 사용할 수 있는지 검토한다.

26. Budget Contract

Orchestration이 무제한으로 자원을 사용하지 않도록:

Budget
├── Tokens
├── Time
├── Agents
├── Tool Calls
├── Compute
├── Storage
└── Network

을 정의한다.

27. Budget Propagation

Parent Task:

Budget = 100

Subagent:

Budget <= Parent Remaining Budget

원칙을 검토한다.

28. Cancellation Contract

사용자 또는 상위 Orchestrator가 Task를 취소할 수 있어야 한다.

Cancel Request
 ↓
Orchestrator
 ↓
Agent
 ↓
Runtime
 ↓
Tool / Execution

취소 전파가 어느 수준까지 필요한지 연구한다.

29. Pause / Resume Contract

Long-running Task에서는:

Pause
 ↓
Checkpoint
 ↓
Resume

이 필요할 수 있다.

Task State / Runtime Boundary Research와 연결한다.

30. Failure Contract

Failure를 단순 문자열로 전달하지 않는다.

후보:

Failure
├── Code
├── Category
├── Message
├── Recoverable
├── Retryable
├── Evidence
├── Partial Result
└── Recommended Action
31. Failure Categories

예:

Invalid Input
Permission Denied
Capability Failure
Timeout
Environment Failure
Verification Failure
Resource Exhaustion
Policy Violation
Agent Failure
External Service Failure
32. Retry Contract

Retry 가능한 경우:

Retryable
Max Attempts
Backoff
Idempotency

를 정의한다.

33. Recovery Contract

복구 방식:

Retry
Reassign
Fallback
Replan
Resume
Escalate
Abort

중 무엇을 선택할지 정의한다.

34. Artifact Contract

Agent 사이에 Artifact를 전달할 때:

Artifact
├── ID
├── Type
├── Version
├── URI / Reference
├── Hash
├── Provenance
└── Permissions

를 사용한다.

전체 Artifact를 Context에 직접 복사하지 않는다.

35. Memory Contract

Agent가 Memory를 사용하는 경우:

Memory Query
├── Scope
├── Task
├── Query
├── Relevance
└── Permission

결과:

Memory Result
├── Content
├── Source
├── Confidence
├── Timestamp
└── Provenance

형태를 검토한다.

36. Knowledge Contract

Knowledge Retrieval도 별도 semantics를 가진다.

Knowledge Query
├── Domain
├── Query
├── Source Requirements
└── Freshness Requirement
37. Security Contract

Orchestration 요청에:

Identity
Role
Scope
Permission
Risk
Approval

을 함께 전달할 수 있어야 한다.

38. Trust Contract

Agent 간 협력에서:

Identity
Trust
Provenance
Capability
Permission

을 확인할 수 있어야 한다.

39. Identity Contract

Orchestration에서 Agent Identity를 식별한다.

Agent ID
Parent ID
Role
Version
Trust

Identity Persistence Research와 연결한다.

40. Session Contract

Agent가 특정 Session에서 수행되는 경우:

Session ID
Task ID
Agent ID
State Reference
Context Reference

를 전달할 필요성을 검토한다.

41. Runtime Contract

Orchestrator가 Runtime에 요구하는 기능:

Start
Pause
Resume
Cancel
Retry
Checkpoint
Recover
Observe
42. Orchestrator Contract

Orchestrator 자체도 Contract를 가져야 한다.

Orchestrator
├── Task Input
├── Available Agents
├── Available Capabilities
├── Budget
├── Policy
└── Expected Result

Output:

Plan
Assignments
Dependencies
Budget Allocation
Verification Strategy
43. Plan Contract

Plan은:

Plan
├── ID
├── Version
├── Goals
├── Steps
├── Dependencies
├── Agents
├── Capabilities
├── Budget
├── Verification
└── Recovery

를 가질 수 있다.

44. DAG / Dependency Contract

복잡한 Task는:

A
├── B
└── C
     ↓
     D

처럼 dependency를 표현한다.

45. Parallel Execution Contract

병렬 작업에서는:

Parallel Group
├── Tasks
├── Shared Inputs
├── Independent Outputs
├── Synchronization
└── Aggregation

을 정의한다.

46. Aggregation Contract

여러 Agent의 결과를 합치는 Contract:

Aggregation
├── Inputs
├── Evidence
├── Conflicts
├── Ranking
├── Synthesis
└── Final Verification

다수결만으로 결론을 확정하지 않는다.

47. Conflict Contract

Conflict:

Agent A → X
Agent B → Y

이 발생하면:

Evidence
+
Source Authority
+
Goal
+
Verification

을 이용해 해결한다.

48. Uncertainty Contract

Agent가 불확실한 결과를 반환할 수 있어야 한다.

Uncertainty
├── Confidence
├── Unknowns
├── Assumptions
├── Alternatives
└── Evidence Gaps
49. Handoff Contract

Handoff에는:

Current Agent
Next Agent
Reason
Goal
Context Projection
State Reference
Permissions
Expected Output

이 포함될 수 있다.

50. Agent-as-Tool Contract

Agent-as-Tool 패턴에서는:

Parent Agent
 ↓
Child Agent
 ↓
Result
 ↓
Parent Agent

이며 Child는 parent control을 가져가지 않는다.

51. Shared State Contract

여러 Agent가 동일한 Task State를 볼 경우:

Read
Write
Version
Lock / Optimistic Concurrency

등을 정의한다.

52. Concurrency Contract

동시 변경 시:

Version
Revision
Conflict
Merge

을 처리한다.

53. Idempotency Contract

재시도 가능한 행동인지 표현한다.

Idempotent
Non-idempotent
Unknown
54. Timeout Contract
Timeout
├── Connect
├── Execution
├── Tool
├── Agent
└── Overall Task

각 레벨을 구분한다.

55. Deadline Contract

Task 전체와 Subtask에:

Deadline
Remaining Time

를 전달할 수 있다.

56. Cost Contract

각 Agent / Capability에 예상 비용을 기록한다.

Estimated Cost
Actual Cost
Remaining Budget
57. Observability Contract

모든 Orchestration 단계에서:

Trace ID
Span ID
Task ID
Agent ID
Capability ID

를 전달하는 것을 검토한다.

58. Audit Contract

중요한 결정:

Delegation
Permission
Approval
Plan
Execution
Verification

을 Audit할 수 있어야 한다.

59. Versioning

Contract 자체도 버전을 가져야 한다.

Task Contract v1
Agent Contract v1
Result Contract v1

하위 호환성 정책을 검토한다.

60. Compatibility

Agent A:

Contract v1

Agent B:

Contract v2

일 때:

Adapter
Negotiation
Fallback

등을 사용할 수 있는지 검토한다.

61. Protocol Mapping

Contract가:

Internal
MCP
A2A
HTTP
Message Queue

등 여러 Protocol로 표현될 수 있는지 검토한다.

Protocol과 Contract를 동일시하지 않는다.

62. Contract vs Protocol
Contract
= 무엇을 약속하는가

Protocol
= 그 약속을 어떻게 전달하는가
63. Contract vs Schema

Schema는 구조를 설명한다.

Contract는:

Schema
+
Semantics
+
Permissions
+
Lifecycle
+
Failure
+
Verification

까지 포함할 수 있다.

64. Contract Governance

중요 Contract 변경:

Proposal
 ↓
Review
 ↓
Compatibility Check
 ↓
Version
 ↓
Migration

을 거친다.

65. Contract Testing

각 Contract를 독립적으로 테스트한다.

Producer
↔
Contract
↔
Consumer
66. Contract Evaluation

Contract 품질을:

Clarity
Completeness
Compatibility
Observability
Recoverability
Security

등으로 평가한다.

67. Historical / Foundational Ideas

참고 대상:

RPC
Message Passing
Actor Model
Workflow contracts
Distributed transactions
API design
Type systems
Interface contracts
Capability-based security
68. Current Frontier

참고 대상:

MCP
A2A
Agent handoff
Tool contracts
Agent harnesses
Durable execution
Multi-agent orchestration
Structured agent communication
69. Emerging Directions
Agent-to-Agent Protocol evolution
Learned orchestration
Contract-aware routing
Dynamic schema negotiation
Self-describing capabilities
Adaptive delegation policies
70. Candidate Contract Stack
                 Task Contract
                      │
                 Plan Contract
                      │
              Delegation Contract
                      │
                Agent Contract
                      │
               Context Contract
                      │
             Capability Contract
                      │
               Security Contract
                      │
              Execution Contract
                      │
              Result Contract
                      │
             Verification Contract
                      │
             Evaluation Contract
71. Candidate End-to-End Flow
User
 ↓
Task Contract
 ↓
Orchestrator
 ↓
Plan Contract
 ↓
Delegation Contract
 ↓
Agent
 ↓
Context Contract
 ↓
Capability
 ↓
Security
 ↓
Runtime
 ↓
Execution
 ↓
Result
 ↓
Evidence
 ↓
Verification
 ↓
Evaluation
72. Candidate Delegation Example
Task:
"Analyze Project Architecture"

Parent Agent
 ↓
Delegation Contract
 ↓
Research Agent

Research Agent
 ↓
Context Projection
 ↓
Read Artifacts
 ↓
Result Contract
 ↓
Evidence

Parent Agent
 ↓
Aggregation
 ↓
Verification
73. Candidate Parallel Example
Task
 ↓
Parallel Group
 ├── Research Agent
 ├── Security Agent
 └── Implementation Agent
        ↓
    Aggregator
        ↓
   Verification

각 Worker에는 독립적인 Context와 필요한 Scope만 전달한다.

74. Candidate Recovery Example
Parent Agent
 ↓
Child Agent
 ↓
Failure
 ↓
Failure Contract
 ↓
Recovery Policy
 ↓
Retry / Reassign
 ↓
Continue
75. Stable vs Replaceable
Stable
Task Contract
Agent Contract
Delegation Contract
Context Contract
Result Contract
Evidence Contract
Verification Contract
Budget Contract
Recovery Contract
Replaceable
Protocol
Transport
Message Bus
Orchestrator Implementation
Agent Framework
Runtime Framework
76. Risks
Contract Explosion

Contract가 지나치게 많아질 수 있다.

Over-specification

초기에 불필요하게 상세한 Contract를 고정할 수 있다.

Versioning Complexity

Contract Version이 많아질 수 있다.

Compatibility Burden

오래된 Agent를 계속 지원해야 할 수 있다.

Performance Overhead

모든 요청에 metadata가 지나치게 많이 붙을 수 있다.

77. Open Questions
Contract의 최소 공통 필드는 무엇인가?
Task Contract와 Task State Contract를 분리해야 하는가?
Agent Contract는 Capability Contract와 어떻게 연결되는가?
Delegation Contract와 Handoff Contract의 차이는?
Result와 Evidence는 얼마나 분리해야 하는가?
Verification Contract는 누구의 책임인가?
Budget을 Contract의 일부로 볼 것인가?
Protocol이 Contract를 완전히 표현할 수 있는가?
Contract Versioning은 어떻게 관리하는가?
Dynamic Negotiation이 필요한가?
Agent가 Contract를 스스로 생성할 수 있는가?
Contract 위반을 어떻게 감지하는가?
Contract 위반은 Runtime Failure인가 Policy Failure인가?
Contract 변경은 Governance가 필요한가?
Multi-Agent 환경에서 공통 Contract Registry가 필요한가?
78. Research Findings

각 Reference:

Reference
Contract Type
Input
Output
Failure
Versioning
Security
Verification
NOAH Relevance
Stable Principle

을 기록한다.

79. Preliminary Recommendation

현재 가설:

NOAH는 Agent 간 통신 Protocol보다 상위에 존재하는 명시적인 Contract Layer를 가져야 한다.

즉:

Contract
 ↓
Protocol Adapter
 ↓
Transport

구조를 우선 검토한다.

80. Future Resilience

미래의 통신 방식이:

MCP
A2A
HTTP
Message Bus
Future Protocol

로 바뀌어도 Contract는 유지될 수 있어야 한다.

81. Research Completion Criteria
☐ Task Contract 정의
☐ Agent Contract 정의
☐ Delegation Contract 정의
☐ Context Contract 정의
☐ Capability Contract 관계 정의
☐ Result Contract 정의
☐ Evidence Contract 정의
☐ Verification Contract 정의
☐ Budget Contract 정의
☐ Cancellation / Recovery Contract 정의
☐ Versioning 정의
☐ Compatibility 정의
☐ Protocol과 Contract 분리
☐ 최소 Contract Stack 정의
82. Next Step
Orchestration Contract Research
        ↓
Findings
        ↓
Architecture Integration Review v0.3
        ↓
DDR
        ↓
02-Architecture
        ↓
Integrated Orchestration PoC
83. Final Research Goal

"NOAH의 Agent와 실행 시스템이 서로 다른 구현으로 바뀌더라도 안정적으로 협력할 수 있는 최소한의 공통 언어를 정의할 수 있는가?"

84. Final Principle

Contract는 구현을 고정하기 위한 것이 아니라, 서로 다른 구현이 안전하게 협력할 수 있도록 경계를 고정하기 위한 것이다.