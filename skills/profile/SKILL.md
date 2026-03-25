---
name: profile
description: "성능 프로파일링. 코드에 @PROFILE 마커 기반 프로파일링 코드를 삽입하여 실행 시간 측정. /profile clean으로 제거."
---
너는 능숙한 프로젝트 성능 프로파일링 전문가야.

## 역할

코드의 병목 구간을 **화면에 직접 출력하는 프로파일링 코드**를 삽입하여, 실행 시간을 빠르게 측정하고 공유할 수 있게 합니다.

---

## 작업 모드

### 인자 기반 동작
- `/profile [대상파일 또는 기능 설명]` -> 프로파일링 코드 삽입
- `/profile clean` -> 현재 컨텍스트의 모든 프로파일링 코드 제거
- `/profile clean [파일경로]` -> 특정 파일의 프로파일링 코드 제거

---

## 프로파일링 규칙

### 1. 마커 규칙 (CRITICAL)
모든 프로파일링 코드에는 **식별 마커**를 반드시 포함:
- 서버사이드: `/* @PROFILE */` 주석을 같은 줄에 포함
- 클라이언트사이드: `/* @PROFILE */` 주석을 같은 줄에 포함

이유: `/profile clean` 시 마커 기반으로 정확하게 제거 가능

### 2. 제거 방법
```bash
# 마커가 포함된 줄을 찾아서 제거
grep -rn "@PROFILE" [파일경로]
```
마커가 포함된 줄을 삭제하면 프로파일링 코드가 완전히 제거됨

### 3. 절대 금지
- 프로젝트의 디버그 로깅 금지 규칙 준수 (CLAUDE.md 절대 규칙)
- 프로파일링 코드를 커밋하지 않음 (반드시 `/profile clean` 후 스테이징)

---

## 서버사이드 프로파일링 패턴

<!-- CUSTOMIZE: Server-Side Profiling Code
The examples below use PHP's microtime(true) for timing.
Replace with your language's profiling pattern:
- Python: `time.perf_counter()` or `time.time()`
- Node.js: `process.hrtime()` or `performance.now()`
- Go: `time.Now()` / `time.Since()`
- Java: `System.nanoTime()`
- Ruby: `Process.clock_gettime(Process::CLOCK_MONOTONIC)`
The STRUCTURE (page-level, function-level, multi-segment, API) is universal.
-->

### A. 모듈/페이지 레벨 (전체 소요시간)

페이지 상단에 시작점, 하단에 출력부 삽입:

```php
$_pfStart = microtime(true); /* @PROFILE */

// ... 기존 코드 ...

$_pfEnd = microtime(true); /* @PROFILE */
$_pfMs = round(($_pfEnd - $_pfStart) * 1000); /* @PROFILE */
echo "<div style='position:fixed;top:0;left:50%;transform:translateX(-50%);z-index:99999;background:#1a1a2e;color:#0ff;padding:8px 20px;font:bold 13px monospace;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,.5);'>[PF] page: {$_pfMs}ms</div>"; /* @PROFILE */
```

### B. 함수 내부 (쿼리별 측정)

각 쿼리/로직 블록을 개별 측정하고, 함수 끝에서 결과 배열에 포함:

```php
$_pf = []; $_pfT0 = microtime(true); /* @PROFILE */

// 쿼리 1
$_pfT = microtime(true); /* @PROFILE */
$result1 = executeQuery($query1);
$_pf['countQuery'] = round((microtime(true) - $_pfT) * 1000); /* @PROFILE */

// 쿼리 2
$_pfT = microtime(true); /* @PROFILE */
$result2 = executeQuery($query2);
$_pf['dataQuery'] = round((microtime(true) - $_pfT) * 1000); /* @PROFILE */

$_pf['total'] = round((microtime(true) - $_pfT0) * 1000); /* @PROFILE */
return ['data' => $data, 'totalCount' => $count, '_pf' => $_pf]; /* @PROFILE: '_pf' 키 추가 */
```

### C. 결과 출력부 (호출 측)

호출부에서 `_pf` 데이터를 수집하여 출력:

```php
$_pfData = isset($queryResult['_pf']) ? $queryResult['_pf'] : []; /* @PROFILE */
if (!empty($_pfData)) { /* @PROFILE */
    $_pfParts = []; /* @PROFILE */
    foreach ($_pfData as $k => $v) { $_pfParts[] = "{$k}: {$v}ms"; } /* @PROFILE */
    $_pfStr = implode(' | ', $_pfParts); /* @PROFILE */
    echo "<pre style='background:#1a1a2e;color:#0f0;padding:10px 16px;margin:8px 12px;font:13px/1.6 monospace;border-left:4px solid #0f0;border-radius:4px;'>[PF] {$_pfStr}</pre>"; /* @PROFILE */
} /* @PROFILE */
```

### D. 복수 구간 비교 (로직 블록)

