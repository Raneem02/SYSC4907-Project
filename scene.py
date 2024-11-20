import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt6.QtCore import Qt


class ObjLoader:
    def __init__(self, filename):
        self.vertices = []
        self.faces = []
        self.load_obj(filename)

    def load_obj(self, filename):
        with open(filename, "r") as file:
            for line in file:
                if line.startswith("v "):  
                    parts = line.split()
                    vertex = (float(parts[1]), float(parts[2]), float(parts[3]))
                    self.vertices.append(vertex)
                elif line.startswith("f "):  
                    parts = line.split()
                    face = [int(idx.split('/')[0]) - 1 for idx in parts[1:]]
                    self.faces.append(face)


class OpenGLWidget(QOpenGLWidget):
    def __init__(self, obj_path):
        super().__init__()
        self.obj = ObjLoader(obj_path)
        self.angle_x = 0
        self.angle_y = 0
        self.last_x = 0
        self.last_y = 0

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST) 
        glClearColor(0.1, 0.1, 0.1, 1.0)  

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)  
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        gluPerspective(60, width / height, 0.1, 100.0)  
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  
        glLoadIdentity()

       
        glTranslatef(0.0, 0.0, -10)  

        glRotatef(self.angle_x, 1, 0, 0)  # Rotate on X-axis
        glRotatef(self.angle_y, 0, 1, 0)  # Rotate on Y-axis

        self.draw_obj()  # Draw the object

    def draw_obj(self):
        glBegin(GL_TRIANGLES)
        for face in self.obj.faces:
            for vertex_idx in face:
                glVertex3fv(self.obj.vertices[vertex_idx])  # Draw each vertex of the face
        glEnd()

    def mousePressEvent(self, event):
        self.last_x = event.position().x()
        self.last_y = event.position().y()

    def mouseMoveEvent(self, event):
        dx = event.position().x() - self.last_x
        dy = event.position().y() - self.last_y

        if event.buttons() & Qt.MouseButton.LeftButton:
            self.angle_x += dy
            self.angle_y += dx

        self.last_x = event.position().x()
        self.last_y = event.position().y()

        self.update()


class MainWindow(QMainWindow):
    def __init__(self, obj_path):
        super().__init__()
        self.setWindowTitle("PyQt6 OpenGL .OBJ Viewer")
        self.opengl_widget = OpenGLWidget(obj_path)
        self.setCentralWidget(self.opengl_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    obj_path = "/Users/raneemcorbin/Desktop/cone.obj"  

    # Create and show the main window
    main_window = MainWindow(obj_path)
    main_window.resize(800, 600)
    main_window.show()

    # Start the application's event loop
    sys.exit(app.exec())
