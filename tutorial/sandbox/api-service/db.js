// 간단한 JSON 파일 기반 데이터 저장소
const fs = require('fs').promises;
const path = require('path');

const DATA_DIR = path.join(__dirname, 'data');

async function ensureDataDir() {
  try {
    await fs.mkdir(DATA_DIR, { recursive: true });
  } catch (err) {
    // 이미 존재하면 무시
  }
}

async function readData(collection) {
  await ensureDataDir();
  const filePath = path.join(DATA_DIR, `${collection}.json`);

  try {
    const raw = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(raw);
  } catch (err) {
    // 파일이 없으면 초기 데이터 반환
    if (collection === 'users') {
      const initial = [
        { id: 1, name: '김튜토', email: 'tuto@example.com', createdAt: '2026-01-01T00:00:00Z' },
        { id: 2, name: '이클로드', email: 'claude@example.com', createdAt: '2026-01-02T00:00:00Z' }
      ];
      await writeData(collection, initial);
      return initial;
    }
    return [];
  }
}

async function writeData(collection, data) {
  await ensureDataDir();
  const filePath = path.join(DATA_DIR, `${collection}.json`);
  await fs.writeFile(filePath, JSON.stringify(data, null, 2), 'utf-8');
}

module.exports = { readData, writeData };
