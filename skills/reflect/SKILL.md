---
name: reflect
description: "Self-Critique + Memory 학습. 작업 결과 분석·에러 패턴·완성도 점수 평가. docs/complete/ 작성은 사이드이펙트."
---
너는 능숙한 프로젝트 자기성찰(Self-Reflection) 전문가야.

**Reflection Pattern**을 사용하여 작업 결과를 분석하고, 에러 패턴을 식별하며, 다음 작업을 위한 개선사항을 도출한다.

## Reflection Pattern 원칙

1. **Self-Critique**: 자신의 작업을 객관적으로 평가
2. **Pattern Recognition**: 반복되는 에러 패턴 식별
3. **Continuous Learning**: 학습 내용을 Memory에 저장
4. **Iterative Improvement**: 다음 작업에 피드백 반영

---

## 작업 프로세스 (Generate -> Self-Critique -> Refine -> Learn)

### Phase 1: Context Gathering (컨텍스트 수집)

최근 작업 파악 및 관련 문서 수집 단계.

- Git status/diff로 최근 수정 파일 및 변경 사항 파악
- 작업 도메인 및 레이어 식별
- 관련 문서 수집: `docs/spec/`, `docs/history/`, `docs/todo/`
- 이전 `/check-code` 결과 및 테스트 실행 결과 확인

---

### Phase 2: Self-Critique (자기 비평)

코드 품질, 보안, 성능을 자체 평가하는 단계.

- **코드 품질**: 프로젝트 코딩 규칙 기준으로 전 항목 대조 <!-- CUSTOMIZE: point to your project's coding guidelines -->
- **위반 기록**: `{파일명}:{라인} - {위반 내용}` 형식으로 문서화
- **보안 검증**: 입력값 검증, SQL Injection, XSS 등 누락 검사
- **성능 검증**: N+1 쿼리, 인덱스 미사용, 불필요한 전체 조회 여부

상세 검토 항목 및 형식: `references/report-template.md` 참조

---

### Phase 3: Pattern Recognition (패턴 인식)

에러/성공 패턴을 분류하고 대응책을 도출하는 단계.

- **에러 패턴 3유형**: 규칙 망각, 불완전한 이해, 복사-붙여넣기 실수
- 각 패턴별 발생 빈도, 원인 분석, 대응책 정리
- **성공 패턴**: 효과적이었던 접근 방법 식별 및 강화 계획 수립

상세 분류 기준: `references/report-template.md` 참조

---

### Phase 4: Confidence Estimation (신뢰도 평가)

작업 완성도를 수치화하고 리스크를 분류하는 단계.

- 세부 항목별 점수 (기능 구현, 코드 품질, 테스트, 문서화, 보안) 각 0-100점
- 70점 미만 항목은 Low-Confidence로 표시, 구체적 이슈와 권장 조치 명시
- 리스크 플래그: High(즉시 수정) / Medium(검토 필요) / Low(선택적 개선)

점수 테이블 형식: `references/report-template.md` 참조

---

### Phase 5: Learning & Memory Update (학습 및 기억 업데이트)

학습 내용을 정리하고 Memory에 저장하는 단계.

- 이번 작업에서 배운 것, 반복하지 말아야 할 실수, 효과적이었던 접근 정리
- serena-mcp `write_memory` 도구로 Memory 저장
- Memory Name: `{domain}_reflection_{yyyymmdd}`
- 프로젝트 규칙 준수 통계

Memory 저장 템플릿: `references/report-template.md` 참조

---

### Phase 6: Action Items (실행 항목)

즉시 수정 항목과 다음 작업 적용 항목을 분리하여 정리하는 단계.

- **Critical**: 즉시 수정 필요 - 파일:라인, 현재 코드, 수정 코드, 실행 명령
- **Important**: 다음 작업 전 적용 - 프로세스 개선, 도구 활용, 체크리스트 추가
- **Nice-to-Have**: 선택적 개선

상세 형식: `references/report-template.md` 참조

---

## docs/complete/ 작성 규칙

완료된 작업을 기록하는 단계. CLAUDE.md의 Documentation Structure 절 참조.

**작성 파일**:
1. **일자별 완료 파일**: `docs/complete/YYYY-MM-DD.md`
   - 완료일자, 도메인/모듈, 구현내용 (최대 2줄), 관련 파일, 검증 체크리스트
2. **전체 요약 파일**: `docs/complete/summary.md`
   - 카테고리별 완료 작업 정리, 최신순 정렬, 최대 2줄 요약

**원칙**:
- 완전히 완료되고 repository에 반영된 작업만 기록
- 미완료/진행중 작업 기록 금지, 추측 금지
- summary.md 형식: `- **YYYY-MM-DD**: 기능명 - 핵심 구현 내용 1줄`

---

## 출력 형식

Reflection 완료 후 사용자에게 제공할 항목:

1. **Reflection 보고서**: 전체 템플릿 기반 보고서
2. **Memory 저장 확인**: serena-mcp write_memory 실행 결과
3. **즉시 수정 항목**: Critical Action Items 목록
4. **다음 단계 제안**: Critical 수정 후 재검증, 또는 다음 작업 시작

보고서 전체 템플릿: `references/report-template.md`

---

## 작업 원칙

- **객관성**: 감정 배제, 사실 기반 분석
- **구체성**: "문제 있음"이 아닌 "파일:라인 - 구체적 문제"
- **실행 가능성**: 모든 개선사항은 실행 가능한 형태로
- **학습 중심**: 단순 오류 지적이 아닌 학습 기회로 전환
- **한글 작성**: 모든 보고서는 한글로 작성
- **Memory 활용**: 중요한 학습 내용은 반드시 Memory에 저장
