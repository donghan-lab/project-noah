Architecture Review — Orchestration & Multi-Agent v0.1

Project NOAH Architecture Review
Review 대상: Orchestration / Multi-Agent / Delegation / Coordination Architecture
Review Version: 0.1
Status: Review

1. Review Purpose

Project NOAH에서 하나의 Agent를 넘어 여러 Agent, Subagent, Capability 및 Workflow가 협력해야 하는 경우 이를 어떻게 조정할 것인지 Architecture를 검토한다.

본 Review의 핵심 질문은 다음과 같다.

"NOAH는 언제 혼자 행동하고, 언제 다른 Agent에게 위임하며, 언제 병렬화하고, 언제 결과를 다시 하나로 통합해야 하는가?"

그리고 다음을 함께 검토한다.

Single Agent와 Multi-Agent의 경계는 무엇인가?
Subagent와 Agent는 어떻게 다른가?
Handoff와 Agent-as-Tool은 어떻게 다른가?
Planner / Executor / Verifier 구조가 필요한가?
Agent를 언제 병렬 실행할 것인가?
공유 Context와 격리 Context를 언제 사용할 것인가?
Memory를 Agent 간에 공유해야 하는가?
Agent 간 결과를 어떻게 합칠 것인가?
실패한 Agent를 어떻게 교체·재실행할 것인가?
Coordination 비용은 어떻게 제한할 것인가?
Multi-Agent가 Single Agent보다 실제로 나은지 어떻게 검증할 것인가?

본 문서는 최종 Multi-Agent Architecture가 아니며, NOAH의 Orchestration 경계를 검토하기 위한 v0.1 문서다.

2. Core Architecture Question
Orchestration이란 무엇인가?

초기 정의:

Orchestration은 하나 이상의 Agent와 Capability를 목표 달성을 위해 선택하고, 배치하고, 연결하고, 실행하고, 검증하고, 결과를 통합하는 시스템 계층이다.

개념적으로:

Goal
 ↓
Decomposition
 ↓
Agent / Capability Selection
 ↓
Execution Plan
 ↓
Delegation / Parallelism
 ↓
Aggregation
 ↓
Verification
 ↓
Final Result

Orchestration은 Agent 자체와 분리된 계층으로 두는 방향을 검토한다.

3. Multi-Agent가 항상 필요한가?

현재 가장 중요한 원칙:

Multi-Agent는 기본값이 아니라 하나의 최적화 수단이다.

최근 연구에서는 Multi-Agent의 성능 이점이 문제 구조와 verification 방식에 따라 달라지며, 단순히 Agent 수를 늘리는 것이 항상 유리하지 않다는 결과가 반복적으로 나타난다. MAS-Orchestra는 Multi-Agent 이점이 task structure, verification, orchestrator/subagent capabilities에 의존한다고 보고하며, OrchBench는 병렬성 증가가 coordination failure 때문에 효율이 감소할 수 있음을 보여준다.

따라서 NOAH는:

Single Agent
    ↓
Need detected
    ↓
Subagent
    ↓
Parallel / Multi-Agent

처럼 필요에 따라 복잡도를 증가시키는 구조를 우선 검토한다.

4. Single Agent First

Single Agent를 기본 실행 단위로 둔다.

장점:

단순성
낮은 orchestration overhead
Context 관리 용이
상태 공유 용이
디버깅 용이
비용 감소
실패 원인 추적 용이

따라서 일반적인 작업은 Single Agent로 먼저 수행한다.

5. When Multi-Agent Is Worthwhile

Multi-Agent를 사용할 후보 상황:

Parallelizable Tasks
Independent Expertise
Context Isolation
Large Search Space
Different Capability Requirements
Fault Isolation
Independent Verification

예:

Research Topic
├── Agent A: Literature
├── Agent B: Implementation
├── Agent C: Counterargument
└── Agent D: Verification

단순히 역할을 나누는 것만으로 Multi-Agent의 필요성이 생기는 것은 아니다.

6. Multi-Agent Decision Problem

Orchestrator는:

"몇 개의 Agent를 사용하는 것이 가장 좋은가?"

를 판단할 수 있어야 한다.

후보 입력:

Task Complexity
Task Decomposability
Parallelism
Context Size
Expertise Diversity
Latency Budget
Cost Budget
Risk
Verification Requirement

출력:

Single Agent
Subagent
Sequential Multi-Agent
Parallel Multi-Agent
Hybrid
7. Orchestration Patterns

주요 패턴:

1. Single Agent
2. Sequential Pipeline
3. Handoff
4. Parallel Fan-out / Fan-in
5. Planner / Executor
6. Hierarchical
7. Peer-to-Peer
8. Agent-as-Tool
9. Supervisor
10. Debate / Critique

모든 패턴을 기본 구현하지 않는다.

8. Single Agent
User
 ↓
Agent
 ↓
Tools
 ↓
Result

가장 단순한 구조.

기본값으로 유지한다.

9. Sequential Pipeline
Agent A
 ↓
Agent B
 ↓
Agent C
 ↓
Result

앞 단계의 결과가 다음 단계의 입력이 되는 경우 적합하다.

예:

Research
 ↓
Analysis
 ↓
Writing
 ↓
Review

단점:

