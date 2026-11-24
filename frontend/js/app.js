/**
 * SmartRail AI+ — Shared UI Utility Functions
 */

function showToast(title, message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div>
      <div class="toast-title">${title}</div>
      <div class="toast-msg">${message}</div>
    </div>
  `;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function checkAuth(redirectIfNotAuth = true) {
  if (!API.isLoggedIn() && redirectIfNotAuth) {
    window.location.href = 'login.html';
    return false;
  }
  return true;
}

function renderSidebarUser() {
  const user = API.getUser();
  const avatarEl = document.getElementById('sidebar-user-avatar');
  const nameEl = document.getElementById('sidebar-user-name');
  const roleEl = document.getElementById('sidebar-user-role');

  if (user) {
    if (avatarEl) avatarEl.textContent = (user.full_name || user.username || 'U').substring(0, 2).toUpperCase();
    if (nameEl) nameEl.textContent = user.full_name || user.username;
    if (roleEl) roleEl.textContent = user.role || 'PASSENGER';
  }
}

function logout() {
  API.clearAuth();
  window.location.href = 'login.html';
}

document.addEventListener('DOMContentLoaded', () => {
  renderSidebarUser();
});
