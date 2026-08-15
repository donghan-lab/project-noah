# Architecture Review — Memory

> Project NOAH Architecture Review
> Review 대상: Memory Architecture
> Review Version: 0.1
> Status: Review

---

# 1. Review Purpose

Project NOAH에서 Memory의 의미와 책임을 정의하고, 경험과 지식을 장기적으로 보존·관리·검색·수정·통합·폐기할 수 있는 Architecture를 검토한다.

본 Review의 핵심 질문은 다음과 같다.

> **"NOAH는 무엇을 기억해야 하며, 그것을 어떻게 보존하고 변화시키며 미래의 판단에 사용할 것인가?"**

본 Review에서는 단순한 저장소 선택보다 다음 문제를 중심으로 검토한다.

* 무엇을 Memory로 승격할 것인가?
* 원본 Experience는 보존해야 하는가?
* Memory와 Knowledge의 차이는 무엇인가?
* Episodic / Semantic / Procedural Memory가 필요한가?
* Memory는 어떻게 작성되는가?
* Memory는 어떻게 수정되는가?
* Memory는 언제 Consolidation되는가?
* 잘못된 Memory는 어떻게 제거되는가?
* 오래된 정보는 어떻게 Forgetting되는가?
* Memory의 신뢰도와 Provenance는 어떻게 관리하는가?
* Memory는 Context에 어떻게 들어가는가?
* Memory 자체가 경험을 통해 개선될 수 있는가?

본 문서는 최종 Memory Blueprint가 아니며, Memory Architecture의 후보와 경계를 검토하는 문서다.

---

# 2. Core Architecture Question

## Memory란 무엇인가?

초기 정의:

> Memory는 미래의 판단·행동·개인화·학습에 다시 사용할 가치가 있다고 판단된 과거 정보와 경험을 지속적으로 관리하는 시스템이다.

Memory는 단순한 데이터 저장소가 아니다.

```text
Experience
    ↓
Memory Candidate
    ↓
Evaluation
    ↓
Memory
    ↓
Management
    ↓
Retrieval
    ↓
Future Decision
```

따라서 Memory의 핵심은 Storage보다 **Selection, Management, Retrieval, Revision**에 있다.

---

# 3. Memory vs State vs Context vs Knowledge

이 네 개념은 분리한다.

```text
State
= 현재 시스템의 canonical condition

Context
= 현재 실행에서 Model에 제공되는 정보

Memory
= 미래의 판단을 위해 지속적으로 보존되는 과거 정보/경험

Knowledge
= 특정 주제에 대해 구조화되어 활용 가능한 정보
```

예:

```text
현재 State
→ "현재 프로젝트는 Runtime PoC 단계"

현재 Context
→ "방금 실패한 테스트와 현재 Task"

Memory
→ "이 프로젝트에서는 이전에 이 접근을 시도했지만 실패했다"

Knowledge
→ "이 Runtime 패턴의 일반적인 특성과 구현 방법"
```

Memory와 Knowledge가 일부 겹칠 수 있지만 동일한 개념으로 취급하지 않는다.

---

# 4. Memory Lifecycle

최근 Memory 연구에서는 Memory를 단순 저장소가 아니라 지속적인 생명주기로 보는 방향이 중요하다.

초기 후보:

```text
Experience
    ↓
Capture
    ↓
Candidate
    ↓
Filter
    ↓
Store
    ↓
Manage
    ↓
Retrieve
    ↓
Use
    ↓
Update / Revise
    ↓
Forget / Archive
```

2026년 Memory survey는 이 과정을 `write → manage → read`라는 기본 생명주기로 정리하면서 continual consolidation, contradiction handling, forgetting, provenance, privacy 등을 핵심 문제로 제시한다.

---

# 5. Raw Experience vs Consolidated Memory

Memory에서 가장 중요한 설계 질문 중 하나다.

과거 경험을 바로 요약하여 Memory로 바꾸는 것에는 위험이 있다.

2026년 연구에서는 LLM이 유용한 episodic trajectories를 지속적으로 consolidation하는 과정에서 기억의 품질이 오히려 저하될 수 있으며, raw episodic evidence를 유지하는 방식이 자동 consolidation보다 경쟁력 있거나 더 안정적일 수 있다는 결과가 보고되었다.

따라서:

```text
Raw Experience
        │
        ├───────────────┐
        ▼               ▼
 Episodic Record    Consolidation
        │               │
        │               ▼
        │          Semantic / Lesson
        │               │
        └───────┬───────┘
                ▼
             Memory
```