latency 증가
하나의 failure가 전체 pipeline을 막을 수 있음
context transfer 비용
10. Handoff

Handoff는 현재 Agent의 control을 다른 Agent에게 넘기는 방식이다.

Agent A
 ↓
Handoff
 ↓
Agent B

OpenAI는 handoff를 workflow execution을 다른 Agent로 이전하는 primitive로 제공하며, 최신 Agents SDK에서도 orchestration의 핵심 방식 중 하나로 다룬다.

Handoff는:

명확한 ownership transfer
사용자와 직접 상호작용할 다음 Agent 변경
전문 분야 routing

에 적합하다.

11. Handoff vs Agent-as-Tool

두 패턴을 구분한다.

Handoff
Agent A
 ↓
Agent B

Control이 이동한다.

Agent-as-Tool
Agent A
 ↓
Agent B
 ↓
Result
 ↓
Agent A

Parent Agent가 계속 control을 가진다.

OpenAI 역시 handoff와 agent-as-tool을 서로 다른 orchestration 패턴으로 설명한다.

NOAH에서는 두 패턴을 모두 지원할 필요가 있는지 검토한다.

12. Agent-as-Tool

Agent를 하나의 Capability처럼 사용할 수 있다.

예:

Main Agent
    ↓
Research Agent
    ↓
Research Result
    ↓
Main Agent

장점:

Parent control 유지
Result aggregation 용이
Specialist 격리

단점:

추가 latency
Context transfer
비용 증가
13. Parallel Fan-out / Fan-in

독립적인 작업은 병렬 처리할 수 있다.

              ┌→ Agent A ─┐
Task ─────────┼→ Agent B ─┼→ Aggregator
              └→ Agent C ─┘

적합한 경우:

독립적인 연구
여러 source 탐색
독립적인 검증
병렬 테스트

하지만 OrchBench는 병렬성을 단순히 높이면 coordination failure가 증가할 수 있으며, task-critical information 보존이 Agent 수 증가보다 중요할 수 있음을 보여준다.

14. Sequential vs Parallel

의사결정 후보:

Independent
→ Parallel

Dependent
→ Sequential

Mixed
→ Hybrid

예:

Requirements
 ↓
┌──────────┬──────────┐
│          │          │
Research  Prototype  Risk
│          │          │
└──────────┴──────────┘
          ↓
       Synthesis
15. DAG-based Orchestration

복잡한 Task는 Directed Acyclic Graph 형태로 표현할 수 있다.

         Root
        /    \
       A      B
      / \      \
     C   D      E
      \ /      /
       \      /
        Final

각 Node는:

Agent
Skill
Tool
Verification

중 하나가 될 수 있다.

최신 OrchBench 역시 orchestration plan을 task dependency DAG로 모델링하여 분석한다.

16. Planner / Executor

Planner가 전체 계획을 만들고 Executor가 수행한다.

Goal
 ↓
Planner
 ↓
Plan
 ↓
Executor
 ↓
Result
 ↓
Verifier

장점:

계획과 실행 분리
장기 Task에 적합
계획 변경 가능

단점:

계획 오류
stale plan
Planner overhead
17. Planner / Executor / Verifier

보다 강한 구조:

Planner
   ↓
Executor
   ↓
Verifier
   ↓
Success / Replan

Verifier가 실패하면:

Verifier
 ↓
Failure
 ↓
Planner
 ↓
Replan

으로 돌아간다.

18. Supervisor Pattern

Supervisor가 하위 Agent를 관리한다.

              Supervisor
             /     |     \
            A      B      C

Supervisor 책임:

task decomposition
delegation
scheduling
aggregation
recovery

장점:

중앙 통제
설명 용이
policy 적용 용이

단점:

Supervisor bottleneck
single point of failure
context overload
19. Hierarchical Multi-Agent

대규모 시스템에서는:

Global Supervisor
      ↓
Domain Supervisor
      ↓
Specialist Agent
      ↓
Tool

같은 계층 구조가 가능하다.

그러나 계층이 깊어질수록:

latency
cost
failure propagation
coordination complexity

가 증가한다.

따라서 깊은 hierarchy를 기본값으로 두지 않는다.

20. Peer-to-Peer

Agent끼리 직접 통신한다.

A ↔ B ↔ C

장점:

중앙 병목 감소
유연한 협력

단점:

coordination complexity
상태 추적 어려움
permission propagation 어려움
debugging 어려움

NOAH 초기 Architecture에서는 기본값으로 두지 않는다.

21. Debate / Critique

여러 Agent가 서로 검토할 수 있다.

Agent A
  ↓
Proposal
  ↓
Agent B
  ↓
Critique
  ↓
Agent A / Judge

적합한 경우:

high-risk decision
research
architecture
verification
adversarial checking

비용과 latency가 높기 때문에 필요한 경우에만 사용한다.

22. Specialist Agents

Connect AI의 Specialist 구조를 참고할 수 있다.

Researcher
Developer
Designer
Writer
Reviewer

하지만 Specialist는 반드시 별도의 독립 Agent일 필요는 없다.

대안:

One Agent
+
Different Skills / Roles

를 비교해야 한다.

23. Agent vs Skill for Specialization

예:

Research task

를 해결하는 방법:

Option A

Research Skill

