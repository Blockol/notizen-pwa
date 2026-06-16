import sys
import json
import threading
import os
import re
import ctypes
from datetime import datetime
from pathlib import Path
import requests

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QPushButton,
    QLabel, QMenu, QDialog, QMessageBox, QFrame, QFileDialog,
    QScrollArea, QSizePolicy, QStatusBar, QStackedWidget, QComboBox,
    QInputDialog, QAbstractItemView, QSizeGrip, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QFontComboBox
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, pyqtSlot, QThread, QSize, QPropertyAnimation,
    QEasingCurve, pyqtProperty, QObject, QEvent, QPoint, QRect,
    QParallelAnimationGroup, QBuffer, QByteArray, QUrl, QIODevice
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QAction, QTextCursor,
    QKeySequence, QShortcut, QTextCharFormat, QTextDocument,
    QPainter, QPen, QBrush, QPixmap, QPainterPath, QRegion, QIcon,
    QImage, QTextImageFormat, QTextFrameFormat, QTextLength
)
from PyQt6.QtCore import QRectF
from PyQt6.QtSvg import QSvgRenderer

# ─────────────────────────────────────────────
#  SVG ICON HELPER
# ─────────────────────────────────────────────
_SETTINGS_SVG = (
    '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0'
    'l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51'
    'a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08'
    'a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18'
    'a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39'
    'a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09'
    'a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25'
    'a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>'
)
_PANEL_LEFT_SVG = '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/>'
_FILE_TEXT_SVG  = ('<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>'
                   '<path d="M14 2v4a2 2 0 0 0 2 2h4"/>'
                   '<path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>')
_SEARCH_SVG     = '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>'
_REFRESH_SVG    = ('<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>'
                   '<path d="M21 3v5h-5"/>'
                   '<path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>'
                   '<path d="M8 16H3v5"/>')
_FOLDER_SVG     = ('<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9'
                   'L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>')
_EYE_SVG        = ('<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>'
                   '<circle cx="12" cy="12" r="3"/>')
_ZAP_SVG        = '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>'
_CLOUD_SVG      = '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>'
_PERSON_SVG     = ('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
                   '<circle cx="12" cy="7" r="4"/>')
_BACKUP_SVG     = ('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
                   '<polyline points="7 10 12 15 17 10"/>'
                   '<line x1="12" x2="12" y1="15" y2="3"/>')
_SLIDERS_SVG    = ('<line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="6" y2="3"/>'
                   '<line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="6" y2="3"/>'
                   '<line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="10" y2="3"/>'
                   '<line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="12" y2="12"/>'
                   '<line x1="18" x2="22" y1="16" y2="16"/>')
_EDIT_SVG       = ('<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>'
                   '<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>')
_FOLDER_PLUS_SVG = ('<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>'
                    '<line x1="12" x2="12" y1="11" y2="17"/><line x1="9" x2="15" y1="14" y2="14"/>')
_CHECKLIST_SVG   = ('<line x1="10" x2="21" y1="6" y2="6"/>'
                    '<line x1="10" x2="21" y1="12" y2="12"/>'
                    '<line x1="10" x2="21" y1="18" y2="18"/>'
                    '<polyline points="3 6 4 7 6 5"/>'
                    '<polyline points="3 12 4 13 6 11"/>'
                    '<polyline points="3 18 4 19 6 17"/>')


def _svg_icon(path_data, color, size=16):
    """Render a Lucide-style SVG path to a QIcon at the given color."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">{path_data}</svg>'
    )
    renderer = QSvgRenderer(svg.encode("utf-8"))
    from PyQt6.QtGui import QIcon
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    renderer.render(painter)
    painter.end()
    return QIcon(px)


# ─────────────────────────────────────────────
#  CONFIG & DATA
# ─────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".notizen_config.json"
NOTES_FILE  = Path.home() / "notizen_data.json"
BACKUP_DIR  = Path.home() / ".notizen_backups"
MAX_BACKUPS = 5

THEMES = {
    "dark": {
        "bg":     "#1e1e1e",   # --background-primary  (editor)
        "bg2":    "#171717",   # --background-secondary (sidebar/rail/tabbar)
        "bg3":    "#252525",   # --background-primary-alt (hover/active)
        "border": "#333333",   # solid ~rgba(255,255,255,0.12)
        "accent": "#00ff88",   # --interactive-accent
        "text":   "#dcddde",   # --text-normal
        "muted":  "#6e6e6e",   # --text-muted
        "danger": "#ff4455",
    },
    "light": {
        "bg":     "#ffffff",  "bg2": "#f2f3f5", "bg3": "#e9eaee",
        "border": "#dde1e4",  "accent": "#00a96e", "text": "#1a1a1a",
        "muted":  "#888888",  "danger": "#dd3344",
    }
}

T = THEMES["dark"]  # active theme reference


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {
        "groq_api_key": "", "gemini_api_key": "",
        "ai_provider": "groq", "ai_model_groq": "llama-3.1-8b-instant",
        "ai_model_gemini": "gemini-2.0-flash",
        "drive_credentials": "", "theme": "dark", "open_tabs": []
    }


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def _set_console_visible(visible: bool):
    """Konsolfenster anzeigen oder verstecken (nur Windows)."""
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 1 if visible else 0)
    except Exception:
        pass


def load_notes():
    if NOTES_FILE.exists():
        with open(NOTES_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"notes": [], "version": 1, "last_modified": datetime.now().isoformat()}


def save_notes(data):
    data["last_modified"] = datetime.now().isoformat()
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


# ── BACKUP ────────────────────────────────────
def list_backups():
    """Gibt gespeicherte Backups sortiert nach Datum zurück (neuestes zuerst)."""
    if not BACKUP_DIR.exists():
        return []
    files = sorted(BACKUP_DIR.glob("backup_*.json"), reverse=True)
    return list(files)

def create_backup():
    """Erstellt ein neues Backup. Löscht älteste, wenn MAX_BACKUPS überschritten."""
    BACKUP_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = BACKUP_DIR / f"backup_{ts}.json"
    payload = {
        "created": datetime.now().isoformat(),
        "notes":   json.loads(NOTES_FILE.read_text(encoding="utf-8")) if NOTES_FILE.exists() else {},
        "config":  json.loads(CONFIG_FILE.read_text(encoding="utf-8")) if CONFIG_FILE.exists() else {},
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    # Älteste entfernen wenn Limit überschritten
    all_backups = list_backups()
    for old in all_backups[MAX_BACKUPS:]:
        old.unlink(missing_ok=True)
    return path

def restore_backup(path: Path, notes_only: bool = False):
    """Stellt ein Backup wieder her. notes_only=True: nur Notizen, keine Config."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("notes"):
        NOTES_FILE.write_text(json.dumps(payload["notes"], indent=2, ensure_ascii=False), encoding="utf-8")
    if not notes_only and payload.get("config"):
        CONFIG_FILE.write_text(json.dumps(payload["config"], indent=2, ensure_ascii=False), encoding="utf-8")

# ── ZOOM / UI-FONT ────────────────────────────
_ZOOM    = [1.0]        # veränderlicher Container
_UI_FONT = ['Segoe UI']  # UI-weite Schriftart


def _sz(n: int) -> int:
    """Platzhalter – UI-Zoom deaktiviert, nur Editor-Text wird skaliert."""
    return n


def build_stylesheet():
    return f"""
        QWidget {{
            background-color: {T['bg']};
            color: {T['text']};
            font-family: '{_UI_FONT[0]}', sans-serif;
            font-size: {_sz(13)}px;
        }}
        QLineEdit, QTextEdit {{
            background-color: {T['bg2']};
            border: 1px solid {T['border']};
            border-radius: 6px;
            padding: 6px 10px;
            color: {T['text']};
            selection-background-color: {T['accent']};
            selection-color: #000;
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {T['accent']};
        }}
        QPushButton {{
            background-color: {T['bg2']};
            border: 1px solid {T['border']};
            border-radius: 6px;
            padding: 6px 14px;
            color: {T['text']};
        }}
        QPushButton:hover {{ background-color: {T['bg3']}; }}
        QPushButton:pressed {{ background-color: {T['border']}; }}
        QScrollBar:vertical {{
            background: {T['bg']};
            width: 5px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {T['border']};
            border-radius: 2px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{
            background: {T['bg']};
            height: 0px;
            border: none;
        }}
        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
        }}
        QListWidget::item {{ padding: 0px; border: none; }}
        QListWidget::item:selected {{ background-color: transparent; }}
        QMenu {{
            background-color: {T['bg2']};
            border: 1px solid {T['border']};
            border-radius: 6px;
            padding: 4px;
        }}
        QMenu::item {{ padding: 6px 16px; border-radius: 4px; }}
        QMenu::item:selected {{ background-color: {T['accent']}; color: #000; }}
        QComboBox {{
            background-color: {T['bg2']};
            border: 1px solid {T['border']};
            border-radius: 6px;
            padding: 6px 10px;
            color: {T['text']};
        }}
        QComboBox::drop-down {{ border: none; }}
        QComboBox QAbstractItemView {{
            background-color: {T['bg2']};
            border: 1px solid {T['border']};
            color: {T['text']};
            selection-background-color: {T['accent']};
            selection-color: #000;
        }}
    """


# ─────────────────────────────────────────────
#  GOOGLE DRIVE SYNC
# ─────────────────────────────────────────────
class DriveSync:
    def __init__(self, config):
        self.config = config
        self.service = None
        self.file_id = None
        self._setup()

    def _setup(self):
        creds_path = self.config.get("drive_credentials", "")
        if not creds_path or not os.path.exists(creds_path):
            return
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            SCOPES = ["https://www.googleapis.com/auth/drive"]
            token_path = Path.home() / ".notizen_token.json"
            creds = None
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                with open(token_path, "w") as f:
                    f.write(creds.to_json())
            self.service = build("drive", "v3", credentials=creds)
            self._find_or_create_file()
            print(f"[SYNC] Drive file_id: {self.file_id}")
        except Exception as e:
            print(f"Drive setup error: {e}")

    def _find_or_create_file(self):
        try:
            results = self.service.files().list(
                q="name='notizen_sync.json' and trashed=false",
                fields="files(id, name)",
                orderBy="createdTime"
            ).execute()
            files = results.get("files", [])
            if len(files) > 1:
                print(f"[SYNC] WARNUNG: {len(files)} 'notizen_sync.json' Dateien gefunden! IDs: {[f['id'] for f in files]}")
                print(f"[SYNC] Verwende älteste: {files[0]['id']}")
            if files:
                self.file_id = files[0]["id"]
            else:
                meta = {"name": "notizen_sync.json", "mimeType": "application/json"}
                f = self.service.files().create(body=meta, fields="id").execute()
                self.file_id = f.get("id")
        except Exception as e:
            print(f"Drive file error: {e}")

    def upload(self, data):
        if not self.service or not self.file_id:
            return False
        try:
            from googleapiclient.http import MediaIoBaseUpload
            import io
            content = json.dumps(data, ensure_ascii=False).encode("utf-8")
            media = MediaIoBaseUpload(io.BytesIO(content), mimetype="application/json")
            self.service.files().update(fileId=self.file_id, media_body=media).execute()
            return True
        except Exception as e:
            print(f"Drive upload error: {e}")
            return False

    def download(self):
        if not self.service or not self.file_id:
            return None
        try:
            import io
            from googleapiclient.http import MediaIoBaseDownload
            request = self.service.files().get_media(fileId=self.file_id)
            fh = io.BytesIO()
            dl = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = dl.next_chunk()
            fh.seek(0)
            return json.loads(fh.read().decode("utf-8"))
        except Exception as e:
            print(f"Drive download error: {e}")
            return None

    def is_connected(self):
        return self.service is not None and self.file_id is not None


# ─────────────────────────────────────────────
#  AI WORKER THREAD
# ─────────────────────────────────────────────
class AIWorker(QThread):
    result_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, config, instruction, text):
        super().__init__()
        self.config = config
        self.instruction = instruction
        self.text = text

    def run(self):
        provider = self.config.get("ai_provider", "groq")
        try:
            if provider == "gemini":
                self._run_gemini()
            else:
                self._run_groq()
        except Exception as e:
            self.error.emit(str(e))

    def _run_groq(self):
        api_key = self.config.get("groq_api_key", "")
        if not api_key:
            self.error.emit("Groq API Key fehlt")
            return
        model = self.config.get("ai_model_groq", "llama-3.1-8b-instant")
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": self.instruction},
                    {"role": "user", "content": self.text}
                ],
                "max_tokens": 1024
            },
            timeout=30
        )
        resp.raise_for_status()
        self.result_ready.emit(resp.json()["choices"][0]["message"]["content"])

    def _run_gemini(self):
        api_key = self.config.get("gemini_api_key", "")
        if not api_key:
            self.error.emit("Gemini API Key fehlt")
            return
        model = self.config.get("ai_model_gemini", "gemini-2.0-flash")
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": f"{self.instruction}\n\n{self.text}"}]}]
            },
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        self.result_ready.emit(text)


# ─────────────────────────────────────────────
#  AI SEARCH WORKER
# ─────────────────────────────────────────────
class AISearchWorker(QThread):
    result_ready = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, config, query, notes):
        super().__init__()
        self.config = config
        self.query = query
        self.notes = notes

    @staticmethod
    def _first_n_words(text, n=600):
        words = text.split()
        return " ".join(words[:n])

    def run(self):
        # Einfache Keyword-Vorfilterung: Notizen ohne Ueberschneidung mit Query nach hinten
        query_words = set(w.lower() for w in self.query.split() if len(w) > 2)
        def _score(note):
            blob = (note.get("title", "") + " " + note.get("content", "")).lower()
            return sum(1 for w in query_words if w in blob)
        sorted_notes = sorted(self.notes, key=_score, reverse=True)
        # Top 12 relevante Notizen nehmen (mind. Score 0 — alle wenn wenige Notizen)
        top = sorted_notes[:12]

        context = ""
        for n in top:
            title = n.get("title", "Unbenannt")
            content = self._first_n_words(n.get("content", "").replace("\n", " "), 600)
            context += f"--- Notiz ID:{n['id']} ---\nTitel: {title}\nInhalt: {content}\n\n"

        instruction = (
            "Du bist ein Notiz-Assistent. Du analysierst ausschliesslich die unten bereitgestellten Notizen "
            "und beantwortest Fragen NUR auf Basis der darin enthaltenen Informationen. "
            "WICHTIG: Erfinde keine Informationen. Antworte nicht aus deinem allgemeinen Wissen. "
            "Wenn die Notizen keine relevante Information zur Frage enthalten, schreibe das ehrlich in 'answer'. "
            "Als 'sources' liste NUR Notizen auf, die direkt relevante Informationen fuer die Antwort enthalten — "
            "keine Notizen einfuegen, die nur vage oder gar nicht passen. "
            "Gib das Ergebnis als JSON zurueck: "
            "{\"answer\": \"Deine Antwort basierend auf den Notizen...\", "
            "\"sources\": [{\"id\": \"...\", \"title\": \"...\", \"reason\": \"Welche konkrete Info aus dieser Notiz wurde genutzt\"}]}. "
            "Maximal 5 Quellen. Nur JSON, kein anderer Text."
        )
        prompt = f"Frage: {self.query}\n\nNotizen:\n{context}"

        provider = self.config.get("ai_provider", "groq")
        try:
            if provider == "gemini":
                result_text = self._call_gemini(instruction, prompt)
            else:
                result_text = self._call_groq(instruction, prompt)
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(result_text)
            self.result_ready.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def _call_groq(self, instruction, prompt):
        api_key = self.config.get("groq_api_key", "")
        if not api_key:
            raise ValueError("Groq API Key fehlt")
        model = self.config.get("ai_model_groq", "llama-3.1-8b-instant")
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1024
            },
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_gemini(self, instruction, prompt):
        api_key = self.config.get("gemini_api_key", "")
        if not api_key:
            raise ValueError("Gemini API Key fehlt")
        model = self.config.get("ai_model_gemini", "gemini-2.0-flash")
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": f"{instruction}\n\n{prompt}"}]}]
            },
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


# ─────────────────────────────────────────────
#  TOGGLE SWITCH WIDGET
# ─────────────────────────────────────────────
class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._thumb_x_val = 26.0 if checked else 4.0
        self.setFixedSize(48, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"_thumb_x")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def isChecked(self):
        return self._checked

    def setChecked(self, val):
        self._checked = val
        self._thumb_x_val = self._target_x()
        self.update()

    def _target_x(self):
        return 26 if self._checked else 4

    def _get_thumb_x(self):
        return self._thumb_x_val

    def _set_thumb_x(self, val):
        self._thumb_x_val = val
        self.update()

    _thumb_x = pyqtProperty(float, _get_thumb_x, _set_thumb_x)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self._anim.stop()
            self._anim.setStartValue(float(self._thumb_x_val))
            self._anim.setEndValue(float(self._target_x()))
            self._anim.start()
            self.toggled.emit(self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = h / 2

        # Track
        track_color = QColor(T['accent']) if self._checked else QColor(T['bg3'])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track_color)
        p.drawRoundedRect(0, 0, w, h, r, r)

        # Thumb
        p.setBrush(QColor("#ffffff"))
        thumb_d = h - 8
        p.drawEllipse(int(self._thumb_x_val), 4, thumb_d, thumb_d)
        p.end()


# ─────────────────────────────────────────────
#  NOTE ITEM WIDGET  (Obsidian flat-row style)
# ─────────────────────────────────────────────
class NoteItem(QWidget):
    def __init__(self, note, is_active=False, folder_child=False):
        super().__init__()
        self.note = note
        self._build(is_active, folder_child)

    def _build(self, is_active, folder_child):
        # Transparent to mouse events → QListWidget handles Shift/Ctrl+Click natively
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left accent bar (active indicator, 2px like Obsidian)
        self._accent_bar = QWidget()
        self._accent_bar.setFixedWidth(2)
        self._accent_bar.setStyleSheet(f"background: {T['accent'] if is_active else 'transparent'};")
        layout.addWidget(self._accent_bar)

        # Content row — no custom hover/bg, QListWidget stylesheet handles that
        self._content_widget = QWidget()
        active_bg = "rgba(0,255,136,0.08)" if is_active else "transparent"
        self._content_widget.setStyleSheet(f"QWidget {{ background: {active_bg}; }}")
        cl = QHBoxLayout(self._content_widget)
        left_pad = 28 if folder_child else 14
        cl.setContentsMargins(left_pad, 5, 10, 5)
        cl.setSpacing(6)

        title = self.note.get("title") or "Unbenannte Notiz"
        self._title_label = QLabel(title[:40])
        self._title_label.setStyleSheet(f"""
            color: {T['accent'] if is_active else T['text']};
            font-size: {_sz(13)}px;
            font-weight: {'500' if is_active else '400'};
            border: none; background: transparent;
        """)
        cl.addWidget(self._title_label, 1)

        date = self.note.get("modified", "")[:10]
        d = QLabel(date)
        d.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(10)}px; border: none; background: transparent;")
        cl.addWidget(d)

        layout.addWidget(self._content_widget, 1)
        self.setFixedHeight(32)

    def set_active(self, is_active):
        self._accent_bar.setStyleSheet(f"background: {T['accent'] if is_active else 'transparent'};")
        active_bg = "rgba(0,255,136,0.08)" if is_active else "transparent"
        self._content_widget.setStyleSheet(f"QWidget {{ background: {active_bg}; }}")
        self._title_label.setStyleSheet(f"""
            color: {T['accent'] if is_active else T['text']};
            font-size: {_sz(13)}px;
            font-weight: {'500' if is_active else '400'};
            border: none; background: transparent;
        """)


# ─────────────────────────────────────────────
#  FOLDER ITEM WIDGET
# ─────────────────────────────────────────────
class FolderItem(QWidget):
    def __init__(self, folder, collapsed=False):
        super().__init__()
        self.folder_id = folder["id"]
        self._build(folder, collapsed)

    def _build(self, folder, collapsed):
        # Transparent to mouse events → QListWidget handles clicks/itemClicked
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        spacer = QWidget()
        spacer.setFixedWidth(2)
        spacer.setStyleSheet("background: transparent;")
        layout.addWidget(spacer)

        content = QWidget()
        content.setStyleSheet("QWidget { background: transparent; }")
        cl = QHBoxLayout(content)
        cl.setContentsMargins(10, 0, 10, 0)
        cl.setSpacing(6)

        chev = QLabel("\u25B6" if collapsed else "\u25BC")
        chev.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(8)}px; background: transparent; border: none;")
        cl.addWidget(chev)

        name_lbl = QLabel(folder.get("name", "Ordner"))
        name_lbl.setStyleSheet(
            f"color: {T['text']}; font-size: {_sz(13)}px; font-weight: 600; "
            f"background: transparent; border: none;"
        )
        cl.addWidget(name_lbl, 1)
        layout.addWidget(content, 1)
        self.setFixedHeight(32)


# ─────────────────────────────────────────────
#  SEARCH RESULT ITEM  (with highlighted preview)
# ─────────────────────────────────────────────
class SearchResultItem(QWidget):
    def __init__(self, note, query):
        super().__init__()
        self.note_id = note["id"]
        self._build(note, query)

    def _build(self, note, query):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(3)

        content = note.get("content", "")
        count = len(re.findall(re.escape(query), content, re.IGNORECASE)) if query else 0

        # ── Header: chevron + title + match count ──
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(5)

        chev = QLabel("\u2304")
        chev.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(10)}px; background: transparent;")
        hl.addWidget(chev)

        title_lbl = QLabel(note.get("title") or "Unbenannte Notiz")
        title_lbl.setStyleSheet(f"color: {T['text']}; font-size: {_sz(13)}px; font-weight: 500; background: transparent;")
        hl.addWidget(title_lbl, 1)

        count_lbl = QLabel(str(count))
        count_lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(11)}px; background: transparent;")
        hl.addWidget(count_lbl)
        layout.addWidget(header)

        # ── Content preview with yellow-highlighted query ──
        if query and content:
            idx = content.lower().find(query.lower())
            if idx >= 0:
                start = max(0, idx - 50)
                end = min(len(content), idx + len(query) + 130)
                raw = content[start:end].replace("\n", " ")
                # HTML-escape then highlight
                raw_esc = raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                highlighted = re.sub(
                    re.escape(query),
                    lambda m: f'<span style="background:rgba(255,200,0,0.5);color:#111;border-radius:2px">{m.group()}</span>',
                    raw_esc,
                    flags=re.IGNORECASE
                )
                prefix = "..." if start > 0 else ""
                suffix = "..." if end < len(content) else ""
                html = f'{prefix}{highlighted}{suffix}'

                preview = QLabel(html)
                preview.setTextFormat(Qt.TextFormat.RichText)
                preview.setWordWrap(True)
                preview.setStyleSheet(f"""
                    QLabel {{
                        color: {T['muted']}; font-size: {_sz(12)}px; line-height: 1.4;
                        background: {T['bg3']}; border: 1px solid {T['border']};
                        border-radius: 4px; padding: 5px 7px;
                    }}
                """)
                layout.addWidget(preview)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("QWidget { background: transparent; } QWidget:hover { background: rgba(255,255,255,0.03); }")


# ─────────────────────────────────────────────
#  ICON RAIL (40px, always visible)
# ─────────────────────────────────────────────
class IconRail(QWidget):
    toggle_clicked = pyqtSignal()
    files_clicked = pyqtSignal()
    quick_switch_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    sync_clicked = pyqtSignal()
    tasks_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(44)   # --ribbon-width: 44px
        self.active_btn = None
        self._build()

    def _build(self):
        self.setStyleSheet(f"background-color: {T['bg2']}; border-right: 1px solid {T['border']};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(2)

        self.btn_toggle = self._make_btn(_PANEL_LEFT_SVG, "Toggle Sidebar", size=17)
        self.btn_toggle.clicked.connect(self.toggle_clicked.emit)
        layout.addWidget(self.btn_toggle)

        self.btn_files = self._make_btn(_FILE_TEXT_SVG, "Dateien", size=16)
        self.btn_files.clicked.connect(lambda: self._activate("files"))
        layout.addWidget(self.btn_files)

        self.btn_search = self._make_btn(_SEARCH_SVG, "Schnellauswahl", size=16)
        self.btn_search.clicked.connect(self.quick_switch_clicked.emit)
        layout.addWidget(self.btn_search)

        self.btn_tasks = self._make_btn(_CHECKLIST_SVG, "Aufgaben", size=16)
        self.btn_tasks.clicked.connect(lambda: self._activate("tasks"))
        layout.addWidget(self.btn_tasks)

        layout.addStretch()

        self.btn_sync = self._make_btn(_REFRESH_SVG, "Synchronisieren", size=16)
        self.btn_sync.clicked.connect(self.sync_clicked.emit)
        self.btn_sync.setVisible(False)
        layout.addWidget(self.btn_sync)

        # Settings (SVG) — nur sichtbar wenn Sidebar ausgeklappt
        self.btn_settings = QPushButton()
        self.btn_settings.setToolTip("Einstellungen")
        self.btn_settings.setFixedSize(40, 40)
        self.btn_settings.setIcon(_svg_icon(_SETTINGS_SVG, T['muted'], 16))
        self.btn_settings.setIconSize(QSize(16, 16))
        self.btn_settings.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; border-radius: 6px;
                          border-left: 2px solid transparent; }}
            QPushButton:hover {{ background: rgba(255,255,255,0.07); }}
        """)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        self.btn_settings.setVisible(False)
        layout.addWidget(self.btn_settings)

    def _make_btn(self, svg_path, tooltip, size=16):
        btn = QPushButton()
        btn.setToolTip(tooltip)
        btn.setFixedSize(40, 40)
        btn.setIcon(_svg_icon(svg_path, T['muted'], size))
        btn.setIconSize(QSize(size, size))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; border-radius: 6px;
                border-left: 2px solid transparent;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.07); }}
        """)
        return btn

    def _activate(self, which):
        if which == "files":
            self.files_clicked.emit()
        elif which == "tasks":
            self.tasks_clicked.emit()
        self._highlight(which)

    def _highlight(self, which):
        svgs = {"files": _FILE_TEXT_SVG, "search": _SEARCH_SVG, "tasks": _CHECKLIST_SVG}
        for btn, name in [(self.btn_files, "files"), (self.btn_search, "search"), (self.btn_tasks, "tasks")]:
            if name == which:
                btn.setIcon(_svg_icon(svgs[name], T['muted'], 16))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(255,255,255,0.07); border: none; border-radius: 6px;
                    }}
                    QPushButton:hover {{ background: rgba(255,255,255,0.1); }}
                """)
            else:
                btn.setIcon(_svg_icon(svgs[name], T['muted'], 16))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent; border: none; border-radius: 6px;
                        border-left: 2px solid transparent;
                    }}
                    QPushButton:hover {{ background: rgba(255,255,255,0.07); }}
                """)

    def set_sidebar_expanded(self, expanded):
        self.btn_settings.setVisible(expanded)
        self.btn_sync.setVisible(expanded)


# ─────────────────────────────────────────────
#  TASK ITEM
# ─────────────────────────────────────────────
class _TaskClickFilter(QObject):
    """Fängt alle Maus-Events auf TaskItem + seinen Kindern ab."""
    def eventFilter(self, obj, event):
        item = obj
        while item and not isinstance(item, TaskItem):
            item = item.parent()
        if not item or not item._panel:
            return False

        etype = event.type()
        _dpath = Path.home() / "task_filter_debug.log"

        if etype == QEvent.Type.MouseButtonPress:
            btn = event.button()
            if btn == Qt.MouseButton.LeftButton:
                cb = item.check_btn
                local = cb.mapFromGlobal(obj.mapToGlobal(event.pos()))
                if cb.rect().contains(local):
                    cb.setChecked(not cb.isChecked())
                    item._on_toggled(cb.isChecked())
                else:
                    item._panel._on_item_clicked(item.task_id, event.modifiers())
                return True
            # Rechtsklick durchlassen → wird zu ContextMenu
            return False
        elif etype == QEvent.Type.ContextMenu:
            gp = event.globalPos()
            item._panel._on_item_context(item.task_id, gp)
            return True
        return False