구조를 검토한다.

### 초기 판단

**Raw Evidence와 Consolidated Memory를 분리한다.**

---

# 6. Episodic Memory

Episodic Memory는 실제로 발생한 경험을 보존한다.

후보 정보:

```text
Episode
├── Time
├── Task
├── Goal
├── Context Snapshot
├── Actions
├── Tool Calls
├── Observations
├── Result
├── Failure
├── Outcome
└── Verification
```

예:

> "2026-08-15 Runtime PoC에서 OpenCode 방식의 Context assembly를 실험했고, Context size가 증가하면서 latency가 크게 증가했다."

Episodic Memory는 미래의 reflection과 학습을 위한 원본 근거로 활용될 수 있다.

---

# 7. Semantic Memory

Semantic Memory는 여러 경험에서 일반화된 사실과 지식을 저장한다.

예:

```text
Experience A
Experience B
Experience C
      ↓
   Reflection
      ↓
Semantic Knowledge
```

예:

> "NOAH의 Runtime에서는 Tool Result 전체를 Context에 넣는 방식보다 selective projection이 유리하다."

Semantic Memory는 특정 하나의 사건보다 **일반화된 지식**을 표현한다.

---

# 8. Procedural Memory

Procedural Memory는 **어떻게 행동하는가**에 관한 지식을 저장한다.

예:

```text
Procedure
├── Trigger
├── Preconditions
├── Steps
├── Constraints
├── Expected Outcome
└── Failure Recovery
```

예:

> "OpenCode 분석 시 README → Agent → Session → Tool → Runner 순서로 탐색한다."

Skill이나 Workflow와 겹칠 수 있기 때문에 별도 경계를 후속 Review에서 검토한다.

---

# 9. Working Memory

Working Memory는 현재 Task 수행에 필요한 단기적인 상태다.

```text
Working Memory
├── Current Goal
├── Current Plan
├── Recent Observations
├── Temporary Conclusions
├── Active Constraints
└── Recent Tool Results
```

Working Memory는 Context와 밀접하게 연결되지만 저장 목적과 수명은 다를 수 있다.

---

# 10. Long-Term Memory

Long-Term Memory는 현재 Session을 넘어 계속 보존할 가치가 있는 정보다.

후보:

```text
Long-Term Memory
├── User Facts
├── Preferences
├── Relationships
├── Project Knowledge
├── Learned Lessons
├── Past Experiences
└── Persistent Identity Information
```

Long-Term Memory는 필요할 때 Retrieval을 통해 Context에 제공한다.

---

# 11. Experience as a First-Class Memory Object

NOAH의 장기 목표를 고려하면 Experience를 단순 로그로 취급하지 않는다.

```text
Experience
├── What happened?
├── Why did it happen?
├── What was attempted?
├── What worked?
├── What failed?
├── What changed?
├── What was learned?
└── What should be done differently?
```

이를 통해 단순한 Conversation History와 **학습 가능한 Experience**를 구분한다.

---

# 12. Memory Candidate

모든 경험을 바로 Long-Term Memory로 승격하지 않는다.

```text
Experience
    ↓
Memory Candidate
    ↓
Relevance
Importance
Novelty
Reliability
Future Utility
Privacy
      ↓
Memory Decision
```

Candidate 상태를 도입하면 Memory Pollution을 줄일 수 있다.

---

# 13. Memory Write

Memory Write는 독립적인 정책을 가져야 한다.

초기 후보:

```text
Experience
    ↓
Candidate Extraction
    ↓
Validation
    ↓
Deduplication
    ↓
Conflict Check
    ↓
Trust Assessment
    ↓
Memory Write
```

특히 Agent가 생성한 정보와 외부에서 관찰한 정보를 동일하게 취급하지 않는다.

---

# 14. Memory Source Authority

Memory에는 출처가 존재해야 한다.

후보:

```text
Memory
├── Source
├── Source Type
├── Timestamp
├── Evidence
├── Confidence
├── Provenance
└── Last Verified
```

출처 후보:

```text
User Statement
Verified External Source
Observed Environment
Tool Result
Agent Inference
Agent Reflection
Imported Knowledge
```

이 정보가 있어야 Memory를 검증하거나 수정할 수 있다.

---

# 15. Memory Confidence

Memory의 신뢰도를 단순한 하나의 숫자로만 표현하지 않는 방향을 검토한다.

예:

