# Content Pipeline – catchKen Content Hub

## Gesamtübersicht

Wie Content von der Quelle bis zum fertigen Post fliesst:
```mermaid
graph TD
    subgraph Quellen["Content-Quellen"]
        A1[Admin Upload<br>Erfolgs-Post]
        A2[RSS Feed<br>SRF etc.]
        A3[Themenpool<br>Theorie-Fragen]
        A4[Google Reviews<br>Bewertungen]
    end

    subgraph Verarbeitung[" Verarbeitung"]
        B1[Bild + Daten speichern]
        B2[Keyword-Filter<br>Unfall, Verkehr etc.]
        B3[Thema auswählen<br>30-Tage-Sperre prüfen]
        B4[Positive Reviews filtern]
    end

    subgraph LLM["LLM Generierung (Ollama)"]
        C1[Caption + Hashtags]
        C2[Hook + Zusammenfassung<br>+ Präventionstipps]
        C3[Carousel/TikTok-Skript<br>+ Quiz + Fehler]
        C4[Review-Post Caption<br>+ Hashtags]
    end

    subgraph Planung["Planung & Review"]
        D1[DRAFT<br>Vorschlag erstellt]
        D2[Admin Review<br>Caption bearbeiten]
        D3[READY<br>Freigegeben]
        D4[PUBLISHED<br>Exportiert/Gepostet]
    end

    A1 --> B1 --> C1 --> D1
    A2 --> B2 --> C2 --> D1
    A3 --> B3 --> C3 --> D1
    A4 --> B4 --> C4 --> D1
    D1 --> D2 --> D3 --> D4
```

## Status-Workflow
```mermaid
stateDiagram-v2
    [*] --> DRAFT: Content generiert
    DRAFT --> READY: Admin gibt frei
    READY --> PUBLISHED: Export / Posting
    DRAFT --> DRAFT: Admin bearbeitet
    READY --> DRAFT: Zurück zur Bearbeitung
    PUBLISHED --> [*]
```

## News-Post Pipeline (Detail)
```mermaid
graph LR
    A[RSS Feed abrufen] --> B{Keywords gefunden?}
    B -->|Ja| C[Artikel extrahieren]
    B -->|Nein| X[Verwerfen]
    C --> D[LLM Analyse]
    D --> E{Geeignet für Post?}
    E -->|Ja| F[Sicherheits-Post generieren]
    E -->|Nein| G[Als allgemeine<br>Prävention markieren]
    F --> H[DRAFT erstellen]
    G --> H
```

## Theorie-Post Pipeline (Detail)
```mermaid
graph LR
    A[Themenpool laden] --> B{Letzter Post<br>älter als 30 Tage?}
    B -->|Ja| C[Thema auswählen]
    B -->|Nein| A
    C --> D[LLM: Carousel oder<br>TikTok-Skript]
    C --> E[LLM: 3 Quizfragen]
    C --> F[LLM: Häufige Fehler]
    D --> G[DRAFT erstellen]
    E --> G
    F --> G
```