class TaskItem(QWidget):
    toggled = pyqtSignal(str, bool)
    deleted = pyqtSignal(str)

    _filter = None  # shared event filter

    def __init__(self, task_id, text, done=False, panel=None):
        super().__init__()
        self.task_id = task_id
        self._done = done
        self._selected = False
        self._panel = panel
        self._build(text)
        # Event-Filter auf sich selbst + alle Kinder installieren (NACH _build!)
        if TaskItem._filter is None:
            TaskItem._filter = _TaskClickFilter()
        flt = TaskItem._filter
        self.installEventFilter(flt)
        self.check_btn.installEventFilter(flt)
        self.label.installEventFilter(flt)

    def _build(self, text):
        self.setFixedHeight(30)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(7)

        self.check_btn = QPushButton()
        self.check_btn.setFixedSize(14, 14)
        self.check_btn.setCheckable(True)
        self.check_btn.setChecked(self._done)
        self._update_check_style()
        layout.addWidget(self.check_btn)

        self.label = QLabel(text)
        self.label.setWordWrap(False)
        self._update_label_style()
        layout.addWidget(self.label, 1)

    def set_selected(self, sel):
        self._selected = sel
        if sel:
            self.label.setStyleSheet(
                f"color: {T['text']}; font-size: 12px;"
                f" background: rgba(100,200,120,0.13); border: none;"
                f" border-radius: 3px; padding: 0 2px;"
            )
        else:
            self._update_label_style()

    def _on_toggled(self, checked):
        self._done = checked
        self._update_check_style()
        self._update_label_style()
        self.toggled.emit(self.task_id, checked)

    def _update_label_style(self):
        if self._done:
            self.label.setStyleSheet(
                f"color: {T['muted']}; font-size: 12px; background: transparent; border: none;"
            )
        else:
            self.label.setStyleSheet(
                f"color: {T['text']}; font-size: 12px; background: transparent; border: none;"
            )

    def _update_check_style(self):
        if self.check_btn.isChecked():
            self.check_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {T['accent']}; border: 1.5px solid {T['accent']};
                    border-radius: 3px; color: #000; font-size: 9px; font-weight: bold;
                }}
            """)
            self.check_btn.setText("✓")
        else:
            self.check_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: 1.5px solid {T['border']};
                    border-radius: 3px;
                }}
                QPushButton:hover {{ border-color: {T['accent']}; }}
            """)
            self.check_btn.setText("")


# ─────────────────────────────────────────────
#  SLIDE CLIP  (animiert maximumWidth, clippt child)
# ─────────────────────────────────────────────
class _SlideClip(QWidget):
    """Wrapper der seinen child-Widget durch maximumWidth-Animation clipped.
    Der child bleibt immer 240px breit → kein Reflow während der Animation."""

    _W = 240

    def __init__(self, child: QWidget):
        super().__init__()
        self._child = child
        child.setParent(self)
        child.hide()   # versteckt bis animate_open aufgerufen wird
        self.setMinimumWidth(0)
        self.setMaximumWidth(0)
        # sizeHint muss 240 zurückgeben, sonst gibt das Layout immer 0px Breite
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._anim = None

    def sizeHint(self):
        return QSize(self._W, 0)

    def resizeEvent(self, event):
        h = self.height()
        if h <= 0 and self.parentWidget():
            h = self.parentWidget().height()
        # Nur bei Höhenänderung setGeometry aufrufen — nicht bei Width-Animation,
        # da jeder setGeometry-Aufruf die ScrollArea-Position auf 0 resettet
        if self._child.height() != h:
            self._child.setGeometry(0, 0, self._W, h)

    def is_open(self):
        return self.maximumWidth() > 0

    def animate_open(self, on_done=None):
        if self._anim and self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()
        h = self.height()
        if h <= 0 and self.parentWidget():
            h = self.parentWidget().height()
        if self._child.height() != h:
            self._child.setGeometry(0, 0, self._W, h)
        self._child.show()   # showEvent → _apply_scroll
        anim = QPropertyAnimation(self, b"maximumWidth")
        anim.setDuration(260)
        anim.setStartValue(self.maximumWidth())
        anim.setEndValue(self._W)
        anim.setEasingCurve(QEasingCurve.Type.OutQuint)
        if on_done:
            anim.finished.connect(on_done)
        self._anim = anim
        anim.start()

    def animate_close(self, on_done=None):
        if self._anim and self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()
        anim = QPropertyAnimation(self, b"maximumWidth")
        anim.setDuration(200)
        anim.setStartValue(self.maximumWidth())
        anim.setEndValue(0)
        anim.setEasingCurve(QEasingCurve.Type.InQuint)
        if on_done:
            anim.finished.connect(on_done)
        anim.finished.connect(self._child.hide)   # nach Animation verstecken
        self._anim = anim
        anim.start()


# ─────────────────────────────────────────────
#  TASK PANEL
# ─────────────────────────────────────────────
class TaskPanel(QWidget):
    """Aufgabenliste: AKTUELL + ZUKUNFT sichtbar, ERLEDIGT per Mausrad-Hochscrollen."""

    def __init__(self):
        super().__init__()
        self.setFixedWidth(240)
        self._tasks = []
        self._save_fn = None
        self._selection = []    # list of selected task_ids
        self._last_clicked = None  # task_id for shift-range
        self._build()

    # ── BUILD ──
    def _build(self):
        self.setStyleSheet(
            f"background-color: {T['bg2']}; border-right: 1px solid {T['border']};"
        )
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header_bar = QWidget()
        header_bar.setStyleSheet(
            f"background: {T['bg2']}; border-bottom: 1px solid {T['border']};"
        )
        header_bar.setFixedHeight(36)
        hh = QHBoxLayout(header_bar)
        hh.setContentsMargins(14, 0, 14, 0)
        lbl = QLabel("Aufgaben")
        lbl.setStyleSheet(
            f"color: {T['text']}; font-weight: bold; font-size: 13px;"
            " background: transparent; border: none;"
        )
        hh.addWidget(lbl)
        outer.addWidget(header_bar)

        # ── Erledigt-Bereich (ausserhalb der ScrollArea, einklappbar) ──
        self._done_clip = QScrollArea()
        self._done_clip.setMinimumHeight(0)
        self._done_clip.setMaximumHeight(0)
        self._done_clip.setWidgetResizable(True)
        self._done_clip.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._done_clip.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._done_clip.setStyleSheet(f"background: {T['bg2']}; border: none;")
        # Alias für Kompatibilität
        self._done_wrapper = self._done_clip

        self._done_content = QWidget()
        self._done_content.setStyleSheet("background: transparent;")
        dc = QVBoxLayout(self._done_content)
        dc.setContentsMargins(10, 8, 10, 0)
        dc.setSpacing(2)
        done_hdr = QLabel("ERLEDIGT")
        done_hdr.setStyleSheet(
            f"color: {T['muted']}; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;"
            " background: transparent; border: none; padding: 0 0 4px 4px;"
        )
        dc.addWidget(done_hdr)
        self._done_container = QVBoxLayout()
        self._done_container.setSpacing(1)
        dc.addLayout(self._done_container)
        dc.addSpacing(6)
        done_sep = QFrame()
        done_sep.setFrameShape(QFrame.Shape.HLine)
        done_sep.setFixedHeight(1)
        done_sep.setStyleSheet(f"background: {T['border']}; border: none;")
        dc.addWidget(done_sep)

        self._done_clip.setWidget(self._done_content)
        outer.addWidget(self._done_clip)

        # ── ScrollArea: nur AKTUELL + ZUKUNFT ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("border: none; background: transparent;")
        self._scroll.viewport().installEventFilter(self)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(10, 12, 10, 12)
        cl.setSpacing(2)

        # AKTUELL
        lbl1 = QLabel("AKTUELL")
        lbl1.setStyleSheet(
            f"color: {T['muted']}; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;"
            " background: transparent; border: none; padding: 0 0 4px 4px;"
        )
        cl.addWidget(lbl1)
        self._soon_container = QVBoxLayout()
        self._soon_container.setSpacing(1)
        cl.addLayout(self._soon_container)
        self._soon_input = QLineEdit()
        self._soon_input.setPlaceholderText("+ Hinzufügen")
        self._soon_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; border: none;
                border-bottom: 1px solid {T['border']}; border-radius: 0;
                padding: 4px 4px; color: {T['muted']}; font-size: 12px;
            }}
            QLineEdit:focus {{
                border-bottom: 1px solid {T['accent']}; color: {T['text']};
            }}
        """)
        self._soon_input.returnPressed.connect(lambda: self._add_task("soon"))
        cl.addWidget(self._soon_input)
        cl.addSpacing(18)

        # Trennlinie
        mid_sep = QFrame()
        mid_sep.setFrameShape(QFrame.Shape.HLine)
        mid_sep.setFixedHeight(1)
        mid_sep.setStyleSheet(f"background: {T['border']}; border: none;")
        cl.addWidget(mid_sep)
        cl.addSpacing(14)

        # ZUKUNFT
        lbl2 = QLabel("ZUKUNFT")
        lbl2.setStyleSheet(
            f"color: {T['muted']}; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;"
            " background: transparent; border: none; padding: 0 0 4px 4px;"
        )
        cl.addWidget(lbl2)
        self._future_container = QVBoxLayout()
        self._future_container.setSpacing(1)
        cl.addLayout(self._future_container)
        self._future_input = QLineEdit()
        self._future_input.setPlaceholderText("+ Hinzufügen")
        self._future_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; border: none;
                border-bottom: 1px solid {T['border']}; border-radius: 0;
                padding: 4px 4px; color: {T['muted']}; font-size: 12px;
            }}
            QLineEdit:focus {{
                border-bottom: 1px solid {T['accent']}; color: {T['text']};
            }}
        """)
        self._future_input.returnPressed.connect(lambda: self._add_task("future"))
        cl.addWidget(self._future_input)
        cl.addStretch()

        self._scroll.setWidget(content)
        outer.addWidget(self._scroll)

    # ── Overscroll: Mausrad fängt done-Bereich auf/zu ──
    def eventFilter(self, obj, event):
        try:
            if obj is self._scroll.viewport() and event.type() == QEvent.Type.Wheel:
                handled = self._handle_wheel(event)
                if handled:
                    event.accept()
                    return True
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def _done_natural_h(self):
        return self._done_content.sizeHint().height()

    def _scroll_done_to_bottom(self):
        """Scrollt den Erledigt-Bereich ans Ende (neueste Tasks sichtbar)."""
        sb = self._done_clip.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _handle_wheel(self, event):
        delta = event.angleDelta().y()
        sb = self._scroll.verticalScrollBar()
        nat = self._done_natural_h()
        cur_h = self._done_clip.maximumHeight()

        if nat <= 0:
            return False  # keine erledigten Tasks

        # Am oberen Rand hochscrollen → done-Bereich aufklappen
        if delta > 0 and sb.value() <= sb.minimum() and cur_h < nat:
            step = delta / 3
            new_h = min(cur_h + step, nat)
            self._done_clip.setMaximumHeight(int(new_h))
            self._scroll_done_to_bottom()
            return True

        # Done-Bereich sichtbar + runterscrollen → done-Bereich zuklappen
        if delta < 0 and cur_h > 0:
            step = -delta / 3
            new_h = max(cur_h - step, 0)
            self._done_clip.setMaximumHeight(int(new_h))
            self._scroll_done_to_bottom()
            return True

        return False

    def scroll_to_current(self):
        """Klappt den done-Bereich zu (beim Öffnen des Panels)."""
        self._done_clip.setMaximumHeight(0)

    # ── DATEN ──
    def load_tasks(self, tasks, save_fn, deleted_task_ids=None):
        self._tasks = tasks
        self._save_fn = save_fn
        self._deleted_task_ids = deleted_task_ids
        self._rebuild_lists(reset_view=True)

    def _rebuild_lists(self, reset_view=False):
        # Scroll-Position + Done-Höhe merken
        scroll_val = self._scroll.verticalScrollBar().value()
        done_h = self._done_clip.maximumHeight()

        for container in (self._done_container, self._soon_container, self._future_container):
            while container.count():
                item = container.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        done_tasks = sorted(
            [t for t in self._tasks if t.get("done", False)],
            key=lambda t: t.get("done_at", t.get("created", ""))
        )
        undone_tasks = [t for t in self._tasks if not t.get("done", False)]

        for t in done_tasks:
            w = TaskItem(t["id"], t["text"], done=True, panel=self)
            w.toggled.connect(self._on_task_toggled)
            w.deleted.connect(self._on_task_deleted)
            self._done_container.addWidget(w)

        for t in undone_tasks:
            w = TaskItem(t["id"], t["text"], done=False, panel=self)
            w.toggled.connect(self._on_task_toggled)
            w.deleted.connect(self._on_task_deleted)
            if t.get("section", "soon") == "future":
                self._future_container.addWidget(w)
            else:
                self._soon_container.addWidget(w)

        self._selection.clear()

        if reset_view:
            self._done_clip.setMaximumHeight(0)
        else:
            # Position wiederherstellen
            nat = self._done_natural_h()
            self._done_clip.setMaximumHeight(min(done_h, nat) if nat > 0 else 0)
            self._scroll_done_to_bottom()
            QTimer.singleShot(0, lambda: self._scroll.verticalScrollBar().setValue(scroll_val))

    def _add_task(self, section):
        inp = self._soon_input if section == "soon" else self._future_input
        text = inp.text().strip()
        if not text:
            return
        task = {
            "id": datetime.now().isoformat() + "_" + str(len(self._tasks)),
            "text": text,
            "done": False,
            "section": section,
            "created": datetime.now().isoformat(),
        }
        self._tasks.append(task)
        inp.clear()
        self._rebuild_lists()
        if self._save_fn:
            self._save_fn()

    def _on_task_toggled(self, task_id, done):
        for t in self._tasks:
            if t["id"] == task_id:
                t["done"] = done
                if done:
                    t["done_at"] = datetime.now().isoformat()
                else:
                    t.pop("done_at", None)
                break

        if done:
            # Fade-Up-Animation: Widget finden und animieren
            widget = self._find_task_widget(task_id)
            if widget:
                self._animate_done(widget, task_id)
                return
        self._rebuild_lists()
        if self._save_fn:
            self._save_fn()

    def _find_task_widget(self, task_id):
        for container in (self._soon_container, self._future_container):
            for i in range(container.count()):
                w = container.itemAt(i).widget()
                if w and getattr(w, 'task_id', None) == task_id:
                    return w
        return None

    def _animate_done(self, widget, task_id):
        eff = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(eff)

        fade = QPropertyAnimation(eff, b"opacity")
        fade.setDuration(350)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.Type.InQuad)

        move = QPropertyAnimation(widget, b"pos")
        move.setDuration(350)
        start = widget.pos()
        move.setStartValue(start)
        move.setEndValue(QPoint(start.x(), start.y() - 20))
        move.setEasingCurve(QEasingCurve.Type.InQuad)

        grp = QParallelAnimationGroup(widget)
        grp.addAnimation(fade)
        grp.addAnimation(move)
        grp.finished.connect(lambda: self._finish_toggle(task_id))
        grp.start()
        self._done_anim = grp  # prevent GC

    def _finish_toggle(self, task_id):
        self._done_anim = None
        self._rebuild_lists()
        if self._save_fn:
            self._save_fn()

    # ── Selection ──
    def _all_task_widgets(self):
        """Alle TaskItem-Widgets in Reihenfolge: done, soon, future."""
        widgets = []
        for container in (self._done_container, self._soon_container, self._future_container):
            for i in range(container.count()):
                w = container.itemAt(i).widget()
                if w:
                    widgets.append(w)
        return widgets

    def _clear_selection(self):
        self._selection.clear()
        for w in self._all_task_widgets():
            w.set_selected(False)

    def _apply_selection(self):
        for w in self._all_task_widgets():
            w.set_selected(w.task_id in self._selection)

    def _on_item_clicked(self, task_id, modifiers):
        ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        if ctrl:
            # Toggle einzelne Auswahl
            if task_id in self._selection:
                self._selection.remove(task_id)
            else:
                self._selection.append(task_id)
            self._last_clicked = task_id
        elif shift and self._last_clicked:
            # Range-Auswahl
            widgets = self._all_task_widgets()
            ids = [w.task_id for w in widgets]
            try:
                i1 = ids.index(self._last_clicked)
                i2 = ids.index(task_id)
            except ValueError:
                return
            lo, hi = min(i1, i2), max(i1, i2)
            self._selection = list(dict.fromkeys(
                self._selection + ids[lo:hi + 1]
            ))
        else:
            # Normaler Klick — Auswahl zurücksetzen auf diesen einen
            self._selection = [task_id]
            self._last_clicked = task_id

        self._apply_selection()

    def _on_item_context(self, task_id, global_pos):
        # Rechtsklick auf nicht-ausgewähltes Item → nur dieses auswählen
        if task_id not in self._selection:
            self._selection = [task_id]
            self._last_clicked = task_id
            self._apply_selection()

        sel = list(self._selection)
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {T['bg2']}; border: 1px solid {T['border']};
                     border-radius: 6px; padding: 4px; color: {T['text']}; font-size: 12px; }}
            QMenu::item {{ padding: 5px 14px; border-radius: 4px; }}
            QMenu::item:selected {{ background: rgba(255,255,255,0.08); }}
        """)
        n = len(sel)
        act_del = QAction(f"Löschen ({n})" if n > 1 else "Löschen", self)
        act_del.triggered.connect(lambda: self._delete_tasks(sel))
        menu.addAction(act_del)

        # Alle abhaken / Alle zurücksetzen
        undone = [tid for tid in sel if not any(t.get("done") for t in self._tasks if t["id"] == tid)]
        done = [tid for tid in sel if any(t.get("done") for t in self._tasks if t["id"] == tid)]
        if undone:
            act_check = QAction(f"Abhaken ({len(undone)})" if len(undone) > 1 else "Abhaken", self)
            act_check.triggered.connect(lambda: self._batch_toggle(undone, True))
            menu.addAction(act_check)
        if done:
            act_uncheck = QAction(f"Zurücksetzen ({len(done)})" if len(done) > 1 else "Zurücksetzen", self)
            act_uncheck.triggered.connect(lambda: self._batch_toggle(done, False))
            menu.addAction(act_uncheck)

        menu.exec(global_pos)

    def _delete_tasks(self, task_ids):
        self._tasks[:] = [t for t in self._tasks if t["id"] not in task_ids]
        self._selection.clear()
        self._rebuild_lists()
        if self._save_fn:
            self._save_fn()

    def _batch_toggle(self, task_ids, done):
        for t in self._tasks:
            if t["id"] in task_ids:
                t["done"] = done
                if done:
                    t["done_at"] = datetime.now().isoformat()
                else:
                    t.pop("done_at", None)
        self._selection.clear()
        self._rebuild_lists()
        if self._save_fn:
            self._save_fn()

    def _on_task_deleted(self, task_id):
        self._tasks[:] = [t for t in self._tasks if t["id"] != task_id]
        if self._deleted_task_ids is not None and task_id not in self._deleted_task_ids:
            self._deleted_task_ids.append(task_id)
        self._rebuild_lists()
        if self._save_fn:
            self._save_fn()


# ─────────────────────────────────────────────
#  SIDEBAR PANEL (collapsible)
# ─────────────────────────────────────────────
class SidebarPanel(QWidget):
    note_selected = pyqtSignal(str)
    settings_requested = pyqtSignal()
    sort_changed = pyqtSignal(str)
    new_note_clicked = pyqtSignal()
    new_folder_clicked = pyqtSignal()

    SORT_OPTIONS = [
        ("Dateiname (A - Z)",              "name_asc"),
        ("Dateiname (Z - A)",              "name_desc"),
        ("Letzte Bearbeitung (neu - alt)", "modified_desc"),
        ("Letzte Bearbeitung (alt - neu)", "modified_asc"),
        ("Erstellungszeitpunkt (neu - alt)", "id_desc"),
        ("Erstellungszeitpunkt (alt - neu)", "id_asc"),
    ]

    def __init__(self):
        super().__init__()
        self._expanded = True
        self._sort_mode = "id_asc"
        self.setMinimumWidth(0)
        self.setMaximumWidth(240)
        self.setStyleSheet(f"background-color: {T['bg2']}; border-right: 1px solid {T['border']};")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header: Dateien / Suche Tabs ──
        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet(f"background: {T['bg2']}; border-bottom: 1px solid {T['border']};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(4, 3, 4, 3)
        hl.setSpacing(2)

        self.btn_files_tab = QPushButton()
        self.btn_files_tab.setFixedHeight(30)
        self.btn_files_tab.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_files_tab.setCheckable(True)
        self.btn_files_tab.setChecked(True)
        self.btn_files_tab.setToolTip("Dateimanager")
        self.btn_files_tab.setIcon(_svg_icon(_FOLDER_SVG, T['text'], 18))
        self.btn_files_tab.setIconSize(QSize(18, 18))
        self.btn_files_tab.clicked.connect(lambda: self.switch_tab("files"))

        self.btn_search_tab = QPushButton()
        self.btn_search_tab.setFixedHeight(30)
        self.btn_search_tab.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_search_tab.setCheckable(True)
        self.btn_search_tab.setToolTip("Suche")
        self.btn_search_tab.setIcon(_svg_icon(_SEARCH_SVG, T['muted'], 18))
        self.btn_search_tab.setIconSize(QSize(18, 18))
        self.btn_search_tab.clicked.connect(lambda: self.switch_tab("search"))

        self._apply_tab_btn_style(self.btn_files_tab, True)
        self._apply_tab_btn_style(self.btn_search_tab, False)

        hl.addWidget(self.btn_files_tab, 1)
        hl.addWidget(self.btn_search_tab, 1)
        layout.addWidget(header)

        # ── Sort toolbar (files tab only) ──
        self.sort_bar = QWidget()
        self.sort_bar.setFixedHeight(30)
        self.sort_bar.setStyleSheet(f"background: {T['bg2']}; border-bottom: 1px solid {T['border']};")
        sbl = QHBoxLayout(self.sort_bar)
        sbl.setContentsMargins(8, 0, 8, 0)
        sbl.setSpacing(2)

        _tb_style = f"""
            QPushButton {{ background: transparent; border: none; border-radius: 4px; padding: 2px; }}
            QPushButton:hover {{ background: rgba(255,255,255,0.07); }}
        """

        self.btn_new_note_sb = QPushButton()
        self.btn_new_note_sb.setFixedSize(24, 24)
        self.btn_new_note_sb.setToolTip("Neue Notiz")
        self.btn_new_note_sb.setIcon(_svg_icon(_EDIT_SVG, T['muted'], 14))
        self.btn_new_note_sb.setIconSize(QSize(14, 14))
        self.btn_new_note_sb.setStyleSheet(_tb_style)
        self.btn_new_note_sb.clicked.connect(self.new_note_clicked)
        sbl.addWidget(self.btn_new_note_sb)

        self.btn_new_folder = QPushButton()
        self.btn_new_folder.setFixedSize(24, 24)
        self.btn_new_folder.setToolTip("Neuer Ordner")
        self.btn_new_folder.setIcon(_svg_icon(_FOLDER_PLUS_SVG, T['muted'], 14))
        self.btn_new_folder.setIconSize(QSize(14, 14))
        self.btn_new_folder.setStyleSheet(_tb_style)
        self.btn_new_folder.clicked.connect(self.new_folder_clicked)
        sbl.addWidget(self.btn_new_folder)

        sbl.addStretch()

        self.sort_btn = QPushButton()
        self.sort_btn.setFixedSize(24, 24)
        self.sort_btn.setToolTip("Sortierreihenfolge \u00e4ndern")
        self.sort_btn.setIcon(_svg_icon(_SLIDERS_SVG, T['muted'], 14))
        self.sort_btn.setIconSize(QSize(14, 14))
        self.sort_btn.setStyleSheet(_tb_style)
        self.sort_btn.clicked.connect(self._show_sort_menu)
        sbl.addWidget(self.sort_btn)
        layout.addWidget(self.sort_bar)

        # ── Search bar (search tab only, hidden initially) ──
        self.search_bar = QWidget()
        self.search_bar.setStyleSheet("background: transparent;")
        sb_layout = QVBoxLayout(self.search_bar)
        sb_layout.setContentsMargins(8, 8, 8, 4)
        sb_layout.setSpacing(4)
        self.search_bar.setVisible(False)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suchbegriff eingeben...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {T['bg3']}; border: 1px solid {T['border']};
                border-radius: 4px; padding: 5px 10px;
                color: {T['text']}; font-size: {_sz(13)}px;
            }}
            QLineEdit:focus {{ border-color: {T['accent']}; }}
        """)
        sb_layout.addWidget(self.search_input)

        # Result count label
        self.result_count_lbl = QLabel("")
        self.result_count_lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(11)}px; padding: 2px 0;")
        self.result_count_lbl.setVisible(False)
        sb_layout.addWidget(self.result_count_lbl)

        # AI search toggle
        self.ai_search_row = QWidget()
        self.ai_search_row.setStyleSheet("background: transparent;")
        ai_row_layout = QHBoxLayout(self.ai_search_row)
        ai_row_layout.setContentsMargins(0, 0, 0, 0)
        ai_row_layout.setSpacing(4)
        self.ai_search_toggle = QPushButton("\u2728 KI-Suche")
        self.ai_search_toggle.setCheckable(True)
        self.ai_search_toggle.setFixedHeight(26)
        self.ai_search_toggle.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: 1px solid {T['border']}; border-radius: 4px;
                          color: {T['muted']}; font-size: {_sz(10)}px; padding: 2px 8px; }}
            QPushButton:checked {{ background: #0d1f15; border-color: {T['accent']}; color: {T['accent']}; }}
        """)
        ai_row_layout.addWidget(self.ai_search_toggle)
        ai_row_layout.addStretch()
        sb_layout.addWidget(self.ai_search_row)

        self.ai_search_status = QLabel("")
        self.ai_search_status.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(9)}px;")
        self.ai_search_status.setVisible(False)
        sb_layout.addWidget(self.ai_search_status)

        layout.addWidget(self.search_bar)

        # ── Notes list ──
        self.notes_list = QListWidget()
        self.notes_list.setSpacing(0)
        self.notes_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.notes_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.notes_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent; border: none; outline: none;
            }}
            QListWidget::item {{
                background: transparent; padding: 0; margin: 0;
            }}
            QListWidget::item:hover {{
                background: rgba(255,255,255,0.05);
            }}
            QListWidget::item:selected {{
                background: rgba(74,144,217,0.18);
            }}
            QListWidget::item:selected:hover {{
                background: rgba(74,144,217,0.26);
            }}
        """)
        layout.addWidget(self.notes_list, 1)

    def _apply_tab_btn_style(self, btn, active):
        svg = _FOLDER_SVG if btn is self.btn_files_tab else _SEARCH_SVG
        icon_color = T['text'] if active else T['muted']
        btn.setIcon(_svg_icon(svg, icon_color, 18))
        btn.setIconSize(QSize(18, 18))
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {T['bg3']}; border: none; border-radius: 6px;
                    padding: 0;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none; border-radius: 6px;
                    padding: 0;
                }}
                QPushButton:hover {{ background: rgba(255,255,255,0.06); }}
            """)

    def switch_tab(self, tab):
        is_files = (tab == "files")
        self.btn_files_tab.setChecked(is_files)
        self.btn_search_tab.setChecked(not is_files)
        self._apply_tab_btn_style(self.btn_files_tab, is_files)
        self._apply_tab_btn_style(self.btn_search_tab, not is_files)
        self.sort_bar.setVisible(is_files)
        self.search_bar.setVisible(not is_files)
        if not is_files:
            self.search_input.setFocus()

    def _show_sort_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {T['bg2']}; border: 1px solid {T['border']};
                    border-radius: 6px; padding: 4px; color: {T['text']}; font-size: {_sz(13)}px; }}
            QMenu::item {{ padding: 6px 16px; border-radius: 4px; }}
            QMenu::item:selected {{ background: rgba(255,255,255,0.08); }}
        """)
        for label, mode in self.SORT_OPTIONS:
            prefix = "\u2713 " if mode == self._sort_mode else "  "
            action = QAction(prefix + label, self)
            action.triggered.connect(lambda _, m=mode: self._set_sort(m))
            menu.addAction(action)
        menu.exec(self.sort_btn.mapToGlobal(self.sort_btn.rect().bottomLeft()))

    def _set_sort(self, mode):
        self._sort_mode = mode
        self.sort_changed.emit(mode)

    def toggle(self):
        if self._expanded:
            self._animate(0)
        else:
            self._animate(240)
        self._expanded = not self._expanded

    def _animate(self, target):
        anim = QPropertyAnimation(self, b"maximumWidth")
        anim.setDuration(200)
        anim.setStartValue(self.maximumWidth())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim = anim
        anim.start()


