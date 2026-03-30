import FreeCAD as App
import Part

doc = App.newDocument()
box = Part.makeBox(1,1,1)

try:
    print("Test import.")
except Exception as e:
    pass

