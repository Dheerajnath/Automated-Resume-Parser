/* ─── GLOBAL STATE ──────────────────────────────────── */
let currentPage = 1;

/* ─── NAV SECTION SWITCHER ──────────────────────────── */
function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  document.getElementById('section-' + name).classList.add('active');
  document.querySelectorAll('.nav-link').forEach(l => {
    if (l.getAttribute('href') === '#' + name) l.classList.add('active');
  });
  if (name === 'candidates') loadCandidates();
}

/* ─── API HEALTH CHECK ──────────────────────────────── */
async function checkHealth() {
  try {
    const r = await fetch('/api/health');
    const j = await r.json();
    const dot = document.getElementById('statusDot');
    const txt = document.getElementById('statusText');
    if (j.status === 'ok') {
      dot.className = 'status-dot online';
      txt.textContent = 'API Online';
    } else throw new Error();
  } catch {
    document.getElementById('statusDot').className = 'status-dot offline';
    document.getElementById('statusText').textContent = 'Offline';
  }
}

/* ─── LOAD STATS ────────────────────────────────────── */
async function loadStats() {
  try {
    const r = await fetch('/api/candidates?per_page=1');
    const j = await r.json();
    if (j.status === 'success') {
      document.getElementById('totalCount').textContent = j.data.total;
    }
  } catch {}
}

/* ─── DRAG & DROP ───────────────────────────────────── */
const uploadArea = document.getElementById('uploadArea');

uploadArea.addEventListener('dragover', e => { e.preventDefault(); uploadArea.classList.add('dragover'); });
uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
uploadArea.addEventListener('drop', e => {
  e.preventDefault();
  uploadArea.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
});
uploadArea.addEventListener('click', () => document.getElementById('fileInput').click());

function handleFileSelect(input) {
  if (input.files[0]) uploadFile(input.files[0]);
}

/* ─── UPLOAD ────────────────────────────────────────── */
async function uploadFile(file) {
  const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
  if (!allowed.includes(file.type) && !file.name.match(/\.(pdf|docx)$/i)) {
    showToast('Only PDF and DOCX files are allowed.', 'error');
    return;
  }

  const progress = document.getElementById('uploadProgress');
  const progressFill = document.getElementById('progressFill');
  const progressText = document.getElementById('progressText');
  const resultCard = document.getElementById('resultCard');

  progress.style.display = 'block';
  resultCard.style.display = 'none';
  progressFill.style.width = '20%';
  progressText.textContent = `Uploading ${file.name}…`;

  try {
    const formData = new FormData();
    formData.append('file', file);
    progressFill.style.width = '50%';
    progressText.textContent = 'Extracting text…';

    const r = await fetch('/api/upload', { method: 'POST', body: formData });
    progressFill.style.width = '80%';
    progressText.textContent = 'Running NLP analysis…';
    const j = await r.json();

    progressFill.style.width = '100%';
    await sleep(400);
    progress.style.display = 'none';
    progressFill.style.width = '0%';

    if (j.status === 'success') {
      renderResult(j.data, true);
      showToast('Resume parsed and saved!', 'success');
      loadStats();
    } else {
      renderResult({ message: j.message }, false);
      showToast(j.message, 'error');
    }
  } catch (err) {
    progress.style.display = 'none';
    showToast('Network error. Is the server running?', 'error');
  }
}

function renderResult(data, success) {
  const rc = document.getElementById('resultCard');
  rc.style.display = 'block';

  if (!success) {
    rc.innerHTML = `
      <div class="result-header">
        <h3>Parse Failed</h3>
        <span class="result-badge badge-error">Error</span>
      </div>
      <div class="result-body"><p style="color:var(--text2)">${data.message}</p></div>`;
    return;
  }

  const skills = (data.skills || []).slice(0, 12);
  const skillsHtml = skills.length
    ? skills.map(s => `<span class="skill-tag">${s}</span>`).join('')
    : '<span style="color:var(--text3);font-size:0.85rem">No skills detected</span>';

  rc.innerHTML = `
    <div class="result-header">
      <h3>✅ Successfully Parsed — ID #${data.id}</h3>
      <span class="result-badge badge-success">Saved to DB</span>
    </div>
    <div class="result-body">
      <div class="result-grid">
        <div class="result-field">
          <span class="field-label">Full Name</span>
          <span class="field-value ${!data.full_name ? 'empty' : ''}">${data.full_name || 'Not detected'}</span>
        </div>
        <div class="result-field">
          <span class="field-label">Email</span>
          <span class="field-value ${!data.email ? 'empty' : ''}">${data.email || 'Not detected'}</span>
        </div>
        <div class="result-field">
          <span class="field-label">Phone</span>
          <span class="field-value ${!data.phone ? 'empty' : ''}">${data.phone || 'Not detected'}</span>
        </div>
        <div class="result-field">
          <span class="field-label">Education</span>
          <span class="field-value ${!data.education ? 'empty' : ''}">${data.education || 'Not detected'}</span>
        </div>
      </div>
      ${data.experience_summary ? `
        <div class="result-field" style="margin-bottom:1.25rem">
          <span class="field-label">Experience Summary</span>
          <span class="field-value" style="font-size:0.85rem;line-height:1.6;color:var(--text2)">${data.experience_summary}</span>
        </div>` : ''}
      <div class="skills-section">
        <h4>Skills Detected (${data.skills ? data.skills.length : 0})</h4>
        <div class="skills-tags">${skillsHtml}</div>
      </div>
    </div>`;
}