# ─────────────────────────────────────────────
#  TAB BUTTON
# ─────────────────────────────────────────────
class TabButton(QWidget):
    clicked = pyqtSignal(str)
    close_clicked = pyqtSignal(str)

    def __init__(self, note_id, title, is_active=False):
        super().__init__()
        self.note_id = note_id
        self._build(title, is_active)

    def _build(self, title, is_active):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(0)

        display_title = (title or "Unbenannt")[:22]
        self.label = QLabel(display_title)
        self.label.setCursor(Qt.CursorShape.PointingHandCursor)
        color = T['text'] if is_active else T['muted']
        weight = "600" if is_active else "400"
        self.label.setStyleSheet(
            f"color: {color}; font-size: {_sz(13)}px; font-weight: {weight};"
            f" background: transparent; border: none;"
        )
        layout.addWidget(self.label)

        if is_active:
            self.setStyleSheet(f"""
                TabButton {{
                    background: {T['bg']};
                    border-top: 1px solid {T['border']};
                    border-left: 1px solid {T['border']};
                    border-right: 1px solid {T['border']};
                    border-bottom: 1px solid {T['bg']};
                    border-radius: 6px 6px 0 0;
                    margin-bottom: -1px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                TabButton {{
                    background: transparent; border: none;
                    border-bottom: 1px solid {T['border']};
                }}
                TabButton:hover {{ background: rgba(255,255,255,0.04); }}
            """)
        self.setMinimumWidth(80)
        self.setMaximumWidth(180)
        self.setFixedHeight(34)

    def set_active(self, is_active):
        color = T['text'] if is_active else T['muted']
        weight = "600" if is_active else "400"
        self.label.setStyleSheet(
            f"color: {color}; font-size: {_sz(13)}px; font-weight: {weight};"
            f" background: transparent; border: none;"
        )
        if is_active:
            self.setStyleSheet(f"""
                TabButton {{
                    background: {T['bg']};
                    border-top: 1px solid {T['border']};
                    border-left: 1px solid {T['border']};
                    border-right: 1px solid {T['border']};
                    border-bottom: 1px solid {T['bg']};
                    border-radius: 6px 6px 0 0;
                    margin-bottom: -1px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                TabButton {{
                    background: transparent; border: none;
                    border-bottom: 1px solid {T['border']};
                }}
                TabButton:hover {{ background: rgba(255,255,255,0.04); }}
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.note_id)
        super().mousePressEvent(event)


# ─────────────────────────────────────────────
#  TAB BAR
# ─────────────────────────────────────────────
class TabBar(QWidget):
    tab_selected = pyqtSignal(str)
    tab_closed = pyqtSignal(str)
    new_tab = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(36)
        self.setStyleSheet(f"background: {T['bg2']}; border-bottom: 1px solid {T['border']};")
        self._drag_pos = None
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.left_arrow = QPushButton("<")
        self.left_arrow.setFixedSize(20, 34)
        self.left_arrow.setStyleSheet(f"""
            QPushButton {{
                background: {T['bg2']}; border: none; border-right: 1px solid {T['border']};
                color: {T['muted']}; font-size: {_sz(13)}px; font-weight: 500;
                padding: 0;
            }}
            QPushButton:hover {{ background: {T['bg3']}; color: {T['text']}; }}
        """)
        self.left_arrow.clicked.connect(self._scroll_left)
        self.left_arrow.setVisible(False)
        layout.addWidget(self.left_arrow)

        self._prev_tab_ids = set()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFixedHeight(36)
        self.scroll_area.setStyleSheet(f"QScrollArea {{ background: transparent; border: none; }}")
        self.scroll_area.horizontalScrollBar().setSingleStep(20)

        self.tab_container = QWidget()
        self.tab_container.setStyleSheet("background: transparent;")
        self.tab_layout = QHBoxLayout(self.tab_container)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_layout.setSpacing(0)
        self.scroll_area.setWidget(self.tab_container)
        self.scroll_area.viewport().installEventFilter(self)
        layout.addWidget(self.scroll_area)

        self.right_arrow = QPushButton(">")
        self.right_arrow.setFixedSize(20, 34)
        self.right_arrow.setStyleSheet(f"""
            QPushButton {{
                background: {T['bg2']}; border: none; border-left: 1px solid {T['border']};
                color: {T['muted']}; font-size: {_sz(13)}px; font-weight: 500;
                padding: 0;
            }}
            QPushButton:hover {{ background: {T['bg3']}; color: {T['text']}; }}
        """)
        self.right_arrow.clicked.connect(self._scroll_right)
        self.right_arrow.setVisible(False)
        layout.addWidget(self.right_arrow)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(36, 34)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; border-left: 1px solid {T['border']};
                color: {T['muted']}; font-size: {_sz(18)}px; font-weight: 300;
                padding: 0;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.06); color: {T['text']}; }}
        """)
        add_btn.clicked.connect(self.new_tab.emit)
        layout.addWidget(add_btn)

        # ── Window controls (frameless, compact) ──
        # Small separator before the group
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(16)
        sep.setStyleSheet(f"background: {T['border']}; margin: 0 4px;")
        layout.addWidget(sep)

        _wc_base = f"""
            QPushButton {{
                background: transparent; border: none;
                color: {T['muted']}; font-size: {_sz(16)}px; font-family: '{_UI_FONT[0]}', sans-serif;
                min-width: 38px; max-width: 38px; height: 36px;
                border-radius: 0; padding: 0;
            }}
        """
        min_btn = QPushButton("\u2212")
        min_btn.setStyleSheet(_wc_base + f"QPushButton:hover {{ background: rgba(255,255,255,0.10); color: {T['text']}; }}")
        min_btn.setToolTip("Minimieren")
        min_btn.clicked.connect(lambda: self.window().showMinimized())
        layout.addWidget(min_btn)

        self._max_btn = QPushButton("\u25a1")
        self._max_btn.setStyleSheet(_wc_base + f"QPushButton:hover {{ background: rgba(255,255,255,0.10); color: {T['text']}; }}")
        self._max_btn.setToolTip("Maximieren / Wiederherstellen")
        self._max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self._max_btn)

        close_btn = QPushButton("\u00d7")
        close_btn.setStyleSheet(_wc_base + "QPushButton:hover { background: #c42b1c; color: #fff; }")
        close_btn.setToolTip("Schlie\u00dfen")
        close_btn.clicked.connect(lambda: self.window().close())
        layout.addWidget(close_btn)

    def _toggle_maximize(self):
        win = self.window()
        if getattr(win, '_is_maximized', False):
            win._is_maximized = False
            geo = getattr(win, '_normal_geo', None)
            win.showNormal()
            if geo:
                QTimer.singleShot(50, lambda: win.setGeometry(geo))
            self._max_btn.setText("□")
        else:
            win._normal_geo = win.geometry()
            win._is_maximized = True
            win.showMaximized()
            self._max_btn.setText("⧉")

    # ── Window drag (frameless) ──
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if not getattr(win, '_is_maximized', False):
                self._drag_pos = event.globalPosition().toPoint() - win.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
        super().mouseDoubleClickEvent(event)

    def _is_empty_tab_area(self, viewport, pos):
        """True if pos is over empty space in the tab scroll area (not over a tab widget)."""
        vp_child = viewport.childAt(pos)
        if vp_child is None:
            return True
        if vp_child is self.tab_container:
            tc_local = self.tab_container.mapFrom(viewport, pos)
            return self.tab_container.childAt(tc_local) is None
        return False

    def eventFilter(self, obj, event):
        """Allow dragging / double-click-maximize from empty areas in the tab bar."""
        if obj is self.scroll_area.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    if self._is_empty_tab_area(obj, event.pos()):
                        win = self.window()
                        if not win.isMaximized():
                            self._drag_pos = (event.globalPosition().toPoint()
                                              - win.frameGeometry().topLeft())
            elif event.type() == QEvent.Type.MouseMove:
                if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
                    self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._drag_pos = None
            elif event.type() == QEvent.Type.MouseButtonDblClick:
                if (event.button() == Qt.MouseButton.LeftButton and
                        self._is_empty_tab_area(obj, event.pos())):
                    self._toggle_maximize()
        return False  # never consume

    def update_tabs(self, open_tabs, active_id, notes_data):
        new_ids = set(open_tabs)

        # Fast path: gleiche Tabs → nur Active-State umschalten (O(n) Styles statt O(n) Widgets)
        if new_ids == self._prev_tab_ids:
            for i in range(self.tab_layout.count()):
                w = self.tab_layout.itemAt(i).widget()
                if w and hasattr(w, 'set_active'):
                    w.set_active(w.note_id == active_id)
            if active_id:
                QTimer.singleShot(60, lambda: self.ensure_tab_visible(active_id))
            return

        added_ids = new_ids - self._prev_tab_ids
        self._prev_tab_ids = new_ids

        # Full rebuild (Notiz hinzugefügt/gelöscht)
        while self.tab_layout.count():
            child = self.tab_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for nid in open_tabs:
            note = next((n for n in notes_data.get("notes", []) if n["id"] == nid), None)
            title = (note.get("title", "") if note else "") or "Unbenannt"
            tab = TabButton(nid, title, is_active=(nid == active_id))
            tab.clicked.connect(self.tab_selected.emit)
            tab.close_clicked.connect(self.tab_closed.emit)
            self.tab_layout.addWidget(tab)
            if nid in added_ids:
                anim = QPropertyAnimation(tab, b"maximumHeight")
                anim.setStartValue(0)
                anim.setEndValue(34)
                anim.setDuration(160)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                tab._slide_anim = anim
                anim.start()

        self._check_overflow()
        if active_id:
            QTimer.singleShot(60, lambda: self.ensure_tab_visible(active_id))

    def _check_overflow(self):
        QTimer.singleShot(50, self._update_arrows)

    def _update_arrows(self):
        sw = self.scroll_area.viewport().width()
        cw = self.tab_container.sizeHint().width()
        overflow = cw > sw
        self.left_arrow.setVisible(overflow)
        self.right_arrow.setVisible(overflow)

    def _smooth_scroll(self, delta):
        sb = self.scroll_area.horizontalScrollBar()
        target = max(sb.minimum(), min(sb.maximum(), sb.value() + delta))
        anim = QPropertyAnimation(sb, b"value", self)
        anim.setDuration(160)
        anim.setStartValue(sb.value())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _scroll_left(self):
        self._smooth_scroll(-140)

    def _scroll_right(self):
        self._smooth_scroll(140)

    def wheelEvent(self, event):
        import time
        delta = event.angleDelta().y()
        if delta == 0:
            event.accept()
            return
        now = time.monotonic()
        dt = now - getattr(self, '_last_wheel_time', 0)
        self._last_wheel_time = now
        # Velocity: kurzer Abstand zwischen Events = schnelles Scrollen → mehr Distanz
        if dt < 0.05:       # sehr schnell
            factor = 4.0
        elif dt < 0.12:     # schnell
            factor = 2.5
        elif dt < 0.25:     # normal
            factor = 1.5
        else:               # langsam
            factor = 1.0
        scroll = int(-(delta / abs(delta)) * abs(delta) / 120 * 120 * factor)
        self._smooth_scroll(scroll)
        event.accept()

    def ensure_tab_visible(self, note_id):
        """Scroll the tab bar so the tab for note_id is fully visible."""
        for i in range(self.tab_layout.count()):
            item = self.tab_layout.itemAt(i)
            if item and isinstance(item.widget(), TabButton):
                tab = item.widget()
                if tab.note_id == note_id:
                    self.scroll_area.ensureWidgetVisible(tab, 20, 0)
                    break


