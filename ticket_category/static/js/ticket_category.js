// ── UTILS ──────────────────────────────────────────────────────────────────
function escHtml(v) {
  if (!v) return '';
  return String(v)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function formatRp(n) {
  return 'Rp ' + Number(n).toLocaleString('id-ID');
}

// ── STATE ──────────────────────────────────────────────────────────────────
let tickets   = typeof TICKETS_DATA !== 'undefined' ? TICKETS_DATA : [];
let canManage = typeof CAN_MANAGE   !== 'undefined' ? CAN_MANAGE   : false;
let currentView = 'table';

// ── FILTER ─────────────────────────────────────────────────────────────────
function getFiltered() {
  const q  = document.getElementById('searchInput').value.trim().toLowerCase();
  const af = document.getElementById('acaraFilter').value;
  return tickets.filter(k => {
    const mq = !q || k.kategori.toLowerCase().includes(q);
    const ma = af === 'all' || k.acara === af;
    return mq && ma;
  });
}

// ── POPULATE ACARA SELECT ──────────────────────────────────────────────────
function populateAcaraSelect() {
  const acaraSet = new Set([
    ...(typeof ACARA_LIST !== 'undefined' ? ACARA_LIST.map(a => a.nama) : []),
    ...tickets.map(k => k.acara)
  ]);
  const opts = Array.from(acaraSet).sort();

  // filter dropdown
  const filterSel = document.getElementById('acaraFilter');
  const prevFilter = filterSel.value;
  filterSel.innerHTML = '<option value="all">Semua Acara</option>' +
    opts.map(a => `<option value="${escHtml(a)}">${escHtml(a)}</option>`).join('');
  filterSel.value = prevFilter;

  // form dropdown
  const formSel = document.getElementById('fAcara');
  const prevForm = formSel.value;
  formSel.innerHTML = '<option value="">Pilih acara</option>' +
    (typeof ACARA_LIST !== 'undefined' ? ACARA_LIST : []).map(a =>
      `<option value="${escHtml(a.id)}">${escHtml(a.nama)}</option>`
    ).join('');
  formSel.value = prevForm;
}

// ── STATS ──────────────────────────────────────────────────────────────────
function updateStats() {
  document.getElementById('statTotal').textContent = tickets.length;
  document.getElementById('statKuota').textContent =
    tickets.reduce((s, k) => s + k.kuota, 0).toLocaleString('id-ID');
  const max = tickets.reduce((m, k) => Math.max(m, k.harga), 0);
  document.getElementById('statHarga').textContent = formatRp(max);
}

// ── RENDER ─────────────────────────────────────────────────────────────────
function render() {
  populateAcaraSelect();
  updateStats();
  const filtered = getFiltered();
  document.getElementById('countLabel').textContent = filtered.length;
  renderTable(filtered);
  renderGrid(filtered);
}

function renderTable(filtered) {
  const tbody = document.getElementById('tableBody');
  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="${canManage ? 5 : 4}" style="text-align:center;padding:48px;color:var(--muted)">Tidak ada kategori yang cocok.</td></tr>`;
    return;
  }
  tbody.innerHTML = filtered.map(k => `
    <tr>
      <td><span class="badge-ticket">${escHtml(k.kategori)}</span></td>
      <td style="font-weight:600">${escHtml(k.acara)}</td>
      <td class="td-price">${formatRp(k.harga)}</td>
      <td class="td-quota">${k.kuota.toLocaleString('id-ID')} <span class="unit">tiket</span></td>
      ${canManage ? `
      <td style="text-align:right">
        <button class="btn-icon-edit" title="Edit" onclick="openEdit('${escHtml(k.id)}')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z"/></svg>
        </button>
        <button class="btn-icon-delete" title="Hapus" onclick="openDelete('${escHtml(k.id)}', '${escHtml(k.kategori)}', '${escHtml(k.acara)}')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6M9 6V4h6v2"/></svg>
        </button>
      </td>` : ''}
    </tr>
  `).join('');
}

function renderGrid(filtered) {
  const grid = document.getElementById('cardGrid');
  if (!filtered.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">Tidak ada kategori yang cocok.</div>`;
    return;
  }
  grid.innerHTML = filtered.map(k => `
    <div class="ticket-card">
      <div class="card-row1">
        <span class="badge-ticket">${escHtml(k.kategori)}</span>
        <span class="card-quota">${k.kuota.toLocaleString('id-ID')} <span class="unit">tiket</span></span>
      </div>
      <div class="card-event">${escHtml(k.acara)}</div>
      <div class="card-price">${formatRp(k.harga)}</div>
      ${canManage ? `
      <div class="card-actions">
        <button class="btn-outline" onclick="openEdit('${escHtml(k.id)}')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z"/></svg>
          Edit
        </button>
        <button class="btn-danger-outline" onclick="openDelete('${escHtml(k.id)}', '${escHtml(k.kategori)}', '${escHtml(k.acara)}')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6M9 6V4h6v2"/></svg>
          Hapus
        </button>
      </div>` : ''}
    </div>
  `).join('');
}

