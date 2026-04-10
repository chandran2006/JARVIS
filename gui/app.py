import sys
import math
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel,
)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal, QObject
from PyQt6.QtGui  import (
    QPainter, QColor, QPen, QBrush,
    QPolygonF, QLinearGradient, QRadialGradient, QFont,
)

# ── Colours ───────────────────────────────────────────────────────────────────
C_CYAN    = QColor("#00FFFF")
C_WHITE   = QColor("#FFFFFF")
C_BLACK   = QColor("#000000")
C_ORANGE  = QColor("#FFA500")
C_GREEN   = QColor("#00FF88")
C_DIM     = QColor("#003333")

# ── Signal bridge (lets background thread update GUI) ─────────────────────────
class _Bridge(QObject):
    set_status   = pyqtSignal(str)   # "LISTENING" | "THINKING" | "SPEAKING" | "IDLE"
    set_text     = pyqtSignal(str)   # last spoken line

_bridge = _Bridge()

def gui_set_status(status: str):
    _bridge.set_status.emit(status)

def gui_set_text(text: str):
    _bridge.set_text.emit(text)

# ── Hexagon panel ─────────────────────────────────────────────────────────────
class HexPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        self._hexes = [
            {"r": r, "c": c,
             "alpha": random.randint(30, 180),
             "speed": random.uniform(1.5, 5),
             "up":    random.choice([True, False])}
            for r in range(6) for c in range(3)
        ]
        t = QTimer(self); t.timeout.connect(self._tick); t.start(60)

    def _tick(self):
        for h in self._hexes:
            h["alpha"] += h["speed"] if h["up"] else -h["speed"]
            if h["alpha"] >= 200: h["up"] = False
            if h["alpha"] <= 25:  h["up"] = True
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        sz, ox, oy = 32, 28, 40
        for h in self._hexes:
            c = QColor(C_CYAN); c.setAlpha(int(h["alpha"]))
            p.setPen(QPen(c, 1.5))
            x = ox + h["c"] * sz * 1.55
            y = oy + h["r"] * sz * 1.73
            if h["c"] % 2: y += sz * 0.87
            pts = [QPointF(x + sz * math.cos(math.radians(60*i)),
                           y + sz * math.sin(math.radians(60*i)))
                   for i in range(6)]
            p.drawPolygon(QPolygonF(pts))

