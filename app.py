import sys
import json
import threading
import os
from datetime import datetime
from pathlib import Path
import requests

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QPushButton,
    QLabel, QMenu, QDialog, QMessageBox, QFrame, QFileDialog,
    QScrollArea, QSizePolicy, QStatusBar, QStackedWidget, QComboBox
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QThread, QSize, QPropertyAnimation,
    QEasingCurve, pyqtProperty, QObject
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QAction, QTextCursor,
    QKeySequence, QShortcut
)

# ─────────────────────────────────────────────
#  CONFIG & DATA
# ─────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".notizen_config.json"
NOTES_FILE  = Path.home() / "notizen_data.json"

THEMES = {
    "dark": {
        "bg":     "#000000",   # --background-primary  (editor)
        "bg2":    "#1e1e1e",   # --background-secondary (sidebar/rail/tabbar)
        "bg3":    "#111111",   # --background-primary-alt (hover/active)
        "border": "#2e2e2e",   # solid ~rgba(255,255,255,0.1)
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

            SCOPES = ["https://www.googleapis.com/auth/drive.file"]
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
        except Exception as e:
            print(f"Drive setup error: {e}")

    def _find_or_create_file(self):
        try:
            results = self.service.files().list(
                q="name='notizen_sync.json' and trashed=false",
                fields="files(id, name)"
            ).execute()
            files = results.get("files", [])
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
    result_ready = pyqtSignal(list)
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
            snippet = (n.get("content", "")[:150]).replace("\n", " ")
            context += f"- ID:{n['id']} Titel:{title} Inhalt:{snippet}\n"

        instruction = (
            "Du bist ein Notizen-Suchassistent. Der User sucht in seinen Notizen. "
            "Gib eine JSON-Liste zurueck mit den relevantesten Notizen. "
            "Format: [{\"id\": \"...\", \"reason\": \"...\"}]. Maximal 10 Ergebnisse. Nur JSON, kein anderer Text."
        )
        prompt = f"Suchanfrage: {self.query}\n\nNotizen:\n{context}"

        provider = self.config.get("ai_provider", "groq")
        try:
            if provider == "gemini":
                result_text = self._call_gemini(instruction, prompt)
            else:
                result_text = self._call_groq(instruction, prompt)
            # Parse JSON from result
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]
            results = json.loads(result_text)
            self.result_ready.emit(results)
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
    def __init__(self, note, is_active=False):
        super().__init__()
        self.note = note
        self._build(is_active)

    def _build(self, is_active):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left accent bar (active indicator, 2px like Obsidian)
        accent_bar = QWidget()
        accent_bar.setFixedWidth(2)
        accent_bar.setStyleSheet(f"background: {T['accent'] if is_active else 'transparent'};")
        layout.addWidget(accent_bar)

        # Content row
        content = QWidget()
        if is_active:
            content.setStyleSheet("""
                QWidget { background: rgba(0,255,136,0.08); }
                QWidget:hover { background: rgba(0,255,136,0.12); }
            """)
        else:
            content.setStyleSheet("""
                QWidget { background: transparent; }
                QWidget:hover { background: rgba(255,255,255,0.05); }
            """)
        cl = QHBoxLayout(content)
        cl.setContentsMargins(14, 5, 10, 5)
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
#  ICON RAIL (40px, always visible)
# ─────────────────────────────────────────────
class IconRail(QWidget):
    toggle_clicked = pyqtSignal()
    files_clicked = pyqtSignal()
    search_clicked = pyqtSignal()
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

        # ☰ hamburger toggle
        self.btn_toggle = self._make_btn("\u2630", "Toggle Sidebar", size=20)
        self.btn_toggle.clicked.connect(self.toggle_clicked.emit)
        layout.addWidget(self.btn_toggle)

        # ⎗ stacked pages = files/notes
        self.btn_files = self._make_btn("\u2397", "Dateien", size=18)
        self.btn_files.clicked.connect(lambda: self._activate("files"))
        layout.addWidget(self.btn_files)

        # ⌕ magnifier = search
        self.btn_search = self._make_btn("\u2315", "Suche", size=18)
        self.btn_search.clicked.connect(lambda: self._activate("search"))
        layout.addWidget(self.btn_search)

        layout.addStretch()

        # ↻ sync
        self.btn_sync = self._make_btn("\u21bb", "Synchronisieren", size=18)
        self.btn_sync.clicked.connect(self.sync_clicked.emit)
        layout.addWidget(self.btn_sync)

        # ⚙ gear = settings (text-mode via VS15)
        self.btn_settings = self._make_btn("\u2699\ufe0e", "Einstellungen", size=18)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.btn_settings)

    def _make_btn(self, icon, tooltip, size=18):
        btn = QPushButton(icon)
        btn.setToolTip(tooltip)
        btn.setFixedSize(40, 40)
        # Force text-mode rendering (no color emoji) via explicit font
        f = QFont("Segoe UI Symbol", size)
        f.setStyleHint(QFont.StyleHint.SansSerif)
        btn.setFont(f)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; border-radius: 6px;
                color: {T['muted']};
                border-left: 2px solid transparent;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.07); color: {T['text']}; }}
        """)
        return btn

    def _activate(self, which):
        if which == "files":
            self.files_clicked.emit()
        elif which == "search":
            self.search_clicked.emit()
        self._highlight(which)

    def _highlight(self, which):
        for btn, name in [(self.btn_files, "files"), (self.btn_search, "search")]:
            if name == which:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(255,255,255,0.07); border: none; border-radius: 6px;
                        color: {T['accent']};
                        border-left: 2px solid {T['accent']};
                    }}
                    QPushButton:hover {{ background: rgba(255,255,255,0.1); }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent; border: none; border-radius: 6px;
                        color: {T['muted']};
                        border-left: 2px solid transparent;
                    }}
                    QPushButton:hover {{ background: rgba(255,255,255,0.07); color: {T['text']}; }}
                """)


