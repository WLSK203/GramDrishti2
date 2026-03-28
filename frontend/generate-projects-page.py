import os

in_file = 'c:/Users/1wlsk/OneDrive/Desktop/Innovit2/innovit/frontend/villager-dashboard.html'
out_file = 'c:/Users/1wlsk/OneDrive/Desktop/Innovit2/innovit/frontend/villager-projects.html'

with open(in_file, 'r', encoding='utf-8') as f:
    text = f.read()

header_end = text.find('<!-- ═══════════════════════════════════════════════════\n     STATS ROW')
footer_start = text.find('</section>\n\n<script src="js/app.js">')
if footer_start == -1: footer_start = text.find('<script src="js/app.js">')

new_html = text[:header_end] + '''<!-- ═══════════════════════════════════════════════════
     MAIN GRID
═══════════════════════════════════════════════════ -->
<div class="db-grid" style="margin-top: 2rem;">

    <!-- ── Left column ── -->
    <div class="db-section">

        <!-- Projects List -->
        <div class="db-animate">
            <div class="db-section-header">
                <h2 class="db-section-title">
                    <span class="db-title-bar" aria-hidden="true"></span>
                    Village Projects
                </h2>
                <div style="display:flex;gap:1rem">
                    <select id="statusFilter" class="db-search" style="padding:0.5rem;border-radius:0.5rem;border:1px solid #e2e8f0;background:white">
                        <option value="">All Projects</option>
                        <option value="in_progress">Active / In Progress</option>
                        <option value="completed">Completed</option>
                    </select>
                </div>
            </div>

            <div id="projectsGrid" aria-live="polite" aria-label="Village projects list" style="display:flex;flex-direction:column;gap:1.5rem">
                <!-- Projects populated by JS -->
                <div class="db-issue-card" style="animation:none;pointer-events:none;opacity:.5">
                    <p class="db-issue-title">Loading projects…</p>
                </div>
            </div>
        </div>
    </div>

    <!-- ── Right sidebar ── -->
    <div class="db-sidebar">
        <!-- Village Budget Card -->
        <div class="db-budget-card db-animate">
            <div class="db-budget-top">
                <p class="db-budget-label">Village Fund Status</p>
                <p class="db-budget-amount" id="totalFunds">—</p>
                <p class="db-budget-fy" id="fiscalYear">—</p>
                <a href="public-ledger.html" class="db-budget-a-link">
                    View Full Ledger
                    <span class="material-symbols-outlined" style="font-size:.875rem" aria-hidden="true">arrow_forward</span>
                </a>
            </div>
            <div class="db-budget-bars" id="budgetBars">
                <!-- Populated by JS -->
            </div>
        </div>
        
        <div class="db-my-card db-animate">
            <div class="db-my-card-header">
                <h2>Quick Links</h2>
            </div>
            <div class="db-my-list">
                <a href="villager-dashboard.html" style="display:block;padding:1rem;color:var(--text);text-decoration:none;border-bottom:1px solid #f1f5f9">← Back to Dashboard</a>
                <a href="raise-issue.html" style="display:block;padding:1rem;color:var(--text);text-decoration:none;border-bottom:1px solid #f1f5f9">Report New Issue</a>
                <a href="public-ledger.html" style="display:block;padding:1rem;color:var(--text);text-decoration:none">View Public Ledger</a>
            </div>
        </div>
    </div>
</div>
''' + text[footer_start:]

