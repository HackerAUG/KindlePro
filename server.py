#!/usr/bin/env python3
"""KindlePro - a lightweight enhancement site for Kindle browsers.
Zero JS, basic HTML, small pages. stdlib only."""
import os, sqlite3, random, string, html, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

DB = os.path.join(os.path.dirname(__file__), "kindlepro.db")
PORT = int(os.environ.get("PORT", "8080"))

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS chat(id INTEGER PRIMARY KEY, name TEXT, msg TEXT, ts TEXT);
    CREATE TABLE IF NOT EXISTS topics(id INTEGER PRIMARY KEY, name TEXT, desc TEXT, creator TEXT, ts TEXT);
    CREATE TABLE IF NOT EXISTS topic_msgs(id INTEGER PRIMARY KEY, topic_id INTEGER, name TEXT, msg TEXT, ts TEXT);
    CREATE TABLE IF NOT EXISTS threads(id INTEGER PRIMARY KEY, title TEXT, author TEXT, body TEXT, ts TEXT);
    CREATE TABLE IF NOT EXISTS replies(id INTEGER PRIMARY KEY, thread_id INTEGER, author TEXT, body TEXT, ts TEXT);
    CREATE TABLE IF NOT EXISTS hangman(gid TEXT PRIMARY KEY, word TEXT, guessed TEXT, wrong INTEGER, over INTEGER);
    CREATE TABLE IF NOT EXISTS numgame(gid TEXT PRIMARY KEY, num INTEGER, tries INTEGER, over INTEGER);
    """)
    c.commit(); c.close()

def esc(s): return html.escape(str(s), quote=True)
def now(): return time.strftime("%m/%d %H:%M")

WORDS = ["kindle","book","page","story","chapter","author","novel","paper","shelf","library","poem","essay","writer","quote","reader"]
QUOTES = ["A reader lives a thousand lives before he dies. - George R.R. Martin",
          "So many books, so little time. - Frank Zappa",
          "There is no friend as loyal as a book. - Hemingway",
          "Reading is to the mind what exercise is to the body. - Addison",
          "A book is a dream that you hold in your hand. - Neil Gaiman"]
WOTD = [("ubiquitous","present everywhere"),("serene","calm and peaceful"),("ephemeral","lasting a short time"),("luminous","full of light"),("resilient","able to recover quickly"),("curious","eager to learn")]

CSS = """body{font-family:Georgia,serif;background:#f4f1e8;color:#222;margin:0;padding:0}
#wrap{max-width:640px;margin:0 auto;padding:8px;background:#fffdf5}
h1{font-size:20px;border-bottom:2px solid #888;padding-bottom:4px}
h2{font-size:16px}
a{color:#0645ad}
#nav{background:#ddd6c0;padding:6px;font-size:14px;text-align:center}
#nav a{margin:0 6px;text-decoration:none}
.msg{border-bottom:1px dotted #bbb;padding:4px 0;font-size:14px}
input,textarea,select{font-size:14px;width:90%;padding:4px;margin:2px 0}
button,input[type=submit]{width:auto;padding:4px 10px;font-size:14px}
table{border-collapse:collapse}
td,th{border:1px solid #999;padding:4px 8px;font-size:14px;text-align:center}
.small{font-size:12px;color:#666}
"""

def page(title, body, refresh=None):
    meta = '<meta http-equiv="refresh" content="%d">' % refresh if refresh else ""
    nav = ('<a href="/">Home</a>|<a href="/chat">Chat</a>|<a href="/topics">Topics</a>|'
           '<a href="/board">Board</a>|<a href="/games">Games</a>|<a href="/tools">Tools</a>')
    return ('<html><head><meta charset="utf-8">%s<title>%s - KindlePro</title>'
            '<style>%s</style></head><body><div id="wrap"><div id="nav">%s</div>'
            '<h1>%s</h1>%s<hr><p class="small">KindlePro</p></div></body></html>'
            % (meta, esc(title), CSS, nav, esc(title), body))

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, s, code=200):
        b = s.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def _redir(self, loc):
        self.send_response(303); self.send_header("Location", loc); self.end_headers()
    def args(self):
        return {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
    def spath(self): return urlparse(self.path).path

    # ---------- GET ----------
    def do_GET(self):
        p, a = self.spath(), self.args()
        try:
            if p == "/": return self.home()
            if p == "/chat": return self.chat(a)
            if p == "/topics": return self.topics()
            if p == "/topic": return self.topic(a)
            if p == "/board": return self.board()
            if p == "/thread": return self.thread(a)
            if p == "/games": return self.games()
            if p == "/hangman": return self.hangman(a)
            if p == "/guess": return self.guess(a)
            if p == "/tictactoe": return self.ttt(a)
            if p == "/rps": return self.rps(a)
            if p == "/tools": return self.tools()
            if p == "/calc": return self.calc(a)
            if p == "/readtime": return self.readtime(a)
            if p == "/convert": return self.convert(a)
            if p == "/quote": return self.quote()
            return self._send(page("404", "<p>Not found.</p>"), 404)
        except Exception as e:
            return self._send(page("Error", "<p>%s</p>" % esc(e)), 500)

    # ---------- POST ----------
    def do_POST(self):
        p = self.spath()
        n = int(self.headers.get("Content-Length", 0))
        a = {k: v[0] for k, v in parse_qs(self.rfile.read(n).decode("utf-8")).items()}
        c = db()
        if p == "/chat":
            c.execute("INSERT INTO chat(name,msg,ts) VALUES(?,?,?)", (a.get("name","anon")[:20], a.get("msg","")[:500], now()))
            c.commit(); c.close(); return self._redir("/chat")
        if p == "/topics":
            if a.get("name"):
                c.execute("INSERT INTO topics(name,desc,creator,ts) VALUES(?,?,?,?)", (a["name"][:40], a.get("desc","")[:200], a.get("creator","anon")[:20], now()))
            c.commit(); c.close(); return self._redir("/topics")
        if p == "/topic":
            c.execute("INSERT INTO topic_msgs(topic_id,name,msg,ts) VALUES(?,?,?,?)", (a.get("id"), a.get("name","anon")[:20], a.get("msg","")[:500], now()))
            c.commit(); c.close(); return self._redir("/topic?id=" + str(a.get("id","")))
        if p == "/board":
            if a.get("title"):
                c.execute("INSERT INTO threads(title,author,body,ts) VALUES(?,?,?,?)", (a["title"][:60], a.get("author","anon")[:20], a.get("body","")[:1000], now()))
            c.commit(); c.close(); return self._redir("/board")
        if p == "/thread":
            c.execute("INSERT INTO replies(thread_id,author,body,ts) VALUES(?,?,?,?)", (a.get("id"), a.get("author","anon")[:20], a.get("body","")[:1000], now()))
            c.commit(); c.close(); return self._redir("/thread?id=" + str(a.get("id","")))
        c.close()
        return self._redir("/")

    # ---------- Pages ----------
    def home(self):
        idx = time.localtime().tm_yday % len(WOTD)
        w, d = WOTD[idx]
        b = ("<p>Welcome to KindlePro, a site made for Kindle browsers. No JavaScript needed!</p>"
             "<h2>Word of the Day</h2><p><b>%s</b>: %s</p>"
             "<h2>Quick Links</h2><ul>"
             "<li><a href='/chat'>Main Chat Room</a> - refresh to see new messages</li>"
             "<li><a href='/topics'>Topics</a> - create your own rooms</li>"
             "<li><a href='/board'>Board</a> - classic topic/reply threads</li>"
             "<li><a href='/games'>Games</a></li><li><a href='/tools'>Useful Tools</a></li></ul>"
             % (w, d))
        self._send(page("Home", b))

    def chat(self, a):
        c = db()
        rows = c.execute("SELECT * FROM chat ORDER BY id DESC LIMIT 30").fetchall()
        c.close()
        msgs = "".join('<div class="msg"><b>%s</b> <span class="small">(%s)</span>: %s</div>'
                       % (esc(r["name"]), r["ts"], esc(r["msg"])) for r in rows) or "<p>No messages yet. Say hi!</p>"
        form = ('<form method="post" action="/chat">Name:<br><input name="name" maxlength="20"><br>'
                'Message:<br><textarea name="msg" rows="3"></textarea><br><input type="submit" value="Send"></form>')
        self._send(page("Main Chat", msgs + "<hr>" + form, refresh=20))

    def topics(self):
        c = db()
        rows = c.execute("SELECT * FROM topics ORDER BY id DESC").fetchall()
        c.close()
        lst = "".join('<div class="msg"><a href="/topic?id=%d"><b>%s</b></a> <span class="small">by %s</span><br><span class="small">%s</span></div>'
                       % (r["id"], esc(r["name"]), esc(r["creator"]), esc(r["desc"])) for r in rows) or "<p>No topics yet.</p>"
        form = ('<h2>Create a Topic</h2><form method="post" action="/topics">'
                'Name:<br><input name="name" maxlength="40"><br>Your name:<br><input name="creator" maxlength="20"><br>'
                'About:<br><input name="desc" maxlength="200"><br><input type="submit" value="Create"></form>')
        self._send(page("Topics", lst + "<hr>" + form))

    def topic(self, a):
        c = db()
        t = c.execute("SELECT * FROM topics WHERE id=?", (a.get("id"),)).fetchone()
        if not t: c.close(); return self._send(page("Topics", '<p>Not found. <a href="/topics">Back</a></p>'))
        rows = c.execute("SELECT * FROM topic_msgs WHERE topic_id=? ORDER BY id DESC LIMIT 30", (a.get("id"),)).fetchall()
        c.close()
        msgs = "".join('<div class="msg"><b>%s</b> <span class="small">(%s)</span>: %s</div>'
                       % (esc(r["name"]), r["ts"], esc(r["msg"])) for r in rows) or "<p>No messages yet.</p>"
        form = ('<form method="post" action="/topic"><input type="hidden" name="id" value="%s">'
                'Name:<br><input name="name" maxlength="20"><br>Message:<br><textarea name="msg" rows="3"></textarea><br>'
                '<input type="submit" value="Post"></form>' % esc(a.get("id","")))
        self._send(page("Topic: " + t["name"], '<p class="small">%s</p>' % esc(t["desc"]) + msgs + "<hr>" + form, refresh=15))

    def board(self):
        c = db()
        rows = c.execute("SELECT t.*, (SELECT COUNT(*) FROM replies WHERE thread_id=t.id) n FROM threads t ORDER BY id DESC").fetchall()
        c.close()
        lst = "".join('<div class="msg"><a href="/thread?id=%d"><b>%s</b></a> <span class="small">by %s, %d replies</span></div>'
                       % (r["id"], esc(r["title"]), esc(r["author"]), r["n"]) for r in rows) or "<p>No threads yet.</p>"
        form = ('<h2>New Thread</h2><form method="post" action="/board">Title:<br><input name="title" maxlength="60"><br>'
                'Your name:<br><input name="author" maxlength="20"><br>Body:<br><textarea name="body" rows="4"></textarea><br>'
                '<input type="submit" value="Post Thread"></form>')
        self._send(page("Board", lst + "<hr>" + form))

    def thread(self, a):
        c = db()
        t = c.execute("SELECT * FROM threads WHERE id=?", (a.get("id"),)).fetchone()
        if not t: c.close(); return self._send(page("Board", '<p>Not found. <a href="/board">Back</a></p>'))
        rows = c.execute("SELECT * FROM replies WHERE thread_id=? ORDER BY id", (a.get("id"),)).fetchall()
        c.close()
        out = '<div class="msg"><b>%s</b> <span class="small">by %s (%s)</span><p>%s</p></div>' % (
            esc(t["title"]), esc(t["author"]), t["ts"], esc(t["body"]))
        out += "".join('<div class="msg"><b>%s</b> <span class="small">(%s)</span>: %s</div>'
                       % (esc(r["author"]), r["ts"], esc(r["body"])) for r in rows)
        form = ('<form method="post" action="/thread"><input type="hidden" name="id" value="%s">'
                'Your name:<br><input name="author" maxlength="20"><br>Reply:<br><textarea name="body" rows="3"></textarea><br>'
                '<input type="submit" value="Reply"></form>' % esc(a.get("id","")))
        self._send(page("Thread", out + "<hr>" + form))

    def games(self):
        b = ("<ul><li><a href='/hangman'>Hangman</a></li><li><a href='/guess'>Guess the Number</a></li>"
             "<li><a href='/tictactoe'>Tic-Tac-Toe</a></li><li><a href='/rps'>Rock Paper Scissors</a></li></ul>")
        self._send(page("Games", b))

    def hangman(self, a):
        c = db(); gid = a.get("g", "default")
        g = c.execute("SELECT * FROM hangman WHERE gid=?", (gid,)).fetchone()
        if g and a.get("new"):
            c.execute("DELETE FROM hangman WHERE gid=?", (gid,)); c.commit(); g = None
        if not g:
            g_row = (gid, random.choice(WORDS), "", 0, 0)
            c.execute("INSERT INTO hangman VALUES(?,?,?,?,?)", g_row); c.commit()
            g = c.execute("SELECT * FROM hangman WHERE gid=?", (gid,)).fetchone()
        if a.get("l") and not g["over"]:
            l = a["l"][0].lower(); guessed = g["guessed"] + l
            wrong = g["wrong"] + (0 if l in g["word"] else 1)
            won = all(ch in guessed for ch in g["word"])
            over = 1 if (wrong >= 6 or won) else 0
            c.execute("UPDATE hangman SET guessed=?, wrong=?, over=? WHERE gid=?", (guessed, wrong, over, gid))
            c.commit()
            g = c.execute("SELECT * FROM hangman WHERE gid=?", (gid,)).fetchone()
        c.close()
        shown = " ".join(ch if ch in g["guessed"] else "_" for ch in g["word"])
        stage = ["o---<br>|<br>/ \\","o---<br>|<br>/","o---<br>|<br>","o<br>|<br>","o<br>|","o",""][max(0, 6-g["wrong"])]
        links = " ".join("<a href='/hangman?l=%s'>%s</a>" % (l, l) for l in string.ascii_lowercase if l not in g["guessed"])
        status = ""
        if g["over"]:
            status = "<p><b>You win!</b></p>" if all(ch in g["guessed"] for ch in g["word"]) else "<p><b>Game over!</b> Word: %s</p>" % g["word"]
        b = ("<pre style='font-size:16px'>%s</pre><p>%s</p><p>Wrong guesses: %d/6</p>%s<p>%s</p>"
             "<p><a href='/hangman?new=1'>New game</a></p>" % (stage, shown, g["wrong"], status, links))
        self._send(page("Hangman", b))

    def guess(self, a):
        c = db(); gid = "default"
        g = c.execute("SELECT * FROM numgame WHERE gid=?", (gid,)).fetchone()
        if g and a.get("new"):
            c.execute("DELETE FROM numgame WHERE gid=?", (gid,)); c.commit(); g = None
        if not g:
            c.execute("INSERT INTO numgame VALUES(?,?,?,?)", (gid, random.randint(1, 50), 0, 0)); c.commit()
            g = c.execute("SELECT * FROM numgame WHERE gid=?", (gid,)).fetchone()
        msg = ""
        if a.get("n") and not g["over"]:
            try: n = int(a["n"]); tries = g["tries"] + 1
            except ValueError: n, tries = -1, g["tries"]
            if n == g["num"]:
                c.execute("UPDATE numgame SET tries=?, over=1 WHERE gid=?", (tries, gid)); msg = "<p><b>Correct! It was %d. Tries: %d</b></p>" % (g["num"], tries); g = c.execute("SELECT * FROM numgame WHERE gid='default'").fetchone(); c.commit()
            elif n > 0:
                c.execute("UPDATE numgame SET tries=? WHERE gid=?", (tries, gid)); c.commit()
                msg = "<p>%s!</p>" % ("Too high" if n > g["num"] else "Too low")
                g = c.execute("SELECT * FROM numgame WHERE gid='default'").fetchone()
        c.close()
        form = ('<form method="get" action="/guess">Guess (1-50):<br><input name="n" type="text" maxlength="3">'
                '<input type="submit" value="Guess"></form><p>Tries: %d</p>' % g["tries"])
        self._send(page("Guess the Number", msg + form + "<p><a href='/guess?new=1'>New game</a></p>"))

    def ttt(self, a):
        board = list(a.get("b", "---------"))[:9]
        board = board + ["-"] * (9 - len(board))
        turn = a.get("t", "X")
        msg = ""
        if a.get("m") is not None and a.get("m").isdigit() and board[int(a["m"])] == "-":
            board[int(a["m"])] = turn
            turn = "O" if turn == "X" else "X"
        winner = None
        lines = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for x,y,z in lines:
            if board[x] != "-" and board[x] == board[y] == board[z]: winner = board[x]
        b = ""
        for i in range(3):
            row = []
            for j in range(3):
                k = i*3+j
                if board[k] == "-" and not winner:
                    row.append('<a href="/tictactoe?b=%s&t=%s&m=%d">_</a>' % ("".join(board), turn, k))
                else:
                    row.append(board[k] if board[k] != "-" else " ")
            b += "<tr><td>" + "</td><td>".join(row) + "</td></tr>"
        if winner: msg = "<p><b>%s wins!</b></p>" % winner
        elif "-" not in board: msg = "<p><b>Draw!</b></p>"
        else: msg = "<p>Turn: %s</p>" % turn
        self._send(page("Tic-Tac-Toe", '<table>%s</table>%s<p><a href="/tictactoe">Restart</a></p>' % (b, msg)))

    def rps(self, a):
        choices = ["rock","paper","scissors"]
        msg = ""
        if a.get("c") in choices:
            comp = random.choice(choices); you = a["c"]
            win = {"rock":"scissors","paper":"rock","scissors":"paper"}
            result = "You win!" if win[you] == comp else ("Draw!" if you == comp else "You lose!")
            msg = "<p>You: %s vs Computer: %s - <b>%s</b></p>" % (you, comp, result)
        b = msg + ("<p><a href='/rps?c=rock'>Rock</a> | <a href='/rps?c=paper'>Paper</a> | <a href='/rps?c=scissors'>Scissors</a></p>")
        self._send(page("Rock Paper Scissors", b))

    def tools(self):
        b = ("<ul><li><a href='/calc'>Calculator</a></li><li><a href='/readtime'>Reading Time Estimator</a></li>"
             "<li><a href='/convert'>Unit Converter</a></li><li><a href='/quote'>Random Quote</a></li></ul>")
        self._send(page("Tools", b))

    def calc(self, a):
        result = ""
        try:
            x, y, op = float(a.get("a","")), float(a.get("b","")), a.get("op","+")
            r = {"+": x+y, "-": x-y, "*": x*y, "/": x/y if y else "err"}[op]
            result = "<p><b>Result: %s</b></p>" % r
        except (ValueError, KeyError): pass
        form = ('<form method="get" action="/calc"><input name="a" maxlength="15" placeholder="number"> '
                '<select name="op"><option>+</option><option>-</option><option>*</option><option>/</option></select> '
                '<input name="b" maxlength="15" placeholder="number"> <input type="submit" value="="></form>')
        self._send(page("Calculator", form + result))

    def readtime(self, a):
        result = ""
        if a.get("w"):
            try:
                w = int(a["w"].replace(",", "")); result = "<p><b>About %d minutes</b> (at 200 wpm)</p>" % max(1, round(w/200))
            except ValueError: result = "<p>Enter a number of words.</p>"
        form = ('<form method="get" action="/readtime">Word count:<br><input name="w" maxlength="10">'
                '<input type="submit" value="Estimate"></form>')
        self._send(page("Reading Time", form + result))

    def convert(self, a):
        result = ""
        try:
            v, t = float(a.get("v","")), a.get("t")
            convs = {"km_mi": v*0.6214, "mi_km": v*1.609, "kg_lb": v*2.205, "lb_kg": v*0.4536, "c_f": v*9/5+32, "f_c": (v-32)*5/9}
            if t in convs: result = "<p><b>%g</b></p>" % convs[t]
        except ValueError: pass
        opts = "".join('<option value="%s">%s</option>' % (k, k.replace("_"," -> ")) for k in ["km_mi","mi_km","kg_lb","lb_kg","c_f","f_c"])
        form = '<form method="get" action="/convert"><input name="v" maxlength="15"> <select name="t">%s</select> <input type="submit" value="Convert"></form>' % opts
        self._send(page("Converter", form + result))

    def quote(self):
        self._send(page("Quote", '<p><i>"%s"</i></p><p><a href="/quote">Another</a></p>' % esc(random.choice(QUOTES))))

if __name__ == "__main__":
    init_db()
    print("KindlePro running at http://localhost:%d" % PORT)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
