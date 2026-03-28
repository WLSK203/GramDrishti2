/* ===================================================
   GramDrishti — Supabase + Cloudinary API Layer
   =================================================== */

// ── Config (replace with your actual values) ──────────
const SUPABASE_URL  = 'https://vikieodqlvvntnxbtapm.supabase.co';
const SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZpa2llb2RxbHZ2bnRueGJ0YXBtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3MDk5OTksImV4cCI6MjA5MDI4NTk5OX0.fI-y-0NfMnBryD-ef7YFeW2t9RqvKq3zIRDvJl91ukI';
const CLOUDINARY_CLOUD = 'dtjvvg1qu';
const CLOUDINARY_PRESET_COMPLAINTS   = 'gramdrishti_complaints';
const CLOUDINARY_PRESET_VERIFICATION = 'gramdrishti_verification';

// ── Init Supabase client ───────────────────────────────
// Add to every HTML page before auth.js:
// <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
const _supa = supabase.createClient(SUPABASE_URL, SUPABASE_ANON);

// ── Session ────────────────────────────────────────────
const SESSION_KEY = 'gram_drishti_session';

function saveSession(user) {
    localStorage.setItem(SESSION_KEY, JSON.stringify({
        ...user, loginTime: new Date().toISOString()
    }));
}
function getSession()   { const d = localStorage.getItem(SESSION_KEY); return d ? JSON.parse(d) : null; }
function clearSession() { localStorage.removeItem(SESSION_KEY); }
function isLoggedIn()   { return getSession() !== null; }
function getCurrentUser() { return getSession(); }

function requireAuth(allowedRoles = null) {
    const user = getCurrentUser();
    if (!user) { window.location.href = 'login.html'; return null; }
    if (allowedRoles && !allowedRoles.includes(user.role)) {
        const map = { villager: 'villager-dashboard.html', sarpanch: 'sarpanch-portal.html', admin: 'admin-panel.html' };
        window.location.href = map[user.role] || 'index.html';
        return null;
    }
    return user;
}

function logout() {
    _supa.auth.signOut();
    clearSession();
    window.location.href = 'index.html';
}

// ── Auth: Login (mobile + PIN) ─────────────────────────
async function loginUser(mobileRaw, pin) {
    const mobile = mobileRaw.replace(/[^0-9]/g, '');
    const email = mobile + '@gramdrishti.in';
    const { data, error } = await _supa.auth.signInWithPassword({ email, password: pin });
    if (error) throw new Error('Invalid credentials');

    // Fetch user profile from public.users
    const { data: userRow, error: uErr } = await _supa
        .from('users')
        .select('*, villages(name)')
        .eq('auth_id', data.user.id)
        .single();
    if (uErr || !userRow) throw new Error('User profile not found');

    const profile = {
        ...userRow,
        village_id: userRow.village_id || 1, // Fallback safety
        villageName: userRow.villages?.name || 'Rampur', // Fallback
        redirectUrl: { villager: 'villager-dashboard.html', sarpanch: 'sarpanch-portal.html', admin: 'admin-panel.html' }[userRow.role] || 'index.html'
    };
    saveSession(profile);
    return profile;
}

// ── Auth: Register ─────────────────────────────────────
async function registerUser({ name, mobile: mobileRaw, pin, role, villageId, ward }) {
    const mobile = mobileRaw.replace(/[^0-9]/g, '');
    const email = mobile + '@gramdrishti.in';
    const { data, error } = await _supa.auth.signUp({ email, password: pin });
    if (error) throw new Error(error.message);

    const externalId = (role.slice(0,3).toUpperCase()) + '-' + Math.random().toString(36).slice(2,8).toUpperCase();
    const avatar = name.split(' ').slice(0,2).map(w => w[0]).join('').toUpperCase();
    const redirectUrl = role === 'villager' ? 'villager-dashboard.html' : role === 'sarpanch' ? 'sarpanch-portal.html' : 'admin-panel.html';

    const { error: insErr } = await _supa.from('users').insert({
        auth_id: data.user.id,
        external_id: externalId,
        name, mobile,
        role, role_name: role.charAt(0).toUpperCase() + role.slice(1),
        village_id: villageId ? parseInt(villageId) : null,
        ward: ward || null,
        avatar, redirect_url: redirectUrl
    });
    if (insErr) throw new Error(insErr.message);
    return { success: true };
}

