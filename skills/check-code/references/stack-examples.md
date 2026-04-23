# check-code: Stack별 예시 카탈로그

`skills/check-code/SKILL.md`의 각 `<!-- CUSTOMIZE -->` 블록은 PHP/MySQL(기본)만 보여줍니다. 다른 기술 스택 예시를 이곳에서 참조하세요.

**지원 스택**: PHP/MySQL (기본, SKILL.md 인라인), React/TypeScript, Python/Django, Node.js/TypeScript

---

## File Discovery

### React + Express

- `src/components/{Feature}/*.tsx`
- `src/api/{feature}/*.ts`
- `src/styles/{feature}.module.css`

### Django

- `{app}/models.py`, `views.py`, `serializers.py`, `urls.py`
- `{app}/templates/{app}/*.html`
- `{app}/static/{app}/*.css`

---

## Syntax Check Commands

### TypeScript

```bash
npx tsc --noEmit {file}
npx eslint {file}
```

### Python

```bash
python -m py_compile {file}
flake8 {file}
mypy {file}
```

---

## Required Structure

### React Component

- `export default` 필수
- PropTypes 또는 TypeScript 타입 정의

### React Hook

- `use*` prefix 필수
- return value 명시

### Django View

- `permission_classes` 지정
- `serializer_class` 지정

### Django Model

- `__str__` 메서드 구현
- `Meta` class 정의

---

## Language Version Compatibility

### Node.js 18+

- [ ] ES2022 features only
- [ ] No experimental APIs

### Python 3.8+

- [ ] No walrus operator if targeting 3.7
- [ ] No match/case if targeting < 3.10

---

## Security Patterns

### Node.js — Parameterized Queries

- [ ] SQL: parameterized queries (no string concatenation)
- [ ] Input: express-validator 또는 joi validation
- [ ] Output: helmet, CORS configuration

### Django ORM

- [ ] ORM 사용 (no raw SQL without parameterization)
- [ ] CSRF token in forms
- [ ] XSS: `mark_safe` only when explicitly safe

---

## API Call Patterns

### React / fetch

- [ ] API base URL from environment variable
- [ ] Error handling with try/catch
- [ ] Loading state management

### Vue / axios

- [ ] axios instance with interceptors
- [ ] Proper error handling

---

## UI Dialog Patterns

### React

- [ ] Modal component usage (no native `alert`/`confirm`)
- [ ] Toast notifications via context/hook

---

## Style Rules

### TailwindCSS

3.1 Custom CSS 최소화: `@apply` 사용 시 확인
3.2 Design token 준수: 커스텀 값 대신 Tailwind 클래스
3.3 Responsive: `sm`/`md`/`lg` breakpoint 적용

### CSS Modules

3.1 Naming: camelCase export
3.2 No global styles
3.3 Variables from theme

---

## SQL Security Pattern

### Node.js — Parameterized Queries

```javascript
// OK: db.query('SELECT * FROM table WHERE id = ?', [id])
// BAD: db.query(`SELECT * FROM table WHERE id = ${id}`)
```

- [ ] Parameterized queries 사용
- [ ] No string interpolation in queries

### Django ORM

- [ ] ORM 사용 (raw SQL 최소화)
- [ ] `raw()` 사용 시 `params=` 필수

---

## Reference Documents

### React DDD

```
src/.claude/ui_style_guide.md       - UI 스타일 가이드
src/.claude/coding_guidelines.md    - 코딩 규칙
src/.claude/spec_review_checklist.md - 설계 검수 체크리스트
src/.claude/checklists/coding_rules.md - 통합 코딩 규칙 체크리스트
```

### Django

```
{project}/.claude/ui_style_guide.md
{project}/.claude/coding_guidelines.md
{project}/.claude/spec_review_checklist.md
```
