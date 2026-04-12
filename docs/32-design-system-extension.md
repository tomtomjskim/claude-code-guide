# 디자인 시스템 확장 규칙

## 개요

기존 디자인 시스템에 새 토큰을 추가하거나 기존 토큰 값을 변경할 때의 절차입니다. CREATIVE 모드 산출물이 기존 시스템과 충돌 없이 통합되도록 합니다.

---

**관련 문서**:
- [듀얼 모드 디자인 전략](31-design-strategy.md)
- Designer 에이전트 프롬프트: `prompts/designer.md`

---

## 1. 확장 유형

| 유형 | 설명 | 위험도 | 승인 |
|------|------|--------|------|
| **토큰 추가** | 새 CSS 변수 추가 (예: `--accent-warm`) | 낮음 | Designer 판단 |
| **토큰 값 변경** | 기존 토큰 값 수정 (예: `--primary: #3B82F6 → #2563EB`) | 중간 | 사용자 확인 필수 |
| **토큰 제거** | 사용 중인 토큰 삭제 | 높음 | 영향 분석 + 사용자 확인 |
| **스케일 변경** | spacing/typography 스케일 체계 변경 | 높음 | 전체 리뷰 필요 |

---

## 2. 토큰 추가 절차

### 2.1 추가 전 확인

```
1. 기존 토큰으로 표현 가능한가? → 가능하면 추가하지 않는다
2. 시맨틱 이름이 명확한가? → --color-warm (X) → --accent-warm (O)
3. 기존 명명 규칙과 일치하는가? → --primary, --primary-dark 패턴 유지
4. 반대 모드(다크/라이트)에서도 유효한가?
```

### 2.2 Extension Spec 형식

```markdown
## Design System Extension: [이름]

### 추가 토큰
| 토큰명 | 값 | 용도 | 사용 위치 |
|--------|-----|------|----------|
| --accent-warm | #F97316 | 강조 CTA, 핫딜 표시 | 랜딩 히어로, 가격 태그 |

### 기존 토큰과의 관계
- --primary (#3B82F6)과 보색 관계로 시각적 대비 형성
- --warning (#F59E0B)과 유사하나, 경고가 아닌 긍정적 강조 용도

### 영향 범위
- 신규 추가이므로 기존 컴포넌트에 영향 없음
- 적용 대상: LandingHero, PriceTag, PromoBadge (신규 컴포넌트)
```

---

## 3. 토큰 값 변경 절차

### 3.1 영향 분석 필수

```bash
# 변경 대상 토큰 사용처 검색
grep -r "var(--primary)" src/ --include="*.tsx" --include="*.css" -l

# Tailwind 유틸리티 사용처 (custom config 기준)
grep -r "bg-primary\|text-primary\|border-primary" src/ -l
```

### 3.2 변경 Spec 형식

```markdown
## Design System Change: [토큰명]

### 변경 내용
| 토큰 | 현재값 | 제안값 | 이유 |
|------|--------|--------|------|
| --primary | #3B82F6 | #2563EB | 명도 대비 강화, WCAG AAA 충족 |

### 영향 분석
- 사용 파일: 23개
- 주요 컴포넌트: Button, Link, Badge, Input focus ring
- 시각적 변화: Blue 500 → Blue 600 (약간 어두움)

### 검증 항목
- [ ] 모든 사용처에서 명도 대비 4.5:1 유지
- [ ] 다크 모드에서 가독성 확인 (해당 시)
- [ ] hover/focus 상태 색상 연쇄 조정 (--primary-dark도 변경 필요 여부)
```

---

## 4. 폰트 변경/추가 규칙

### 시스템 폰트 변경

```
1. 로딩 성능 영향 평가 (웹폰트 크기, subset 가능 여부)
2. 한글/영문 혼용 렌더링 테스트
3. 기존 font-size 스케일과의 호환성 (x-height 차이)
4. 라이선스 확인 (SIL OFL, Apache 2.0 등)
```

### CREATIVE 모드 폰트 선택

CREATIVE 모드에서 새 폰트를 제안할 때:
- Display + Body 페어링 필수 (동일 폰트 금지)
- Google Fonts 또는 자체 호스팅 가능한 폰트만
- variable font 우선 (파일 크기 최적화)
- 한글 지원 필수: Pretendard, SUIT, Wanted Sans, Noto Sans KR 중 택 1 + 영문 display 폰트

---

## 5. 금지 사항

- 토큰 정의 파일 외 위치에서 CSS 변수 재정의 금지
- `!important`로 토큰 값 오버라이드 금지
- 컴포넌트 로컬 스코프에서 글로벌 토큰명 재사용 금지 (예: 컴포넌트 내 `--primary` 재정의)
- 토큰 제거 시 deprecated 기간 없이 즉시 삭제 금지 (최소 1 릴리스 유지)

---

## 다음 단계

1. [듀얼 모드 디자인 전략](31-design-strategy.md) — 전체 디자인 워크플로우
2. [하네스 엔지니어링 가이드](29-harness-engineering.md) — Design Gate Hook 상세