```text
Confidence
+
Source Authority
+
Freshness
+
Evidence
+
Verification Status
```

예:

```text
User explicitly stated
→ high authority

Agent inference
→ lower authority

Old unverified observation
→ low freshness
```

---

# 16. Memory Provenance

Memory가 어떻게 만들어졌는지 추적할 수 있어야 한다.

```text
Memory
 ↓
Derived From
 ├── Episode A
 ├── Episode B
 └── External Source
```

가능한 Provenance 정보:

```text
Origin
Created At
Updated At
Derived From
Agent
Model
Source
Evidence
Transformations
```

이를 통해 잘못된 Memory의 원인을 역추적할 수 있다.

---

# 17. Contradictory Memory

장기적으로 Memory는 충돌한다.

예:

```text
Memory A
"사용자는 Python 3.12를 사용한다"

Memory B
"사용자는 Python 3.13을 사용한다"
```

새로운 Memory가 들어왔다고 무조건 기존 Memory를 삭제하지 않는다.

후보:

```text
Conflict
   ↓
Compare Sources
   ↓
Freshness
   ↓
Authority
   ↓
Verification
   ↓
Resolution
```

또한 상황에 따라 두 기억이 동시에 참일 가능성도 고려한다.

---

# 18. Temporal Memory

Memory는 시간에 따라 변한다.

예:

```text
2025
Python 3.12

2026
Python 3.13
```

따라서 Memory를 단순 key-value 현재값만으로 저장하지 않고:

```text
Fact
├── Value
├── Valid From
├── Valid To
├── Confidence
└── Evidence
```

처럼 temporal information을 관리하는 방향을 검토한다.

Zep/Graphiti 계열의 temporal knowledge graph 연구는 이런 시간적 관계와 cross-session 정보를 장기 Memory의 핵심 문제로 다룬다.

---

# 19. Forgetting

Memory가 많아지는 것 자체가 좋은 것은 아니다.

오래되거나 잘못된 Memory는 Future Decision을 오염시킬 수 있다.

2026년 Memora benchmark는 기존 long-term-memory 시스템이 invalidated memory를 계속 사용하는 문제를 확인하고, obsolete memory에 의존할수록 점수를 낮추는 forgetting-aware 평가를 제안한다.

따라서:

```text
Memory
  ↓
Freshness Check
  ↓
Still Useful?
  ├── Yes → Keep
  ├── Update → Revise
  ├── Uncertain → Verify
  └── No → Archive / Forget
```

구조를 검토한다.

---

# 20. Archive vs Delete

Forget을 반드시 완전 삭제로 정의하지 않는다.

후보:

```text
Active
  ↓
Stale
  ↓
Archived
  ↓
Deleted
```

Archive는 나중에 다시 필요할 수 있는 증거를 보존하는 역할을 한다.

따라서 Memory의 삭제 정책은 중요도와 Provenance에 따라 달라질 수 있다.

---

# 21. Consolidation

여러 Episodic Memories를 일반화하여 Semantic/Procedural Memory로 만들 수 있다.

```text
Episodes
  ↓
Reflection
  ↓
Pattern Detection
  ↓
Candidate Knowledge
  ↓
Validation
  ↓
Consolidated Memory
```

하지만 자동 consolidation을 무조건 실행하지 않는다.

2026년 연구에서는 지속적인 LLM-based consolidation이 원본보다 품질이 나빠질 수 있다는 결과가 보고되었기 때문에 **raw episodic evidence를 1급 데이터로 유지하고 consolidation을 gated operation으로 취급하는 것**을 우선 검토한다.

---

# 22. Reflection

Reflection은 여러 Experience를 분석하여 새로운 일반화를 발견하는 과정이다.

예:

```text
Episode A
Episode B
Episode C
   ↓
Reflection
   ↓
"What pattern exists?"
   ↓
Candidate Insight
```

Reflection 결과는 바로 Truth가 아니라 Candidate Knowledge로 취급한다.

---

# 23. Experience → Knowledge

NOAH의 장기 발전 관점에서 다음 Cycle을 검토한다.

```text
Experience
    ↓
Capture
    ↓
Episodic Memory
    ↓
Reflection
    ↓
Candidate Knowledge
    ↓
Validation
    ↓
Semantic / Procedural Memory
    ↓
Future Retrieval
    ↓
Better Decision
```

2026년 Memory 연구에서는 Storage → Reflection → Experience를 Memory 시스템의 발전 방향으로 보는 관점이 제안되었다.