# ─────────────────────────────────────────────
#  SIDEBAR PANEL (collapsible)
# ─────────────────────────────────────────────
class SidebarPanel(QWidget):
    note_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._expanded = True
        self._target_width = 220
        self.setMinimumWidth(0)
        self.setMaximumWidth(220)
        self.setStyleSheet(f"background-color: {T['bg2']}; border-right: 1px solid {T['border']};")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suchen...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {T['bg3']}; border: 1px solid {T['border']};
                border-radius: 4px; padding: 5px 10px;
                color: {T['text']}; font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {T['accent']}; }}
        """)
        layout.addWidget(self.search_input)

        # AI search toggle
        self.ai_search_row = QWidget()
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
        layout.addWidget(self.ai_search_row)

        # AI search status
        self.ai_search_status = QLabel("")
        self.ai_search_status.setStyleSheet(f"color: {T['muted']}; font-size: 9px;")
        self.ai_search_status.setVisible(False)
        layout.addWidget(self.ai_search_status)

        lbl = QLabel("NOTIZEN")
        lbl.setStyleSheet(f"color: {T['muted']}; font-size: 10px; font-weight: 600; letter-spacing: 1px; padding-left: 8px; padding-top: 4px;")
        layout.addWidget(lbl)

        self.notes_list = QListWidget()
        self.notes_list.setSpacing(0)
        layout.addWidget(self.notes_list)

    def toggle(self):
        if self._expanded:
            self._animate(0)
        else:
            self._animate(220)
        self._expanded = not self._expanded

    def _animate(self, target):
        anim = QPropertyAnimation(self, b"maximumWidth")
        anim.setDuration(200)
        anim.setStartValue(self.maximumWidth())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim = anim  # prevent GC
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
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.left_arrow = QPushButton("\u25C0")
        self.left_arrow.setFixedSize(24, 32)
        self.left_arrow.setStyleSheet(f"QPushButton {{ background: {T['bg2']}; border: none; color: {T['muted']}; font-size: 10px; }} QPushButton:hover {{ color: {T['text']}; }}")
        self.left_arrow.clicked.connect(self._scroll_left)
        self.left_arrow.setVisible(False)
        layout.addWidget(self.left_arrow)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFixedHeight(36)
        self.scroll_area.setStyleSheet(f"QScrollArea {{ background: transparent; border: none; }}")

        self.tab_container = QWidget()
        self.tab_container.setStyleSheet("background: transparent;")
        self.tab_layout = QHBoxLayout(self.tab_container)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_layout.setSpacing(0)
        self.scroll_area.setWidget(self.tab_container)
        layout.addWidget(self.scroll_area)

        self.right_arrow = QPushButton("\u25B6")
        self.right_arrow.setFixedSize(24, 32)
        self.right_arrow.setStyleSheet(f"QPushButton {{ background: {T['bg2']}; border: none; color: {T['muted']}; font-size: 10px; }} QPushButton:hover {{ color: {T['text']}; }}")
        self.right_arrow.clicked.connect(self._scroll_right)
        self.right_arrow.setVisible(False)
        layout.addWidget(self.right_arrow)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(34, 36)
        add_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; border-left: 1px solid {T['border']};
                          color: {T['muted']}; font-size: 18px; font-weight: 400; }}
            QPushButton:hover {{ background: rgba(255,255,255,0.05); color: {T['text']}; }}
        """)
        add_btn.clicked.connect(self.new_tab.emit)
        layout.addWidget(add_btn)

    def update_tabs(self, open_tabs, active_id, notes_data):
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

    def _scroll_left(self):
        sb = self.scroll_area.horizontalScrollBar()
        sb.setValue(sb.value() - 120)

    def _scroll_right(self):
        sb = self.scroll_area.horizontalScrollBar()
        sb.setValue(sb.value() + 120)

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

    def _build(self):
        # Dark semi-transparent backdrop
        self.setStyleSheet("background: rgba(0,0,0,0.55);")

        # The actual modal card sits centered inside this backdrop widget
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Center container
        center_h = QHBoxLayout()
        center_h.setContentsMargins(0, 0, 0, 0)
        center_h.addStretch(1)

        self.modal = QWidget()
        self.modal.setFixedSize(820, 560)
        self.modal.setStyleSheet(f"""
            QWidget {{
                background: {T['bg']};
                border: 1px solid {T['border']};
                border-radius: 12px;
            }}
        """)

        modal_layout = QVBoxLayout(self.modal)
        modal_layout.setContentsMargins(0, 0, 0, 0)
        modal_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet(f"background: {T['bg']}; border-bottom: 1px solid {T['border']}; border-radius: 12px 12px 0 0;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 12, 0)
        title = QLabel("Einstellungen")
        title.setStyleSheet(f"color: {T['text']}; font-size: 16px; font-weight: 600;")
        hl.addWidget(title)
        hl.addStretch()
        close_btn = QPushButton("\u00D7")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: 1px solid {T['border']}; color: {T['muted']};
                          font-size: 16px; border-radius: 6px; }}
            QPushButton:hover {{ background: {T['bg3']}; color: {T['text']}; }}
        """)
        close_btn.clicked.connect(self._close)
        hl.addWidget(close_btn)
        modal_layout.addWidget(header)

        # Body: categories left, content right
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Category list (Obsidian settings nav)
        self.cat_list = QListWidget()
        self.cat_list.setFixedWidth(190)
        self.cat_list.setStyleSheet(f"""
            QListWidget {{
                background: {T['bg2']}; border: none;
                border-right: 1px solid {T['border']};
                border-radius: 0 0 0 12px;
                padding: 8px 6px;
            }}
            QListWidget::item {{
                padding: 7px 12px; color: {T['muted']}; font-size: 13px;
                border-radius: 4px; margin: 1px 0;
            }}
            QListWidget::item:hover {{ color: {T['text']}; background: rgba(255,255,255,0.06); }}
            QListWidget::item:selected {{
                background: rgba(255,255,255,0.1); color: {T['text']};
                font-weight: 500;
            }}
        """)
        for cat in ["Allgemein", "Darstellung", "KI", "Synchronisation"]:
            self.cat_list.addItem(cat)
        self.cat_list.currentRowChanged.connect(self._on_cat_change)
        body_layout.addWidget(self.cat_list)

        # Stacked pages
        self.pages = QStackedWidget()
        self.pages.setStyleSheet(f"background: {T['bg']}; border-radius: 0 0 12px 0;")
        self._build_general_page()
        self._build_appearance_page()
        self._build_ai_page()
        self._build_sync_page()
        body_layout.addWidget(self.pages)
        modal_layout.addWidget(body)

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

        layout.addStretch()
        self.pages.addWidget(scroll)

    def _on_cat_change(self, index):
        self.pages.setCurrentIndex(index)

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
            ("\U0001F30D Uebersetzen (EN)", "Uebersetze den Text ins Englische."),
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
#  MAIN WINDOW
# ─────────────────────────────────────────────
class NotizenApp(QMainWindow):
    sync_status_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("\u2726 Notizen")
        self.resize(1100, 720)
        self.setMinimumSize(800, 500)

        self.config = load_config()
        self.notes_data = load_notes()
        self.current_note_id = None
        self.open_tabs = list(self.config.get("open_tabs", []))
        self.active_tab_id = None
        self.drive_sync = None
        self._sync_lock = threading.Lock()

        self._apply_theme(self.config.get("theme", "dark"))
        self._build_ui()
        self._refresh_list()
        self._update_tabs()
        self._init_drive()

        # Restore last active tab
        if self.open_tabs:
            self._switch_to_tab(self.open_tabs[0])

        # Auto-save every 5s
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self._save_current)
        self.autosave_timer.start(5000)

        # Auto-sync every 30s fallback (upload)
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._auto_sync)
        self.sync_timer.start(30000)

        # Auto-download every 5s (pick up changes from other devices)
        self.download_timer = QTimer()
        self.download_timer.timeout.connect(self._periodic_download)
        self.download_timer.start(5000)

        # Debounce upload: 2s after last change
        self._upload_debounce = QTimer()
        self._upload_debounce.setSingleShot(True)
        self._upload_debounce.timeout.connect(self._auto_sync)

        self.sync_status_signal.connect(self._update_sync_label)

        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._save_current)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._new_note)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self._close_active_tab)

    def _apply_theme(self, theme_name):
        global T
        T = THEMES.get(theme_name, THEMES["dark"])
        self.setStyleSheet(build_stylesheet())

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
        self.icon_rail.search_clicked.connect(self._show_search)
        self.icon_rail.settings_clicked.connect(self._open_settings)
        self.icon_rail.sync_clicked.connect(self._manual_sync)
        root.addWidget(self.icon_rail)

        # Sidebar
        self.sidebar = SidebarPanel()
        self.sidebar.search_input.textChanged.connect(self._on_search)
        self.sidebar.notes_list.itemClicked.connect(self._on_list_click)
        self.sidebar.notes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sidebar.notes_list.customContextMenuRequested.connect(self._list_context_menu)
        self.sidebar.ai_search_toggle.toggled.connect(self._on_ai_search_toggle)
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

        # Settings Overlay (backdrop over entire central widget)
        self.settings_overlay = SettingsOverlay(central, self.config)
        self.settings_overlay.closed.connect(lambda: None)
        self.settings_overlay.theme_changed.connect(self._on_theme_changed)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"background: {T['bg2']}; color: {T['muted']}; font-size: 12px; border-top: 1px solid {T['border']};")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Keine Notiz ausgewaehlt")

        # Highlight files by default
        self.icon_rail._highlight("files")

    # ── SIDEBAR ──────────────────────────────
    def _toggle_sidebar(self):
        self.sidebar.toggle()

    def _show_files(self):
        if not self.sidebar._expanded:
            self.sidebar.toggle()
        self.sidebar.ai_search_toggle.setChecked(False)

    def _show_search(self):
        if not self.sidebar._expanded:
            self.sidebar.toggle()
        self.sidebar.search_input.setFocus()

    def _on_search(self, text):
        if self.sidebar.ai_search_toggle.isChecked():
            return  # AI search uses enter key
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
        self.sidebar.ai_search_status.setText("\u23F3 Suche laeuft...")
        self.sidebar.ai_search_status.setVisible(True)

        self._ai_search_worker = AISearchWorker(self.config, query, self.notes_data.get("notes", []))
        self._ai_search_worker.result_ready.connect(self._on_ai_search_result)
        self._ai_search_worker.error.connect(self._on_ai_search_error)
        self._ai_search_worker.start()

    def _on_ai_search_result(self, results):
        self.sidebar.ai_search_status.setText(f"\u2713 {len(results)} Treffer")
        result_ids = [r["id"] for r in results if "id" in r]
        self.sidebar.notes_list.clear()
        notes = self.notes_data.get("notes", [])
        for rid in result_ids:
            note = next((n for n in notes if n["id"] == rid), None)
            if not note:
                continue
            item = QListWidgetItem()
            widget = NoteItem(note, is_active=(note["id"] == self.current_note_id))
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, note["id"])
            self.sidebar.notes_list.addItem(item)
            self.sidebar.notes_list.setItemWidget(item, widget)

    def _on_ai_search_error(self, err):
        self.sidebar.ai_search_status.setText(f"Fehler: {err[:50]}")

    # ── NOTES ─────────────────────────────────
    def _refresh_list(self):
        self.sidebar.notes_list.clear()
        query = self.sidebar.search_input.text().lower().strip()
        notes = self.notes_data.get("notes", [])

        if query:
            notes = [n for n in notes if
                     query in n.get("title", "").lower() or
                     query in n.get("content", "").lower()]

        notes = sorted(notes, key=lambda n: n.get("id", ""))

        for note in notes:
            item = QListWidgetItem()
            widget = NoteItem(note, is_active=(note["id"] == self.current_note_id))
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, note["id"])
            self.sidebar.notes_list.addItem(item)
            self.sidebar.notes_list.setItemWidget(item, widget)

    def _on_list_click(self, item):
        note_id = item.data(Qt.ItemDataRole.UserRole)
        self._open_note_in_tab(note_id)

    def _open_note_in_tab(self, note_id):
        if note_id not in self.open_tabs:
            self.open_tabs.append(note_id)
        self._switch_to_tab(note_id)

    def _switch_to_tab(self, note_id):
        self._save_current()
        self.current_note_id = note_id
        self.active_tab_id = note_id
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
            self.notes_data["notes"] = [n for n in self.notes_data["notes"] if n["id"] != note_id]
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

    def _save_current(self):
        if not self.current_note_id:
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
        if self.drive_sync and self.drive_sync.is_connected():
            self._upload_debounce.start(2000)

    def _on_text_changed(self):
        content = self.text_editor.toPlainText()
        words = len(content.split()) if content.strip() else 0
        chars = len(content)
        self.status_bar.showMessage(f"  {words} Woerter  \u00B7  {chars} Zeichen")
        if self.drive_sync and self.drive_sync.is_connected():
            self._upload_debounce.start(2000)

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
        note_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        del_action = QAction("\U0001F5D1  Loeschen", self)
        del_action.triggered.connect(lambda: self._delete_note(note_id))
        menu.addAction(del_action)
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
        self.settings_overlay.show_overlay()
        # Overlay covers the entire central widget (backdrop + centered modal)
        central = self.centralWidget()
        self.settings_overlay.setGeometry(central.rect())
        self.settings_overlay.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.settings_overlay.isVisible():
            central = self.centralWidget()
            self.settings_overlay.setGeometry(central.rect())

    def _on_theme_changed(self, theme_name):
        self._apply_theme(theme_name)
        # Rebuild UI by re-applying stylesheet
        self.setStyleSheet(build_stylesheet())
        QMessageBox.information(self, "Theme", f"Theme auf '{theme_name}' geaendert.\nNeustart empfohlen fuer volle Wirkung.")

    # ── DRIVE SYNC ───────────────────────────
    def _init_drive(self):
        def init():
            self.drive_sync = DriveSync(self.config)
            if self.drive_sync.is_connected():
                self.sync_status_signal.emit(f"\u2713  Drive verbunden", T["accent"])
                self._download_merge()
            else:
                self.sync_status_signal.emit("\u25CF  Drive nicht verbunden", T["muted"])
        threading.Thread(target=init, daemon=True).start()

    def _update_sync_label(self, text, color):
        self.status_bar.showMessage(text)

    def _manual_sync(self):
        if not self.drive_sync or not self.drive_sync.is_connected():
            QMessageBox.information(self, "Sync", "Google Drive nicht verbunden.\nBitte Einstellungen oeffnen.")
            return
        self._save_current()
        self.sync_status_signal.emit("\u27F3  Synchronisiere...", "#ffaa00")
        threading.Thread(target=self._upload_to_drive, daemon=True).start()

    def _auto_sync(self):
        if self.drive_sync and self.drive_sync.is_connected():
            self._save_current()
            threading.Thread(target=self._upload_to_drive, daemon=True).start()

    def _periodic_download(self):
        if self.drive_sync and self.drive_sync.is_connected():
            threading.Thread(target=self._download_merge, daemon=True).start()

    def _upload_to_drive(self):
        with self._sync_lock:
            ok = self.drive_sync.upload(self.notes_data)
            t = datetime.now().strftime("%H:%M")
            if ok:
                self.sync_status_signal.emit(f"\u2713  Synced {t}", T["accent"])
            else:
                self.sync_status_signal.emit("\u26A0  Sync fehlgeschlagen", "#ff4444")

    def _download_merge(self):
        with self._sync_lock:
            remote = self.drive_sync.download()
            if not remote:
                return
            local_by_id = {n["id"]: n for n in self.notes_data.get("notes", [])}
            remote_by_id = {n["id"]: n for n in remote.get("notes", [])}
            merged = {}
            changed = False
            for nid in set(list(local_by_id) + list(remote_by_id)):
                l, r = local_by_id.get(nid), remote_by_id.get(nid)
                if l and r:
                    winner = l if l["modified"] >= r["modified"] else r
                    if winner is r and r["modified"] > l["modified"]:
                        changed = True
                    merged[nid] = winner
                elif r:
                    merged[nid] = r
                    changed = True
                else:
                    merged[nid] = l
            if changed:
                self.notes_data["notes"] = list(merged.values())
                save_notes(self.notes_data)
                from PyQt6.QtCore import QMetaObject
                QMetaObject.invokeMethod(self, "_on_remote_update", Qt.ConnectionType.QueuedConnection)

    def _on_remote_update(self):
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

    def closeEvent(self, event):
        self._save_current()
        self._save_tab_state()
        event.accept()


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = NotizenApp()
    window.show()
    sys.exit(app.exec())
