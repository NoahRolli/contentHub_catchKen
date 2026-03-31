// app.js – Frontend-Logik für catchKen Content Hub
// Verbindet HTML-Formular mit FastAPI-Backend
// Phase 3+: LLM-Generierung, Post bearbeiten, Kalender einplanen

// === API Basis-URLs ===
const API_BASE = "/api/success";
const API_TRAINING = "/api/training-data";
const API_CAL = "/api/calendar";

// === DOM-Elemente ===
const form = document.getElementById("success-form");
const postsList = document.getElementById("posts-list");
const formMessage = document.getElementById("form-message");
const trainingStatus = document.getElementById("training-status");

// === State: welcher Post ist in welchem Modal aktiv ===
let currentGeneratePostId = null;
let currentEditPostId = null;
let currentSchedulePostId = null;


// =====================================================
// Posts laden und anzeigen
// =====================================================
async function loadPosts() {
    try {
        const response = await fetch(API_BASE);
        const data = await response.json();

        if (data.total === 0) {
            postsList.innerHTML = '<p class="empty-state">Noch keine Erfolgs-Posts. Erstelle den ersten!</p>';
            return;
        }

        postsList.innerHTML = data.posts.map(post => {
            // Bild-URL aus dem gespeicherten Pfad ableiten
            // "local_media/uploads/success/abc.jpg" → "/uploads/success/abc.jpg"
            const imgUrl = post.image_path ? pathToUrl(post.image_path) : null;
            const imgHtml = imgUrl ? `<img class="post-thumb" src="${imgUrl}" alt="Bild">` : "";

            // Caption-Vorschau (voller Post-Text inkl. Hashtags)
            const captionHtml = post.caption
                ? `<p class="post-caption-preview">${truncate(post.caption, 120)}</p>`
                : "";

            // Details-Hinweis falls vorhanden
            const detailsHtml = post.details
                ? `<p class="post-details-hint">Details: ${truncate(post.details, 60)}</p>`
                : "";

            return `
                <div class="post-item" data-id="${post.id}">
                    ${imgHtml}
                    <div class="post-info">
                        <h3>${post.student_name || "Ohne Name"} – Kat. ${post.category}</h3>
                        <p>${formatDate(post.exam_date)} · Erstellt: ${formatDateTime(post.created_at)}</p>
                        ${captionHtml}
                        ${detailsHtml}
                    </div>
                    <div class="post-actions">
                        <span class="status-badge status-${post.status}">${post.status}</span>
                        <button class="btn-generate" onclick="generateContent(${post.id})" title="Caption via KI generieren">
                            Generieren
                        </button>
                        <button class="btn-small btn-edit" onclick="openEditModal(${post.id})" title="Post bearbeiten">
                            Bearbeiten
                        </button>
                        <button class="btn-small btn-schedule" onclick="openScheduleModal(${post.id})" title="Im Kalender einplanen">
                            Einplanen
                        </button>
                        <button class="btn-small btn-delete" onclick="deletePost(${post.id})" title="Post löschen">
                            Löschen
                        </button>
                    </div>
                </div>
            `;
        }).join("");

    } catch (error) {
        postsList.innerHTML = '<p class="empty-state">Fehler beim Laden der Posts.</p>';
        console.error("Fehler beim Laden:", error);
    }
}


// =====================================================
// Trainingsdaten-Status laden
// =====================================================
async function loadTrainingStatus() {
    try {
        const response = await fetch(`${API_TRAINING}/stats`);
        const stats = await response.json();

        if (stats.has_training_data) {
            trainingStatus.classList.add("has-data");
            trainingStatus.classList.remove("no-data");
            trainingStatus.innerHTML = `
                <div>
                    <span class="status-text">Few-Shot Modus aktiv</span>
                    <span class="status-count"> · ${stats.total_count} Trainingsbeispiele geladen</span>
                </div>
            `;
        } else {
            trainingStatus.classList.add("no-data");
            trainingStatus.classList.remove("has-data");
            trainingStatus.innerHTML = `
                <div>
                    <span class="status-text">Generischer Modus</span>
                    <span class="status-count"> · Keine Trainingsdaten geladen</span>
                </div>
            `;
        }
    } catch (error) {
        trainingStatus.classList.add("hidden");
        console.error("Trainingsdaten-Status nicht ladbar:", error);
    }
}


