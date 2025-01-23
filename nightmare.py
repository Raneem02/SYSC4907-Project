import sys
import os
import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSlider, QComboBox, QLineEdit, QFormLayout)
from PyQt6.QtOpenGLWidgets import QOpenGLWidget 
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QKeyEvent,  QDrag, QPainter, QColor, QPixmap
import math
import numpy as np


class ObjLoader:
    def __init__(self, filename):
        self.vertices = []
        self.faces = []
        self.center = (0.0, 0.0, 0.0)
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
        self.calculate_center()
        
    def find_closest_vertex(self, x, y, z):
        """Find the closest vertex to a given point."""
        min_distance = float('inf')
        closest_vertex = None

        for vertex in self.vertices:
            distance = np.sqrt((vertex[0] - x) ** 2 + (vertex[1] - y) ** 2 + (vertex[2] - z) ** 2)
            if distance < min_distance:
                min_distance = distance
                closest_vertex = vertex

        return closest_vertex
    
                    
    def calculate_center(self):
        if not self.vertices:
            return
        xs, ys, zs = zip(*self.vertices)
        self.center = (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))



class DraggableLight(QLabel):
    def __init__(self, color):
        super().__init__()
        self.color = color
        self.setFixedSize(40, 40)

        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(*color))
        painter.setPen(Qt.GlobalColor.black)
        painter.drawEllipse(0, 0, 40, 40)
        painter.end()
        self.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(f"{self.color[0]},{self.color[1]},{self.color[2]}")
            drag.setMimeData(mime_data)

            drag_pixmap = QPixmap(self.size())
            self.render(drag_pixmap)
            drag.setPixmap(drag_pixmap)
            drag.setHotSpot(event.pos())

            drag.exec(Qt.DropAction.MoveAction)

