# app/services/llm/prompts.py
# ============================================================
# Alle Prompt-Templates für die LLM Content-Generierung.
# Zwei Modi:
#   1. GENERISCH: Kein Trainingsbeispiel vorhanden → Standard-Prompt
#   2. FEW-SHOT:  Trainingsbeispiele vorhanden → LLM imitiert den Style
#
# Warum separate Datei? Prompts ändern sich oft beim Feintuning.
# So müssen wir nie den Provider-Code anfassen.
# ============================================================
 
 
def build_instagram_prompt(
    student_name: str,
    exam_type: str,
    details: str | None = None,
    training_examples: list[dict] | None = None
) -> str:
    """
    Baut den kompletten Prompt für Instagram Caption + Hashtags.
 
    Wenn training_examples vorhanden → Few-Shot Prompt mit echten Beispielen.
    Wenn nicht → generischer Prompt mit allgemeinen Anweisungen.
 
    Args:
        student_name: Name des Schülers
        exam_type: z.B. "Autoprüfung", "Motorradprüfung"
        details: Optionale Zusatzinfos
        training_examples: Liste von dicts mit "caption" und "hashtags"
 
    Returns:
        Fertiger Prompt-String für den LLM
    """
 
    # --- Basis-Kontext (immer dabei) ---
    base_context = (
        "Du bist der Social-Media-Manager einer Schweizer Fahrschule (catchKen). "
        "Du schreibst Instagram-Posts auf Schweizerdeutsch / Deutsch. "
        "Der Ton ist herzlich, motivierend und authentisch. "
        "Du freust dich ehrlich für jeden Schüler der bestanden hat."
    )
 
    # --- Details-String zusammenbauen (nur wenn vorhanden) ---
    details_text = f"\nZusätzliche Details: {details}" if details else ""
 
    # --- MODUS 1: Few-Shot mit Trainingsdaten ---
    if training_examples and len(training_examples) > 0:
        # Formatiere die Beispiele als nummerierte Liste
        examples_text = _format_training_examples(training_examples)
 
        return (
            f"{base_context}\n\n"
            f"Hier sind echte Beispiel-Posts aus unserem Instagram-Account. "
            f"Orientiere dich stark an diesem Style — gleicher Ton, ähnliche Länge, "
            f"ähnliche Emoji-Nutzung, gleiche Art von Hashtags:\n\n"
            f"{examples_text}\n\n"
            f"Erstelle jetzt einen neuen Instagram-Post für:\n"
            f"- Schüler/in: {student_name}\n"
            f"- Prüfung: {exam_type}\n"
            f"{details_text}\n\n"
            f"Antworte NUR im folgenden Format (kein anderer Text!):\n"
            f"CAPTION: [deine Caption hier]\n"
            f"HASHTAGS: [deine Hashtags hier]"
        )
 
    # --- MODUS 2: Generischer Prompt ohne Trainingsdaten ---
    return (
        f"{base_context}\n\n"
        f"Erstelle einen Instagram-Post für einen Fahrschüler der bestanden hat.\n\n"
        f"Anforderungen:\n"
        f"- Herzliche Gratulation auf Deutsch (gerne mit Schweizer Touch)\n"
        f"- 2-4 Sätze, nicht zu lang\n"
        f"- Passende Emojis einbauen (🎉🚗💪 etc.)\n"
        f"- 5-10 relevante Hashtags\n\n"
        f"Post-Infos:\n"
        f"- Schüler/in: {student_name}\n"
        f"- Prüfung: {exam_type}\n"
        f"{details_text}\n\n"
        f"Antworte NUR im folgenden Format (kein anderer Text!):\n"
        f"CAPTION: [deine Caption hier]\n"
        f"HASHTAGS: [deine Hashtags hier]"
    )
 
 
