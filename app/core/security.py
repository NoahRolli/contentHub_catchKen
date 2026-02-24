# security.py – Sicherheits-Grundgerüst für catchKen Content Hub
# Wird in Phase 2 vollständig implementiert (Login, Auth, etc.)
# Vorerst: Passwort-Hashing und Token-Vorbereitung

from passlib.context import CryptContext  # Bibliothek für sicheres Passwort-Hashing

# === Passwort-Hashing ===
# bcrypt ist der Industriestandard – wandelt Passwörter in nicht-umkehrbare Hashes um
# "deprecated=auto" sorgt dafür, dass alte Hash-Methoden automatisch aktualisiert werden
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Wandelt ein Klartext-Passwort in einen sicheren Hash um.
    
    Beispiel:
        hash_password("mein-passwort") → "$2b$12$LJ3m4ks..."
    Jeder Aufruf erzeugt einen anderen Hash (durch Salt) – das ist gewollt.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Prüft ob ein eingegebenes Passwort zum gespeicherten Hash passt.
    
    Beispiel:
        verify_password("mein-passwort", "$2b$12$LJ3m4ks...") → True
        verify_password("falsches-pw", "$2b$12$LJ3m4ks...") → False
    """
    return pwd_context.verify(plain_password, hashed_password)


# === TODO: Phase 2 ===
# - JWT Token Erstellung (für Login-Sessions)
# - Token-Validierung (für geschützte Endpunkte)
# - Benutzer-Authentifizierung (get_current_user)
# - Rollen-System (Admin vs. Viewer)
# - CORS-Konfiguration