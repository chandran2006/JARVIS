import sys
import random
import math
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QLinearGradient

# --- Colors ---
PRIMARY_COLOR = QColor("#00FFFF")  # Cyan
ACCENT_COLOR = QColor("#FFFFFF")   # White
BG_COLOR = QColor("#000000")       # Black
WARNING_COLOR = QColor("#FFA500")  # Orange (for Pause)

class HexagonPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.opacity = 50
        self.increasing = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(100) # Update opacity

    def animate(self):
        if self.increasing:
            self.opacity += 5
            if self.opacity >= 200: self.increasing = False
        else:
            self.opacity -= 5
            if self.opacity <= 50: self.increasing = True
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(PRIMARY_COLOR)
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw grid of hexagons
        size = 30
        rows = 4
        cols = 3
        x_offset = 20
        y_offset = 50

        for r in range(rows):
            for c in range(cols):
                color = QColor(PRIMARY_COLOR)
                # Randomize opacity slightly based on position to create "glitch" or wave effect logic could go here
                # For now use global pulsing opacity
                current_opacity = self.opacity
                if (r + c) % 2 == 0:
                   current_opacity = max(50, current_opacity - 50)
                
                color.setAlpha(current_opacity)
                painter.setPen(QPen(color, 2))
                
                x = x_offset + c * (size * 1.5)
                y = y_offset + r * (size * math.sqrt(3))
                if c % 2 == 1:
                    y += size * math.sqrt(3) / 2
                
                self.draw_hexagon(painter, x, y, size)

    def draw_hexagon(self, painter, x, y, size):
        points = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.radians(angle_deg)
            px = x + size * math.cos(angle_rad)
            py = y + size * math.sin(angle_rad)
            points.append(QPointF(px, py))
        painter.drawPolygon(QPolygonF(points))

class TelemetryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.bar_heights = [20, 40, 60, 30]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(100)

    def animate(self):
        # Randomize bar heights
        self.bar_heights = [random.randint(10, 100) for _ in range(4)]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Circuit Lines (Static decoration)
        pen = QPen(ACCENT_COLOR)
        pen.setWidth(2)
        painter.setPen(pen)
        
        path_points = [
            QPointF(10, 200), QPointF(50, 240), QPointF(150, 240), QPointF(180, 200)
        ]
        painter.drawPolyline(QPolygonF(path_points))
        
        # Draw Equalizer
        bar_width = 30
        gap = 10
        start_x = 20
        base_y = 150
        
        painter.setBrush(QBrush(PRIMARY_COLOR))
        painter.setPen(Qt.PenStyle.NoPen)
        
        for i, h in enumerate(self.bar_heights):
            x = start_x + i * (bar_width + gap)
            # Draw bar upwards from base_y
            painter.drawRect(QRectF(x, base_y - h, bar_width, h))


class CentralReactor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle_outer = 0
        self.angle_inner = 0
        self.is_paused = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30) # ~30fps

    def animate(self):
        if not self.is_paused:
            self.angle_outer = (self.angle_outer + 2) % 360  # Clockwise
            self.angle_inner = (self.angle_inner - 4) % 360  # Counter-Clockwise
            self.update()

    def set_paused(self, paused):
        self.is_paused = paused
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Determine Color based on Pause state
        main_color = WARNING_COLOR if self.is_paused else PRIMARY_COLOR
        
        # 1. Draw Core (Solid Circle)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(main_color))
        core_radius = 20
        # Pulse effect for core
        if not self.is_paused:
             pulse = (math.sin(self.angle_outer * 0.1) + 1) * 5
             painter.drawEllipse(QPointF(center_x, center_y), core_radius + pulse, core_radius + pulse)
        else:
             painter.drawEllipse(QPointF(center_x, center_y), core_radius, core_radius)

        painter.setBrush(Qt.BrushStyle.NoBrush)

        # 2. Middle Ring (Thick Segmented)
        pen = QPen(main_color)
        pen.setWidth(12)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        # Dash pattern: [dash_length, space_length, ...]
        pen.setDashPattern([10, 10]) 
        painter.setPen(pen)
        
        radius_mid = 100
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.angle_outer)
        painter.drawEllipse(QPointF(0, 0), radius_mid, radius_mid)
        painter.restore()

        # 3. Inner Ring (Thin Dashed)
        pen = QPen(ACCENT_COLOR) # White
        pen.setWidth(4)
        pen.setDashPattern([5, 5])
        painter.setPen(pen)
        
        radius_inner = 70
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.angle_inner)
        painter.drawEllipse(QPointF(0, 0), radius_inner, radius_inner)
        painter.restore()

        # 4. Outer Bracket (Semi-circles)
        pen = QPen(main_color)
        pen.setWidth(3)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        radius_outer = 130
        
        rect_outer = QRectF(center_x - radius_outer, center_y - radius_outer, 2*radius_outer, 2*radius_outer)
        # Draw two arcs
        start_angle = 30 * 16 # sixteenths of a degree? No, specify in degrees * 16 usually for some QT functions, but drawArc takes startAngle and spanAngle in 1/16th degrees
        # drawArc(rect, int startAngle, int spanAngle)
        # 45 degrees to 135 degrees
        
        painter.drawArc(rect_outer, 45 * 16, 90 * 16)
        painter.drawArc(rect_outer, 225 * 16, 90 * 16)


class JarvisGUI(QMainWindow):
    def __init__(self, pause_event):
        super().__init__()
        self.pause_event = pause_event
        self.is_paused = False
        
        self.setWindowTitle("JARVIS HUD")
        self.resize(1000, 600)
        
        # Frameless and Black Background
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: black;")
        
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left Panel (Hexagons)
        self.left_panel = HexagonPanel()
        main_layout.addWidget(self.left_panel)
        
        # Center (Reactor)
        self.reactor = CentralReactor()
        main_layout.addWidget(self.reactor, stretch=2) # Give center more space
        
        # Right Panel (Telemetry)
        self.right_panel = TelemetryPanel()
        main_layout.addWidget(self.right_panel)
        
        # Click listener shortcut (using mousePressEvent on window)

    def mousePressEvent(self, event):
        # Toggle Pause
        self.toggle_pause()
        
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.reactor.set_paused(self.is_paused)
        
        if self.is_paused:
            self.pause_event.set()
            print("GUI: PAUSED")
        else:
            self.pause_event.clear()
            print("GUI: RESUMED")

    def keyPressEvent(self, event):
        # Allow exiting with ESC
        if event.key() == Qt.Key.Key_Escape:
            self.close()

def run_gui(pause_event):
    app = QApplication(sys.argv)
    window = JarvisGUI(pause_event)
    window.show()
    sys.exit(app.exec())
