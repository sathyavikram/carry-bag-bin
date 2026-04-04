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
    shaft_length = 51.0 * config.SCALE
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
    
    # Male Threaded Tip
    thread_length = 12.0 * config.SCALE
    pitch = 3.0 * config.SCALE
    r_minor = 2.5 * config.SCALE
    r_major = 3.5 * config.SCALE
    
    # Center core of the thread
    core = Part.makeCylinder(r_minor, thread_length)
    core.translate(App.Vector(0, 0, shaft_length))
    
    # Thread helix
    helix = Part.makeHelix(pitch, thread_length, r_minor)
    
    # Thread profile
    w = pitch * 0.4
    h = r_major - r_minor
    # Start thread profile slightly shifted into the core so it doesn't leave non-manifold edges
    prof_pts = [
        App.Vector(r_minor - 0.2, 0.0, -w/2),
        App.Vector(r_minor + h, 0.0, -w/2 + w*0.1),
        App.Vector(r_minor + h, 0.0, w/2 - w*0.1),
        App.Vector(r_minor - 0.2, 0.0, w/2),
        App.Vector(r_minor - 0.2, 0.0, -w/2)
    ]
    prof = Part.makePolygon(prof_pts)
    
    # Move profile up to start
    # No, helix starts at Z=0. We'll translate the whole thread to z = shaft_length
    wire = Part.Wire(helix)
    thread = wire.makePipeShell([prof], True, True)
    thread.translate(App.Vector(0, 0, shaft_length))
    
    # Add a chamfer to the tip, sunk by 0.2 to prevent zero-thickness face boolean failure
    tip_cone = Part.makeCone(r_major, 1.5, 1.5 * config.SCALE + 0.2)
    tip_cone.translate(App.Vector(0, 0, shaft_length + thread_length - 0.2))
    
    male_pin = shaft.fuse([head, core, thread, tip_cone])
    
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
