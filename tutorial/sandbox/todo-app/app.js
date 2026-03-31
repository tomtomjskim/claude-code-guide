// Todo App - Claude Code 개발자 튜토리얼
// 의도적으로 몇 가지 개선 포인트가 있습니다

let todos = [];
let currentFilter = 'all';

function addTodo() {
  const input = document.getElementById('todoInput');
  const text = input.value.trim();

  if (!text) return;

  todos.push({
    id: Date.now(),
    text: text,
    done: false
  });

  input.value = '';
  render();
}

function toggleTodo(id) {
  const todo = todos.find(t => t.id === id);
  if (todo) {
    todo.done = !todo.done;
    render();
  }
}

function deleteTodo(id) {
  todos = todos.filter(t => t.id !== id);
  render();
}

function filterTodos(filter) {
  currentFilter = filter;

  document.querySelectorAll('.filter').forEach(btn => {
    btn.classList.remove('active');
  });
  event.target.classList.add('active');

  render();
}

function getFilteredTodos() {
  switch (currentFilter) {
    case 'active':
      return todos.filter(t => !t.done);
    case 'done':
      return todos.filter(t => t.done);
    default:
      return todos;
  }
}

function render() {
  const list = document.getElementById('todoList');
  const filtered = getFilteredTodos();

  list.innerHTML = filtered.map(todo => `
    <li class="todo-item ${todo.done ? 'done' : ''}">
      <input
        type="checkbox"
        class="todo-checkbox"
        ${todo.done ? 'checked' : ''}
        onchange="toggleTodo(${todo.id})"
      >
      <span class="todo-text">${todo.text}</span>
      <button class="todo-delete" onclick="deleteTodo(${todo.id})">×</button>
    </li>
  `).join('');

  // 통계 업데이트
  document.getElementById('totalCount').textContent = todos.length;
  document.getElementById('doneCount').textContent = todos.filter(t => t.done).length;
}

// Enter 키로 추가
document.getElementById('todoInput').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') addTodo();
});

// 초기 샘플 데이터
todos = [
  { id: 1, text: 'Claude Code 설치하기', done: true },
  { id: 2, text: 'CLAUDE.md 작성하기', done: false },
  { id: 3, text: '/dispatch 사용해보기', done: false }
];
render();