// ── Villages ───────────────────────────────────────────
async function getVillage(villageId) {
    if (!villageId) return null;
    const { data } = await _supa.from('villages').select('*').eq('id', villageId).single();
    return data;
}

async function listVillages() {
    const { data } = await _supa.from('villages').select('*').order('name').limit(100);
    return data || [];
}

// ── Issues / Complaints ────────────────────────────────
async function getIssues(villageId, userId) {
    let q = _supa.from('issues').select(`
        *, projects(verification_images, progress)
    `).order('created_at', { ascending: false }).limit(50);

    if (villageId) q = q.eq('village_id', villageId);

    const { data, error } = await q;
    if (error) throw new Error(error.message);

    // Attach userVoted flag and normalize DB columns to UI expectations
    let finalData = data || [];
    if (finalData.length > 0) {
        let votedSet = new Set();
        if (userId) {
            const ids = finalData.map(i => i.id);
            const { data: votes } = await _supa.from('issue_votes')
                .select('issue_id').eq('user_id', userId).in('issue_id', ids);
            votedSet = new Set((votes || []).map(v => v.issue_id));
        }
        
        finalData = finalData.map(i => {
            // Safely parse attachments if it comes back as stringified JSON
            let atts = i.attachments || [];
            if (typeof atts === 'string') {
                try { atts = JSON.parse(atts); } catch(e) { atts = []; }
            }
            
            return {
                ...i,
                userVoted: votedSet.has(i.id),
                categoryName: i.category_name || i.category,
                reportedByName: i.reported_by_name,
                reportedBy: i.reported_by_id,
                reportedDate: i.reported_date || i.created_at,
                createdAt: i.created_at,
                statusName: i.status_name || i.status,
                attachments: Array.isArray(atts) ? atts : [],
                verificationImages: i.projects && i.projects[0] ? i.projects[0].verification_images : [],
                progress: i.projects && i.projects[0] ? i.projects[0].progress : 0
            };
        });
    }

    return finalData;
}

async function createIssue({ title, description, category, villageId, reportedById, location, priority, department, attachments }) {
    const user = await _supa.from('users').select('name, village_id').eq('id', reportedById).single();
    const catNames = { water:'Water Supply', roads:'Roads & Paths', electricity:'Electricity', sanitation:'Hygiene & Sanitation', education:'Education' };

    const safeVillageId = parseInt(villageId) || user.data?.village_id || 1;

    const { data, error } = await _supa.from('issues').insert({
        title, description, category,
        category_name: catNames[category] || category,
        village_id: safeVillageId,
        reported_by_id: parseInt(reportedById),
        reported_by_name: user.data?.name,
        priority: priority || 'normal',
        department: department || null,
        location: location || null,
        attachments: attachments || [],
        status: 'submitted', status_name: 'Submitted'
    }).select().single();
    if (error) throw new Error(error.message);
    return data;
}

async function voteIssue(issueId, userId) {
    // Check if already voted
    const { data: existing } = await _supa.from('issue_votes')
        .select('id').eq('issue_id', issueId).eq('user_id', userId).single();

    if (existing) {
        await _supa.from('issue_votes').delete().eq('issue_id', issueId).eq('user_id', userId);
        const { data: issue } = await _supa.from('issues').select('votes').eq('id', issueId).single();
        await _supa.from('issues').update({ votes: Math.max(0, (issue?.votes || 0) - 1) }).eq('id', issueId);
        return { success: true, voted: false };
    } else {
        await _supa.from('issue_votes').insert({ issue_id: issueId, user_id: userId });
        const { data: issue } = await _supa.from('issues').select('votes').eq('id', issueId).single();
        await _supa.from('issues').update({ votes: (issue?.votes || 0) + 1 }).eq('id', issueId);
        return { success: true, voted: true };
    }
}

