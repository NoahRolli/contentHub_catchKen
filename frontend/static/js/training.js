// training.js – Trainingsdaten-Verwaltung für alle Content-Typen
// Manuell erstellen, JSON Import, Anzeigen, Filtern, Löschen

const API_TRAINING = "/api/training-data";
const form = document.getElementById("training-form");
const importForm = document.getElementById("import-form");
const trainingList = document.getElementById("training-list");
const formMessage = document.getElementById("form-message");
const importMessage = document.getElementById("import-message");
const statsSection = document.getElementById("training-stats");

// Content-Typ Labels für Anzeige
const TYPE_LABELS = {
    success: "Prüfung bestanden",
    theory: "Theorie",
    news: "News",
    review: "Review",
};


// =====================================================
// Statistiken laden
// =====================================================
async function loadStats() {
    try {
        const res = await fetch(`${API_TRAINING}/stats`);
        const stats = await res.json();

        if (!stats.has_training_data) {
            statsSection.innerHTML = `
                <p style="color: var(--text-medium); font-size: 0.9rem;">
                    Keine Trainingsdaten vorhanden. Füge Beispiel-Posts hinzu damit der LLM
                    im Few-Shot Modus arbeiten kann.
                </p>
            `;
            return;
        }

        // Statistik nach Plattform und Typ aufbereiten
        const platformParts = Object.entries(stats.by_platform)
            .map(([k, v]) => `${k}: ${v}`)
            .join(" · ");
        const typeParts = Object.entries(stats.by_content_type)
            .map(([k, v]) => `${TYPE_LABELS[k] || k}: ${v}`)
            .join(" · ");

        statsSection.innerHTML = `
            <div>
                <span class="status-text">${stats.total_count} Trainingsbeispiele</span>
                <span class="status-count"> · ${platformParts}</span>
            </div>
            <div style="font-size: 0.85rem; color: var(--text-medium); margin-top: 0.3rem;">
                ${typeParts}
            </div>
        `;
    } catch (error) {
        statsSection.innerHTML = "";
    }
}


// =====================================================
// Trainingsdaten laden und anzeigen
// =====================================================
async function loadTrainingData() {
    const platform = document.getElementById("filter-platform").value;
    const contentType = document.getElementById("filter-type").value;

    let url = `${API_TRAINING}/?limit=100`;
    if (platform) url += `&platform=${platform}`;
    if (contentType) url += `&content_type=${contentType}`;

    try {
        const res = await fetch(url);
        const posts = await res.json();

        if (posts.length === 0) {
            trainingList.innerHTML = '<p class="empty-state">Keine Trainingsdaten gefunden.</p>';
            return;
        }

        trainingList.innerHTML = posts.map(post => `
            <div class="post-item" data-id="${post.id}">
                <div class="post-info">
                    <h3>${post.platform} · ${TYPE_LABELS[post.content_type] || post.content_type}</h3>
                    <p>${truncate(post.caption, 150)}</p>
                    ${post.hashtags ? `<p class="post-details-hint">${truncate(post.hashtags, 80)}</p>` : ""}
                </div>
                <div class="post-actions">
                    <button class="btn-small btn-delete" onclick="deleteTraining(${post.id})">
                        Löschen
                    </button>
                </div>
            </div>
        `).join("");
    } catch (error) {
        trainingList.innerHTML = '<p class="empty-state">Fehler beim Laden.</p>';
    }
}


// =====================================================
// Manuell Trainingsdaten erstellen
// =====================================================
form.addEventListener("submit", async function(e) {
    e.preventDefault();

    const body = {
        platform: document.getElementById("train-platform").value,
        content_type: document.getElementById("train-type").value,
        caption: document.getElementById("train-caption").value,
        hashtags: document.getElementById("train-hashtags").value || null,
    };

    try {
        const res = await fetch(API_TRAINING, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (res.ok) {
            showMsg(formMessage, "Trainingsbeispiel gespeichert!", "success");
            form.reset();
            loadTrainingData();
            loadStats();
        } else {
            showMsg(formMessage, `Fehler: ${(await res.json()).detail}`, "error");
        }
    } catch (error) {
        showMsg(formMessage, "Verbindungsfehler.", "error");
    }
});


// =====================================================
// Instagram JSON Import
// =====================================================
importForm.addEventListener("submit", async function(e) {
    e.preventDefault();

    const file = document.getElementById("import-file").files[0];
    if (!file) return;

    const contentType = document.getElementById("import-type").value;
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch(`${API_TRAINING}/import-instagram?content_type=${contentType}`, {
            method: "POST",
            body: formData,
        });

        if (res.ok) {
            const imported = await res.json();
            showMsg(importMessage, `${imported.length} Posts importiert!`, "success");
            importForm.reset();
            loadTrainingData();
            loadStats();
        } else {
            showMsg(importMessage, `Fehler: ${(await res.json()).detail}`, "error");
        }
    } catch (error) {
        showMsg(importMessage, "Verbindungsfehler.", "error");
    }
});


// =====================================================
// Einzelne Trainingsdaten löschen
// =====================================================
async function deleteTraining(postId) {
    if (!confirm("Dieses Trainingsbeispiel löschen?")) return;
    try {
        await fetch(`${API_TRAINING}/${postId}`, { method: "DELETE" });
        loadTrainingData();
        loadStats();
    } catch (error) {
        console.error("Löschen fehlgeschlagen:", error);
    }
}


// =====================================================
// Hilfsfunktionen
// =====================================================
function showMsg(el, text, type) {
    el.textContent = text;
    el.className = `message ${type}`;
    setTimeout(() => { el.className = "message hidden"; }, 4000);
}

function truncate(text, max) {
    if (!text) return "";
    return text.length > max ? text.substring(0, max) + "…" : text;
}

// Filter-Änderungen sofort anwenden
document.getElementById("filter-platform").addEventListener("change", loadTrainingData);
document.getElementById("filter-type").addEventListener("change", loadTrainingData);

// Beim Laden
document.addEventListener("DOMContentLoaded", function() {
    loadStats();
    loadTrainingData();
});
