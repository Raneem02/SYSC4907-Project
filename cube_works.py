import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtWidgets import QApplication
from PyQt6.Qt3DExtras import Qt3DWindow, QOrbitCameraController, QPhongMaterial, QCuboidMesh
from PyQt6.Qt3DCore import QEntity
from PyQt6.QtGui import QVector3D  # Import QVector3D
 #THIS ONE WORKS!
def main():
    # Create the application
    app = QApplication(sys.argv)

    # Set the surface format
    format = QSurfaceFormat()
    format.setSamples(4)  # Enable anti-aliasing
    QSurfaceFormat.setDefaultFormat(format)

    # Create the 3D window
    view = Qt3DWindow()
    view.setTitle("3D Cube Example")
    view.setGeometry(100, 100, 800, 600)

    # Create a root entity
    root_entity = QEntity()

    # Create a cube entity
    cube_entity = QEntity(root_entity)

    # Create a cube mesh and set it to the cube entity
    cube_mesh = QCuboidMesh()
    cube_entity.addComponent(cube_mesh)

    # Create a material for the cube
    cube_material = QPhongMaterial()
    cube_material.setDiffuse(Qt.GlobalColor.blue)  # Set the color to blue
    cube_entity.addComponent(cube_material)

    # Set the root entity for the 3D view
    view.setRootEntity(root_entity)

    # Create a camera
    camera = view.camera()
    camera.setPosition(QVector3D(0, 0, 20))  # Use QVector3D for position
    camera.setViewCenter(QVector3D(0, 0, 0))  # Use QVector3D for view center

    # Add a camera controller
    camera_controller = QOrbitCameraController(root_entity)
    camera_controller.setCamera(camera)

    # Show the view
    view.show()

    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