# ─────────────────────────────────────────────
#  SETTINGS OVERLAY
# ─────────────────────────────────────────────
class SettingsOverlay(QWidget):
    closed = pyqtSignal()
    theme_changed = pyqtSignal(str)
    _users_ready = pyqtSignal(object, object)  # (users_list, error_str)

    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.setVisible(False)
        self._build()

    def set_backdrop(self, pixmap):
        self._backdrop = pixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if hasattr(self, '_backdrop') and not self._backdrop.isNull():
            painter.drawPixmap(self.rect(), self._backdrop)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 30))

    def mousePressEvent(self, event):
        if not self.modal.geometry().contains(event.pos()):
            self._close()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'modal'):
            pad_h, pad_v = 80, 60
            w = max(520, self.width()  - pad_h * 2)
            h = max(400, self.height() - pad_v * 2)
            w = min(w, 880)
            h = min(h, 580)
            self.modal.setFixedSize(w, h)
            _path = QPainterPath()
            _path.addRoundedRect(QRectF(0, 0, w, h), 12.0, 12.0)
            self.modal.setMask(QRegion(_path.toFillPolygon().toPolygon()))

    def _build(self):
        self._backdrop = QPixmap()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        center_h = QHBoxLayout()
        center_h.setContentsMargins(0, 0, 0, 0)
        center_h.addStretch(1)

        self.modal = QWidget()
        self.modal.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.modal.setStyleSheet(f"""
            QWidget#modal {{
                background: {T['bg']};
                border: 1px solid {T['border']};
                border-radius: 12px;
            }}
        """)
        self.modal.setObjectName("modal")
        self.modal.setMinimumSize(520, 400)
        shadow = QGraphicsDropShadowEffect(self.modal)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.modal.setGraphicsEffect(shadow)

        modal_layout = QHBoxLayout(self.modal)
        modal_layout.setContentsMargins(0, 0, 0, 0)
        modal_layout.setSpacing(0)

        # ── Left nav ──
        nav = QWidget()
        nav.setFixedWidth(210)
        nav.setStyleSheet(f"""
            QWidget {{
                background: {T['bg2']};
                border-right: 1px solid {T['border']};
                border-radius: 12px 0 0 12px;
            }}
        """)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(12, 20, 12, 20)
        nav_layout.setSpacing(2)

        section_lbl = QLabel("OPTIONEN")
        section_lbl.setStyleSheet(
            f"color: {T['muted']}; font-size: {_sz(10)}px; font-weight: 700; "
            f"letter-spacing: 1px; padding: 0 4px 6px 4px; background: transparent; border: none;"
        )
        nav_layout.addWidget(section_lbl)

        self.cat_list = QListWidget()
        self.cat_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent; border: none; outline: none;
            }}
            QListWidget::item {{
                padding: 7px 10px; color: {T['muted']}; font-size: {_sz(13)}px;
                border-radius: 6px; margin: 1px 0;
            }}
            QListWidget::item:hover {{
                color: {T['text']}; background: rgba(255,255,255,0.06);
            }}
            QListWidget::item:selected {{
                background: rgba(255,255,255,0.1); color: {T['text']}; font-weight: 500;
            }}
        """)

        for cat, icon_svg in [
            ("Allgemein",       _SLIDERS_SVG),
            ("Darstellung",     _EYE_SVG),
            ("KI",              _ZAP_SVG),
            ("Synchronisation", _CLOUD_SVG),
            ("Nutzer",          _PERSON_SVG),
            ("Backup",          _BACKUP_SVG),
        ]:
            item = QListWidgetItem("  " + cat)
            item.setIcon(_svg_icon(icon_svg, T['muted'], 14))
            self.cat_list.addItem(item)

        self.cat_list.currentRowChanged.connect(self._on_cat_change)
        nav_layout.addWidget(self.cat_list)
        nav_layout.addStretch()
        modal_layout.addWidget(nav)

        # ── Right: header + stacked pages ──
        right = QWidget()
        right.setStyleSheet(f"background: {T['bg']}; border-radius: 0 12px 12px 0;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Header row with close button
        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet(
            f"background: transparent; border-bottom: 1px solid {T['border']};"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(32, 0, 16, 0)
        self.header_title = QLabel("Allgemein")
        self.header_title.setStyleSheet(
            f"color: {T['text']}; font-size: {_sz(18)}px; font-weight: 600; background: transparent; border: none;"
        )
        hl.addWidget(self.header_title)
        hl.addStretch()

        close_btn = QPushButton("\u00D7")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; color: {T['muted']};
                          font-size: {_sz(18)}px; border-radius: 6px; }}
            QPushButton:hover {{ background: rgba(255,255,255,0.08); color: {T['text']}; }}
        """)
        close_btn.clicked.connect(self._close)
        hl.addWidget(close_btn)
        right_layout.addWidget(header)

        # Stacked pages
        self.pages = QStackedWidget()
        self.pages.setStyleSheet(f"background: transparent;")
        self._build_general_page()
        self._build_appearance_page()
        self._build_ai_page()
        self._build_sync_page()
        self._build_users_page()
        self._build_backup_page()
        right_layout.addWidget(self.pages)
        modal_layout.addWidget(right)

        center_h.addWidget(self.modal)
        center_h.addStretch(1)

        center_v = QVBoxLayout()
        center_v.addStretch(1)
        center_v.addLayout(center_h)
        center_v.addStretch(1)

        outer.addLayout(center_v)

    def _make_section_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(10)}px; letter-spacing: 1px; font-weight: 600; margin-top: 8px; margin-bottom: 4px;")
        return lbl

    def _make_setting_row(self, layout, name, description, control):
        """Obsidian setting-item: name+desc on left, control on right, border-top separator."""
        row = QWidget()
        row.setStyleSheet(f"background: transparent; border-top: 1px solid {T['border']};")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 14, 0, 14)
        rl.setSpacing(16)

        text_col = QWidget()
        text_col.setStyleSheet("background: transparent; border: none;")
        tcl = QVBoxLayout(text_col)
        tcl.setContentsMargins(0, 0, 0, 0)
        tcl.setSpacing(3)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"color: {T['text']}; font-size: {_sz(14)}px; font-weight: 500; border: none; background: transparent;")
        tcl.addWidget(name_lbl)
        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(12)}px; border: none; background: transparent;")
            desc_lbl.setWordWrap(True)
            tcl.addWidget(desc_lbl)
        rl.addWidget(text_col, 1)
        rl.addWidget(control, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(row)

    def _make_field(self, value="", placeholder="", echo=False, width=220):
        field = QLineEdit(value)
        field.setPlaceholderText(placeholder)
        field.setFixedWidth(width)
        if echo:
            field.setEchoMode(QLineEdit.EchoMode.Password)
        return field

    # ── General Page ──
    def _build_general_page(self):
        page = QWidget()
        page.setStyleSheet(f"background: {T['bg']};")
        scroll = QScrollArea()
        scroll.setWidget(page)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(0)

        version_lbl = QLabel("Notizen App v2.0")
        version_lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(12)}px;")
        layout.addWidget(version_lbl)
        layout.addSpacing(16)

        layout.addWidget(self._make_section_label("EDITOR"))

        self.title_toggle = ToggleSwitch(checked=self.config.get("show_title", True))
        self.title_toggle.toggled.connect(self._on_title_toggle)
        self._make_setting_row(layout, "Überschrift anzeigen",
                               "Titel und Datum über dem Text ein- oder ausblenden.",
                               self.title_toggle)

        _combo_style = (
            f"QFontComboBox, QComboBox {{ background: {T['bg3']}; color: {T['text']};"
            f" border: 1px solid {T['border']}; border-radius: 6px;"
            f" padding: 4px 8px; font-size: {_sz(13)}px; }}"
        )

        # ── UI-Schrift ──
        layout.addWidget(self._make_section_label("SCHRIFT"))

        ui_font_lbl = QLabel("Programmoberfläche")
        ui_font_lbl.setStyleSheet(f"color: {T['text']}; font-size: {_sz(13)}px; font-weight: 500; margin-top: 4px;")
        layout.addWidget(ui_font_lbl)
        layout.addSpacing(4)
        self.ui_font_combo = QFontComboBox()
        self.ui_font_combo.blockSignals(True)
        self.ui_font_combo.setCurrentFont(QFont(self.config.get("ui_font", "Segoe UI")))
        self.ui_font_combo.blockSignals(False)
        self.ui_font_combo.setStyleSheet(_combo_style)
        self.ui_font_combo.currentFontChanged.connect(self._on_ui_font_changed)
        _ui_reset = QPushButton("↺")
        _ui_reset.setFixedSize(32, 32)
        _ui_reset.setToolTip("Zurücksetzen auf Segoe UI")
        _ui_reset.setStyleSheet(f"QPushButton {{ background: {T['bg3']}; color: {T['muted']}; border: 1px solid {T['border']}; border-radius: 6px; font-size: {_sz(14)}px; }} QPushButton:hover {{ color: {T['text']}; }}")
        _ui_reset.clicked.connect(lambda: self._on_ui_font_changed(QFont("Segoe UI")) or self.ui_font_combo.setCurrentFont(QFont("Segoe UI")))
        _ui_row = QHBoxLayout()
        _ui_row.setSpacing(6)
        _ui_row.addWidget(self.ui_font_combo)
        _ui_row.addWidget(_ui_reset)
        layout.addLayout(_ui_row)
        layout.addSpacing(12)

        # ── Editor-Schrift ──
        ed_font_lbl = QLabel("Seiten-Inhalt (Schrift + Größe)")
        ed_font_lbl.setStyleSheet(f"color: {T['text']}; font-size: {_sz(13)}px; font-weight: 500;")
        layout.addWidget(ed_font_lbl)
        layout.addSpacing(4)
        self.editor_font_combo = QFontComboBox()
        self.editor_font_combo.blockSignals(True)
        self.editor_font_combo.setCurrentFont(QFont(self.config.get("editor_font", "Consolas")))
        self.editor_font_combo.blockSignals(False)
        self.editor_font_combo.setStyleSheet(_combo_style)
        self.editor_font_combo.currentFontChanged.connect(self._on_editor_font_changed)
        _ed_reset = QPushButton("↺")
        _ed_reset.setFixedSize(32, 32)
        _ed_reset.setToolTip("Zurücksetzen auf Consolas, Größe 14")
        _ed_reset.setStyleSheet(f"QPushButton {{ background: {T['bg3']}; color: {T['muted']}; border: 1px solid {T['border']}; border-radius: 6px; font-size: {_sz(14)}px; }} QPushButton:hover {{ color: {T['text']}; }}")
        _ed_reset.clicked.connect(lambda: self._reset_editor_font())
        _ed_row = QHBoxLayout()
        _ed_row.setSpacing(6)
        _ed_row.addWidget(self.editor_font_combo)
        _ed_row.addWidget(_ed_reset)
        layout.addLayout(_ed_row)
        layout.addSpacing(6)
        self.editor_size_combo = QComboBox()
        for s in ["8","9","10","11","12","13","14","15","16","18","20","22","24","28","32","36"]:
            self.editor_size_combo.addItem(s)
        cur = str(self.config.get("editor_font_size", 14))
        idx = self.editor_size_combo.findText(cur)
        if idx >= 0:
            self.editor_size_combo.setCurrentIndex(idx)
        self.editor_size_combo.setFixedWidth(90)
        self.editor_size_combo.setStyleSheet(_combo_style)
        self.editor_size_combo.currentTextChanged.connect(self._on_editor_size_changed)
        layout.addWidget(self.editor_size_combo)
        layout.addSpacing(8)

        layout.addWidget(self._make_section_label("WINDOWS"))

        self.console_toggle = ToggleSwitch(checked=self.config.get("show_console", True))
        self.console_toggle.toggled.connect(self._on_console_toggle)
        self._make_setting_row(layout, "Konsole anzeigen",
                               "Python-Konsolenfenster im Hintergrund anzeigen oder verstecken.",
                               self.console_toggle)

        layout.addWidget(self._make_section_label("EXPORT"))

        btn_txt = QPushButton("Exportieren")
        btn_txt.setFixedWidth(120)
        btn_txt.setStyleSheet(f"background: {T['bg3']}; border: 1px solid {T['border']}; color: {T['text']}; border-radius: 6px; padding: 6px 14px;")
        btn_txt.clicked.connect(self._export_txt)
        self._make_setting_row(layout, "Als TXT exportieren",
                               "Eine .txt-Datei pro Notiz in einem Verzeichnis speichern.", btn_txt)

        btn_json = QPushButton("Exportieren")
        btn_json.setFixedWidth(120)
        btn_json.setStyleSheet(f"background: {T['bg3']}; border: 1px solid {T['border']}; color: {T['text']}; border-radius: 6px; padding: 6px 14px;")
        btn_json.clicked.connect(self._export_json)
        self._make_setting_row(layout, "Als JSON exportieren",
                               "Alle Notizen als einzelne notizen_export.json speichern.", btn_json)

        layout.addStretch()
        self.pages.addWidget(scroll)

    # ── Appearance Page ──
    def _build_appearance_page(self):
        page = QWidget()
        page.setStyleSheet(f"background: {T['bg']};")
        scroll = QScrollArea()
        scroll.setWidget(page)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(0)

        layout.addWidget(self._make_section_label("ERSCHEINUNGSBILD"))

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        current = self.config.get("theme", "dark")
        self.theme_combo.setCurrentIndex(0 if current == "dark" else 1)
        self.theme_combo.setFixedWidth(160)

        apply_btn = QPushButton("Anwenden")
        apply_btn.setFixedWidth(100)
        apply_btn.setStyleSheet(f"background: {T['accent']}; color: #000; border: none; font-weight: bold; border-radius: 6px; padding: 6px 14px;")
        apply_btn.clicked.connect(self._apply_theme)

        theme_row_widget = QWidget()
        theme_row_widget.setStyleSheet("background: transparent; border: none;")
        trw_l = QHBoxLayout(theme_row_widget)
        trw_l.setContentsMargins(0, 0, 0, 0)
        trw_l.setSpacing(8)
        trw_l.addWidget(self.theme_combo)
        trw_l.addWidget(apply_btn)

        self._make_setting_row(layout, "Farbschema",
                               "Waehle zwischen Dark- und Light-Theme.", theme_row_widget)

        layout.addStretch()
        self.pages.addWidget(scroll)

    # ── AI Page ──
    def _build_ai_page(self):
        page = QWidget()
        page.setStyleSheet(f"background: {T['bg']};")
        scroll = QScrollArea()
        scroll.setWidget(page)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(0)

        layout.addWidget(self._make_section_label("PROVIDER"))

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Groq", "Gemini"])
        current = self.config.get("ai_provider", "groq")
        self.provider_combo.setCurrentIndex(0 if current == "groq" else 1)
        self.provider_combo.setFixedWidth(160)
        self._make_setting_row(layout, "KI-Provider",
                               "Waehle den Anbieter fuer KI-Aktionen.", self.provider_combo)

        layout.addWidget(self._make_section_label("GROQ"))

        self.groq_field = self._make_field(self.config.get("groq_api_key", ""), "gsk_...", echo=True)
        self._make_setting_row(layout, "Groq API Key",
                               "Kostenlos unter console.groq.com", self.groq_field)

        self.groq_model_field = self._make_field(self.config.get("ai_model_groq", "llama-3.1-8b-instant"))
        self._make_setting_row(layout, "Groq Modell",
                               "z.B. llama-3.1-8b-instant", self.groq_model_field)

        layout.addWidget(self._make_section_label("GEMINI"))

        self.gemini_field = self._make_field(self.config.get("gemini_api_key", ""), "AI...", echo=True)
        self._make_setting_row(layout, "Gemini API Key",
                               "Via Google AI Studio (aistudio.google.com)", self.gemini_field)

        self.gemini_model_field = self._make_field(self.config.get("ai_model_gemini", "gemini-2.0-flash"))
        self._make_setting_row(layout, "Gemini Modell",
                               "z.B. gemini-2.0-flash", self.gemini_model_field)

        save_btn = QPushButton("Speichern")
        save_btn.setFixedWidth(120)
        save_btn.setStyleSheet(f"background: {T['accent']}; color: #000; border: none; font-weight: bold; border-radius: 6px; padding: 7px 14px;")
        save_btn.clicked.connect(self._save_ai)
        layout.addSpacing(16)
        layout.addWidget(save_btn)

        layout.addStretch()
        self.pages.addWidget(scroll)

    # ── Sync Page ──
    def _build_sync_page(self):
        page = QWidget()
        page.setStyleSheet(f"background: {T['bg']};")
        scroll = QScrollArea()
        scroll.setWidget(page)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(0)

        layout.addWidget(self._make_section_label("GOOGLE DRIVE"))

        self.creds_field = self._make_field(self.config.get("drive_credentials", ""), "Pfad zur credentials.json")
        self._make_setting_row(layout, "Credentials-Datei",
                               "Pfad zur OAuth-JSON-Datei (siehe SETUP.md)", self.creds_field)

        self.sync_status_label = QLabel("Status: Unbekannt")
        self.sync_status_label.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(11)}px;")
        self._make_setting_row(layout, "Verbindungsstatus", "", self.sync_status_label)

        save_btn = QPushButton("Speichern")
        save_btn.setFixedWidth(120)
        save_btn.setStyleSheet(f"background: {T['accent']}; color: #000; border: none; font-weight: bold; border-radius: 6px; padding: 7px 14px;")
        save_btn.clicked.connect(self._save_sync)
        layout.addSpacing(16)
        layout.addWidget(save_btn)

        layout.addWidget(self._make_section_label("SYNC-MODUS"))
        self.oneway_toggle = ToggleSwitch(checked=self.config.get("one_way_sync", False))
        self.oneway_toggle.toggled.connect(self._on_oneway_toggle)
        self._make_setting_row(layout, "Einweg-Sync (PC \u2192 Handy)",
                               "Nur vom PC zum Handy synchronisieren.\nHandy kann keine \u00c4nderungen zur\u00fcckschreiben.", self.oneway_toggle)

        layout.addWidget(self._make_section_label("ENTWICKLER"))
        reset_btn = QPushButton("Gelöscht-Liste zurücksetzen")
        reset_btn.setFixedWidth(220)
        reset_btn.setStyleSheet(f"background: {T['bg2']}; color: {T['text']}; border: 1px solid {T['border']}; border-radius: 6px; padding: 7px 14px;")
        reset_btn.clicked.connect(self._reset_tombstones)
        self._make_setting_row(layout, "Tombstones", "Lösch-Markierungen zurücksetzen (bei Sync-Problemen)", reset_btn)

        layout.addStretch()
        self.pages.addWidget(scroll)

    def _on_cat_change(self, index):
        self.pages.setCurrentIndex(index)
        cats = ["Allgemein", "Darstellung", "KI", "Synchronisation", "Nutzer", "Backup"]
        if index < len(cats):
            self.header_title.setText(cats[index])

    def _apply_theme(self):
        theme_name = "light" if self.theme_combo.currentIndex() == 1 else "dark"
        self.config["theme"] = theme_name
        save_config(self.config)
        self.theme_changed.emit(theme_name)

    def _save_ai(self):
        self.config["ai_provider"] = "gemini" if self.provider_combo.currentIndex() == 1 else "groq"
        self.config["groq_api_key"] = self.groq_field.text().strip()
        self.config["gemini_api_key"] = self.gemini_field.text().strip()
        self.config["ai_model_groq"] = self.groq_model_field.text().strip() or "llama-3.1-8b-instant"
        self.config["ai_model_gemini"] = self.gemini_model_field.text().strip() or "gemini-2.0-flash"
        save_config(self.config)

    def _on_console_toggle(self, checked: bool):
        self.config["show_console"] = checked
        save_config(self.config)
        _set_console_visible(checked)

    def _on_title_toggle(self, checked: bool):
        self.config["show_title"] = checked
        save_config(self.config)
        main_app = self.parent()
        if hasattr(main_app, 'title_input'):
            main_app.title_input.setVisible(checked)
            main_app.date_label.setVisible(checked)

    def _reset_editor_font(self):
        self.editor_font_combo.setCurrentFont(QFont("Consolas"))
        self._on_editor_font_changed(QFont("Consolas"))
        idx = self.editor_size_combo.findText("14")
        if idx >= 0:
            self.editor_size_combo.setCurrentIndex(idx)

    def _on_ui_font_changed(self, font: QFont):
        _UI_FONT[0] = font.family()
        self.config["ui_font"] = font.family()
        save_config(self.config)
        # Nur App-Stylesheet neu setzen – kein UI-Rebuild nötig
        QApplication.instance().setStyleSheet(build_stylesheet())

    def _on_editor_font_changed(self, font: QFont):
        self.config["editor_font"] = font.family()
        save_config(self.config)
        main_app = self.parent()
        if hasattr(main_app, '_apply_editor_font'):
            main_app._apply_editor_font()

    def _on_editor_size_changed(self, size_text: str):
        try:
            self.config["editor_font_size"] = int(size_text)
        except ValueError:
            return
        save_config(self.config)
        main_app = self.parent()
        if hasattr(main_app, '_apply_editor_font'):
            main_app._apply_editor_font()

    def _save_sync(self):
        self.config["drive_credentials"] = self.creds_field.text().strip()
        save_config(self.config)
        main_app = self.parent().parent()
        if hasattr(main_app, '_init_drive'):
            main_app._init_drive()

    def _on_oneway_toggle(self, checked: bool):
        old = self.config.get("one_way_sync", False)
        if checked == old:
            return
        msg = ("Einweg-Sync aktivieren?\n\n"
               "Das Handy kann dann keine \u00c4nderungen mehr zur\u00fcckschreiben.\n"
               "Die App wird neu gestartet.") if checked else (
               "Zwei-Wege-Sync wieder aktivieren?\n"
               "Die App wird neu gestartet.")
        reply = QMessageBox.question(self, "Sync-Modus \u00e4ndern", msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            self.oneway_toggle.blockSignals(True)
            self.oneway_toggle.setChecked(old)
            self.oneway_toggle.blockSignals(False)
            return
        self.config["one_way_sync"] = checked
        save_config(self.config)
        # MainWindow finden (durch Parent-Chain nach oben)
        main_app = self.parent()
        while main_app and not hasattr(main_app, 'notes_data'):
            main_app = main_app.parent()
        # Upload mit neuem Flag, damit PWA es sieht
        if main_app and hasattr(main_app, 'notes_data'):
            main_app.notes_data["one_way_sync"] = checked
            save_notes(main_app.notes_data)
            print(f"[SYNC] one_way_sync={checked}, uploading...")
            if hasattr(main_app, 'drive_sync') and main_app.drive_sync and main_app.drive_sync.is_connected():
                upload_data = dict(main_app.notes_data)
                upload_data["notes"] = [{k: v for k, v in n.items() if k != "_base"} for n in upload_data.get("notes", [])]
                ok = main_app.drive_sync.upload(upload_data)
                print(f"[SYNC] one_way_sync upload: {'OK' if ok else 'FAILED'}")
            else:
                print("[SYNC] WARNUNG: drive_sync nicht verbunden!")
        else:
            print("[SYNC] WARNUNG: MainWindow nicht gefunden!")
        # App neu starten
        import subprocess
        subprocess.Popen([sys.executable] + sys.argv)
        QApplication.instance().quit()

    def _reset_tombstones(self):
        reply = QMessageBox.question(self, "Tombstones zurücksetzen",
            "Alle Lösch-Markierungen löschen?\nBereits gelöschte Notizen/Ordner könnten zurückkehren.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        main_app = self.parent()
        if hasattr(main_app, 'notes_data'):
            main_app.notes_data["deleted_ids"] = []
            main_app.notes_data["deleted_folder_ids"] = []
            save_notes(main_app.notes_data)
            if hasattr(main_app, '_upload_to_drive') and main_app.drive_sync and main_app.drive_sync.is_connected():
                import threading
                threading.Thread(target=main_app._upload_to_drive, daemon=True).start()
        QMessageBox.information(self, "Tombstones", "Gelöscht-Liste wurde zurückgesetzt.")

    # ── Users Page ──
    def _build_users_page(self):
        from PyQt6.QtWidgets import QTextEdit
        page = QWidget()
        page.setStyleSheet(f"background: {T['bg']};")
        scroll = QScrollArea()
        scroll.setWidget(page)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(0)

        layout.addWidget(self._make_section_label("FIREBASE SERVICE ACCOUNT"))

        self._fb_sa_field = QTextEdit()
        self._fb_sa_field.setFixedHeight(90)
        self._fb_sa_field.setPlaceholderText('{"type":"service_account","project_id":"...","private_key":"..."}')
        self._fb_sa_field.setPlainText(self.config.get("firebase_service_account", ""))
        self._fb_sa_field.setStyleSheet(f"""
            QTextEdit {{
                background: {T['bg2']}; border: 1px solid {T['border']};
                color: {T['text']}; font-family: monospace; font-size: {_sz(11)}px;
                border-radius: 6px; padding: 6px;
            }}
        """)

        save_sa_btn = QPushButton("Speichern")
        save_sa_btn.setFixedWidth(100)
        save_sa_btn.setStyleSheet(f"background: {T['accent']}; color: #000; border: none; font-weight: bold; border-radius: 6px; padding: 6px 14px;")
        save_sa_btn.clicked.connect(self._save_fb_sa)

        sa_row = QWidget()
        sa_row.setStyleSheet(f"background: transparent; border-top: 1px solid {T['border']};")
        sa_rl = QHBoxLayout(sa_row)
        sa_rl.setContentsMargins(0, 14, 0, 14)
        sa_rl.addWidget(self._fb_sa_field, 1)
        sa_rl.addSpacing(12)
        sa_rl.addWidget(save_sa_btn, 0)
        layout.addWidget(sa_row)

        layout.addWidget(self._make_section_label("NUTZER"))

        load_btn = QPushButton("Nutzer laden")
        load_btn.setFixedWidth(130)
        load_btn.setStyleSheet(f"background: {T['bg3']}; border: 1px solid {T['border']}; color: {T['text']}; border-radius: 6px; padding: 6px 14px;")
        load_btn.clicked.connect(self._load_fb_users)

        self._users_status_lbl = QLabel("")
        self._users_status_lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(11)}px; background: transparent; border: none;")

        hrow = QWidget()
        hrow.setStyleSheet(f"background: transparent; border-top: 1px solid {T['border']};")
        hrl = QHBoxLayout(hrow)
        hrl.setContentsMargins(0, 10, 0, 10)
        hrl.addWidget(load_btn)
        hrl.addWidget(self._users_status_lbl, 1)
        layout.addWidget(hrow)

        self._users_list_layout = QVBoxLayout()
        self._users_list_layout.setContentsMargins(0, 0, 0, 0)
        self._users_list_layout.setSpacing(0)
        layout.addLayout(self._users_list_layout)
        layout.addStretch()
        self.pages.addWidget(scroll)
        self._users_ready.connect(self._render_users)

    # ── Backup Page ──
    def _build_backup_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(32, 24, 32, 24)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setWidget(page)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(0)

        # Info-Text
        info = QLabel(f"Maximal {MAX_BACKUPS} Backups. Älteste werden automatisch gelöscht.")
        info.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(12)}px; background: transparent; border: none; margin-bottom: 12px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Backup erstellen Button
        create_btn = QPushButton("  Backup erstellen")
        create_btn.setIcon(_svg_icon(_BACKUP_SVG, T['accent'], 14))
        create_btn.setIconSize(QSize(14, 14))
        create_btn.setFixedHeight(34)
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T['accent']}22; border: 1px solid {T['accent']}66;
                border-radius: 6px; color: {T['accent']}; font-size: {_sz(13)}px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background: {T['accent']}44; }}
        """)
        create_btn.clicked.connect(self._on_create_backup)
        layout.addWidget(create_btn, 0, Qt.AlignmentFlag.AlignLeft)

        layout.addSpacing(20)
        layout.addWidget(self._make_section_label("GESPEICHERTE BACKUPS"))

        # Liste der Backups
        self._backup_list_layout = QVBoxLayout()
        self._backup_list_layout.setSpacing(0)
        layout.addLayout(self._backup_list_layout)
        layout.addStretch()

        scroll.setWidget(inner)
        self.pages.addWidget(scroll)

    def _on_create_backup(self):
        path = create_backup()
        ts = path.stem.replace("backup_", "").replace("_", " ").replace("-", ".")
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Backup erstellt", f"Backup gespeichert:\n{ts}")
        self._refresh_backup_list()

    def _refresh_backup_list(self):
        # Alle alten Einträge entfernen
        while self._backup_list_layout.count():
            item = self._backup_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        backups = list_backups()
        if not backups:
            lbl = QLabel("Keine Backups vorhanden.")
            lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(13)}px; background: transparent; border: none; padding: 12px 0;")
            self._backup_list_layout.addWidget(lbl)
            return

        for bp in backups:
            try:
                import json as _json
                meta = _json.loads(bp.read_text(encoding="utf-8"))
                created = meta.get("created", "")[:16].replace("T", "  ")
                n_notes = len(meta.get("notes", {}).get("notes", []))
            except Exception:
                created = bp.stem
                n_notes = "?"

            row = QWidget()
            row.setStyleSheet(f"background: transparent; border-top: 1px solid {T['border']};")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 12, 0, 12)
            rl.setSpacing(12)

            lbl = QLabel(f"{created}  •  {n_notes} Notiz{'en' if n_notes != 1 else ''}")
            lbl.setStyleSheet(f"color: {T['text']}; font-size: {_sz(13)}px; background: transparent; border: none;")
            rl.addWidget(lbl, 1)

            load_btn = QPushButton("Laden")
            load_btn.setFixedWidth(70)
            load_btn.setStyleSheet(f"""
                QPushButton {{ background: {T['bg3']}; border: 1px solid {T['border']};
                              border-radius: 5px; color: {T['text']}; font-size: {_sz(12)}px; padding: 4px 0; }}
                QPushButton:hover {{ border-color: {T['accent']}; color: {T['accent']}; }}
            """)
            load_btn.clicked.connect(lambda _, p=bp: self._on_load_backup(p))
            rl.addWidget(load_btn)

            del_btn = QPushButton("Löschen")
            del_btn.setFixedWidth(70)
            del_btn.setStyleSheet(f"""
                QPushButton {{ background: {T['bg3']}; border: 1px solid {T['border']};
                              border-radius: 5px; color: {T['muted']}; font-size: {_sz(12)}px; padding: 4px 0; }}
                QPushButton:hover {{ border-color: #ff5555; color: #ff5555; }}
            """)
            del_btn.clicked.connect(lambda _, p=bp: self._on_delete_backup(p))
            rl.addWidget(del_btn)

            self._backup_list_layout.addWidget(row)

    def _on_load_backup(self, path: Path):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
        dlg = QDialog(self)
        dlg.setWindowTitle("Backup laden")
        dlg.setFixedWidth(360)
        dlg.setStyleSheet(f"background: {T['bg2']}; color: {T['text']};")
        vl = QVBoxLayout(dlg)
        vl.setContentsMargins(24, 20, 24, 20)
        vl.setSpacing(12)

        title_lbl = QLabel("Was soll wiederhergestellt werden?")
        title_lbl.setStyleSheet(f"color: {T['text']}; font-size: {_sz(14)}px; font-weight: 600; background: transparent; border: none;")
        title_lbl.setWordWrap(True)
        vl.addWidget(title_lbl)

        info = QLabel("Die aktuellen Daten werden dabei überschrieben.")
        info.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(12)}px; background: transparent; border: none;")
        info.setWordWrap(True)
        vl.addWidget(info)

        vl.addSpacing(8)

        def btn_style(accent=False):
            if accent:
                return (f"QPushButton {{ background: {T['accent']}22; border: 1px solid {T['accent']}66; "
                        f"border-radius: 6px; color: {T['accent']}; font-size: {_sz(13)}px; padding: 8px 12px; }}"
                        f"QPushButton:hover {{ background: {T['accent']}44; }}")
            return (f"QPushButton {{ background: {T['bg3']}; border: 1px solid {T['border']}; "
                    f"border-radius: 6px; color: {T['text']}; font-size: {_sz(13)}px; padding: 8px 12px; }}"
                    f"QPushButton:hover {{ border-color: {T['accent']}; color: {T['accent']}; }}")

        chosen = [None]  # None | "notes" | "all"

        notes_btn = QPushButton("Nur Notizen laden")
        notes_btn.setStyleSheet(btn_style(True))
        notes_btn.clicked.connect(lambda: (chosen.__setitem__(0, "notes"), dlg.accept()))
        vl.addWidget(notes_btn)

        all_btn = QPushButton("Notizen + Einstellungen laden")
        all_btn.setStyleSheet(btn_style(False))
        all_btn.clicked.connect(lambda: (chosen.__setitem__(0, "all"), dlg.accept()))
        vl.addWidget(all_btn)

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.setStyleSheet(f"QPushButton {{ background: transparent; border: none; color: {T['muted']}; "
                                  f"font-size: {_sz(12)}px; padding: 6px; }} QPushButton:hover {{ color: {T['text']}; }}")
        cancel_btn.clicked.connect(dlg.reject)
        vl.addWidget(cancel_btn, 0, Qt.AlignmentFlag.AlignCenter)

        dlg.exec()

        if chosen[0] is None:
            return

        notes_only = (chosen[0] == "notes")
        restore_backup(path, notes_only=notes_only)

        # Config auch im Speicher aktualisieren, damit closeEvent sie nicht überschreibt
        if not notes_only:
            try:
                import json as _json
                restored = _json.loads(path.read_text(encoding="utf-8")).get("config", {})
                self.config.clear()
                self.config.update(restored)
            except Exception:
                pass

        msg = "Notizen wurden wiederhergestellt." if notes_only else "Backup wurde vollständig wiederhergestellt."
        QMessageBox.information(self, "Backup geladen", msg + "\nBitte das Programm neu starten.")

    def _on_delete_backup(self, path: Path):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Backup löschen",
            f"Backup vom {path.stem.replace('backup_','').replace('_',' ')} wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            path.unlink(missing_ok=True)
            self._refresh_backup_list()

    def _save_fb_sa(self):
        self.config["firebase_service_account"] = self._fb_sa_field.toPlainText().strip()
        save_config(self.config)
        self._users_status_lbl.setText("Gespeichert.")

    def _load_fb_users(self):
        self._users_status_lbl.setText("Lade...")
        def run():
            users, err = self._fetch_firestore_users()
            self._users_ready.emit(users, err)
        threading.Thread(target=run, daemon=True).start()

    def _fetch_firestore_users(self):
        import json as _json
        sa_raw = self.config.get("firebase_service_account", "").strip()
        if not sa_raw:
            return None, "Kein Service Account gespeichert."
        try:
            from google.oauth2 import service_account as _sa
            from google.auth.transport.requests import Request as _Req
            sa_info = _json.loads(sa_raw)
            project_id = sa_info.get("project_id", "")
            creds = _sa.Credentials.from_service_account_info(
                sa_info, scopes=["https://www.googleapis.com/auth/datastore"])
            creds.refresh(_Req())
            url = (f"https://firestore.googleapis.com/v1/projects/{project_id}"
                   f"/databases/(default)/documents/users")
            resp = requests.get(url, headers={"Authorization": f"Bearer {creds.token}"})
            resp.raise_for_status()
            docs = resp.json().get("documents", [])
            users = []
            for doc in docs:
                uid = doc["name"].split("/")[-1]
                f = doc.get("fields", {})
                users.append({
                    "uid": uid,
                    "email": f.get("email", {}).get("stringValue", ""),
                    "displayName": f.get("displayName", {}).get("stringValue", ""),
                    "status": f.get("status", {}).get("stringValue", "pending"),
                })
            return users, None
        except Exception as e:
            return None, str(e)

    def _update_firestore_status(self, uid, status):
        import json as _json
        sa_raw = self.config.get("firebase_service_account", "").strip()
        try:
            from google.oauth2 import service_account as _sa
            from google.auth.transport.requests import Request as _Req
            sa_info = _json.loads(sa_raw)
            project_id = sa_info.get("project_id", "")
            creds = _sa.Credentials.from_service_account_info(
                sa_info, scopes=["https://www.googleapis.com/auth/datastore"])
            creds.refresh(_Req())
            url = (f"https://firestore.googleapis.com/v1/projects/{project_id}"
                   f"/databases/(default)/documents/users/{uid}"
                   f"?updateMask.fieldPaths=status")
            body = {"fields": {"status": {"stringValue": status}}}
            resp = requests.patch(url, json=body,
                                  headers={"Authorization": f"Bearer {creds.token}"})
            resp.raise_for_status()
            return True, None
        except Exception as e:
            return False, str(e)

    def _render_users(self, users, err):
        # Alte Einträge löschen
        while self._users_list_layout.count():
            child = self._users_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if err:
            self._users_status_lbl.setText(f"Fehler: {err[:80]}")
            return
        if not users:
            self._users_status_lbl.setText("Keine Nutzer in Firestore.")
            return

        self._users_status_lbl.setText(f"{len(users)} Nutzer geladen")

        STATUS_COLOR = {"approved": T["accent"], "denied": "#ff5555", "pending": "#ffaa00"}

        for u in users:
            row = QWidget()
            row.setStyleSheet(f"background: transparent; border-top: 1px solid {T['border']};")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 10, 0, 10)
            rl.setSpacing(8)

            col = QWidget()
            col.setStyleSheet("background: transparent; border: none;")
            cl = QVBoxLayout(col)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(2)

            email_lbl = QLabel(u["email"] or u["uid"])
            email_lbl.setStyleSheet(f"color: {T['text']}; font-size: {_sz(13)}px; border: none; background: transparent;")
            st_color = STATUS_COLOR.get(u["status"], T["muted"])
            st_lbl = QLabel(u["status"].upper())
            st_lbl.setStyleSheet(f"color: {st_color}; font-size: {_sz(10)}px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
            cl.addWidget(email_lbl)
            cl.addWidget(st_lbl)
            rl.addWidget(col, 1)

            uid = u["uid"]
            if u["status"] != "approved":
                ok_btn = QPushButton("✓ Genehmigen")
                ok_btn.setFixedWidth(110)
                ok_btn.setStyleSheet(f"background: {T['accent']}; color: #000; border: none; font-weight: bold; border-radius: 5px; padding: 5px 10px; font-size: {_sz(12)}px;")
                ok_btn.clicked.connect(lambda _, i=uid: self._set_user_status(i, "approved"))
                rl.addWidget(ok_btn)

            if u["status"] != "denied":
                no_btn = QPushButton("✗ Ablehnen")
                no_btn.setFixedWidth(100)
                no_btn.setStyleSheet(f"background: {T['bg3']}; color: {T['text']}; border: 1px solid {T['border']}; border-radius: 5px; padding: 5px 10px; font-size: {_sz(12)}px;")
                no_btn.clicked.connect(lambda _, i=uid: self._set_user_status(i, "denied"))
                rl.addWidget(no_btn)

            self._users_list_layout.addWidget(row)

    def _set_user_status(self, uid, status):
        self._users_status_lbl.setText("Speichere...")
        def run():
            ok, err = self._update_firestore_status(uid, status)
            if ok:
                users, e2 = self._fetch_firestore_users()
                self._users_ready.emit(users, e2)
            else:
                self._users_ready.emit(None, err)
        threading.Thread(target=run, daemon=True).start()

    def _export_txt(self):
        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "Export-Verzeichnis waehlen")
        if not dir_path:
            return
        notes = self.parent().findChild(NotizenApp) if False else None
        # Access notes from parent window
        win = self.window()
        for note in win.notes_data.get("notes", []):
            title = note.get("title", "Unbenannte Notiz").replace("/", "_").replace("\\", "_")
            filepath = os.path.join(dir_path, f"{title}.txt")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(note.get("content", ""))
        QMessageBox.information(self, "Export", f"Notizen als TXT exportiert nach:\n{dir_path}")

    def _export_json(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "JSON speichern", "notizen_export.json", "JSON (*.json)")
        if not path:
            return
        win = self.window()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(win.notes_data, f, indent=2, ensure_ascii=False)
        QMessageBox.information(self, "Export", f"Exportiert nach:\n{path}")

    def _close(self):
        self.setVisible(False)
        self.closed.emit()

    def show_overlay(self):
        self.cat_list.setCurrentRow(0)
        self.pages.setCurrentIndex(0)
        self.header_title.setText("Allgemein")
        self.groq_field.setText(self.config.get("groq_api_key", ""))
        self.gemini_field.setText(self.config.get("gemini_api_key", ""))
        self.creds_field.setText(self.config.get("drive_credentials", ""))
        self.provider_combo.setCurrentIndex(0 if self.config.get("ai_provider", "groq") == "groq" else 1)
        self.theme_combo.setCurrentIndex(0 if self.config.get("theme", "dark") == "dark" else 1)
        self._refresh_backup_list()
        self.setVisible(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._close()
        super().keyPressEvent(event)


# ─────────────────────────────────────────────
#  AI DIALOG (kept as overlay-style dialog)
# ─────────────────────────────────────────────
class AIDialog(QDialog):
    def __init__(self, parent, selected_text, config):
        super().__init__(parent)
        self.selected_text = selected_text
        self.config = config
        self.result_text = ""
        self.action = None
        self.setWindowTitle("\u2726 KI-Aktion")
        self.setMinimumSize(540, 520)
        self.setStyleSheet(build_stylesheet())
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("\u2726 KI-AKTION")
        title.setStyleSheet(f"color: {T['accent']}; font-size: {_sz(16)}px; font-weight: bold; letter-spacing: 3px;")
        layout.addWidget(title)

        provider = self.config.get("ai_provider", "groq").upper()
        sub = QLabel(f"Provider: {provider}")
        sub.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(11)}px;")
        layout.addWidget(sub)

        grid = QWidget()
        gl = QHBoxLayout(grid)
        gl.setSpacing(6)
        gl.setContentsMargins(0, 0, 0, 0)

        quick = [
            ("\U0001F4DD Zusammenfassen", "Fasse den Text kurz und praegnant zusammen."),
            ("\u270F\uFE0F Verbessern", "Verbessere Rechtschreibung und Stil. Gib nur den verbesserten Text zurueck."),
            ("\U0001F4CB Regel erstellen", (
                "Forme den folgenden Text in eine strukturierte Regel im folgenden Markdown-Format um:\n\n"
                "## \U0001F539 Regel [Nummer]: [Kurzer Titel]\n\n"
                "Kurze Situationsbeschreibung, wann diese Regel gilt.\n\n"
                "- **Bedingung oder Kontext** -> Konsequenz / Handlungsanweisung\n"
                "- Weitere Punkte falls vorhanden\n\n"
                "\U0001F449 Grundsatz: **Praegnante Zusammenfassung der Kernaussage**\n\n"
                "Beachte: Nur den Regelblock ausgeben, kein weiterer Text. "
                "Behalte alle wichtigen Informationen aus dem Originaltext bei. "
                "Nutze Fettschrift fuer Schluesselwoerter."
            )),
            ("\U0001F4A1 Ideen", "Entwickle kreative Weiterentwicklungen basierend auf diesem Text."),
        ]
        for label, prompt in quick:
            btn = QPushButton(label)
            btn.setStyleSheet(f"color: {T['accent']}; border: 1px solid {T['border']}; background: transparent; border-radius: 6px; padding: 6px 10px;")
            btn.clicked.connect(lambda _, p=prompt: self.instruction_box.setPlainText(p))
            gl.addWidget(btn)
        layout.addWidget(grid)

        lbl = QLabel("Eigene Anweisung:")
        lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(10)}px;")
        layout.addWidget(lbl)

        self.instruction_box = QTextEdit()
        self.instruction_box.setMaximumHeight(70)
        self.instruction_box.setPlaceholderText("z.B. 'Schreibe eine Zusammenfassung auf Englisch'...")
        layout.addWidget(self.instruction_box)

        run_btn = QPushButton("\u25B6  Ausfuehren")
        run_btn.setStyleSheet(f"background: {T['accent']}; color: #000; border: none; font-weight: bold; border-radius: 6px; padding: 8px;")
        run_btn.setMinimumHeight(38)
        run_btn.clicked.connect(self._run)
        layout.addWidget(run_btn)

        rlbl = QLabel("Ergebnis:")
        rlbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(10)}px;")
        layout.addWidget(rlbl)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setPlaceholderText("Ergebnis erscheint hier...")
        layout.addWidget(self.result_box)

        btn_row = QHBoxLayout()
        replace_btn = QPushButton("Ersetzen")
        replace_btn.setStyleSheet(f"color: {T['accent']}; border: 1px solid {T['border']};")
        replace_btn.clicked.connect(lambda: self._finish("replace"))
        copy_btn = QPushButton("Kopieren")
        copy_btn.setStyleSheet(f"color: {T['muted']}; border: 1px solid {T['border']};")
        copy_btn.clicked.connect(self._copy)
        close_btn = QPushButton("Schliessen")
        close_btn.setStyleSheet(f"color: {T['muted']}; border: none;")
        close_btn.clicked.connect(lambda: self._finish(None))
        btn_row.addWidget(replace_btn)
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _run(self):
        instruction = self.instruction_box.toPlainText().strip()
        if not instruction:
            QMessageBox.warning(self, "Hinweis", "Bitte gib eine Anweisung ein.")
            return
        self.result_box.setPlainText("\u23F3 Wird verarbeitet...")
        self.worker = AIWorker(self.config, instruction, self.selected_text)
        self.worker.result_ready.connect(self._on_result)
        self.worker.error.connect(lambda e: self.result_box.setPlainText(f"Fehler: {e}"))
        self.worker.start()

    def _on_result(self, text):
        self.result_text = text
        self.result_box.setPlainText(text)

    def _copy(self):
        text = self.result_box.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)

    def _finish(self, action):
        self.action = action
        self.accept()


# ─────────────────────────────────────────────
#  AI ANSWER DIALOG
# ─────────────────────────────────────────────
class AIAnswerDialog(QDialog):
    open_note = pyqtSignal(str)

    def __init__(self, parent, query, result, notes):
        super().__init__(parent)
        self.result = result
        self.notes = notes
        self.setWindowTitle("\u2726 KI-Antwort")
        self.setMinimumSize(560, 480)
        self.setStyleSheet(build_stylesheet())
        self._build(query)

    def _build(self, query):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        title_lbl = QLabel("\u2726 KI-ANTWORT")
        title_lbl.setStyleSheet(f"color: {T['accent']}; font-size: {_sz(16)}px; font-weight: bold; letter-spacing: 3px;")
        layout.addWidget(title_lbl)

        query_lbl = QLabel(f"Frage: {query}")
        query_lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(11)}px;")
        query_lbl.setWordWrap(True)
        layout.addWidget(query_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {T['border']};")
        layout.addWidget(sep)

        answer_lbl = QLabel("Antwort:")
        answer_lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(10)}px;")
        layout.addWidget(answer_lbl)

        self.answer_box = QTextEdit()
        self.answer_box.setReadOnly(True)
        self.answer_box.setPlainText(self.result.get("answer", "Keine Antwort erhalten."))
        self.answer_box.setStyleSheet(
            f"background: {T['bg2']}; border: 1px solid {T['border']}; border-radius: 6px; padding: 8px; font-size: {_sz(12)}px;"
        )
        layout.addWidget(self.answer_box, stretch=1)

        sources = self.result.get("sources", [])
        if sources:
            src_lbl = QLabel("Quellen:")
            src_lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(10)}px;")
            layout.addWidget(src_lbl)

            src_widget = QWidget()
            src_layout = QVBoxLayout(src_widget)
            src_layout.setSpacing(4)
            src_layout.setContentsMargins(0, 0, 0, 0)

            for src in sources:
                note = next((n for n in self.notes if n["id"] == src.get("id")), None)
                title = src.get("title") or (note.get("title", "Unbenannt") if note else "Unbekannte Notiz")
                reason = src.get("reason", "")
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(8)

                btn = QPushButton(f"\u2192 {title}")
                btn.setStyleSheet(
                    f"color: {T['accent']}; border: 1px solid {T['border']}; "
                    f"background: transparent; border-radius: 4px; padding: 4px 10px; text-align: left;"
                )
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                note_id = src.get("id", "")
                btn.clicked.connect(lambda _, nid=note_id: self._open(nid))

                reason_lbl = QLabel(reason)
                reason_lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(10)}px;")
                reason_lbl.setWordWrap(True)

                row_layout.addWidget(btn)
                row_layout.addWidget(reason_lbl, stretch=1)
                src_layout.addWidget(row)

            layout.addWidget(src_widget)

        close_btn = QPushButton("Schliessen")
        close_btn.setStyleSheet(f"color: {T['muted']}; border: none; padding: 6px;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _open(self, note_id):
        self.open_note.emit(note_id)
        self.accept()


# ─────────────────────────────────────────────
#  FIND OVERLAY  (Ctrl+F floating top-right)
# ─────────────────────────────────────────────
class FindOverlay(QWidget):
    def __init__(self, editor, container):
        super().__init__(container)
        self.editor = editor
        self.container = container
        self._build()
        self.hide()
        container.installEventFilter(self)

    def _build(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            FindOverlay {{
                background: {T['bg2']};
                border: 1px solid {T['border']};
                border-radius: 10px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 5, 6, 5)
        layout.setSpacing(2)

        # Input field with own subtle background
        self.field = QLineEdit()
        self.field.setPlaceholderText("Suchen...")
        self.field.setFixedHeight(30)
        self.field.setStyleSheet(f"""
            QLineEdit {{
                background: {T['bg3']}; border: 1px solid {T['border']};
                border-radius: 6px; padding: 0 8px;
                color: {T['text']}; font-size: {_sz(13)}px;
            }}
            QLineEdit:focus {{ border-color: {T['accent']}; }}
        """)
        self.field.textChanged.connect(self._on_text_changed)
        self.field.returnPressed.connect(self._find_next)
        layout.addWidget(self.field, 1)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(11)}px; background: transparent; border: none; padding: 0 6px;")
        self.count_lbl.setMinimumWidth(60)
        layout.addWidget(self.count_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(20)
        sep.setStyleSheet(f"background: {T['border']}; border: none;")
        layout.addWidget(sep)

        _btn_style = f"""
            QPushButton {{ background: transparent; border: none; color: {T['muted']};
                          font-size: {_sz(15)}px; border-radius: 5px; padding: 0; }}
            QPushButton:hover {{ background: rgba(255,255,255,0.10); color: {T['text']}; }}
        """
        for label, slot in [("\u2191", self._find_prev), ("\u2193", self._find_next)]:
            btn = QPushButton(label)
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(_btn_style)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        layout.addSpacing(2)

        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; color: {T['muted']};
                          font-size: {_sz(13)}px; border-radius: 5px; padding: 0; }}
            QPushButton:hover {{ background: rgba(255,255,255,0.10); color: {T['text']}; }}
        """)
        close_btn.clicked.connect(self.close_bar)
        layout.addWidget(close_btn)

    def open_bar(self):
        self._reposition()
        self.show()
        self.raise_()
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            self.field.setText(cursor.selectedText())
        self.field.selectAll()
        self.field.setFocus()
        self._on_text_changed(self.field.text())

    def close_bar(self):
        self.editor.setExtraSelections([])
        self.hide()
        self.editor.setFocus()

    def _reposition(self):
        cw = self.container.width()
        w = min(340, cw - 60)
        self.setGeometry(cw - w - 20, 36, w, 44)

    def eventFilter(self, obj, event):
        if obj is self.container and event.type() == QEvent.Type.Resize:
            if self.isVisible():
                self._reposition()
        return False

    def _on_text_changed(self, text):
        if not text:
            self.editor.setExtraSelections([])
            self.count_lbl.setText("")
            return
        selections = self._find_all(text)
        self.editor.setExtraSelections(selections)
        count = len(selections)
        if count == 0:
            self.count_lbl.setText("Nicht gefunden")
            self.count_lbl.setStyleSheet(f"color: {T['danger']}; font-size: {_sz(11)}px; background: transparent; border: none;")
        else:
            self.count_lbl.setText(f"{count} Treffer")
            self.count_lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(11)}px; background: transparent; border: none;")
        if selections:
            self.editor.setTextCursor(selections[0].cursor)
            self.editor.ensureCursorVisible()

    def _find_all(self, query):
        doc = self.editor.document()
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(255, 200, 0, 150))
        selections = []
        cursor = QTextCursor(doc)
        while True:
            cursor = doc.find(query, cursor)
            if cursor.isNull():
                break
            sel = QTextEdit.ExtraSelection()
            sel.format = fmt
            sel.cursor = QTextCursor(cursor)
            selections.append(sel)
        return selections

    def _find_next(self):
        q = self.field.text()
        if not q:
            return
        if not self.editor.find(q):
            self.editor.moveCursor(QTextCursor.MoveOperation.Start)
            self.editor.find(q)

    def _find_prev(self):
        q = self.field.text()
        if not q:
            return
        if not self.editor.find(q, QTextDocument.FindFlag.FindBackward):
            self.editor.moveCursor(QTextCursor.MoveOperation.End)
            self.editor.find(q, QTextDocument.FindFlag.FindBackward)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_bar()
        else:
            super().keyPressEvent(event)


