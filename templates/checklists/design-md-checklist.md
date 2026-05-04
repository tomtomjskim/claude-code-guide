# DESIGN.md Checklist

- [ ] 프로젝트 루트에 `DESIGN.md`가 있거나 생성 대상 경로가 명시되어 있다.
- [ ] YAML front matter와 Markdown body가 모두 있다.
- [ ] `version`, `name`, `description`이 있다.
- [ ] 핵심 색상 토큰이 hex 값으로 정의되어 있다.
- [ ] 타이포그래피 토큰이 `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`를 포함한다.
- [ ] spacing/radius/component token이 구현자가 재사용할 수 있는 값으로 정의되어 있다.
- [ ] 컴포넌트별 normal, hover/focus, disabled/loading/error 상태 기준이 있다.
- [ ] 모바일/태블릿/데스크톱 동작이 실제 레이아웃 행동으로 적혀 있다.
- [ ] 접근성 기준이 색 대비, focus, touch target 관점에서 적혀 있다.
- [ ] 기존 프로젝트에서는 현재 CSS 변수/Tailwind theme/component library를 우선 반영했다.
- [ ] 신규 토큰은 추가 이유, 사용 위치, 기존 토큰과의 관계가 적혀 있다.
- [ ] `Do's and Don'ts`가 에이전트가 판단할 수 있을 정도로 구체적이다.
- [ ] 가능하면 `npx @google/design.md lint DESIGN.md`를 실행하고 결과를 남겼다.
- [ ] 변경 시 `Version Notes`와 완료 기록에 변경 유형을 남겼다.