// =====================================================
// Neuen Post erstellen
// =====================================================
form.addEventListener("submit", async function(event) {
    event.preventDefault();

    const formData = new FormData();
    formData.append("exam_date", document.getElementById("exam_date").value);
    formData.append("consent_given", document.getElementById("consent_given").checked);
    formData.append("category", document.getElementById("category").value);

    const studentName = document.getElementById("student_name").value;
    if (studentName) formData.append("student_name", studentName);

    // Details für LLM (optional)
    const details = document.getElementById("details").value;
    if (details) formData.append("details", details);

    // Alle ausgewählten Bilder hinzufügen (multiple)
    const imageInput = document.getElementById("images");
    if (imageInput && imageInput.files) {
        for (const file of imageInput.files) {
            formData.append("images", file);
        }
    }

    try {
        const response = await fetch(API_BASE, { method: "POST", body: formData });

        if (response.ok) {
            const newPost = await response.json();
            showMessage(`Post #${newPost.id} erstellt!`, "success");
            form.reset();
            loadPosts();
        } else {
            const error = await response.json();
            showMessage(`Fehler: ${error.detail}`, "error");
        }
    } catch (error) {
        showMessage("Verbindungsfehler zum Server.", "error");
        console.error("Fehler beim Erstellen:", error);
    }
});


// =====================================================
// Content generieren (LLM)
// =====================================================
async function generateContent(postId) {
    const button = document.querySelector(`.post-item[data-id="${postId}"] .btn-generate`);
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner"></span> Generiere...';
    button.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/${postId}/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ use_training_data: true }),
        });

        if (response.ok) {
            openModal(postId, await response.json());
        } else {
            showMessage(`Generierung fehlgeschlagen: ${(await response.json()).detail}`, "error");
        }
    } catch (error) {
        showMessage("Verbindungsfehler. Ist Ollama gestartet?", "error");
        console.error("Fehler bei Generierung:", error);
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}


// =====================================================
// Generate-Modal: Generierten Content anzeigen + speichern
// =====================================================
function openModal(postId, result) {
    currentGeneratePostId = postId;

    document.getElementById("modal-provider-info").innerHTML = `
        <span>Provider: <strong>${result.provider}</strong></span>
        <span>${result.used_training_data
            ? `Few-Shot (${result.training_examples_count} Beispiele)`
            : "Generischer Modus"
        }</span>
    `;

    // Textfelder befüllen — direkt editierbar bevor gespeichert wird
    document.getElementById("modal-ig-caption").value = result.instagram_caption;
    document.getElementById("modal-tt-description").value = result.tiktok_description;
    document.getElementById("generate-modal").classList.remove("hidden");
}

function closeModal() {
    document.getElementById("generate-modal").classList.add("hidden");
    currentGeneratePostId = null;
}

