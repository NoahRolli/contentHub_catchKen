// calendar.js – Kalender-Logik für catchKen Content Hub
// Rendert Wochen-/2-Wochen-/Monatsansicht, Drag & Drop, CRUD

const API_CAL = "/api/calendar";

// === State ===
let currentView = "week";       // "week", "twoweek", "month"
let currentDate = new Date();   // Referenz-Datum für Navigation
let draggedPostId = null;       // ID des aktuell gezogenen Posts

// === DOM-Referenzen ===
const calendarTitle = document.getElementById("calendar-title");
const calendarHeader = document.getElementById("calendar-header");
const calendarGrid = document.getElementById("calendar-grid");

// === Wochentage (Deutsch, Montag zuerst) ===
const DAY_NAMES = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];
const MONTH_NAMES = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
];

// Content-Type Labels
const TYPE_LABELS = {
    success: "Erfolg",
    news: "News",
    theory: "Theorie",
    review: "Review"
};


// =====================================================
// Initialisierung
// =====================================================
document.addEventListener("DOMContentLoaded", function () {
    renderDayNames();
    renderCalendar();
    setupEventListeners();
});


// =====================================================
// Event Listeners
// =====================================================
function setupEventListeners() {
    // Navigation
    document.getElementById("btn-prev").addEventListener("click", () => navigate(-1));
    document.getElementById("btn-next").addEventListener("click", () => navigate(1));
    document.getElementById("btn-today").addEventListener("click", goToToday);

    // View Switcher
    document.querySelectorAll(".btn-view").forEach(btn => {
        btn.addEventListener("click", () => switchView(btn.dataset.view));
    });

    // Modal speichern
    document.getElementById("btn-save-entry").addEventListener("click", saveEntry);
}


// =====================================================
// Navigation
// =====================================================
function navigate(direction) {
    if (currentView === "week") {
        currentDate.setDate(currentDate.getDate() + direction * 7);
    } else if (currentView === "twoweek") {
        currentDate.setDate(currentDate.getDate() + direction * 14);
    } else {
        currentDate.setMonth(currentDate.getMonth() + direction);
    }
    renderCalendar();
}

function goToToday() {
    currentDate = new Date();
    renderCalendar();
}

function switchView(view) {
    currentView = view;
    document.querySelectorAll(".btn-view").forEach(b => b.classList.remove("active"));
    document.querySelector(`[data-view="${view}"]`).classList.add("active");
    renderCalendar();
}


// =====================================================
// Kalender rendern
// =====================================================
function renderDayNames() {
    calendarHeader.innerHTML = DAY_NAMES
        .map(name => `<div class="day-name">${name}</div>`)
        .join("");
}

async function renderCalendar() {
    const { startDate, endDate, days } = calculateDateRange();
    updateTitle(startDate, endDate);

    // Posts vom Backend laden
    const startStr = formatDateISO(startDate);
    const endStr = formatDateISO(endDate);
    let posts = [];
    try {
        const res = await fetch(`${API_CAL}/range?start=${startStr}&end=${endStr}`);
        if (res.ok) posts = await res.json();
    } catch (e) {
        console.error("Kalender-Daten nicht ladbar:", e);
    }

    // Grid rendern
    const today = formatDateISO(new Date());
    calendarGrid.innerHTML = days.map(day => {
        const dateStr = formatDateISO(day.date);
        const isToday = dateStr === today;
        const isOther = day.otherMonth;
        const dayPosts = posts.filter(p => p.scheduled_date === dateStr);

        const postsHtml = dayPosts.map(p => `
            <div class="calendar-post type-${p.content_type}"
                 draggable="true"
                 data-id="${p.id}"
                 title="${TYPE_LABELS[p.content_type] || p.content_type}: ${p.caption || 'Kein Text'}">
                ${TYPE_LABELS[p.content_type] || p.content_type}
                ${p.scheduled_time ? " " + p.scheduled_time : ""}
            </div>
        `).join("");

        return `
            <div class="calendar-day ${isToday ? "today" : ""} ${isOther ? "other-month" : ""}"
                 data-date="${dateStr}">
                <div class="day-number">${day.date.getDate()}</div>
                <button class="day-add" onclick="openEntryModal('${dateStr}')" title="Neuer Eintrag">+</button>
                ${postsHtml}
            </div>
        `;
    }).join("");

    // Drag & Drop Setup
    setupDragAndDrop();
}