new_js = '''
    <script>
        var allProjects = [];
        
        document.addEventListener('DOMContentLoaded', async function() {
            var user = GramDrishti.requireAuth();
            if (!user) return;

            // Load header info
            if (document.getElementById('villageName')) document.getElementById('villageName').textContent = user.village || 'GramDrishti';
            if (document.getElementById('userName')) document.getElementById('userName').textContent = user.name || 'Citizen';
            if (document.getElementById('userAvatar')) document.getElementById('userAvatar').textContent = (user.name || 'C').charAt(0).toUpperCase();
            if (document.getElementById('welcomeMsg')) document.getElementById('welcomeMsg').textContent = GramDrishti.getGreeting() + ', ' + (user.name ? user.name.split(' ')[0] : 'Citizen') + '!';
            
            try {
                var stats = await GramDrishti.getBudget(user.villageId || user.village_id);
                if (stats) {
                    if (document.getElementById('totalFunds')) document.getElementById('totalFunds').textContent = GramDrishti.formatCurrency(stats.totalReceived);
                    if (document.getElementById('fiscalYear')) document.getElementById('fiscalYear').textContent = (stats.fiscalYear || 'FY') + ' • Total Received';
                    
                    var spent = stats.totalSpent || 0;
                    var avail = stats.available || 0;
                    var total = stats.totalReceived || 0;
                    var pctS = total > 0 ? ((spent / total) * 100).toFixed(0) : 0;
                    var pctA = total > 0 ? ((avail / total) * 100).toFixed(0) : 0;
                    
                    var bHtml = `
                        <div class="db-brow"><div class="db-brow-top"><span class="db-brow-label">Spent</span><div style="text-align:right"><span class="db-brow-val">${GramDrishti.formatCurrency(spent)}</span><span class="db-brow-pct"> · ${pctS}%</span></div></div><div class="db-bar"><div class="db-bar-fill orange" style="width:${pctS}%"></div></div></div>
                        <div class="db-brow"><div class="db-brow-top"><span class="db-brow-label">Available</span><div style="text-align:right"><span class="db-brow-val">${GramDrishti.formatCurrency(avail)}</span><span class="db-brow-pct"> · ${pctA}%</span></div></div><div class="db-bar"><div class="db-bar-fill green" style="width:${pctA}%"></div></div></div>
                    `;
                    if (document.getElementById('budgetBars')) document.getElementById('budgetBars').innerHTML = bHtml;
                    
                    if (stats.projects) {
                        allProjects = stats.projects;
                        renderProjects();
                    }
                }
            } catch(e) { console.error(e); }
            
            document.getElementById('statusFilter').addEventListener('change', renderProjects);
        });

        function renderProjects() {
            var grid = document.getElementById('projectsGrid');
            var statusFilter = document.getElementById('statusFilter').value;
            
            var filtered = allProjects;
            if (statusFilter) {
                var isCompleted = statusFilter === 'completed';
                filtered = allProjects.filter(p => isCompleted ? p.status === 'completed' : p.status !== 'completed');
            }
            
            if (!filtered || filtered.length === 0) {
                grid.innerHTML = '<div class="db-issue-empty"><span class="material-symbols-outlined">folder_off</span><p>No projects found in this category.</p></div>';
                return;
            }
            
            grid.innerHTML = filtered.map(function(p) {
                var isCompleted = p.status === 'completed';
                var statusIcon = isCompleted ? 'task_alt' : 'construction';
                var statusClass = isCompleted ? 'resolved' : 'progress';
                var statusName = isCompleted ? 'Completed' : 'In Progress';
                
                var proofHtml = '';
                if (p.verificationImages && p.verificationImages.length > 0) {
                    var base = GramDrishti.API_BASE || 'http://127.0.0.1:5000';
                    proofHtml = '<div style="margin-top:1rem; padding:0.75rem; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:0.5rem;">' +
                        '<p style="font-size:0.75rem; font-weight:700; color:#16a34a; margin-bottom:0.5rem; display:flex; align-items:center; gap:0.25rem; text-transform:uppercase;"><span class="material-symbols-outlined" style="font-size:1.1rem;">verified</span> Documented Proofs</p>' +
                        '<div style="display:flex;gap:.5rem;flex-wrap:wrap;">' +
                        p.verificationImages.map(function(url) {
                            return '<img src="' + base + url + '" style="width:50px;height:50px;object-fit:cover;border-radius:.25rem;cursor:pointer;border:1px solid #86efac" onclick="window.open(\'' + base + url + '\',\'_blank\')" alt="Proof Photo">';
                        }).join('') +
                        '</div></div>';
                }
                
                return `
                <article class="db-issue-card db-animate">
                    <div class="db-issue-top">
                        <span class="db-issue-cat ${(p.category || 'other').toLowerCase()}">${p.category || 'Infrastructure'}</span>
                        <span class="db-issue-status ${statusClass}">
                            <span class="material-symbols-outlined">${statusIcon}</span> ${statusName}
                        </span>
                    </div>
                    <h3 class="db-issue-title">${p.name}</h3>
                    <p class="db-issue-desc" style="margin-top:0.25rem">Assigned to: <strong>${p.contractor || 'Dept.'}</strong> • Budget: <strong>${GramDrishti.formatCurrency(p.sanctioned)}</strong></p>
                    
                    <div style="margin-top: 1rem;">
                        <div style="display:flex; justify-content:space-between; font-size:0.875rem; font-weight:600; color:#475569; margin-bottom:0.5rem;">
                            <span>Progress</span>
                            <span>${p.progress || 0}%</span>
                        </div>
                        <div style="width:100%; height:8px; background:#e2e8f0; border-radius:4px; overflow:hidden;">
                            <div style="height:100%; width:${p.progress || 0}%; background:var(--primary); transition:width 1s ease;"></div>
                        </div>
                    </div>
                    
                    ${proofHtml}
                    
                    <div class="db-issue-meta" style="margin-top:1rem; padding-top:1rem; border-top:1px solid #f1f5f9;">
                        <span><span class="material-symbols-outlined">calendar_today</span> Started: ${p.startDate || 'Recently'}</span>
                        ${isCompleted ? `<span><span class="material-symbols-outlined">check_circle</span> Finished: ${p.completedDate || 'Recently'}</span>` : ''}
                    </div>
                </article>`;
            }).join('');
        }
    </script>
</body>
</html>
'''

old_js_start = new_html.rfind('<script>')
if old_js_start != -1:
    new_html = new_html[:old_js_start] + new_js
else:
    new_html = new_html.replace('</body>', new_js)

with open(out_file, 'w', encoding='utf-8') as f:
    f.write(new_html)

print('Done')
