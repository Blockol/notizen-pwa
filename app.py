import sys
import json
import threading
import os
import re
from datetime import datetime
from pathlib import Path
import requests

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QPushButton,
    QLabel, QMenu, QDialog, QMessageBox, QFrame, QFileDialog,
    QScrollArea, QSizePolicy, QStatusBar, QStackedWidget, QComboBox,
    QInputDialog, QAbstractItemView, QSizeGrip, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, pyqtSlot, QThread, QSize, QPropertyAnimation,
    QEasingCurve, pyqtProperty, QObject, QEvent, QPoint
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QAction, QTextCursor,
    QKeySequence, QShortcut, QTextCharFormat, QTextDocument,
    QPainter, QBrush, QPixmap, QPainterPath, QRegion
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
_SLIDERS_SVG    = ('<line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="6" y2="3"/>'
                   '<line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="6" y2="3"/>'
                   '<line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="10" y2="3"/>'
                   '<line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="12" y2="12"/>'
                   '<line x1="18" x2="22" y1="16" y2="16"/>')
_EDIT_SVG       = ('<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>'
                   '<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>')
_FOLDER_PLUS_SVG = ('<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>'
                    '<line x1="12" x2="12" y1="11" y2="17"/><line x1="9" x2="15" y1="14" y2="14"/>')


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


def load_notes():
    if NOTES_FILE.exists():
        with open(NOTES_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"notes": [], "version": 1, "last_modified": datetime.now().isoformat()}


