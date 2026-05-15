/* ======================================
   STATE
====================================== */

let artists = ARTISTS_DATA || [];
const canManage = CAN_MANAGE || false;

let genreFilter = "all";
let currentView = "table";


/* ======================================
   UTILITIES
====================================== */

function escapeHtml(value) {
    if (!value) return "";
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

const avatarPalettes = [
    "linear-gradient(135deg,#7c3aed,#3b82f6)",
    "linear-gradient(135deg,#10b981,#06b6d4)",
    "linear-gradient(135deg,#f59e0b,#ef4444)",
    "linear-gradient(135deg,#ec4899,#8b5cf6)",
    "linear-gradient(135deg,#6366f1,#a855f7)"
];

function getAvatarGradient(name) {
    let hash = 0;
    for (const char of name) {
        hash = char.charCodeAt(0) + ((hash << 5) - hash);
    }
    return avatarPalettes[Math.abs(hash) % avatarPalettes.length];
}

function getInitials(name) {
    return name
        .split(" ")
        .slice(0, 2)
        .map(word => word[0])
        .join("")
        .toUpperCase();
}


/* ======================================
   GENRE FILTER
====================================== */

function buildGenreMenu() {
    const genres = [
        ...new Set(artists.map(a => a.genre).filter(Boolean))
    ].sort();

    let html = `
        <div onclick="selectGenre('all')"
            class="custom-select-item ${genreFilter === 'all' ? 'selected' : ''}">
            Semua Genre
        </div>
    `;

    genres.forEach(genre => {
        html += `
            <div onclick="selectGenre('${escapeHtml(genre)}')"
                class="custom-select-item ${genreFilter === genre ? 'selected' : ''}">
                ${escapeHtml(genre)}
            </div>
        `;
    });

    document.getElementById("genreMenu").innerHTML = html;
}

function toggleGenreMenu() {
    document.getElementById("genreMenu").classList.toggle("show");
    document.getElementById("genreSelectBtn").classList.toggle("open");
}

function selectGenre(genre) {
    genreFilter = genre;
    document.getElementById("genreLabel").textContent =
        genre === "all" ? "Semua Genre" : genre;
    document.getElementById("genreMenu").classList.remove("show");
    render();
}


/* ======================================
   VIEW SWITCH
====================================== */

function setView(viewType) {
    currentView = viewType;
    localStorage.setItem('artistView', viewType);
    document.getElementById("btn-view-table").classList.toggle("active", viewType === "table");
    document.getElementById("btn-view-grid").classList.toggle("active", viewType === "grid");
    render();
}


/* ======================================
   FILTERED DATA
====================================== */

function getFilteredArtists() {
    const keyword = document.getElementById("searchInput").value.toLowerCase();
    return artists.filter(artist => {
        const matchSearch =
            !keyword ||
            artist.nama.toLowerCase().includes(keyword) ||
            (artist.genre || "").toLowerCase().includes(keyword);
        const matchGenre =
            genreFilter === "all" || artist.genre === genreFilter;
        return matchSearch && matchGenre;
    });
}


/* ======================================
   RENDER
====================================== */

function render() {
    const filtered = getFilteredArtists();
    document.getElementById("countNum").textContent = filtered.length;
    const container = document.getElementById("content");

    if (!filtered.length) {
        container.innerHTML = `<div class="empty-state">Tidak ada artis ditemukan</div>`;
        return;
    }

    if (currentView === "table") {
        renderTable(filtered, container);
    } else {
        renderGrid(filtered, container);
    }

    buildGenreMenu();
}

function renderTable(data, container) {
    let html = `
    <div class="table-card">
        <table class="table">
            <thead>
                <tr>
                    <th>Artis</th>
                    <th>Genre</th>
                    <th>Tampil di Event</th>
                    ${canManage ? `<th style="text-align:right;">Aksi</th>` : ""}
                </tr>
            </thead>
            <tbody>
    `;

    data.forEach(artist => {
        html += `
        <tr>
            <td>
                <div class="artist-cell">
                    <div class="avatar" style="background:${getAvatarGradient(artist.nama)}">
                        ${getInitials(artist.nama)}
                    </div>
                    <span class="artist-name">${escapeHtml(artist.nama)}</span>
                </div>
            </td>
            <td><span class="badge">${escapeHtml(artist.genre || "Lainnya")}</span></td>
            <td><b>${artist.tampil || 0}</b> event</td>
            ${canManage ? `
            <td style="text-align:right;">
                <button class="btn-icon-edit" onclick="openEdit('${artist.id}')">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z"/></svg>
                </button>
                <button class="btn-icon-delete"
                    data-id="${artist.id}"
                    data-nama="${escapeHtml(artist.nama)}"
                    onclick="openDelete(this.dataset.id, this.dataset.nama)">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
                </button>
            </td>
            ` : ""}
        </tr>
        `;
    });

    html += `</tbody></table></div>`;
    container.innerHTML = html;
}

function renderGrid(filtered, container) {
    let html = `<div class="artist-grid">`;

    filtered.forEach(a => {
        html += `
        <div class="artist-card">
            <div class="artist-card-top">
                <div class="avatar-lg" style="background:${getAvatarGradient(a.nama)}">
                    ${getInitials(a.nama)}
                </div>
                <div class="artist-card-info">
                    <div class="artist-card-name">${escapeHtml(a.nama)}</div>
                    <div class="artist-badge">${escapeHtml(a.genre || "Lainnya")}</div>
                    <div class="artist-card-tampil">Tampil di ${a.tampil || 0} event</div>
                </div>
            </div>
            ${canManage ? `
            <div class="artist-card-actions">
                <button class="btn-outline" onclick="openEdit('${a.id}')">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z"/>
                    </svg>
                    Edit
                </button>
                <button class="btn-danger-outline"
                    data-id="${a.id}"
                    data-nama="${escapeHtml(a.nama)}"
                    onclick="openDelete(this.dataset.id, this.dataset.nama)">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6l-1 14H6L5 6"/>
                        <path d="M10 11v6"/><path d="M14 11v6"/>
                    </svg>
                    Hapus
                </button>
            </div>
            ` : ""}
        </div>
        `;
    });

    html += `</div>`;
    container.innerHTML = html;
}


/* ======================================
   CREATE / EDIT
====================================== */

function openCreate() {
    document.getElementById("errName").style.display = "none";
    const form = document.getElementById("artistForm");
    form.action = CREATE_URL;
    document.getElementById("formTitle").textContent = "Tambah Artis";
    document.getElementById("submitBtn").textContent = "Tambah Artis";
    document.getElementById("inputName").value = "";
    document.getElementById("inputGenre").value = "";
    document.getElementById("formOverlay").classList.add("show");
}

function openEdit(id) {
    document.getElementById("errName").style.display = "none";
    fetch(`${EDIT_URL_BASE}${id}/data/`)
        .then(res => res.json())
        .then(artist => {
            const form = document.getElementById("artistForm");
            form.action = `${EDIT_URL_BASE}${id}/edit/`;
            document.getElementById("inputName").value = artist.nama;
            document.getElementById("inputGenre").value = artist.genre || "";
            document.getElementById("formTitle").textContent = "Edit Artis";
            document.getElementById("submitBtn").textContent = "Simpan Perubahan";
            document.getElementById("formOverlay").classList.add("show");
        });
}

function closeForm() {
    document.getElementById("formOverlay").classList.remove("show");
}

function validateForm() {
    const name = document.getElementById("inputName").value.trim();
    const err = document.getElementById("errName");
    if (!name) {
        err.style.display = "block";
        return false;
    }
    err.style.display = "none";
    return true;
}


/* ======================================
   DELETE
====================================== */

function openDelete(id, nama) {
    document.getElementById("deleteDesc").innerHTML = `Hapus <b>${escapeHtml(nama)}</b>?`;
    document.getElementById("deleteForm").action = `${DELETE_URL_BASE}${id}/delete/`;
    document.getElementById("deleteOverlay").classList.add("show");
}

function closeDelete() {
    document.getElementById("deleteOverlay").classList.remove("show");
}


/* ======================================
   FLASH BANNER
====================================== */

function initFlashBanner() {
    const params = new URLSearchParams(window.location.search);
    const banner = document.getElementById('flashBanner');

    const successMap = {
        created: 'Artis berhasil ditambahkan.',
        updated: 'Artis berhasil diperbarui.',
        deleted: 'Artis berhasil dihapus.',
    };
    const errorMap = {
        has_events: 'Artis tidak dapat dihapus karena masih terdaftar di event.',
    };

    if (params.get('success') && successMap[params.get('success')]) {
        banner.textContent = successMap[params.get('success')];
        banner.style.background = '#d1fae5';
        banner.style.color = '#065f46';
        banner.style.display = 'block';
    } else if (params.get('error') && errorMap[params.get('error')]) {
        banner.textContent = errorMap[params.get('error')];
        banner.style.background = '#fee2e2';
        banner.style.color = '#991b1b';
        banner.style.display = 'block';
    }

    if (params.get('success') || params.get('error')) {
        window.history.replaceState({}, '', '/artist/');
    }
}


/* ======================================
   INIT
====================================== */

document.addEventListener("DOMContentLoaded", () => {
    document.body.appendChild(document.getElementById('formOverlay'));
    document.body.appendChild(document.getElementById('deleteOverlay'));

    const savedView = localStorage.getItem('artistView');
    if (savedView) currentView = savedView;

    buildGenreMenu();
    render();
    initFlashBanner();

    document.getElementById("btn-view-table").classList.toggle("active", currentView === "table");
    document.getElementById("btn-view-grid").classList.toggle("active", currentView === "grid");

    window.onclick = function(e) {
        if (!e.target.closest("#genreSelectWrap")) {
            document.getElementById("genreMenu").classList.remove("show");
            document.getElementById("genreSelectBtn").classList.remove("open");
        }
    };
});