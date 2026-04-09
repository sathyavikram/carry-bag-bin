import FreeCAD as App
import Part
import os
import sys

try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    pass

import config
import importlib
importlib.reload(config)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_BASE = os.path.join(CURRENT_DIR, "exports")
EXPORT_STEP = os.path.join(EXPORT_BASE, "part_05_hinge_pin_female.step")
EXPORT_STL = os.path.join(EXPORT_BASE, "part_05_hinge_pin_female.stl")

def construct_hinge_pin_female():
    shaft_length = 10.0 * config.SCALE
    shaft_radius = 4.5 * config.SCALE  # Increased to 4.5 (9mm diameter)
    
    # Shaft
    shaft = Part.makeCylinder(shaft_radius, shaft_length)
    
    # Head
    head_radius = 7.5 * config.SCALE
    head_length = 3.0 * config.SCALE
    head = Part.makeCylinder(head_radius, head_length)
    head.translate(App.Vector(0, 0, -head_length))
    
    slot = Part.makeBox(2.5, 14.0, 1.5)
    slot.translate(App.Vector(-1.25, -7.0, -head_length - 0.1))
    head = head.cut(slot)
    
    female_pin = shaft.fuse(head)
    
    # Female Glue Bore (Replaces Thread)
    # Bore length 10mm to fit 8.5mm peg with some room at bottom
    bore_depth = 10.0 * config.SCALE
    
    # Peg radius is 2.6mm, bore radius 2.8mm (0.2mm radial clearance = 0.4mm total diameter clearance)
    bore_radius = 2.8 * config.SCALE
    
    # The center bore cylinder to cut out the inside
    bore = Part.makeCylinder(bore_radius, bore_depth)
    bore.translate(App.Vector(0, 0, shaft_length - bore_depth))
    
    female_pin = female_pin.cut(bore)
    female_pin = female_pin.removeSplitter()
    
    # Rotate to lay flat for printing
    female_pin.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)
    female_pin.translate(App.Vector(head_length, 0, shaft_radius))
    
    os.makedirs(EXPORT_BASE, exist_ok=True)
    female_pin.exportStep(EXPORT_STEP)
    female_pin.exportStl(EXPORT_STL)
    print(f"Exported Female Threaded Pin to {EXPORT_STEP}")

    return female_pin

def main():
    doc = App.newDocument("FemalePin")
    shape = construct_hinge_pin_female()
    part = doc.addObject("Part::Feature", "PinPart")
    part.Shape = shape

if __name__ == "__main__":
    main()
