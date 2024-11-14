import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QSurfaceFormat
from OpenGL.GL import *  # Import OpenGL functions from PyOpenGL

class OpenGLWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OpenGL with PyQt6")
        self.resize(800, 600)

    def initializeGL(self):
        glClearColor(0.1, 0.1, 0.1, 1.0)  # Set background color

    def paintEvent(self, event):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clear buffers
        # Draw your OpenGL scene here

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenGL Example with PyQt6")
        self.setGeometry(100, 100, 800, 600)
        
        # Using QWidget as a base since QOpenGLWidget is not available
        self.opengl_widget = OpenGLWidget()
        self.setCentralWidget(self.opengl_widget)

def main():
    app = QApplication(sys.argv)

    # Set a default OpenGL surface format
    format = QSurfaceFormat()
    format.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(format)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
