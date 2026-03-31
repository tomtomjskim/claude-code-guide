// API Service - Claude Code 전문가 튜토리얼
// Express 없이 Node.js 내장 http 모듈만 사용

const http = require('http');
const { readData, writeData } = require('./db');
const { parseBody, sendJson, sendError } = require('./utils');

const PORT = 3000;

const routes = {
  'GET /api/users': async (req, res) => {
    const users = await readData('users');
    sendJson(res, users);
  },

  'GET /api/users/:id': async (req, res, params) => {
    const users = await readData('users');
    const user = users.find(u => u.id === parseInt(params.id));
    if (!user) return sendError(res, 404, 'User not found');
    sendJson(res, user);
  },

  'POST /api/users': async (req, res) => {
    const body = await parseBody(req);
    if (!body.name || !body.email) {
      return sendError(res, 400, 'name and email are required');
    }

    const users = await readData('users');
    const newUser = {
      id: users.length > 0 ? Math.max(...users.map(u => u.id)) + 1 : 1,
      name: body.name,
      email: body.email,
      createdAt: new Date().toISOString()
    };
    users.push(newUser);
    await writeData('users', users);
    sendJson(res, newUser, 201);
  },

  'DELETE /api/users/:id': async (req, res, params) => {
    const users = await readData('users');
    const index = users.findIndex(u => u.id === parseInt(params.id));
    if (index === -1) return sendError(res, 404, 'User not found');

    users.splice(index, 1);
    await writeData('users', users);
    sendJson(res, { message: 'Deleted' });
  }
};

function matchRoute(method, url) {
  for (const [pattern, handler] of Object.entries(routes)) {
    const [routeMethod, routePath] = pattern.split(' ');
    if (method !== routeMethod) continue;

    const routeParts = routePath.split('/');
    const urlParts = url.split('?')[0].split('/');

    if (routeParts.length !== urlParts.length) continue;

    const params = {};
    let match = true;

    for (let i = 0; i < routeParts.length; i++) {
      if (routeParts[i].startsWith(':')) {
        params[routeParts[i].slice(1)] = urlParts[i];
      } else if (routeParts[i] !== urlParts[i]) {
        match = false;
        break;
      }
    }

    if (match) return { handler, params };
  }
  return null;
}

const server = http.createServer(async (req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    return res.end();
  }

  const route = matchRoute(req.method, req.url);

  if (route) {
    try {
      await route.handler(req, res, route.params);
    } catch (err) {
      console.error('Error:', err.message);
      sendError(res, 500, 'Internal Server Error');
    }
  } else {
    sendError(res, 404, 'Not Found');
  }
});

server.listen(PORT, () => {
  console.log(`API Server running at http://localhost:${PORT}`);
});