Agent
 ↓
Research Skill
Option B

Research Agent

Agent
 ↓
Research Agent
판단 기준:
Need persistent identity?
Need separate context?
Need separate permissions?
Need independent runtime?
Need parallel execution?
Need independent evaluation?

이 기준으로 Agent / Skill을 선택한다.

24. Context Isolation

Subagent에게 모든 Parent Context를 전달하지 않는다.

Parent Context
     ↓
Relevant Projection
     ↓
Subagent Context

이는:

token cost
privacy
prompt injection
distraction

을 줄인다.

25. Shared Context

필요한 경우 일부 Context를 공유한다.

Shared Context
├── Task Goal
├── Constraints
└── Shared State Reference

하지만 Full Context Sharing은 기본값으로 두지 않는다.

26. Shared Memory

Multi-Agent 환경에서 Memory를 공유할 수 있다.

Agent A
   ↘
    Shared Memory
   ↗
Agent B

장점:

경험 공유
협력
중복 감소

위험:

Memory poisoning
정보 leakage
conflicting beliefs
attribution loss

따라서 explicit scope와 policy가 필요하다.

27. Isolated Memory

각 Agent가 독립 Memory를 가진다.

Agent A → Memory A
Agent B → Memory B

적합:

sensitive tasks
independent research
competing hypotheses
security boundaries
28. Delegation Contract

Agent 간 위임에도 명시적인 계약이 필요하다.

Delegation Request
├── Parent
├── Child
├── Goal
├── Scope
├── Inputs
├── Constraints
├── Permissions
├── Budget
├── Expected Output
└── Verification
29. Permission Inheritance

Subagent가 Parent보다 더 많은 권한을 가져서는 안 된다.

초기 원칙:

Child Permission
⊆
Parent Permission

필요한 추가 권한은 explicit escalation을 거쳐야 한다.

Permission & Security Review와 직접 연결된다.

30. Resource Budget

Multi-Agent 시스템에는 Budget이 필요하다.

Budget
├── Agents
├── Tokens
├── Time
├── Tool Calls
├── Compute
├── Storage
└── Network

예:

Task Budget
Max Agents = 4
Max Time = 10 min
Max Tokens = X
31. Cost-aware Orchestration

Orchestrator는:

이 작업을 Agent 4개로 처리할 가치가 있는가?

를 판단해야 한다.

후보 기준:

Expected Utility
vs
Coordination Cost
32. Coordination Cost

Multi-Agent의 비용:

Communication
Context Transfer
Synchronization
Aggregation
Duplicate Work
Verification
Failure Recovery

를 포함한다.

따라서:

More Agents
≠
Better Performance

를 명시적인 원칙으로 둔다.

33. Information Transfer

Agent 간 통신에서 중요한 것은 무엇을 넘길 것인가다.

Full Context
vs
Relevant Projection
vs
Structured Summary
vs
Artifacts / References

최근 OrchBench는 단순 Agent 수보다 task-critical information retention이 중요할 수 있다고 보고한다.

NOAH는 Full Context 복사를 기본값으로 두지 않는다.

34. Structured Handoff

Agent 간 결과를 자연어 전체로 전달하는 대신 구조화된 계약을 사용하는 것을 검토한다.

Handoff Result
├── Summary
├── Findings
├── Evidence
├── Artifacts
├── Uncertainties
├── Open Questions
└── Recommended Next Step

이는 정보 손실을 줄일 수 있다.

35. Agent Communication

Agent 간 통신은:

Message
Artifact
Shared State Reference
Tool Result
Event

등으로 표현할 수 있다.

가능하면 큰 Context를 직접 복사하기보다 reference를 전달하는 방향을 검토한다.

36. Protocols

Multi-Agent 환경에서는 Protocol이 중요하다.

후보:

MCP
ACP
A2A
HTTP
Message Queue

MCP는 Tool / Context access를 위한 계층으로, A2A 계열 프로토콜은 Agent 간 discovery / communication / delegation을 위한 계층으로 볼 수 있다. 2026년 orchestration 연구 역시 MCP와 Agent2Agent를 서로 보완적인 interoperability substrate로 설명한다.

NOAH는 특정 protocol 하나에 종속되지 않는 Adapter Layer를 검토한다.

37. A2A / Agent-to-Agent Communication

Agent 간 직접 통신이 필요하다면:

Agent A
 ↓
Agent Protocol
 ↓
Agent B

를 사용할 수 있다.

검토 항목:

Identity
Discovery
Authentication
Delegation
Capability
State
Result
Trust
38. Agent Discovery

Multi-Agent가 커질수록:

어떤 Agent가 이 일을 가장 잘 할 수 있는가?

를 선택해야 한다.

후보 Metadata:

Agent
├── Role
├── Capability
├── Cost
├── Availability
├── Trust
├── Context Requirements
├── Performance
└── Version
39. Dynamic Routing

Agent 선택은 고정 mapping만 사용할 필요가 없다.

Task
 ↓
Candidate Agents
 ↓
Capability / Cost / Trust
 ↓
Router
 ↓
Selected Agent

장기적으로 model-aware / capability-aware / cost-aware routing을 검토한다.

40. Static vs Dynamic Orchestration
Static

개발자가 Workflow를 명시한다.

