// app.js – Frontend-Logik für catchKen Content Hub
// Verbindet das HTML-Formular mit der FastAPI-Backend-API
// Lädt Posts, erstellt neue Posts, löscht Posts
// Phase 3: Generiert Captions via LLM und zeigt sie im Modal

// === API Basis-URLs ===
const API_BASE = "/api/success";          // Erfolgs-Post Endpunkte
const API_TRAINING = "/api/training-data"; // Trainingsdaten Endpunkte

// === DOM-Elemente (HTML-Referenzen) ===
const form = document.getElementById("success-form");
const postsList = document.getElementById("posts-list");
const formMessage = document.getElementById("form-message");
const trainingStatus = document.getElementById("training-status");

// === Aktuelle Post-ID für Modal (welcher Post wird gerade generiert?) ===
let currentGeneratePostId = null;


// =====================================================
// Posts laden und anzeigen
// =====================================================
async function loadPosts() {
    try {
        const response = await fetch(API_BASE);
        const data = await response.json();

        if (data.total === 0) {
            postsList.innerHTML = '<p class="empty-state">Noch keine Erfolgs-Posts vorhanden. Erstelle den ersten!</p>';
            return;
        }

        // Posts als HTML rendern — jetzt mit Generate-Button
        postsList.innerHTML = data.posts.map(post => `
            <div class="post-item" data-id="${post.id}">
                <div class="post-info">
                    <h3>
                        ${post.student_name ? post.student_name : "Ohne Name"} 
                        – Kat. ${post.category}
                    </h3>
                    <p>
                        ${formatDate(post.exam_date)} 
                        · Erstellt: ${formatDateTime(post.created_at)}
                    </p>
                    ${post.caption 
                        ? `<p class="post-caption-preview">Caption: ${truncate(post.caption, 80)}</p>` 
                        : ""
                    }
                </div>
                <div class="post-actions">
                    <span class="status-badge status-${post.status}">${post.status}</span>
                    <button class="btn-generate" onclick="generateContent(${post.id})" title="Caption via KI generieren">
                        Generieren
                    </button>
                    <button class="btn-small btn-delete" onclick="deletePost(${post.id})" title="Post löschen">Löschen</button>
                </div>
            </div>
        `).join("");

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
            // Trainingsdaten vorhanden → Few-Shot Modus aktiv
            trainingStatus.classList.add("has-data");
            trainingStatus.classList.remove("no-data");
            trainingStatus.innerHTML = `
                <div>
                    <span class="status-text">Few-Shot Modus aktiv</span>
                    <span class="status-count"> · ${stats.total_count} Trainingsbeispiele geladen</span>
                </div>
            `;
        } else {
            // Keine Trainingsdaten → Generischer Modus
            trainingStatus.classList.add("no-data");
            trainingStatus.classList.remove("has-data");
            trainingStatus.innerHTML = `
                <div>
                    <span class="status-text">Generischer Modus</span>
                    <span class="status-count"> · Keine Trainingsdaten. Lade Beispiel-Posts für bessere Ergebnisse.</span>
                </div>
            `;
        }
    } catch (error) {
        // Falls der Endpunkt nicht erreichbar ist → Status ausblenden
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
    if (studentName) {
        formData.append("student_name", studentName);
    }

    const imageInput = document.getElementById("image");
    if (imageInput.files.length > 0) {
        formData.append("image", imageInput.files[0]);
    }

    try {
        const response = await fetch(API_BASE, {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            const newPost = await response.json();
            showMessage(`Erfolgs-Post #${newPost.id} erstellt!`, "success");
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
// Content generieren (LLM aufrufen)
// =====================================================
async function generateContent(postId) {
    // Button-Referenz holen und auf "Loading" setzen
    const button = document.querySelector(`.post-item[data-id="${postId}"] .btn-generate`);
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner"></span> Generiere...';
    button.disabled = true;

    try {
        // POST-Request an den Generate-Endpoint
        const response = await fetch(`${API_BASE}/${postId}/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                use_training_data: true  // Trainingsdaten nutzen wenn vorhanden
            }),
        });

        if (response.ok) {
            const result = await response.json();
            // Modal mit generierten Inhalten öffnen
            openModal(postId, result);
        } else {
            const error = await response.json();
            showMessage(`Generierung fehlgeschlagen: ${error.detail}`, "error");
        }
    } catch (error) {
        showMessage("Verbindungsfehler. Ist Ollama gestartet?", "error");
        console.error("Fehler bei Generierung:", error);
    } finally {
        // Button zurücksetzen
        button.innerHTML = originalText;
        button.disabled = false;
    }
}


// =====================================================
// Modal: Generierte Captions anzeigen
// =====================================================
function openModal(postId, result) {
    currentGeneratePostId = postId;

    // Provider-Info anzeigen
    const providerInfo = document.getElementById("modal-provider-info");
    providerInfo.innerHTML = `
        <span>Provider: <strong>${result.provider}</strong></span>
        <span>${result.used_training_data 
            ? `Few-Shot (${result.training_examples_count} Beispiele)` 
            : "Generischer Modus"
        }</span>
    `;

    // Textfelder befüllen
    document.getElementById("modal-ig-caption").value = result.instagram_caption;
    document.getElementById("modal-ig-hashtags").value = result.instagram_hashtags;
    document.getElementById("modal-tt-description").value = result.tiktok_description;
    document.getElementById("modal-tt-hashtags").value = result.tiktok_hashtags;

    // Modal einblenden
    document.getElementById("generate-modal").classList.remove("hidden");
}

function closeModal() {
    document.getElementById("generate-modal").classList.add("hidden");
    currentGeneratePostId = null;
}

// Modal schliessen mit Escape-Taste
document.addEventListener("keydown", function(event) {
    if (event.key === "Escape") {
        closeModal();
    }
});


// =====================================================
// Generierten Content speichern (Apply)
// =====================================================
async function saveGenerated() {
    if (!currentGeneratePostId) return;

    // Werte aus den Modal-Textfeldern holen (Admin kann sie bearbeitet haben)
    const caption = document.getElementById("modal-ig-caption").value;
    const hashtags = document.getElementById("modal-ig-hashtags").value;
    const storyText = document.getElementById("modal-tt-description").value;

    // FormData bauen für den Apply-Endpoint
    const formData = new FormData();
    formData.append("caption", caption);
    if (hashtags) formData.append("hashtags", hashtags);
    if (storyText) formData.append("story_text", storyText);

    try {
        const response = await fetch(`${API_BASE}/${currentGeneratePostId}/apply-generated`, {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            showMessage("Caption gespeichert!", "success");
            closeModal();
            loadPosts();  // Liste neu laden um Caption-Vorschau anzuzeigen
        } else {
            const error = await response.json();
            showMessage(`Fehler beim Speichern: ${error.detail}`, "error");
        }
    } catch (error) {
        showMessage("Verbindungsfehler.", "error");
        console.error("Fehler beim Speichern:", error);
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
        console.error("Fehler beim Löschen:", error);
    }
}


// =====================================================
// Hilfsfunktionen
// =====================================================

// Zeigt eine Feedback-Nachricht an (grün oder rot)
function showMessage(text, type) {
    formMessage.textContent = text;
    formMessage.className = `message ${type}`;
    setTimeout(() => {
        formMessage.className = "message hidden";
    }, 4000);
}

// Datum formatieren: "2026-03-10" → "10.03.2026"
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString("de-CH");
}

// Datum + Zeit formatieren: "2026-03-10T13:50:21" → "10.03.2026, 13:50"
function formatDateTime(dateTimeString) {
    if (!dateTimeString) return "";
    const date = new Date(dateTimeString);
    return date.toLocaleString("de-CH", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

// Text kürzen mit "..." am Ende
function truncate(text, maxLength) {
    if (!text) return "";
    return text.length > maxLength ? text.substring(0, maxLength) + "…" : text;
}


// =====================================================
// Beim Laden der Seite: Posts und Trainingsstatus abrufen
// =====================================================
document.addEventListener("DOMContentLoaded", function() {
    loadPosts();
    loadTrainingStatus();
});