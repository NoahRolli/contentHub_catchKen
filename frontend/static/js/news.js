// news.js – Frontend-Logik für RSS-News
// Quellen verwalten, Feeds scannen, News-Posts generieren

const API_NEWS = "/api/news";
const sourceForm = document.getElementById("source-form");
const sourcesList = document.getElementById("sources-list");
const newsList = document.getElementById("news-list");
const sourceMsg = document.getElementById("source-message");
const scanMsg = document.getElementById("scan-message");

let currentGenItemId = null;


// =====================================================
// Quellen laden
// =====================================================
async function loadSources() {
    try {
        const res = await fetch(`${API_NEWS}/sources`);
        const sources = await res.json();

        if (sources.length === 0) {
            sourcesList.innerHTML = '<p class="empty-state">Keine RSS-Quellen. Füge eine hinzu!</p>';
            return;
        }

        sourcesList.innerHTML = sources.map(s => {
            const statusClass = s.is_active ? "status-ready" : "status-draft";
            const statusText = s.is_active ? "aktiv" : "pausiert";
            const lastScan = s.last_scanned_at
                ? `Letzter Scan: ${new Date(s.last_scanned_at).toLocaleString("de-CH")}`
                : "Noch nicht gescannt";

            return `
                <div class="post-item" data-id="${s.id}">
                    <div class="post-info">
                        <h3>${s.name}</h3>
                        <p>${s.url}</p>
                        <p class="post-details-hint">
                            ${lastScan}
                            ${s.keywords ? ` · Keywords: ${s.keywords}` : ""}
                        </p>
                    </div>
                    <div class="post-actions">
                        <span class="status-badge ${statusClass}">${statusText}</span>
                        <button class="btn-generate" onclick="scanSource(${s.id})">Scannen</button>
                        <button class="btn-small" onclick="toggleSource(${s.id})">
                            ${s.is_active ? "Pausieren" : "Aktivieren"}
                        </button>
                        <button class="btn-small btn-delete" onclick="deleteSource(${s.id})">Löschen</button>
                    </div>
                </div>
            `;
        }).join("");
    } catch (error) {
        sourcesList.innerHTML = '<p class="empty-state">Fehler beim Laden.</p>';
    }
}