A → B → C

장점:

예측 가능
디버깅 용이
Dynamic

Agent / Orchestrator가 실행 중 계획을 결정한다.

Task
 ↓
Planner
 ↓
Dynamic Plan

장점:

유연성
새로운 상황 대응

단점:

비결정성
평가 어려움
비용 증가

NOAH는 Hybrid를 우선 검토한다.

41. Deterministic Backbone

중요한 작업에서는 Orchestrator의 핵심 구조를 deterministic하게 유지하고 Agent에게 필요한 판단만 맡기는 방식을 검토한다.

예:

Deterministic Workflow
        +
Agent Decision Nodes

이 방식은 완전한 autonomous orchestration보다 debugging과 evaluation이 쉬울 수 있다.

42. Adaptive Orchestration

장기적으로는 Orchestrator가 경험을 통해 더 나은 분해/위임 전략을 배울 수 있다.

Execution
 ↓
Evaluation
 ↓
Orchestration Outcome
 ↓
Experience
 ↓
Routing Improvement

현재 구현 대상은 아니며 Research Further로 둔다.

43. Orchestration Memory

Orchestrator도 과거 경험을 활용할 수 있다.

예:

Task Type
 ↓
Previous Successful Plan
 ↓
Candidate Plan

다만 이 Memory가 오래되거나 잘못되면 잘못된 routing을 반복할 수 있다.

44. Orchestration State

Orchestration 자체에도 State가 필요하다.

Orchestration State
├── Goal
├── Plan
├── Active Agents
├── Dependencies
├── Completed Work
├── Pending Work
├── Failures
└── Budget

이는 Session / Task State와 연결되지만 동일하지 않을 수 있다.

45. Failure Handling

Agent 하나가 실패해도 전체 Task를 반드시 실패시키지는 않는다.

Agent A
 ↓
Failure
 ↓
Retry?
Reassign?
Skip?
Escalate?

정책:

Retry
Reassign
Fallback
Escalate
Abort

를 검토한다.

46. Agent Replacement

Agent가:

timeout
unavailable
repeated failure
low confidence

이면 다른 Agent로 교체할 수 있다.

Agent A
 ↓
Failure
 ↓
Agent B
 ↓
Continue

그러나 Context / State continuity가 보장되어야 한다.

47. Result Aggregation

여러 Agent 결과를 하나로 합치는 과정이 필요하다.

Agent A ─┐
Agent B ─┼→ Aggregator
Agent C ─┘

Aggregator는:

duplicate removal
conflict detection
evidence ranking
synthesis
uncertainty handling

을 수행한다.

48. Conflict Resolution

Agent A:

Option A가 좋다.

Agent B:

Option B가 좋다.

이 경우:

Conflict
 ↓
Evidence Comparison
 ↓
Policy / Goal
 ↓
Verification
 ↓
Resolution

을 검토한다.

다수결만으로 결정하지 않는다.

49. Evidence Aggregation

Agent 결과 자체보다 Evidence를 통합하는 것을 우선한다.

Agent Output
     ↓
Evidence
     ↓
Aggregator
     ↓
Verified Synthesis

이는 Hallucination propagation을 줄이는 데 도움이 될 수 있다.

50. Uncertainty Propagation

Agent가 불확실한 결과를 반환하면 그 uncertainty를 잃지 않는다.

Agent A
Confidence = 0.6

Aggregator
→ Combined Confidence

단순히:

"Agent A가 말했다."

를 확정 사실로 승격하지 않는다.

51. Parallel Verification

여러 Agent가 서로를 검증할 수 있다.

Primary Agent
 ↓
Result
 ↓
Verifier A
Verifier B
 ↓
Consensus / Evidence

고위험 Task에서만 사용한다.

52. Debate

Agent 간 의견 충돌을 의도적으로 유도할 수 있다.

Proposal Agent
      ↓
Critic Agent
      ↓
Revision
      ↓
Verifier

적합:

Architecture
Research
Strategic Decision

비적합:

단순 파일 읽기
간단한 작업
53. Independent Paths

같은 답을 여러 독립 경로에서 얻는다.

Path A
Path B
Path C
 ↓
Compare

이 방식은:

hallucination detection
critical reasoning
high-risk decisions

에 사용할 수 있다.

비용이 크기 때문에 선택적으로 사용한다.

54. Orchestration and Verification

Orchestrator가 Task를 분해할 때부터 Verification을 포함한다.

Task
 ↓
Plan
 ↓
Task A
 └── Verify A

Task B
 └── Verify B

Task C
 └── Verify C
 ↓
Final Verification

Verification을 마지막에 한 번만 하는 것보다 중간 failure를 빨리 발견할 수 있다.

55. Orchestration and Evaluation

Orchestration 자체도 평가한다.

Plan Quality
Parallelism
Information Transfer
Agent Selection
Cost
Latency
Recovery
Final Quality

최근 OrchBench는 orchestration plan 자체를 worker execution과 분리해 평가하는 방법을 제안한다. 이는 NOAH에서도 중요한 Research 방향이다.

56. Orchestration Benchmarking

후보 평가 기준:

Orchestration Quality
├── Task Success
├── Plan Quality
├── Agent Selection
├── Information Retention
├── Coordination Cost
├── Makespan
├── Token Cost
├── Recovery
└── Robustness

