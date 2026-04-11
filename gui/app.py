import sys
import math
import random
import threading
import urllib.parse
import requests
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                              QVBoxLayout, QLabel, QPushButton, QListWidget,
                              QListWidgetItem, QSizePolicy)
from PyQt6.QtCore    import Qt, QTimer, QPointF, QRectF, pyqtSignal, QObject
from PyQt6.QtGui     import QPainter, QColor, QPen, QBrush, QPolygonF, QLinearGradient, QRadialGradient, QFont

# ── colours ───────────────────────────────────────────────────────────────────
C = {
    "IDLE":      QColor("#00FFFF"),
    "LISTENING": QColor("#00FF88"),
    "THINKING":  QColor("#FFA500"),
    "SPEAKING":  QColor("#CC88FF"),
    "PAUSED":    QColor("#FF4444"),
    "white":     QColor("#FFFFFF"),
    "black":     QColor("#000000"),
    "dim":       QColor("#003333"),
}

_LABEL_STYLE = {
    "IDLE":      "color:#00FFFF;",
    "LISTENING": "color:#00FF88;",
    "THINKING":  "color:#FFA500;",
    "SPEAKING":  "color:#CC88FF;",
    "PAUSED":    "color:#FF4444;",
}

# ── thread → GUI signal bridge ────────────────────────────────────────────────
class _Bridge(QObject):
    sig_status = pyqtSignal(str)
    sig_text   = pyqtSignal(str)
    sig_ticker = pyqtSignal(str)

_bridge = _Bridge()

def gui_set_status(s: str): _bridge.sig_status.emit(s)
def gui_set_text(t: str):   _bridge.sig_text.emit(t)

# ── live ticker data fetcher ──────────────────────────────────────────────────
_TICKER_SYMBOLS = {
    "Gold":    "GC=F",
    "Silver":  "SI=F",
    "Nifty":   "^NSEI",
    "Sensex":  "^BSESN",
    "S&P500":  "^GSPC",
    "Nasdaq":  "^IXIC",
    "Crude":   "CL=F",
}

# Symbols priced in USD that need INR conversion
_USD_SYMBOLS = {"Gold", "Silver", "Crude", "S&P500", "Nasdaq"}

def _get_usd_inr() -> float:
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD",
                         timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        return r.json().get("rates", {}).get("INR", 84.0)
    except Exception:
        return 84.0

def _inr_fmt(value: float) -> str:
    """Format a rupee value in Indian style: crore / lakh / thousand."""
    if value >= 1_00_00_000:
        return f"\u20b9{value/1_00_00_000:.2f}Cr"
    if value >= 1_00_000:
        return f"\u20b9{value/1_00_000:.2f}L"
    if value >= 1_000:
        return f"\u20b9{value/1_000:.2f}K"
    return f"\u20b9{value:,.2f}"

def _fetch_ticker() -> str:
    usd_inr = _get_usd_inr()
    parts = []
    for label, sym in _TICKER_SYMBOLS.items():
        try:
            r = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}",
                params={"interval": "1d", "range": "1d"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=5
            )
            if r.status_code == 200:
                meta  = r.json()["chart"]["result"][0]["meta"]
                price = meta.get("regularMarketPrice", 0)
                prev  = meta.get("chartPreviousClose", price)
                pct   = ((price - prev) / prev * 100) if prev else 0
                arrow = "\u25b2" if pct >= 0 else "\u25bc"
                # Convert USD-priced assets to INR
                inr_price = price * usd_inr if label in _USD_SYMBOLS else price
                parts.append(f"{label}: {_inr_fmt(inr_price)}  {arrow}{abs(pct):.2f}%")
        except Exception:
            pass
    return "     \u25c6     ".join(parts) if parts else ""

def _ticker_worker():
    """Background thread: fetch prices every 60 s and push to GUI."""
    while True:
        try:
            text = _fetch_ticker()
            if text:
                _bridge.sig_ticker.emit(text)
        except Exception:
            pass
        threading.Event().wait(60)   # refresh every 60 seconds

# Start ticker thread once at import time
_ticker_thread = threading.Thread(target=_ticker_worker, daemon=True)
_ticker_thread.start()

