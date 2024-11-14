import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat
from OpenGL.GL import *  # Import OpenGL functions from PyOpenGL

# Create a class that inherits from QOpenGLWidget
class BasicOpenGLWidget(QOpenGLWidget):
    def initializeGL(self):
        # Set the background color
        glClearColor(0.1, 0.1, 0.1, 1.0)  # Dark gray background

    def paintGL(self):
        # Clear the screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Draw a simple triangle
        glBegin(GL_TRIANGLES)
        glColor3f(1.0, 0.0, 0.0)  # Red
        glVertex2f(-0.5, -0.5)
        glColor3f(0.0, 1.0, 0.0)  # Green
        glVertex2f(0.5, -0.5)
        glColor3f(0.0, 0.0, 1.0)  # Blue
        glVertex2f(0.0, 0.5)
        glEnd()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Basic OpenGL with PyQt6")
        self.setGeometry(100, 100, 800, 600)

        # Create an instance of BasicOpenGLWidget and set it as the central widget
        self.opengl_widget = BasicOpenGLWidget()
        self.setCentralWidget(self.opengl_widget)

def main():
    # Create a QApplication instance
    app = QApplication(sys.argv)

    # Set a default OpenGL surface format
    format = QSurfaceFormat()
    format.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(format)

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the application's event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