```php
$_pfT = microtime(true); /* @PROFILE */
// ... 로직 블록 A ...
$_pfA = round((microtime(true) - $_pfT) * 1000); /* @PROFILE */

$_pfT = microtime(true); /* @PROFILE */
// ... 로직 블록 B ...
$_pfB = round((microtime(true) - $_pfT) * 1000); /* @PROFILE */

echo "<pre style='background:#1a1a2e;color:#0f0;padding:10px 16px;margin:8px 12px;font:13px/1.6 monospace;border-left:4px solid #0f0;border-radius:4px;'>[PF] blockA: {$_pfA}ms | blockB: {$_pfB}ms</pre>"; /* @PROFILE */
```

---

## API 프로파일링 패턴

API 응답에 `_pf` 필드를 추가하여 Network 탭에서 확인:

```php
$_pfT0 = microtime(true); /* @PROFILE */

// ... API 로직 ...

$_pfT = microtime(true); /* @PROFILE */
$queryResult = executeQuery($query);
$_pf['mainQuery'] = round((microtime(true) - $_pfT) * 1000); /* @PROFILE */
$_pf['total'] = round((microtime(true) - $_pfT0) * 1000); /* @PROFILE */

return [
    'result' => 'success',
    'payload' => [ ... ],
    '_pf' => $_pf /* @PROFILE */
];
```

---

## 클라이언트사이드 프로파일링 패턴

### AJAX 호출 측정

```javascript
var _pfStart = performance.now(); /* @PROFILE */
apiPost('some/endpoint', data).then(function(res) {
    var _pfEnd = performance.now(); /* @PROFILE */
    var _pfMs = Math.round(_pfEnd - _pfStart); /* @PROFILE */
    var _pfApi = (res && res._pf) ? JSON.stringify(res._pf) : ''; /* @PROFILE */
    document.body.insertAdjacentHTML('afterbegin', "<div style='position:fixed;top:0;left:50%;transform:translateX(-50%);z-index:99999;background:#1a1a2e;color:#0ff;padding:8px 20px;font:bold 13px monospace;border-radius:0 0 8px 8px;'>[PF] fetch: " + _pfMs + "ms | server: " + _pfApi + "</div>"); /* @PROFILE */
});
```

### 페이지 로드 DOMContentLoaded

```javascript
var _pfDom = performance.now(); /* @PROFILE */
window.addEventListener("DOMContentLoaded", function() { /* @PROFILE */
    var _pfReady = Math.round(performance.now() - _pfDom); /* @PROFILE */
    document.body.insertAdjacentHTML('afterbegin', "<div style='position:fixed;top:30px;left:50%;transform:translateX(-50%);z-index:99999;background:#1a1a2e;color:#ff0;padding:8px 20px;font:bold 13px monospace;border-radius:0 0 8px 8px;'>[PF] DOMReady: " + _pfReady + "ms</div>"); /* @PROFILE */
}); /* @PROFILE */
```

---

## 출력 스타일 가이드

### 색상 체계
| 요소 | 색상 | 용도 |
|------|------|------|
| 배경 | `#1a1a2e` | 다크 네이비 (페이지 디자인과 구분) |
| 서버 측정값 | `#0f0` (그린) | 서버사이드 쿼리/로직 시간 |
| 클라이언트 측정값 | `#0ff` (시안) | 클라이언트 fetch/DOM 시간 |
| 경고 (느린 구간) | `#ff0` (옐로) | 임계값 초과 시 |
| 위험 (매우 느림) | `#f44` (레드) | 심각한 병목 |

### 위치 규칙
- **페이지 레벨**: `position:fixed; top:0` -- 상단 고정 바
- **함수 레벨**: `<pre>` 블록 -- 페이지 콘텐츠 위에 인라인
- **API**: 응답 JSON `_pf` 필드 -- Network 탭에서 확인

### 접두어
모든 출력은 `[PF]` 접두어로 통일:
```
[PF] page: 2340ms
[PF] countQuery: 949ms | dataQuery: 18ms | total: 2695ms
[PF] fetch: 1230ms | server: {"mainQuery": 980, "total": 1100}
```

---

## 작업 프로세스

### 삽입 모드 (`/profile [대상]`)

1. **대상 파일/기능 식별**: 사용자 설명 또는 대화 컨텍스트 기반
2. **측정 포인트 결정**: 쿼리, 루프, 외부 API 호출 등 병목 가능 지점
3. **프로파일링 코드 삽입**: 위 패턴 적용, 모든 줄에 `/* @PROFILE */` 마커
4. **문법 검증**: 문법 오류 없는지 확인
5. **안내 출력**: 삽입 위치, 측정 항목 요약

### 제거 모드 (`/profile clean`)

1. **마커 검색**: `grep -rn "@PROFILE"` 로 대상 파일/줄 확인
2. **제거 실행**: 마커가 포함된 줄 삭제
3. **코드 정합성 확인**: return 문에서 `'_pf'` 키 제거 시 원래 return 복원
4. **문법 검증**
5. **결과 출력**: 제거된 파일/줄 수 요약

---

## 주의사항

- 프로파일링 변수는 `$_pf` 접두어 사용 (기존 변수와 충돌 방지)
- 함수 return 값에 `_pf` 키 추가 시, 호출부에서 해당 키를 사용하지 않더라도 무해함
- 프로파일링 코드는 **임시**이며, 반드시 작업 완료 후 `/profile clean` 실행
- `/stage` 실행 시 `@PROFILE` 마커 잔존 여부를 반드시 체크할 것
