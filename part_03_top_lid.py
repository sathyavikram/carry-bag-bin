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
    fillet_r = min(10.0 * config.SCALE, radius * 0.5) if radius > 0 else 0
    chamfer_r = radius
    w2 = width/2 + chamfer_r
    l2 = length/2 + chamfer_r
    p1 = App.Vector(-w2 + chamfer_r, -l2, 0)
    p2 = App.Vector(w2 - chamfer_r, -l2, 0)
    p3 = App.Vector(w2, -l2 + chamfer_r, 0)
    p4 = App.Vector(w2, l2 - chamfer_r, 0)
    p5 = App.Vector(w2 - chamfer_r, l2, 0)
    p6 = App.Vector(-w2 + chamfer_r, l2, 0)
    p7 = App.Vector(-w2, l2 - chamfer_r, 0)
    p8 = App.Vector(-w2, -l2 + chamfer_r, 0)
    poly = Part.makePolygon([p1, p2, p3, p4, p5, p6, p7, p8, p1])
    face = Part.Face(poly)
    if fillet_r > 0:
        face = face.makeOffset2D(-fillet_r, join=1)
        face = face.makeOffset2D(fillet_r, join=0)
    prism = face.extrude(App.Vector(0,0,height))
    return prism

def construct_lid():
    # To keep the ultimate outer bounds of the lid flush with the outer dimensions of the bin
    # while changing the corner radius natively, we must recalculate the core straight dimensions.
    total_w = config.WIDTH_TOP + 2 * config.CORNER_RADIUS - config.LID_TOLERANCE
    total_l = config.LENGTH_TOP + 2 * config.CORNER_RADIUS - config.LID_TOLERANCE
    
    outer_w = total_w - 2 * config.LID_CORNER_RADIUS
    outer_l = total_l - 2 * config.LID_CORNER_RADIUS
    
    # Base weighted lid part
    lid = create_rounded_box(outer_w, outer_l, config.LID_THICKNESS, max(0.1, config.LID_CORNER_RADIUS))
    
    # Stylish Modern Handle
    # A wide, gently sloped front lip that provides a large, easy-to-grab under-surface
    handle_w = 100.0 * config.SCALE
    handle_l = 20.0 * config.SCALE
    handle_h = 10.0 * config.SCALE
    
    # Create the base block for the handle
    handle_base = create_rounded_box(handle_w, handle_l, handle_h, 5.0 * config.SCALE)
    
    # Slant the back side of the handle using a cut for a sleek, ergonomic feel
    cut_box = Part.makeBox(handle_w + 10, handle_l + 10, handle_h + 10)
    cut_box.rotate(App.Vector(0,0,0), App.Vector(1,0,0), 30) # 30 degree ergonomic slope
    cut_box.translate(App.Vector(-(handle_w+10)/2, handle_l/2 - 10*config.SCALE, 5.0*config.SCALE))
    handle = handle_base.cut(cut_box)
    
    # Fillet the sharp edge of the handle cut
    try:
        edges_to_fillet_h = []
        for edge in handle.Edges:
            if edge.BoundBox.ZLength < 0.1 and edge.BoundBox.ZMax > handle_h - 1:
                edges_to_fillet_h.append(edge)
        if edges_to_fillet_h:
            handle = handle.makeFillet(2.0, edges_to_fillet_h)
    except:
        pass

    # Position handle at the correct location on the lid
    handle.translate(App.Vector(0, -total_l/2 + 2.0*config.SCALE, config.LID_THICKNESS))
    
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
    
    # Hinge mechanism
    def make_lid_hinge(width, y_start, y_center):
        z_drop = -6.0 * config.SCALE
        p1 = App.Vector(-width/2, y_start, 0)
        p2 = App.Vector(width/2, y_start, 0)
        p3 = App.Vector(width/2, y_start, config.LID_THICKNESS)
        p4 = App.Vector(-width/2, y_start, config.LID_THICKNESS)
        f_start = Part.Face(Part.makePolygon([p1, p2, p3, p4, p1]))
        
        cyl_r = 5.0 * config.SCALE
        p1e = App.Vector(-width/2, y_center, z_drop - cyl_r)
        p2e = App.Vector(width/2, y_center, z_drop - cyl_r)
        p3e = App.Vector(width/2, y_center, z_drop + cyl_r)
        p4e = App.Vector(-width/2, y_center, z_drop + cyl_r)
        f_end = Part.Face(Part.makePolygon([p1e, p2e, p3e, p4e, p1e]))
        
        loft = Part.makeLoft([f_start.Wires[0], f_end.Wires[0]], True)
        
        cyl = Part.makeCylinder(cyl_r, width)
        cyl.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)
        cyl.translate(App.Vector(-width/2, y_center, z_drop))
        
        pin_width = width + 10.0 * config.SCALE
        pin = Part.makeCylinder(config.HINGE_PIN_RADIUS, pin_width)
        pin.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)
        pin.translate(App.Vector(-pin_width/2, y_center, z_drop))
        
        return loft.fuse([cyl, pin])

    h_width = 79.0 * config.SCALE
    h_start = (total_l / 2.0) - 2.0 * config.SCALE
    h_center = (config.LENGTH_TOP / 2.0) + config.CORNER_RADIUS + 18.0 * config.SCALE
    
    lid_hinge = make_lid_hinge(h_width, h_start, h_center)
    lid = lid.fuse(lid_hinge)
    
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
