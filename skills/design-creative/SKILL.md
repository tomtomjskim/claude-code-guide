---
name: design-creative
description: 창의적 프론트엔드 디자인 — 공식 frontend-design 미학 원칙으로 방향 수립 후 프로젝트 토큰으로 매핑
---

# /design-creative

새 프로젝트, 랜딩페이지, 프로토타입 등 기존 디자인 시스템에 얽매이지 않는 창의적 UI 설계가 필요할 때 사용한다.

## 사용 시점
- 신규 프로젝트 첫 UI 설계
- 랜딩페이지, 마케팅 페이지
- 프로토타입/PoC UI
- 리브랜딩, 대규모 디자인 리뉴얼
- 사용자가 "새로운 느낌", "creative", "bold" 등 요청

## 사용하지 않을 때
- 기존 디자인 시스템이 있는 프로젝트의 일반 UI 수정 → `/design` 사용
- 버그 수정, 컴포넌트 미세 조정 → designer 에이전트 직접 활용

## 실행 절차

### Phase 1: 컨텍스트 파악
1. 목적: 이 인터페이스가 해결하는 문제는?
2. 대상: 누가 사용하는가?
3. 제약: 프레임워크, 성능, 접근성 요구사항
4. 차별점: 사용자가 기억할 한 가지는?

### Phase 2: 미학 방향 수립 (Creative)
공식 frontend-design 원칙 적용:
- **톤 선택**: brutally minimal / maximalist / retro-futuristic / organic / luxury / playful / editorial / brutalist / art deco / soft-pastel / industrial 중 택 1
- **타이포그래피**: 맥락에 맞는 개성 있는 폰트 페어링 (display + body)
- **색상**: 강한 주조색 + 날카로운 액센트. 소극적 팔레트 금지
- **모션**: 고효과 순간 집중 — 페이지 로드 staggered reveal, scroll-triggered, hover surprise
- **공간**: 비대칭, 겹침, 대각선, 그리드 파괴, 의도적 여백
- **시각적 깊이**: 그라디언트 메시, 노이즈 텍스처, 레이어 투명도, 커스텀 커서

### Phase 3: 토큰 브릿지
Phase 2의 창의적 방향을 구조화된 토큰으로 전환:

```css
/* 신규 프로젝트 토큰 제안 형식 */
:root {
  /* Primary Palette */
  --primary: #{선택한 주조색};
  --primary-dark: #{어두운 변형};
  --accent: #{액센트 색};
  
  /* Typography */
  --font-display: '{display 폰트}', serif;
  --font-body: '{body 폰트}', sans-serif;
  
  /* Spacing Scale */
  --space-unit: 4px;  /* 기본 단위 유지 */
}
```

기존 프로젝트 토큰이 있으면:
- 기존 토큰과 충돌 여부 확인
- 확장이 필요하면 Design System Extension Spec 작성
- 기존 토큰명 유지, 값만 변경 제안

### Phase 4: 구현 산출물
1. **Design Direction Document**: 미학 방향 + 레퍼런스 + 톤 설명
2. **Token Spec**: CSS 변수 정의서 (신규 또는 확장)
3. **Component Spec**: 핵심 컴포넌트 3~5개의 상세 스펙
4. **Motion Spec**: 애니메이션/트랜지션 정의 (CSS-only 우선, 필요 시 Motion 라이브러리)

### Phase 5: 검증
- [ ] 선택한 미학이 목적/대상과 일치하는가
- [ ] AI slop 회피 — Inter, Roboto, purple gradient 등 클리셰 없는가
- [ ] 접근성 기본 충족 (명도 대비 4.5:1, 키보드 네비게이션)
- [ ] 토큰이 4px 단위 시스템을 따르는가
- [ ] 반응형 3개 뷰포트 (375px, 768px, 1280px) 고려되었는가

## AI Slop 회피 목록
다음은 절대 사용하지 않는다:
- Inter, Roboto, Arial, system-ui를 유일한 폰트로
- 흰 배경 위 보라색 그라디언트
- 모든 프로젝트에 동일한 카드-그리드 레이아웃
- Space Grotesk 반복 사용
- 의미 없는 장식적 블롭/원 배경
- 기본 Tailwind 색상만으로 구성된 팔레트

## 참조
- 공식 frontend-design 플러그인: anthropics/claude-code plugins/frontend-design
- 기존 designer 에이전트: prompts/designer.md
- 디자인 모드 규칙: .claude/rules/design-mode.md
