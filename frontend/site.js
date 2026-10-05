function refreshUser(){
  api('/api/me', null, function(u){
    var el = document.getElementById('userbox'); if(!el) return;
    el.innerHTML = (u && u.username)
      ? 'Logged in as <b>' + esc(u.username) + '</b><br>' + esc(u.role) + (u.banned?' (BANNED)':'') +
        '<br><a href="admin.html">Admin</a><br><a href="#" onclick="logout();return false">Logout</a>'
      : '<a href="login.html">Login</a><br><a href="register.html">Register</a>';
  });
}
function logout(){ setToken(''); location.href = 'index.html'; }
refreshUser();
