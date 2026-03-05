# generate_docs.py – Generiert automatische Dokumentation aus dem Code
# Wird von GitHub Actions (docs.yml) bei jedem Push auf main ausgeführt
# Erstellt eine Übersicht aller Modelle, Endpunkte und Projektstruktur

import os
import ast
import datetime


def get_models_info():
    """Liest alle Modelle aus app/models/ und extrahiert Klassen + Docstrings."""
    models = []
    models_dir = os.path.join("app", "models")
    
    for filename in sorted(os.listdir(models_dir)):
        # Nur Python-Dateien, keine __init__.py
        if not filename.endswith(".py") or filename == "__init__.py":
            continue
        
        filepath = os.path.join(models_dir, filename)
        
        # Datei als AST (Abstract Syntax Tree) parsen
        with open(filepath, "r") as f:
            tree = ast.parse(f.read())
        
        # Alle Klassen in der Datei finden
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node) or "Keine Beschreibung"
                
                # Spalten (Column-Definitionen) zählen
                columns = []
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                columns.append(target.id)
                
                models.append({
                    "name": node.name,
                    "file": filename,
                    "docstring": docstring,
                    "columns": columns
                })
    
    return models


def get_routes_info():
    """Liest die API-Endpunkte aus app/main.py."""
    routes = []
    filepath = os.path.join("app", "main.py")
    
    with open(filepath, "r") as f:
        tree = ast.parse(f.read())
    
    for node in ast.walk(tree):
        # Suche nach @app.get(), @app.post() etc.
        if isinstance(node, ast.AsyncFunctionDef) or isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node) or "Keine Beschreibung"
            
            # Prüfe ob die Funktion einen Decorator hat (z.B. @app.get)
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and hasattr(decorator, 'func'):
                    if hasattr(decorator.func, 'attr'):
                        method = decorator.func.attr.upper()  # get → GET
                        # Pfad aus dem ersten Argument extrahieren
                        if decorator.args:
                            path = decorator.args[0]
                            if isinstance(path, ast.Constant):
                                routes.append({
                                    "method": method,
                                    "path": path.value,
                                    "name": node.name,
                                    "docstring": docstring.split('\n')[0]  # Erste Zeile
                                })
    
    return routes


def generate_markdown():
    """Erstellt die komplette Dokumentation als Markdown."""
    models = get_models_info()
    routes = get_routes_info()
    now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    
    doc = f"""# catchKen Content Hub – Auto-generierte Dokumentation

> Automatisch generiert am {now} via GitHub Actions

---

## API-Endpunkte

| Methode | Pfad | Funktion | Beschreibung |
| ------- | ---- | -------- | ------------ |
"""
    
    for route in routes:
        doc += f"| `{route['method']}` | `{route['path']}` | `{route['name']}` | {route['docstring']} |\n"
    
    doc += f"""
---

## Datenbank-Modelle ({len(models)} Tabellen)

"""
    
    for model in models:
        doc += f"### {model['name']}\n"
        doc += f"**Datei:** `app/models/{model['file']}`\n\n"
        
        # Erste Zeile des Docstrings als Kurzbeschreibung
        first_line = model['docstring'].split('\n')[0]
        doc += f"{first_line}\n\n"
        
        if model['columns']:
            doc += "**Felder:** "
            doc += ", ".join([f"`{col}`" for col in model['columns']])
            doc += "\n\n"
        
        doc += "---\n\n"
    
    doc += """## Projektstruktur
```
app/
├── core/           # Infrastruktur (Config, DB, Security)
├── models/         # Datenbank-Modelle (SQLAlchemy)
├── schemas/        # API Request/Response Formate
├── routers/        # API-Endpunkte
├── services/       # Geschäftslogik
│   └── llm/        # Ollama/OpenAI Integration
├── utils/          # Hilfsfunktionen
└── main.py         # FastAPI Einstiegspunkt
```
"""
    
    return doc


if __name__ == "__main__":
    # Dokumentation generieren und speichern
    markdown = generate_markdown()
    
    # docs/ Ordner erstellen falls nicht vorhanden
    os.makedirs("docs", exist_ok=True)
    
    # In Datei schreiben
    with open("docs/auto-generated.md", "w") as f:
        f.write(markdown)
    
    print("Dokumentation generiert: docs/auto-generated.md")