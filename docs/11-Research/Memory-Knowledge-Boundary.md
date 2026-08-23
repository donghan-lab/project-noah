# Memory / Knowledge Boundary Research

> Project NOAH Research
> Research 대상: Memory / Knowledge Boundary
> Research Version: 0.1
> Priority: P0
> Status: Research

---

# 1. Research Purpose

Project NOAH에서 Memory와 Knowledge의 개념적·기능적 경계를 정의하기 위한 연구를 수행한다.

핵심 질문:

> "Memory와 Knowledge는 무엇이 다르며, 두 시스템은 어디에서 분리되고 어디에서 연결되어야 하는가?"

본 문서는 최종 Architecture를 결정하지 않는다.

---

# 2. Why This Research Matters

현재 Architecture Integration Review에서 다음 개념의 경계가 아직 완전히 확정되지 않았다.

- Memory
- Knowledge
- Context
- State
- Experience
- Artifact
- Retrieval
- Learning

현재까지의 Architecture Review에서는:

Memory
= 과거 경험과 지속적으로 사용할 정보

Knowledge
= 외부 또는 구조화된 정보

라는 초기 가설을 사용했지만,
실제 시스템에서는 둘이 상당 부분 겹칠 수 있다.

따라서 다음을 연구한다.

- Memory와 Knowledge의 정확한 차이
- Experience가 Memory가 되는 과정
- Knowledge가 Memory가 되는 과정
- Memory와 Knowledge의 저장 방식
- Retrieval의 공통점과 차이
- Provenance와 Trust
- Temporal information
- Update / Revision
- Forgetting
- User-specific information
- Project-specific information
- External knowledge
- Generated knowledge

---

# 3. Current NOAH Hypothesis

현재 가설:

> Memory는 과거의 경험과 지속적인 개인·프로젝트 맥락을 미래의 판단에 사용하기 위해 보존하는 시스템이다.

> Knowledge는 외부 또는 내부의 구조화된 사실·정보·개념을 검색하고 활용할 수 있도록 관리하는 시스템이다.

그러나 실제로 하나의 정보가 두 범주에 동시에 속할 가능성을 검토한다.

예:

