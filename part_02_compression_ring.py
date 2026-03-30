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
    inner_solid = create_rounded_box(ring_w_inner, ring_l_inner, config.RING_HEIGHT, max(0.1, config.CORNER_RADIUS-2*config.WALL_THICKNESS))
    
    ring = outer_solid.cut(inner_solid)
    
    # Add snap-tabs on the outer edge (middle of all 4 sides)
    # We add a chamfer to the bottom of the tabs for easier insertion
    
    def make_chamfered_tab(width, depth, height):
        # Construct a prism with a chamfered bottom-outer corner
        # Profile in XZ plane (at Y=0)
        # X goes from 0 to depth
        # Z goes from 0 to height
        # Chamfer at corner (X=depth, Z=0)
        chamfer = depth * 0.6
        if chamfer > height: chamfer = height - 0.1
        
        # Points for the side profile
        p1 = App.Vector(0, 0, 0)
        p2 = App.Vector(depth - chamfer, 0, 0)
        p3 = App.Vector(depth, 0, chamfer) # Chamfer slope
        p4 = App.Vector(depth, 0, height)
        p5 = App.Vector(0, 0, height)
        
        # Create polygon and face
        poly = Part.makePolygon([p1, p2, p3, p4, p5, p1])
        face = Part.Face(poly)
        
        # Extrude in Y direction to create the width
        tab = face.extrude(App.Vector(0, width, 0))
        
        return tab

    # Adjust tab positions by outer_rad to place them on the actual outer surface
    # Right Tab (+X)
    tab1 = make_chamfered_tab(config.SNAP_TAB_WIDTH, config.SNAP_TAB_DEPTH, config.RING_HEIGHT/2.0)
    tab1.translate(App.Vector(ring_w_outer/2 + outer_rad, -config.SNAP_TAB_WIDTH/2, config.RING_HEIGHT/4.0))
    
    # Left Tab (-X)
    tab2 = make_chamfered_tab(config.SNAP_TAB_WIDTH, config.SNAP_TAB_DEPTH, config.RING_HEIGHT/2.0)
    tab2.rotate(App.Vector(0,0,0), App.Vector(0,0,1), 180)
    tab2.translate(App.Vector(-(ring_w_outer/2 + outer_rad), config.SNAP_TAB_WIDTH/2, config.RING_HEIGHT/4.0))
    
    # Back Tab (+Y)
    tab3 = make_chamfered_tab(config.SNAP_TAB_WIDTH, config.SNAP_TAB_DEPTH, config.RING_HEIGHT/2.0)
    tab3.rotate(App.Vector(0,0,0), App.Vector(0,0,1), 90)
    tab3.translate(App.Vector(config.SNAP_TAB_WIDTH/2, ring_l_outer/2 + outer_rad, config.RING_HEIGHT/4.0))
    
    # Front Tab (-Y)
    tab4 = make_chamfered_tab(config.SNAP_TAB_WIDTH, config.SNAP_TAB_DEPTH, config.RING_HEIGHT/2.0)
    tab4.rotate(App.Vector(0,0,0), App.Vector(0,0,1), -90)
    tab4.translate(App.Vector(-config.SNAP_TAB_WIDTH/2, -(ring_l_outer/2 + outer_rad), config.RING_HEIGHT/4.0))
    
    ring = ring.fuse([tab1, tab2, tab3, tab4])
    
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
