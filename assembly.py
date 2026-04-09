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
from part_04_hinge_pin_male import construct_hinge_pin_male
from part_05_hinge_pin_female import construct_hinge_pin_female

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
    male_pin = get_part_shape(construct_hinge_pin_male, "part_04_hinge_pin_male.step")
    female_pin = get_part_shape(construct_hinge_pin_female, "part_05_hinge_pin_female.step")
    
    # Position ring near the top
    ring.translate(App.Vector(0, 0, config.BIN_HEIGHT - (config.RING_HEIGHT + 2.0 * config.SCALE)))
    
    # Position lid on top
    lid.translate(App.Vector(0, 0, config.BIN_HEIGHT + 1.0 * config.SCALE))
    
    # Center lines for hinges
    h_y = (config.LENGTH_TOP / 2.0) + config.CORNER_RADIUS + 18.0 * config.SCALE
    h_z = config.BIN_HEIGHT + 1.0 * config.SCALE - 6.0 * config.SCALE
    
    # Position Male Pin
    # The pin export puts the outer face of the head at X=0 and points +X.
    # The shaft axis is at Z = 4.5
    male_pin.translate(App.Vector(0, 0, -4.5 * config.SCALE))
    # Pivot 180 to enter from right side facing inwards (now points -X, inner head surface is at X = -3)
    male_pin.rotate(App.Vector(0,0,0), App.Vector(0,0,1), 180)
    male_pin.translate(App.Vector(53.0 * config.SCALE, h_y, h_z))
    
    # Position Female Pin
    # The female pin also has outer head face at X=0, points +X. Inner head surface is at X = 3
    # It will enter from the left side pointing +X
    female_pin.translate(App.Vector(0, 0, -4.5 * config.SCALE))
    female_pin.translate(App.Vector(-53.0 * config.SCALE, h_y, h_z))
    
    body1 = doc.addObject('App::Part', 'Part_Bin')
    p1 = doc.addObject("Part::Feature", "Shape_Bin")
    p1.Shape = bin_body
    body1.addObject(p1)
    if p1.ViewObject: p1.ViewObject.ShapeColor = (0.7, 0.7, 0.7)
    
    body2 = doc.addObject('App::Part', 'Part_CompressionRing')
    p2 = doc.addObject("Part::Feature", "Shape_Ring")
    p2.Shape = ring
    body2.addObject(p2)
    if p2.ViewObject: p2.ViewObject.ShapeColor = (0.2, 0.6, 0.2)
    
    body3 = doc.addObject('App::Part', 'Part_TopLid')
    p3 = doc.addObject("Part::Feature", "Shape_Lid")
    p3.Shape = lid
    body3.addObject(p3)
    if p3.ViewObject: p3.ViewObject.ShapeColor = (0.2, 0.2, 0.8)
        
    body4 = doc.addObject('App::Part', 'Part_MalePin')
    p4 = doc.addObject("Part::Feature", "Shape_Male")
    p4.Shape = male_pin
    body4.addObject(p4)
    if p4.ViewObject: p4.ViewObject.ShapeColor = (0.8, 0.2, 0.2)
        
    body5 = doc.addObject('App::Part', 'Part_FemalePin')
    p5 = doc.addObject("Part::Feature", "Shape_Female")
    p5.Shape = female_pin
    body5.addObject(p5)
    if p5.ViewObject: p5.ViewObject.ShapeColor = (0.8, 0.4, 0.4)
    
    os.makedirs(EXPORT_BASE, exist_ok=True)
    import Import
    Import.export([body1, body2, body3, body4, body5], os.path.join(EXPORT_BASE, "assembly.step"))
    assembly_compound = Part.makeCompound([bin_body, ring, lid, male_pin, female_pin])
    assembly_compound.exportStl(os.path.join(EXPORT_BASE, "assembly.stl"))

if __name__ == "__main__" or __name__ == "assembly":
    main()