# ── hexagon side panel ────────────────────────────────────────────────────────
class HexPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(180)
        self._hexes = [
            {"r": r, "c": c,
             "a": random.randint(20, 160),
             "spd": random.uniform(1.2, 4.5),
             "up": random.choice([True, False])}
            for r in range(7) for c in range(3)
        ]
        self._col = C["IDLE"]
        t = QTimer(self); t.timeout.connect(self._tick); t.start(55)

    def set_color(self, col: QColor): self._col = col

    def _tick(self):
        for h in self._hexes:
            h["a"] += h["spd"] if h["up"] else -h["spd"]
            if h["a"] >= 180: h["up"] = False
            if h["a"] <= 15:  h["up"] = True
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        sz, ox, oy = 26, 18, 30
        for h in self._hexes:
            col = QColor(self._col); col.setAlpha(int(h["a"]))
            p.setPen(QPen(col, 1.2))
            x = ox + h["c"] * sz * 1.55
            y = oy + h["r"] * sz * 1.73
            if h["c"] % 2: y += sz * 0.87
            pts = [QPointF(x + sz * math.cos(math.radians(60*i)),
                           y + sz * math.sin(math.radians(60*i)))
                   for i in range(6)]
            p.drawPolygon(QPolygonF(pts))

# ── voice bar visualiser ──────────────────────────────────────────────────────
class VoiceBars(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self._bars   = [0] * 40
        self._active = False
        self._col    = C["IDLE"]
        t = QTimer(self); t.timeout.connect(self._tick); t.start(35)

    def set_active(self, v: bool, col: QColor = None):
        self._active = v
        if col: self._col = col

    def _tick(self):
        if self._active:
            self._bars = [random.randint(5, 48) for _ in self._bars]
        else:
            self._bars = [max(0, b - 4) for b in self._bars]
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width() / len(self._bars)
        for i, h in enumerate(self._bars):
            g = QLinearGradient(0, self.height() - h, 0, self.height())
            g.setColorAt(0, self._col)
            g.setColorAt(1, QColor(0, 40, 60))
            p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(i*w+1, self.height()-h, w-2, h), 2, 2)

# ── arc reactor ───────────────────────────────────────────────────────────────
class Reactor(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self._a1 = self._a2 = self._a3 = 0.0
        self._phase  = 0.0
        self._status = "IDLE"
        self._paused = False
        t = QTimer(self); t.timeout.connect(self._tick); t.start(25)

    def set_status(self, s: str): self._status = s
    def set_paused(self, v: bool): self._paused = v

    def _tick(self):
        if not self._paused:
            self._a1  = (self._a1 + 0.7)  % 360
            self._a2  = (self._a2 - 1.3)  % 360
            self._a3  = (self._a3 + 2.0)  % 360
            self._phase = (self._phase + 0.06) % (2 * math.pi)
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        col = C["PAUSED"] if self._paused else C.get(self._status, C["IDLE"])

        # glow
        gr = QRadialGradient(cx, cy, 110)
        gc = QColor(col); gc.setAlpha(55)
        gr.setColorAt(0, gc); gr.setColorAt(1, QColor(0,0,0,0))
        p.setBrush(QBrush(gr)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), 145, 145)

        p.setBrush(Qt.BrushStyle.NoBrush)

        # outer bracket arcs
        p.setPen(QPen(col, 2))
        r0 = QRectF(cx-148, cy-148, 296, 296)
        for s in (15, 105, 195, 285):
            p.drawArc(r0, s*16, 75*16)

        # ring 3
        pen = QPen(col, 8); pen.setDashPattern([16, 10]); p.setPen(pen)
        p.save(); p.translate(cx, cy); p.rotate(self._a1)
        p.drawEllipse(QPointF(0,0), 118, 118); p.restore()

        # ring 2
        pen = QPen(C["white"], 2); pen.setDashPattern([7, 7]); p.setPen(pen)
        p.save(); p.translate(cx, cy); p.rotate(self._a2)
        p.drawEllipse(QPointF(0,0), 85, 85); p.restore()

        # ring 1
        pen = QPen(col, 4); pen.setDashPattern([10, 7]); p.setPen(pen)
        p.save(); p.translate(cx, cy); p.rotate(self._a3)
        p.drawEllipse(QPointF(0,0), 57, 57); p.restore()

        # core
        pulse = math.sin(self._phase) * 6 if not self._paused else 0
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(col))
        p.drawEllipse(QPointF(cx, cy), 22 + pulse, 22 + pulse)

        # state label
        p.setPen(QPen(C["black"]))
        f = QFont("Consolas", 7, QFont.Weight.Bold); p.setFont(f)
        p.drawText(QRectF(cx-40, cy+26, 80, 16),
                   Qt.AlignmentFlag.AlignCenter, self._status)