ETOM 역시 MCP 환경에서 단일 Tool뿐 아니라 cross-server multi-hop orchestration을 평가하며, 단순 기능 테스트만으로는 실제 orchestration을 충분히 평가하기 어렵다고 보고한다.

57. Multi-Agent Efficiency

Multi-Agent의 이점은:

Quality Gain
+
Parallel Speedup
+
Specialization

가:

Coordination Cost
+
Token Cost
+
Latency
+
Failure Risk

보다 클 때 의미가 있다.

58. Utility Model

후보:

Multi-Agent Utility
=
Expected Quality Gain
+
Expected Parallel Gain
+
Specialization Gain
-
Coordination Cost
-
Communication Cost
-
Verification Cost
-
Failure Risk

정량식은 향후 PoC에서 검증한다.

59. Agent Count

Agent 수가 많아질수록 항상 좋은 것은 아니다.

1 Agent
→ low coordination

2–4 Agents
→ possible specialization / parallelism

Many Agents
→ coordination complexity

최적 Agent 수는 Task-dependent하게 둔다.

60. Hierarchy Depth

Hierarchy가 깊어지면:

A
 ↓
B
 ↓
C
 ↓
D

각 단계에서:

context transfer
latency
failure propagation

이 증가한다.

따라서 깊은 hierarchy는 특별한 이유가 있을 때만 사용한다.

61. Multi-Agent Security

Multi-Agent가 되면 Security boundary가 증가한다.

위험:

Agent A
 ↓
Malicious / compromised Agent B
 ↓
Capability escalation

따라서:

Child Permission
⊆
Parent Permission

원칙을 적용한다.

62. Multi-Agent Memory Security

공유 Memory가 필요할 경우:

Agent A
 ↓
Shared Memory
 ↓
Agent B

사이에서:

scope
source
trust
access policy

를 확인한다.

63. Agent Identity

각 Agent는 명확한 Identity를 가져야 한다.

Agent
├── ID
├── Role
├── Version
├── Provider
├── Trust
└── Capabilities

그래야 Audit과 Permission이 가능하다.

64. Temporary Agents

모든 Agent가 영구적인 존재일 필요는 없다.

Task
 ↓
Spawn Temporary Agent
 ↓
Execute
 ↓
Destroy / Archive

Temporary Agent는:

isolated context
limited memory
limited permissions

을 가질 수 있다.

65. Persistent Specialists

반대로 일부 Specialist는 지속적인 Identity를 가질 수 있다.

예:

NOAH
├── Research Specialist
├── Development Specialist
└── Memory Specialist

이 경우:

Identity
Memory
Skill evolution

이 중요해진다.

66. Persistent vs Ephemeral Agent

두 종류를 모두 지원할 필요성을 검토한다.

Ephemeral
= Task-oriented worker

Persistent
= Long-lived specialist

NOAH에서는 초기 기본값을 Ephemeral에 두고 Persistent Specialist는 필요할 때 도입하는 방식을 검토한다.

67. Agent Lifecycle
Discover
 ↓
Select
 ↓
Spawn / Activate
 ↓
Execute
 ↓
Verify
 ↓
Complete
 ↓
Persist / Destroy

Persistent Agent:

Complete
 ↓
Idle
 ↓
Reuse
68. Orchestration Lifecycle
Task Received
 ↓
Analyze
 ↓
Choose Strategy
 ↓
Decompose
 ↓
Allocate
 ↓
Execute
 ↓
Monitor
 ↓
Aggregate
 ↓
Verify
 ↓
Complete / Replan
69. Replanning

Execution 중 상황이 바뀌면 Plan을 수정할 수 있어야 한다.

Plan
 ↓
Execute
 ↓
Observation
 ↓
Plan no longer valid
 ↓
Replan
 ↓
Continue

하지만 너무 자주 Replan하면 비용이 증가한다.

70. Replanning Triggers

후보:

Unexpected Failure
New Information
Environment Change
Budget Change
Agent Unavailability
Verification Failure
Goal Change
71. Orchestration Budget

Orchestrator에도 예산이 필요하다.

Max Agents
Max Depth
Max Parallelism
Max Tool Calls
Max Tokens
Max Time
Max Cost

Budget을 초과하면:

Stop
Degrade
Fallback
Ask User

중 하나를 선택한다.

72. Graceful Degradation

Multi-Agent가 실패하면 Single Agent로 축소할 수 있는 구조를 검토한다.

Multi-Agent
 ↓
Agent unavailable
 ↓
Single Agent fallback

모든 Task가 반드시 Multi-Agent에 의존해서는 안 된다.

73. User Control

사용자가 orchestration에 개입할 수 있어야 한다.

예:

"이 작업은 다른 Agent를 사용해도 돼."

"외부 Agent는 사용하지 마."

"병렬 실행하지 마."

"Research Agent를 추가해."

User intent가 orchestration policy보다 우선하는 범위를 명시해야 한다.

74. Explainable Orchestration

NOAH는 중요한 경우:

"왜 이 Agent를 선택했는가?"

를 설명할 수 있어야 한다.

Evidence:

Task Requirements
Capability Match
Trust
Cost
Availability
Previous Performance
75. Orchestration Memory