// ── VIEW SWITCH ────────────────────────────────────────────────────────────
function switchView(v) {
  currentView = v;
  localStorage.setItem('ticketView', v);
  document.getElementById('table-view').style.display = v === 'table' ? '' : 'none';
  document.getElementById('grid-view').style.display  = v === 'grid'  ? '' : 'none';
  document.getElementById('pillTable').classList.toggle('active', v === 'table');
  document.getElementById('pillGrid').classList.toggle('active', v === 'grid');
}

// ── FORM MODAL ─────────────────────────────────────────────────────────────
function openCreate() {
  document.getElementById('modalTitle').textContent = 'Tambah Kategori Tiket';
  document.getElementById('submitBtn').textContent  = 'Tambah Kategori';
  document.getElementById('fAcara').value    = '';
  document.getElementById('fKategori').value = '';
  document.getElementById('fHarga').value    = '';
  document.getElementById('fKuota').value    = '';
  document.getElementById('ticketForm').action = CREATE_URL;
  // hidden event_id kosongkan
  document.getElementById('fEventId').value = '';
  clearErrors();
  document.getElementById('formOverlay').classList.add('show');
}

function openEdit(id) {
  fetch(`${EDIT_URL_BASE}${id}/data/?role=${typeof CURRENT_ROLE !== 'undefined' ? CURRENT_ROLE : 'admin'}`)
    .then(r => r.json())
    .then(k => {
      document.getElementById('modalTitle').textContent = 'Edit Kategori Tiket';
      document.getElementById('submitBtn').textContent  = 'Simpan Perubahan';
      populateAcaraSelect();
      // set hidden event_id
      document.getElementById('fEventId').value  = k.event_id;
      document.getElementById('fKategori').value = k.kategori;
      document.getElementById('fHarga').value    = k.harga;
      document.getElementById('fKuota').value    = k.kuota;
      document.getElementById('ticketForm').action = `${EDIT_URL_BASE}${id}/edit/?role=${typeof CURRENT_ROLE !== 'undefined' ? CURRENT_ROLE : 'admin'}`;
      clearErrors();
      document.getElementById('formOverlay').classList.add('show');
    });
}

function closeForm() {
  document.getElementById('formOverlay').classList.remove('show');
}

function clearErrors() {
  ['Acara','Kategori','Harga','Kuota'].forEach(f => {
    const el = document.getElementById('err' + f);
    if (el) el.textContent = '';
  });
}

function validateForm() {
  clearErrors();
  const eventId  = document.getElementById('fEventId').value;
  const kategori = document.getElementById('fKategori').value.trim();
  const harga    = Number(document.getElementById('fHarga').value);
  const kuota    = Number(document.getElementById('fKuota').value);
  let valid = true;
  if (!eventId)             { document.getElementById('errAcara').textContent    = 'Acara wajib dipilih'; valid = false; }
  if (!kategori)            { document.getElementById('errKategori').textContent = 'Nama kategori wajib diisi'; valid = false; }
  if (!harga || harga <= 0) { document.getElementById('errHarga').textContent    = 'Harga harus > 0'; valid = false; }
  if (!kuota || kuota <= 0) { document.getElementById('errKuota').textContent    = 'Kuota harus > 0'; valid = false; }
  return valid;
}

// ── DELETE MODAL ───────────────────────────────────────────────────────────
function openDelete(id, kategori, acara) {
  document.getElementById('delKategori').textContent = kategori;
  document.getElementById('delAcara').textContent    = acara;
  document.getElementById('deleteForm').action = `${DELETE_URL_BASE}${id}/delete/?role=${typeof CURRENT_ROLE !== 'undefined' ? CURRENT_ROLE : 'admin'}`;
  document.getElementById('deleteOverlay').classList.add('show');
}

function closeDelete() {
  document.getElementById('deleteOverlay').classList.remove('show');
}

document.addEventListener('DOMContentLoaded', () => {
  document.body.appendChild(document.getElementById('formOverlay'));
  document.body.appendChild(document.getElementById('deleteOverlay'));

  const savedView = localStorage.getItem('ticketView');
  if (savedView) currentView = savedView;

  render();
  switchView(currentView);

  ['formOverlay','deleteOverlay'].forEach(id => {
    document.getElementById(id).addEventListener('click', function(e) {
      if (e.target === this) this.classList.remove('show');
    });
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closeForm(); closeDelete(); }
  });

  document.getElementById('fAcara').addEventListener('change', function() {
    document.getElementById('fEventId').value = this.value;
  });
});