```text
Memory:
"2026-08-24에 이 프로젝트의 Runtime 구조를 이렇게 결정했다."

Knowledge:
"Durable execution은 checkpoint와 recovery를 통해 장기 실행을 지원한다."
4. Memory vs Knowledge

초기 구분:

Memory
= 경험과 지속성

Knowledge
= 사실과 정보

하지만 이 구분이 충분한지 검토한다.

5. Experience

Experience는 실제로 발생한 사건이다.

Experience
├── Time
├── Task
├── Context
├── Actions
├── Observations
├── Result
└── Outcome

Experience 자체는 Memory와 동일하지 않다.

6. Experience → Memory

후보:

Experience
 ↓
Candidate
 ↓
Evaluation
 ↓
Memory

모든 Experience를 Memory로 승격하지 않는다.

7. Experience → Knowledge

경험에서 일반화된 사실이 만들어질 수도 있다.

Experience A
Experience B
Experience C
      ↓
Reflection
      ↓
General Pattern
      ↓
Knowledge

예:

Experience:
OpenCode Runtime PoC가 특정 상황에서 실패했다.

Knowledge:
해당 종류의 Runtime에서 Context projection을 제한해야 한다.
8. Knowledge → Memory

외부 Knowledge도 개인/프로젝트 경험과 연결되면 Memory가 될 수 있는지 검토한다.

예:

Knowledge:
Python 3.13 behavior

Memory:
NOAH 프로젝트에서는 Python 3.13을 사용한다.

즉 외부 사실 자체와 프로젝트에 적용된 사실을 구분할 필요가 있다.

9. Memory → Knowledge

Memory에 저장된 경험에서 일반화된 지식을 추출할 수 있다.

Memory
 ↓
Reflection
 ↓
Generalization
 ↓
Knowledge

이 과정에서 원본 Evidence와 Provenance를 유지한다.

10. Context

Memory와 Knowledge 모두 Context에 들어올 수 있다.

Memory
 ↓
Retrieval
 ↓
Context

Knowledge
 ↓
Retrieval
 ↓
Context

따라서 Context는 둘을 저장하는 시스템이 아니라 현재 Model execution에 필요한 projection layer로 유지한다.

11. State

State는 현재 canonical condition이다.

State
≠
Memory
≠
Knowledge

예:

State:
Current Runtime = paused

Memory:
예전에 Runtime pause/recovery를 수행한 경험

Knowledge:
Durable execution의 일반적인 원리
12. Artifact

Artifact도 Memory/Knowledge와 구분한다.

Artifact
= 실제 생성되거나 변경된 결과물

Memory
= Artifact와 관련하여 미래에 사용할 수 있는 경험

Knowledge
= Artifact에 포함되거나 추출된 사실

예:

Artifact:
Architecture.md

Memory:
"Architecture v1을 이 방식으로 결정했다."

Knowledge:
"NOAH Runtime은 durable execution을 지원하도록 설계된다."
13. Source of Truth

Memory와 Knowledge 각각의 canonical source가 무엇인지 검토한다.

후보:

User
Database
Document
Artifact
External Source
Tool Observation
Experience
Agent Inference

모든 Source를 동일한 신뢰도로 취급하지 않는다.

14. Provenance

Memory와 Knowledge 모두 출처를 가져야 할 가능성이 높다.

후보:

Source
Created At
Updated At
Author
Agent
Evidence
Derived From
Confidence
Verification
15. Trust

정보의 신뢰 수준을 관리한다.

예:

User-confirmed
Verified external source
Observed environment
Tool result
Agent inference
Unverified generated information
16. Temporal Knowledge

Knowledge도 시간에 따라 변할 수 있다.

예:

Python 3.12
→ 2025

Python 3.13
→ 2026

따라서 Knowledge가 단순한 immutable fact인지 temporal fact인지 검토한다.

17. Temporal Memory

Memory도 시간 정보를 가진다.

Experience
→ when did this happen?

Memory
→ when was this true?

Memory와 Knowledge 모두 temporal model이 필요할 수 있다.

18. Contradiction

Knowledge에도 충돌이 발생한다.

Source A
→ X

Source B
→ Y

Memory에서도:

Memory A
→ preference X

Memory B
→ preference Y

가 충돌할 수 있다.

따라서 공통 Conflict Resolution 계층이 필요한지 검토한다.

19. Memory Scope

Memory는:

Global
User
Project
Agent
Session
Task
Temporary

등의 Scope를 가질 수 있다.

20. Knowledge Scope

Knowledge 역시:

Public
External
Project
User
Private
Internal

과 같은 Scope를 가질 수 있다.

21. Shared Memory vs Shared Knowledge

Multi-Agent 환경에서는:

Shared Memory

와:

Shared Knowledge

를 다르게 취급할 가능성이 있다.

Memory는 관계·경험과 연결될 수 있기 때문에 공유 범위를 더 엄격하게 제한할 수 있다.

22. Retrieval

Memory Retrieval과 Knowledge Retrieval이 동일한 시스템인지 검토한다.

공통:

Query
 ↓
Candidate Retrieval
 ↓
Ranking
 ↓
Projection
 ↓
Context

차이:

Memory
→ temporal / personal / experiential relevance

Knowledge
→ semantic / factual / source relevance
23. Retrieval Ranking

공통 ranking 요소:

Relevance
Recency
Authority
Confidence
Task Utility

Memory에 추가:

Personal Importance
Relationship Relevance
Experience Similarity

Knowledge에 추가:

Source Authority
Publication Date
Version
Domain Reliability
24. Storage

Memory와 Knowledge가 반드시 별도 Database여야 하는 것은 아니다.

후보:

Relational
Vector
Graph
Document
File
Event
Object

Logical separation과 Physical storage를 분리해서 연구한다.

25. Memory Storage Candidate

Memory 후보:

Episodic Store
Structured Store
Vector Index
Graph Index
Document / File Store
Version History
26. Knowledge Storage Candidate

Knowledge 후보:

Document Store
Structured Database
Vector Index
Graph
Knowledge Graph
External Search Index

둘 사이에 저장소를 공유할 수 있는지 검토한다.

27. Versioning

Memory:

Memory v1
→ Memory v2

Knowledge:

Knowledge Source v1
→ Source v2

둘 모두 Versioning이 필요할 수 있다.

28. Revision

Memory Revision:

Old Memory
 ↓
Evidence
 ↓
New Memory

Knowledge Revision:

Old Knowledge
 ↓
Updated Source
 ↓
New Knowledge

Revision semantics가 다른지 검토한다.

29. Forgetting

Memory에서는 Forgetting이 핵심이다.

Active
 ↓
Stale
 ↓
Archived
 ↓
Forgotten

Knowledge에서는 보통:

Active
 ↓
Outdated
 ↓
Deprecated

와 같은 방식이 더 적합할 수 있다.

이 차이가 실제 Architecture Boundary가 될 수 있는지 검토한다.

30. Knowledge Freshness

Knowledge는 최신성의 영향을 많이 받는다.

예:

Current API
vs
Deprecated API

따라서:

Last Verified
Version
Source
Expiration

등을 고려한다.

31. Memory Freshness

Memory에서도 freshness가 중요하지만 의미가 다르다.

예:

"사용자는 Python 3.13을 사용한다."

시간이 지나면 오래된 Memory가 될 수 있다.

32. User Memory

User Memory는:

Preferences
Facts
Relationships
Important Experiences

를 포함할 수 있다.

Knowledge Base와 분리할 필요성을 검토한다.

33. Project Knowledge

Project-specific information:

Architecture
Decisions
Code conventions
Infrastructure
Roadmap

은 User Memory와 External Knowledge 사이에 위치할 수 있다.

34. Project Memory vs Project Knowledge

예:

Project Memory:
"2026-08-24에 OpenCode 분석 결과 이 구조를 채택하지 않기로 했다."

Project Knowledge:
"OpenCode의 Session Runner는 이 방식으로 동작한다."

둘의 구분은 중요하다.

35. External Knowledge

외부 연구와 Reference:

Papers
Documentation
Repositories
Benchmarks
Articles

는 Knowledge의 중요한 Source다.

36. Generated Knowledge

Agent가 생성한 정보도 Knowledge Candidate가 될 수 있다.

그러나:

Generated
≠
Verified

이므로 validation이 필요하다.

37. Memory Candidate vs Knowledge Candidate

공통:

Information
 ↓
Candidate
 ↓
Validation
 ↓
Promotion

차이:

Memory Candidate
→ future personal/project utility

Knowledge Candidate
→ general / reference utility
38. Confidence

Memory와 Knowledge의 Confidence가 다른 의미를 가질 수 있다.

Memory:

How certain are we this happened / remains true?

Knowledge:

How reliable is this claim?
39. Knowledge Authority

Knowledge는 source hierarchy를 가질 수 있다.

예:

Official documentation
>
Primary research
>
Verified implementation
>
Community discussion
>
Unverified generated content

프로젝트 목적에 따라 달라질 수 있다.

40. Memory Authority

Memory:

User-confirmed
>
Observed
>
Tool-derived
>
Agent-inferred

등의 hierarchy를 검토한다.

41. Provenance Chain

Knowledge:

Claim
 ↓
Source
 ↓
Evidence

Memory:

Memory
 ↓
Experience
 ↓
Evidence

이러한 구조가 공통 Provenance Model로 통합될 수 있는지 검토한다.

42. Knowledge Graph

Knowledge 관계가 중요한 경우:

Entity
 ↓
Relationship
 ↓
Temporal State

형태를 사용할 수 있다.

Graphiti 같은 temporal knowledge graph 계열 접근을 Reference로 검토한다.

43. Memory Graph

Memory도 Relationship graph를 사용할 수 있다.

Person
 ↓
Experience
 ↓
Project
 ↓
Decision

하지만 Memory 전체를 Graph로 저장해야 한다는 뜻은 아니다.

44. Vector Memory / Vector Knowledge

Vector retrieval은 두 시스템에서 모두 사용할 수 있다.

하지만:

Vector DB
≠
Memory

그리고:

Vector DB
≠
Knowledge

라는 기존 원칙을 유지한다.

45. Files as Memory / Knowledge

파일 기반 Memory / Knowledge도 검토한다.

예:

Memory/
Knowledge/
Skills/

형태의 human-readable repository.

Git-backed memory 연구는 Memory를 사람이 검토하고 versioning할 수 있는 방향을 보여주는 현재 Reference 중 하나다.

46. Memory + Knowledge Unified Layer

후보:

Cognitive Information Layer
├── Memory
└── Knowledge

공통:

Write
Manage
Retrieve
Provenance
Versioning
Evaluation

차이는 metadata와 policy에서 둔다.

47. Separate Memory / Knowledge Systems

반대 후보:

Memory System
Knowledge System

를 완전히 독립시킨다.

장점:

명확한 semantics
privacy boundary
lifecycle 차이

단점:

duplication
retrieval complexity
cross-system integration
48. Unified Retrieval Interface

물리적으로 분리되어 있어도:

Information Retrieval Interface

를 통해:

Memory
Knowledge

를 하나의 Query API로 접근할 가능성을 검토한다.

49. Context Projection

최종적으로:

Memory
Knowledge
State
Artifact

가:

Context Manager

를 통해 하나의 Context로 projection될 수 있다.

50. Memory / Knowledge and Learning

Memory:

Experience
→ Memory

Knowledge:

Research
→ Knowledge

Learning은:

Memory + Knowledge + Evaluation
→ Better Behavior

로 연결될 가능성이 있다.

51. Knowledge and Capability

Knowledge는 Capability 선택을 개선할 수 있다.

예:

Knowledge:
PostgreSQL indexing principles

Capability:
database.optimize
52. Memory and Capability

Memory도 Capability 선택을 개선할 수 있다.

예:

Memory:
"이 Tool은 이전 Task에서 실패했다."

Capability Selection:
다른 Tool 선택
53. Knowledge and Orchestration

Knowledge를 이용해 Agent routing을 개선할 수 있다.

예:

Task
 ↓
Knowledge:
domain = security
 ↓
Security Specialist
54. Memory and Orchestration

Past strategy를 Memory에서 검색할 수 있다.

Task
 ↓
Past successful orchestration
 ↓
Candidate Plan
55. Knowledge Poisoning

외부 Knowledge가 악성/오류 정보일 수 있다.

따라서:

External Source
 ↓
Validation
 ↓
Knowledge

구조를 유지한다.

56. Memory Poisoning

Memory 역시:

Experience
 ↓
Candidate Memory
 ↓
Validation
 ↓
Memory

과정을 거친다.

57. Knowledge vs Hallucination

Agent가 생성한 사실을 Knowledge로 바로 승격하지 않는다.

Generated Claim
 ↓
Evidence
 ↓
Verification
 ↓
Knowledge Candidate
58. Memory vs Hallucination

Agent가 기억한다고 주장하는 것도 실제 Memory와 일치하는지 검증한다.

Agent Claim
 ↓
Memory Lookup
 ↓
Evidence
59. Security Boundary

Memory와 Knowledge 모두 Security Boundary를 가진다.

Memory:

Privacy
Consent
Scope
Access
Deletion

Knowledge:

Source Trust
Integrity
Access
Provenance
60. Privacy

Memory는 User-specific information을 포함할 가능성이 높다.

따라서:

Memory
→ User-controlled

Knowledge
→ Source / License controlled

과 같은 차이가 존재할 수 있다.

61. Ownership

Memory:

User / Project / NOAH

Knowledge:

External Source / Project / Public

Ownership semantics를 연구한다.

62. Export / Deletion

Memory는 사용자의:

inspect
edit
export
delete

권리를 고려해야 한다.

Knowledge는 source policy에 따라 다르다.

63. Evaluation

Memory와 Knowledge 각각의 평가:

Memory:

Recall
Freshness
Utility
Forgetting
Personalization
Contradiction

Knowledge:

Correctness
Source Reliability
Freshness
Coverage
Retrieval Accuracy
Citation
64. Evaluation of Boundary

가장 중요한 실험:

Same Information
→ Memory
→ Knowledge

를 각각 처리했을 때:

Retrieval
Context quality
Task success
Cost
Freshness
Trust

가 어떻게 달라지는지 비교한다.

65. Historical / Foundational Ideas

오래된 아이디어도 조사한다.

Database Systems

Data vs metadata vs transaction.

Information Retrieval

Document vs query vs index.

Knowledge Representation

Facts vs rules vs relationships.

Cognitive Architectures

Working / Episodic / Semantic Memory.

Case-Based Reasoning

Past experiences를 future problem solving에 재사용.

Knowledge Graphs

Relationship-centered knowledge.

66. Current Frontier

현재 연구 방향:

Agentic Memory
Evolving Memory
Temporal Knowledge
Memory Governance
Memory-as-Policy
Externalized Task State
Context Repositories
Knowledge Graph + Memory
Long-Horizon Memory
Memory Evaluation
67. Candidate Boundary

현재 가설:

                  Cognitive Information
                         │
               ┌─────────┴─────────┐
               │                   │
            Memory              Knowledge
               │                   │
        Experience-based      Fact / Source-based
               │                   │
               └─────────┬─────────┘
                         │
                    Retrieval
                         │
                  Context Manager
                         │
                       Agent
68. Unified Interface Candidate
Information Interface
├── remember()
├── retrieve_memory()
├── search_knowledge()
├── explain_source()
├── update()
├── archive()
└── forget()

실제 API는 Specification에서 결정한다.

69. Stable vs Replaceable

Stable:

Memory semantics
Knowledge semantics
Provenance
Scope
Retrieval contract
Revision contract

Replaceable:

Vector DB
Graph DB
Embedding
Search engine
File system
Storage backend
70. Risks
Concept Overlap

Memory와 Knowledge를 나누면서 오히려 복잡해질 수 있다.

Duplication

같은 정보가 양쪽에 중복 저장될 수 있다.

Inconsistent Updates

한쪽은 업데이트되고 다른 쪽은 stale할 수 있다.

Retrieval Competition

Memory와 Knowledge가 서로 다른 결과를 반환할 수 있다.

Provenance Complexity

정보의 출처 추적이 복잡해질 수 있다.

Privacy Leakage

Memory가 Knowledge layer를 통해 노출될 수 있다.

Knowledge Pollution

검증되지 않은 정보가 Knowledge에 들어갈 수 있다.

71. Open Questions
Memory와 Knowledge를 반드시 별도로 정의해야 하는가?
둘의 최소 의미적 차이는 무엇인가?
Project Knowledge와 Project Memory의 경계는?
경험에서 나온 일반화는 Memory인가 Knowledge인가?
User preference는 Memory인가 Knowledge인가?
Decision 기록은 Memory인가 Project Knowledge인가?
Conversation summary는 Memory인가 Artifact인가?
Knowledge source를 Memory에 링크하는 방식은?
Memory와 Knowledge가 동일한 retrieval engine을 사용해도 되는가?
Unified Information Interface가 필요한가?
Temporal information은 공통 모델로 만들 수 있는가?
Provenance model을 통합할 수 있는가?
Memory와 Knowledge의 security policy는 어떻게 다른가?
Knowledge freshness와 Memory freshness를 하나의 모델로 만들 수 있는가?
Forgetting과 deprecation의 관계는?
하나의 object가 Memory와 Knowledge 두 역할을 동시에 가질 수 있는가?
Knowledge가 Memory로 승격되는 조건은?
Memory가 Knowledge로 승격되는 조건은?
Human-editable file와 Database의 경계를 어디에 둘 것인가?
Memory / Knowledge가 Agent Identity에 어떤 영향을 주어야 하는가?
72. Research Findings

각 Reference에 대해:

Reference
Problem
Memory Model
Knowledge Model
Storage
Retrieval
Lifecycle
Provenance
Strengths
Weaknesses
NOAH Relevance
Stable Principle

을 기록한다.

73. Historical / Current / Emerging Comparison
Category	Example	Main Idea
Historical	Case-Based Reasoning	경험 재사용
Historical	Cognitive Architectures	Memory specialization
Current	Graph / Vector Memory	Retrieval
Current	Context Repositories	Human/Agent editable memory
Emerging	Agentic Memory	Active memory policy
Emerging	Evolving Knowledge	Revision / temporal state
74. Preliminary Recommendation

현재 정보만으로는:

Memory와 Knowledge를 완전히 하나로 합치기보다, 의미적으로 구분하되 공통 Information / Retrieval interface를 공유하는 방향

이 유력하다.

즉:

Memory System
Knowledge System
      ↓
Shared Information Interface
      ↓
Context Manager

구조를 우선 검토한다.

75. Why Not Fully Separate?

완전히 분리하면:

retrieval duplication
storage duplication
contradiction handling duplication
provenance duplication

문제가 발생할 수 있다.

76. Why Not Fully Unified?

완전히 합치면:

privacy boundary 약화
semantics 혼합
lifecycle 혼합
forgetting/deprecation 혼합
ownership ambiguity

가 발생할 수 있다.

77. Proposed Semantic Rule

현재 가장 유력한 규칙:

Memory는 경험의 지속성에 초점을 둔다. Knowledge는 정보의 신뢰성과 활용에 초점을 둔다.

하지만 하나의 객체가 상황에 따라 두 역할을 동시에 가질 수 있는 가능성을 열어둔다.

78. Future Resilience

향후 Memory가:

Vector
Graph
File
Learned State
External Repository

로 변화해도:

Memory Contract

를 유지할 수 있어야 한다.

Knowledge도 동일하다.

79. Research Completion Criteria
☐ Memory / Knowledge semantic boundary 정의
☐ Experience relation 정의
☐ Project Memory / Project Knowledge boundary
☐ Retrieval relationship
☐ Provenance relationship
☐ Temporal model
☐ Privacy / ownership boundary
☐ Storage independence
☐ Unified interface 가능성
☐ Knowledge ↔ Memory promotion rules
☐ 평가 방법 정의
☐ Integration Review에 반영할 후보 결정
80. Next Step

이번 연구가 끝난 후:

Memory / Knowledge Boundary Research
          ↓
Findings
          ↓
Integration Review v0.2
          ↓
P1 Artifact Architecture Research
          ↓
P1 Identity Persistence Research
          ↓
DDR
          ↓
02-Architecture

로 진행한다.

81. Final Research Goal

최종 목적:

"NOAH가 과거를 기억하면서도 외부 세계의 지식을 올바르게 구분하고, 둘을 현재 판단에 필요한 형태로 결합할 수 있는가?"