def save_notes(data):
    data["last_modified"] = datetime.now().isoformat()
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_stylesheet():
    return f"""
        QWidget {{
            background-color: {T['bg']};
            color: {T['text']};
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
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

    def run(self):
        context = ""
        for n in self.notes:
            title = n.get("title", "Unbenannt")
            content = (n.get("content", "")[:600]).replace("\n", " ")
            context += f"--- Notiz ID:{n['id']} ---\nTitel: {title}\nInhalt: {content}\n\n"

        instruction = (
            "Du bist ein KI-Assistent fuer Notizen. Der Nutzer stellt eine Frage oder Suchanfrage. "
            "Analysiere alle Notizen und gib eine hilfreiche, ausfuehrliche Antwort auf Deutsch. "
            "Gib das Ergebnis als JSON zurueck: "
            "{\"answer\": \"Deine ausfuehrliche Antwort hier...\", "
            "\"sources\": [{\"id\": \"...\", \"title\": \"...\", \"reason\": \"Kurze Begruendung\"}]}. "
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
        accent_bar = QWidget()
        accent_bar.setFixedWidth(2)
        accent_bar.setStyleSheet(f"background: {T['accent'] if is_active else 'transparent'};")
        layout.addWidget(accent_bar)

        # Content row — no custom hover/bg, QListWidget stylesheet handles that
        content = QWidget()
        active_bg = "rgba(0,255,136,0.08)" if is_active else "transparent"
        content.setStyleSheet(f"QWidget {{ background: {active_bg}; }}")
        cl = QHBoxLayout(content)
        left_pad = 28 if folder_child else 14
        cl.setContentsMargins(left_pad, 5, 10, 5)
        cl.setSpacing(6)

        title = self.note.get("title") or "Unbenannte Notiz"
        t = QLabel(title[:40])
        t.setStyleSheet(f"""
            color: {T['accent'] if is_active else T['text']};
            font-size: 13px;
            font-weight: {'500' if is_active else '400'};
            border: none; background: transparent;
        """)
        cl.addWidget(t, 1)

        date = self.note.get("modified", "")[:10]
        d = QLabel(date)
        d.setStyleSheet(f"color: {T['muted']}; font-size: 10px; border: none; background: transparent;")
        cl.addWidget(d)

        layout.addWidget(content, 1)
        self.setFixedHeight(32)


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
        chev.setStyleSheet(f"color: {T['muted']}; font-size: 8px; background: transparent; border: none;")
        cl.addWidget(chev)

        name_lbl = QLabel(folder.get("name", "Ordner"))
        name_lbl.setStyleSheet(
            f"color: {T['text']}; font-size: 13px; font-weight: 600; "
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
        chev.setStyleSheet(f"color: {T['muted']}; font-size: 10px; background: transparent;")
        hl.addWidget(chev)

        title_lbl = QLabel(note.get("title") or "Unbenannte Notiz")
        title_lbl.setStyleSheet(f"color: {T['text']}; font-size: 13px; font-weight: 500; background: transparent;")
        hl.addWidget(title_lbl, 1)

        count_lbl = QLabel(str(count))
        count_lbl.setStyleSheet(f"color: {T['muted']}; font-size: 11px; background: transparent;")
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
                        color: {T['muted']}; font-size: 12px; line-height: 1.4;
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
        self._highlight(which)

    def _highlight(self, which):
        svgs = {"files": _FILE_TEXT_SVG, "search": _SEARCH_SVG}
        for btn, name in [(self.btn_files, "files"), (self.btn_search, "search")]:
            if name == which:
                btn.setIcon(_svg_icon(svgs[name], T['accent'], 16))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(255,255,255,0.07); border: none; border-radius: 6px;
                        border-left: 2px solid {T['accent']};
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
        self._sort_mode = "name_asc"
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
                color: {T['text']}; font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {T['accent']}; }}
        """)
        sb_layout.addWidget(self.search_input)

        # Result count label
        self.result_count_lbl = QLabel("")
        self.result_count_lbl.setStyleSheet(f"color: {T['muted']}; font-size: 11px; padding: 2px 0;")
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
                          color: {T['muted']}; font-size: 10px; padding: 2px 8px; }}
            QPushButton:checked {{ background: #0d1f15; border-color: {T['accent']}; color: {T['accent']}; }}
        """)
        ai_row_layout.addWidget(self.ai_search_toggle)
        ai_row_layout.addStretch()
        sb_layout.addWidget(self.ai_search_row)

        self.ai_search_status = QLabel("")
        self.ai_search_status.setStyleSheet(f"color: {T['muted']}; font-size: 9px;")
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
                    border-radius: 6px; padding: 4px; color: {T['text']}; font-size: 13px; }}
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
        layout.setContentsMargins(12, 0, 4, 0)
        layout.setSpacing(2)

        display_title = (title or "Unbenannt")[:22]
        self.label = QLabel(display_title)
        self.label.setCursor(Qt.CursorShape.PointingHandCursor)
        color = T['text'] if is_active else T['muted']
        weight = "600" if is_active else "400"
        self.label.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: {weight};"
            f" background: transparent; border: none;"
        )
        layout.addWidget(self.label)

        close_btn = QPushButton("\u00D7")
        close_btn.setFixedSize(16, 16)
        if is_active:
            close_btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; color: {T['muted']};
                              font-size: 13px; border-radius: 3px; }}
                QPushButton:hover {{ background: rgba(255,255,255,0.15); color: {T['text']}; }}
            """)
        else:
            # Inactive: hide × until hover (achieved via near-transparent)
            close_btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; color: transparent;
                              font-size: 13px; border-radius: 3px; }}
                QPushButton:hover {{ color: {T['muted']}; }}
            """)
        close_btn.clicked.connect(lambda: self.close_clicked.emit(self.note_id))
        layout.addWidget(close_btn)

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
                color: {T['muted']}; font-size: 13px; font-weight: 500;
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
                color: {T['muted']}; font-size: 13px; font-weight: 500;
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
                color: {T['muted']}; font-size: 18px; font-weight: 300;
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
                color: {T['muted']}; font-size: 16px; font-family: 'Segoe UI', sans-serif;
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
        added_ids = new_ids - self._prev_tab_ids
        self._prev_tab_ids = new_ids

        # Clear old tabs
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
            # Slide-in animation for newly added tabs
            if nid in added_ids:
                anim = QPropertyAnimation(tab, b"maximumHeight")
                anim.setStartValue(0)
                anim.setEndValue(34)
                anim.setDuration(160)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                tab._slide_anim = anim  # prevent GC
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
        delta = event.angleDelta().y()
        self._smooth_scroll(-delta // 2)
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

    def _build(self):
        self._backdrop = QPixmap()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        center_h = QHBoxLayout()
        center_h.setContentsMargins(0, 0, 0, 0)
        center_h.addStretch(1)

        self.modal = QWidget()
        self.modal.setFixedSize(880, 580)
        self.modal.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.modal.setStyleSheet(f"""
            QWidget#modal {{
                background: {T['bg']};
                border: 1px solid {T['border']};
                border-radius: 12px;
            }}
        """)
        self.modal.setObjectName("modal")
        # Rounded corners via mask (clips all child widgets)
        _path = QPainterPath()
        _path.addRoundedRect(QRectF(0, 0, 880, 580), 12.0, 12.0)
        self.modal.setMask(QRegion(_path.toFillPolygon().toPolygon()))
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
            f"color: {T['muted']}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 1px; padding: 0 4px 6px 4px; background: transparent; border: none;"
        )
        nav_layout.addWidget(section_lbl)

        self.cat_list = QListWidget()
        self.cat_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent; border: none; outline: none;
            }}
            QListWidget::item {{
                padding: 7px 10px; color: {T['muted']}; font-size: 13px;
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
            f"color: {T['text']}; font-size: 18px; font-weight: 600; background: transparent; border: none;"
        )
        hl.addWidget(self.header_title)
        hl.addStretch()

        close_btn = QPushButton("\u00D7")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; color: {T['muted']};
                          font-size: 18px; border-radius: 6px; }}
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
        lbl.setStyleSheet(f"color: {T['muted']}; font-size: 10px; letter-spacing: 1px; font-weight: 600; margin-top: 8px; margin-bottom: 4px;")
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
        name_lbl.setStyleSheet(f"color: {T['text']}; font-size: 14px; font-weight: 500; border: none; background: transparent;")
        tcl.addWidget(name_lbl)
        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setStyleSheet(f"color: {T['muted']}; font-size: 12px; border: none; background: transparent;")
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
        version_lbl.setStyleSheet(f"color: {T['muted']}; font-size: 12px;")
        layout.addWidget(version_lbl)
        layout.addSpacing(16)

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
        self.sync_status_label.setStyleSheet(f"color: {T['muted']}; font-size: 11px;")
        self._make_setting_row(layout, "Verbindungsstatus", "", self.sync_status_label)

        save_btn = QPushButton("Speichern")
        save_btn.setFixedWidth(120)
        save_btn.setStyleSheet(f"background: {T['accent']}; color: #000; border: none; font-weight: bold; border-radius: 6px; padding: 7px 14px;")
        save_btn.clicked.connect(self._save_sync)
        layout.addSpacing(16)
        layout.addWidget(save_btn)

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
        cats = ["Allgemein", "Darstellung", "KI", "Synchronisation"]
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

    def _save_sync(self):
        self.config["drive_credentials"] = self.creds_field.text().strip()
        save_config(self.config)
        main_app = self.parent().parent()
        if hasattr(main_app, '_init_drive'):
            main_app._init_drive()

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
        title.setStyleSheet(f"color: {T['accent']}; font-size: 16px; font-weight: bold; letter-spacing: 3px;")
        layout.addWidget(title)

        provider = self.config.get("ai_provider", "groq").upper()
        sub = QLabel(f"Provider: {provider}")
        sub.setStyleSheet(f"color: {T['muted']}; font-size: 11px;")
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
        lbl.setStyleSheet(f"color: {T['muted']}; font-size: 10px;")
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
        rlbl.setStyleSheet(f"color: {T['muted']}; font-size: 10px;")
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
        title_lbl.setStyleSheet(f"color: {T['accent']}; font-size: 16px; font-weight: bold; letter-spacing: 3px;")
        layout.addWidget(title_lbl)

        query_lbl = QLabel(f"Frage: {query}")
        query_lbl.setStyleSheet(f"color: {T['muted']}; font-size: 11px;")
        query_lbl.setWordWrap(True)
        layout.addWidget(query_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {T['border']};")
        layout.addWidget(sep)

        answer_lbl = QLabel("Antwort:")
        answer_lbl.setStyleSheet(f"color: {T['muted']}; font-size: 10px;")
        layout.addWidget(answer_lbl)

        self.answer_box = QTextEdit()
        self.answer_box.setReadOnly(True)
        self.answer_box.setPlainText(self.result.get("answer", "Keine Antwort erhalten."))
        self.answer_box.setStyleSheet(
            f"background: {T['bg2']}; border: 1px solid {T['border']}; border-radius: 6px; padding: 8px; font-size: 12px;"
        )
        layout.addWidget(self.answer_box, stretch=1)

        sources = self.result.get("sources", [])
        if sources:
            src_lbl = QLabel("Quellen:")
            src_lbl.setStyleSheet(f"color: {T['muted']}; font-size: 10px;")
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
                reason_lbl.setStyleSheet(f"color: {T['muted']}; font-size: 10px;")
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
                color: {T['text']}; font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {T['accent']}; }}
        """)
        self.field.textChanged.connect(self._on_text_changed)
        self.field.returnPressed.connect(self._find_next)
        layout.addWidget(self.field, 1)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(f"color: {T['muted']}; font-size: 11px; background: transparent; border: none; padding: 0 6px;")
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
                          font-size: 15px; border-radius: 5px; padding: 0; }}
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
                          font-size: 13px; border-radius: 5px; padding: 0; }}
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
            self.count_lbl.setStyleSheet(f"color: {T['danger']}; font-size: 11px; background: transparent; border: none;")
        else:
            self.count_lbl.setText(f"{count} Treffer")
            self.count_lbl.setStyleSheet(f"color: {T['muted']}; font-size: 11px; background: transparent; border: none;")
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
                font-size: 14px; color: {T['text']};
            }}
        """)
        self.search_field.textChanged.connect(self._filter)
        self.search_field.returnPressed.connect(self._accept_current)
        fr_layout.addWidget(self.search_field, 1)

        clear_btn = QPushButton("\u2715")
        clear_btn.setFixedSize(22, 22)
        clear_btn.setStyleSheet(f"""
            QPushButton {{ background: {T['bg3']}; border: none; border-radius: 11px;
                          color: {T['muted']}; font-size: 11px; }}
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
                font-size: 13px; border-radius: 4px;
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
            lbl.setStyleSheet(f"color: {T['muted']}; font-size: 11px; background: transparent; border: none;")
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
        self.current_note_id = None
        self.open_tabs = list(self.config.get("open_tabs", []))
        self.active_tab_id = None
        self.drive_sync = None
        self._sync_lock = threading.Lock()
        self._collapsed_folders = set()
        self._has_local_changes = False  # True nur wenn PC-User getippt hat
        self._remote_merge_pending = False  # True waehrend remote merge → verhindert autosave

        self._drag_pos = None
        self._is_maximized = False
        self._normal_geo = None
        self._quick_switch_dlg = None
        self._apply_theme(self.config.get("theme", "dark"))
        self._build_ui()
        self._refresh_list()
        self._update_tabs()
        self._init_drive()

        # Restore last active tab
        if self.open_tabs:
            self._switch_to_tab(self.open_tabs[0])

        # Auto-save every 3s
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self._save_current)
        self.autosave_timer.start(3000)

        # Auto-sync every 30s fallback (upload)
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._auto_sync)
        self.sync_timer.start(30000)

        # Auto-download every 2s (pick up changes from other devices)
        self.download_timer = QTimer()
        self.download_timer.timeout.connect(self._periodic_download)
        self.download_timer.start(2000)

        # Debounce upload: 1s after last change
        self._upload_debounce = QTimer()
        self._upload_debounce.setSingleShot(True)
        self._upload_debounce.timeout.connect(self._auto_sync)

        self.sync_status_signal.connect(self._update_sync_label)

        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._save_current)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._new_note)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self._close_active_tab)
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
                font-size: 20px; font-weight: bold; color: {T['text']};
                padding: 14px 24px;
            }}
            QLineEdit:focus {{ border-bottom-color: {T['accent']}; }}
        """)
        self.title_input.textChanged.connect(self._on_title_changed)
        ea_layout.addWidget(self.title_input)

        self.date_label = QLabel("")
        self.date_label.setStyleSheet(f"color: {T['border']}; font-size: 9px; padding: 3px 26px;")
        ea_layout.addWidget(self.date_label)

        # Editor
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("Schreib deine Notiz hier...\n\nTipp: Text markieren -> Rechtsklick -> KI-Aktion")
        self.text_editor.setStyleSheet(f"""
            QTextEdit {{
                background: {T['bg']}; border: none; border-radius: 0;
                padding: 12px 24px; font-size: 13px; color: {T['text']};
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
        self.status_bar.setStyleSheet(f"background: {T['bg2']}; color: {T['muted']}; font-size: 12px; border-top: 1px solid {T['border']};")
        self.status_bar.setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Keine Notiz ausgewaehlt")
        # Size grip for frameless window resize
        grip = QSizeGrip(self)
        grip.setStyleSheet("background: transparent;")
        grip.setFixedSize(16, 16)
        self.status_bar.addPermanentWidget(grip)

        # Highlight files by default
        self.icon_rail._highlight("files")
        # Sidebar starts expanded — show sync/settings in rail
        self.icon_rail.set_sidebar_expanded(True)

    # ── SIDEBAR ──────────────────────────────
    def _toggle_sidebar(self):
        self.sidebar.toggle()
        self.icon_rail.set_sidebar_expanded(self.sidebar._expanded)

    def _show_files(self):
        if not self.sidebar._expanded:
            self.sidebar.toggle()
            self.icon_rail.set_sidebar_expanded(True)
        self.sidebar.switch_tab("files")

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
        # Switch to search tab if user types in search field
        self.sidebar.switch_tab("search")
        self._refresh_list()

    def _on_sort_changed(self, mode):
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
                for note in self._apply_sort(child_notes):
                    add_note_item(note, folder_child=True)

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
            if uid in self._collapsed_folders:
                self._collapsed_folders.discard(uid)
            else:
                self._collapsed_folders.add(uid)
            self._refresh_list()
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

    def _on_list_double_click(self, item):
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
        if note_id not in self.open_tabs:
            self.open_tabs.append(note_id)
        self._switch_to_tab(note_id)

    def _switch_to_tab(self, note_id):
        self._save_current()
        self.current_note_id = note_id
        self.active_tab_id = note_id
        self.text_editor.setExtraSelections([])  # clear highlights
        note = self._get_note(note_id)
        if note:
            self.title_input.blockSignals(True)
            self.text_editor.blockSignals(True)
            self.title_input.setText(note.get("title", ""))
            self.text_editor.setPlainText(note.get("content", ""))
            self.title_input.blockSignals(False)
            self.text_editor.blockSignals(False)
            mod = note.get("modified", "")[:16].replace("T", "  ")
            self.date_label.setText(f"Zuletzt bearbeitet: {mod}")
            self.status_bar.showMessage(f"  {note.get('title', 'Unbenannte Notiz')}")
        self._update_tabs()
        self._refresh_list()
        # Hide settings overlay when switching tabs
        self.settings_overlay.setVisible(False)

    def _close_tab(self, note_id):
        if note_id in self.open_tabs:
            idx = self.open_tabs.index(note_id)
            self.open_tabs.remove(note_id)
            if self.active_tab_id == note_id:
                if self.open_tabs:
                    new_idx = min(idx, len(self.open_tabs) - 1)
                    self._switch_to_tab(self.open_tabs[new_idx])
                else:
                    self.current_note_id = None
                    self.active_tab_id = None
                    self.title_input.clear()
                    self.text_editor.clear()
                    self.date_label.setText("")
                    self.status_bar.showMessage("Keine Notiz ausgewaehlt")
            self._update_tabs()
            self._save_tab_state()

    def _close_active_tab(self):
        if self.active_tab_id:
            self._close_tab(self.active_tab_id)

    def _update_tabs(self):
        self.tab_bar.update_tabs(self.open_tabs, self.active_tab_id, self.notes_data)
        self._save_tab_state()

    def _save_tab_state(self):
        self.config["open_tabs"] = self.open_tabs
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
        self.title_input.setFocus()

    def _delete_note(self, note_id):
        reply = QMessageBox.question(self, "Loeschen", "Diese Notiz wirklich loeschen?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._add_tombstone(note_id)
            self.notes_data["notes"] = [n for n in self.notes_data["notes"] if n["id"] != note_id]
            self._remove_note_from_all_folders(note_id)
            if note_id in self.open_tabs:
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
        for note_id in note_ids:
            self._add_tombstone(note_id)
            self.notes_data["notes"] = [n for n in self.notes_data["notes"] if n["id"] != note_id]
            self._remove_note_from_all_folders(note_id)
            if note_id in self.open_tabs:
                self.open_tabs.remove(note_id)
            if self.active_tab_id == note_id:
                self.active_tab_id = None
                self.current_note_id = None
        save_notes(self.notes_data)
        if self.active_tab_id is None:
            if self.open_tabs:
                self._switch_to_tab(self.open_tabs[-1])
            else:
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
        note = self._get_note(self.current_note_id)
        if note:
            new_title = self.title_input.text().strip()
            new_content = self.text_editor.toPlainText()
            if note.get("title") != new_title or note.get("content") != new_content:
                note["title"] = new_title or "Unbenannte Notiz"
                note["content"] = new_content
                note["modified"] = datetime.now().isoformat()
                save_notes(self.notes_data)
                self._update_tabs()
                self._refresh_list()

    def _on_title_changed(self):
        self._save_current()
        self._has_local_changes = True
        if self.drive_sync and self.drive_sync.is_connected():
            self._upload_debounce.start(1000)

    def _on_text_changed(self):
        content = self.text_editor.toPlainText()
        words = len(content.split()) if content.strip() else 0
        chars = len(content)
        self.status_bar.showMessage(f"  {words} Woerter  \u00B7  {chars} Zeichen")
        self._has_local_changes = True
        if self.drive_sync and self.drive_sync.is_connected():
            self._upload_debounce.start(1000)

    # ── CONTEXT MENUS ─────────────────────────
    def _editor_context_menu(self, pos):
        menu = QMenu(self)
        ai_action = QAction("\u2726  KI-Aktion...", self)
        ai_action.triggered.connect(self._open_ai_dialog)
        menu.addAction(ai_action)
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
                    border-radius: 6px; padding: 4px; color: {T['text']}; font-size: 13px; }}
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
                self.text_editor.setPlainText(note.get("content", ""))
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

        if changed:
            self._remote_merge_pending = True
            self.notes_data["notes"] = list(merged.values())
            save_notes(self.notes_data)
        return changed

    def _upload_to_drive(self):
        """Download+merge first, then upload merged result — prevents overwriting other devices."""
        with self._sync_lock:
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
        if self.current_note_id:
            note = next((n for n in self.notes_data.get("notes", []) if n["id"] == self.current_note_id), None)
            if note:
                cursor_pos = self.text_editor.textCursor().position()
                self.text_editor.blockSignals(True)
                self.title_input.blockSignals(True)
                self.title_input.setText(note.get("title", ""))
                self.text_editor.setPlainText(note.get("content", ""))
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

    def closeEvent(self, event):
        self._save_current()
        self._save_tab_state()
        event.accept()


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = NotizenApp()
    app.installEventFilter(window)  # Window drag über gesamte TabBar
    window.show()
    sys.exit(app.exec())
