function switchTab(tab) {
  document.querySelectorAll('.auth-tab').forEach((t,i) => t.classList.toggle('active', (tab==='login'&&i===0)||(tab==='register'&&i===1)));
  document.getElementById('login-form').classList.toggle('active', tab==='login');
  document.getElementById('register-form').classList.toggle('active', tab==='register');
}

function doRegister() {
  const name = document.getElementById('reg-name').value.trim();
  const email = document.getElementById('reg-email').value.trim().toLowerCase();
  const pass = document.getElementById('reg-pass').value;
  const msg = document.getElementById('reg-msg');
  if (!name || !email || !pass) { msg.textContent='Please fill in all fields.'; msg.className='auth-msg error'; return; }
  if (pass.length < 6) { msg.textContent='Password must be at least 6 characters.'; msg.className='auth-msg error'; return; }
  const users = getUsers();
  if (users[email]) { msg.textContent='An account with this email already exists.'; msg.className='auth-msg error'; return; }
  users[email] = { name, email, pass };
  saveUsers(users);
  msg.textContent='Account created! You can now sign in.'; msg.className='auth-msg success';
  setTimeout(() => switchTab('login'), 1200);
}

function doLogin() {
  const email = document.getElementById('login-email').value.trim().toLowerCase();
  const pass = document.getElementById('login-pass').value;
  const msg = document.getElementById('login-msg');
  const users = getUsers();
  if (!users[email] || users[email].pass !== pass) {
    msg.textContent='Incorrect email or password.'; msg.className='auth-msg error'; return;
  }
  msg.textContent = ''; // Clear error message on successful login
  setSession(users[email]);
  document.getElementById('nav-avatar').textContent = users[email].name.charAt(0).toUpperCase();
  document.getElementById('main-nav').classList.add('visible');
  showPage('home');
}

function logout() {
  clearSession();
  document.getElementById('main-nav').classList.remove('visible');
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('auth-page').classList.add('active');
}