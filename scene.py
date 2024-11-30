import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
import math


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
        self.camera_state=0
        self.positionX = 0.0
        self.positionY = 0.0
        self.positionZ = -10.0
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

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

        glRotatef(self.angle_x, 1, 0, 0)  # Rotate on X-axis
        glRotatef(self.angle_y, 0, 1, 0)  # Rotate on Y-axis
        
        glTranslatef(self.positionX, self.positionY, self.positionZ)  



        self.draw_obj()  # Draw the object

    def draw_obj(self):
        glBegin(GL_TRIANGLES)
        for face in self.obj.faces:
            if len(face) == 3:
                for vertex_idx in face:
                    glVertex3fv(self.obj.vertices[vertex_idx])
            elif len(face) == 4:
                glVertex3fv(self.obj.vertices[face[0]])
                glVertex3fv(self.obj.vertices[face[1]])
                glVertex3fv(self.obj.vertices[face[2]])
                glVertex3fv(self.obj.vertices[face[0]])
                glVertex3fv(self.obj.vertices[face[2]])
                glVertex3fv(self.obj.vertices[face[3]])
        glEnd()

    def mousePressEvent(self, event):
        self.last_x = event.position().x()
        self.last_y = event.position().y()
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Space:
            self.camera_state = 1 - self.camera_state
                      
            
        self.update()  # Trigger repaint

    def mouseMoveEvent(self, event):
        dx = event.position().x() - self.last_x
        dy = event.position().y() - self.last_y
        

        if event.buttons() & Qt.MouseButton.LeftButton: 
            if self.camera_state == 0:    
                self.angle_x += dy
                self.angle_y += dx
 
            else:
                
    
                self.positionX += ((dx * 0.03 * math.cos(math.radians(self.angle_y))) + (-dy * 0.03 * math.sin(math.radians(self.angle_x))* math.sin(math.radians(self.angle_y))))             
                self.positionY -= dy * 0.03 * math.cos(math.radians(self.angle_x))
                self.positionZ -= ((-dx * 0.03 * math.sin(math.radians(self.angle_y))) + (-dy * 0.03 * math.sin(math.radians(self.angle_x)) * math.sin(math.radians(self.angle_x))))
                
        self.last_x = event.position().x()
        self.last_y = event.position().y()

        self.update()


class MainWindow(QMainWindow):
    def __init__(self, obj_path):
        super().__init__()
        self.setWindowTitle("PyQt6 OpenGL .OBJ Viewer")
        self.opengl_widget = OpenGLWidget(obj_path)
        self.setCentralWidget(self.opengl_widget)
        self.opengl_widget.setFocus()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    obj_path = "cone.obj"  

    # Create and show the main window
    main_window = MainWindow(obj_path)
    main_window.resize(800, 600)
    main_window.show()

    # Start the application's event loop
    sys.exit(app.exec())