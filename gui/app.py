import sys
import math
import random
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel
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

# ── thread → GUI signal bridge ────────────────────────────────────────────────
class _Bridge(QObject):
    sig_status = pyqtSignal(str)
    sig_text   = pyqtSignal(str)

_bridge = _Bridge()

def gui_set_status(s: str): _bridge.sig_status.emit(s)
def gui_set_text(t: str):   _bridge.sig_text.emit(t)

# ── hexagon side panel ────────────────────────────────────────────────────────
class HexPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self._hexes = [
            {"r": r, "c": c,
             "a": random.randint(20, 160),
             "spd": random.uniform(1.2, 4.5),
             "up": random.choice([True, False])}
            for r in range(7) for c in range(3)
        ]
        self._col = C["IDLE"]
        QTimer(self).timeout.connect(self._tick) or None
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
        sz, ox, oy = 28, 20, 30
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
        self.setFixedHeight(55)
        self._bars   = [0] * 32
        self._active = False
        self._col    = C["IDLE"]
        t = QTimer(self); t.timeout.connect(self._tick); t.start(40)

    def set_active(self, v: bool, col: QColor = None):
        self._active = v
        if col: self._col = col

    def _tick(self):
        if self._active:
            self._bars = [random.randint(5, 50) for _ in self._bars]
        else:
            self._bars = [max(0, b - 5) for b in self._bars]
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 320)
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

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        col = C["PAUSED"] if self._paused else C.get(self._status, C["IDLE"])

        # glow
        gr = QRadialGradient(cx, cy, 100)
        gc = QColor(col); gc.setAlpha(50)
        gr.setColorAt(0, gc); gr.setColorAt(1, QColor(0,0,0,0))
        p.setBrush(QBrush(gr)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), 140, 140)

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
        pulse = math.sin(self._phase) * 5 if not self._paused else 0
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(col))
        p.drawEllipse(QPointF(cx, cy), 20 + pulse, 20 + pulse)

        # state label
        p.setPen(QPen(C["black"]))
        f = QFont("Consolas", 7, QFont.Weight.Bold); p.setFont(f)
        p.drawText(QRectF(cx-40, cy+24, 80, 16),
                   Qt.AlignmentFlag.AlignCenter, self._status)

# ── main window ───────────────────────────────────────────────────────────────
class JarvisGUI(QMainWindow):
    def __init__(self, pause_event):
        super().__init__()
        self.pause_event = pause_event
        self._paused     = False
        self._status     = "IDLE"

        self.setWindowTitle("JARVIS")
        self.resize(1100, 660)
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
            "font-size:11px;padding:6px;")
        vbox.addWidget(self._top)

        # ── main row ──────────────────────────────────────────────────────────
        row = QHBoxLayout(); row.setSpacing(0)
        self._hex_l  = HexPanel()
        self._reactor = Reactor()
        self._hex_r  = HexPanel()
        row.addWidget(self._hex_l)
        row.addWidget(self._reactor, stretch=2)
        row.addWidget(self._hex_r)
        vbox.addLayout(row, stretch=1)

        # ── voice bars ────────────────────────────────────────────────────────
        self._bars = VoiceBars()
        vbox.addWidget(self._bars)

        # ── last heard ────────────────────────────────────────────────────────
        self._heard = QLabel("...")
        self._heard.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._heard.setStyleSheet(
            "color:#006666;font-family:Consolas;font-size:11px;"
            "background:transparent;padding:2px;")
        vbox.addWidget(self._heard)

        # ── transcript ────────────────────────────────────────────────────────
        self._transcript = QLabel("JARVIS ONLINE")
        self._transcript.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._transcript.setWordWrap(True)
        self._transcript.setMaximumHeight(70)
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

        self._drag_pos = None

    def _update_top(self):
        now   = datetime.now().strftime("%H:%M:%S")
        state = "PAUSED" if self._paused else self._status
        self._top.setText(
            f"JARVIS  |  {now}  |  {state}  |  SPACE=Pause  ESC=Quit")

    def _on_status(self, s: str):
        self._status = s
        col = C.get(s, C["IDLE"])
        self._reactor.set_status(s)
        self._bars.set_active(s == "LISTENING", col)
        self._hex_l.set_color(col)
        self._hex_r.set_color(col)
        self._update_top()

    def _on_text(self, t: str):
        self._transcript.setText(t[:130] + ("..." if len(t) > 130 else ""))

    def _toggle_pause(self):
        self._paused = not self._paused
        self._reactor.set_paused(self._paused)
        if self._paused:
            self.pause_event.set()
        else:
            self.pause_event.clear()
        self._update_top()

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

def run_gui(pause_event):
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = JarvisGUI(pause_event)
    win.show()
    sys.exit(app.exec())