# ─────────────────────────────────────────────
#  QUICK SWITCH DIALOG
# ─────────────────────────────────────────────
class QuickSwitchDialog(QDialog):
    note_selected = pyqtSignal(str)

    def __init__(self, parent, notes):
        super().__init__(parent)
        self.notes = notes
        self._filtered = list(notes)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Popup |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(600)
        self.setStyleSheet("background: transparent;")
        self._build()
        self._center_on_parent()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(0)

        self.card = QWidget()
        self.card.setStyleSheet(f"""
            QWidget {{
                background: {T['bg2']};
                border: 1px solid {T['border']};
                border-radius: 12px;
            }}
        """)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Search field
        field_row = QWidget()
        field_row.setStyleSheet(f"background: transparent; border-bottom: 1px solid {T['border']};")
        fr_layout = QHBoxLayout(field_row)
        fr_layout.setContentsMargins(16, 12, 16, 12)
        fr_layout.setSpacing(8)

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Gib einen Namen ein, um zu einer Notiz zu wechseln oder diese zu erstellen...")
        self.search_field.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; border: none;
                font-size: {_sz(14)}px; color: {T['text']};
            }}
        """)
        self.search_field.textChanged.connect(self._filter)
        self.search_field.returnPressed.connect(self._accept_current)
        fr_layout.addWidget(self.search_field, 1)

        clear_btn = QPushButton("\u2715")
        clear_btn.setFixedSize(22, 22)
        clear_btn.setStyleSheet(f"""
            QPushButton {{ background: {T['bg3']}; border: none; border-radius: 11px;
                          color: {T['muted']}; font-size: {_sz(11)}px; }}
            QPushButton:hover {{ color: {T['text']}; }}
        """)
        clear_btn.clicked.connect(self.search_field.clear)
        fr_layout.addWidget(clear_btn)
        card_layout.addWidget(field_row)

        # Results list
        self.result_list = QListWidget()
        self.result_list.setFixedHeight(320)
        self.result_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent; border: none; outline: none;
                padding: 4px 0;
            }}
            QListWidget::item {{
                padding: 8px 16px; color: {T['accent']};
                font-size: {_sz(13)}px; border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background: rgba(255,255,255,0.08); color: {T['text']};
            }}
            QListWidget::item:hover {{
                background: rgba(255,255,255,0.05);
            }}
        """)
        self.result_list.itemClicked.connect(self._on_item_click)
        card_layout.addWidget(self.result_list)

        # Footer shortcuts
        footer = QWidget()
        footer.setStyleSheet(f"background: transparent; border-top: 1px solid {T['border']};")
        foot_layout = QHBoxLayout(footer)
        foot_layout.setContentsMargins(16, 8, 16, 8)
        foot_layout.setSpacing(16)

        for hint in ["\u2191\u2193 navigieren", "\u23ce \u00f6ffnen", "Shift+\u23ce erstellen", "Esc abbrechen"]:
            lbl = QLabel(hint)
            lbl.setStyleSheet(f"color: {T['muted']}; font-size: {_sz(11)}px; background: transparent; border: none;")
            foot_layout.addWidget(lbl)
        foot_layout.addStretch()
        card_layout.addWidget(footer)

        outer.addWidget(self.card)
        self._populate(self.notes)

    def _center_on_parent(self):
        parent = self.parentWidget()
        if parent:
            pg = parent.geometry()
            x = pg.x() + (pg.width() - self.sizeHint().width()) // 2
            y = pg.y() + pg.height() // 4
            self.move(x, y)

    def _populate(self, notes):
        self.result_list.clear()
        for note in notes:
            title = note.get("title") or "Unbenannte Notiz"
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, note["id"])
            self.result_list.addItem(item)
        if self.result_list.count():
            self.result_list.setCurrentRow(0)

    def _filter(self, text):
        q = text.lower().strip()
        if q:
            self._filtered = [n for n in self.notes if q in (n.get("title") or "").lower()]
        else:
            self._filtered = list(self.notes)
        self._populate(self._filtered)

    def _accept_current(self):
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            self._create_new()
            return
        item = self.result_list.currentItem()
        if item:
            self.note_selected.emit(item.data(Qt.ItemDataRole.UserRole))
            self.accept()

    def _on_item_click(self, item):
        self.note_selected.emit(item.data(Qt.ItemDataRole.UserRole))
        self.accept()

    def _create_new(self):
        # Signal with empty string = create new
        self.note_selected.emit("__new__")
        self.accept()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.reject()
        elif key == Qt.Key.Key_Down:
            row = self.result_list.currentRow()
            if row < self.result_list.count() - 1:
                self.result_list.setCurrentRow(row + 1)
        elif key == Qt.Key.Key_Up:
            row = self.result_list.currentRow()
            if row > 0:
                self.result_list.setCurrentRow(row - 1)
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if not self.card.geometry().contains(event.pos()):
            self.reject()
        else:
            super().mousePressEvent(event)


# ─────────────────────────────────────────────
#  ZOOM EVENT FILTER
# ─────────────────────────────────────────────
#  BILD-RESIZE HANDLE
# ─────────────────────────────────────────────
HANDLE_R = 7  # Radius des Resize-Kreises in px


