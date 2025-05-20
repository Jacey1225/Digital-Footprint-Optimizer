document.getElementById('loginBtn').addEventListener('click', () => {
  // auth logic...

  // show dashboard, hide login

  document.getElementById('loginPage').style.display = 'none';
  document.getElementById('dashboardPage').style.display = 'block';
});

document.getElementById('logoutBtn').addEventListener('click', () => {
  // show login, hide dashboard
  document.getElementById('dashboardPage').style.display = 'none';
  document.getElementById('loginPage').style.display = 'block';
});

document.getElementById('trackBtn').addEventListener('click', () => {
  // show login, hide dashboard
  document.getElementById('dashboardPage').style.display = 'none';
  document.getElementById('loginPage').style.display = 'none';
  document.getElementById('activityPage').style.display = 'block';
});