class OpenGLWidget(QOpenGLWidget):
    def __init__(self, obj_path):
        super().__init__()
        self.sphere=gluNewQuadric()
        self.obj = ObjLoader(obj_path)
        self.lights = []  # Store lights as (x, y, z, color) tuples
        self.last_mouse_pos = None  # Track the last mouse position for movement
        self.angle_x = 0
        self.angle_y = 0
        self.obj_angle_x = 0 # for rotation within anchor mode
        self.obj_angle_y = 0
        self.last_x = 0
        self.last_y = 0
        self.camera_state=0
        self.positionX = 0.0
        self.positionY = 0.0
        self.positionZ = -10.0
        self.last_px = 0
        self.last_py = 0
        self.last_pz = 0
        self.Zcorrection = 1
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.transparency = 0.4

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST) 
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)        

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
        

        glRotatef(self.obj_angle_x, 1, 0, 0) # rotation within anchor mode
        glRotatef(self.obj_angle_y, 0, 1, 0)       
        
        self.draw_grass()
        self.draw_lights()        
        self.draw_obj()  # Draw the object

    def draw_obj(self):
        glColor4f(1.0, 1.0, 1.0, self.transparency)
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
        
        
    def draw_grass(self):
        glColor3f(0.0, 0.5, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(-10.0, -1.0, -10.0)
        glVertex3f(10.0, -1.0, -10.0)
        glVertex3f(10.0, -1.0, 10.0)
        glVertex3f(-10.0, -1.0, 10.0)
        glEnd()

    def draw_lights(self):
        for x, y, z, color in self.lights:
            glColor3f(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
            glPushMatrix()
            glTranslatef(x, y, z)
            gluSphere(self.sphere,0.2, 10,10)
            glPopMatrix()
    

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
        

        if event.buttons() and Qt.MouseButton.LeftButton: 
            if self.camera_state == 0:    
                self.angle_x += dy
                self.angle_y += dx
                if (self.angle_y > 90 and self.angle_y < 270):
                    self.Zcorrection = -1
                else:
                    self.Zcorrection = 1
                    
            elif self.camera_state == 1:
                
    
                self.positionX += ((dx * 0.03 * math.cos(math.radians(self.angle_y)))  + 
                                   (-dy * 0.03 * math.sin(math.radians(self.angle_x))* math.sin(math.radians(self.angle_y))))             
                self.positionY -= dy * 0.03 * math.cos(math.radians(self.angle_x))
                self.positionZ -= ((-dx * 0.03 * math.sin(math.radians(self.angle_y))) + 
                                   (-dy * self.Zcorrection * 0.03 * math.sin(math.radians(self.angle_x)) * math.sin(math.radians(self.angle_x))))
                
                #print(self.positionX, self.positionY, self.positionZ)
                #print(self.angle_x, self.angle_y)
                
                
            elif self.camera_state == 2:
                self.obj_angle_x += dy
                self.obj_angle_y += dx
               
        self.last_x = event.position().x()
        self.last_y = event.position().y()

        self.update()


    def update_transparency(self, value):
        self.transparency = value / 100.0  # Convert 1-100 to 0.0-1.0
        self.update()
        
    def swap_anchor(self):
        if self.camera_state != 2:
            self.camera_state = 1 - self.camera_state
            self.update()
        
    def select_light(self,value):
        pass
        
    def light_red_handler(self,value):
        pass
        
    def light_blue_handler(self,value):
        pass
                
    def light_green_handler(self,value):
        pass

    def object_rotation(self,value):
        if(self.camera_state == 2):           #return to standard camera control
            self.camera_state = 0
            self.positionX,self.positionY,self.positionZ= (self.last_px,self.last_py,self.last_pz)
            
            self.angle_x,self.angle_y = (self.obj_angle_x + self.angle_x,self.obj_angle_y + self.angle_y)#maintains camera angle after leaving anchor
            
            self.obj_angle_x,self.obj_angle_y=(0,0)
            
        else:
                                  #set camera to neutral position for rotation control
            self.camera_state = 2
            self.last_px,self.last_py,self.last_pz= (self.positionX,self.positionY,self.positionZ)
            obj_center = self.obj.center
            self.positionX = -obj_center[0]
            self.positionY = -obj_center[1]
            self.positionZ = -obj_center[2]-20
        self.update()
            

    def change_light_colour(self,index, colour):
        light = self.lights[index]                   
        self.lights[index] = (light[0],light[1],light[2],colour)
    


class Viewer2DCanvas(QWidget):
    def __init__(self, add_light_callback, obj):
        super().__init__()
        self.figure = Figure(figsize=(4, 4))
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.ax = None
        self.add_light_callback = add_light_callback
        self.obj = obj
        self.view_mode = "Top"
        self.counter_label = QLabel("Lights: 0")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.counter_label.setStyleSheet("color: black; background-color: white; font-size: 12px;")
        layout.addWidget(self.counter_label)

    def update_2d_view(self, vertices, lights, view_mode):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title(f"{view_mode} View")
        self.view_mode = view_mode

        if view_mode == "Top":
            xs = [v[0] for v in vertices]
            ys = [v[2] for v in vertices]
        elif view_mode == "Front":
            xs = [v[0] for v in vertices]
            ys = [v[1] for v in vertices]
        elif view_mode == "Side":
            xs = [v[2] for v in vertices]
            ys = [v[1] for v in vertices]
        self.ax.scatter(xs, ys, c='blue', s=10, label="Object Vertices")

        for light in lights:
            if view_mode == "Top":
                lx, ly = light[0], light[2]
            elif view_mode == "Front":
                lx, ly = light[0], light[1]
            elif view_mode == "Side":
                lx, ly = light[2], light[1]
            self.ax.add_patch(Circle((lx, ly), 0.2, color=[c / 255.0 for c in light[3]], label="Light"))    #Ben: change?

        self.ax.set_xlabel("X" if view_mode in ["Top", "Front"] else "Z")
        self.ax.set_ylabel("Y" if view_mode in ["Front", "Side"] else "Z")
        self.ax.legend()
        self.ax.grid(True)

        # Update light counter
        self.counter_label.setText(f"Lights: {len(lights)}")

        self.canvas.mpl_connect('button_press_event', self.handle_click) #Ben: needs changed
        self.canvas.draw()

    def handle_click(self, event):
        if event.inaxes is not None:
            lx, ly = event.xdata, event.ydata
            if self.view_mode == "Top":
                closest_vertex = self.obj.find_closest_vertex(lx, 0, ly)
            elif self.view_mode == "Front":
                closest_vertex = self.obj.find_closest_vertex(lx, ly, 0)
            elif self.view_mode == "Side":
                closest_vertex = self.obj.find_closest_vertex(0, ly, lx)
            #print(closest_vertex)
            if closest_vertex:
                self.add_light_callback(*closest_vertex)





class MainWindow(QMainWindow):
    def __init__(self, obj_path):
        super().__init__()
        main_widget = QWidget()
        main_layout = QGridLayout()
        self.setWindowTitle("Helicopter GUI WIP Prototype")
        
        self.opengl_widget = OpenGLWidget(obj_path)
        self.lights = []
        self.draggable_lights = []#had to make a seperate list that stores the object itself
        self.light_counter = 1
        
        main_layout.addWidget(self.opengl_widget,0,0)
        self.opengl_widget.lights = self.lights
        self.opengl_widget.setFocus()
        controls_layout = QGridLayout()
        controls_layout2 = QGridLayout()
        controls_layout3 = QGridLayout()  
        
        # Add 2D Viewer
        self.viewer_2d = Viewer2DCanvas(self.add_light, self.opengl_widget.obj)
        controls_layout2.addWidget(self.viewer_2d,0,0)         
        
        rotate_button = QPushButton("Translate/Rotate")
        rotate_button.clicked.connect(self.opengl_widget.swap_anchor)
        controls_layout.addWidget(rotate_button,0,0)    
        
        
        transparency_slider = QSlider(Qt.Orientation.Horizontal)
        transparency_slider.setRange(1, 100)
        transparency_slider.setValue(50)
        transparency_slider.valueChanged.connect(self.opengl_widget.update_transparency)
        
        controls_layout.addWidget(QLabel("Helicopter Transparency:"),0,1)
        controls_layout.addWidget(transparency_slider,0,2)
        
        self.light_selector = QComboBox()
        #light_selector.addItems(['One', 'Two', 'Three', 'Four'])# must add a way to dynamically include options for all renderd lights
        self.light_selector.currentIndexChanged.connect(self.opengl_widget.select_light)
        
        controls_layout.addWidget(QLabel("Light Selector:"),0,3)
        controls_layout.addWidget(self.light_selector,0,4)
        
        colour_selector = QComboBox()
        colour_selector.addItems(['Yellow', 'Red', 'Green', 'Blue'])# must add a way to dynamically include options for all renderd lights
        colour_selector.currentIndexChanged.connect(self.light_change_handler)
        
        controls_layout.addWidget(QLabel("Colour Selector:"),1,3)
        controls_layout.addWidget(colour_selector,1,4)        
        
        #brightness_slider = QSlider(Qt.Orientation.Horizontal)
        #brightness_slider.setRange(1, 100)
        #brightness_slider.setValue(50)
        #brightness_slider.valueChanged.connect(self.opengl_widget.update_brightness)         
        
        self.red_slider = QSlider(Qt.Orientation.Horizontal)
        self.red_slider.setRange(1, 100)
        self.red_slider.setValue(50)
        self.red_slider.valueChanged.connect(self.opengl_widget.light_red_handler)
        
        self.blue_slider = QSlider(Qt.Orientation.Horizontal)
        self.blue_slider.setRange(1, 100)
        self.blue_slider.setValue(50)
        self.blue_slider.valueChanged.connect(self.opengl_widget.light_blue_handler)
        
        self.green_slider = QSlider(Qt.Orientation.Horizontal)
        self.green_slider.setRange(1, 100)
        self.green_slider.setValue(50)
        self.green_slider.valueChanged.connect(self.opengl_widget.light_green_handler)        
        
        
        controls_layout.addWidget(QLabel("Light Custom Colour(R/G/B):"),1,0)
        controls_layout.addWidget(self.red_slider,1,1)
        controls_layout.addWidget(self.blue_slider,2,1)     
        controls_layout.addWidget(self.green_slider,3,1)  
        
        anchor_button = QPushButton("Send Custom Colour")
        anchor_button.clicked.connect(self.light_custom_colour)
        controls_layout.addWidget(anchor_button,2,0)         
        
        anchor_button = QPushButton("Anchor/Unanchor")
        anchor_button.clicked.connect(self.opengl_widget.object_rotation)
        controls_layout.addWidget(anchor_button,1,2)     


        
        
        top_view_btn = QPushButton("Top View")
        top_view_btn.clicked.connect(lambda: self.update_2d_view("Top"))
        front_view_btn = QPushButton("Front View")
        front_view_btn.clicked.connect(lambda: self.update_2d_view("Front"))
        side_view_btn = QPushButton("Side View")
        side_view_btn.clicked.connect(lambda: self.update_2d_view("Side"))

        controls_layout2.addWidget(top_view_btn,1,0)
        controls_layout2.addWidget(front_view_btn,2,0)
        controls_layout2.addWidget(side_view_btn,3,0)        
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        x=0
        for color in colors:
            light = DraggableLight(color)
            controls_layout3.addWidget(light,0,x)
            x+=1



        coord_layout = QFormLayout()
        self.x_input = QLineEdit()
        self.y_input = QLineEdit()
        self.z_input = QLineEdit()
        coord_layout.addRow("X:", self.x_input)
        coord_layout.addRow("Y:", self.y_input)
        coord_layout.addRow("Z:", self.z_input)
        controls_layout3.addLayout(coord_layout,1,0)

        place_light_btn = QPushButton("Place Light at Coordinates")
        place_light_btn.clicked.connect(self.place_light_from_coords)
        controls_layout3.addWidget(place_light_btn,2,0)        
        
        
        
        main_layout.addLayout(controls_layout,1,0)
        main_layout.addLayout(controls_layout2,0,1)
        main_layout.addLayout(controls_layout3,1,1)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)        
 
    def light_change_handler(self,colour):
        if not bool(self.lights):
            print("error, no lights exist")
        else:
            match colour:
                case 0:
                    self.opengl_widget.change_light_colour(self.light_selector.currentIndex(),(255,255,0))
                case 1:
                    self.opengl_widget.change_light_colour(self.light_selector.currentIndex(),(255,0,0))
                case 2:
                    self.opengl_widget.change_light_colour(self.light_selector.currentIndex(),(0,255,0))
                case 3:
                    self.opengl_widget.change_light_colour(self.light_selector.currentIndex(),(0,0,255))      
            self.opengl_widget.update()
     
 
    def light_custom_colour(self):
        if not bool(self.lights):
            print("error, no lights exist")
        else:
            self.opengl_widget.change_light_colour(self.light_selector.currentIndex(),(self.red_slider.value(),self.green_slider.value(),self.blue_slider.value()))
            self.opengl_widget.update()
        
 
    def update_2d_view(self, view_mode):
        self.viewer_2d.update_2d_view(self.opengl_widget.obj.vertices, self.lights, view_mode)
        
    def add_light(self, x, y, z, color=(255, 255, 0)):
        self.lights.append((x, y, z, color))
        self.opengl_widget.update()
        self.viewer_2d.update_2d_view(self.opengl_widget.obj.vertices, self.lights, self.viewer_2d.view_mode)
        
        self.light_selector.addItems([str(self.light_counter)])
        self.light_counter +=1        
    
    
    def place_light_from_coords(self):
        try:
            x = float(self.x_input.text())
            y = float(self.y_input.text())
            z = float(self.z_input.text())
            self.add_light(x,y,z)
            #closest_vertex = self.obj.find_closest_vertex(x, y, z)
            #if closest_vertex:
            #    self.add_light(*closest_vertex)
        except ValueError:
            print("Invalid coordinates entered!")            
        
        
        
        
        
        
        

if __name__ == "__main__":
    app = QApplication(sys.argv)

    obj_path = "cone.obj"  

    # Create and show the main window
    main_window = MainWindow(obj_path)
    main_window.resize(800, 600)
    main_window.show()
    

    # Start the application's event loop
    sys.exit(app.exec())
    
    
    
    #place light from coord no longer gravitates to a vertice
    
    #make anchoring neutral rotation values & fix off center rotation
    #plug in all my methods