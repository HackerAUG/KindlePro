const express = require('express');
const cors = require('cors');
const crypto = require('crypto');
const db = require('./db');

const app = express();
app.use(cors());
app.use(express.json());

const LONG = (v, n) => String(v || '').slice(0, n);
const sha = (pw, salt) => crypto.createHash('sha256').update(salt + ':' + pw).digest('hex');

function clientIp(req) {
  return (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.socket.remoteAddress;
}

async function userFrom(req) {
  const h = req.headers.authorization || '';
  const token = h.replace(/^Bearer /, '');
  if (!token) return null;
  const r = await db.query(
    'SELECT u.* FROM tokens t JOIN users u ON u.id=t.user_id WHERE t.token=$1', [token]);
  return r.rows[0] || null;
}

async function auth(req, res, next) {
  const u = await userFrom(req);
  if (!u) return res.status(401).json({ error: 'login required' });
  req.user = u;
  await db.query('INSERT INTO ip_logs(user_id, ip) VALUES($1,$2)', [u.id, clientIp(req)]);
  next();
}

async function adminOnly(req, res, next) {
  await auth(req, res, async () => {
    if (req.user.role !== 'admin') return res.status(403).json({ error: 'admin only' });
    next();
  });
}

function canPost(u, res) {
  if (u.banned) { res.status(403).json({ error: 'you are banned' }); return false; }
  return true;
}

// ---------- Auth ----------
app.post('/api/register', async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) return res.status(400).json({ error: 'username + password required' });
  const salt = crypto.randomBytes(8).toString('hex');
  const hash = sha(password, salt);
  try {
    const count = await db.query('SELECT COUNT(*)::int c FROM users');
    const role = count.rows[0].c === 0 ? 'admin' : 'user'; // first user is admin
    const r = await db.query('INSERT INTO users(username,salt,hash,role) VALUES($1,$2,$3,$4) RETURNING id',
      [LONG(username, 20), salt, hash, role]);
    const token = crypto.randomBytes(16).toString('hex');
    await db.query('INSERT INTO tokens(token,user_id) VALUES($1,$2)', [token, r.rows[0].id]);
    res.json({ token, role });
  } catch (e) { res.status(400).json({ error: 'username taken' }); }
});

app.post('/api/login', async (req, res) => {
  const { username, password } = req.body;
  const r = await db.query('SELECT * FROM users WHERE username=$1', [LONG(username, 20)]);
  const u = r.rows[0];
  if (!u || u.hash !== sha(password || '', u.salt)) return res.status(401).json({ error: 'bad login' });
  const token = crypto.randomBytes(16).toString('hex');
  await db.query('INSERT INTO tokens(token,user_id) VALUES($1,$2)', [token, u.id]);
  await db.query('INSERT INTO ip_logs(user_id,ip) VALUES($1,$2)', [u.id, clientIp(req)]);
  res.json({ token, role: u.role, banned: u.banned });
});

app.get('/api/me', async (req, res) => {
  const u = await userFrom(req);
  res.json(u ? { username: u.username, role: u.role, banned: u.banned } : null);
});

// ---------- Chat (login required) ----------
app.get('/api/chat', auth, async (req, res) => {
  const r = await db.query('SELECT * FROM chat ORDER BY id DESC LIMIT 30');
  res.json(r.rows.reverse());
});
app.post('/api/chat', auth, async (req, res) => {
  if (!canPost(req.user, res)) return;
  const { msg } = req.body;
  if (!msg) return res.status(400).json({ error: 'empty' });
  await db.query('INSERT INTO chat(name,msg) VALUES($1,$2)', [req.user.username, LONG(msg, 500)]);
  res.json({ ok: true });
});

// ---------- Topics ----------
app.get('/api/topics', auth, async (req, res) => {
  const r = await db.query('SELECT * FROM topics ORDER BY id DESC'); res.json(r.rows);
});
app.post('/api/topics', auth, async (req, res) => {
  if (!canPost(req.user, res)) return;
  const { name, description } = req.body;
  if (!name) return res.status(400).json({ error: 'name required' });
  const r = await db.query('INSERT INTO topics(name,creator,description) VALUES($1,$2,$3) RETURNING *',
    [LONG(name, 40), req.user.username, LONG(description, 200)]);
  res.json(r.rows[0]);
});
app.get('/api/topics/:id', auth, async (req, res) => {
  const r = await db.query('SELECT * FROM topics WHERE id=$1', [req.params.id]); res.json(r.rows[0] || null);
});
app.get('/api/topics/:id/messages', auth, async (req, res) => {
  const r = await db.query('SELECT * FROM topic_msgs WHERE topic_id=$1 ORDER BY id DESC LIMIT 30', [req.params.id]);
  res.json(r.rows.reverse());
});
app.post('/api/topics/:id/messages', auth, async (req, res) => {
  if (!canPost(req.user, res)) return;
  const { msg } = req.body;
  if (!msg) return res.status(400).json({ error: 'empty' });
  await db.query('INSERT INTO topic_msgs(topic_id,name,msg) VALUES($1,$2,$3)', [req.params.id, req.user.username, LONG(msg, 500)]);
  res.json({ ok: true });
});

// ---------- Board ----------
app.get('/api/threads', auth, async (req, res) => {
  const r = await db.query(`SELECT t.*, (SELECT COUNT(*) FROM replies WHERE thread_id=t.id)::int AS replies FROM threads t ORDER BY t.id DESC`);
  res.json(r.rows);
});
app.post('/api/threads', auth, async (req, res) => {
  if (!canPost(req.user, res)) return;
  const { title, body } = req.body;
  if (!title) return res.status(400).json({ error: 'title required' });
  const r = await db.query('INSERT INTO threads(title,author,body) VALUES($1,$2,$3) RETURNING *',
    [LONG(title, 60), req.user.username, LONG(body, 1000)]);
  res.json(r.rows[0]);
});
app.get('/api/threads/:id', auth, async (req, res) => {
  const t = await db.query('SELECT * FROM threads WHERE id=$1', [req.params.id]);
  const r = await db.query('SELECT * FROM replies WHERE thread_id=$1 ORDER BY id', [req.params.id]);
  res.json({ thread: t.rows[0] || null, replies: r.rows });
});
app.post('/api/threads/:id/replies', auth, async (req, res) => {
  if (!canPost(req.user, res)) return;
  const { body } = req.body;
  if (!body) return res.status(400).json({ error: 'empty' });
  await db.query('INSERT INTO replies(thread_id,author,body) VALUES($1,$2,$3)', [req.params.id, req.user.username, LONG(body, 1000)]);
  res.json({ ok: true });
});

// ---------- Admin / moderation ----------
app.get('/api/admin/users', adminOnly, async (req, res) => {
  const r = await db.query(`SELECT u.username, u.role, u.banned, u.created_at,
    (SELECT ip FROM ip_logs WHERE user_id=u.id ORDER BY id DESC LIMIT 1) AS last_ip
    FROM users u ORDER BY u.id`);
  res.json(r.rows);
});
app.post('/api/admin/ban', adminOnly, async (req, res) => {
  await db.query('UPDATE users SET banned=$1 WHERE username=$2', [!!req.body.banned, LONG(req.body.username, 20)]);
  res.json({ ok: true });
});
app.get('/api/admin/ips', adminOnly, async (req, res) => {
  const r = await db.query(
    `SELECT i.ip, i.ts FROM ip_logs i JOIN users u ON u.id=i.user_id WHERE u.username=$1 ORDER BY i.id DESC LIMIT 50`,
    [LONG(req.query.username, 20)]);
  res.json(r.rows);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log('KindlePro API on port ' + PORT));
