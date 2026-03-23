import sys
import random
import math
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QLabel, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QPolygonF, 
                        QLinearGradient, QRadialGradient, QIcon, QPixmap, QAction)

# Theme System
class Theme:
    STARK = {
        "primary": QColor("#00FFFF"),
        "accent": QColor("#FFFFFF"),
        "bg": QColor("#000000"),
        "warning": QColor("#FFA500"),
        "success": QColor("#00FF00"),
        "error": QColor("#FF0000")
    }
    
    ULTRON = {
        "primary": QColor("#FF0000"),
        "accent": QColor("#8B0000"),
        "bg": QColor("#1A0000"),
        "warning": QColor("#FF4500"),
        "success": QColor("#FFD700"),
        "error": QColor("#8B0000")
    }
    
    VISION = {
        "primary": QColor("#FFD700"),
        "accent": QColor("#FFA500"),
        "bg": QColor("#0A0A0A"),
        "warning": QColor("#FF8C00"),
        "success": QColor("#32CD32"),
        "error": QColor("#DC143C")
    }

class VoiceVisualizer(QWidget):
    """Real-time voice activity visualization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.bars = [0] * 32
        self.is_active = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)
    
    def set_active(self, active: bool):
        self.is_active = active
    
    def animate(self):
        if self.is_active:
            self.bars = [random.randint(20, 100) for _ in range(32)]
        else:
            self.bars = [max(0, b - 10) for b in self.bars]
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        bar_width = width / len(self.bars)
        
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#00FFFF"))
        gradient.setColorAt(1, QColor("#0080FF"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        
        for i, height in enumerate(self.bars):
            x = i * bar_width
            y = self.height() - height
            painter.drawRect(int(x), int(y), int(bar_width - 2), int(height))

class EnhancedHexagonPanel(QWidget):
    """Enhanced hexagon panel with depth and glow effects."""
    
    def __init__(self, parent=None, theme=Theme.STARK):
        super().__init__(parent)
        self.theme = theme
        self.setMinimumWidth(250)
        self.hexagons = []
        self.init_hexagons()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)
    
    def init_hexagons(self):
        for r in range(5):
            for c in range(3):
                self.hexagons.append({
                    "row": r,
                    "col": c,
                    "opacity": random.randint(50, 200),
                    "speed": random.uniform(2, 8),
                    "increasing": random.choice([True, False])
                })
    
    def animate(self):
        for hex_data in self.hexagons:
            if hex_data["increasing"]:
                hex_data["opacity"] += hex_data["speed"]
                if hex_data["opacity"] >= 255:
                    hex_data["increasing"] = False
            else:
                hex_data["opacity"] -= hex_data["speed"]
                if hex_data["opacity"] <= 30:
                    hex_data["increasing"] = True
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        size = 35
        x_offset = 30
        y_offset = 60
        
        for hex_data in self.hexagons:
            r, c = hex_data["row"], hex_data["col"]
            
            color = QColor(self.theme["primary"])
            color.setAlpha(int(hex_data["opacity"]))
            
            painter.setPen(QPen(color, 2))
            
            x = x_offset + c * (size * 1.5)
            y = y_offset + r * (size * math.sqrt(3))
            if c % 2 == 1:
                y += size * math.sqrt(3) / 2
            
            self.draw_hexagon(painter, x, y, size)
    
    def draw_hexagon(self, painter, x, y, size):
        points = []
        for i in range(6):
            angle_rad = math.radians(60 * i)
            px = x + size * math.cos(angle_rad)
            py = y + size * math.sin(angle_rad)
            points.append(QPointF(px, py))
        painter.drawPolygon(QPolygonF(points))

class EnhancedReactor(QWidget):
    """Enhanced arc reactor with multiple layers and effects."""
    
    def __init__(self, parent=None, theme=Theme.STARK):
        super().__init__(parent)
        self.theme = theme
        self.angle_outer = 0
        self.angle_middle = 0
        self.angle_inner = 0
        self.is_paused = False
        self.pulse_phase = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
    
    def animate(self):
        if not self.is_paused:
            self.angle_outer = (self.angle_outer + 1) % 360
            self.angle_middle = (self.angle_middle - 2) % 360
            self.angle_inner = (self.angle_inner + 3) % 360
            self.pulse_phase = (self.pulse_phase + 0.1) % (2 * math.pi)
        self.update()
    
    def set_paused(self, paused):
        self.is_paused = paused
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        main_color = self.theme["warning"] if self.is_paused else self.theme["primary"]
        
        # Glow effect
        if not self.is_paused:
            glow_radius = 40 + math.sin(self.pulse_phase) * 10
            gradient = QRadialGradient(center_x, center_y, glow_radius)
            gradient.setColorAt(0, QColor(main_color.red(), main_color.green(), main_color.blue(), 100))
            gradient.setColorAt(1, QColor(main_color.red(), main_color.green(), main_color.blue(), 0))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(center_x, center_y), glow_radius * 2, glow_radius * 2)
        
        # Core
        painter.setBrush(QBrush(main_color))
        core_radius = 25 + (math.sin(self.pulse_phase) * 5 if not self.is_paused else 0)
        painter.drawEllipse(QPointF(center_x, center_y), core_radius, core_radius)
        
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Inner ring
        pen = QPen(self.theme["accent"], 3)
        pen.setDashPattern([5, 5])
        painter.setPen(pen)
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.angle_inner)
        painter.drawEllipse(QPointF(0, 0), 60, 60)
        painter.restore()
        
        # Middle ring
        pen = QPen(main_color, 8)
        pen.setDashPattern([15, 10])
        painter.setPen(pen)
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.angle_middle)
        painter.drawEllipse(QPointF(0, 0), 90, 90)
        painter.restore()
        
        # Outer ring
        pen = QPen(main_color, 10)
        pen.setDashPattern([20, 15])
        painter.setPen(pen)
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.angle_outer)
        painter.drawEllipse(QPointF(0, 0), 120, 120)
        painter.restore()
        
        # Outer brackets
        pen = QPen(main_color, 4)
        painter.setPen(pen)
        rect_outer = QRectF(center_x - 140, center_y - 140, 280, 280)
        painter.drawArc(rect_outer, 30 * 16, 60 * 16)
        painter.drawArc(rect_outer, 120 * 16, 60 * 16)
        painter.drawArc(rect_outer, 210 * 16, 60 * 16)
        painter.drawArc(rect_outer, 300 * 16, 60 * 16)

class StatusBar(QWidget):
    """Status bar showing system information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(40)
        layout = QHBoxLayout(self)
        
        self.status_label = QLabel("● ONLINE")
        self.status_label.setStyleSheet("color: #00FF00; font-size: 14px; font-weight: bold;")
        
        self.mode_label = QLabel("MODE: VOICE")
        self.mode_label.setStyleSheet("color: #00FFFF; font-size: 12px;")
        
        self.skills_label = QLabel("SKILLS: 0")
        self.skills_label.setStyleSheet("color: #FFFFFF; font-size: 12px;")
        
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.mode_label)
        layout.addWidget(self.skills_label)
    
    def update_status(self, status: str, color: str = "#00FF00"):
        self.status_label.setText(f"● {status}")
        self.status_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
    
    def update_skills(self, count: int):
        self.skills_label.setText(f"SKILLS: {count}")