---

# 24. Memory Retrieval

Memory Retrieval은 단순 Vector Search가 아니다.

후보 요소:

```text
Retrieval
├── Semantic Similarity
├── Temporal Relevance
├── Entity / Relationship
├── Task Relevance
├── User Importance
├── Recency
├── Confidence
└── Provenance
```

따라서:

```text
Query
 ↓
Candidate Retrieval
 ↓
Ranking
 ↓
Verification
 ↓
Context Projection
```

구조를 검토한다.

---

# 25. Multi-Modal Memory

NOAH의 장기 발전을 고려하면 Memory는 텍스트만을 대상으로 하지 않을 수 있다.

후보:

```text
Memory
├── Text
├── Image
├── Audio
├── Video
├── Code
├── Structured Data
└── Events
```

그러나 v0.1에서는 텍스트/구조화 데이터 중심으로 시작하고 Multi-modal Memory는 향후 확장 가능성을 남긴다.

---

# 26. Memory Representation

하나의 Storage representation에 모든 Memory를 넣지 않는 방향을 검토한다.

후보:

```text
Structured DB
Vector Store
Graph Store
Document / File Store
Event Store
Object Store
```

각 representation은 서로 다른 목적을 가진다.

예:

```text
Vector
→ Semantic similarity

Graph
→ Relationships / Temporal relations

Relational
→ Structured facts

Files
→ Human / Agent editable knowledge

Event Store
→ Raw experience
```

Mem0의 연구는 dynamically extracted/consolidated/retrieved memory와 graph-based memory를 비교했고, Zep/Graphiti는 temporal knowledge graph를 통해 동적 관계와 cross-session 정보를 다루는 접근을 제안한다.

---

# 27. Memory as a Git-backed System

최근 Letta는 Context Repository를 Git 기반 Memory로 제안했다.

Agent의 Memory를 파일 시스템으로 관리하고, Git으로 versioning하며, subagent가 별도의 worktree에서 Memory를 병렬 수정한 뒤 merge하는 구조까지 가능하게 만들었다. 또한 progressive disclosure와 memory reflection/defragmentation을 skill로 구성한다.

NOAH에서 검토할 후보:

```text
Memory Repository
├── Files
├── Metadata
├── Version History
├── Branch
└── Merge
```

이 구조는 NOAH의 장기 Memory뿐 아니라 **Memory 자체를 사람이 보고 수정할 수 있는 시스템**을 만드는 데 의미가 있다.

---

# 28. Memory as Editable State

Memory는 완전히 숨겨진 Vector DB가 아니라 사람이 직접 검토·수정할 수 있는 구조도 고려한다.

```text
Agent
   ↕
Memory Interface
   ↕
Memory Repository
   ↕
Human
```

이것은 신뢰와 Debugging을 높일 수 있지만, 직접 수정된 Memory에 대한 provenance와 validation이 필요하다.

---

# 29. Shared Memory

하나의 Agent가 여러 Conversation을 가지더라도 동일한 장기 Memory를 공유할 수 있는지 검토한다.

Letta의 2026 Conversations API는 하나의 Agent가 여러 concurrent conversations를 가지면서도 Agent의 identity와 경험을 공유하는 구조를 제시한다. Conversation별 경험이 Agent-wide memory로 이어질 수 있다.

NOAH 후보:

```text
Agent Identity
      │
      ├── Conversation A
      ├── Conversation B
      └── Conversation C
             │
             ▼
      Shared Long-Term Memory
```

---

# 30. Memory Isolation

반대로 모든 Memory를 공유해서는 안 된다.

후보 Scope:

```text
Memory Scope
├── Global
├── User
├── Agent
├── Project
├── Session
├── Task
└── Temporary
```

예:

```text
Project memory
→ Project A에서만 사용

User preference
→ User 전체에서 사용

Task memory
→ 해당 Task에서만 사용
```

Memory Scope는 Security와 Privacy에도 직접 연결된다.

---

# 31. Cross-Agent Memory

Specialist Agent가 경험을 공유할지 결정해야 한다.

후보:

```text
Research Agent
      ↓
Shared Memory
      ↑
Developer Agent
```

그러나 공유 Memory는:

* contamination
* permission leakage
* conflicting knowledge
* attribution loss

위험을 증가시킨다.

따라서 기본적으로 **공유보다 명시적 Scope와 Access Policy를 우선**한다.

---

# 32. Sleep-time / Offline Memory Processing