def build_tiktok_prompt(
    student_name: str,
    exam_type: str,
    details: str | None = None,
    training_examples: list[dict] | None = None
) -> str:
    """
    Baut den Prompt für TikTok-Beschreibungen.
    TikTok-Style ist anders als Instagram:
    - Kürzer und punchiger
    - Mehr Emojis
    - Trendige Hashtags (#fyp, #fahrschule etc.)
    - Lockerer Ton
    """
 
    base_context = (
        "Du bist der Social-Media-Manager einer Schweizer Fahrschule (catchKen). "
        "Du schreibst TikTok-Beschreibungen auf Schweizerdeutsch / Deutsch. "
        "TikTok-Style: kurz, punchy, viele Emojis, trendige Hashtags. "
        "Weniger formell als Instagram, mehr Energie."
    )
 
    details_text = f"\nZusätzliche Details: {details}" if details else ""
 
    # --- Few-Shot mit TikTok-Trainingsdaten ---
    if training_examples and len(training_examples) > 0:
        examples_text = _format_training_examples(training_examples)
 
        return (
            f"{base_context}\n\n"
            f"Hier sind echte Beispiel-Beschreibungen von unserem TikTok. "
            f"Imitiere diesen Style genau:\n\n"
            f"{examples_text}\n\n"
            f"Erstelle jetzt eine TikTok-Beschreibung für:\n"
            f"- Schüler/in: {student_name}\n"
            f"- Prüfung: {exam_type}\n"
            f"{details_text}\n\n"
            f"Antworte NUR im folgenden Format (kein anderer Text!):\n"
            f"DESCRIPTION: [deine Beschreibung hier]\n"
            f"HASHTAGS: [deine Hashtags hier]"
        )
 
    # --- Generischer TikTok-Prompt ---
    return (
        f"{base_context}\n\n"
        f"Erstelle eine TikTok-Beschreibung für einen Fahrschüler der bestanden hat.\n\n"
        f"Anforderungen:\n"
        f"- Kurz und energiegeladen (1-2 Sätze max)\n"
        f"- Viele Emojis 🎉🔥💪🚗\n"
        f"- TikTok-typische Hashtags (#fyp #viral #fahrschule etc.)\n"
        f"- Lockerer, jugendlicher Ton\n\n"
        f"Post-Infos:\n"
        f"- Schüler/in: {student_name}\n"
        f"- Prüfung: {exam_type}\n"
        f"{details_text}\n\n"
        f"Antworte NUR im folgenden Format (kein anderer Text!):\n"
        f"DESCRIPTION: [deine Beschreibung hier]\n"
        f"HASHTAGS: [deine Hashtags hier]"
    )
 
 
def _format_training_examples(examples: list[dict]) -> str:
    """
    Formatiert Trainings-Posts als nummerierte Liste für den Prompt.
    Private Hilfsfunktion (Underscore-Prefix = "nur intern verwenden").
 
    Args:
        examples: Liste von dicts, z.B.:
            [{"caption": "Herzliche Gratulation...", "hashtags": "#fahrschule..."}]
 
    Returns:
        Formatierter String wie:
            Beispiel 1:
            Caption: Herzliche Gratulation...
            Hashtags: #fahrschule...
    """
    formatted_parts = []  # Sammelt die formatierten Beispiele
 
    for i, example in enumerate(examples, start=1):  # start=1 → zählt ab 1, nicht ab 0
        # Caption ist immer vorhanden (Pflichtfeld im Model)
        part = f"Beispiel {i}:\nCaption: {example['caption']}"
 
        # Hashtags nur anhängen wenn vorhanden
        if example.get("hashtags"):
            part += f"\nHashtags: {example['hashtags']}"
 
        formatted_parts.append(part)
 
    # Alle Beispiele mit Leerzeile dazwischen zusammenfügen
    return "\n\n".join(formatted_parts)
 
 
def parse_instagram_response(raw_response: str) -> dict:
    """
    Parst die LLM-Antwort und extrahiert Caption + Hashtags.
    Der LLM antwortet (hoffentlich) im Format:
        CAPTION: ...
        HASHTAGS: ...
 
    Falls der LLM das Format nicht einhält, geben wir den
    gesamten Text als Caption zurück (graceful fallback).
 
    Returns:
        {"caption": "...", "hashtags": "..."}
    """
    caption = ""
    hashtags = ""
 
    # Zeile für Zeile durchgehen und nach CAPTION: / HASHTAGS: suchen
    for line in raw_response.strip().split("\n"):
        line_stripped = line.strip()
 
        # upper() für case-insensitive Matching ("Caption:" und "CAPTION:" beide ok)
        if line_stripped.upper().startswith("CAPTION:"):
            # Alles nach "CAPTION:" ist die Caption
            caption = line_stripped[len("CAPTION:"):].strip()
 
        elif line_stripped.upper().startswith("HASHTAGS:"):
            hashtags = line_stripped[len("HASHTAGS:"):].strip()
 
    # Fallback: Wenn kein CAPTION:-Prefix gefunden → ganzen Text als Caption
    if not caption:
        caption = raw_response.strip()
 
    return {"caption": caption, "hashtags": hashtags}
 
 
def parse_tiktok_response(raw_response: str) -> dict:
    """
    Parst die TikTok-Antwort. Gleiche Logik wie Instagram,
    aber sucht nach DESCRIPTION: statt CAPTION:.
 
    Returns:
        {"description": "...", "hashtags": "..."}
    """
    description = ""
    hashtags = ""
 
    for line in raw_response.strip().split("\n"):
        line_stripped = line.strip()
 
        if line_stripped.upper().startswith("DESCRIPTION:"):
            description = line_stripped[len("DESCRIPTION:"):].strip()
 
        elif line_stripped.upper().startswith("HASHTAGS:"):
            hashtags = line_stripped[len("HASHTAGS:"):].strip()
 
    if not description:
        description = raw_response.strip()
 
    return {"description": description, "hashtags": hashtags}
 