class _SelectionOverlay(QWidget):
    """Transparentes Overlay – zeichnet blauen Rahmen + Resize-Kreis über dem selektierten Bild."""

    def __init__(self, viewport):
        super().__init__(viewport)
        self._img_rect = None
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setGeometry(viewport.rect())
        self.hide()

    def update_rect(self, img_rect):
        vp = self.parent()
        if vp:
            self.setGeometry(vp.rect())
        self._img_rect = img_rect
        self.show()
        self.raise_()
        self.update()

    def clear(self):
        self._img_rect = None
        self.hide()

    def paintEvent(self, event):
        if not self._img_rect:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self._img_rect
        p.setPen(QPen(QColor("#4A90E2"), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(r.adjusted(1, 1, -1, -1))
        cx = r.right()
        cy = r.bottom()
        p.setBrush(QBrush(QColor("#4A90E2")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx - HANDLE_R, cy - HANDLE_R, HANDLE_R * 2, HANDLE_R * 2)


# ─────────────────────────────────────────────
#  RICH TEXT EDITOR (Bilder per Paste / DnD)
# ─────────────────────────────────────────────
class NoteTextEdit(QTextEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._img_b64_cache: dict = {}
        self._img_fullres_cache: dict = {}  # volle Auflösung für Vollbild (nur In-Session)
        self._overlay: '_SelectionOverlay | None' = None
        # Autocomplete-Popup bei App-Fokusverlust schließen (Alt+Tab)
        QApplication.instance().applicationStateChanged.connect(self._on_app_state_changed)
        self._sel_img_pos: 'int | None' = None
        self._dragging    = False
        self._drag_start  = None
        self._drag_orig_w = 0
        self._drag_orig_h = 0
        self._block_scroll = False
        self._paste_plain  = False
        # Copy-Block Overlay-Button
        self._copy_btn = QPushButton(self.viewport())
        self._copy_btn.setFixedSize(26, 26)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.setToolTip("Block-Inhalt kopieren")
        self._copy_btn.setIcon(self._make_copy_icon())
        self._copy_btn.setIconSize(QSize(16, 16))
        self._copy_btn.setStyleSheet(
            "QPushButton { background: transparent; border: 1px solid #b0c8d8; border-radius: 4px; padding: 0; }"
            "QPushButton:hover { background: #d0e4f0; }"
        )
        self._copy_btn.clicked.connect(self._on_copy_btn)
        self._copy_btn.hide()
        self._active_cb_frame = None
        self.cursorPositionChanged.connect(self._update_copy_btn)

    @staticmethod
    def _make_copy_icon():
        """Erzeugt ein Copy-Icon (zwei ueberlappende Quadrate)."""
        px = QPixmap(16, 16)
        px.fill(QColor(0, 0, 0, 0))
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#5a7a8a"), 1.4)
        p.setPen(pen)
        p.setBrush(QBrush(QColor(0, 0, 0, 0)))
        # Hinteres Quadrat (oben links)
        p.drawRoundedRect(1, 1, 10, 10, 2, 2)
        # Vorderes Quadrat (unten rechts, gefuellt)
        p.setBrush(QBrush(QColor("#e8f0f8")))
        p.drawRoundedRect(5, 5, 10, 10, 2, 2)
        p.end()
        return QIcon(px)

    def _get_overlay(self) -> '_SelectionOverlay':
        if self._overlay is None:
            self._overlay = _SelectionOverlay(self.viewport())
        return self._overlay

    def _sel_img_rect(self):
        if self._sel_img_pos is None:
            return None
        c = QTextCursor(self.document())
        c.setPosition(self._sel_img_pos)
        fmt = c.charFormat()          # charFormat() = char BEFORE cursor = image
        if not fmt.isImageFormat():
            return None
        img_fmt = fmt.toImageFormat()
        r = self.cursorRect(c)        # cursor sits at RIGHT edge of image
        left_x = r.x() - int(img_fmt.width())
        return QRect(left_x, r.y(), int(img_fmt.width()), int(img_fmt.height()))

    def _update_overlay(self):
        rect = self._sel_img_rect()
        ov = self._get_overlay()
        if rect:
            ov.update_rect(rect)
        else:
            ov.clear()
            self._sel_img_pos = None

    # ── Maus-Events ────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            import math
            vp_pos = event.position().toPoint()
            # Klick im Bottom-Padding → Cursor UNTER die letzte Zeile
            if self.document().characterCount() > 1:
                end_cur = QTextCursor(self.document())
                end_cur.movePosition(QTextCursor.MoveOperation.End)
                last_rect = self.cursorRect(end_cur)
                if last_rect.isValid() and vp_pos.y() > last_rect.bottom() + 4:
                    self._block_scroll = True
                    # Neue Zeile anfuegen wenn letzte Zeile nicht leer
                    if self.document().lastBlock().text():
                        end_cur.insertBlock()
                    else:
                        self.setTextCursor(end_cur)
                    self._block_scroll = False
                    event.accept()
                    return
            rect = self._sel_img_rect()
            if rect is not None:
                cx = rect.right()
                cy = rect.bottom()
                if math.sqrt((vp_pos.x() - cx) ** 2 + (vp_pos.y() - cy) ** 2) <= HANDLE_R + 4:
                    self._dragging    = True
                    self._drag_start  = event.globalPosition().toPoint()
                    c = QTextCursor(self.document())
                    c.setPosition(self._sel_img_pos)
                    fmt = c.charFormat().toImageFormat()
                    self._drag_orig_w = int(fmt.width())
                    self._drag_orig_h = int(fmt.height())
                    event.accept()
                    return
            super().mousePressEvent(event)
            cur = self.cursorForPosition(vp_pos)
            img_cur = self._find_image_cursor(cur)
            if img_cur:
                # Verify click is actually within the image's visual bounds
                c2 = QTextCursor(self.document())
                c2.setPosition(img_cur.position())
                ifmt = c2.charFormat()
                if ifmt.isImageFormat():
                    ir = self.cursorRect(c2)
                    ifw = int(ifmt.toImageFormat().width())
                    ifh = int(ifmt.toImageFormat().height())
                    img_visual = QRect(ir.x() - ifw, ir.y(), ifw, ifh)
                    self._sel_img_pos = img_cur.position() if img_visual.contains(vp_pos) else None
                else:
                    self._sel_img_pos = None
            else:
                self._sel_img_pos = None
            self._update_overlay()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_start is not None:
            dx = event.globalPosition().toPoint().x() - self._drag_start.x()
            ratio = self._drag_orig_h / max(1, self._drag_orig_w)
            new_w = max(20, self._drag_orig_w + dx)
            new_h = max(20, int(new_w * ratio))
            c = QTextCursor(self.document())
            c.setPosition(self._sel_img_pos)
            fmt = c.charFormat()          # char BEFORE cursor = image
            if fmt.isImageFormat():
                nf = QTextImageFormat()
                nf.setName(fmt.toImageFormat().name())
                nf.setWidth(new_w)
                nf.setHeight(new_h)
                # Select the image char (it's BEFORE the cursor → move left first)
                sel = QTextCursor(c)
                sel.movePosition(QTextCursor.MoveOperation.Left)
                sel.movePosition(QTextCursor.MoveOperation.Right,
                                 QTextCursor.MoveMode.KeepAnchor, 1)
                sel.setCharFormat(nf)
                self._update_overlay()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging   = False
            self._drag_start = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def scrollContentsBy(self, dx, dy):
        if self._block_scroll:
            return
        super().scrollContentsBy(dx, dy)
        if self._sel_img_pos is not None:
            self._update_overlay()
        if self._active_cb_frame:
            self._update_copy_btn()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._overlay:
            self._overlay.setGeometry(self.viewport().rect())
        if self._sel_img_pos is not None:
            self._update_overlay()


    def _find_image_cursor(self, cursor):
        # charFormat() = char BEFORE cursor → cursor AFTER image gives image format
        if cursor.charFormat().isImageFormat():
            return cursor
        # Cursor might be BEFORE image → check one step right
        test = QTextCursor(cursor)
        test.movePosition(QTextCursor.MoveOperation.Right)
        if test.charFormat().isImageFormat():
            return test
        return None

    def wheelEvent(self, event):
        # Ctrl+Scroll: Qt's eingebauten Zoom blockieren — unser _WheelZoomFilter übernimmt
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            event.ignore()
            return
        super().wheelEvent(event)

    def insertFromMimeData(self, source):
        img = self._extract_image(source)
        if img:
            self._insert_qimage(img)
        elif self._paste_plain or not source.hasHtml():
            # Kein HTML vorhanden oder explizit Plain-Text gewünscht (Ctrl+Shift+V)
            self.insertPlainText(source.text())
        else:
            # Ctrl+V: Formatierung übernehmen (fett, kursiv, Größe etc.)
            super().insertFromMimeData(source)

    def dragEnterEvent(self, event):
        md = event.mimeData()
        if md.hasImage() or self._has_image_urls(md):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        md = event.mimeData()
        if md.hasImage() or self._has_image_urls(md):
            self.setTextCursor(self.cursorForPosition(event.position().toPoint()))
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        md = event.mimeData()
        img = self._extract_image(md)
        if img:
            self.setTextCursor(self.cursorForPosition(event.position().toPoint()))
            self._insert_qimage(img)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    # ── Hilfsmethoden ──────────────────────────
    @staticmethod
    def _has_image_urls(md):
        _IMG_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff')
        return any(url.toLocalFile().lower().endswith(_IMG_EXT) for url in md.urls())

    def _extract_image(self, md):
        if md.hasImage():
            img = QImage(md.imageData())
            return img if not img.isNull() else None
        for url in md.urls():
            path = url.toLocalFile()
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff')):
                img = QImage(path)
                if not img.isNull():
                    return img
        return None

    def _insert_qimage(self, image: QImage, max_width: int = 1920):
        import uuid
        # Volle Auflösung begrenzen
        full = image if image.width() <= max_width else image.scaledToWidth(
            max_width, Qt.TransformationMode.SmoothTransformation)
        # Display-Größe: 20 % — als Preview in den Editor (1:1 → scharf)
        disp_w = max(20, int(full.width() * 0.2))
        disp_h = max(20, int(full.height() * 0.2))
        preview = full.scaledToWidth(disp_w, Qt.TransformationMode.SmoothTransformation)

        name = f"img_{uuid.uuid4().hex[:10]}.png"
        # Preview als Dokument-Resource (wird im Editor scharf angezeigt)
        self.document().addResource(QTextDocument.ResourceType.ImageResource, QUrl(name), preview)
        # Full-Res im HTML speichern (persistiert über Neustarts für Vollbild)
        ba = QByteArray(); buf = QBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        full.save(buf, "PNG")
        fullres_b64 = bytes(ba.toBase64()).decode()
        self._img_b64_cache[name] = fullres_b64
        self._img_fullres_cache[name] = fullres_b64

        fmt = QTextImageFormat()
        fmt.setName(name)
        fmt.setWidth(disp_w)
        fmt.setHeight(disp_h)
        self.textCursor().insertImage(fmt)

    def resize_image_at_cursor(self, factor: float):
        cur = self.textCursor()
        fmt = cur.charFormat()          # char BEFORE cursor
        if not fmt.isImageFormat():
            # Try: image is after cursor
            test = QTextCursor(cur)
            test.movePosition(QTextCursor.MoveOperation.Right)
            fmt = test.charFormat()
            if fmt.isImageFormat():
                cur = test
        if not fmt.isImageFormat():
            return
        img_fmt = fmt.toImageFormat()
        new_w = max(20, int(img_fmt.width() * factor))
        new_h = max(20, int(img_fmt.height() * factor))
        new_fmt = QTextImageFormat()
        new_fmt.setName(img_fmt.name())
        new_fmt.setWidth(new_w)
        new_fmt.setHeight(new_h)
        # Image is BEFORE cur → move left to select it
        sel = QTextCursor(cur)
        sel.movePosition(QTextCursor.MoveOperation.Left)
        sel.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
        sel.setCharFormat(new_fmt)

    def is_cursor_on_image(self) -> bool:
        cur = self.textCursor()
        if cur.charFormat().isImageFormat():   # image before cursor
            return True
        test = QTextCursor(cur)
        test.movePosition(QTextCursor.MoveOperation.Right)
        return test.charFormat().isImageFormat()  # image after cursor

    # ── Copy Block ────────────────────────────
    _COPYBLOCK_BORDER = QColor("#b8d4e8")
    _COPYBLOCK_BG     = QColor("#e8f0f8")

    def insertCopyBlock(self):
        """Fuegt einen Copy Block (hellblauer Rahmen-Block) an der Cursor-Position ein."""
        cur = self.textCursor()
        if cur.position() > 0:
            cur.insertBlock()
        fmt = QTextFrameFormat()
        fmt.setBorder(1)
        fmt.setBorderBrush(QBrush(self._COPYBLOCK_BORDER))
        fmt.setBackground(QBrush(self._COPYBLOCK_BG))
        fmt.setPadding(12)
        fmt.setTopMargin(4)
        fmt.setBottomMargin(4)
        fmt.setLeftMargin(4)
        fmt.setRightMargin(4)
        fmt.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))
        cur.insertFrame(fmt)
        self.setTextCursor(cur)

    def insertHorizontalLine(self):
        """Fuegt eine horizontale Trennlinie an der Cursor-Position ein."""
        cur = self.textCursor()
        cur.insertHtml('<hr>')
        self.setTextCursor(cur)

    def _get_copyblock_frame(self):
        """Gibt den CopyBlock-Frame zurueck wenn der Cursor sich in einem befindet, sonst None."""
        cur = self.textCursor()
        frame = cur.currentFrame()
        while frame and frame != self.document().rootFrame():
            if self._is_copyblock_frame(frame):
                return frame
            frame = frame.parentFrame()
        return None

    @staticmethod
    def _is_copyblock_frame(frame):
        fmt = frame.frameFormat()
        return fmt.background().color().name() == "#e8f0f8" and fmt.border() >= 1

    def _copy_block_content(self, frame):
        """Kopiert den Inhalt eines CopyBlock-Frames als Rich Text in die Zwischenablage."""
        if not frame:
            return
        start = frame.firstCursorPosition()
        end   = frame.lastCursorPosition()
        sel   = QTextCursor(start)
        sel.setPosition(end.position(), QTextCursor.MoveMode.KeepAnchor)
        from PyQt6.QtCore import QMimeData
        md = QMimeData()
        tmp_doc = QTextDocument()
        tmp_cur = QTextCursor(tmp_doc)
        tmp_cur.insertFragment(sel.selection())
        html = tmp_doc.toHtml()
        md.setHtml(html)
        plain = sel.selectedText().replace('\u2029', '\n').strip()
        md.setText(plain)
        QApplication.clipboard().setMimeData(md)

    # ── ! Autocomplete ────────────────────────
    _COMMANDS = [
        ("copyblock", "\U0001f4cb  Copy Block"),
        ("line", "\u2015  Horizontale Linie"),
    ]
    _insert_popup = None

    def keyPressEvent(self, event):
        # Ctrl+Shift+V: ohne Formatierung einfügen
        if (event.key() == Qt.Key.Key_V and
                event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
            self._paste_plain = True
            self.paste()
            self._paste_plain = False
            return
        # Backspace: CopyBlock loeschen wenn Cursor direkt darunter steht
        if event.key() == Qt.Key.Key_Backspace:
            cur = self.textCursor()
            if not cur.hasSelection() and cur.positionInBlock() == 0:
                test = QTextCursor(cur)
                test.movePosition(QTextCursor.MoveOperation.Left)
                frame = test.currentFrame()
                if frame and frame != self.document().rootFrame() and self._is_copyblock_frame(frame):
                    sel = QTextCursor(self.document())
                    sel.setPosition(frame.firstPosition() - 1)
                    sel.setPosition(frame.lastPosition() + 1, QTextCursor.MoveMode.KeepAnchor)
                    sel.removeSelectedText()
                    return
        # Enter: pruefe ob aktuelle Zeile ein !befehl ist
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._try_execute_command():
                return
        # Escape schliesst Popup
        if event.key() == Qt.Key.Key_Escape and self._insert_popup:
            self._close_insert_popup()
            return
        # Tab: vervollstaendige zum ersten Treffer (Enter fuehrt dann aus)
        if event.key() == Qt.Key.Key_Tab and self._insert_popup:
            prefix = self._get_command_prefix()
            if prefix is not None:
                matches = [k for k, _ in self._COMMANDS if k.startswith(prefix.lower())]
                if matches:
                    cur = self.textCursor()
                    pos = cur.position()
                    cur.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    cur.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
                    cur.removeSelectedText()
                    cur.insertText('!' + matches[0])
                    self.setTextCursor(cur)
                    QTimer.singleShot(0, self._update_insert_popup)
            return
        super().keyPressEvent(event)
        # Popup nur aktualisieren wenn Popup offen oder aktuelle Zeile '!' enthält
        if self._insert_popup or '!' in self.textCursor().block().text():
            QTimer.singleShot(0, self._update_insert_popup)

    def _get_command_prefix(self):
        cur = self.textCursor()
        text = cur.block().text()[:cur.positionInBlock()]
        stripped = text.lstrip()
        if stripped.startswith('!'):
            return stripped[1:]
        return None

    def _try_execute_command(self):
        prefix = self._get_command_prefix()
        if prefix is None:
            return False
        cmd = prefix.strip().lower()
        if any(k == cmd for k, _ in self._COMMANDS):
            self._close_insert_popup()
            cur = self.textCursor()
            # Nur den Befehl löschen (Start → Cursor), Text dahinter bleibt
            pos = cur.position()
            cur.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cur.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
            cur.removeSelectedText()
            self.setTextCursor(cur)
            self._run_command(cmd)
            return True
        return False

    def _run_command(self, cmd):
        if cmd == "copyblock":
            self.insertCopyBlock()
        elif cmd == "line":
            self.insertHorizontalLine()

    def _update_insert_popup(self):
        prefix = self._get_command_prefix()
        if prefix is None:
            self._close_insert_popup()
            return
        matches = [(k, lbl) for k, lbl in self._COMMANDS if k.startswith(prefix.lower())]
        if not matches:
            self._close_insert_popup()
            return
        # Popup als QFrame mit QListWidget — stiehlt NICHT den Fokus
        if not self._insert_popup:
            popup = QFrame(self, Qt.WindowType.ToolTip)
            popup.setStyleSheet(f"""
                QFrame {{ background: {T['bg2']}; border: 1px solid {T['border']}; border-radius: 6px; }}
                QListWidget {{ background: transparent; border: none; color: {T['text']}; font-size: {_sz(13)}px; outline: none; }}
                QListWidget::item {{ padding: 6px 14px; border-radius: 4px; }}
                QListWidget::item:hover {{ background: rgba(255,255,255,0.08); }}
            """)
            lw = QListWidget(popup)
            lw.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            lw.setMouseTracking(True)
            lw.itemClicked.connect(self._on_popup_click)
            lay = QVBoxLayout(popup)
            lay.setContentsMargins(4, 4, 4, 4)
            lay.addWidget(lw)
            self._insert_popup = popup
            self._insert_lw = lw
        lw = self._insert_lw
        lw.clear()
        for cmd_key, cmd_label in matches:
            item = QListWidgetItem('!' + cmd_key)
            item.setData(Qt.ItemDataRole.UserRole, cmd_key)
            lw.addItem(item)
        h = lw.sizeHintForRow(0) * lw.count() + 12
        self._insert_popup.setFixedSize(200, max(32, h))
        cur_rect = self.cursorRect()
        pos = self.viewport().mapToGlobal(cur_rect.bottomLeft())
        self._insert_popup.move(pos)
        self._insert_popup.show()

    def _on_popup_click(self, item):
        cmd = item.data(Qt.ItemDataRole.UserRole)
        self._close_insert_popup()
        cur = self.textCursor()
        pos = cur.position()
        cur.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cur.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
        cur.removeSelectedText()
        self.setTextCursor(cur)
        self._run_command(cmd)

    def _close_insert_popup(self):
        if self._insert_popup:
            self._insert_popup.close()
            self._insert_popup = None
            self._insert_lw = None

    def _on_app_state_changed(self, state):
        if state != Qt.ApplicationState.ApplicationActive:
            self._close_insert_popup()

    # ── Copy-Button Overlay ───────────────────
    def _get_frame_rect(self, frame):
        """Berechnet das Viewport-Rechteck eines QTextFrame ueber das Dokument-Layout."""
        doc_layout = self.document().documentLayout()
        fp = doc_layout.frameBoundingRect(frame)
        # Dokument-Koordinaten → Viewport (Scroll-Offset beruecksichtigen)
        scroll_x = self.horizontalScrollBar().value()
        scroll_y = self.verticalScrollBar().value()
        return QRect(
            int(fp.x()) - scroll_x,
            int(fp.y()) - scroll_y,
            int(fp.width()),
            int(fp.height())
        )

    def _update_copy_btn(self):
        """Zeigt/versteckt den Kopier-Button je nachdem ob Cursor in einem CopyBlock ist."""
        frame = self._get_copyblock_frame()
        if frame:
            self._active_cb_frame = frame
            fr = self._get_frame_rect(frame)
            btn_x = fr.right() - self._copy_btn.width() - 2
            btn_y = fr.top() + 2
            self._copy_btn.move(btn_x, btn_y)
            self._copy_btn.show()
            self._copy_btn.raise_()
        else:
            self._active_cb_frame = None
            self._copy_btn.hide()

    def _on_copy_btn(self):
        if self._active_cb_frame:
            self._copy_block_content(self._active_cb_frame)
            check_px = QPixmap(16, 16)
            check_px.fill(QColor(0, 0, 0, 0))
            p = QPainter(check_px)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(QPen(QColor("#2a7a2a"), 2.0))
            p.drawLine(3, 9, 6, 12)
            p.drawLine(6, 12, 13, 4)
            p.end()
            self._copy_btn.setIcon(QIcon(check_px))
            QTimer.singleShot(800, lambda: self._copy_btn.setIcon(self._make_copy_icon()))

    # ── Serialisierung ─────────────────────────
    def toRichText(self) -> str:
        import re
        doc  = self.document()
        html = doc.toHtml()

        def embed(m):
            src = m.group(1)
            if src.startswith(('data:', 'http://', 'https://')):
                return m.group(0)
            if src in self._img_b64_cache:
                return f'src="data:image/png;base64,{self._img_b64_cache[src]}"'
            res = doc.resource(QTextDocument.ResourceType.ImageResource, QUrl(src))
            if res is None:
                return m.group(0)
            img = res if isinstance(res, QImage) else QImage(res)
            if img.isNull():
                return m.group(0)
            ba = QByteArray(); buf = QBuffer(ba)
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            img.save(buf, "PNG")
            b64 = bytes(ba.toBase64()).decode()
            self._img_b64_cache[src] = b64
            return f'src="data:image/png;base64,{b64}"'

        return re.sub(r'src="([^"]+)"', embed, html)

    def _apply_bottom_padding(self):
        """Setzt 120px Extra-Platz am unteren Rand des Dokuments."""
        root = self.document().rootFrame()
        fmt = root.frameFormat()
        if fmt.bottomMargin() != 120:
            fmt.setBottomMargin(120)
            root.setFrameFormat(fmt)

    def setRichText(self, content: str):
        import re, base64 as _b64
        self._img_b64_cache.clear()
        self._img_fullres_cache.clear()
        if not content.strip().startswith('<'):
            self.setPlainText(content)
            self._apply_bottom_padding()
            return
        doc = self.document()
        counter = [0]

        # Bilder sammeln: name → preview_QImage
        _pending: dict = {}

        def extract_img_tag(m):
            full_tag = m.group(0)
            src_m = re.search(r'src="(data:image[^"]*)"', full_tag)
            if not src_m:
                return full_tag
            src = src_m.group(1)
            try:
                _, data_part = src.split(',', 1)
                raw = _b64.b64decode(data_part)
                full_img = QImage()
                full_img.loadFromData(QByteArray(bytes(raw)))
                if full_img.isNull():
                    return full_tag
                counter[0] += 1
                name = f"img_{counter[0]}.png"
                self._img_b64_cache[name] = data_part
                self._img_fullres_cache[name] = data_part
                # Display-Breite aus dem img-Tag lesen (width-Attribut),
                # sonst 20 % der vollen Breite — Preview genau auf Display-Größe
                # skalieren, damit Qt keine Skalierung vornimmt → scharf
                w_attr = re.search(r'\bwidth="([\d.]+)"', full_tag)
                if w_attr:
                    disp_w = max(20, int(float(w_attr.group(1))))
                else:
                    disp_w = max(20, int(full_img.width() * 0.2))
                preview = full_img.scaledToWidth(disp_w, Qt.TransformationMode.SmoothTransformation)
                _pending[name] = preview
                return full_tag.replace(src_m.group(0), f'src="{name}"')
            except Exception:
                return full_tag

        html = re.sub(r'<img\b[^>]*src="data:image[^"]*"[^>]*>', extract_img_tag, content)
        # Explizite font-size entfernen, damit setDefaultFont (Zoom) greift
        html = re.sub(r'font-size\s*:\s*[\d.]+(?:pt|px)\s*;?\s*', '', html)
        self.setHtml(html)
        # Resources NACH setHtml setzen (setHtml löscht vorher gesetzte Resources)
        for _name, _preview in _pending.items():
            self.document().addResource(
                QTextDocument.ResourceType.ImageResource, QUrl(_name), _preview)
        if _pending:
            self.document().markContentsDirty(0, self.document().characterCount())
        # setHtml setzt das Dokument neu → Default-Font wiederherstellen
        self.document().setDefaultFont(self.font())
        self._apply_bottom_padding()


class _WheelZoomFilter(QObject):
    def __init__(self, window):
        super().__init__()
        self._win = window

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Type.Wheel and
                event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self._win._adjust_zoom(1 if event.angleDelta().y() > 0 else -1)
            return True
        return False


# ─────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────
class NotizenApp(QMainWindow):
    sync_status_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("\u2726 Notizen")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.resize(1100, 720)
        self.setMinimumSize(800, 500)

        self.config = load_config()
        self.notes_data = load_notes()
        if "folders" not in self.notes_data:
            self.notes_data["folders"] = []
        if "tasks" not in self.notes_data:
            self.notes_data["tasks"] = []
        if "deleted_task_ids" not in self.notes_data:
            self.notes_data["deleted_task_ids"] = []
        self.current_note_id = None
        self.open_tabs = []
        self.active_tab_id = None
        self._scroll_positions: dict = {}  # note_id → scroll-Y (nur In-Session)
        self.drive_sync = None
        self._sync_lock = threading.Lock()
        self._collapsed_folders = set(self.config.get("collapsed_folders", []))
        self._has_local_changes = False  # True nur wenn PC-User getippt hat
        self._editor_dirty = False        # True wenn Editor-Inhalt seit letztem Save geändert
        self._remote_merge_pending = False  # True waehrend remote merge → verhindert autosave

        self._drag_pos = None
        self._is_maximized = False
        self._normal_geo = None
        self._quick_switch_dlg = None

        # Zoom + UI-Font aus Config laden
        _ZOOM[0] = float(self.config.get("zoom", 1.0))
        _stored_font = self.config.get("ui_font", "Segoe UI")
        # Validieren: nur Fonts mit Latein-Unterstützung als UI-Font verwenden
        try:
            _db = QFontDatabase()
            if QFontDatabase.WritingSystem.Latin not in _db.writingSystems(_stored_font):
                _stored_font = "Segoe UI"
                self.config["ui_font"] = "Segoe UI"
                save_config(self.config)
        except Exception:
            _stored_font = "Segoe UI"
        _UI_FONT[0] = _stored_font

        self._apply_theme(self.config.get("theme", "dark"))
        self._build_ui()
        self.task_panel.load_tasks(
            self.notes_data["tasks"],
            lambda: save_notes(self.notes_data),
            self.notes_data["deleted_task_ids"]
        )

        # Zoom-Label initialisieren
        self.zoom_label.setText(f"{int(round(_ZOOM[0] * 100))}%")

        # Ctrl+Scroll auf der gesamten App abfangen
        self._zoom_filter = _WheelZoomFilter(self)
        QApplication.instance().installEventFilter(self._zoom_filter)
        self.sidebar._sort_mode = self.config.get("sort_mode", "id_asc")
        # Letzten Tab VOR _update_tabs lesen (sonst wird er durch _save_tab_state überschrieben)
        _last = self.config.get("last_active_tab")

        self._refresh_list()
        self._update_tabs()
        self._init_drive()

        # Restore last active tab
        _all = self._all_tabs()
        if _last and _last in _all:
            self._switch_to_tab(_last)
        elif _all:
            self._switch_to_tab(_all[0])

        # Auto-save alle 15s (Safety-Net für lange Tipp-Sessions)
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self._save_current)
        self.autosave_timer.start(15000)

        # Auto-sync every 30s fallback (upload)
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._auto_sync)
        self.sync_timer.start(30000)

        # Auto-download every 2s (pick up changes from other devices)
        # Bei Einweg-Sync: kein Download noetig (PC ist Master)
        self.download_timer = QTimer()
        self.download_timer.timeout.connect(self._periodic_download)
        if not _cfg.get("one_way_sync", False):
            self.download_timer.start(2000)

        # Debounce Wort-/Zeichenanzahl: nur nach Tipp-Pause aktualisieren
        self._wordcount_timer = QTimer()
        self._wordcount_timer.setSingleShot(True)
        self._wordcount_timer.timeout.connect(self._update_word_count)

        # Debounce Save: 5s nach letztem Tastendruck (Crash-Schutz)
        self._save_debounce = QTimer()
        self._save_debounce.setSingleShot(True)
        self._save_debounce.timeout.connect(self._save_current)

        self._search_debounce = QTimer()
        self._search_debounce.setSingleShot(True)
        self._search_debounce.timeout.connect(self._do_search)

        # Debounce upload: 3s after last change
        self._upload_debounce = QTimer()
        self._upload_debounce.setSingleShot(True)
        self._upload_debounce.timeout.connect(self._auto_sync)

        self.sync_status_signal.connect(self._update_sync_label)

        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._save_current)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._new_note)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(lambda: self.find_bar.open_bar())


    def _apply_theme(self, theme_name):
        global T
        T = THEMES.get(theme_name, THEMES["dark"])
        sheet = build_stylesheet()
        self.setStyleSheet(sheet)
        QApplication.instance().setStyleSheet(sheet)

    # ── UI BUILD ──────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Icon Rail
        self.icon_rail = IconRail()
        self.icon_rail.toggle_clicked.connect(self._toggle_sidebar)
        self.icon_rail.files_clicked.connect(self._show_files)
        self.icon_rail.quick_switch_clicked.connect(self._open_quick_switch)
        self.icon_rail.settings_clicked.connect(self._open_settings)
        self.icon_rail.sync_clicked.connect(self._manual_sync)
        self.icon_rail.tasks_clicked.connect(self._show_tasks)
        root.addWidget(self.icon_rail)

        # Sidebar
        self.sidebar = SidebarPanel()
        self.sidebar.search_input.textChanged.connect(self._on_search)
        self.sidebar.notes_list.itemClicked.connect(self._on_list_click)
        self.sidebar.notes_list.itemDoubleClicked.connect(self._on_list_double_click)
        self.sidebar.notes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sidebar.notes_list.customContextMenuRequested.connect(self._list_context_menu)
        self.sidebar.ai_search_toggle.toggled.connect(self._on_ai_search_toggle)
        self.sidebar.settings_requested.connect(self._open_settings)
        self.sidebar.sort_changed.connect(self._on_sort_changed)
        self.sidebar.new_note_clicked.connect(self._new_note)
        self.sidebar.new_folder_clicked.connect(self._new_folder)
        root.addWidget(self.sidebar)

        # Task Panel (in Slide-Clip gewrappt für reflow-freie Animation)
        self.task_panel = TaskPanel()
        self._task_clip = _SlideClip(self.task_panel)
        root.addWidget(self._task_clip)

        # Editor Area (tab bar + title + editor + status)
        editor_area = QWidget()
        editor_area.setStyleSheet(f"background: {T['bg']};")
        ea_layout = QVBoxLayout(editor_area)
        ea_layout.setContentsMargins(0, 0, 0, 0)
        ea_layout.setSpacing(0)

        # Tab Bar
        self.tab_bar = TabBar()
        self.tab_bar.tab_selected.connect(self._switch_to_tab)
        self.tab_bar.tab_closed.connect(self._close_tab)
        self.tab_bar.new_tab.connect(self._new_note)
        ea_layout.addWidget(self.tab_bar)

        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titel der Notiz...")
        self.title_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; border: none;
                border-bottom: 1px solid {T['border']}; border-radius: 0;
                font-size: {_sz(20)}px; font-weight: bold; color: {T['text']};
                padding: 14px 24px;
            }}
            QLineEdit:focus {{ border-bottom-color: {T['accent']}; }}
        """)
        self.title_input.textChanged.connect(self._on_title_changed)
        ea_layout.addWidget(self.title_input)

        self.date_label = QLabel("")
        self.date_label.setStyleSheet(f"color: {T['border']}; font-size: {_sz(9)}px; padding: 3px 26px;")
        ea_layout.addWidget(self.date_label)

        # Titel-Sichtbarkeit aus Config
        _show_title = self.config.get("show_title", True)
        self.title_input.setVisible(_show_title)
        self.date_label.setVisible(_show_title)

        # Editor
        self.text_editor = NoteTextEdit()
        self.text_editor.setPlaceholderText("")
        _ef   = self.config.get("editor_font", "Consolas")
        _efs  = max(6, int(round(self.config.get("editor_font_size", 14) * _ZOOM[0])))
        self.text_editor.setStyleSheet(f"""
            QTextEdit {{
                background: {T['bg']}; border: none; border-radius: 0;
                padding: 12px 24px; font-size: {_efs}px;
                font-family: '{_ef}'; color: {T['text']};
            }}
        """)
        self.text_editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.text_editor.customContextMenuRequested.connect(self._editor_context_menu)
        self.text_editor.textChanged.connect(self._on_text_changed)
        ea_layout.addWidget(self.text_editor)

        root.addWidget(editor_area)
        self.editor_area = editor_area

        # Find overlay (Ctrl+F) — floating over editor_area
        self.find_bar = FindOverlay(self.text_editor, editor_area)

        # Settings Overlay (backdrop over full window) — delete old one on rebuild
        if hasattr(self, 'settings_overlay') and self.settings_overlay is not None:
            self.settings_overlay.deleteLater()
            self.settings_overlay = None
        self.settings_overlay = SettingsOverlay(self, self.config)
        self.settings_overlay.closed.connect(lambda: None)
        self.settings_overlay.theme_changed.connect(self._on_theme_changed)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"background: {T['bg2']}; color: {T['muted']}; font-size: {_sz(12)}px; border-top: 1px solid {T['border']};")
        self.status_bar.setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Keine Notiz ausgewaehlt")
        # Size grip for frameless window resize
        self.zoom_label = QLabel(f"{int(round(_ZOOM[0] * 100))}%")
        self.zoom_label.setStyleSheet(
            f"color: {T['muted']}; font-size: {_sz(11)}px; padding: 0 8px;"
            " background: transparent; border: none;"
        )
        self.status_bar.addPermanentWidget(self.zoom_label)

        grip = QSizeGrip(self)
        grip.setStyleSheet("background: transparent;")
        grip.setFixedSize(16, 16)
        self.status_bar.addPermanentWidget(grip)

        # Highlight files by default
        self.icon_rail._highlight("files")
        # Sidebar-Zustand aus Config wiederherstellen
        _sidebar_exp = self.config.get("sidebar_expanded", True)
        if not _sidebar_exp:
            self.sidebar.setMaximumWidth(0)
            self.sidebar._expanded = False
        self.icon_rail.set_sidebar_expanded(_sidebar_exp)

    # ── SIDEBAR ──────────────────────────────
    def _toggle_sidebar(self):
        if self._task_clip.is_open():
            self._task_clip.animate_close()
            self.icon_rail._highlight("")
        self.sidebar.toggle()
        self.icon_rail.set_sidebar_expanded(self.sidebar._expanded)

    def _show_files(self):
        if self._task_clip.is_open():
            self._task_clip.animate_close()
        if self.sidebar._expanded:
            # bereits offen → schließen
            self.sidebar.toggle()
            self.icon_rail.set_sidebar_expanded(False)
            self.icon_rail._highlight("")
        else:
            self.sidebar.toggle()
            self.icon_rail.set_sidebar_expanded(True)
            self.sidebar.switch_tab("files")
            self.icon_rail._highlight("files")

    def _show_tasks(self):
        if self._task_clip.is_open():
            # bereits offen → rausslideen
            self.icon_rail._highlight("")
            self._task_clip.animate_close()
        else:
            if self.sidebar._expanded:
                self.sidebar.setMaximumWidth(0)
                self.sidebar._expanded = False
                self.icon_rail.set_sidebar_expanded(False)
            self._task_clip.animate_open(on_done=self.task_panel.scroll_to_current)
            self.icon_rail._highlight("tasks")

    def _open_quick_switch(self):
        notes = self.notes_data.get("notes", [])
        self._quick_switch_dlg = QuickSwitchDialog(self, notes)
        self._quick_switch_dlg.note_selected.connect(self._on_quick_switch_selected)
        self._quick_switch_dlg.exec()
        self._quick_switch_dlg = None

    def _on_quick_switch_selected(self, note_id):
        if note_id == "__new__":
            self._new_note()
        else:
            self._open_note_in_tab(note_id)

    def _on_search(self, text):
        if self.sidebar.ai_search_toggle.isChecked():
            return  # AI search uses enter key
        # Clear editor highlights when search is cleared
        if not text.strip():
            self.text_editor.setExtraSelections([])
        # Switch to search tab if user types in search field
        self.sidebar.switch_tab("search")
        self._search_debounce.start(150)

    def _do_search(self):
        self._refresh_list()

    def _on_sort_changed(self, mode):
        self.config["sort_mode"] = mode
        save_config(self.config)
        self._refresh_list()

    def _on_ai_search_toggle(self, checked):
        if checked:
            self.sidebar.search_input.setPlaceholderText("\u2728 KI-Suche... (Enter)")
            self.sidebar.search_input.returnPressed.connect(self._run_ai_search)
        else:
            self.sidebar.search_input.setPlaceholderText("\U0001F50D  Suchen...")
            try:
                self.sidebar.search_input.returnPressed.disconnect(self._run_ai_search)
            except TypeError:
                pass
            self.sidebar.ai_search_status.setVisible(False)
            self._refresh_list()

    def _run_ai_search(self):
        query = self.sidebar.search_input.text().strip()
        if not query:
            return
        self._last_ai_query = query
        self.sidebar.ai_search_status.setText("\u23F3 Suche laeuft...")
        self.sidebar.ai_search_status.setVisible(True)

        self._ai_search_worker = AISearchWorker(self.config, query, self.notes_data.get("notes", []))
        self._ai_search_worker.result_ready.connect(self._on_ai_search_result)
        self._ai_search_worker.error.connect(self._on_ai_search_error)
        self._ai_search_worker.start()

    def _on_ai_search_result(self, result):
        sources = result.get("sources", [])
        self.sidebar.ai_search_status.setText(f"\u2713 {len(sources)} Quellen")
        # Filter sidebar to show source notes
        source_ids = [s["id"] for s in sources if "id" in s]
        notes = self.notes_data.get("notes", [])
        self.sidebar.notes_list.clear()
        for sid in source_ids:
            note = next((n for n in notes if n["id"] == sid), None)
            if not note:
                continue
            item = QListWidgetItem()
            widget = NoteItem(note, is_active=(note["id"] == self.current_note_id))
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, note["id"])
            self.sidebar.notes_list.addItem(item)
            self.sidebar.notes_list.setItemWidget(item, widget)
        # Open answer dialog
        dlg = AIAnswerDialog(self, getattr(self, "_last_ai_query", ""), result, notes)
        dlg.open_note.connect(self._open_note_in_tab)
        dlg.exec()

    def _on_ai_search_error(self, err):
        self.sidebar.ai_search_status.setText(f"Fehler: {err[:50]}")

    # ── NOTES ─────────────────────────────────
    def _apply_sort(self, notes):
        mode = self.sidebar._sort_mode
        if mode == "name_asc":
            return sorted(notes, key=lambda n: (n.get("title") or "").lower())
        elif mode == "name_desc":
            return sorted(notes, key=lambda n: (n.get("title") or "").lower(), reverse=True)
        elif mode == "modified_desc":
            return sorted(notes, key=lambda n: n.get("modified", ""), reverse=True)
        elif mode == "modified_asc":
            return sorted(notes, key=lambda n: n.get("modified", ""))
        elif mode == "id_desc":
            return sorted(notes, key=lambda n: n.get("id", ""), reverse=True)
        else:  # id_asc default
            return sorted(notes, key=lambda n: n.get("id", ""))

    def _update_sidebar_active(self):
        """Nur Active-Highlight in der Sidebar aktualisieren (O(n) Styles, kein Widget-Rebuild)."""
        nlist = self.sidebar.notes_list
        for i in range(nlist.count()):
            item = nlist.item(i)
            w = nlist.itemWidget(item)
            if w and hasattr(w, 'set_active'):
                nid = item.data(Qt.ItemDataRole.UserRole)
                w.set_active(nid == self.current_note_id)

    def _refresh_list(self):
        nlist = self.sidebar.notes_list
        _scroll = nlist.verticalScrollBar().value()
        nlist.clear()
        query = self.sidebar.search_input.text().strip()
        query_lower = query.lower()
        all_notes = self.notes_data.get("notes", [])
        is_search_tab = self.sidebar.btn_search_tab.isChecked()

        # ── Search tab: flat highlighted list ──
        if is_search_tab and query:
            notes = [n for n in all_notes if
                     query_lower in n.get("title", "").lower() or
                     query_lower in n.get("content", "").lower()]
            notes = self._apply_sort(notes)
            count = len(notes)
            self.sidebar.result_count_lbl.setText(f"{count} Ergebnis{'se' if count != 1 else ''}")
            self.sidebar.result_count_lbl.setVisible(count > 0)
            for note in notes:
                item = QListWidgetItem()
                widget = SearchResultItem(note, query)
                content = note.get("content", "")
                has_preview = bool(query_lower in content.lower())
                item_height = 42 + (72 if has_preview else 0)
                item.setSizeHint(QSize(0, item_height))
                item.setData(Qt.ItemDataRole.UserRole, note["id"])
                item.setData(Qt.ItemDataRole.UserRole + 1, "note")
                nlist.addItem(item)
                nlist.setItemWidget(item, widget)
            return

        # ── Files tab: folders + root notes ──
        self.sidebar.result_count_lbl.setVisible(False)

        if query_lower:
            all_notes = [n for n in all_notes if
                         query_lower in n.get("title", "").lower() or
                         query_lower in n.get("content", "").lower()]

        folders = self.notes_data.get("folders", [])
        # All note IDs that belong to any folder
        folder_note_ids = set()
        for f in folders:
            folder_note_ids.update(f.get("note_ids", []))

        note_map = {n["id"]: n for n in all_notes}

        def add_note_item(note, folder_child=False):
            item = QListWidgetItem()
            widget = NoteItem(note, is_active=(note["id"] == self.current_note_id),
                              folder_child=folder_child)
            item.setSizeHint(QSize(0, 32))
            item.setData(Qt.ItemDataRole.UserRole, note["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, "note")
            nlist.addItem(item)
            nlist.setItemWidget(item, widget)

        # Folders sorted oldest→newest (always)
        for folder in sorted(folders, key=lambda f: f.get("id", "")):
            folder_id = folder["id"]
            collapsed = folder_id in self._collapsed_folders

            f_item = QListWidgetItem()
            f_widget = FolderItem(folder, collapsed=collapsed)
            f_item.setSizeHint(QSize(0, 32))
            f_item.setData(Qt.ItemDataRole.UserRole, folder_id)
            f_item.setData(Qt.ItemDataRole.UserRole + 1, "folder")
            f_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # not selectable
            nlist.addItem(f_item)
            nlist.setItemWidget(f_item, f_widget)

            if not collapsed:
                child_notes = [note_map[nid] for nid in folder.get("note_ids", [])
                               if nid in note_map]
                sorted_children = self._apply_sort(child_notes)
                for note in sorted_children:
                    add_note_item(note, folder_child=True)
                if sorted_children:
                    self._add_folder_separator(nlist)

        # Root notes (not in any folder)
        root_notes = [n for n in all_notes if n["id"] not in folder_note_ids]
        for note in self._apply_sort(root_notes):
            add_note_item(note, folder_child=False)

        # Restore anchor to active note so Shift+Click works correctly after rebuild
        if self.current_note_id:
            for row in range(nlist.count()):
                it = nlist.item(row)
                if (it.data(Qt.ItemDataRole.UserRole) == self.current_note_id and
                        it.data(Qt.ItemDataRole.UserRole + 1) == "note"):
                    nlist.setCurrentRow(row)
                    break
        # Restore scroll position — prevent auto-jump to active note
        nlist.verticalScrollBar().setValue(_scroll)

    def _on_list_click(self, item):
        item_type = item.data(Qt.ItemDataRole.UserRole + 1)
        uid = item.data(Qt.ItemDataRole.UserRole)

        if item_type == "folder":
            # Stop any running folder animation
            if hasattr(self, '_folder_anim_timer') and self._folder_anim_timer.isActive():
                self._folder_anim_timer.stop()
                # Finish pending collapse cleanly
                if hasattr(self, '_folder_anim_pending'):
                    fid, _ = self._folder_anim_pending
                    self._collapsed_folders.add(fid)
                    del self._folder_anim_pending
                    self._refresh_list()
            self._toggle_folder_animated(uid)
            return

        # With Shift or Ctrl: only change selection, don't open note
        mods = QApplication.keyboardModifiers()
        if mods & (Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier):
            return

        # Already active → do nothing (prevents rebuild on first click of double-click)
        if uid == self.current_note_id:
            return

        self._open_note_in_tab(uid)
        if self.sidebar.btn_search_tab.isChecked():
            query = self.sidebar.search_input.text().strip()
            if query:
                QTimer.singleShot(60, lambda q=query: self._highlight_in_editor(q))

    def _add_folder_separator(self, nlist, insert_at=None, opacity=1.0):
        """Add a thin separator line after a folder's children."""
        sep = QWidget()
        sep.setFixedHeight(5)
        sep.setStyleSheet("background: transparent;")
        sep_lay = QHBoxLayout(sep)
        sep_lay.setContentsMargins(20, 2, 10, 2)
        sep_lay.setSpacing(0)
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {T['border']};")
        sep_lay.addWidget(line)
        sep.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        sep_item = QListWidgetItem()
        sep_item.setSizeHint(QSize(0, 5))
        sep_item.setData(Qt.ItemDataRole.UserRole, "")
        sep_item.setData(Qt.ItemDataRole.UserRole + 1, "separator")
        sep_item.setFlags(Qt.ItemFlag.NoItemFlags)
        if insert_at is not None:
            nlist.insertItem(insert_at, sep_item)
        else:
            nlist.addItem(sep_item)
        nlist.setItemWidget(sep_item, sep)
        if opacity < 1.0:
            eff = QGraphicsOpacityEffect(sep)
            eff.setOpacity(opacity)
            sep.setGraphicsEffect(eff)
        return sep_item, sep

    def _toggle_folder_animated(self, folder_id):
        nlist = self.sidebar.notes_list
        expanding = folder_id in self._collapsed_folders

        # Find folder row
        folder_row = -1
        for row in range(nlist.count()):
            it = nlist.item(row)
            if (it.data(Qt.ItemDataRole.UserRole) == folder_id and
                    it.data(Qt.ItemDataRole.UserRole + 1) == "folder"):
                folder_row = row
                break
        if folder_row < 0:
            return

        # Update chevron immediately
        fw = nlist.itemWidget(nlist.item(folder_row))
        if fw:
            for lbl in fw.findChildren(QLabel):
                if lbl.text() in ("\u25B6", "\u25BC"):
                    lbl.setText("\u25BC" if expanding else "\u25B6")
                    break

        if expanding:
            # ── EXPAND: insert child items one by one ──
            self._collapsed_folders.discard(folder_id)
            folders = self.notes_data.get("folders", [])
            folder = next((f for f in folders if f["id"] == folder_id), None)
            if not folder:
                return
            note_map = {n["id"]: n for n in self.notes_data.get("notes", [])}
            child_notes = [note_map[nid] for nid in folder.get("note_ids", [])
                           if nid in note_map]
            child_notes = self._apply_sort(child_notes)
            if not child_notes:
                return
            # Pre-create all items (hidden) + separator at end
            new_items = []
            for i, note in enumerate(child_notes):
                item = QListWidgetItem()
                widget = NoteItem(note, is_active=(note["id"] == self.current_note_id),
                                  folder_child=True)
                item.setSizeHint(QSize(0, 32))
                item.setData(Qt.ItemDataRole.UserRole, note["id"])
                item.setData(Qt.ItemDataRole.UserRole + 1, "note")
                insert_row = folder_row + 1 + i
                nlist.insertItem(insert_row, item)
                nlist.setItemWidget(item, widget)
                item.setHidden(True)
                new_items.append(item)
            # Add separator (hidden, fades in at the end)
            sep_row = folder_row + 1 + len(child_notes)
            sep_item, sep_widget = self._add_folder_separator(nlist, insert_at=sep_row, opacity=0.0)
            sep_item.setHidden(True)
            idx = [0]
            delay = max(8, 120 // len(new_items))
            def show_next():
                if idx[0] < len(new_items):
                    new_items[idx[0]].setHidden(False)
                    idx[0] += 1
                else:
                    timer.stop()
                    # Fade in separator
                    sep_item.setHidden(False)
                    eff = sep_widget.graphicsEffect()
                    if eff:
                        self._sep_fade = QPropertyAnimation(eff, b"opacity")
                        self._sep_fade.setDuration(150)
                        self._sep_fade.setStartValue(0.0)
                        self._sep_fade.setEndValue(1.0)
                        self._sep_fade.start()
            timer = QTimer(self)
            timer.setInterval(delay)
            timer.timeout.connect(show_next)
            self._folder_anim_timer = timer
            timer.start()
        else:
            # ── COLLAPSE: remove folder's note items + separator ──
            folders = self.notes_data.get("folders", [])
            folder = next((f for f in folders if f["id"] == folder_id), None)
            folder_note_ids = set(folder.get("note_ids", [])) if folder else set()
            child_rows = []
            sep_row = None
            for row in range(folder_row + 1, nlist.count()):
                it = nlist.item(row)
                itype = it.data(Qt.ItemDataRole.UserRole + 1)
                if itype == "folder":
                    break
                if itype == "separator":
                    sep_row = row
                    break  # separator is always last
                if it.data(Qt.ItemDataRole.UserRole) in folder_note_ids:
                    child_rows.append(row)
            if not child_rows:
                # Remove separator if present
                if sep_row is not None:
                    nlist.takeItem(sep_row)
                self._collapsed_folders.add(folder_id)
                return
            # Fade out separator first, then remove notes
            all_remove_rows = list(child_rows)
            if sep_row is not None:
                all_remove_rows.append(sep_row)
            self._folder_anim_pending = (folder_id, list(all_remove_rows))
            # Start by fading separator, then cascade-remove notes
            rows_rev = list(reversed(child_rows))
            if sep_row is not None:
                rows_rev = [sep_row] + rows_rev  # separator first
            idx = [0]
            delay = max(8, 120 // max(len(rows_rev), 1))
            def remove_next():
                if idx[0] < len(rows_rev):
                    nlist.takeItem(rows_rev[idx[0]])
                    # Adjust remaining indices after removal
                    removed = rows_rev[idx[0]]
                    for j in range(idx[0] + 1, len(rows_rev)):
                        if rows_rev[j] > removed:
                            rows_rev[j] -= 1
                    idx[0] += 1
                else:
                    timer.stop()
                    self._collapsed_folders.add(folder_id)
                    if hasattr(self, '_folder_anim_pending'):
                        del self._folder_anim_pending
            timer = QTimer(self)
            timer.setInterval(delay)
            timer.timeout.connect(remove_next)
            self._folder_anim_timer = timer
            timer.start()

    def _on_list_double_click(self, item):
        # Ignore during folder animation
        if hasattr(self, '_folder_anim_timer') and self._folder_anim_timer.isActive():
            return
        # Ignore double-click when Shift or Ctrl are held (selection mode)
        mods = QApplication.keyboardModifiers()
        if mods & (Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier):
            return
        item_type = item.data(Qt.ItemDataRole.UserRole + 1)
        uid = item.data(Qt.ItemDataRole.UserRole)
        if item_type == "note":
            self._rename_note(uid)
        elif item_type == "folder":
            self._rename_folder(uid)

    def _rename_note(self, note_id):
        note = self._get_note(note_id)
        if not note:
            return
        self.activateWindow()
        self.raise_()
        current_title = note.get("title", "")
        name, ok = QInputDialog.getText(self, "Notiz umbenennen", "Neuer Name:", text=current_title)
        if ok and name.strip():
            note["title"] = name.strip()
            note["modified"] = datetime.now().isoformat()
            save_notes(self.notes_data)
            # Update title input if this note is currently open
            if note_id == self.current_note_id:
                self.title_input.blockSignals(True)
                self.title_input.setText(name.strip())
                self.title_input.blockSignals(False)
            self._update_tabs()
            self._refresh_list()

    def _highlight_in_editor(self, query):
        """Highlight all occurrences of query in the editor and scroll to first."""
        doc = self.text_editor.document()
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(255, 200, 0, 150))
        selections = []
        cursor = QTextCursor(doc)
        while True:
            cursor = doc.find(query, cursor)
            if cursor.isNull():
                break
            sel = QTextEdit.ExtraSelection()
            sel.format = fmt
            sel.cursor = QTextCursor(cursor)
            selections.append(sel)
        self.text_editor.setExtraSelections(selections)
        if selections:
            self.text_editor.setTextCursor(selections[0].cursor)
            self.text_editor.ensureCursorVisible()

    def _open_note_in_tab(self, note_id):
        self._switch_to_tab(note_id)

    def _switch_to_tab(self, note_id):
        # Scroll-Position der aktuellen Seite speichern (In-Session)
        if self.current_note_id:
            self._scroll_positions[self.current_note_id] = \
                self.text_editor.verticalScrollBar().value()

        self._switching_tab = True
        self._save_current()
        self._switching_tab = False
        self.current_note_id = note_id
        self.active_tab_id = note_id
        self.text_editor.setExtraSelections([])  # clear highlights
        note = self._get_note(note_id)
        if note:
            self.title_input.blockSignals(True)
            self.text_editor.blockSignals(True)
            self.title_input.setText(note.get("title", ""))
            self.text_editor.setRichText(note.get("content", ""))
            self.title_input.blockSignals(False)
            self.text_editor.blockSignals(False)
            # Cursor an den Anfang (verhindert "toter Editor")
            cursor = self.text_editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.text_editor.setTextCursor(cursor)
            # Scroll-Position wiederherstellen (falls diese Session schon besucht)
            saved_scroll = self._scroll_positions.get(note_id, 0)
            if saved_scroll:
                QTimer.singleShot(0, lambda v=saved_scroll:
                    self.text_editor.verticalScrollBar().setValue(v))
            mod = note.get("modified", "")[:16].replace("T", "  ")
            self.date_label.setText(f"Zuletzt bearbeitet: {mod}")
            self.status_bar.showMessage(f"  {note.get('title', 'Unbenannte Notiz')}")
        self._update_tabs()
        self._update_sidebar_active()
        # Hide settings overlay when switching tabs
        self.settings_overlay.setVisible(False)

    def _close_tab(self, note_id):
        """Wird beim Löschen einer Notiz aufgerufen. Wechselt zum nächsten Tab."""
        if self.active_tab_id == note_id:
            # note_id wurde bereits aus notes_data entfernt; _all_tabs gibt Restliste
            remaining = self._all_tabs()
            if remaining:
                self._switch_to_tab(remaining[-1])
            else:
                self.current_note_id = None
                self.active_tab_id = None
                self.title_input.clear()
                self.text_editor.clear()
                self.date_label.setText("")
                self.status_bar.showMessage("Keine Notiz ausgewaehlt")
        self._update_tabs()

    def _close_active_tab(self):
        if self.active_tab_id:
            self._close_tab(self.active_tab_id)

    def _all_tabs(self):
        """Alle Notizen als Tabs, sortiert nach Erstellzeit (ID = Timestamp, älteste zuerst)."""
        return sorted([n["id"] for n in self.notes_data.get("notes", [])], key=lambda x: x)

    def _update_tabs(self):
        self.open_tabs = self._all_tabs()
        self.tab_bar.update_tabs(self.open_tabs, self.active_tab_id, self.notes_data)
        self._save_tab_state()

    def _save_tab_state(self):
        self.config["last_active_tab"] = self.active_tab_id
        save_config(self.config)

    def _get_note(self, note_id):
        return next((n for n in self.notes_data["notes"] if n["id"] == note_id), None)

    def _new_note(self):
        self._save_current()
        note_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        note = {"id": note_id, "title": "", "content": "", "modified": datetime.now().isoformat()}
        self.notes_data["notes"].append(note)
        save_notes(self.notes_data)
        self._open_note_in_tab(note_id)
        # Fokus + Cursor explizit setzen, damit der Editor sofort schreibbereit ist
        self.text_editor.setFocus()
        cursor = self.text_editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.text_editor.setTextCursor(cursor)
        # Sync: neue Notiz sofort hochladen
        self._has_local_changes = True
        if self.drive_sync and self.drive_sync.is_connected():
            self._upload_debounce.start(3000)

    def _delete_note(self, note_id):
        reply = QMessageBox.question(self, "Loeschen", "Diese Notiz wirklich loeschen?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._add_tombstone(note_id)
            self.notes_data["notes"] = [n for n in self.notes_data["notes"] if n["id"] != note_id]
            self._remove_note_from_all_folders(note_id)
            self._close_tab(note_id)
            if self.current_note_id == note_id:
                self.current_note_id = None
                self.title_input.clear()
                self.text_editor.clear()
                self.date_label.setText("")
                self.status_bar.showMessage("Keine Notiz ausgewaehlt")
            save_notes(self.notes_data)
            self._refresh_list()
            self._sync_after_delete()

    def _delete_selected_notes(self, note_ids):
        count = len(note_ids)
        reply = QMessageBox.question(
            self, "L\u00f6schen",
            f"{count} Notiz{'en' if count > 1 else ''} wirklich l\u00f6schen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        deleted_set = set(note_ids)
        for note_id in note_ids:
            self._add_tombstone(note_id)
            self.notes_data["notes"] = [n for n in self.notes_data["notes"] if n["id"] != note_id]
            self._remove_note_from_all_folders(note_id)
        save_notes(self.notes_data)
        remaining = self._all_tabs()
        if self.active_tab_id in deleted_set:
            if remaining:
                self._switch_to_tab(remaining[-1])
            else:
                self.active_tab_id = None
                self.current_note_id = None
                self.title_input.clear()
                self.text_editor.clear()
                self.date_label.setText("")
                self.status_bar.showMessage("Keine Notiz ausgew\u00e4hlt")
        self._update_tabs()
        self._refresh_list()
        self._sync_after_delete()

    def _add_tombstone(self, note_id):
        """Notiz als gelöscht markieren (Tombstone)."""
        deleted = self.notes_data.setdefault("deleted_ids", [])
        if note_id not in deleted:
            deleted.append(note_id)

    def _add_folder_tombstone(self, folder_id):
        """Ordner als gelöscht markieren (Tombstone)."""
        deleted = self.notes_data.setdefault("deleted_folder_ids", [])
        if folder_id not in deleted:
            deleted.append(folder_id)

    def _sync_after_delete(self):
        """Sofort nach Löschung uploaden — Download-Timer kurz pausieren damit die Notiz nicht wiederhergestellt wird."""
        if not self.drive_sync:
            return
        self.download_timer.stop()
        self._has_local_changes = True
        threading.Thread(target=self._upload_to_drive, daemon=True).start()
        # Download-Timer nach 5s wieder starten
        QTimer.singleShot(5000, lambda: self.download_timer.start(2000))

    def _remove_note_from_all_folders(self, note_id):
        for folder in self.notes_data.get("folders", []):
            if note_id in folder.get("note_ids", []):
                folder["note_ids"].remove(note_id)
                folder["modified"] = datetime.now().isoformat()

    def _new_folder(self):
        name, ok = QInputDialog.getText(self, "Neuer Ordner", "Ordnername:", text="Neuer Ordner")
        if not ok or not name.strip():
            return
        folder_id = "folder_" + datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.notes_data["folders"].append({"id": folder_id, "name": name.strip(), "note_ids": [], "modified": datetime.now().isoformat()})
        save_notes(self.notes_data)
        self._refresh_list()
        self._has_local_changes = True
        if self.drive_sync and self.drive_sync.is_connected():
            threading.Thread(target=self._upload_to_drive, daemon=True).start()

    def _rename_folder(self, folder_id):
        folder = next((f for f in self.notes_data.get("folders", []) if f["id"] == folder_id), None)
        if not folder:
            return
        name, ok = QInputDialog.getText(self, "Umbenennen", "Neuer Name:", text=folder["name"])
        if ok and name.strip():
            folder["name"] = name.strip()
            save_notes(self.notes_data)
            self._refresh_list()

    def _delete_folder(self, folder_id):
        reply = QMessageBox.question(
            self, "Ordner l\u00f6schen",
            "Ordner l\u00f6schen? Die enthaltenen Notizen bleiben erhalten.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._add_folder_tombstone(folder_id)
        self.notes_data["folders"] = [
            f for f in self.notes_data.get("folders", []) if f["id"] != folder_id]
        self._collapsed_folders.discard(folder_id)
        save_notes(self.notes_data)
        self._refresh_list()
        self._sync_after_delete()

    def _move_to_folder(self, note_ids, folder_id):
        for note_id in note_ids:
            # Aus alten Ordnern entfernen + modified setzen
            for f in self.notes_data.get("folders", []):
                if note_id in f.get("note_ids", []):
                    f["note_ids"].remove(note_id)
                    f["modified"] = datetime.now().isoformat()
            if folder_id is not None:
                for folder in self.notes_data.get("folders", []):
                    if folder["id"] == folder_id:
                        if note_id not in folder.get("note_ids", []):
                            folder.setdefault("note_ids", []).append(note_id)
                            folder["modified"] = datetime.now().isoformat()
        save_notes(self.notes_data)
        self._has_local_changes = True
        self._refresh_list()
        if self.drive_sync and self.drive_sync.is_connected():
            threading.Thread(target=self._upload_to_drive, daemon=True).start()

    def _save_current(self):
        if not self.current_note_id:
            return
        # Waehrend ein Remote-Merge auf Editor-Update wartet, NICHT speichern
        # (sonst wuerde der alte Editor-Inhalt den gemergten Inhalt ueberschreiben)
        if self._remote_merge_pending:
            return
        # Nichts geändert → toRichText() + save_notes() überspringen (Performance)
        if not self._editor_dirty:
            return
        self._editor_dirty = False
        note = self._get_note(self.current_note_id)
        if note:
            new_title = self.title_input.text().strip()
            new_content = self.text_editor.toRichText()
            if note.get("title") != new_title or note.get("content") != new_content:
                title_changed = note.get("title") != new_title
                note["title"] = new_title or "Unbenannte Notiz"
                note["content"] = new_content
                note["modified"] = datetime.now().isoformat()
                save_notes(self.notes_data)
                # Tabs/Liste nur bei Titeländerung neu aufbauen (70 Widgets = teuer)
                if title_changed and not getattr(self, '_switching_tab', False):
                    self._update_tabs()
                    self._refresh_list()

    def _on_title_changed(self):
        self._editor_dirty = True
        self._save_current()
        self._has_local_changes = True
        if self.drive_sync and self.drive_sync.is_connected():
            self._upload_debounce.start(3000)

    def _on_text_changed(self):
        self._editor_dirty = True
        # Wort-/Zeichenzahl debounced (toPlainText ist O(n) → nicht auf jeden Tastendruck)
        self._wordcount_timer.start(500)
        # Save 5s nach letztem Tastendruck (Crash-Schutz, unabhängig von Drive)
        self._save_debounce.start(5000)
        self._has_local_changes = True
        if self.drive_sync and self.drive_sync.is_connected():
            self._upload_debounce.start(3000)

    def _update_word_count(self):
        content = self.text_editor.toPlainText()
        words = len(content.split()) if content.strip() else 0
        chars = len(content)
        self.status_bar.showMessage(f"  {words} Woerter  \u00B7  {chars} Zeichen")

    # ── CONTEXT MENUS ─────────────────────────
    def _get_image_name_at(self, pos) -> str:
        """Gibt den Ressourcenamen des Bildes an der Rechtsklick-Position zurück."""
        for cur in [
            self.text_editor.cursorForPosition(pos),
            self.text_editor.textCursor(),
        ]:
            # Bild links vom Cursor
            f = cur.charFormat().toImageFormat()
            if f.isValid() and f.name():
                return f.name()
            # Bild rechts vom Cursor
            right = QTextCursor(cur)
            right.movePosition(QTextCursor.MoveOperation.Right)
            f = right.charFormat().toImageFormat()
            if f.isValid() and f.name():
                return f.name()
        return ""

    def _show_image_fullscreen(self, name: str):
        img = QImage()
        import base64 as _b64
        # Volle Auflösung bevorzugen (nur in-session verfügbar)
        fullres = self.text_editor._img_fullres_cache
        preview = self.text_editor._img_b64_cache
        src = fullres.get(name) or preview.get(name)
        if src:
            raw = _b64.b64decode(src)
            img.loadFromData(QByteArray(bytes(raw)))
        if img.isNull():
            res = self.text_editor.document().resource(
                QTextDocument.ResourceType.ImageResource, QUrl(name)) if name else None
            if isinstance(res, QImage):
                img = res
        if img.isNull():
            return

        from PyQt6.QtGui import QPixmap
        _pix = QPixmap.fromImage(img)

        viewer = QDialog(self)
        viewer.setWindowTitle("Vollbild – ESC zum Schließen")
        viewer.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint
        )
        viewer.setStyleSheet("background: #111;")

        lbl = QLabel(viewer)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("background: #111;")

        layout = QVBoxLayout(viewer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(lbl)

        def _viewer_key(e):
            e.accept()
            if e.key() == Qt.Key.Key_Escape:
                viewer.reject()
        viewer.keyPressEvent = _viewer_key

        def _set_pix():
            ratio = viewer.devicePixelRatio()
            w = max(int((viewer.width()  - 40) * ratio), 100)
            h = max(int((viewer.height() - 40) * ratio), 100)
            scaled = _pix.scaled(w, h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            scaled.setDevicePixelRatio(ratio)
            lbl.setPixmap(scaled)

        viewer.setGeometry(self.geometry())
        viewer.show()
        QTimer.singleShot(50, _set_pix)
        viewer.exec()

    def _editor_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {T['bg2']}; border: 1px solid {T['border']};
                    border-radius: 6px; padding: 4px; color: {T['text']}; font-size: {_sz(13)}px; }}
            QMenu::item {{ padding: 6px 16px; border-radius: 4px; }}
            QMenu::item:selected {{ background: rgba(255,255,255,0.08); }}
            QMenu::separator {{ height: 1px; background: {T['border']}; margin: 3px 8px; }}
        """)
        # Bild-Menü wenn Cursor auf einem Bild steht
        if self.text_editor.is_cursor_on_image():
            bigger = QAction("🔍  Bild größer  (+50 %)", self)
            bigger.triggered.connect(lambda: self.text_editor.resize_image_at_cursor(1.5))
            smaller = QAction("🔎  Bild kleiner  (−33 %)", self)
            smaller.triggered.connect(lambda: self.text_editor.resize_image_at_cursor(0.67))
            orig = QAction("⟳  Originalgröße  (100 %)", self)
            orig.triggered.connect(lambda: self.text_editor.resize_image_at_cursor(1.0 / (
                self.text_editor.textCursor().charFormat().toImageFormat().width() /
                max(1, self.text_editor.document().resource(
                    QTextDocument.ResourceType.ImageResource,
                    QUrl(self.text_editor.textCursor().charFormat().toImageFormat().name())
                ).width() if isinstance(self.text_editor.document().resource(
                    QTextDocument.ResourceType.ImageResource,
                    QUrl(self.text_editor.textCursor().charFormat().toImageFormat().name())
                ), QImage) else 1)
            )))
            # Bildnamen via cursorForPosition(pos) holen — zuverlässigste Methode
            _img_name = self._get_image_name_at(pos)
            fullscreen = QAction("⛶  In Vollbild anzeigen", self)
            fullscreen.triggered.connect(lambda: self._show_image_fullscreen(_img_name))
            menu.addAction(bigger)
            menu.addAction(smaller)
            menu.addAction(orig)
            menu.addSeparator()
            menu.addAction(fullscreen)
            menu.addSeparator()
        ai_action = QAction("\u2726  KI-Aktion...", self)
        ai_action.triggered.connect(self._open_ai_dialog)
        menu.addAction(ai_action)
        cb_action = QAction("\U0001f4cb  Copy Block einf\u00fcgen", self)
        cb_action.triggered.connect(self.text_editor.insertCopyBlock)
        menu.addAction(cb_action)
        hr_action = QAction("\u2015  Horizontale Linie einf\u00fcgen", self)
        hr_action.triggered.connect(self.text_editor.insertHorizontalLine)
        menu.addAction(hr_action)
        menu.addSeparator()
        menu.addAction(QAction("Ausschneiden", self, triggered=self.text_editor.cut))
        menu.addAction(QAction("Kopieren", self, triggered=self.text_editor.copy))
        menu.addAction(QAction("Einfuegen", self, triggered=self.text_editor.paste))
        menu.exec(self.text_editor.mapToGlobal(pos))

    def _list_context_menu(self, pos):
        item = self.sidebar.notes_list.itemAt(pos)
        if not item:
            return

        _menu_style = f"""
            QMenu {{ background: {T['bg2']}; border: 1px solid {T['border']};
                    border-radius: 6px; padding: 4px; color: {T['text']}; font-size: {_sz(13)}px; }}
            QMenu::item {{ padding: 6px 20px; border-radius: 4px; }}
            QMenu::item:selected {{ background: rgba(255,255,255,0.08); }}
            QMenu::separator {{ height: 1px; background: {T['border']}; margin: 3px 8px; }}
        """

        item_type = item.data(Qt.ItemDataRole.UserRole + 1)
        uid = item.data(Qt.ItemDataRole.UserRole)

        # ── Folder context menu ──
        if item_type == "folder":
            menu = QMenu(self)
            menu.setStyleSheet(_menu_style)
            rename_a = QAction("Umbenennen", self)
            rename_a.triggered.connect(lambda: self._rename_folder(uid))
            menu.addAction(rename_a)
            menu.addSeparator()
            del_a = QAction("Ordner l\u00f6schen (Notizen bleiben)", self)
            del_a.triggered.connect(lambda: self._delete_folder(uid))
            menu.addAction(del_a)
            menu.exec(self.sidebar.notes_list.mapToGlobal(pos))
            return

        # ── Note context menu (multi-select aware) ──
        selected_items = self.sidebar.notes_list.selectedItems()
        selected_note_ids = [
            i.data(Qt.ItemDataRole.UserRole)
            for i in selected_items
            if i.data(Qt.ItemDataRole.UserRole + 1) == "note"
        ]
        # If right-clicked item not in selection, treat as single
        if uid not in selected_note_ids:
            selected_note_ids = [uid]

        menu = QMenu(self)
        menu.setStyleSheet(_menu_style)
        count = len(selected_note_ids)

        folders = self.notes_data.get("folders", [])
        if folders:
            move_menu = QMenu(f"In Ordner verschieben", self)
            move_menu.setStyleSheet(_menu_style)
            for folder in sorted(folders, key=lambda f: f.get("id", "")):
                fid = folder["id"]
                fa = QAction(folder["name"], self)
                fa.triggered.connect(
                    lambda _, ids=selected_note_ids, fid=fid: self._move_to_folder(ids, fid))
                move_menu.addAction(fa)
            move_menu.addSeparator()
            remove_a = QAction("Aus Ordner entfernen", self)
            remove_a.triggered.connect(
                lambda: self._move_to_folder(selected_note_ids, None))
            move_menu.addAction(remove_a)
            menu.addMenu(move_menu)
            menu.addSeparator()

        if count == 1:
            rename_a = QAction("Umbenennen", self)
            rename_a.triggered.connect(lambda: self._rename_note(selected_note_ids[0]))
            menu.addAction(rename_a)
            menu.addSeparator()

        del_label = f"{count} Notiz{'en' if count > 1 else ''} l\u00f6schen"
        del_a = QAction(del_label, self)
        del_a.triggered.connect(lambda: self._delete_selected_notes(selected_note_ids))
        menu.addAction(del_a)
        menu.exec(self.sidebar.notes_list.mapToGlobal(pos))

    # ── AI ────────────────────────────────────
    def _open_ai_dialog(self):
        cursor = self.text_editor.textCursor()
        selected = cursor.selectedText()
        if not selected.strip():
            selected = self.text_editor.toPlainText()
        if not selected.strip():
            QMessageBox.information(self, "Hinweis", "Bitte markiere zuerst einen Text.")
            return

        dlg = AIDialog(self, selected, self.config)
        dlg.exec()

        if dlg.action == "replace" and dlg.result_text:
            cursor = self.text_editor.textCursor()
            if cursor.hasSelection():
                cursor.insertText(dlg.result_text)
            else:
                self.text_editor.setPlainText(dlg.result_text)

    # ── SETTINGS ──────────────────────────────
    def _open_settings(self):
        self.settings_overlay.config = self.config
        # Cover full window (including status bar)
        self.settings_overlay.setGeometry(self.rect())
        # Grab current content BEFORE showing overlay
        self.settings_overlay.set_backdrop(self.grab())
        self.settings_overlay.show_overlay()
        self.settings_overlay.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.settings_overlay.isVisible():
            self.settings_overlay.setGeometry(self.rect())

    def _apply_dwm_shadow(self):
        """DWM-Schatten für rahmenloses Fenster aktivieren (Windows only)."""
        try:
            import ctypes
            class MARGINS(ctypes.Structure):
                _fields_ = [("cxLeftWidth", ctypes.c_int), ("cxRightWidth", ctypes.c_int),
                             ("cyTopHeight", ctypes.c_int), ("cyBottomHeight", ctypes.c_int)]
            hwnd = int(self.winId())
            # NC-Rendering explizit aktivieren
            DWMWA_NCRENDERING_POLICY = 2
            DWMNCRP_ENABLED = 2
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_NCRENDERING_POLICY,
                ctypes.byref(ctypes.c_int(DWMNCRP_ENABLED)),
                ctypes.sizeof(ctypes.c_int)
            )
            # Rahmen 1px in Client-Area verlängern → aktiviert DWM-Schatten
            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(MARGINS(1, 1, 1, 1)))
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._apply_dwm_shadow)
        if not getattr(self, '_shown_once', False):
            self._shown_once = True
            # Gespeicherte Größe als Animations-Ziel setzen
            _wg = self.config.get("window_geo")
            if _wg and len(_wg) == 4:
                self._saved_geo = QRect(int(_wg[0]), int(_wg[1]), int(_wg[2]), int(_wg[3]))
            else:
                self._saved_geo = self.geometry()
            QTimer.singleShot(0, self._animate_in)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            was_minimized = bool(event.oldState() & Qt.WindowState.WindowMinimized)
            is_normal = not bool(self.windowState() & Qt.WindowState.WindowMinimized)
            if was_minimized and is_normal:
                QTimer.singleShot(0, self._animate_in)
        super().changeEvent(event)

    def showMinimized(self):
        self._saved_geo = self.geometry()
        self._animate_to_taskbar(callback=lambda: super(NotizenApp, self).showMinimized())

    def closeEvent(self, event):
        if getattr(self, '_closing', False):
            event.accept()
            return
        event.ignore()
        # Größe immer speichern – bevor Animation die Geometrie verändert
        g = self.geometry()
        self.config["window_geo"] = [g.x(), g.y(), g.width(), g.height()]
        self.config["collapsed_folders"] = list(self._collapsed_folders)
        self.config["sidebar_expanded"] = self.sidebar._expanded
        save_config(self.config)
        self._saved_geo = g
        self._animate_to_taskbar(callback=self._do_close)

    def _do_close(self):
        self._save_current()
        self._save_tab_state()
        self._closing = True
        self.close()

    def _taskbar_anchor(self, reference_geo=None):
        """Mittelpunkt der Taskleiste auf dem Bildschirm, auf dem das Fenster liegt."""
        geo = reference_geo or getattr(self, '_saved_geo', None) or self.geometry()
        screen = QApplication.screenAt(geo.center())
        if screen is None:
            screen = QApplication.primaryScreen()
        full  = screen.geometry()
        avail = screen.availableGeometry()
        # Taskleisten-Seite ermitteln und Mittelpunkt berechnen
        gap_b = full.bottom()  - avail.bottom()
        gap_t = avail.top()    - full.top()
        gap_l = avail.left()   - full.left()
        gap_r = full.right()   - avail.right()
        biggest = max(gap_b, gap_t, gap_l, gap_r)
        if biggest == gap_b:
            cx, cy = avail.center().x(), avail.bottom() + gap_b // 2
        elif biggest == gap_t:
            cx, cy = avail.center().x(), full.top() + gap_t // 2
        elif biggest == gap_l:
            cx, cy = full.left() + gap_l // 2, avail.center().y()
        else:
            cx, cy = avail.right() + gap_r // 2, avail.center().y()
        return QPoint(cx, cy)

    def _animate_to_taskbar(self, callback):
        """Fenster zur Taskleiste schrumpfen + ausblenden."""
        if getattr(self, '_win_anim', None):
            try:
                self._win_anim.stop()
            except Exception:
                pass
        anchor    = self._taskbar_anchor()
        start_geo = self.geometry()
        sw = max(start_geo.width()  // 4, 80)
        sh = max(start_geo.height() // 4, 60)
        end_geo = QRect(anchor.x() - sw // 2, anchor.y() - sh // 2, sw, sh)

        geo_anim = QPropertyAnimation(self, b"geometry")
        geo_anim.setDuration(110)
        geo_anim.setStartValue(start_geo)
        geo_anim.setEndValue(end_geo)
        geo_anim.setEasingCurve(QEasingCurve.Type.InQuart)

        op_anim = QPropertyAnimation(self, b"windowOpacity")
        op_anim.setDuration(100)
        op_anim.setStartValue(1.0)
        op_anim.setEndValue(0.0)
        op_anim.setEasingCurve(QEasingCurve.Type.InQuad)

        grp = QParallelAnimationGroup(self)
        grp.addAnimation(geo_anim)
        grp.addAnimation(op_anim)
        grp.finished.connect(callback)
        grp.start()
        self._win_anim = grp

    def _animate_in(self):
        """Fenster von Taskleiste einblenden – volle Größe von Anfang an (kein Layout-Reflow)."""
        if getattr(self, '_win_anim', None):
            try:
                self._win_anim.stop()
            except Exception:
                pass
        target_geo = getattr(self, '_saved_geo', None) or self.geometry()
        anchor = self._taskbar_anchor(reference_geo=target_geo)

        # Volle Zielgröße, aber zentriert am Taskleisten-Anker positioniert
        # → Layout wird einmal berechnet, kein Neuzeichnen während der Animation
        start_geo = QRect(
            anchor.x() - target_geo.width()  // 2,
            anchor.y() - target_geo.height() // 2,
            target_geo.width(),
            target_geo.height()
        )

        self.setWindowOpacity(0.0)
        self.setGeometry(start_geo)

        geo_anim = QPropertyAnimation(self, b"geometry")
        geo_anim.setDuration(128)
        geo_anim.setStartValue(start_geo)
        geo_anim.setEndValue(target_geo)
        geo_anim.setEasingCurve(QEasingCurve.Type.OutQuart)

        op_anim = QPropertyAnimation(self, b"windowOpacity")
        op_anim.setDuration(112)
        op_anim.setStartValue(0.0)
        op_anim.setEndValue(1.0)
        op_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        grp = QParallelAnimationGroup(self)
        grp.addAnimation(geo_anim)
        grp.addAnimation(op_anim)
        grp.start()
        self._win_anim = grp

    def _adjust_zoom(self, direction: int):
        """direction: +1 = rein, -1 = raus. Schritt 10 %, Bereich 50–200 %."""
        new_zoom = round(_ZOOM[0] + direction * 0.1, 1)
        new_zoom = max(0.5, min(2.0, new_zoom))
        if new_zoom == _ZOOM[0]:
            return
        _ZOOM[0] = new_zoom
        self.config["zoom"] = new_zoom
        save_config(self.config)
        self._apply_editor_font()
        self.zoom_label.setText(f"{int(round(new_zoom * 100))}%")

    def _apply_editor_font(self):
        """Editor-Schrift (Familie + Größe × Zoom) neu setzen – kein UI-Rebuild."""
        family = self.config.get("editor_font", "Consolas")
        base   = self.config.get("editor_font_size", 14)
        size   = max(6, int(round(base * _ZOOM[0])))
        font = QFont(family, size)
        self.text_editor.document().setDefaultFont(font)
        self.text_editor.setFont(font)
        self.text_editor.setStyleSheet(f"""
            QTextEdit {{
                background: {T['bg']}; border: none; border-radius: 0;
                padding: 12px 24px; font-size: {size}px;
                font-family: '{family}'; color: {T['text']};
            }}
        """)

    def _on_theme_changed(self, theme_name):
        # Save state
        _tabs   = list(self.open_tabs)
        _active = self.active_tab_id
        _current = self.current_note_id

        # Apply new theme colors + global stylesheet
        self._apply_theme(theme_name)

        # Rebuild entire UI (all inline stylesheets use T at build time)
        self._build_ui()

        # Restore state
        self.open_tabs      = _tabs
        self.active_tab_id  = _active
        self.current_note_id = _current
        self._refresh_list()
        self._update_tabs()
        if _current:
            note = self._get_note(_current)
            if note:
                self.title_input.blockSignals(True)
                self.text_editor.blockSignals(True)
                self.title_input.setText(note.get("title", ""))
                self.text_editor.setRichText(note.get("content", ""))
                self.title_input.blockSignals(False)
                self.text_editor.blockSignals(False)
                self.date_label.setText(note.get("modified", "")[:16].replace("T", "  "))
                self.status_bar.showMessage(f"  {note.get('title', 'Unbenannte Notiz')}")

    # ── DRIVE SYNC ───────────────────────────
    def _init_drive(self):
        def init():
            self.drive_sync = DriveSync(self.config)
            if self.drive_sync.is_connected():
                self.sync_status_signal.emit(f"\u2713  Drive verbunden", T["accent"])
                self._download_merge()
            else:
                self.sync_status_signal.emit("\u2297  Drive nicht verbunden", T["muted"])
        threading.Thread(target=init, daemon=True).start()

    def _update_sync_label(self, text, color):
        self.status_bar.showMessage(text)

    def _manual_sync(self):
        if not self.drive_sync or not self.drive_sync.is_connected():
            QMessageBox.information(self, "Sync", "Google Drive nicht verbunden.\nBitte Einstellungen oeffnen.")
            return
        self._save_current()
        self.sync_status_signal.emit("\u2191  Wird hochgeladen...", "#4da6ff")
        threading.Thread(target=self._upload_to_drive, daemon=True).start()

    def _auto_sync(self):
        # Nur hochladen wenn PC-User tatsaechlich Aenderungen gemacht hat
        # verhindert das Ueberschreiben von Handy-Aenderungen durch PC-Fallback-Upload
        if self.drive_sync and self.drive_sync.is_connected() and self._has_local_changes:
            self._save_current()
            threading.Thread(target=self._upload_to_drive, daemon=True).start()

    def _periodic_download(self):
        if self.drive_sync and self.drive_sync.is_connected():
            threading.Thread(target=self._download_merge, daemon=True).start()

    @staticmethod
    def _text_merge3(base, local, remote):
        """3-Wege-Text-Merge: kombiniert Aenderungen von beiden Geraeten."""
        if local == remote: return local
        if local == base: return remote
        if remote == base: return local
        i = 0
        min_all = min(len(base), len(local), len(remote))
        while i < min_all and base[i] == local[i] == remote[i]: i += 1
        j = 0
        max_j = min(len(base) - i, len(local) - i, len(remote) - i)
        while j < max_j and base[-1-j] == local[-1-j] == remote[-1-j]: j += 1
        prefix = base[:i]
        suffix = base[-j:] if j > 0 else ''
        b_mid = base[i:len(base)-j if j else None]
        l_mid = local[i:len(local)-j if j else None]
        r_mid = remote[i:len(remote)-j if j else None]
        if l_mid == b_mid: return prefix + r_mid + suffix
        if r_mid == b_mid: return prefix + l_mid + suffix
        return prefix + l_mid + r_mid + suffix

    def _merge_remote(self, remote):
        """Merge remote data into local notes_data. Returns True if anything changed."""
        # ── Tombstones zusammenführen ──
        local_deleted = set(self.notes_data.get("deleted_ids", []))
        remote_deleted = set(remote.get("deleted_ids", []))
        all_deleted = local_deleted | remote_deleted

        local_deleted_folders = set(self.notes_data.get("deleted_folder_ids", []))
        remote_deleted_folders = set(remote.get("deleted_folder_ids", []))
        all_deleted_folders = local_deleted_folders | remote_deleted_folders

        local_by_id = {n["id"]: n for n in self.notes_data.get("notes", [])}
        remote_by_id = {n["id"]: n for n in remote.get("notes", [])}

        # Tombstone-Pruning: nur behalten wenn Notiz/Ordner auf einer Seite existiert
        all_note_ids = set(local_by_id) | set(remote_by_id)
        all_folder_ids = set(f["id"] for f in self.notes_data.get("folders", [])) | set(f["id"] for f in remote.get("folders", []))
        all_deleted = {d for d in all_deleted if d in all_note_ids}
        all_deleted_folders = {d for d in all_deleted_folders if d in all_folder_ids}

        self.notes_data["deleted_ids"] = list(all_deleted)
        self.notes_data["deleted_folder_ids"] = list(all_deleted_folders)
        merged = {}
        changed = False
        for nid in set(list(local_by_id) + list(remote_by_id)):
            if nid in all_deleted:
                if nid in local_by_id:  # Nur "changed" wenn lokal noch vorhanden
                    changed = True
                continue
            l, r = local_by_id.get(nid), remote_by_id.get(nid)
            if l and r:
                base = l.get("_base", "")
                local_changed = l.get("content", "") != base
                remote_changed = r.get("content", "") != base
                if local_changed and remote_changed and l.get("content") != r.get("content"):
                    merged_content = self._text_merge3(base, l.get("content", ""), r.get("content", ""))
                    winner = dict(l)
                    winner["content"] = merged_content
                    winner["modified"] = datetime.now().isoformat()
                    winner["_base"] = merged_content
                    changed = True
                    self._has_local_changes = True
                    print(f"[SYNC] 3-WAY MERGE: {nid[:8]}...")
                    merged[nid] = winner
                else:
                    winner = l if l["modified"] >= r["modified"] else r
                    if winner is r and r["modified"] > l["modified"]:
                        changed = True
                        winner = dict(r)
                        winner["_base"] = r.get("content", "")
                    merged[nid] = winner
            elif r:
                merged[nid] = r
                changed = True
            else:
                merged[nid] = l

        # ── Ordner-Merge: Remote-Reihenfolge als Basis ──
        local_fmap = {f["id"]: f for f in self.notes_data.get("folders", [])}
        remote_folders = remote.get("folders", [])
        remote_fmap = {f["id"]: f for f in remote_folders}

        # Remote-Reihenfolge beibehalten, lokale neue Ordner anhängen
        merged_folders = []
        seen_fids = set()
        for f in remote_folders:
            fid = f["id"]
            if fid in all_deleted_folders:
                continue
            local_f = local_fmap.get(fid)
            if local_f:
                # Ordner auf beiden Seiten: neuerer gewinnt komplett
                local_newer = local_f.get("modified", "") > f.get("modified", "")
                winner = local_f if local_newer else f
                merged_f = dict(winner)
                merged_f["note_ids"] = [n for n in winner.get("note_ids", []) if n not in all_deleted]
                print(f"[SYNC] Folder '{f.get('name','')}': L_mod={local_f.get('modified','?')[-12:]} R_mod={f.get('modified','?')[-12:]} → {'LOCAL' if local_newer else 'REMOTE'} wins, note_ids={merged_f['note_ids']}")
                merged_folders.append(merged_f)
            else:
                merged_folders.append(f)
            seen_fids.add(fid)

        # Lokale Ordner die remote nicht existieren (neu erstellt lokal)
        for f in self.notes_data.get("folders", []):
            if f["id"] not in seen_fids and f["id"] not in all_deleted_folders:
                merged_folders.append(f)

        old_folders = self.notes_data.get("folders", [])
        folders_changed = (len(merged_folders) != len(old_folders) or
                          any(mf.get("id") != lf.get("id") or
                              mf.get("note_ids", []) != lf.get("note_ids", []) or
                              mf.get("name") != lf.get("name")
                              for mf, lf in zip(merged_folders, old_folders)))
        if folders_changed:
            changed = True
        self.notes_data["folders"] = merged_folders

        # ── Tasks zusammenführen ──
        local_deleted_tasks = set(self.notes_data.get("deleted_task_ids", []))
        remote_deleted_tasks = set(remote.get("deleted_task_ids", []))
        all_deleted_tasks = local_deleted_tasks | remote_deleted_tasks

        local_task_map = {t["id"]: t for t in self.notes_data.get("tasks", [])}
        remote_task_map = {t["id"]: t for t in remote.get("tasks", [])}
        all_task_ids = set(local_task_map) | set(remote_task_map)
        # Pruning: nur behalten wenn Task auf einer Seite noch existiert
        all_deleted_tasks = {d for d in all_deleted_tasks if d in all_task_ids}

        merged_tasks = []
        for tid in all_task_ids:
            if tid in all_deleted_tasks:
                continue
            l, r = local_task_map.get(tid), remote_task_map.get(tid)
            if l and r:
                # Neuerer Zustand gewinnt (done_at falls vorhanden, sonst created)
                l_mod = l.get("done_at") or l.get("created", "")
                r_mod = r.get("done_at") or r.get("created", "")
                merged_tasks.append(l if l_mod >= r_mod else r)
            elif l:
                merged_tasks.append(l)
            else:
                merged_tasks.append(r)

        self.notes_data["deleted_task_ids"] = list(all_deleted_tasks)
        old_task_ids = {t["id"] for t in self.notes_data.get("tasks", [])}
        new_task_ids = {t["id"] for t in merged_tasks}
        if old_task_ids != new_task_ids or any(
            local_task_map.get(t["id"], {}).get("done") != t.get("done")
            for t in merged_tasks
        ):
            self.notes_data["tasks"][:] = merged_tasks
            changed = True

        if changed:
            self._remote_merge_pending = True
            self.notes_data["notes"] = list(merged.values())
            save_notes(self.notes_data)
        return changed

    def _upload_to_drive(self):
        """Download+merge first, then upload merged result — prevents overwriting other devices."""
        with self._sync_lock:
            # Bei Einweg-Sync: kein Download/Merge, direkt uploaden
            if not _cfg.get("one_way_sync", False):
                # Step 1: Download & merge
                self.sync_status_signal.emit("\u2193  Synchronisiere...", "#4da6ff")
                remote = self.drive_sync.download()
                if remote:
                    changed = self._merge_remote(remote)
                    if changed:
                        from PyQt6.QtCore import QMetaObject
                        QMetaObject.invokeMethod(self, "_on_remote_update", Qt.ConnectionType.QueuedConnection)
            # Step 2: Upload merged data (ohne _base)
            self.sync_status_signal.emit("\u2191  Wird hochgeladen...", "#4da6ff")
            upload_data = dict(self.notes_data)
            upload_data["notes"] = [{k: v for k, v in n.items() if k != "_base"} for n in upload_data.get("notes", [])]
            upload_data["one_way_sync"] = _cfg.get("one_way_sync", False)
            print(f"[SYNC] Upload: {len(upload_data.get('notes',[]))} Notizen, {len(upload_data.get('folders',[]))} Ordner, deleted_ids={len(upload_data.get('deleted_ids',[]))}, deleted_folder_ids={upload_data.get('deleted_folder_ids',[])}")
            ok = self.drive_sync.upload(upload_data)
            t = datetime.now().strftime("%H:%M")
            if ok:
                self._has_local_changes = False
                # base_content aktualisieren nach erfolgreichem Sync
                for n in self.notes_data.get("notes", []):
                    n["_base"] = n.get("content", "")
                save_notes(self.notes_data)
                self.sync_status_signal.emit(f"\u2713  Synced {t}", T["accent"])
            else:
                self.sync_status_signal.emit("\u26A0  Sync fehlgeschlagen \u2013 kein Internet?", "#ffaa00")

    def _download_merge(self):
        """Periodic background download — only download, no upload."""
        with self._sync_lock:
            self.sync_status_signal.emit("\u2193  Wird heruntergeladen...", "#4da6ff")
            remote = self.drive_sync.download()
            if not remote:
                self.sync_status_signal.emit("\u2297  Kein Zugriff auf Drive", T["muted"])
                return
            # Debug: aktuelle Notiz auf Remote pruefen
            print(f"[SYNC] DL: {len(remote.get('notes',[]))} Notizen, {len(remote.get('folders',[]))} Ordner, del={len(remote.get('deleted_ids',[]))}, del_f={len(remote.get('deleted_folder_ids',[]))}")
            print(f"[SYNC] RAW keys: {list(remote.keys())}")
            changed = self._merge_remote(remote)
            print(f"[SYNC] After merge: {len(self.notes_data.get('notes',[]))} Notizen, {len(self.notes_data.get('folders',[]))} Ordner, del={len(self.notes_data.get('deleted_ids',[]))}")
            # _base NUR fuer komplett neue Notizen setzen — NICHT fuer bestehende!
            # Sonst wird 3-Wege-Merge verhindert weil _base == remote nach Download
            for n in self.notes_data.get("notes", []):
                if "_base" not in n:
                    n["_base"] = n.get("content", "")
            t = datetime.now().strftime("%H:%M")
            if changed:
                print(f"[SYNC] Remote-Update erkannt! Aktualisiere UI...")
                from PyQt6.QtCore import QMetaObject
                QMetaObject.invokeMethod(self, "_on_remote_update", Qt.ConnectionType.QueuedConnection)
            else:
                self.sync_status_signal.emit(f"\u2713  Synced {t}", T["accent"])

    @pyqtSlot()
    def _on_remote_update(self):
        t = datetime.now().strftime("%H:%M")
        self.sync_status_signal.emit(f"\u2713  Synced {t}", T["accent"])
        self._refresh_list()
        self._update_tabs()
        self.task_panel.load_tasks(
            self.notes_data["tasks"],
            lambda: save_notes(self.notes_data),
            self.notes_data["deleted_task_ids"]
        )
        if self.current_note_id:
            note = next((n for n in self.notes_data.get("notes", []) if n["id"] == self.current_note_id), None)
            if note:
                cursor_pos = self.text_editor.textCursor().position()
                self.text_editor.blockSignals(True)
                self.title_input.blockSignals(True)
                self.title_input.setText(note.get("title", ""))
                self.text_editor.setRichText(note.get("content", ""))
                cursor = self.text_editor.textCursor()
                cursor.setPosition(min(cursor_pos, len(note.get("content", ""))))
                self.text_editor.setTextCursor(cursor)
                self.text_editor.blockSignals(False)
                self.title_input.blockSignals(False)
        # Editor ist jetzt aktualisiert — autosave darf wieder laufen
        self._remote_merge_pending = False

    # ── Window drag: leere Flächen in TabBar + IconRail ──
    def _is_drag_area(self, global_pos):
        """True wenn der Klick auf einer leeren Fläche in TabBar oder IconRail ist."""
        from PyQt6.QtWidgets import QApplication
        widget = QApplication.widgetAt(global_pos)
        if widget is None:
            return False
        # Prüfe ob das Widget oder ein Elternteil interaktiv ist
        w = widget
        while w is not None:
            if isinstance(w, (QPushButton, TabButton)):
                return False
            if isinstance(w, QLineEdit):
                return False
            if w is self:
                break
            w = w.parent()
        # Erlaubt: leere Flächen in TabBar oder IconRail
        w = widget
        while w is not None:
            if w is self.tab_bar or w is self.icon_rail:
                return True
            if w is self:
                break
            w = w.parent()
        return False

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                gp = event.globalPosition().toPoint()
                if not getattr(self, '_is_maximized', False) and self._is_drag_area(gp):
                    self._drag_pos = gp - self.frameGeometry().topLeft()
                    return True
        elif event.type() == QEvent.Type.MouseMove:
            if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if self._drag_pos is not None:
                self._drag_pos = None
                return True
        elif event.type() == QEvent.Type.MouseButtonDblClick:
            if event.button() == Qt.MouseButton.LeftButton:
                gp = event.globalPosition().toPoint()
                if self._is_drag_area(gp):
                    self.tab_bar._toggle_maximize()
                    return True
        return super().eventFilter(obj, event)



# ─────────────────────────────────────────────
if __name__ == "__main__":
    import traceback as _tb
    _crash_path = Path(__file__).parent / "crash.log"
    _boot_log = Path(__file__).parent / "boot.log"
    def _blog(msg):
        with open(_boot_log, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    def _global_exc(typ, val, tb):
        txt = "".join(_tb.format_exception(typ, val, tb))
        _crash_path.write_text(txt, encoding="utf-8")
        _blog(f"[CRASH] {txt}")
        sys.__excepthook__(typ, val, tb)
    sys.excepthook = _global_exc
    _boot_log.write_text("", encoding="utf-8")  # reset
    try:
        _blog("[BOOT] load_config...")
        _cfg = load_config()
        _set_console_visible(_cfg.get("show_console", True))
        _blog("[BOOT] QApplication...")
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        # App-Icon für Fenster + Taskleiste
        _icon_path = Path(__file__).parent / "favicon_io" / "favicon.ico"
        if _icon_path.exists():
            _app_icon = QIcon(str(_icon_path))
            app.setWindowIcon(_app_icon)
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("notizen.app")
            except Exception:
                pass
        _blog("[BOOT] NotizenApp()...")
        window = NotizenApp()
        _blog("[BOOT] show()...")
        app.installEventFilter(window)
        window.show()
        _blog("[BOOT] exec()...")
        sys.exit(app.exec())
    except Exception:
        txt = _tb.format_exc()
        _crash_path.write_text(txt, encoding="utf-8")
        _blog(f"[CRASH] {txt}")
        raise
