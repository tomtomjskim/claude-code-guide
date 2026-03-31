# API Service - 전문가 튜토리얼 프로젝트

## 프로젝트 개요
Node.js 내장 http 모듈 기반 REST API 서버. 사용자(User) CRUD.

## 기술 스택
- Node.js (외부 의존성 없음)
- JSON 파일 기반 데이터 저장

## 파일 구조
- `server.js` — HTTP 서버 + 라우팅
- `db.js` — 데이터 읽기/쓰기
- `utils.js` — HTTP 유틸리티
- `data/` — JSON 데이터 파일 (자동 생성)

## API 엔드포인트
- `GET /api/users` — 전체 사용자 목록
- `GET /api/users/:id` — 특정 사용자 조회
- `POST /api/users` — 사용자 생성 (body: name, email)
- `DELETE /api/users/:id` — 사용자 삭제

## 알려진 개선 포인트
- 입력 검증(validation) 최소화
- 테스트 코드 없음
- PUT/PATCH 미구현
- 에러 로깅 기본 수준
- 동시 쓰기 시 race condition 가능