# ── command history panel ─────────────────────────────────────────────────────
class HistoryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(4)

        title = QLabel("COMMAND LOG")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#004444;font-family:Consolas;font-size:9px;")
        layout.addWidget(title)

        self._list = QListWidget()
        self._list.setStyleSheet(
            "QListWidget{background:#000000;border:1px solid #003333;"
            "color:#00AAAA;font-family:Consolas;font-size:9px;}"
            "QListWidget::item{padding:2px;border-bottom:1px solid #001111;}"
            "QScrollBar:vertical{background:#001111;width:6px;}"
            "QScrollBar::handle:vertical{background:#003333;}")
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self._list)

    def add_entry(self, role: str, text: str):
        prefix = "YOU" if role == "user" else "JAR"
        col    = "#00FF88" if role == "user" else "#CC88FF"
        item   = QListWidgetItem(f"[{prefix}] {text[:40]}")
        item.setForeground(QColor(col))
        self._list.addItem(item)
        self._list.scrollToBottom()
        # Keep max 50 entries
        while self._list.count() > 50:
            self._list.takeItem(0)

# ── main window ───────────────────────────────────────────────────────────────
class JarvisGUI(QMainWindow):
    def __init__(self, pause_event):
        super().__init__()
        self.pause_event = pause_event
        self._paused     = False
        self._status     = "IDLE"

        self.setWindowTitle("JARVIS")
        self.resize(1200, 700)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color:#000000;")

        root = QWidget(); self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0); vbox.setSpacing(0)

        # ── top bar ───────────────────────────────────────────────────────────
        self._top = QLabel()
        self._top.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._top.setStyleSheet(
            "color:#00FFFF;background:#001111;font-family:Consolas;"
            "font-size:11px;padding:6px;letter-spacing:1px;")
        vbox.addWidget(self._top)

        # ── live ticker bar ───────────────────────────────────────────────────
        self._ticker_label = QLabel("  ⟳ Loading live prices...")
        self._ticker_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._ticker_label.setStyleSheet(
            "color:#FFD700;background:#0a0a00;font-family:Consolas;"
            "font-size:10px;padding:3px 8px;border-bottom:1px solid #333300;")
        vbox.addWidget(self._ticker_label)

        # Scroll ticker text left every 40 ms
        self._ticker_text  = ""
        self._ticker_offset = 0
        self._scroll_timer  = QTimer(self)
        self._scroll_timer.timeout.connect(self._scroll_ticker)
        self._scroll_timer.start(50)

        # ── main row ──────────────────────────────────────────────────────────
        row = QHBoxLayout(); row.setSpacing(0)
        self._hex_l   = HexPanel()
        self._reactor = Reactor()
        self._reactor.clicked.connect(self._toggle_pause)
        self._hex_r   = HexPanel()
        self._history = HistoryPanel()

        row.addWidget(self._hex_l)
        row.addWidget(self._reactor, stretch=2)
        row.addWidget(self._hex_r)
        row.addWidget(self._history)
        vbox.addLayout(row, stretch=1)

        # ── voice bars ────────────────────────────────────────────────────────
        self._bars = VoiceBars()
        vbox.addWidget(self._bars)

        # ── status row ────────────────────────────────────────────────────────
        status_row = QHBoxLayout()
        status_row.setContentsMargins(8, 2, 8, 2)

        self._status_label = QLabel("● IDLE")
        self._status_label.setStyleSheet("color:#00FFFF;font-family:Consolas;font-size:11px;")
        status_row.addWidget(self._status_label)

        status_row.addStretch()

        # Interrupt button
        self._btn_interrupt = QPushButton("■ STOP")
        self._btn_interrupt.setFixedSize(80, 24)
        self._btn_interrupt.setStyleSheet(
            "QPushButton{background:#1a0000;color:#FF4444;border:1px solid #FF4444;"
            "font-family:Consolas;font-size:10px;border-radius:3px;}"
            "QPushButton:hover{background:#330000;}")
        self._btn_interrupt.clicked.connect(self._interrupt)
        status_row.addWidget(self._btn_interrupt)

        # Pause button
        self._btn_pause = QPushButton("⏸ PAUSE")
        self._btn_pause.setFixedSize(80, 24)
        self._btn_pause.setStyleSheet(
            "QPushButton{background:#001a1a;color:#00FFFF;border:1px solid #00FFFF;"
            "font-family:Consolas;font-size:10px;border-radius:3px;}"
            "QPushButton:hover{background:#003333;}")
        self._btn_pause.clicked.connect(self._toggle_pause)
        status_row.addWidget(self._btn_pause)

        vbox.addLayout(status_row)

        # ── transcript ────────────────────────────────────────────────────────
        self._transcript = QLabel("JARVIS ONLINE — READY")
        self._transcript.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._transcript.setWordWrap(True)
        self._transcript.setMaximumHeight(65)
        self._transcript.setStyleSheet(
            "color:#00FFFF;font-family:Consolas;font-size:13px;"
            "background:transparent;padding:4px;")
        vbox.addWidget(self._transcript)

        # ── clock timer ───────────────────────────────────────────────────────
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_top)
        self._clock_timer.start(1000)
        self._update_top()

        # ── signals ───────────────────────────────────────────────────────────
        _bridge.sig_status.connect(self._on_status)
        _bridge.sig_text.connect(self._on_text)
        _bridge.sig_ticker.connect(self._on_ticker)

        self._drag_pos = None
        self._last_text = ""

    def _on_ticker(self, text: str):
        self._ticker_text   = text + "          "
        self._ticker_offset = 0

    def _scroll_ticker(self):
        if not self._ticker_text:
            return
        display = self._ticker_text[self._ticker_offset:] + "   " + self._ticker_text[:self._ticker_offset]
        self._ticker_label.setText(display[:120])
        self._ticker_offset = (self._ticker_offset + 1) % len(self._ticker_text)

    def _update_top(self):
        now   = datetime.now().strftime("%A  %H:%M:%S")
        state = "PAUSED" if self._paused else self._status
        self._top.setText(
            f"J.A.R.V.I.S  ◆  {now}  ◆  {state}  ◆  SPACE=Pause  I=Interrupt  ESC=Quit")

    def _on_status(self, s: str):
        self._status = s
        col = C.get(s, C["IDLE"])
        self._reactor.set_status(s)
        self._bars.set_active(s in ("LISTENING", "SPEAKING"), col)
        self._hex_l.set_color(col)
        self._hex_r.set_color(col)
        style = _LABEL_STYLE.get(s, "color:#00FFFF;")
        self._status_label.setStyleSheet(f"{style}font-family:Consolas;font-size:11px;")
        self._status_label.setText(f"● {s}")
        self._update_top()

    def _on_text(self, t: str):
        self._transcript.setText(t[:140] + ("..." if len(t) > 140 else ""))
        # Add to history — detect role by checking if it changed
        if t != self._last_text:
            role = "jarvis" if self._status in ("SPEAKING", "THINKING") else "user"
            self._history.add_entry(role, t)
            self._last_text = t

    def _toggle_pause(self):
        self._paused = not self._paused
        self._reactor.set_paused(self._paused)
        if self._paused:
            self.pause_event.set()
            self._btn_pause.setText("▶ RESUME")
        else:
            self.pause_event.clear()
            self._btn_pause.setText("⏸ PAUSE")
        self._update_top()

    def _interrupt(self):
        try:
            from core.voice import interrupt_speech
            interrupt_speech()
        except Exception:
            pass

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.close()
        elif e.key() == Qt.Key.Key_Space:
            self._toggle_pause()
        elif e.key() == Qt.Key.Key_I:
            self._interrupt()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None


def run_gui(pause_event):
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = JarvisGUI(pause_event)
    win.show()
    sys.exit(app.exec())