# ── Voice bar visualiser ──────────────────────────────────────────────────────
class VoiceBars(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self._bars  = [0] * 28
        self._active = False
        t = QTimer(self); t.timeout.connect(self._tick); t.start(45)

    def set_active(self, v: bool): self._active = v

    def _tick(self):
        if self._active:
            self._bars = [random.randint(8, 55) for _ in self._bars]
        else:
            self._bars = [max(0, b - 6) for b in self._bars]
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width() / len(self._bars)
        for i, h in enumerate(self._bars):
            grad = QLinearGradient(0, self.height() - h, 0, self.height())
            grad.setColorAt(0, C_CYAN)
            grad.setColorAt(1, QColor("#004466"))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(
                QRectF(i * w + 1, self.height() - h, w - 2, h), 2, 2
            )

# ── Central reactor ───────────────────────────────────────────────────────────
class Reactor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(340, 340)
        self._a1 = self._a2 = self._a3 = 0.0
        self._phase  = 0.0
        self._paused = False
        self._status = "IDLE"   # IDLE | LISTENING | THINKING | SPEAKING
        t = QTimer(self); t.timeout.connect(self._tick); t.start(28)

    def set_paused(self, v: bool): self._paused = v; self.update()
    def set_status(self, s: str):  self._status = s; self.update()

    def _tick(self):
        if not self._paused:
            self._a1  = (self._a1 + 0.8)  % 360
            self._a2  = (self._a2 - 1.4)  % 360
            self._a3  = (self._a3 + 2.1)  % 360
            self._phase = (self._phase + 0.07) % (2 * math.pi)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2

        # colour by state
        col = {
            "IDLE":      C_CYAN,
            "LISTENING": C_GREEN,
            "THINKING":  C_ORANGE,
            "SPEAKING":  QColor("#FF66FF"),
        }.get(self._status, C_CYAN)
        if self._paused: col = C_ORANGE

        # glow
        gr = QRadialGradient(cx, cy, 90)
        gc = QColor(col); gc.setAlpha(60)
        gr.setColorAt(0, gc); gr.setColorAt(1, QColor(0,0,0,0))
        p.setBrush(QBrush(gr)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), 130, 130)

        # outer bracket arcs
        pen = QPen(col, 3); p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        r = QRectF(cx-145, cy-145, 290, 290)
        for start in (20, 110, 200, 290):
            p.drawArc(r, start*16, 70*16)

        # ring 3 (outermost spinning)
        pen = QPen(col, 9); pen.setDashPattern([18, 12]); p.setPen(pen)
        p.save(); p.translate(cx, cy); p.rotate(self._a1)
        p.drawEllipse(QPointF(0,0), 115, 115); p.restore()

        # ring 2
        pen = QPen(C_WHITE, 3); pen.setDashPattern([8, 8]); p.setPen(pen)
        p.save(); p.translate(cx, cy); p.rotate(self._a2)
        p.drawEllipse(QPointF(0,0), 82, 82); p.restore()

        # ring 1 (innermost)
        pen = QPen(col, 5); pen.setDashPattern([12, 8]); p.setPen(pen)
        p.save(); p.translate(cx, cy); p.rotate(self._a3)
        p.drawEllipse(QPointF(0,0), 55, 55); p.restore()

        # core pulse
        pulse = math.sin(self._phase) * 6 if not self._paused else 0
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(col))
        p.drawEllipse(QPointF(cx, cy), 22 + pulse, 22 + pulse)

        # status label inside reactor
        p.setPen(QPen(C_BLACK))
        font = QFont("Consolas", 8, QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(QRectF(cx-40, cy+28, 80, 18),
                   Qt.AlignmentFlag.AlignCenter, self._status)

# ── Transcript label ──────────────────────────────────────────────────────────
class Transcript(QLabel):
    def __init__(self, parent=None):
        super().__init__("JARVIS ONLINE", parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setMaximumHeight(80)
        self.setStyleSheet(
            "color: #00FFFF; font-family: Consolas; font-size: 13px;"
            "background: transparent; padding: 4px;"
        )

# ── Main window ───────────────────────────────────────────────────────────────
class JarvisGUI(QMainWindow):
    def __init__(self, pause_event):
        super().__init__()
        self.pause_event = pause_event
        self._paused = False

        self.setWindowTitle("JARVIS")
        self.resize(1100, 620)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: #000000;")

        # ── layout ────────────────────────────────────────────────────────────
        root = QWidget(); self.setCentralWidget(root)
        vbox = QVBoxLayout(root); vbox.setContentsMargins(0, 0, 0, 0); vbox.setSpacing(0)

        # top status bar
        self._status_lbl = QLabel("● ONLINE  |  VOICE MODE  |  PRESS SPACE TO PAUSE")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setStyleSheet(
            "color:#00FFFF; background:#001111; font-family:Consolas;"
            "font-size:11px; padding:5px;"
        )
        vbox.addWidget(self._status_lbl)

        # main row
        row = QHBoxLayout(); row.setSpacing(0)
        self._hex_l  = HexPanel()
        self._reactor = Reactor()
        self._hex_r  = HexPanel()
        row.addWidget(self._hex_l)
        row.addWidget(self._reactor, stretch=2)
        row.addWidget(self._hex_r)
        vbox.addLayout(row, stretch=1)

        # voice bars
        self._bars = VoiceBars()
        vbox.addWidget(self._bars)

        # transcript
        self._transcript = Transcript()
        vbox.addWidget(self._transcript)

        # ── connect bridge signals ─────────────────────────────────────────────
        _bridge.set_status.connect(self._on_status)
        _bridge.set_text.connect(self._on_text)

        # ── drag support ──────────────────────────────────────────────────────
        self._drag_pos = None

    # ── bridge slots ──────────────────────────────────────────────────────────
    def _on_status(self, s: str):
        self._reactor.set_status(s)
        self._bars.set_active(s == "LISTENING")
        self._status_lbl.setText(
            f"● {s}  |  {'PAUSED' if self._paused else 'ACTIVE'}  |  SPACE = PAUSE  |  ESC = QUIT"
        )

    def _on_text(self, t: str):
        # Trim to ~120 chars for display
        self._transcript.setText(t[:120] + ("…" if len(t) > 120 else ""))

    # ── pause toggle ──────────────────────────────────────────────────────────
    def _toggle_pause(self):
        self._paused = not self._paused
        self._reactor.set_paused(self._paused)
        if self._paused:
            self.pause_event.set()
            self._reactor.set_status("IDLE")
        else:
            self.pause_event.clear()
            self._reactor.set_status("IDLE")

    # ── events ────────────────────────────────────────────────────────────────
    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.close()
        elif e.key() == Qt.Key.Key_Space:
            self._toggle_pause()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None

# ── public launcher ───────────────────────────────────────────────────────────
def run_gui(pause_event):
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = JarvisGUI(pause_event)
    win.show()
    sys.exit(app.exec())
