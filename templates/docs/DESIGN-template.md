---
version: "0.1.0"
name: "[PROJECT_NAME]"
description: "[One sentence design system summary]"
colors:
  primary: "#111827"
  secondary: "#6B7280"
  accent: "#2563EB"
  background: "#FFFFFF"
  surface: "#F9FAFB"
  text: "#111827"
  muted: "#6B7280"
  border: "#E5E7EB"
typography:
  h1:
    fontFamily: "[Display Font]"
    fontSize: "2.5rem"
    fontWeight: "700"
    lineHeight: "1.1"
  body:
    fontFamily: "[Body Font]"
    fontSize: "1rem"
    fontWeight: "400"
    lineHeight: "1.6"
  label:
    fontFamily: "[Body Font]"
    fontSize: "0.875rem"
    fontWeight: "600"
    lineHeight: "1.4"
rounded:
  sm: "4px"
  md: "8px"
  lg: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: "12px 16px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
---

# DESIGN.md

## Overview

[제품/프로젝트가 주어야 하는 첫 인상, 사용 맥락, 시각 밀도, 디자인 철학을 3-5문장으로 적는다.]

## Colors

| Token | Value | Role |
|---|---:|---|
| `primary` | `#111827` | 핵심 텍스트와 강한 대비 |
| `secondary` | `#6B7280` | 보조 텍스트, 메타 정보 |
| `accent` | `#2563EB` | 주요 CTA, focus, 활성 상태 |
| `background` | `#FFFFFF` | 기본 배경 |
| `surface` | `#F9FAFB` | 카드, 패널, 구획 배경 |
| `border` | `#E5E7EB` | 구분선, input border |

## Typography

- Display: [브랜드/화면 성격에 맞는 제목 폰트]
- Body: [긴 읽기와 한글/영문 혼용에 적합한 본문 폰트]
- 숫자/데이터: [필요 시 tabular number 또는 mono 기준]
- 금지: [프로젝트에 맞지 않는 폰트/과한 letter-spacing/모바일 줄바꿈 위험]

## Layout

- Grid:
- Container:
- Section spacing:
- Information density:
- Mobile behavior:

## Elevation & Depth

- 기본 surface는 그림자보다 border와 배경 차이를 우선한다.
- Shadow는 hover, popover, modal처럼 계층 변화가 필요한 경우에만 쓴다.
- 장식용 gradient, blur, blob은 프로젝트 성격에 맞을 때만 허용한다.

## Shapes

- 기본 radius:
- 버튼 radius:
- 카드 radius:
- 입력 필드 radius:
- 예외:

## Components

### Button

- Primary:
- Secondary:
- Destructive:
- Disabled:
- Loading:
- Focus:

### Card

- 사용 목적:
- padding:
- border:
- hover:
- 내부 중첩 금지 기준:

### Input

- Label:
- Placeholder:
- Error:
- Focus:
- Disabled:

### Navigation

- Desktop:
- Mobile:
- Active state:
- Overflow:

## Responsive Behavior

| Viewport | Behavior |
|---|---|
| Mobile | [390px 기준 핵심 행동, header/footer, 줄바꿈] |
| Tablet | [2열/단일열 전환 기준] |
| Desktop | [container max, density, side navigation 여부] |

## Agent Prompt Guide

에이전트는 UI 작업 전 이 파일을 먼저 읽고 다음 순서로 판단한다.

1. 기존 토큰으로 해결 가능한지 확인한다.
2. 불가능한 경우 신규 토큰을 제안하고 사용 위치를 적는다.
3. 컴포넌트는 기존 스타일을 먼저 따른다.
4. `UX_CONCEPT.md`, `IA.md`, `UI_SPEC.md`가 있으면 그 결정을 우선한다.
5. 구현 후 접근성, 반응형, 토큰 일관성을 확인한다.

## Do's and Don'ts

### Do

- [프로젝트에 맞는 UI 판단 3-7개]

### Don't

- [금지할 시각 패턴, 컴포넌트 사용, 레이아웃 습관 3-7개]

## Version Notes

| Version | Date | Change |
|---|---|---|
| `0.1.0` | YYYY-MM-DD | Initial DESIGN.md |
