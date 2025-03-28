import sys
import os
import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSlider, QComboBox, QLineEdit, QFormLayout)
from PyQt6.QtOpenGLWidgets import QOpenGLWidget 
from PyQt6.QtCore import QPoint
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QKeyEvent,  QDrag, QPainter, QColor, QPixmap
import math
import numpy as np
import threading
from PIL import Image, ImageDraw, ImageFont
import time

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
        #print(self.center)



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
    def __init__(self, obj_path=None,obj_info=None):
        super().__init__()
        self.sphere=gluNewQuadric()
        self.objs = None
        self.obj_attributes = None
        self.labelbool=None
        if obj_path is not None and obj_info is not None:
            self.objs = [ObjLoader(obj_path)]
            self.obj_attributes = [obj_info] # syntax: [[x,y,z],color,[angle_x,angle_y,angle_z],transparency,name] in reference to each object at the same index
            self.labelbool=[1]
        self.lights = []  # Store lights as (x, y, z, color) tuples
        self.last_mouse_pos = None  # Track the last mouse position for movement
        self.angle_x = 0
        self.angle_y = 0
        self.obj_angle_x = 0 # for rotation within anchor mode
        self.obj_angle_y = 0
        self.lastangle_x = 0
        self.lastangle_y = 0        
        self.last_x = 0
        self.last_y = 0
        self.camera_state=0
        self.positionX = 0.0
        self.positionY = 0.0
        self.positionZ = -10.0
        self.orbitX= 0 
        self.orbitY= 0
        self.orbitZ= 0
        self.last_px = 0
        self.last_py = 0
        self.last_pz = 0
        self.Zcorrection = 1
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.transparency = 0.4
        self.mutex=False
        
    
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
        
        glTranslatef(self.orbitX, self.orbitY, self.orbitZ)
        while(self.mutex):
            time.sleep(0.2)
        self.mutex=True
        self.draw_grass()
        self.draw_lights()        
        self.draw_obj()  # Draw the object
        self.mutex=False
        #self.draw_secondary_obj()

    def draw_obj(self):
        index = -1
        projected_labels=[]
        if self.objs != []:
            for x in self.objs:
                index += 1
                glColor4f(self.obj_attributes[index][1][0]/255,self.obj_attributes[index][1][1]/255,self.obj_attributes[index][1][2]/255, self.obj_attributes[index][3])
                #glBegin(GL_TRIANGLES)   
                glPushMatrix()
                glTranslatef(self.obj_attributes[index][0][0],self.obj_attributes[index][0][1],self.obj_attributes[index][0][2]) 
                glRotatef(self.obj_attributes[index][2][0],1,0,0)
                glRotatef(self.obj_attributes[index][2][1],0,1,0)
                glRotatef(self.obj_attributes[index][2][2],0,0,1)
                
                #[[x,y,z],color,[angle_x,angle_y],transparency,label]
                glBegin(GL_TRIANGLES) 
                for face in x.faces:
                    if len(face) == 3:
                        for vertex_idx in face:
                            glVertex3fv(x.vertices[vertex_idx])
                    elif len(face) == 4:
                        glVertex3fv(x.vertices[face[0]])
                        glVertex3fv(x.vertices[face[1]])
                        glVertex3fv(x.vertices[face[2]])
                        glVertex3fv(x.vertices[face[0]])
                        glVertex3fv(x.vertices[face[2]])
                        glVertex3fv(x.vertices[face[3]])

                glEnd()
                #draw label for each object
                if self.labelbool[index]==1 and self.objs != []:
                    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
                    projection = glGetDoublev(GL_PROJECTION_MATRIX)
                    viewport = glGetIntegerv(GL_VIEWPORT)
                    winX, winY, winZ = gluProject(0,0,0, modelview, projection, viewport)
                
                    projected_labels.append((winX, winY, self.obj_attributes[index][4]))
                

                
                glPopMatrix()
        self.draw_labels(projected_labels)
  
    def create_text_texture(self,text, font_size=24):
            font = ImageFont.truetype("arial.ttf", font_size)
            padding=12
            dummy_img = Image.new("RGBA", (1, 1))
            dummy_draw = ImageDraw.Draw(dummy_img)
            bbox = dummy_draw.multiline_textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            texture_width = text_width + 2 * padding + 100
            texture_height = text_height + 2 * padding

            img = Image.new("RGBA", (texture_width, texture_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            draw.multiline_text((padding, padding), text, font=font, fill=(255, 255, 255, 255))
            img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            img_data = np.array(img.convert("RGBA"), dtype=np.uint8)

            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, texture_width, texture_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)


            return texture_id, texture_width, texture_height

    def draw_textured_quad(self,x, y, w, h, texture_id):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glColor3f(1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x, y)
        glTexCoord2f(1, 0); glVertex2f(x + w, y)
        glTexCoord2f(1, 1); glVertex2f(x + w, y + h)
        glTexCoord2f(0, 1); glVertex2f(x, y + h)
        glEnd()

        glDisable(GL_TEXTURE_2D)

    def draw_labels(self, labels):
        if not labels:
            return

        glDepthMask(GL_FALSE)
        glMatrixMode(GL_PROJECTION)
        width, height = self.width(), self.height()
        glViewport(0, 0, width, height)
        glPushMatrix()
        glLoadIdentity()
        offset = self.mapTo(self.window(), QPoint(0, 0))
        offset_x, offset_y = offset.x(), offset.y()

        # Now create an orthographic projection that accounts for the widget's offset:
        glOrtho(offset_x, width + offset_x, offset_y, height + offset_y, -1, 1)
        #glOrtho(0, width+50, 0, height+50, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glDepthFunc(GL_ALWAYS)
        for winX, winY, label_text in labels:
            texture_id, tex_w, tex_h = self.create_text_texture(label_text)
            print(winX - tex_w, winY, tex_w, tex_h)
            self.draw_textured_quad((winX - tex_w), winY,  tex_w, tex_h, texture_id)
            glDeleteTextures([texture_id])
        
        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        

    def draw_grass(self):
        glColor3f(0.0, 0.5, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(-10.0, -1.0, -10.0)
        glVertex3f(10.0, -1.0, -10.0)
        glVertex3f(10.0, -1.0, 10.0)
        glVertex3f(-10.0, -1.0, 10.0)
        glEnd()

    def draw_lights(self):
        if self.lights.__len__ != 0:
            for x, y, z, color in self.lights:
                glColor3f(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
                glPushMatrix()
                #print(self.obj_attributes[0][0][0],self.obj_attributes[0][0][1],self.obj_attributes[0][0][2])
                glTranslatef(self.obj_attributes[0][0][0],self.obj_attributes[0][0][1],self.obj_attributes[0][0][2])          
                glRotatef(self.obj_attributes[0][2][0],1,0,0)# translate,rotate,rotate to helis current position
                glRotatef(self.obj_attributes[0][2][1],0,1,0)
                glTranslatef(x, y, z)#translate to lights position on heli
                gluSphere(self.sphere,0.2, 10,10)
                glPopMatrix()
    
    #def draw_labels(self):


    def add_secondary(self,path,attributes): #for adding secondary objects during runtime
        self.objs.append(ObjLoader(path))
        self.obj_attributes.append(attributes)
        self.labelbool.append(1)
        self.update()
    
    def edit_obj(self,index,attributes):
        self.obj_attributes[index]=attributes
        if self.camera_state==2 and index==0:
            obj_center = self.objs[0].center
            self.orbitX = -obj_center[0] - self.obj_attributes[0][0][0]
            self.orbitY = -obj_center[1] - self.obj_attributes[0][0][1]
            self.orbitZ = -obj_center[2] - self.obj_attributes[0][0][2]
        self.update()

    def set_camera(self,type,angle,x=None,y=None,z=None):
        if (self.camera_state == 2) ^ (type == 1):#if camera type is not aligned
            self.object_rotation()
        if type==0:
            self.positionX=x
            self.positionY=y
            self.positionZ=z
            self.angle_x=angle[0]
            self.angle_y=angle[1]
        else:
            self.obj_angle_x=angle[0]
            self.obj_angle_y=angle[1]
        self.update()


    def set_label(self,index,set):
        self.labelbool[index]=set

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

    def wipe(self):
        while(self.mutex):
            time.sleep(0.2)
        self.mutex=True
        self.objs=[]
        self.obj_attributes=[]
        #self.lights=[]
        self.update()
        self.mutex=False
        
    def select_light(self,value):
        pass
        
    def light_red_handler(self,value):
        pass
        
    def light_blue_handler(self,value):
        pass
                
    def light_green_handler(self,value):
        pass

    def object_rotation(self):   #swap between orbit and free cameras
        if(self.camera_state == 2):           #return to standard camera control
            self.camera_state = 0
            self.orbitX,self.orbitY,self.orbitZ= (0,0,0)
            self.positionX,self.positionY,self.positionZ=(self.last_px,self.last_py,self.last_pz)
            self.positionZ +=20
            self.angle_x,self.angle_y = self.lastangle_x,self.lastangle_y#maintains camera angle after leaving anchor
            
            self.obj_angle_x,self.obj_angle_y=(0,0)
            
        else:
                                  #set camera to neutral position for rotation control
            self.camera_state = 2
            self.last_px,self.last_py,self.last_pz=(self.positionX,self.positionY,self.positionZ)
            self.positionX,self.positionY,self.positionZ=(0,0,0)
            self.positionZ -=20
            self.lastangle_x,self.lastangle_y = self.angle_x,self.angle_y
            self.angle_x,self.angle_y=0,0
            obj_center = self.objs[0].center
            self.orbitX = -obj_center[0] - self.obj_attributes[0][0][0]
            self.orbitY = -obj_center[1] - self.obj_attributes[0][0][1]
            self.orbitZ = -obj_center[2] - self.obj_attributes[0][0][2]
        self.update()
            

    def change_light_colour(self,index, colour):
        light = self.lights[index]                   
        self.lights[index] = (light[0],light[1],light[2],colour)
        self.update()
    


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
    def __init__(self, obj_path=None, obj_info=None):
        super().__init__()
        #print(obj_info)
        main_widget = QWidget()
        main_layout = QGridLayout()
        self.setWindowTitle("Helicopter GUI WIP Prototype")
        
        self.opengl_widget = OpenGLWidget(obj_path,obj_info)
        self.lights = []
        self.draggable_lights = []#had to make a seperate list that stores the object itself
        self.light_counter = 1
        self.play=True

        main_layout.addWidget(self.opengl_widget,0,0)
        self.opengl_widget.lights = self.lights
        self.opengl_widget.setFocus()
        controls_layout = QGridLayout()
        controls_layout2 = QGridLayout()
        controls_layout3 = QGridLayout()  
        
        # Add 2D Viewer
        self.viewer_2d = Viewer2DCanvas(self.add_light, self.opengl_widget.objs[0])
        controls_layout2.addWidget(self.viewer_2d,0,0)         
        
        controls_layout.addWidget(QLabel("Free Camera Translate/Rotate(space)"),0,0)
        rotate_button = QPushButton("Swap Control")
        rotate_button.clicked.connect(self.opengl_widget.swap_anchor)
        controls_layout.addWidget(rotate_button,1,0)    
        
        transparency_slider = QSlider(Qt.Orientation.Horizontal)
        transparency_slider.setRange(1, 100)
        transparency_slider.setValue(50)
        transparency_slider.valueChanged.connect(self.opengl_widget.update_transparency)
        
        controls_layout.addWidget(QLabel("Helicopter Transparency:"),4,0)
        controls_layout.addWidget(transparency_slider,5,0)
        
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
        
        self.red_slider = QSlider(Qt.Orientation.Horizontal)
        self.red_slider.setRange(1, 255)
        self.red_slider.setValue(50)
        self.red_slider.valueChanged.connect(self.opengl_widget.light_red_handler)
        
        self.blue_slider = QSlider(Qt.Orientation.Horizontal)
        self.blue_slider.setRange(1, 255)
        self.blue_slider.setValue(50)
        self.blue_slider.valueChanged.connect(self.opengl_widget.light_blue_handler)
        
        self.green_slider = QSlider(Qt.Orientation.Horizontal)
        self.green_slider.setRange(1, 255)
        self.green_slider.setValue(50)
        self.green_slider.valueChanged.connect(self.opengl_widget.light_green_handler)        
        
        
        controls_layout.addWidget(QLabel("Light Custom Colour(R/G/B):"),0,2)
        controls_layout.addWidget(self.red_slider,1,2)
        controls_layout.addWidget(self.blue_slider,2,2)     
        controls_layout.addWidget(self.green_slider,3,2)  
        
        anchor_button = QPushButton("Send Custom Colour")
        anchor_button.clicked.connect(self.light_custom_colour)
        controls_layout.addWidget(anchor_button,4,2)         
        
        controls_layout.addWidget(QLabel("Swap Orbit/Free Camera"),2,0)
        anchor_button = QPushButton("Swap Camera")
        anchor_button.clicked.connect(self.opengl_widget.object_rotation)
        controls_layout.addWidget(anchor_button,3,0)             
        
        top_view_btn = QPushButton("Top View")
        top_view_btn.clicked.connect(lambda: self.update_2d_view("Top"))
        top_view_btn.resize(4,0)
        front_view_btn = QPushButton("Front View")
        front_view_btn.clicked.connect(lambda: self.update_2d_view("Front"))
        side_view_btn = QPushButton("Side View")
        side_view_btn.clicked.connect(lambda: self.update_2d_view("Side"))

        controls_layout2.addWidget(top_view_btn,1,0)
        controls_layout2.addWidget(front_view_btn,2,0)
        controls_layout2.addWidget(side_view_btn,3,0)        
        """colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        x=0
        for color in colors:
            light = DraggableLight(color)
            controls_layout3.addWidget(light,0,x)
            x+=1
        """


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
        
        play_pause_btn = QPushButton(".log play/pause")
        load_obj_btn = QPushButton("edit existing object")
        edit_obj_btn = QPushButton("load new object")
        play_pause_btn.clicked.connect(self.play_pause)
        load_obj_btn.clicked.connect(self.edit_object)
        edit_obj_btn.clicked.connect(self.load_new_object)
        controls_layout.addWidget(play_pause_btn,2,4)
        controls_layout.addWidget(edit_obj_btn,3,4)
        controls_layout.addWidget(load_obj_btn,4,4)          
        
        
        main_layout.addLayout(controls_layout,1,0)
        main_layout.addLayout(controls_layout2,0,1)
        main_layout.addLayout(controls_layout3,1,1)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)        
 
    def play_pause(self):
        if self.play:
            self.play=False 
        else:
            self.play=True

    def load_new_object(self):
        #print(self.secondary_filepath.text())
        #filename = self.secondary_filepath.text()
        #self.opengl_widget.add_secondary(filename)
        print("in load object") 
        select_window.new(self)   
        
    def edit_object(self):
        select_window.edit(self)

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
     
 
    def light_custom_colour(self,index=None,colour=None):
        if not bool(self.lights):
            print("error, no lights exist")
        else:
        
            self.opengl_widget.change_light_colour(self.light_selector.currentIndex(),(self.red_slider.value(),self.green_slider.value(),self.blue_slider.value()))
            self.opengl_widget.update()
        
 
    def update_2d_view(self, view_mode):
        self.viewer_2d.update_2d_view(self.opengl_widget.objs[0].vertices, self.lights, view_mode)
        
    def add_light(self, x, y, z, color=(255, 255, 0)):
        self.lights.append((x, y, z, color))
        self.opengl_widget.update()
        self.viewer_2d.update_2d_view(self.opengl_widget.objs[0].vertices, self.lights, self.viewer_2d.view_mode)
        
        self.light_selector.addItems([str(self.light_counter)])
        self.light_counter +=1        
    
    def wipe(self):
        self.lights=[]
        self.opengl_widget.lights=self.lights

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
    
    def closeEvent(self, event):
        os._exit(0)    

class fileReader():
    def __init__(self,filename,ref,select_window):
        self.file = open(filename, "r")
        self.select_window = select_window
        self.ref=ref
        self.newfile=""
        self.oldfiles=[]
        print ("hello")
        line =self.file.readline()
        attributes = line.strip().split(",")
        self.time = 0.0
        #print(attributes)
        if attributes[0] == "CREATE":
            vals=[[int(attributes[3]),int(attributes[4]),int(attributes[5])],[int(attributes[6]),int(attributes[7]),int(attributes[8])],[int(attributes[9]),int(attributes[10]),int(attributes[11])],float(attributes[12]),attributes[13]]
            # syntax: [[x,y,z],color,[angle_x,angle_y],transparency,name]
            self.ref = MainWindow(attributes[2],vals)
            self.ref.resize(900, 650)   
            self.ref.show()
        else:
            print("read file corrupt, does not start with create")
        #self.read()
        result = threading.Thread(target=lambda: self.read()).start()


    def read(self,index=0):
        event=threading.Event()
        self.file.seek(index)
        for index,line in enumerate(self.file):
            while not self.ref.play:
                time.sleep(0.5)
            attributes = line.strip().split(",")
            print(attributes)
            event.wait(float(attributes[1])-self.time-0.01)
            self.time=float(attributes[1])
            if attributes[0] == "CREATE":
                # syntax: [[x,y,z],color,[angle_x,angle_y,angle_z],transparency,name]
                vals=[[float(attributes[3]),float(attributes[4]),float(attributes[5])],[int(attributes[6]),int(attributes[7]),int(attributes[8])],[int(attributes[9]),int(attributes[10]),int(attributes[11])],float(attributes[12]),attributes[13]]
                self.ref.opengl_widget.add_secondary(attributes[2],vals)
            elif attributes[0] == "MODIFY":
                vals=[[float(attributes[3]),float(attributes[4]),float(attributes[5])],[int(attributes[6]),int(attributes[7]),int(attributes[8])],[int(attributes[9]),int(attributes[10]),int(attributes[11])],float(attributes[12]),attributes[13]]
                threading.Thread(target=lambda: self.ref.opengl_widget.edit_obj(int(attributes[2])-1,vals)).start()    
            elif attributes[0] == "ADD_LIGHT":
                self.ref.add_light(float(attributes[2]),float(attributes[3]),float(attributes[4]),(int(attributes[5]),int(attributes[6]),int(attributes[7])))
            elif attributes[0] == "MODIFY_LIGHT":
                threading.Thread(target=lambda: self.ref.opengl_widget.change_light_colour(int(attributes[2])-1,(int(attributes[3]),int(attributes[4]),int(attributes[5])))).start()
            elif attributes[0] == "SET_LABEL":
                self.ref.opengl_widget.set_label(int(attributes[2])-1,int(attributes[3]))
            elif attributes[0] == "SET_CAMERA":
                if int(attributes[2])==1:
                    self.ref.opengl_widget.set_camera(int(attributes[2])-1,[float(attributes[3]),float(attributes[4])],float(attributes[5]),float(attributes[6]),float(attributes[7]))
                else:
                    self.ref.opengl_widget.set_camera(int(attributes[2])-1,[float(attributes[3]),float(attributes[4])])
            elif attributes[0] == "RESTART_FILE":
                self.newfile=self.file
                self.ref.opengl_widget.wipe()
                self.ref.wipe()
                self.file.seek(0)
                self.read()
            elif attributes[0] == "NEW_FILE":
                self.oldfiles.append([self.file,index,self.time])
                self.file=open(attributes[2], "r")
                self.ref.opengl_widget.wipe()
                self.ref.wipe()
                self.read()
        print(self.oldfiles)
        if(self.oldfiles != []):
            self.file,index,self.time=self.oldfiles.pop(-1)
            self.ref.opengl_widget.wipe()
            self.ref.wipe()
            self.file.read(index)



class attributeSelect(QMainWindow): 
    def new(self,parent):
        self.show()
        self.parent=parent
        self.type="new"
        self.label.setText("inputs:x,y,z|angle x,y|colour r,g,b|transparency,name,filepath")

    def edit(self,parent):
        self.show()
        self.parent=parent
        self.type="edit"
        self.label.setText("inputs:x,y,z|angle x,y|colour r,g,b|transparency,name,object number")

    def __init__(self,parent = None,ref=None):
        print("in select init")
        self.parent=parent
        super().__init__()
        self.ref=ref
        self.type="new"
        self.x_input = QLineEdit()
        self.y_input = QLineEdit()
        self.z_input = QLineEdit()
        self.ax = QLineEdit()
        self.ay = QLineEdit()
        self.az = QLineEdit()
        self.r= QLineEdit()
        self.g= QLineEdit()
        self.b= QLineEdit()
        self.transparency= QLineEdit()
        self.path = QLineEdit()
        self.name= QLineEdit()
        main_widget = QWidget()
        main_layout = QGridLayout()
        self.setWindowTitle("Object Attribute Selector")        
        # syntax: [[x,y,z],color,[angle_x,angle_y,angle_z],transparency,name]
        self.label = QLabel("inputs:x,y,z|angle x,y,z|colour r,g,b|transparency,name,filepath")
        main_layout.addWidget(self.label,4,1)
        self.load_obj_btn = QPushButton("load new object")
        self.load_obj_btn.clicked.connect(self.load_attributes)
        main_layout.addWidget(self.x_input,0,0)
        main_layout.addWidget(self.y_input,1,0)
        main_layout.addWidget(self.z_input,2,0)
        main_layout.addWidget(self.ax,0,1)
        main_layout.addWidget(self.ay,1,1)
        main_layout.addWidget(self.az,2,1)
        main_layout.addWidget(self.load_obj_btn,4,0)
        main_layout.addWidget(self.r,0,2)
        main_layout.addWidget(self.g,1,2)
        main_layout.addWidget(self.b,2,2)
        main_layout.addWidget(self.transparency,0,3)
        main_layout.addWidget(self.name,1,3)
        main_layout.addWidget(self.path,2,3)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)       
        
    def load_attributes(self):
        attributes = [[int(self.x_input.text()),int(self.y_input.text()),int(self.z_input.text())],[int(self.r.text()),int(self.g.text()),int(self.b.text())],[int(self.ax.text()),int(self.ay.text()),int(self.az.text())],float(self.transparency.text()),self.name.text()]
            
        if self.parent=="main":#[[x,y,z],color,[angle_x,angle_y],transparency,name]
            print("in load main")
            #sendobjinfo(self.path,[[self.x_input,self.y_input,self.z_input],[self.r,self.g,self.b],[self.ax,self.ay],self.transparency,self.name])

            main_window = MainWindow(self.path.text(),attributes)
            main_window.resize(900, 650)   
            main_window.show()
            self.hide()            
        else:
            if self.type=="new":
                print ("in load else")
                self.parent.opengl_widget.add_secondary(self.path.text(),attributes)       
                self.hide()
            else:
                print("in edit")
                self.parent.opengl_widget.edit_obj(int(self.path.text())-1,attributes)       
                self.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    #obj_path = "bell_412.obj"  
    print("1 for file reader 2 for manual input")
    entry = int(input())    
    select_window = attributeSelect("main")    
    if entry ==1:
        print("enter file name")
        inpu = input() 
        main_window = None 
        reader = fileReader(inpu,main_window,select_window)
    else:
        

        select_window.show()    
    #obj_path = "bell_412.obj"  
    
    # Create and show the main window
    
    

    # Start the application's event loop
    sys.exit(app.exec())
    
    
    
