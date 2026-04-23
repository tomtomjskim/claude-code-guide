# 도구 동시성 & 실행 모델

## 개요

Claude Code는 도구(Tool)의 성격에 따라 병렬 실행이 가능한 것과 반드시 직렬로 실행해야 하는 것을 구분합니다.
이 구분을 이해하고 활용하면 작업 속도를 크게 향상시킬 수 있습니다.

---

## 1. 병렬 안전(Concurrent-safe) 도구

다음 도구들은 동시에 여러 번 호출해도 상태 충돌이 없으므로 병렬 실행이 가능합니다.

| 도구 | 설명 | 병렬 활용 예시 |
|------|------|--------------|
| `Read` | 파일 읽기 | 여러 파일을 동시에 읽기 |
| `Grep` | 패턴 검색 | 여러 디렉토리를 동시에 검색 |
| `Glob` | 파일 패턴 탐색 | 복수의 패턴을 동시에 탐색 |
| `Agent` | 서브에이전트 스폰 | 복수의 에이전트를 한 턴에 스폰 |
| `WebSearch` | 웹 검색 | 여러 쿼리를 동시에 검색 |
| `WebFetch` | URL 가져오기 | 여러 URL을 동시에 fetch |
| `ToolSearch` | 도구 검색 | 복수의 검색 동시 실행 |

### 병렬 실행 상한

```
CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=10  (기본값)
```

한 번에 최대 10개의 병렬 안전 도구를 동시에 실행할 수 있습니다. 이 값을 넘는 요청은 큐에서 대기합니다.

---

## 2. 직렬 전용(Sequential-only) 도구

다음 도구들은 파일시스템 상태를 변경하거나 프로세스를 실행하기 때문에 순서를 지켜야 합니다.

| 도구 | 설명 | 주의사항 |
|------|------|---------|
| `Bash` | 쉘 명령 실행 | 이전 명령 결과에 의존할 수 있음 |
| `Write` | 파일 전체 덮어쓰기 | 동시 쓰기 시 데이터 손실 위험 |
| `Edit` | 파일 일부 수정 | 동일 파일 동시 수정 시 충돌 |
| `NotebookEdit` | Jupyter 셀 수정 | 셀 순서/상태 의존성 |

> 직렬 전용 도구를 병렬로 호출하면 내부적으로 직렬 큐에서 순서대로 처리됩니다.
> 동일 파일에 대한 `Edit`/`Write` 호출은 반드시 순차적으로 수행해야 합니다.

---

## 3. 성능 최적화 팁

### 3.1 읽기 작업은 항상 병렬로

나쁜 예 (직렬):
```
Read file_a → Read file_b → Read file_c → 분석
```

좋은 예 (병렬):
```
Read file_a
Read file_b      (동시 실행)
Read file_c
    ↓
분석
```

여러 파일을 탐색할 때는 한 번의 응답에서 모든 Read/Grep/Glob 호출을 묶어서 요청하면 됩니다.

### 3.2 Bash 명령은 `&&`로 체이닝

불필요한 왕복을 줄이려면 Bash 명령을 하나의 호출로 합칩니다.

```bash
# 나쁜 예: 3번의 Bash 호출
npm install
npm run build
npm test

# 좋은 예: 1번의 Bash 호출
npm install && npm run build && npm test
```

앞 명령이 실패하면 `&&` 체인이 중단되므로 에러 감지도 자동으로 이루어집니다.

### 3.3 복수의 Agent를 한 턴에 스폰

`Agent` 도구는 병렬 안전이므로 한 턴에 여러 서브에이전트를 동시에 스폰할 수 있습니다.

```
한 턴에서:
  Agent("백엔드 API 구현")
  Agent("프론트엔드 컴포넌트 구현")   (동시 실행)
  Agent("테스트 케이스 작성")
```

각 에이전트는 독립적인 컨텍스트에서 실행되며, 모든 에이전트가 완료된 후 결과를 수집합니다.

---

## 4. 서브에이전트 동시성

`Agent` 도구는 동시성 모델에서 특별한 위치를 차지합니다.

### 4.1 Agent는 항상 병렬 안전

- 각 `Agent` 호출은 완전히 독립된 프로세스로 실행됩니다.
- 에이전트 간 공유 메모리가 없으므로 경쟁 조건(race condition)이 발생하지 않습니다.
- 단, 에이전트들이 **동일 파일**을 수정하는 경우에는 결과가 덮어써질 수 있으니 작업 범위를 명확히 분리해야 합니다.

### 4.2 한 턴에 여러 에이전트 스폰 패턴

```
오케스트레이터 에이전트
    │
    ├─ Agent A: src/api/users.ts 작업
    ├─ Agent B: src/api/products.ts 작업   (동시)
    └─ Agent C: src/components/Header.tsx 작업
```

이 패턴을 사용할 때는 각 에이전트의 **작업 파일 범위**가 겹치지 않도록 지시해야 합니다.

### 4.3 동시성 한도와 에이전트 수

`CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=10` 기본값 기준으로,
한 턴에 최대 10개의 에이전트를 동시에 스폰하는 것이 최적입니다.
그 이상은 큐에 대기하므로 실질적 속도 이득이 감소합니다.

---

## 5. 동시성 설정 변경

```bash
# 환경변수로 최대 동시성 변경
export CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=5   # 낮추면 메모리 절약
export CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=15  # 높이면 처리량 증가 (리소스 주의)
```

또는 `settings.json`에서 환경변수로 영구 설정:
```json
{
  "env": {
    "CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY": "10"
  }
}
```

---

## 6. 실행 모델 요약

```
도구 호출 요청
    │
    ▼
병렬 안전 여부 판단
    │
    ├─ 병렬 안전 (Read/Grep/Glob/Agent/WebSearch/WebFetch/ToolSearch)
    │       │
    │       ▼
    │   동시 실행 풀 (최대 10개)
    │       │
    │       ▼
    │   모두 완료 후 결과 반환
    │
    └─ 직렬 전용 (Bash/Write/Edit/NotebookEdit)
            │
            ▼
        직렬 큐 (순서대로 실행)
            │
            ▼
        완료 후 다음 도구 실행
```

---

## 관련 문서

- [환경변수 레퍼런스](17-environment-variables.md) - `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY` 포함 전체 환경변수
- [Agent Frontmatter 스키마](22-agent-frontmatter-schema.md) - Agent 도구 설정 옵션
- [Coordinator Mode](26-coordinator-mode.md) - 고급 멀티에이전트 오케스트레이션