/* ─── LOAD CANDIDATES ───────────────────────────────── */
async function loadCandidates(page = 1) {
  currentPage = page;
  const grid = document.getElementById('candidatesGrid');
  grid.innerHTML = '<div class="loading-spinner">Loading candidates…</div>';

  try {
    const r = await fetch(`/api/candidates?page=${page}&per_page=9`);
    const j = await r.json();

    if (j.status !== 'success') throw new Error();

    const { candidates, total, pages } = j.data;
    document.getElementById('candidateCount').textContent = `${total} candidate${total !== 1 ? 's' : ''} total`;

    if (candidates.length === 0) {
      grid.innerHTML = `<div class="empty-state">
        <div class="empty-icon">👤</div>
        <p>No candidates yet. Upload a resume to get started!</p>
      </div>`;
      document.getElementById('pagination').innerHTML = '';
      return;
    }

    grid.innerHTML = candidates.map(c => candidateCardHtml(c)).join('');
    renderPagination(page, pages);
  } catch {
    grid.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><p>Failed to load candidates.</p></div>';
  }
}

function candidateCardHtml(c) {
  const initials = c.full_name
    ? c.full_name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()
    : '?';
  const skills = (c.skills || []).slice(0, 4);
  const extra = (c.skills || []).length - skills.length;
  const date = c.created_at ? new Date(c.created_at).toLocaleDateString() : '—';

  return `
    <div class="candidate-card" onclick="showCandidateModal(${c.id})">
      <div class="card-avatar">${initials}</div>
      <div class="card-name">${c.full_name || '<span style="color:var(--text3)">Unknown Name</span>'}</div>
      <div class="card-email">📧 ${c.email || '<span style="color:var(--text3)">—</span>'}</div>
      <div class="card-phone">📞 ${c.phone || '<span style="color:var(--text3)">—</span>'}</div>
      <div class="card-skills">
        ${skills.map(s => `<span class="card-skill-tag">${s}</span>`).join('')}
        ${extra > 0 ? `<span class="card-more">+${extra} more</span>` : ''}
      </div>
      <div class="card-footer">
        <span class="card-date">${date}</span>
        <div class="card-actions" onclick="event.stopPropagation()">
          <button class="btn btn-danger btn-sm" onclick="deleteCandidate(${c.id})">🗑 Delete</button>
        </div>
      </div>
    </div>`;
}

function renderPagination(current, total) {
  if (total <= 1) { document.getElementById('pagination').innerHTML = ''; return; }
  const pg = document.getElementById('pagination');
  let html = '';
  for (let i = 1; i <= total; i++) {
    html += `<button class="page-btn ${i === current ? 'active' : ''}" onclick="loadCandidates(${i})">${i}</button>`;
  }
  pg.innerHTML = html;
}

