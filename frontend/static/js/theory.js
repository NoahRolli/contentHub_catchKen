// theory.js – Frontend-Logik für Theorie-Posts
// CRUD, LLM-Generierung, Bearbeiten

const API_THEORY = "/api/theory";
const form = document.getElementById("theory-form");
const theoryList = document.getElementById("theory-list");
const formMessage = document.getElementById("form-message");

let currentGenPostId = null;
let currentEditPostId = null;


// =====================================================
// Theorie-Posts laden und anzeigen
// =====================================================
async function loadPosts() {
    try {
        const res = await fetch(API_THEORY);
        const data = await res.json();

        if (data.total === 0) {
            theoryList.innerHTML = '<p class="empty-state">Noch keine Theorie-Posts. Erstelle den ersten!</p>';
            return;
        }

        theoryList.innerHTML = data.posts.map(post => {
            const captionHtml = post.caption
                ? `<p class="post-caption-preview">${truncate(post.caption, 120)}</p>`
                : "";
            const sourceHtml = post.source
                ? `<p class="post-details-hint">Quelle: ${post.source}</p>`
                : "";

            return `
                <div class="post-item" data-id="${post.id}">
                    <div class="post-info">
                        <h3>${post.topic}</h3>
                        <p>${truncate(post.content, 80)}</p>
                        ${captionHtml}
                        ${sourceHtml}
                    </div>
                    <div class="post-actions">
                        <span class="status-badge status-${post.status}">${post.status}</span>
                        <button class="btn-generate" onclick="generateContent(${post.id})">
                            Generieren
                        </button>
                        <button class="btn-small btn-edit" onclick="openEditModal(${post.id})">
                            Bearbeiten
                        </button>
                        <button class="btn-small btn-delete" onclick="deletePost(${post.id})">
                            Löschen
                        </button>
                    </div>
                </div>
            `;
        }).join("");
    } catch (error) {
        theoryList.innerHTML = '<p class="empty-state">Fehler beim Laden.</p>';
    }
}


// =====================================================
// Neuen Theorie-Post erstellen
// =====================================================
form.addEventListener("submit", async function(e) {
    e.preventDefault();

    const body = {
        topic: document.getElementById("topic").value,
        content: document.getElementById("content").value,
        source: document.getElementById("source").value || null,
    };

    try {
        const res = await fetch(API_THEORY, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (res.ok) {
            showMessage("Theorie-Post erstellt!", "success");
            form.reset();
            loadPosts();
        } else {
            showMessage(`Fehler: ${(await res.json()).detail}`, "error");
        }
    } catch (error) {
        showMessage("Verbindungsfehler.", "error");
    }
});


// =====================================================
// Content generieren (LLM)
// =====================================================
async function generateContent(postId) {
    const btn = document.querySelector(`.post-item[data-id="${postId}"] .btn-generate`);
    const orig = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Generiere...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API_THEORY}/${postId}/generate`, { method: "POST" });

        if (res.ok) {
            openGenModal(postId, await res.json());
        } else {
            showMessage(`Generierung fehlgeschlagen: ${(await res.json()).detail}`, "error");
        }
    } catch (error) {
        showMessage("Verbindungsfehler. Ist Ollama gestartet?", "error");
    } finally {
        btn.innerHTML = orig;
        btn.disabled = false;
    }
}


// =====================================================
// Generate-Modal
// =====================================================
function openGenModal(postId, result) {
    currentGenPostId = postId;
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
    currentGenPostId = null;
}

async function saveGenerated() {
    if (!currentGenPostId) return;

    const body = {
        caption: document.getElementById("modal-ig-caption").value,
        story_text: document.getElementById("modal-tt-description").value,
    };

    try {
        const res = await fetch(`${API_THEORY}/${currentGenPostId}/apply-generated`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (res.ok) {
            showMessage("Caption gespeichert!", "success");
            closeGenModal();
            loadPosts();
        } else {
            showMessage("Fehler beim Speichern.", "error");
        }
    } catch (error) {
        showMessage("Verbindungsfehler.", "error");
    }
}


// =====================================================
// Edit-Modal
// =====================================================
async function openEditModal(postId) {
    currentEditPostId = postId;
    try {
        const res = await fetch(`${API_THEORY}/${postId}`);
        const post = await res.json();

        document.getElementById("edit-topic").value = post.topic;
        document.getElementById("edit-content").value = post.content;
        document.getElementById("edit-source").value = post.source || "";
        document.getElementById("edit-caption").value = post.caption || "";
        document.getElementById("edit-story-text").value = post.story_text || "";
        document.getElementById("edit-status").value = post.status;

        document.getElementById("edit-modal").classList.remove("hidden");
    } catch (error) {
        showMessage("Fehler beim Laden.", "error");
    }
}

function closeEditModal() {
    document.getElementById("edit-modal").classList.add("hidden");
    currentEditPostId = null;
}

async function saveEdit() {
    if (!currentEditPostId) return;

    const body = {
        topic: document.getElementById("edit-topic").value,
        content: document.getElementById("edit-content").value,
        source: document.getElementById("edit-source").value || null,
        caption: document.getElementById("edit-caption").value || null,
        story_text: document.getElementById("edit-story-text").value || null,
        status: document.getElementById("edit-status").value,
    };

    try {
        const res = await fetch(`${API_THEORY}/${currentEditPostId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (res.ok) {
            showMessage("Gespeichert!", "success");
            closeEditModal();
            loadPosts();
        } else {
            showMessage("Fehler beim Speichern.", "error");
        }
    } catch (error) {
        showMessage("Verbindungsfehler.", "error");
    }
}


// =====================================================
// Post löschen
// =====================================================
async function deletePost(postId) {
    if (!confirm("Diesen Theorie-Post wirklich löschen?")) return;
    try {
        const res = await fetch(`${API_THEORY}/${postId}`, { method: "DELETE" });
        if (res.ok) {
            showMessage("Gelöscht.", "success");
            loadPosts();
        }
    } catch (error) {
        showMessage("Fehler.", "error");
    }
}


// =====================================================
// Hilfsfunktionen
// =====================================================
function showMessage(text, type) {
    formMessage.textContent = text;
    formMessage.className = `message ${type}`;
    setTimeout(() => { formMessage.className = "message hidden"; }, 4000);
}

function truncate(text, max) {
    if (!text) return "";
    return text.length > max ? text.substring(0, max) + "…" : text;
}

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { closeGenModal(); closeEditModal(); }
});

document.addEventListener("DOMContentLoaded", loadPosts);
