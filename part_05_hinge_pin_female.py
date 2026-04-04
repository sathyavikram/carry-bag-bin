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
    
    female_pin = shaft.fuse(head)
    
    # Internal Thread Cutter (Clearance added!)
    # Bore length 14mm to fit 12mm thread + 1.5mm tip + slight extra
    bore_depth = 15.0 * config.SCALE
    pitch = 3.0 * config.SCALE
    
    # Female minor is male minor + clearance
    # Male minor is 2.5, Female minor 2.8 (0.3 radial clearance)
    f_minor = 2.8 * config.SCALE
    # Female major is male major + clearance
    # Male major is 3.5, Female major 3.8 (0.3 radial clearance)
    f_major = 3.8 * config.SCALE
    
    # The center bore cylinder to cut out the inside, radius f_minor
    bore = Part.makeCylinder(f_minor, bore_depth)
    bore.translate(App.Vector(0, 0, shaft_length - bore_depth))
    
    female_pin = female_pin.cut(bore)
    
    # Cut out the threads from the inside walls
    # We sweep a thread profile with f_minor -> f_major
    # Thread helix needs to align with male thread!
    # Pitch is the same, 3.0
    helix = Part.makeHelix(pitch, bore_depth, f_minor)
    
    # Give the thread a little extra width for horizontal clearance
    # Male width was pitch*0.4 = 1.2
    # Let's make female cut width 1.8mm (so 0.3mm wide clearance on each side of the thread teeth)
    w = pitch * 0.6
    h = f_major - f_minor
    # The cut profile extends from inside the bore out to f_major+0.2 to ensure a clean cutout
    prof_pts = [
        App.Vector(f_minor - 0.2, 0.0, -w/2),
        App.Vector(f_major + 0.2, 0.0, -w/2 + w*0.1),
        App.Vector(f_major + 0.2, 0.0, w/2 - w*0.1),
        App.Vector(f_minor - 0.2, 0.0, w/2),
        App.Vector(f_minor - 0.2, 0.0, -w/2)
    ]
    prof = Part.makePolygon(prof_pts)
    
    wire = Part.Wire(helix)
    thread_cut = wire.makePipeShell([prof], True, True)
    thread_cut.translate(App.Vector(0, 0, shaft_length - bore_depth))
    
    female_pin = female_pin.cut(thread_cut)
    
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
