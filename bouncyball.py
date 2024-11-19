import sys
import math
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from PyQt6.QtGui import QPainter, QColor


class BouncingCircleWidget(QOpenGLWidget):
    def __init__(self, green_light_label, red_light_label):
        super().__init__()
        self.circle_radius = 0.1
        self.x_pos = 0.0
        self.y_pos = 0.0
        self.x_velocity = 0.02
        self.y_velocity = 0.015
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.bouncing_speed = 16  # Initial speed, 60 FPS equivalent
        self.green_light_flash = False
        self.red_light_flash = False
        
        # Store references to the green and red lights
        self.green_light_label = green_light_label
        self.red_light_label = red_light_label
        
        # Timer for flashing lights
        self.light_timer = QTimer(self)
        self.light_timer.timeout.connect(self.toggle_lights)

    def start_bouncing(self):
        self.timer.start(self.bouncing_speed)
        self.green_light_flash = True
        self.red_light_flash = False
        self.light_timer.start(1000)  # Flash every 1 second

    def stop_bouncing(self):
        self.timer.stop()
        self.green_light_flash = False
        self.red_light_flash = True
        self.light_timer.start(1000)  # Flash every 1 second

    def set_speed(self, value):
        self.bouncing_speed = max(1, 100 - value)  # Speed is inversely proportional
        if self.timer.isActive():
            self.timer.start(self.bouncing_speed)

    def update_position(self):
        self.x_pos += self.x_velocity
        self.y_pos += self.y_velocity

        # Check for boundary collisions and reverse velocity if necessary
        if abs(self.x_pos) + self.circle_radius > 1:
            self.x_velocity = -self.x_velocity
        if abs(self.y_pos) + self.circle_radius > 1:
            self.y_velocity = -self.y_velocity

        self.update()  # Trigger a repaint

    def initializeGL(self):
        glClearColor(0.1, 0.1, 0.1, 1.0)  # Background color

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = width / height
        if aspect_ratio > 1:
            glOrtho(-aspect_ratio, aspect_ratio, -1, 1, -1, 1)
        else:
            glOrtho(-1, 1, -1 / aspect_ratio, 1 / aspect_ratio, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glColor3f(1.0, 0.0, 0.0)  # Red color for the circle
        self.draw_circle(self.x_pos, self.y_pos, self.circle_radius)

    def draw_circle(self, x, y, radius):
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(x, y)  # Center of the circle
        num_segments = 100
        for i in range(num_segments + 1):
            angle = 2 * math.pi * i / num_segments
            glVertex2f(x + radius * math.cos(angle), y + radius * math.sin(angle))
        glEnd()

    def toggle_lights(self):
        # Flash green light when active (moving)
        if self.green_light_flash:
            self.green_light_label.flash_on()
        else:
            self.green_light_label.flash_off()

        # Flash red light when active (stopped)
        if self.red_light_flash:
            self.red_light_label.flash_on()
        else:
            self.red_light_label.flash_off()


class LightCircle(QLabel):
    def __init__(self, color="green"):
        super().__init__()
        self.setFixedSize(30, 30)
        self.color = color  # Store the color
        self.setStyleSheet(f"background-color: {self.color}; border-radius: 15px;")

    def flash_on(self):
        # Make the circle bright and flashing
        self.setStyleSheet(f"background-color: {self.color}; border-radius: 15px; box-shadow: 0 0 20px {self.color};")

    def flash_off(self):
        # Dim the circle when turned off
        self.setStyleSheet(f"background-color: dimgray; border-radius: 15px;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AUTONOMOUS HELICOPTER CONTROLS")
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Title label
        title_label = QLabel("AUTONOMOUS HELICOPTER CONTROLS")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # HELICOPTER STATUS panel
        status_layout = QHBoxLayout()
        status_label = QLabel("HELICOPTER STATUS")
        status_layout.addWidget(status_label)

        # Green Light circle (flashing)
        self.green_light_label = LightCircle("lime")  # Brighter green
        status_layout.addWidget(self.green_light_label)

        # Red Light circle (flashing)
        self.red_light_label = LightCircle("red")  # Brighter red
        status_layout.addWidget(self.red_light_label)

        main_layout.addLayout(status_layout)

        # OpenGL widget (the bouncing circle)
        self.opengl_widget = BouncingCircleWidget(self.green_light_label, self.red_light_label)
        main_layout.addWidget(self.opengl_widget)

        # Control buttons and slider
        controls_layout = QHBoxLayout()

        start_button = QPushButton("START")
        start_button.clicked.connect(self.start_bouncing_circle)
        controls_layout.addWidget(start_button)

        stop_button = QPushButton("STOP")
        stop_button.clicked.connect(self.stop_bouncing_circle)
        controls_layout.addWidget(stop_button)

        speed_slider = QSlider(Qt.Orientation.Horizontal)
        speed_slider.setRange(1, 100)
        speed_slider.setValue(50)  # Initial value
        speed_slider.valueChanged.connect(self.opengl_widget.set_speed)
        controls_layout.addWidget(QLabel("Speed:"))
        controls_layout.addWidget(speed_slider)

        main_layout.addLayout(controls_layout)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def start_bouncing_circle(self):
        # Trigger flashing green light when the ball starts bouncing
        self.green_light_label.flash_on()
        self.red_light_label.flash_off()
        self.opengl_widget.start_bouncing()

    def stop_bouncing_circle(self):
        # Trigger flashing red light when the ball stops bouncing
        self.green_light_label.flash_off()
        self.red_light_label.flash_on()
        self.opengl_widget.stop_bouncing()


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