async function saveGenerated() {
    if (!currentGeneratePostId) return;

    const formData = new FormData();
    formData.append("caption", document.getElementById("modal-ig-caption").value);
    const storyText = document.getElementById("modal-tt-description").value;
    if (storyText) formData.append("story_text", storyText);

    try {
        const response = await fetch(`${API_BASE}/${currentGeneratePostId}/apply-generated`, {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            showMessage("Caption gespeichert!", "success");
            closeModal();
            loadPosts();
        } else {
            showMessage(`Fehler: ${(await response.json()).detail}`, "error");
        }
    } catch (error) {
        showMessage("Verbindungsfehler.", "error");
    }
}


// =====================================================
// Edit-Modal: Post bearbeiten
// =====================================================
async function openEditModal(postId) {
    currentEditPostId = postId;

    // Post-Daten laden um Formular vorzubefüllen
    try {
        const response = await fetch(`${API_BASE}/${postId}`);
        const post = await response.json();

        document.getElementById("edit-student-name").value = post.student_name || "";
        document.getElementById("edit-exam-date").value = post.exam_date;
        document.getElementById("edit-category").value = post.category;
        document.getElementById("edit-details").value = post.details || "";
        document.getElementById("edit-caption").value = post.caption || "";
        document.getElementById("edit-story-text").value = post.story_text || "";
        document.getElementById("edit-status").value = post.status;

        document.getElementById("edit-modal").classList.remove("hidden");
    } catch (error) {
        showMessage("Fehler beim Laden des Posts.", "error");
    }
}

function closeEditModal() {
    document.getElementById("edit-modal").classList.add("hidden");
    currentEditPostId = null;
}

async function saveEdit() {
    if (!currentEditPostId) return;

    // Nur Felder senden die einen Wert haben (Partial Update via PUT)
    const body = {
        student_name: document.getElementById("edit-student-name").value || null,
        exam_date: document.getElementById("edit-exam-date").value,
        category: document.getElementById("edit-category").value,
        details: document.getElementById("edit-details").value || null,
        caption: document.getElementById("edit-caption").value || null,
        story_text: document.getElementById("edit-story-text").value || null,
        status: document.getElementById("edit-status").value,
    };

    try {
        const response = await fetch(`${API_BASE}/${currentEditPostId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (response.ok) {
            showMessage("Post gespeichert!", "success");
            closeEditModal();
            loadPosts();
        } else {
            showMessage(`Fehler: ${(await response.json()).detail}`, "error");
        }
    } catch (error) {
        showMessage("Verbindungsfehler.", "error");
    }
}


// =====================================================
// Schedule-Modal: Post im Kalender einplanen
// =====================================================
function openScheduleModal(postId) {
    currentSchedulePostId = postId;
    // Datum auf heute vorsetzen
    document.getElementById("schedule-date").value = new Date().toISOString().split("T")[0];
    document.getElementById("schedule-time").value = "";
    document.getElementById("schedule-platform").value = "both";
    document.getElementById("schedule-modal").classList.remove("hidden");
}

function closeScheduleModal() {
    document.getElementById("schedule-modal").classList.add("hidden");
    currentSchedulePostId = null;
}

async function saveSchedule() {
    if (!currentSchedulePostId) return;

    const data = {
        content_type: "success",
        scheduled_date: document.getElementById("schedule-date").value,
        scheduled_time: document.getElementById("schedule-time").value || null,
        platform: document.getElementById("schedule-platform").value,
        notes: `Verknüpft mit Erfolgs-Post #${currentSchedulePostId}`,
    };

    try {
        const response = await fetch(API_CAL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });

        if (response.ok) {
            showMessage("Post eingeplant!", "success");
            closeScheduleModal();
        } else {
            showMessage(`Fehler: ${(await response.json()).detail}`, "error");
        }
    } catch (error) {
        showMessage("Verbindungsfehler.", "error");
    }
}


// =====================================================
// Post löschen
// =====================================================
async function deletePost(postId) {
    if (!confirm("Diesen Post wirklich löschen?")) return;

    try {
        const response = await fetch(`${API_BASE}/${postId}`, { method: "DELETE" });

        if (response.ok) {
            showMessage("Post gelöscht.", "success");
            loadPosts();
        } else {
            showMessage("Fehler beim Löschen.", "error");
        }
    } catch (error) {
        showMessage("Verbindungsfehler.", "error");
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

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString("de-CH");
}

function formatDateTime(dateTimeString) {
    if (!dateTimeString) return "";
    return new Date(dateTimeString).toLocaleString("de-CH", {
        day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit",
    });
}

function truncate(text, maxLength) {
    if (!text) return "";
    return text.length > maxLength ? text.substring(0, maxLength) + "…" : text;
}

// Konvertiert gespeicherten Dateipfad in Browser-URL
// "local_media/uploads/success/abc.jpg" → "/uploads/success/abc.jpg"
function pathToUrl(filePath) {
    if (!filePath) return "";
    const uploadsIndex = filePath.indexOf("/uploads/");
    return uploadsIndex !== -1 ? filePath.substring(uploadsIndex) : "";
}

// Alle Modals mit Escape-Taste schliessen
document.addEventListener("keydown", function(event) {
    if (event.key === "Escape") {
        closeModal();
        closeEditModal();
        closeScheduleModal();
    }
});

// Beim Laden der Seite: Posts und Trainingsstatus abrufen
document.addEventListener("DOMContentLoaded", function() {
    loadPosts();
    loadTrainingStatus();
});
