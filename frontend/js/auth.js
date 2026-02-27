/* =====================================================
   GRAM-SABHA Authentication & API (DB-backed)
   ===================================================== */

// API base URL (Flask backend); set in one place
const API_BASE = (function() {
    const u = document.querySelector('script[data-api-base]');
    if (u && u.dataset.apiBase) return u.dataset.apiBase.replace(/\/$/, '');
    return 'http://127.0.0.1:5000';
})();

// Session Management
const SESSION_KEY = 'gram_sabha_session';

function saveSession(user) {
    const session = {
        ...user,
        loginTime: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
    };
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

function getSession() {
    const sessionData = localStorage.getItem(SESSION_KEY);
    if (!sessionData) return null;
    const session = JSON.parse(sessionData);
    if (new Date(session.expiresAt) < new Date()) {
        clearSession();
        return null;
    }
    return session;
}

function clearSession() {
    localStorage.removeItem(SESSION_KEY);
}

function isLoggedIn() {
    return getSession() !== null;
}

function getCurrentUser() {
    return getSession();
}

function requireAuth(allowedRoles = null) {
    const user = getCurrentUser();
    if (!user) {
        window.location.href = 'login.html';
        return null;
    }
    if (allowedRoles && !allowedRoles.includes(user.role)) {
        window.location.href = user.redirectUrl || user.redirecturl || (user.role === 'admin' ? 'admin-panel.html' : user.role === 'sarpanch' ? 'sarpanch-portal.html' : 'villager-dashboard.html') || 'index.html';
        return null;
    }
    return user;
}

function logout() {
    clearSession();
    window.location.href = 'index.html';
}

// ---------- API helpers ----------
async function apiGet(path) {
    const res = await fetch(API_BASE + path, { credentials: 'omit' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
}

async function apiPost(path, body) {
    const res = await fetch(API_BASE + path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body || {}),
        credentials: 'omit'
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
}

async function getVillage(villageId) {
    if (!villageId) return null;
    const r = await apiGet('/api/villages/' + villageId);
    return r.data || null;
}

async function getIssues(villageId, userId) {
    let path = '/api/issues?';
    if (villageId) path += 'village_id=' + encodeURIComponent(villageId);
    if (userId) path += (villageId ? '&' : '') + 'user_id=' + encodeURIComponent(userId);
    const r = await apiGet(path);
    return r.data || [];
}

async function getBudget(villageId) {
    const path = villageId ? '/api/budget?village_id=' + encodeURIComponent(villageId) : '/api/budget';
    const r = await apiGet(path);
    return r.data || { totalReceived: 0, totalSpent: 0, pendingApproval: 0, available: 0, fiscalYear: '', projects: [] };
}

async function getActivities(villageId) {
    const path = villageId ? '/api/activities?village_id=' + encodeURIComponent(villageId) : '/api/activities';
    const r = await apiGet(path);
    return r.data || [];
}

async function voteIssue(issueId, userId) {
    const r = await apiPost('/api/issues/' + encodeURIComponent(issueId) + '/vote', { user_id: userId });
    return r;
}

async function createProject(projectData) {
    const r = await apiPost('/api/projects', projectData);
    return r;
}

async function assignProject(projectId, contractorName) {
    const r = await apiPost('/api/projects/' + encodeURIComponent(projectId) + '/assign', { contractor_name: contractorName });
    return r;
}

async function verifyProjectStep(projectId, step, photoUrl) {
    const payload = { step: step };
    if (photoUrl) payload.photo_url = photoUrl;
    const r = await apiPost('/api/projects/' + encodeURIComponent(projectId) + '/verify_step', payload);
    return r;
}

// ---------- Admin API helpers ----------
async function getAdminStats() {
    const r = await apiGet('/api/admin/stats');
    return r.data || { activeVillages: 0, registeredUsers: 0, issuesResolved: 0, totalFundsTracked: 0 };
}

async function getAdminUsers() {
    const r = await apiGet('/api/admin/users');
    return r.data || [];
}

async function getAdminAlerts() {
    const r = await apiGet('/api/admin/alerts');
    return r.data || [];
}

// Role detection for login page (optional: call API to show role before submit)
async function checkMobileRole(mobile) {
    if (!mobile || mobile.length < 10) return null;
    try {
        const r = await apiGet('/api/auth/check-mobile?mobile=' + encodeURIComponent(mobile));
        return r.found ? r : null;
    } catch {
        return null;
    }
}

// Login Handler (calls backend)
async function handleLogin(event) {
    event.preventDefault();
    const userId = document.getElementById('userId').value.trim();
    const password = document.getElementById('password').value.trim();
    const submitBtn = document.getElementById('submitBtn');
    const userIdError = document.getElementById('userIdError');
    const passwordError = document.getElementById('passwordError');

    userIdError.classList.remove('show');
    passwordError.classList.remove('show');
    document.getElementById('userId').classList.remove('error');
    document.getElementById('password').classList.remove('error');

    if (userId.length < 10) {
        document.getElementById('userId').classList.add('error');
        userIdError.textContent = 'Please enter a valid mobile or Aadhaar number (10+ digits).';
        userIdError.classList.add('show');
        return;
    }

    submitBtn.classList.add('loading');
    submitBtn.disabled = true;

    try {
        const res = await apiPost('/api/auth/login', { mobile: userId, password: password });
        if (!res.success || !res.user) {
            document.getElementById('password').classList.add('error');
            passwordError.textContent = res.error || 'Invalid credentials.';
            passwordError.classList.add('show');
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
            return;
        }
        saveSession(res.user);
        var url = res.user.redirectUrl || res.user.redirecturl || { villager: 'villager-dashboard.html', sarpanch: 'sarpanch-portal.html', admin: 'admin-panel.html' }[res.user.role] || 'villager-dashboard.html';
        window.location.href = url;
    } catch (err) {
        document.getElementById('password').classList.add('error');
        passwordError.textContent = err.message || 'Login failed. Check backend is running at ' + API_BASE;
        passwordError.classList.add('show');
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
    }
}

// Role Detection on login page (optional: show role from API when user types mobile)
function detectRole(mobileInput) {
    const roleDetection = document.getElementById('roleDetection');
    const roleIcon = document.getElementById('roleIcon');
    const roleName = document.getElementById('roleName');
    const roleDesc = document.getElementById('roleDesc');
    if (!roleDetection) return;
    const mobile = (typeof mobileInput === 'string' ? mobileInput : (mobileInput && mobileInput.value)) || '';
    if (mobile.length < 10) {
        roleDetection.classList.remove('show');
        return;
    }
    checkMobileRole(mobile).then(function(info) {
        if (!info || !info.found) {
            roleDetection.classList.remove('show');
            return;
        }
        const icons = { villager: 'person', sarpanch: 'gavel', admin: 'admin_panel_settings', csc: 'storefront' };
        const pages = { villager: 'Villager Dashboard', sarpanch: 'Sarpanch Portal', admin: 'Admin Panel', csc: 'CSC Portal' };
        roleDetection.className = 'role-detection show ' + (info.role || '');
        if (roleIcon) roleIcon.textContent = icons[info.role] || 'person';
        if (roleName) roleName.textContent = (info.roleName || info.role) + ' Account Detected';
        if (roleDesc) roleDesc.textContent = 'You\'ll be redirected to ' + (pages[info.role] || 'your dashboard');
    });
}

// Demo Auto-fill (only fills form fields; auth is via API)
function fillDemo(mobile, pin) {
    document.getElementById('userId').value = mobile || '';
    document.getElementById('password').value = pin || '';
    detectRole(mobile);
}

// Biometric Login (simulated: login as first villager from API or show message)
function handleBiometric() {
    if (typeof showNotification === 'function') {
        showNotification('Biometric authentication is simulated. Use mobile + PIN to login.', 'info');
    }
}

// Password Toggle
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.querySelector('.password-toggle');
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        if (toggleIcon) toggleIcon.textContent = 'visibility_off';
    } else {
        passwordInput.type = 'password';
        if (toggleIcon) toggleIcon.textContent = 'visibility';
    }
}

// Notification (fallback if app.js not loaded)
if (typeof showNotification !== 'function') {
    function showNotification(message, type) {
        const n = document.createElement('div');
        n.style.cssText = 'position:fixed;bottom:2rem;right:2rem;padding:1rem 1.5rem;background:#1e293b;color:white;border-radius:0.75rem;font-weight:600;box-shadow:0 10px 40px rgba(0,0,0,0.2);z-index:9999;';
        n.textContent = message;
        document.body.appendChild(n);
        setTimeout(function() { n.remove(); }, 3000);
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount || 0);
}

function formatDate(dateString) {
    if (!dateString) return '';
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-IN', options);
}

function getGreeting() {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
}

// Export for use in other pages
window.GramSabha = {
    API_BASE,
    apiBase: API_BASE,   // alias so GramSabha.apiBase works everywhere
    apiGet,
    apiPost,
    getVillage,
    getIssues,
    getBudget,
    getActivities,
    voteIssue,
    createProject,
    assignProject,
    verifyProjectStep,
    checkMobileRole,
    saveSession,
    getSession,
    clearSession,
    isLoggedIn,
    getCurrentUser,
    requireAuth,
    logout,
    detectRole,
    fillDemo,
    formatCurrency,
    formatDate,
    getGreeting,
    showNotification
};

document.addEventListener('DOMContentLoaded', function() {
    const methodBtns = document.querySelectorAll('.login-method-btn');
    methodBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            methodBtns.forEach(function(b) { b.classList.remove('active'); });
            this.classList.add('active');
            const method = this.dataset.method;
            const input = document.getElementById('userId');
            const icon = document.querySelector('.form-icon');
            if (method === 'aadhaar') {
                if (input) input.placeholder = 'Enter 12-digit Aadhaar number';
                if (input) input.maxLength = 12;
                if (icon) icon.textContent = 'badge';
            } else {
                if (input) input.placeholder = 'Enter mobile or Aadhaar number';
                if (input) input.maxLength = 12;
                if (icon) icon.textContent = 'phone_android';
            }
        });
    });
});

console.log('GRAM-SABHA Auth (API) loaded. Backend: ' + API_BASE);