async function deleteIssue(issueId, userId) {
    const { data: issue } = await _supa.from('issues').select('id, reported_by_id').eq('id', issueId).single();
    if (!issue) throw new Error('Issue not found');
    if (issue.reported_by_id !== userId) throw new Error('You can only delete your own issues');
    await _supa.from('issue_votes').delete().eq('issue_id', issueId);
    await _supa.from('issues').delete().eq('id', issueId);
    return { success: true };
}

// ── Budget & Projects ──────────────────────────────────
async function getBudget(villageId) {
    const { data: summary } = await _supa.from('budget_summary').select('*').eq('village_id', villageId).single();
    const { data: projects } = await _supa.from('projects').select('*').eq('village_id', villageId).order('id');

    const realSpent   = (projects || []).reduce((s, p) => s + (p.spent || 0), 0);
    const realPending = (projects || []).filter(p => !['completed','closed','resolved'].includes(p.status))
        .reduce((s, p) => s + Math.max(0, (p.sanctioned || 0) - (p.spent || 0)), 0);
    const totalReceived = summary?.total_received || 0;

    return {
        totalReceived,
        totalSpent:    realSpent,
        pendingApproval: realPending,
        available:     totalReceived - realSpent - realPending,
        fiscalYear:    summary?.fiscal_year || '',
        projects:      projects || []
    };
}

async function createProject({ name, category, sanctioned, villageId }) {
    const { data, error } = await _supa.from('projects').insert({
        name, category, sanctioned: parseFloat(sanctioned),
        village_id: parseInt(villageId),
        status: 'in_progress', progress: 0, released: 0, spent: 0
    }).select().single();
    if (error) throw new Error(error.message);
    return data;
}

async function assignProject(projectId, contractorName) {
    const { data, error } = await _supa.from('projects')
        .update({ contractor: contractorName, status: 'in_progress' })
        .eq('id', projectId).select().single();
    if (error) throw new Error(error.message);
    return data;
}

// Convert an issue to a project and assign it to a contractor
async function assignIssueToContractor(issueId, contractorName, sanctionedAmount) {
    const { data: issueRow, error: issueErr } = await _supa.from('issues').select('*').eq('id', issueId).single();
    if (issueErr || !issueRow) throw new Error('Issue not found');
    
    // Create new project
    const { data: newProj, error: projErr } = await _supa.from('projects').insert({
        name: issueRow.title,
        category: issueRow.category,
        village_id: issueRow.village_id,
        contractor: contractorName,
        sanctioned: sanctionedAmount || 0,
        status: 'in_progress',
        progress: 0, released: 0, spent: 0
    }).select().single();
    
    if (projErr) throw new Error(projErr.message);
    
    // Mark issue as in-progress and link project
    const { error: updErr } = await _supa.from('issues').update({ status: 'in_progress' }).eq('id', issueId);
    if (updErr) console.warn('Failed to update issue status', updErr);
    
    return newProj;
}

async function verifyProjectStep(projectId, step, cloudinaryUrl) {
    const validSteps = [
        'verifications_site_inspection','verifications_photos',
        'verifications_materials','verifications_gps',
        'verifications_community','verifications_audit'
    ];
    if (!validSteps.includes(step)) throw new Error('Invalid step: ' + step);

    // Fetch current project
    const { data: proj } = await _supa.from('projects').select('*').eq('id', projectId).single();
    if (!proj) throw new Error('Project not found');

    const images = Array.isArray(proj.verification_images) ? proj.verification_images : [];
    if (cloudinaryUrl && !images.includes(cloudinaryUrl)) images.push(cloudinaryUrl);

    const update = { [step]: true, verification_images: images };

    // Recalculate progress
    const allSteps = validSteps.map(s => s === step ? true : proj[s]);
    const done = allSteps.filter(Boolean).length;
    update.progress = Math.round((done / 6) * 100);
    if (done === 6) { update.status = 'completed'; update.completed_date = new Date().toISOString().split('T')[0]; }

    const { data, error } = await _supa.from('projects').update(update).eq('id', projectId).select().single();
    if (error) throw new Error(error.message);
    return { success: true, data };
}

