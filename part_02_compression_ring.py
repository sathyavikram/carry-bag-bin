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
EXPORT_STEP = os.path.join(EXPORT_BASE, "part_02_compression_ring.step")
EXPORT_STL = os.path.join(EXPORT_BASE, "part_02_compression_ring.stl")

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

def construct_compression_ring():
    # Calculate dimensions at the installation height
    ring_z_pos = config.BIN_HEIGHT - 25.0 * config.SCALE
    factor = ring_z_pos / config.BIN_HEIGHT
    
    # Outer width/length of the BIN at this height
    bin_w_at_z = config.WIDTH_BOTTOM + (config.WIDTH_TOP - config.WIDTH_BOTTOM) * factor
    bin_l_at_z = config.LENGTH_BOTTOM + (config.LENGTH_TOP - config.LENGTH_BOTTOM) * factor
    
    # Inner width/length of the BIN at this height (the available space)
    available_w = bin_w_at_z - 2*config.WALL_THICKNESS
    available_l = bin_l_at_z - 2*config.WALL_THICKNESS
    
    # Ring dimensions (fitting inside with tolerance)
    ring_w_outer = available_w - config.RING_TOLERANCE
    ring_l_outer = available_l - config.RING_TOLERANCE
    ring_w_inner = ring_w_outer - 2*config.WALL_THICKNESS
    ring_l_inner = ring_l_outer - 2*config.WALL_THICKNESS

    outer_rad = max(0.1, config.CORNER_RADIUS-config.WALL_THICKNESS)
    outer_solid = create_rounded_box(ring_w_outer, ring_l_outer, config.RING_HEIGHT, outer_rad)
    inner_rad = max(0.1, config.CORNER_RADIUS-2*config.WALL_THICKNESS)
    inner_solid = create_rounded_box(ring_w_inner, ring_l_inner, config.RING_HEIGHT, inner_rad)
    
    ring = outer_solid.cut(inner_solid)
    
    # --- Add hinge pin for snapping the ring to the bin ---
    y_max_out = ring_l_outer / 2.0 + outer_rad
    y_max_in = ring_l_inner / 2.0 + inner_rad
    rear_y_center = (y_max_out + y_max_in) / 2.0

    notch_w = 40.0 * config.SCALE
    notch = Part.makeBox(notch_w, 30.0 * config.SCALE, config.RING_HEIGHT + 10)
    notch.translate(App.Vector(-notch_w/2, rear_y_center - 10.0 * config.SCALE, -5))
    ring = ring.cut(notch)
    
    pin_radius = 2.5 * config.SCALE
    pin = Part.makeCylinder(pin_radius, notch_w)
    pin.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)
    pin.translate(App.Vector(-notch_w/2, rear_y_center, config.RING_HEIGHT / 2.0))
    
    ring = ring.fuse(pin)
    
    # --- Add front thumb tab for easy snapping ---
    front_y_center = -rear_y_center
    tab_w = 40.0 * config.SCALE
    tab_l = 15.0 * config.SCALE
    tab = Part.makeBox(tab_w, tab_l, config.RING_HEIGHT)
    tab.translate(App.Vector(-tab_w/2, front_y_center, 0))
    ring = ring.fuse(tab)
    # -----------------------------------------------------

    try:
        edges_to_fillet = []

        for edge in ring.Edges:
            z_mid = (edge.BoundBox.ZMin + edge.BoundBox.ZMax) / 2.0
            # Fillet horizontal edges only
            if edge.BoundBox.ZLength < 0.1:  # horizontal edges
                if abs(z_mid - config.RING_HEIGHT) < 0.1 or abs(z_mid) < 0.1:
                    edges_to_fillet.append(edge)
        
        if edges_to_fillet:
            ring = ring.makeFillet(config.EDGE_FILLET_RADIUS * 0.7, edges_to_fillet)
    except Exception as e:
        print("Warning: Filleting compression_ring failed:", e)
        
    os.makedirs(EXPORT_BASE, exist_ok=True)
    ring.exportStep(EXPORT_STEP)
    ring.exportStl(EXPORT_STL)
    print(f"Exported Compression Ring to {EXPORT_STEP} and {EXPORT_STL}")

    return ring

def main():
    doc = App.newDocument("CompressionRing")
    shape = construct_compression_ring()
    part = doc.addObject("Part::Feature", "RingPart")
    part.Shape = shape

if __name__ == "__main__":
    main()