Memory 처리는 Agent가 사용자와 실시간 대화할 때만 실행할 필요가 없다.

Letta는 sleep-time compute와 memory reflection을 사용해 idle 상태에서 과거 context를 검토하는 방향을 연구하고 있으며, 2026년에는 이를 memory-first harness와 결합하고 있다.

NOAH 후보:

```text
Active Interaction
      ↓
Raw Experience
      ↓
Background Reflection
      ↓
Memory Update
```

즉 Memory Processing을 사용자 latency와 완전히 결합하지 않는 방향을 검토한다.

---

# 33. Memory Defragmentation

Memory가 오래 운영되면:

* 중복
* 지나치게 큰 파일
* 낡은 표현
* 분산된 지식
* 충돌하는 정보

가 발생할 수 있다.

Letta는 Git-backed memory repository를 대상으로 memory defragmentation skill을 사용하여 백업 후 파일을 분할·병합·재구성하는 방향을 제안한다.

NOAH에서도 향후:

```text
Memory
 ↓
Analyze
 ↓
Defragment
 ↓
Validate
 ↓
Reorganize
```

를 고려할 수 있다.

---

# 34. Memory Safety

Memory는 장기 지속성 때문에 새로운 공격 표면을 만든다.

위험:

```text
Memory Poisoning
False Memory
Prompt Injection Persistence
Unauthorized Memory Access
Cross-user Leakage
Sensitive Memory Exposure
```

따라서 Memory Write에도 Security Policy가 필요하다.

---

# 35. Memory Privacy

Constitution의:

> Memory must respect the user.

원칙을 Architecture에 반영한다.

Memory에는 다음과 같은 정책이 필요할 수 있다.

```text
Memory Policy
├── Consent
├── Visibility
├── Scope
├── Retention
├── Export
├── Correction
└── Deletion
```

특히 User Memory는 시스템 내부 사실과 동일한 방법으로 관리해서는 안 된다.

---

# 36. Memory Evaluation

Memory 성능을 단순 Recall Accuracy 하나로 평가하지 않는다.

평가 후보:

```text
Recall
Precision
Freshness
Temporal Consistency
Contradiction Resolution
Forgetting
Personalization
Task Utility
Hallucination Reduction
Latency
Cost
Privacy
```

2026년 Memora는 기억하는 능력뿐 아니라 reasoning/recommending과 obsolete-memory misuse까지 장기간 평가해야 한다고 제안한다.

---

# 37. Memory Benchmarking

NOAH Memory Evaluation은 다음 유형을 포함해야 한다.

## Recall

예전에 말한 사실을 정확하게 기억하는가?

## Temporal Update

과거 정보가 변경되었을 때 최신 상태를 유지하는가?

## Contradiction

서로 충돌하는 Memory를 처리하는가?

## Forgetting

더 이상 유효하지 않은 정보를 잊거나 낮은 우선순위로 만드는가?

## Experience Transfer

한 경험에서 얻은 Lesson을 이후의 다른 Task에 적용하는가?

## Personalization

사용자 선호를 지속적으로 반영하는가?

## Resistance to Poisoning

악의적/잘못된 정보가 Memory를 오염시키지 않는가?

---

# 38. Memory Utility

Memory의 목적은 많이 기억하는 것이 아니다.

평가 기준:

```text
Memory Utility
=
Future Decision Improvement
```

즉:

> Memory가 얼마나 많은 정보를 저장했는가?

보다:

> Memory를 사용했을 때 Agent의 미래 판단이 얼마나 좋아졌는가?

를 핵심 지표로 본다.

---

# 39. Memory Cost

Memory는:

* Storage
* Retrieval latency
* Context tokens
* Compute
* Maintenance
* Evaluation

비용을 발생시킨다.

따라서:

```text
Memory Value
vs
Memory Cost
```

를 비교해야 한다.

---

# 40. Memory Priority

모든 Memory의 중요도가 같지 않다.

후보 Priority:

```text
Critical
High
Normal
Low
Archive
```

또는 continuous score를 사용할 수 있다.

중요도는:

```text
Future Utility
+
Frequency
+
Recency
+
User Importance
+
Confidence
```

등으로 계산할 수 있다.

---

# 41. Memory Consolidation Policy

Consolidation은 자동으로 항상 실행하지 않는다.

후보 Trigger:

```text
Time-based
Task completion
Memory volume
Conflict detected
Idle time
User request
Repeated pattern
Evaluation signal
```

즉:

```text
Experience
 ↓
Should consolidate?
 ├── No → Preserve Episode
 └── Yes → Consolidate
```

를 검토한다.

---

# 42. Raw Evidence Preservation

NOAH는 가능하면 Memory가 생성될 때 원본 Evidence와 연결을 유지한다.

```text
Consolidated Memory
        │
        ▼
Evidence
 ├── Episode A
 ├── Episode B
 └── Episode C
```

이를 통해:

* Debugging
* Trust
* Correction
* Re-consolidation
* Forgetting

이 가능해진다.

---

# 43. Memory Revision

Memory는 immutable 또는 mutable 중 하나만 선택할 필요가 없다.

후보:

```text
Memory Version 1
      ↓
Update
      ↓
Memory Version 2
      ↓
Validation
      ↓
Current Memory
```

이때 이전 Version은 audit 또는 archive 목적으로 유지할 수 있다.

---

# 44. Memory Rollback

잘못된 Memory가 대량으로 생성되면 rollback이 필요할 수 있다.

```text
Bad Consolidation
      ↓
Detection
      ↓
Rollback
      ↓
Previous Memory Version
      ↓
Re-evaluate
```

이 기능은 Git-backed Memory와 특히 잘 연결될 수 있다.

---

# 45. Memory Architecture Candidate

현재 Review의 후보:

```text
                         NOAH MEMORY
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
        Episodic          Semantic         Procedural
            │                 │                 │
            └─────────────────┼─────────────────┘
                              │
                         Memory Manager
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
        Retrieval         Consolidation       Forgetting
           │                  │                  │
           └──────────────────┼──────────────────┘
                              │
                        Provenance
                              │
                         Evaluation
                              │
                        Context Bridge
```

---

# 46. Storage Architecture Candidate

Memory representation을 하나로 고정하지 않는다.

```text
Memory System
├── Episodic Store
├── Structured Store
├── Vector Index
├── Graph Index
├── Document / File Store
└── Version History
```

각 저장소는 필요에 따라 교체 가능하도록 Interface를 둔다.

---

# 47. Memory Interface

Agent가 특정 Database를 직접 호출하지 않는다.

```text
Agent
   ↓
Memory Interface
   ↓
Memory Manager
   ↓
Storage / Index
```

예:

```text
remember()
search()
retrieve()
update()
archive()
forget()
explain()
```

단, 실제 API는 후속 Specification에서 결정한다.

---

# 48. Memory vs Knowledge Base

Knowledge와 Memory는 완전히 동일하지 않다.

초기 구분:

```text
Memory
= 경험과 개인/프로젝트의 지속적인 변화

Knowledge
= 구조화된 사실과 정보
```

Knowledge가 외부 자료에서 온 것일 수도 있고 Memory가 경험에서 파생될 수도 있다.

그러나 실제 저장 구조는 일부 공유할 수 있다.

---

# 49. Memory and Identity

NOAH의 장기 Identity가 형성되기 위해서는 Memory와 Identity가 연결될 가능성이 높다.

```text
Experience
 ↓
Memory
 ↓
Persistent Self Model
 ↓
Identity Continuity
```

하지만 Identity를 Memory의 단순 합으로 정의하지 않는다.

Identity Architecture는 향후 별도의 Review가 필요하다.

---

# 50. Memory and Learning

Learning은 Memory와 관계가 깊지만 동일하지 않다.

```text
Memory
= 무엇을 기억하는가

Learning
= 기억을 기반으로 행동을 어떻게 개선하는가
```

따라서:

```text
Experience
 ↓
Memory
 ↓
Evaluation
 ↓
Learning Signal
 ↓
Skill / Policy / Harness Improvement
```

구조를 장기 후보로 둔다.

---

# 51. Experience-driven Memory

2026년 연구 흐름에서는 Memory를 단순한 저장이 아니라 **Experience → Reflection → Experience abstraction**으로 발전시키는 관점이 나타난다.

NOAH의 장기 방향:

```text
Experience
 ↓
Episodic Evidence
 ↓
Reflection
 ↓
Lesson
 ↓
Memory
 ↓
Future Behavior
```

---

# 52. Memory-driven Self Improvement

최종적으로 NOAH가 경험을 통해 발전하려면:

```text
Experience
 ↓
Memory
 ↓
Evaluation
 ↓
Lesson
 ↓
Skill / Workflow / Harness Update
 ↓
Future Execution
 ↓
New Experience
```

Cycle을 검토한다.