// =====================================================
// Datumsbereich berechnen
// =====================================================
function calculateDateRange() {
    const days = [];
    let startDate, endDate;

    if (currentView === "month") {
        // Monatsansicht: 1. des Monats bis letzter Tag, aufgefüllt auf volle Wochen
        const first = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
        const last = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);

        // Montag der Woche in der der 1. liegt (getDay: 0=So, 1=Mo...)
        const startOffset = (first.getDay() + 6) % 7;
        startDate = new Date(first);
        startDate.setDate(1 - startOffset);

        // Bis Sonntag der letzten Woche
        const endOffset = (7 - last.getDay()) % 7;
        endDate = new Date(last);
        endDate.setDate(last.getDate() + endOffset);

        for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
            days.push({
                date: new Date(d),
                otherMonth: d.getMonth() !== currentDate.getMonth()
            });
        }
    } else {
        // Wochen-/2-Wochen-Ansicht: Start am Montag
        const dayOfWeek = (currentDate.getDay() + 6) % 7;
        startDate = new Date(currentDate);
        startDate.setDate(currentDate.getDate() - dayOfWeek);

        const numDays = currentView === "week" ? 7 : 14;
        endDate = new Date(startDate);
        endDate.setDate(startDate.getDate() + numDays - 1);

        for (let i = 0; i < numDays; i++) {
            const d = new Date(startDate);
            d.setDate(startDate.getDate() + i);
            days.push({ date: d, otherMonth: false });
        }
    }

    return { startDate, endDate, days };
}


// =====================================================
// Titel updaten
// =====================================================
function updateTitle(start, end) {
    if (currentView === "month") {
        calendarTitle.textContent = `${MONTH_NAMES[currentDate.getMonth()]} ${currentDate.getFullYear()}`;
    } else {
        const s = start.toLocaleDateString("de-CH", { day: "numeric", month: "short" });
        const e = end.toLocaleDateString("de-CH", { day: "numeric", month: "short", year: "numeric" });
        calendarTitle.textContent = `${s} – ${e}`;
    }
}


// =====================================================
// Drag & Drop
// =====================================================
function setupDragAndDrop() {
    // Posts: Drag starten
    document.querySelectorAll(".calendar-post").forEach(el => {
        el.addEventListener("dragstart", (e) => {
            draggedPostId = el.dataset.id;
            el.classList.add("dragging");
            e.dataTransfer.effectAllowed = "move";
        });
        el.addEventListener("dragend", () => {
            el.classList.remove("dragging");
            draggedPostId = null;
        });
    });

    // Tages-Zellen: Drop-Zone
    document.querySelectorAll(".calendar-day").forEach(cell => {
        cell.addEventListener("dragover", (e) => {
            e.preventDefault();
            cell.classList.add("drag-over");
        });
        cell.addEventListener("dragleave", () => {
            cell.classList.remove("drag-over");
        });
        cell.addEventListener("drop", async (e) => {
            e.preventDefault();
            cell.classList.remove("drag-over");
            if (!draggedPostId) return;

            const newDate = cell.dataset.date;
            try {
                await fetch(`${API_CAL}/${draggedPostId}/move`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ scheduled_date: newDate }),
                });
                renderCalendar();
            } catch (err) {
                console.error("Verschieben fehlgeschlagen:", err);
            }
        });
    });
}


// =====================================================
// Modal: Neuer Eintrag
// =====================================================
function openEntryModal(dateStr) {
    document.getElementById("entry-date").value = dateStr;
    document.getElementById("entry-time").value = "";
    document.getElementById("entry-type").value = "success";
    document.getElementById("entry-platform").value = "both";
    document.getElementById("entry-notes").value = "";
    document.getElementById("entry-modal-title").textContent = "Neuer Eintrag";
    document.getElementById("entry-modal").classList.remove("hidden");
}

function closeEntryModal() {
    document.getElementById("entry-modal").classList.add("hidden");
}

async function saveEntry() {
    const data = {
        content_type: document.getElementById("entry-type").value,
        scheduled_date: document.getElementById("entry-date").value,
        scheduled_time: document.getElementById("entry-time").value || null,
        platform: document.getElementById("entry-platform").value,
        notes: document.getElementById("entry-notes").value || null,
    };

    try {
        const res = await fetch(API_CAL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (res.ok) {
            closeEntryModal();
            renderCalendar();
        }
    } catch (err) {
        console.error("Speichern fehlgeschlagen:", err);
    }
}

// Escape schliesst Modal
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeEntryModal();
});


// =====================================================
// Hilfsfunktionen
// =====================================================
function formatDateISO(d) {
    // "2026-03-24" Format (für API)
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}