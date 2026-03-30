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
EXPORT_STEP = os.path.join(EXPORT_BASE, "part_03_top_lid.step")
EXPORT_STL = os.path.join(EXPORT_BASE, "part_03_top_lid.stl")

def create_rounded_box(width, length, height, radius):
    p1 = App.Vector(-width/2, -length/2, 0)
    p2 = App.Vector(width/2, -length/2, 0)
    p3 = App.Vector(width/2, length/2, 0)
    p4 = App.Vector(-width/2, length/2, 0)
    poly = Part.makePolygon([p1, p2, p3, p4, p1])
    face = Part.Face(poly)
    if radius > 0:
        face = face.makeOffset2D(radius, join=2)
    prism = face.extrude(App.Vector(0,0,height))
    return prism

def construct_lid():
    outer_w = config.WIDTH_TOP - config.LID_TOLERANCE
    outer_l = config.LENGTH_TOP - config.LID_TOLERANCE
    
    # Base weighted lid part
    lid = create_rounded_box(outer_w, outer_l, config.LID_THICKNESS, max(0.1, config.CORNER_RADIUS))
    
    # Handle protrusion for easy grabbing
    handle = create_rounded_box(30*config.SCALE, 10*config.SCALE, 10*config.SCALE, 2*config.SCALE)
    handle.translate(App.Vector(0, -outer_l/2 + 15*config.SCALE, config.LID_THICKNESS))
    
    lid = lid.fuse(handle)
    
    # Centering Lip (Protrusion on bottom to keep lid centered)
    # Fits inside the bin opening at the top.
    # Bin Inner Dims at top:
    bin_inner_w = config.WIDTH_TOP - 2*config.WALL_THICKNESS
    bin_inner_l = config.LENGTH_TOP - 2*config.WALL_THICKNESS
    
    # Lip dims should be slightly smaller for clearance
    lip_clearance = 1.0 * config.SCALE
    lip_w = bin_inner_w - 2*lip_clearance
    lip_l = bin_inner_l - 2*lip_clearance
    lip_h = 2.5 * config.SCALE # Depth into the bin (reduced to avoid interference)
    
    lip = create_rounded_box(lip_w, lip_l, lip_h, max(0.1, config.CORNER_RADIUS - config.WALL_THICKNESS - lip_clearance))
    # Translate down. Lid is at Z=0 to THICKNESS. Lip should be at Z=-lip_h
    lip.translate(App.Vector(0, 0, -lip_h))
    
    lid = lid.fuse(lip)
    
    try:
        edges_to_fillet = []
        for edge in lid.Edges:
            z_mid = (edge.BoundBox.ZMin + edge.BoundBox.ZMax) / 2.0
            # Fillet all horizontal edges only
            if edge.BoundBox.ZLength < 0.1:  # horizontal edges
                edges_to_fillet.append(edge)
        
        if edges_to_fillet:
            lid = lid.makeFillet(config.EDGE_FILLET_RADIUS, edges_to_fillet)
    except Exception as e:
        print("Warning: Filleting top_lid failed:", e)
        
    os.makedirs(EXPORT_BASE, exist_ok=True)
    lid.exportStep(EXPORT_STEP)
    lid.exportStl(EXPORT_STL)
    print(f"Exported Lid to {EXPORT_STEP} and {EXPORT_STL}")

    return lid

def main():
    doc = App.newDocument("TopLid")
    shape = construct_lid()
    part = doc.addObject("Part::Feature", "LidPart")
    part.Shape = shape

if __name__ == "__main__":
    main()