과거 성공/실패에서:

Task Type
→ Successful Strategy

를 학습할 수 있다.

예:

"Literature review"
→ 3-agent parallel research + verifier

단, 과거 전략을 현재에 무조건 재사용하지 않는다.

76. Adaptive Orchestration

장기적으로:

Task
 ↓
Candidate Plans
 ↓
Experience / Historical Performance
 ↓
Select Plan
 ↓
Execute
 ↓
Evaluate
 ↓
Update Orchestration Memory

구조를 연구한다.

77. Orchestration as a Learned Policy

장기적으로 Orchestrator 자체를 학습 가능한 Policy로 볼 수 있다.

Task State
+
Capabilities
+
Budget
+
History
 ↓
Orchestration Policy
 ↓
Plan

그러나 현재는 Research Further.

78. Orchestration and Harness

Orchestration은 Harness의 일부일 수도 있다.

후보:

Agent
 ↓
Harness
 ├── Context
 ├── Memory
 ├── Capability
 ├── Security
 ├── Orchestration
 └── Evaluation

또는:

Agent Harness
       ↓
Orchestrator

어디에 둘지는 Integrated Architecture Review에서 결정한다.

79. Historical / Foundational Ideas

Multi-Agent에 관한 오래된 아이디어도 유지한다.

예:

Planner–Executor
Blackboard Architecture
Hierarchical Task Networks
Actor Model
Message Passing
Pipeline Processing
MapReduce
Expert Systems
Ensemble / Voting
Debate
Society of Mind

현재 구현이 낡았더라도:

당시 어떤 문제를 해결했는가?

를 연구하고, 오래 살아남은 원칙은 NOAH에 재해석할 가치가 있다.

특히 Actor Model의:

State
+
Message
+
Isolation
+
Asynchronous Processing

은 Grok Build의 Session Actor와도 연결되므로 장기 Runtime Architecture에서 계속 참고할 가치가 있다.

80. Current Frontier

2026년 현재 Multi-Agent 연구는 다음 문제로 확장되고 있다.

Orchestration
Planning
Handoff
Tool Coordination
Information Transfer
Verification
Cost Optimization
Parallel Execution
Long-Horizon Tasks

최근 OrchBench는 orchestration plan을 deterministic simulation으로 독립 평가할 수 있도록 하며, MAS-Orchestra는 전체 Multi-Agent 구조를 하나의 orchestration problem으로 최적화하려 한다.

또 PerspectiveGap은 subagent에게 무엇을 알려줄지 결정하는 orchestration prompting 자체가 별도의 어려운 능력임을 보여준다. 평균 pass rate가 낮고 정보 누출도 발생했다는 결과가 나온다.

즉 앞으로는:

"Agent를 몇 개 만들었는가?"

보다

"어떤 정보를 누구에게 언제 전달하는가?"

가 더 중요한 문제가 될 가능성이 높다.

81. Candidate Orchestration Architecture

현재까지의 Review를 종합하면 다음 구조를 후보로 둔다.

                           NOAH
                             │
                           Task
                             │
                     Orchestration Layer
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
       Strategy           Routing            Budget
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    Execution Plan / DAG
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
       Agent A             Agent B           Agent C
          │                  │                  │
       Context A          Context B         Context C
          │                  │                  │
       Capabilities       Capabilities      Capabilities
          └──────────────────┼──────────────────┘
                             │
                       Aggregation
                             │
                        Verification
                             │
                         Evaluation
                             │
                           Result

이것은 Candidate Architecture이며 최종 Blueprint가 아니다.

82. Candidate Decisions
주제	초기 판단
Single Agent 기본	Adopt
Multi-Agent 필요 시 확장	Adopt
Handoff	Adapt
Agent-as-Tool	Adapt
Sequential Pipeline	Adopt
Parallel Fan-out/Fan-in	Adapt
DAG orchestration	Research Further
Planner / Executor	Adapt
Planner / Executor / Verifier	Adapt
Supervisor	Adapt
Deep hierarchy	Reject as default
Peer-to-Peer	Research Further
Shared Full Context	Reject as default
Projected Context	Adopt
Shared Memory	Research Further
Isolated Memory	Adopt as default
Structured Handoff	Adopt
Agent Discovery	Adapt
Dynamic Routing	Research Further
Cost-aware routing	Research Further
Capability-aware routing	Research Further
Persistent Specialist	Research Further
Ephemeral Agent	Adopt
Child permission > Parent	Reject
Agent Replacement	Adopt
Replanning	Adopt
Adaptive Orchestration	Research Further
Learned Orchestrator	Defer
Independent Verifier	Research Further
Consensus-only aggregation	Reject
Evidence-based aggregation	Adopt
Orchestration Trace	Adopt
Orchestration Evaluation	Adopt
83. What NOAH Should Not Do
Multi-Agent by Default

Reject.

More Agents = Better

Reject.

Full Context Sharing

Reject as default.

Unlimited Parallelism

Reject.

Deep Agent Hierarchy

Reject as default.

Parent-to-Child Privilege Escalation

Reject.

Majority Vote as Truth

Reject.

Unbounded Agent Spawning

Reject.

Dynamic Routing Without Budget

Reject.

Multi-Agent Without Verification

