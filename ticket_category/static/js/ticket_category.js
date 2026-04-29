// ticket_category.js
// Data diisi dari Django template:
// const TICKETS_DATA = {{ tickets_json|safe }};
// const ACARA_LIST   = {{ acara_list_json|safe }};
// const CAN_MANAGE   = {{ can_manage|yesno:"true,false" }};
// const CREATE_URL   = "{% url 'ticket_category:create' %}";
// const EDIT_URL_BASE   = "{% url 'ticket_category:list' %}";  // base, append id
// const DELETE_URL_BASE = "{% url 'ticket_category:list' %}";

/* ── STATE ── */
let tickets   = typeof TICKETS_DATA !== 'undefined' ? TICKETS_DATA : [];
let canManage = typeof CAN_MANAGE   !== 'undefined' ? CAN_MANAGE   : false;
let currentView = 'table';

/* ── HELPERS ── */
// formatRp & escHtml dari base.js

/* ── FILTER ── */
function getFiltered() {
  const q  = document.getElementById('searchInput').value.trim().toLowerCase();
  const af = document.getElementById('acaraFilter').value;
  return tickets.filter(k => {
    const mq = !q || k.kategori.toLowerCase().includes(q);
    const ma = af === 'all' || k.acara === af;
    return mq && ma;
  });
}

/* ── POPULATE ACARA SELECT ── */
function populateAcaraSelect() {
  const acaraSet = new Set([
    ...(typeof ACARA_LIST !== 'undefined' ? ACARA_LIST : []),
    ...tickets.map(k => k.acara)
  ]);
  const opts = Array.from(acaraSet).sort();

  ['acaraFilter', 'fAcara'].forEach(id => {
    const sel   = document.getElementById(id);
    const prev  = sel.value;
    const first = id === 'acaraFilter'
      ? '<option value="all">Semua Acara</option>'
      : '<option value="">Pilih acara</option>';
    sel.innerHTML = first + opts.map(a => `<option value="${escHtml(a)}">${escHtml(a)}</option>`).join('');
    sel.value = prev;
  });
}

/* ── STATS ── */
function updateStats() {
  document.getElementById('statTotal').textContent = tickets.length;
  document.getElementById('statKuota').textContent =
    tickets.reduce((s, k) => s + k.kuota, 0).toLocaleString('id-ID');
  const max = tickets.reduce((m, k) => Math.max(m, k.harga), 0);
  document.getElementById('statHarga').textContent = formatRp(max);
}

/* ── RENDER ── */
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
        <div class="action-btns">
          <button class="btn-ghost-icon" title="Edit" onclick="openEdit(${k.id})">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button class="btn-ghost-icon danger" title="Hapus" onclick="openDelete(${k.id}, '${escHtml(k.kategori)}', '${escHtml(k.acara)}')">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6M9 6V4h6v2"/></svg>
          </button>
        </div>
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
        <button class="btn-outline" onclick="openEdit(${k.id})">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          Edit
        </button>
        <button class="btn-danger-outline" onclick="openDelete(${k.id}, '${escHtml(k.kategori)}', '${escHtml(k.acara)}')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6M9 6V4h6v2"/></svg>
          Hapus
        </button>
      </div>` : ''}
    </div>
  `).join('');
}

/* ── VIEW SWITCH ── */
function switchView(v) {
  currentView = v;
  document.getElementById('table-view').style.display = v === 'table' ? '' : 'none';
  document.getElementById('grid-view').style.display  = v === 'grid'  ? '' : 'none';
}

/* ── FORM MODAL ── */
function openCreate() {
  document.getElementById('modalTitle').textContent  = 'Tambah Kategori Tiket';
  document.getElementById('submitBtn').textContent   = 'Tambah Kategori';
  document.getElementById('fAcara').value    = '';
  document.getElementById('fKategori').value = '';
  document.getElementById('fHarga').value    = '';
  document.getElementById('fKuota').value    = '';
  document.getElementById('ticketForm').action = CREATE_URL;
  clearErrors();
  document.getElementById('formOverlay').classList.add('show');
}

function openEdit(id) {
  fetch(`${EDIT_URL_BASE}${id}/data/`)
    .then(r => r.json())
    .then(k => {
      document.getElementById('modalTitle').textContent = 'Edit Kategori Tiket';
      document.getElementById('submitBtn').textContent  = 'Simpan Perubahan';
      populateAcaraSelect();
      document.getElementById('fAcara').value    = k.acara;
      document.getElementById('fKategori').value = k.kategori;
      document.getElementById('fHarga').value    = k.harga;
      document.getElementById('fKuota').value    = k.kuota;
      document.getElementById('ticketForm').action = `${EDIT_URL_BASE}${id}/edit/`;
      clearErrors();
      document.getElementById('formOverlay').classList.add('show');
    });
}

function closeForm() {
  document.getElementById('formOverlay').classList.remove('show');
}

function clearErrors() {
  ['Acara', 'Kategori', 'Harga', 'Kuota'].forEach(f => {
    document.getElementById('err' + f).textContent = '';
  });
}

function validateForm() {
  clearErrors();
  const acara    = document.getElementById('fAcara').value;
  const kategori = document.getElementById('fKategori').value.trim();
  const harga    = Number(document.getElementById('fHarga').value);
  const kuota    = Number(document.getElementById('fKuota').value);
  let valid = true;
  if (!acara)               { document.getElementById('errAcara').textContent    = 'Acara wajib dipilih'; valid = false; }
  if (!kategori)            { document.getElementById('errKategori').textContent = 'Nama kategori wajib diisi'; valid = false; }
  if (!harga || harga <= 0) { document.getElementById('errHarga').textContent    = 'Harga harus > 0'; valid = false; }
  if (!kuota || kuota <= 0) { document.getElementById('errKuota').textContent    = 'Kuota harus > 0'; valid = false; }
  return valid;
}

/* ── DELETE MODAL ── */
function openDelete(id, kategori, acara) {
  document.getElementById('delKategori').textContent = kategori;
  document.getElementById('delAcara').textContent    = acara;
  document.getElementById('deleteForm').action = `${DELETE_URL_BASE}${id}/delete/`;
  document.getElementById('deleteOverlay').classList.add('show');
}

function closeDelete() {
  document.getElementById('deleteOverlay').classList.remove('show');
}

/* ── INIT ── */
document.addEventListener('DOMContentLoaded', () => {
  render();

  ['formOverlay', 'deleteOverlay'].forEach(id => {
    document.getElementById(id).addEventListener('click', function(e) {
      if (e.target === this) this.classList.remove('show');
    });
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closeForm(); closeDelete(); }
  });
});