/* ─── CANDIDATE MODAL ───────────────────────────────── */
async function showCandidateModal(id) {
  const overlay = document.getElementById('modalOverlay');
  const content = document.getElementById('modalContent');
  overlay.classList.add('open');
  content.innerHTML = '<div style="text-align:center;padding:2rem;color:var(--text3)">Loading…</div>';

  try {
    const r = await fetch(`/api/candidates/${id}`);
    const j = await r.json();
    if (j.status !== 'success') throw new Error();
    const c = j.data;
    const initials = c.full_name ? c.full_name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() : '?';
    const skillsHtml = (c.skills || []).map(s => `<span class="skill-tag">${s}</span>`).join('') || '<span style="color:var(--text3)">None detected</span>';

    content.innerHTML = `
      <div style="display:flex;align-items:center;gap:1.25rem;margin-bottom:2rem">
        <div class="card-avatar" style="width:64px;height:64px;font-size:1.6rem;border-radius:16px">${initials}</div>
        <div>
          <div style="font-size:1.4rem;font-weight:700">${c.full_name || 'Unknown'}</div>
          <div style="color:var(--text3);font-size:0.85rem">Candidate #${c.id}</div>
        </div>
      </div>
      <div class="result-grid" style="margin-bottom:1.5rem">
        <div class="result-field">
          <span class="field-label">Email</span>
          <span class="field-value ${!c.email ? 'empty' : ''}">${c.email || 'Not found'}</span>
        </div>
        <div class="result-field">
          <span class="field-label">Phone</span>
          <span class="field-value ${!c.phone ? 'empty' : ''}">${c.phone || 'Not found'}</span>
        </div>
        <div class="result-field">
          <span class="field-label">Education</span>
          <span class="field-value ${!c.education ? 'empty' : ''}">${c.education || 'Not found'}</span>
        </div>
        <div class="result-field">
          <span class="field-label">Parsed On</span>
          <span class="field-value">${c.created_at ? new Date(c.created_at).toLocaleString() : '—'}</span>
        </div>
      </div>
      ${c.experience_summary ? `
        <div class="result-field" style="margin-bottom:1.5rem">
          <span class="field-label">Experience</span>
          <span class="field-value" style="font-size:0.85rem;line-height:1.7;color:var(--text2)">${c.experience_summary}</span>
        </div>` : ''}
      <div class="skills-section">
        <h4>Skills (${(c.skills || []).length})</h4>
        <div class="skills-tags">${skillsHtml}</div>
      </div>
      <div style="margin-top:2rem;display:flex;justify-content:flex-end">
        <button class="btn btn-danger" onclick="deleteCandidate(${c.id}, true)">🗑 Delete Candidate</button>
      </div>`;
  } catch {
    content.innerHTML = '<div style="color:var(--red);text-align:center;padding:2rem">Failed to load candidate.</div>';
  }
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
}

/* ─── DELETE CANDIDATE ──────────────────────────────── */
async function deleteCandidate(id, fromModal = false) {
  if (!confirm(`Delete candidate #${id}? This cannot be undone.`)) return;
  try {
    const r = await fetch(`/api/candidates/${id}`, { method: 'DELETE' });
    const j = await r.json();
    if (j.status === 'success') {
      showToast(`Candidate #${id} deleted.`, 'success');
      if (fromModal) closeModal();
      loadCandidates(currentPage);
      loadStats();
    } else {
      showToast(j.message, 'error');
    }
  } catch {
    showToast('Delete failed.', 'error');
  }
}

/* ─── SEARCH ────────────────────────────────────────── */
async function searchCandidates() {
  const skill = document.getElementById('searchSkill').value.trim();
  const name = document.getElementById('searchName').value.trim();

  if (!skill && !name) { showToast("Enter a skill or name to search.", 'error'); return; }

  const params = new URLSearchParams();
  if (skill) params.append('skill', skill);
  if (name) params.append('name', name);

  const results = document.getElementById('searchResults');
  results.innerHTML = '<div style="text-align:center;padding:2rem;color:var(--text3)">Searching…</div>';

  try {
    const r = await fetch(`/api/search?${params}`);
    const j = await r.json();
    if (j.status !== 'success') throw new Error(j.message);

    const { results: candidates, count } = j.data;
    if (count === 0) {
      results.innerHTML = `<div class="no-results">🔍 No candidates found matching your query.</div>`;
      return;
    }

    results.innerHTML = `
      <div class="results-header">
        <h3>Results</h3>
        <span class="results-count">${count} found</span>
      </div>
      <div class="candidates-grid">${candidates.map(c => candidateCardHtml(c)).join('')}</div>`;
  } catch (err) {
    results.innerHTML = `<div class="no-results">⚠️ ${err.message || 'Search failed.'}</div>`;
  }
}

/* ─── Allow Enter key in search ─────────────────────── */
document.getElementById('searchSkill').addEventListener('keydown', e => { if (e.key === 'Enter') searchCandidates(); });
document.getElementById('searchName').addEventListener('keydown', e => { if (e.key === 'Enter') searchCandidates(); });

/* ─── TOAST ─────────────────────────────────────────── */
function showToast(msg, type = 'success') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

/* ─── UTILS ─────────────────────────────────────────── */
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* ─── INIT ──────────────────────────────────────────── */
checkHealth();
loadStats();
setInterval(checkHealth, 30000);