이 구조는 현재 구현하지 않는다.

장기 Architecture 후보로만 둔다.

---

# 53. What NOAH Should Not Do

## Memory = Vector DB

Reject.

## 모든 Conversation을 Long-Term Memory로 저장

Reject.

## 모든 Memory를 Context에 넣기

Reject.

## 자동 Consolidation을 모든 Episode에 적용

Reject as default.

## Memory를 검증 없는 Truth로 취급

Reject.

## Memory를 Agent 내부 변수로만 관리

Reject.

## Forgetting을 단순 DB 삭제로 처리

Reject.

---

# 54. Candidate Decisions

| 주제                       | 초기 판단            |
| ------------------------ | ---------------- |
| Memory ≠ Vector DB       | Adopt            |
| Memory Lifecycle         | Adopt            |
| Episodic Memory          | Adopt            |
| Semantic Memory          | Adopt            |
| Procedural Memory        | Research Further |
| Working Memory           | Adopt            |
| Raw Episode Preservation | Adopt            |
| Candidate Memory         | Adopt            |
| Provenance               | Adopt            |
| Confidence / Trust       | Adapt            |
| Contradiction Handling   | Adopt            |
| Temporal Memory          | Adopt            |
| Forgetting               | Adopt            |
| Archive before Delete    | Adapt            |
| Gated Consolidation      | Adopt            |
| Memory Retrieval Layer   | Adopt            |
| Git-backed Memory        | Research Further |
| Graph Memory             | Research Further |
| Multi-modal Memory       | Defer            |
| Shared Agent Memory      | Research Further |
| Memory Defragmentation   | Research Further |
| Sleep-time Reflection    | Research Further |
| Learned Memory Policy    | Defer            |
| Memory-as-Policy         | Research Further |
| Memory Evaluation        | Adopt            |
| Memory Poisoning Defense | Research Further |
| User Memory Controls     | Adopt            |
| Memory Rollback          | Research Further |

---

# 55. Future Resilience

Memory Architecture는 특정 저장 기술에 종속되지 않는다.

```text
❌ NOAH는 Qdrant를 Memory로 사용한다.

✅ NOAH는 Retrieval / Storage Interface를 정의한다.
```

```text
❌ NOAH는 Neo4j를 Knowledge Graph로 사용한다.

✅ NOAH는 Relationship-aware Knowledge Interface를 정의한다.
```

```text
❌ NOAH의 Memory는 현재의 Vector RAG 방식이다.

✅ NOAH의 Memory는 현재 구현보다 상위의
   Write / Manage / Read 계약을 가진다.
```

미래에 새로운 Memory architecture가 등장해도 Storage layer만 교체할 수 있어야 한다.

---

# 56. Architecture Risks

## Memory Pollution

불필요한 정보가 계속 쌓일 수 있다.

## Memory Drift

오래된 사실이 현재 현실과 달라질 수 있다.

## False Consolidation

Reflection 과정에서 원본보다 잘못된 Memory가 만들어질 수 있다.

## Retrieval Failure

올바른 Memory가 있어도 검색되지 않을 수 있다.

## Over-Retrieval

필요하지 않은 Memory가 Context를 오염시킬 수 있다.

## Contradictions

서로 충돌하는 Memory가 계속 누적될 수 있다.

## Privacy

민감한 정보가 오래 남을 수 있다.

## Storage Cost

Memory가 커지면서 검색과 관리 비용이 증가할 수 있다.

## Maintenance Complexity

Consolidation, forgetting, provenance, versioning이 모두 필요하면 시스템이 지나치게 복잡해질 수 있다.

---

# 57. Open Questions

