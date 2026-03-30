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
from part_01_bin_body import construct_bin_body
from part_02_compression_ring import construct_compression_ring
from part_03_top_lid import construct_lid

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_BASE = os.path.join(CURRENT_DIR, "exports")

def get_part_shape(construct_func, step_filename):
    step_path = os.path.join(EXPORT_BASE, step_filename)
    if os.path.exists(step_path):
        print(f"Loading {step_filename} from {EXPORT_BASE}...")
        shape = Part.Shape()
        shape.read(step_path)
        return shape
    else:
        print(f"Building {step_filename} from source...")
        return construct_func()

def main():
    doc = App.newDocument("Assembly")
    
    bin_body = get_part_shape(construct_bin_body, "part_01_bin_body.step")
    ring = get_part_shape(construct_compression_ring, "part_02_compression_ring.step")
    lid = get_part_shape(construct_lid, "part_03_top_lid.step")
    
    # Position ring near the top. Height = config.BIN_HEIGHT
    # Increased vertical offset to avoid interference with lid
    ring.translate(App.Vector(0, 0, config.BIN_HEIGHT - 35 * config.SCALE))
    
    # Position lid on top of the bin with a small lift for clearance
    lid.translate(App.Vector(0, 0, config.BIN_HEIGHT + 1.0 * config.SCALE))
    
    body1 = doc.addObject('App::Part', 'Part_Bin')
    p1 = doc.addObject("Part::Feature", "Shape_Bin")
    p1.Shape = bin_body
    body1.addObject(p1)
    if p1.ViewObject:
        p1.ViewObject.ShapeColor = (0.7, 0.7, 0.7)
    
    body2 = doc.addObject('App::Part', 'Part_CompressionRing')
    p2 = doc.addObject("Part::Feature", "Shape_Ring")
    p2.Shape = ring
    body2.addObject(p2)
    if p2.ViewObject:
        p2.ViewObject.ShapeColor = (0.2, 0.6, 0.2)
    
    body3 = doc.addObject('App::Part', 'Part_TopLid')
    p3 = doc.addObject("Part::Feature", "Shape_Lid")
    p3.Shape = lid
    body3.addObject(p3)
    if p3.ViewObject:
        p3.ViewObject.ShapeColor = (0.2, 0.2, 0.8)
    
    # Ensure export directories exist
    os.makedirs(EXPORT_BASE, exist_ok=True)

    # And final fused assembly into exports
    assembly_shape = bin_body.fuse([ring, lid])
    assembly_shape.exportStep(os.path.join(EXPORT_BASE, "assembly.step"))
    assembly_shape.exportStl(os.path.join(EXPORT_BASE, "assembly.stl"))
    
    # Save the FreeCAD document so parts can be toggled in the GUI
    doc.recompute()
    doc.saveAs(os.path.join(CURRENT_DIR, "assembly.FCStd"))
    print(f"Exported parts, assembly, and assembly.FCStd to {EXPORT_BASE}")

if __name__ == "__main__" or __name__ == "assembly":
    main()