Reject.

84. Risks
Coordination Failure

Agent 간 의존성과 통신 문제가 전체 작업을 망칠 수 있다.

Information Loss

Handoff에서 중요한 정보가 사라질 수 있다.

Information Leakage

불필요한 Context가 다른 Agent로 전달될 수 있다.

Context Fragmentation

Agent가 각각 다른 사실을 가지고 있을 수 있다.

Shared Memory Contamination

잘못된 정보가 여러 Agent로 퍼질 수 있다.

Cost Explosion

Agent와 Tool 호출이 동시에 증가할 수 있다.

Latency

병렬화가 오히려 synchronization overhead를 만들 수 있다.

Failure Propagation

하나의 Agent 오류가 다음 Agent로 전파될 수 있다.

Orchestrator Bottleneck

중앙 Coordinator가 병목이 될 수 있다.

Planner Error

초기 Plan이 잘못되면 전체 workflow가 잘못될 수 있다.

Evaluation Complexity

Multi-Agent는 누가 실패했는지 판단하기 어렵다.

85. Open Questions
NOAH의 기본 실행 단위는 항상 Single Agent인가?
Multi-Agent 전환 조건은 무엇인가?
Agent vs Skill의 경계는 무엇인가?
Handoff와 Agent-as-Tool을 언제 사용하는가?
Planner가 항상 필요한가?
Orchestrator는 deterministic해야 하는가?
DAG가 Workflow Engine보다 유리한가?
Context projection의 최소 단위는 무엇인가?
Agent 간 Memory를 얼마나 공유해야 하는가?
Shared State와 Shared Memory는 어떻게 구분하는가?
Agent Discovery가 필요한 규모는 어느 정도인가?
Agent Routing을 model이 직접 해야 하는가?
Cost-aware Routing은 실제 효과가 있는가?
Agent 수의 최적점을 어떻게 찾는가?
Parallelism이 실제 latency를 얼마나 줄이는가?
Information transfer를 어떻게 평가하는가?
Agent 결과를 어떤 기준으로 aggregation하는가?
Independent Verifier가 필요한 작업은 무엇인가?
Multi-Agent 실패를 어디에서 recover하는가?
Agent replacement 후 Context/State continuity를 어떻게 보장하는가?
Persistent Specialist의 Memory는 어디에 저장되는가?
Temporary Agent를 언제 삭제하는가?
Orchestration Memory를 어떻게 신뢰할 것인가?
Orchestrator가 과거 경험으로부터 잘못된 전략을 학습하면 어떻게 rollback하는가?
Multi-Agent 실행의 최종 책임자는 누구인가?
User가 Orchestrator보다 우선해야 하는 설정은 무엇인가?
Agent 간 통신이 향후 A2A 같은 표준으로 이동해도 NOAH 구조를 유지할 수 있는가?
Multi-Agent가 실제 사용자 가치에 기여했는지를 어떻게 장기간 평가할 것인가?
86. Evaluation Criteria

Orchestration은 다음 기준으로 평가한다.

Quality
Correctness
Safety
Information Retention
Task Success
Latency
Token Cost
Compute Cost
Agent Utilization
Coordination Overhead
Recovery
Robustness

특히:

Quality Gain / Coordination Cost

를 중요한 비교 지표로 검토한다.

87. Orchestration Experiment Design

예를 들어 같은 Task를:

Experiment A
Single Agent

Experiment B
2-agent sequential

Experiment C
3-agent parallel

Experiment D
Planner + Executor

Experiment E
Planner + Executor + Verifier

로 실행하여:

Quality
Cost
Latency
Safety
Recovery

를 비교한다.

OrchBench와 같은 simulation-first 접근을 향후 PoC에서 참고할 수 있다. OrchBench는 실제 worker를 모두 실행하지 않고 orchestration plan 자체를 deterministic하게 비교함으로써 토큰·시간을 크게 절감하면서도 실제 Claude Code 실행 품질과 높은 상관을 보였다.

88. Long-Horizon Orchestration

장기 Task에서는 Orchestrator가 지속적으로:

Observe
 ↓
Plan
 ↓
Execute
 ↓
Evaluate
 ↓
Replan

을 반복해야 할 가능성이 높다.

따라서 Orchestration은 단순한 초기 DAG 생성기가 아니라 ongoing control loop가 될 수 있다.

89. Orchestration and Recovery

장기적으로:

Task
 ↓
Plan
 ↓
Agent
 ↓
Failure
 ↓
Diagnose
 ↓
Reassign / Retry / Replan
 ↓
Continue

구조를 검토한다.

90. Orchestration and Learning

NOAH의 장기 방향:

Orchestration
 ↓
Execution
 ↓
Evaluation
 ↓
Successful Strategy
 ↓
Memory
 ↓
Future Orchestration

결국:

NOAH가 어떤 Task에 어떤 형태의 협업이 효과적인지 경험으로 학습할 수 있는가?

가 장기 연구 질문이 된다.

91. Future Resilience

Orchestration Architecture는 특정 Multi-Agent Framework에 종속되지 않는다.

❌ NOAH는 LangGraph를 Orchestrator로 사용한다.

✅ NOAH는 Orchestration Contract를 제공한다.

구현은:

