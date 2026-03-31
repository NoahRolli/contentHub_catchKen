# app/services/llm/prompts.py
# ============================================================
# Alle Prompt-Templates für die LLM Content-Generierung.
# Zwei Modi:
#   1. GENERISCH: Kein Trainingsbeispiel vorhanden → Standard-Prompt
#   2. FEW-SHOT:  Trainingsbeispiele vorhanden → LLM imitiert den Style
#
# Kein strukturiertes Format (kein CAPTION:/HASHTAGS: Split) —
# der LLM gibt einen fertigen Post-Text zurück inkl. Hashtags.
# ============================================================


def build_instagram_prompt(
    student_name: str,
    exam_type: str,
    details: str | None = None,
    training_examples: list[dict] | None = None
) -> str:
    """
    Baut den Prompt für einen fertigen Instagram-Post (Caption + Hashtags in einem Text).

    Args:
        student_name: Name des Schülers
        exam_type: z.B. "Autoprüfung (Kat. B)"
        details: Optionale Zusatzinfos
        training_examples: Liste von dicts mit "caption" und "hashtags"

    Returns:
        Fertiger Prompt-String für den LLM
    """

    base_context = (
        "Du bist der Social-Media-Manager einer Schweizer Fahrschule (catchKen). "
        "Du schreibst Instagram-Posts auf Schweizerdeutsch / Deutsch. "
        "Der Ton ist herzlich, motivierend und authentisch. "
        "Du freust dich ehrlich für jeden Schüler der bestanden hat."
    )

    details_text = f"\nZusätzliche Details: {details}" if details else ""

    # --- MODUS 1: Few-Shot mit Trainingsdaten ---
    if training_examples and len(training_examples) > 0:
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
            f"Antworte NUR mit dem fertigen Post-Text (Caption + Hashtags am Ende). "
            f"Kein anderer Text, keine Erklärungen, keine Anführungszeichen."
        )

    # --- MODUS 2: Generischer Prompt ohne Trainingsdaten ---
    return (
        f"{base_context}\n\n"
        f"Erstelle einen Instagram-Post für einen Fahrschüler der bestanden hat.\n\n"
        f"Anforderungen:\n"
        f"- Herzliche Gratulation auf Deutsch (gerne mit Schweizer Touch)\n"
        f"- 2-4 Sätze, nicht zu lang\n"
        f"- Passende Emojis\n"
        f"- 5-10 relevante Hashtags am Ende des Posts\n\n"
        f"Post-Infos:\n"
        f"- Schüler/in: {student_name}\n"
        f"- Prüfung: {exam_type}\n"
        f"{details_text}\n\n"
        f"Antworte NUR mit dem fertigen Post-Text (Caption + Hashtags am Ende). "
        f"Kein anderer Text, keine Erklärungen, keine Anführungszeichen."
    )


