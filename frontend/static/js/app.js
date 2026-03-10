// app.js – Frontend-Logik für catchKen Content Hub
// Verbindet das HTML-Formular mit der FastAPI-Backend-API
// Lädt Posts, erstellt neue Posts, löscht Posts

// === API Basis-URL ===
const API_BASE = "/api/success";  // Alle Erfolgs-Post Endpunkte

// === DOM-Elemente (HTML-Referenzen) ===
const form = document.getElementById("success-form");  // Das Formular
const postsList = document.getElementById("posts-list");  // Container für Post-Liste
const formMessage = document.getElementById("form-message");  // Feedback-Nachricht


// === Posts laden und anzeigen ===
async function loadPosts() {
    try {
        // GET-Request an die API
        const response = await fetch(API_BASE);  // Holt /api/success/
        const data = await response.json();  // JSON-Antwort parsen

        // Prüfen ob Posts vorhanden sind
        if (data.total === 0) {
            // Keine Posts → Leer-Zustand anzeigen
            postsList.innerHTML = '<p class="empty-state">Noch keine Erfolgs-Posts vorhanden. Erstelle den ersten!</p>';
            return;
        }

        // Posts als HTML rendern
        postsList.innerHTML = data.posts.map(post => `
            <div class="post-item" data-id="${post.id}">
                <div class="post-info">
                    <h3>
                        ${post.student_name ? post.student_name : "Ohne Name"} 
                        – Kat. ${post.category}
                    </h3>
                    <p>
                        📅 ${formatDate(post.exam_date)} 
                        · Erstellt: ${formatDateTime(post.created_at)}
                        ${post.caption ? " · ✍️ Caption vorhanden" : ""}
                    </p>
                </div>
                <div class="post-actions">
                    <span class="status-badge status-${post.status}">${post.status}</span>
                    <button class="btn-small btn-delete" onclick="deletePost(${post.id})">🗑️</button>
                </div>
            </div>
        `).join("");  // Array zu einem HTML-String zusammenfügen

    } catch (error) {
        // Fehler beim Laden anzeigen
        postsList.innerHTML = '<p class="empty-state">Fehler beim Laden der Posts.</p>';
        console.error("Fehler beim Laden:", error);
    }
}


// === Neuen Post erstellen ===
form.addEventListener("submit", async function(event) {
    event.preventDefault();  // Verhindert normales Formular-Absenden (Seiten-Reload)

    // FormData sammelt alle Formularfelder inkl. Datei-Upload
    const formData = new FormData();

    // Pflichtfelder hinzufügen
    formData.append("exam_date", document.getElementById("exam_date").value);
    formData.append("consent_given", document.getElementById("consent_given").checked);
    formData.append("category", document.getElementById("category").value);

    // Optionale Felder hinzufügen (nur wenn ausgefüllt)
    const studentName = document.getElementById("student_name").value;
    if (studentName) {
        formData.append("student_name", studentName);
    }

    // Bild hinzufügen (nur wenn ausgewählt)
    const imageInput = document.getElementById("image");
    if (imageInput.files.length > 0) {
        formData.append("image", imageInput.files[0]);
    }

    try {
        // POST-Request an die API senden
        const response = await fetch(API_BASE, {
            method: "POST",
            body: formData,  // FormData wird automatisch als multipart/form-data gesendet
        });

        if (response.ok) {
            // Erfolg → Grüne Nachricht zeigen
            const newPost = await response.json();
            showMessage(`✅ Erfolgs-Post #${newPost.id} erstellt!`, "success");
            form.reset();  // Formular zurücksetzen
            loadPosts();  // Liste neu laden
        } else {
            // API-Fehler → Rote Nachricht zeigen
            const error = await response.json();
            showMessage(`❌ Fehler: ${error.detail}`, "error");
        }

    } catch (error) {
        // Netzwerk-Fehler
        showMessage("❌ Verbindungsfehler zum Server.", "error");
        console.error("Fehler beim Erstellen:", error);
    }
});


// === Post löschen ===
async function deletePost(postId) {
    // Sicherheitsabfrage bevor gelöscht wird
    if (!confirm("Diesen Post wirklich löschen?")) {
        return;  // Abbrechen wenn Nein geklickt
    }

    try {
        // DELETE-Request an die API
        const response = await fetch(`${API_BASE}/${postId}`, {
            method: "DELETE",
        });

        if (response.ok) {
            showMessage("🗑️ Post gelöscht.", "success");
            loadPosts();  // Liste neu laden
        } else {
            showMessage("❌ Fehler beim Löschen.", "error");
        }

    } catch (error) {
        showMessage("❌ Verbindungsfehler.", "error");
        console.error("Fehler beim Löschen:", error);
    }
}


// === Hilfsfunktionen ===

// Zeigt eine Feedback-Nachricht an (grün oder rot)
function showMessage(text, type) {
    formMessage.textContent = text;
    formMessage.className = `message ${type}`;  // CSS-Klasse setzen (success/error)

    // Nachricht nach 4 Sekunden automatisch ausblenden
    setTimeout(() => {
        formMessage.className = "message hidden";
    }, 4000);
}

// Datum formatieren: "2026-03-10" → "10.03.2026"
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString("de-CH");  // Schweizer Format
}

// Datum + Zeit formatieren: "2026-03-10T13:50:21" → "10.03.2026, 13:50"
function formatDateTime(dateTimeString) {
    if (!dateTimeString) return "";  // Falls kein Datum vorhanden
    const date = new Date(dateTimeString);
    return date.toLocaleString("de-CH", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}


// === Beim Laden der Seite: Posts abrufen ===
document.addEventListener("DOMContentLoaded", loadPosts);