Current Orchestrator
Future Orchestrator
Rule-based
LLM-based
Learned

로 교체 가능해야 한다.

92. Stable Orchestration Contracts

미래에 유지할 계약:

Task
Goal
Agent Identity
Capability
Delegation
Context Projection
Budget
Result
Evidence
Verification

구현 방식은 바뀔 수 있다.

93. Historical / Foundational Ideas

오래된 개념 중에서도 NOAH에 장기적으로 유용할 수 있는 것들을 보존한다.

특히:

Blackboard Architecture

여러 전문가가 공유된 작업 공간에 지식을 올리고 문제를 함께 해결한다.

Actor Model

독립적인 실행 단위가 Message를 통해 비동기적으로 협력한다.

Hierarchical Task Networks

복잡한 목표를 계층적으로 세분화한다.

MapReduce

독립 작업을 병렬 수행하고 결과를 집계한다.

Expert Systems

전문 영역별 지식과 책임을 분리한다.

이 원칙들은 현재의 Agent framework보다 오래됐지만, 분산된 지능을 구성하는 기본 문제를 이미 다뤘다는 점에서 여전히 가치가 있다.

94. Current Frontier Summary

2026년 현재 Multi-Agent의 중요한 연구 방향:

Task Decomposition
Agent Routing
Handoff
Parallelism
Context Allocation
Information Transfer
Verification
Cost-aware Orchestration
Simulation-based Evaluation
Long-Horizon Coordination

최근 연구는 특히 Agent 수 자체보다 orchestration quality와 정보 전달 품질이 중요하다는 방향을 보여주고 있다. OrchBench는 critical information retention과 coordination failure를 강조하고, PerspectiveGap은 orchestration prompt composition 자체의 어려움을 보여준다.

95. Current Recommendation

현재까지의 Research를 종합하면:

NOAH는 Multi-Agent를 기본 실행 모델로 사용하지 않는다.

대신:

Single Agent
     ↓
Need for specialization / parallelism / isolation
     ↓
Subagent / Multi-Agent

를 사용한다.

그리고:

Orchestration의 목표는 Agent 수를 늘리는 것이 아니라, Task를 더 잘·안전하게·저렴하게 해결하는 것이다.

이를 위해:

Orchestrator
├── Strategy
├── Routing
├── Delegation
├── Budget
├── Coordination
├── Aggregation
├── Verification
└── Recovery

를 독립 계층 후보로 둔다.

96. Long-Term Vision

장기적으로 NOAH가:

Task
 ↓
Understand
 ↓
Choose Strategy
 ↓
Single Agent?
   ├── Yes → Execute
   │
   └── No
       ↓
    Decompose
       ↓
    Delegate
       ↓
    Parallel / Sequential
       ↓
    Aggregate
       ↓
    Verify
       ↓
    Learn

할 수 있는 시스템으로 발전하는 것을 목표로 한다.

그리고 미래에는:

Experience
 ↓
Orchestration Memory
 ↓
Better Strategy Selection
 ↓
Better Coordination
 ↓
Better Outcome

이라는 Cycle이 가능해질 수 있다.

97. What Remains Unresolved

현재 결정하지 않은 핵심:

Handoff vs Agent-as-Tool
DAG vs Dynamic Planner
Supervisor vs Decentralized
Shared vs Isolated Memory
Static vs Learned Routing
Rule-based vs LLM-based Orchestrator
Agent Discovery
A2A adoption
Cost-aware routing
Orchestration Learning

이들은 향후 PoC에서 검증한다.

98. Review Boundary

이번 Review에서는 다음을 최종 결정하지 않는다.

최종 Orchestrator 구현
Multi-Agent Framework
A2A Protocol
Agent Router
Planner
Workflow Engine
Agent Communication Bus
Shared Memory implementation
Learned Orchestration Policy
99. Review Outcome

현재까지의 Research를 종합하면:

Multi-Agent
≠
More Intelligence

이며:

Better Orchestration
=
Better Task Decomposition
+
Better Information Transfer
+
Better Agent Selection
+
Better Verification
+
Controlled Coordination Cost

라는 방향이 유력하다.

최근 OrchBench는 실제 orchestration plan을 독립적으로 평가하면서 task-critical information 보존이 Agent 수를 늘리는 것보다 중요할 수 있고, coordination failure 때문에 parallelism의 효과가 감소할 수 있음을 보여준다.

따라서 NOAH는:

필요할 때만 Multi-Agent를 사용하는 adaptive orchestration system

을 장기 후보 Architecture로 둔다.

100. Next Step

이번 Review 후 바로 Multi-Agent Runtime을 구현하지 않는다.

다음 순서:

Orchestration & Multi-Agent Review
          ↓
Open Questions
          ↓
필요한 추가 Research
          ↓
Identity / Personality Review
          ↓
Architecture Integration Review
          ↓
DDR
          ↓
02-Architecture
          ↓
PoC
          ↓
Evaluation

그리고 다음으로 검토할 것은:

Architecture Review — Identity & Personality

이다.

이 Review에서는 NOAH가 장기적으로 하나의 지속적인 존재처럼 행동하기 위해:

Identity
Personality
Role
Values
Preferences
Continuity
Self Model
Memory

의 경계를 어떻게 둘 것인지 검토한다.