def build_tiktok_prompt(
    student_name: str,
    exam_type: str,
    details: str | None = None,
    training_examples: list[dict] | None = None
) -> str:
    """
    Baut den Prompt für eine fertige TikTok-Beschreibung (Text + Hashtags in einem).
    TikTok-Style: kürzer, punchiger, mehr Energie als Instagram.
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
            f"Antworte NUR mit der fertigen Beschreibung (Text + Hashtags am Ende). "
            f"Kein anderer Text, keine Erklärungen, keine Anführungszeichen."
        )

    # --- Generischer TikTok-Prompt ---
    return (
        f"{base_context}\n\n"
        f"Erstelle eine TikTok-Beschreibung für einen Fahrschüler der bestanden hat.\n\n"
        f"Anforderungen:\n"
        f"- Kurz und energiegeladen (1-2 Sätze max)\n"
        f"- Viele Emojis\n"
        f"- TikTok-typische Hashtags am Ende (#fyp #viral #fahrschule etc.)\n"
        f"- Lockerer, jugendlicher Ton\n\n"
        f"Post-Infos:\n"
        f"- Schüler/in: {student_name}\n"
        f"- Prüfung: {exam_type}\n"
        f"{details_text}\n\n"
        f"Antworte NUR mit der fertigen Beschreibung (Text + Hashtags am Ende). "
        f"Kein anderer Text, keine Erklärungen, keine Anführungszeichen."
    )


def _format_training_examples(examples: list[dict]) -> str:
    """
    Formatiert Trainings-Posts als nummerierte Liste für den Prompt.

    Args:
        examples: Liste von dicts mit "caption" und optional "hashtags"

    Returns:
        Formatierter String mit allen Beispielen
    """
    formatted_parts = []

    for i, example in enumerate(examples, start=1):
        # Beispiel aufbauen: Caption als Basis
        part = f"Beispiel {i}:\n{example['caption']}"

        # Hashtags direkt ans Beispiel anhängen (so sieht der LLM das gewünschte Format)
        if example.get("hashtags"):
            part += f"\n{example['hashtags']}"

        formatted_parts.append(part)

    return "\n\n".join(formatted_parts)


# ============================================================
# THEORIE-PROMPTS — Fahrschultheorie als Social-Media-Content
# ============================================================

def build_theory_instagram_prompt(
    topic: str,
    content: str,
    training_examples: list[dict] | None = None
) -> str:
    """Baut den Prompt für einen Instagram-Theorie-Post."""

    base_context = (
        "Du bist der Social-Media-Manager einer Schweizer Fahrschule (catchKen). "
        "Du schreibst Instagram-Posts die Fahrschultheorie einfach und verständlich erklären. "
        "Der Ton ist lehrreich aber locker — nicht wie ein Lehrbuch, sondern wie ein Freund "
        "der einem einen Tipp gibt. Auf Deutsch mit optionalem Schweizer Touch."
    )

    if training_examples and len(training_examples) > 0:
        examples_text = _format_training_examples(training_examples)
        return (
            f"{base_context}\n\n"
            f"Hier sind Beispiele wie wir Theorie-Posts schreiben:\n\n"
            f"{examples_text}\n\n"
            f"Erstelle jetzt einen Instagram-Post zu folgendem Theorie-Thema:\n"
            f"- Thema: {topic}\n"
            f"- Inhalt: {content}\n\n"
            f"Antworte NUR mit dem fertigen Post-Text (inkl. Hashtags am Ende). "
            f"Kein anderer Text, keine Erklärungen, keine Anführungszeichen."
        )

    return (
        f"{base_context}\n\n"
        f"Erstelle einen Instagram-Post zu folgendem Fahrschul-Theorie-Thema.\n\n"
        f"Anforderungen:\n"
        f"- Erkläre die Regel/das Thema einfach und korrekt\n"
        f"- 2-4 Sätze, verständlich für Fahrschüler\n"
        f"- Passende Emojis\n"
        f"- 5-10 Hashtags am Ende (#fahrschule #theorie #fahrprüfung etc.)\n\n"
        f"Thema: {topic}\n"
        f"Inhalt: {content}\n\n"
        f"Antworte NUR mit dem fertigen Post-Text (inkl. Hashtags am Ende). "
        f"Kein anderer Text, keine Erklärungen, keine Anführungszeichen."
    )


def build_theory_tiktok_prompt(
    topic: str,
    content: str,
    training_examples: list[dict] | None = None
) -> str:
    """Baut den Prompt für eine TikTok-Theorie-Beschreibung."""

    base_context = (
        "Du bist der Social-Media-Manager einer Schweizer Fahrschule (catchKen). "
        "Du schreibst TikTok-Beschreibungen die Fahrschultheorie kurz und catchy erklären. "
        "TikTok-Style: kurz, punchy, Emojis, Hook am Anfang. "
        "Z.B. 'Wusstest du...?' oder 'Diesen Fehler machen 90% bei der Prüfung!'"
    )

    if training_examples and len(training_examples) > 0:
        examples_text = _format_training_examples(training_examples)
        return (
            f"{base_context}\n\n"
            f"Hier sind Beispiele wie wir Theorie-Posts auf TikTok schreiben:\n\n"
            f"{examples_text}\n\n"
            f"Erstelle jetzt eine TikTok-Beschreibung zu:\n"
            f"- Thema: {topic}\n"
            f"- Inhalt: {content}\n\n"
            f"Antworte NUR mit der fertigen Beschreibung (inkl. Hashtags am Ende). "
            f"Kein anderer Text, keine Erklärungen, keine Anführungszeichen."
        )

    return (
        f"{base_context}\n\n"
        f"Erstelle eine TikTok-Beschreibung zu einem Fahrschul-Theorie-Thema.\n\n"
        f"Anforderungen:\n"
        f"- Catchy Hook am Anfang\n"
        f"- 1-2 Sätze, ultra-kurz\n"
        f"- Viele Emojis\n"
        f"- Hashtags am Ende (#fyp #fahrschule #theorie etc.)\n\n"
        f"Thema: {topic}\n"
        f"Inhalt: {content}\n\n"
        f"Antworte NUR mit der fertigen Beschreibung (inkl. Hashtags am Ende). "
        f"Kein anderer Text, keine Erklärungen, keine Anführungszeichen."
    )


def parse_instagram_response(raw_response: str) -> dict:
    """
    Gibt den rohen LLM-Text als Instagram-Caption zurück.
    Kein strukturiertes Parsing nötig — der Text enthält Caption + Hashtags in einem.

    Bereinigt nur führende/nachfolgende Anführungszeichen falls vorhanden.

    Returns:
        {"caption": "Herzliche Gratulation... #fahrschule #bestanden", "hashtags": ""}
    """
    # Anführungszeichen am Anfang/Ende entfernen (LLM umschliesst Text gelegentlich)
    caption = raw_response.strip().strip('"\'')
    return {"caption": caption, "hashtags": ""}


def parse_tiktok_response(raw_response: str) -> dict:
    """
    Gibt den rohen LLM-Text als TikTok-Beschreibung zurück.

    Returns:
        {"description": "Bestanden! #fyp #fahrschule", "hashtags": ""}
    """
    description = raw_response.strip().strip('"\'')
    return {"description": description, "hashtags": ""}