1. Memory Unit의 최소 단위는 무엇인가?
2. Episode와 Memory의 정확한 경계는 무엇인가?
3. 어떤 경험을 Memory Candidate로 승격할 것인가?
4. Memory를 누가 작성할 것인가?
5. Agent가 직접 Memory를 수정할 수 있는가?
6. Memory Write는 별도 Policy를 거쳐야 하는가?
7. Raw Experience를 얼마나 오래 보존할 것인가?
8. Consolidation은 언제 실행할 것인가?
9. Consolidation 결과를 어떻게 검증할 것인가?
10. Memory Conflict는 어떻게 해결하는가?
11. Memory의 신뢰도는 어떻게 계산하는가?
12. Memory가 오래되어도 원본 Evidence는 보존할 것인가?
13. Forgetting은 어떤 기준으로 수행하는가?
14. Memory Scope는 User / Project / Agent / Task 중 어떻게 구분하는가?
15. 여러 Agent가 Memory를 공유할 수 있는가?
16. 공유 Memory에 어떤 Permission이 필요한가?
17. Memory와 Knowledge Base를 어디서 분리하는가?
18. Memory는 Git-backed filesystem으로 관리할 가치가 있는가?
19. Vector + Graph + Structured + Files를 동시에 유지할 필요가 있는가?
20. Sleep-time reflection을 언제 수행하는가?
21. Memory defragmentation은 자동화할 것인가?
22. Memory가 Agent Identity 형성에 어떻게 연결되는가?
23. Memory에서 얻은 Lesson이 Skill이나 Harness를 어떻게 바꾸는가?
24. Memory 자체의 품질을 지속적으로 평가할 수 있는가?
25. Memory Poisoning을 어떻게 방지하는가?

---

# 58. Current Recommendation

현재까지의 연구를 기반으로 다음 방향을 가장 유력한 후보로 둔다.

> **NOAH Memory는 단순 Retrieval Store가 아니라 Experience를 보존하고, 관리하고, 검증하고, 필요할 때 지식과 행동 개선으로 연결하는 독립적인 시스템이다.**

핵심 Cycle:

```text
Experience
    ↓
Episodic Evidence
    ↓
Candidate Memory
    ↓
Validation
    ↓
Memory Store
    ↓
Manage / Revise
    ↓
Retrieve
    ↓
Context
    ↓
Future Action
    ↓
New Experience
```

또한:

> **Raw episodic evidence는 장기적으로 보존할 가치가 있으며, consolidation은 자동 실행이 아니라 검증 가능한 gated operation으로 취급한다.**

이는 최근 연구에서 continual consolidation이 오히려 Memory 품질을 악화시킬 수 있다는 결과와도 부합한다.

---

# 59. Long-Term NOAH Direction

NOAH의 장기 목표와 연결하면 Memory는 다음과 같이 발전할 수 있다.

```text
Experience
 ↓
Memory
 ↓
Reflection
 ↓
Knowledge
 ↓
Skill / Procedure
 ↓
Behavior Improvement
 ↓
Better Experience
```

더 장기적으로는:

```text
Experience
 ↓
Memory
 ↓
Learning
 ↓
Harness Improvement
 ↓
Better Agent
 ↓
Better Experience
```

의 순환 구조를 목표로 할 수 있다.

Letta가 2026년에 Memory-first harness, Context Repository, memory reflection, skill learning, memory model 등을 한 축으로 발전시키고 있다는 점은 이 방향이 단순한 이론만은 아니라는 것을 보여준다.

---

# 60. Review Boundary

이번 Review에서는 다음을 최종 결정하지 않는다.

* PostgreSQL / Qdrant / Neo4j / Redis 등 구체적인 Storage
* 최종 Embedding Model
* Retrieval Algorithm
* Graph Schema
* Memory API
* Memory Database Schema
* Learning Algorithm
* Identity Architecture
* Final Memory Consolidation Algorithm

이들은 이후 Specification과 PoC에서 검증한다.

---

# 61. Review Outcome

현재까지의 Research를 종합하면:

```text
Memory
≠ Storage
≠ Vector DB
≠ Conversation History
≠ Context
≠ Knowledge Base
```

Memory는:

```text
Capture
+
Selection
+
Persistence
+
Management
+
Retrieval
+
Revision
+
Forgetting
+
Evaluation
```

을 포함하는 **독립적인 lifecycle system**으로 정의하는 것이 가장 유력하다.

특히 장기 NOAH를 고려하면:

```text
Raw Experience
+
Structured Memory
+
Evidence
+
Provenance
+
Versioning
```

을 함께 고려하는 것이 중요하다.

---

# 62. Next Step

Memory Review 이후 바로 구현에 들어가지 않는다.

다음 순서:

```text
Memory Review
      ↓
Open Questions
      ↓
필요한 추가 Research
      ↓
DDR
      ↓
02-Architecture
      ↓
Memory PoC
      ↓
Evaluation
```

다음 Architecture Review에서는 **Capability / Tools / Skills / Workflow / Protocol**의 경계를 검토한다.

특히 Memory와 Capability가 장기적으로 어떻게 연결되는지:

```text
Experience
 ↓
Memory
 ↓
Lesson
 ↓
Skill
 ↓
Future Action
```

을 함께 검토한다.