class EnhancedJarvisGUI(QMainWindow):
    """Enhanced JARVIS GUI with advanced features."""
    
    def __init__(self, pause_event, theme=Theme.STARK):
        super().__init__()
        self.pause_event = pause_event
        self.is_paused = False
        self.theme = theme
        
        self.setWindowTitle("JARVIS - Advanced AI Assistant")
        self.resize(1200, 700)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: black;")
        
        self.setup_ui()
        self.setup_system_tray()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status bar
        self.status_bar = StatusBar()
        main_layout.addWidget(self.status_bar)
        
        # Main content
        content_layout = QHBoxLayout()
        
        # Left panel
        self.left_panel = EnhancedHexagonPanel(theme=self.theme)
        content_layout.addWidget(self.left_panel)
        
        # Center reactor
        self.reactor = EnhancedReactor(theme=self.theme)
        content_layout.addWidget(self.reactor, stretch=2)
        
        # Right panel
        self.right_panel = EnhancedHexagonPanel(theme=self.theme)
        content_layout.addWidget(self.right_panel)
        
        main_layout.addLayout(content_layout)
        
        # Voice visualizer
        self.voice_viz = VoiceVisualizer()
        main_layout.addWidget(self.voice_viz)
    
    def setup_system_tray(self):
        """Setup system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create icon (simple colored square)
        pixmap = QPixmap(32, 32)
        pixmap.fill(self.theme["primary"])
        self.tray_icon.setIcon(QIcon(pixmap))
        
        # Create menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        pause_action = QAction("Pause/Resume", self)
        pause_action.triggered.connect(self.toggle_pause)
        tray_menu.addAction(pause_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def mousePressEvent(self, event):
        self.toggle_pause()
    
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.reactor.set_paused(self.is_paused)
        self.voice_viz.set_active(not self.is_paused)
        
        if self.is_paused:
            self.pause_event.set()
            self.status_bar.update_status("PAUSED", "#FFA500")
        else:
            self.pause_event.clear()
            self.status_bar.update_status("ONLINE", "#00FF00")
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Space:
            self.toggle_pause()
        elif event.key() == Qt.Key.Key_H:
            self.hide()

def run_enhanced_gui(pause_event, theme_name="STARK"):
    """Run the enhanced GUI."""
    app = QApplication(sys.argv)
    
    theme = getattr(Theme, theme_name, Theme.STARK)
    window = EnhancedJarvisGUI(pause_event, theme)
    window.show()
    
    sys.exit(app.exec())