// ── Cloudinary Upload ──────────────────────────────────
async function uploadToCloudinary(file, preset) {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('upload_preset', preset);
    const res = await fetch(`https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD}/auto/upload`, {
        method: 'POST', body: fd
    });
    const json = await res.json();
    if (!json.secure_url) throw new Error('Cloudinary upload failed: ' + (json.error?.message || 'unknown'));
    return json.secure_url;  // Returns the permanent HTTPS URL
}

// Upload complaint media (photo/video)
async function uploadComplaintMedia(file)    { return uploadToCloudinary(file, CLOUDINARY_PRESET_COMPLAINTS); }
// Upload verification proof photos
async function uploadVerificationPhoto(file) { return uploadToCloudinary(file, CLOUDINARY_PRESET_VERIFICATION); }

// ── Activities ─────────────────────────────────────────
async function getActivities(villageId) {
    let q = _supa.from('activities').select('*').order('created_at', { ascending: false }).limit(20);
    if (villageId) q = q.eq('village_id', villageId);
    const { data } = await q;
    return data || [];
}

// ── Admin ──────────────────────────────────────────────
async function getAdminStats() {
    const [{ count: vil }, { count: usr }, { count: res }, { data: funds }] = await Promise.all([
        _supa.from('villages').select('*', { count: 'exact', head: true }),
        _supa.from('users').select('*', { count: 'exact', head: true }),
        _supa.from('issues').select('*', { count: 'exact', head: true }).eq('status', 'resolved'),
        _supa.from('projects').select('sanctioned')
    ]);
    return {
        activeVillages: vil || 0, registeredUsers: usr || 0,
        issuesResolved: res || 0,
        totalFundsTracked: (funds || []).reduce((s, p) => s + (p.sanctioned || 0), 0)
    };
}

async function getAdminUsers() {
    const { data } = await _supa.from('users').select('*, villages(name)').order('id', { ascending: false });
    return (data || []).map(u => ({ ...u, villageName: u.villages?.name }));
}

// ── Utilities ──────────────────────────────────────────
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount || 0);
}
function formatDate(d) {
    if (!d) return '';
    return new Date(d).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
}
function getGreeting() {
    const h = new Date().getHours();
    return h < 12 ? 'Good Morning' : h < 17 ? 'Good Afternoon' : 'Good Evening';
}

if (typeof showNotification !== 'function') {
    function showNotification(msg, type) {
        const n = document.createElement('div');
        n.style.cssText = 'position:fixed;bottom:2rem;right:2rem;padding:1rem 1.5rem;background:#1e293b;color:white;border-radius:.75rem;font-weight:600;box-shadow:0 10px 40px rgba(0,0,0,.2);z-index:9999;';
        n.textContent = msg;
        document.body.appendChild(n);
        setTimeout(() => n.remove(), 3000);
    }
}

// ── Export (replaces the old GramDrishti object) ───────
window.GramDrishti = {
    supabase: _supa,
    // Auth
    loginUser, registerUser, logout,
    saveSession, getSession, clearSession, isLoggedIn, getCurrentUser, requireAuth,
    // Data
    getVillage, listVillages, getIssues, createIssue, voteIssue, deleteIssue,
    getBudget, createProject, assignProject, assignIssueToContractor, verifyProjectStep,
    getActivities, getAdminStats, getAdminUsers,
    // Media
    uploadComplaintMedia, uploadVerificationPhoto, uploadToCloudinary,
    CLOUDINARY_CLOUD,
    // Helpers
    formatCurrency, formatDate, getGreeting, showNotification
};
