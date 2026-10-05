function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
var TOKEN = null;
try { TOKEN = localStorage.getItem('kp_token'); } catch(e) {}
function setToken(t){ TOKEN = t; try { localStorage.setItem('kp_token', t); } catch(e) {} }
function api(path, data, cb){
  var x = new XMLHttpRequest();
  x.open(data ? 'POST' : 'GET', API + path, true);
  x.setRequestHeader('Content-Type', 'application/json');
  if (TOKEN) x.setRequestHeader('Authorization', 'Bearer ' + TOKEN);
  x.onreadystatechange = function(){
    if (x.readyState === 4) {
      var out; try { out = JSON.parse(x.responseText); } catch(e){ out = null; }
      if (x.status === 401) { location.href = 'login.html'; return; }
      cb(out);
    }
  };
  x.send(data ? JSON.stringify(data) : null);
}
function qs(name){
  var m = location.search.match(new RegExp('[?&]' + name + '=([^&]*)'));
  return m ? decodeURIComponent(m[1]) : '';
}