// =====================================================
// Quelle hinzufügen
// =====================================================
sourceForm.addEventListener("submit", async function(e) {
    e.preventDefault();

    const body = {
        name: document.getElementById("source-name").value,
        url: document.getElementById("source-url").value,
        keywords: document.getElementById("source-keywords").value || null,
    };

    try {
        const res = await fetch(`${API_NEWS}/sources`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (res.ok) {
            showMsg(sourceMsg, "Quelle hinzugefügt!", "success");
            sourceForm.reset();
            loadSources();
        } else {
            showMsg(sourceMsg, `Fehler: ${(await res.json()).detail}`, "error");
        }
    } catch (error) {
        showMsg(sourceMsg, "Verbindungsfehler.", "error");
    }
});


// =====================================================
// Quelle aktivieren/deaktivieren/löschen
// =====================================================
async function toggleSource(id) {
    await fetch(`${API_NEWS}/sources/${id}/toggle`, { method: "PATCH" });
    loadSources();
}

async function deleteSource(id) {
    if (!confirm("Quelle und alle zugehörigen Artikel löschen?")) return;
    await fetch(`${API_NEWS}/sources/${id}`, { method: "DELETE" });
    loadSources();
    loadNews();
}


// =====================================================
// Feeds scannen
// =====================================================
async function scanAll() {
    showMsg(scanMsg, "Scanne alle Feeds...", "success");
    try {
        const res = await fetch(`${API_NEWS}/scan`, { method: "POST" });
        const result = await res.json();
        showMsg(scanMsg, `${result.scanned} Quellen gescannt, ${result.new_items} neue Artikel gefunden.`, "success");
        loadSources();
        loadNews();
    } catch (error) {
        showMsg(scanMsg, "Scan fehlgeschlagen.", "error");
    }
}

async function scanSource(sourceId) {
    try {
        const res = await fetch(`${API_NEWS}/scan/${sourceId}`, { method: "POST" });
        const items = await res.json();
        showMsg(scanMsg, `${items.length} neue Artikel gefunden.`, "success");
        loadSources();
        loadNews();
    } catch (error) {
        showMsg(scanMsg, "Scan fehlgeschlagen.", "error");
    }
}


// =====================================================
// News-Artikel laden
// =====================================================
async function loadNews() {
    try {
        const res = await fetch(`${API_NEWS}/items?limit=50`);
        const items = await res.json();

        if (items.length === 0) {
            newsList.innerHTML = '<p class="empty-state">Keine Artikel. Füge eine Quelle hinzu und scanne.</p>';
            return;
        }

        newsList.innerHTML = items.map(item => {
            const date = item.published_at
                ? new Date(item.published_at).toLocaleDateString("de-CH")
                : "";
            const keywords = item.keywords_matched
                ? `Keywords: ${item.keywords_matched}`
                : "";
            const processedBadge = item.is_processed
                ? '<span class="status-badge status-published">generiert</span>'
                : '<span class="status-badge status-draft">neu</span>';

            return `
                <div class="post-item" data-id="${item.id}">
                    <div class="post-info">
                        <h3><a href="${item.url}" target="_blank" style="color: var(--text-dark); text-decoration: none;">${item.title}</a></h3>
                        <p>${truncate(item.summary || "", 150)}</p>
                        <p class="post-details-hint">${date} ${keywords ? " · " + keywords : ""}</p>
                    </div>
                    <div class="post-actions">
                        ${processedBadge}
                        <button class="btn-generate" onclick="generatePost(${item.id})" ${item.is_processed ? 'title="Erneut generieren"' : ''}>
                            Generieren
                        </button>
                        <button class="btn-small btn-delete" onclick="deleteItem(${item.id})">Löschen</button>
                    </div>
                </div>
            `;
        }).join("");
    } catch (error) {
        newsList.innerHTML = '<p class="empty-state">Fehler beim Laden.</p>';
    }
}


// =====================================================
// Post generieren aus News-Artikel
// =====================================================
async function generatePost(itemId) {
    const btn = document.querySelector(`.post-item[data-id="${itemId}"] .btn-generate`);
    const orig = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Generiere...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API_NEWS}/items/${itemId}/generate`, { method: "POST" });

        if (res.ok) {
            const result = await res.json();
            openGenModal(itemId, result);
            loadNews(); // Status aktualisieren
        } else {
            showMsg(scanMsg, `Generierung fehlgeschlagen: ${(await res.json()).detail}`, "error");
        }
    } catch (error) {
        showMsg(scanMsg, "Verbindungsfehler. Ist Ollama gestartet?", "error");
    } finally {
        btn.innerHTML = orig;
        btn.disabled = false;
    }
}


// =====================================================
// Generate-Modal
// =====================================================
function openGenModal(itemId, result) {
    currentGenItemId = itemId;
    document.getElementById("modal-provider-info").innerHTML = `
        <span>Provider: <strong>${result.provider}</strong></span>
        <span>${result.used_training_data
            ? `Few-Shot (${result.training_examples_count} Beispiele)`
            : "Generischer Modus"
        }</span>
    `;
    document.getElementById("modal-ig-caption").value = result.instagram_caption;
    document.getElementById("modal-tt-description").value = result.tiktok_description;
    document.getElementById("generate-modal").classList.remove("hidden");
}

function closeGenModal() {
    document.getElementById("generate-modal").classList.add("hidden");
    currentGenItemId = null;
}


// =====================================================
// Artikel löschen
// =====================================================
async function deleteItem(id) {
    if (!confirm("Artikel löschen?")) return;
    await fetch(`${API_NEWS}/items/${id}`, { method: "DELETE" });
    loadNews();
}


// =====================================================
// Hilfsfunktionen
// =====================================================
function showMsg(el, text, type) {
    el.textContent = text;
    el.className = `message ${type}`;
    setTimeout(() => { el.className = "message hidden"; }, 5000);
}

function truncate(text, max) {
    if (!text) return "";
    return text.length > max ? text.substring(0, max) + "…" : text;
}

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeGenModal();
});

document.addEventListener("DOMContentLoaded", function() {
    loadSources();
    loadNews();
});
