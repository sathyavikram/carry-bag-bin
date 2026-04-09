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
EXPORT_STEP = os.path.join(EXPORT_BASE, "part_04_hinge_pin_male.step")
EXPORT_STL = os.path.join(EXPORT_BASE, "part_04_hinge_pin_male.stl")

def construct_hinge_pin_male():
    shaft_length = 90.0 * config.SCALE
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
    
    # Male Glue Peg (Replaces Thread)
    peg_length = 8.5 * config.SCALE
    
    # We want a 0.4mm total diameter clearance
    # If the female bore is 2.8mm radius (5.6mm diameter), we want the male peg to be 2.6mm radius (5.2mm diameter)
    peg_radius = 2.6 * config.SCALE
    
    # Center peg
    peg_base = Part.makeCylinder(peg_radius, peg_length - 0.5 * config.SCALE)
    peg_base.translate(App.Vector(0, 0, shaft_length))
    
    # Bevel tip for easy insertion
    chamfer = Part.makeCone(peg_radius, peg_radius - 0.5 * config.SCALE, 0.5 * config.SCALE)
    chamfer.translate(App.Vector(0, 0, shaft_length + peg_length - 0.5 * config.SCALE))
    
    peg = peg_base.fuse(chamfer)
    
    male_pin = shaft.fuse([head, peg])
    male_pin = male_pin.removeSplitter()
    
    # Rotate to lay flat for printing
    # Wait, the user said "insert pins horizontally" in assembly, which means they should be oriented along X.
    # The twist lock was rotated 90 deg around Y. We should export them horizontal as before!
    male_pin.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)
    male_pin.translate(App.Vector(head_length, 0, shaft_radius))
    
    os.makedirs(EXPORT_BASE, exist_ok=True)
    male_pin.exportStep(EXPORT_STEP)
    male_pin.exportStl(EXPORT_STL)
    print(f"Exported Male Threaded Pin to {EXPORT_STEP}")

    return male_pin

def main():
    doc = App.newDocument("MalePin")
    shape = construct_hinge_pin_male()
    part = doc.addObject("Part::Feature", "PinPart")
    part.Shape = shape

if __name__ == "__main__":
    main()
