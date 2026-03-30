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
EXPORT_STEP = os.path.join(EXPORT_BASE, "part_01_bin_body.step")
EXPORT_STL = os.path.join(EXPORT_BASE, "part_01_bin_body.stl")

def create_tapered_box(width_t, length_t, width_b, length_b, height, radius):
    def make_filleted_chamfer_face(w, l, z, r):
        fillet_r = min(10.0 * config.SCALE, r * 0.5) if r > 0 else 0
        chamfer_r = r
        w2 = w/2 + chamfer_r
        l2 = l/2 + chamfer_r
        # Chamfer points
        p1 = App.Vector(-w2 + chamfer_r, -l2, z)
        p2 = App.Vector(w2 - chamfer_r, -l2, z)
        p3 = App.Vector(w2, -l2 + chamfer_r, z)
        p4 = App.Vector(w2, l2 - chamfer_r, z)
        p5 = App.Vector(w2 - chamfer_r, l2, z)
        p6 = App.Vector(-w2 + chamfer_r, l2, z)
        p7 = App.Vector(-w2, l2 - chamfer_r, z)
        p8 = App.Vector(-w2, -l2 + chamfer_r, z)
        poly = Part.makePolygon([p1, p2, p3, p4, p5, p6, p7, p8, p1])
        f = Part.Face(poly)
        if fillet_r > 0:
            f = f.makeOffset2D(-fillet_r, join=1)
            f = f.makeOffset2D(fillet_r, join=0)
        return f

    face_b = make_filleted_chamfer_face(width_b, length_b, 0, radius)
    face_t = make_filleted_chamfer_face(width_t, length_t, height, radius)
        
    loft = Part.makeLoft([face_b.Wires[0], face_t.Wires[0]], True)
    return loft

def construct_bin_body():
    # Outer body
    outer_solid = create_tapered_box(config.WIDTH_TOP, config.LENGTH_TOP, config.WIDTH_BOTTOM, config.LENGTH_BOTTOM, config.BIN_HEIGHT, config.CORNER_RADIUS)
    
    # Inner body (hollow cut)
    inner_width_t = config.WIDTH_TOP - 2*config.WALL_THICKNESS
    inner_length_t = config.LENGTH_TOP - 2*config.WALL_THICKNESS
    inner_width_b = config.WIDTH_BOTTOM - 2*config.WALL_THICKNESS
    inner_length_b = config.LENGTH_BOTTOM - 2*config.WALL_THICKNESS
    inner_radius = max(0.1, config.CORNER_RADIUS - config.WALL_THICKNESS)
    inner_solid = create_tapered_box(inner_width_t, inner_length_t, inner_width_b, inner_length_b, config.BIN_HEIGHT + config.WALL_THICKNESS + 5.0, inner_radius)
    
    # Shift inner solid up by Wall Thickness to ensure solid bottom
    inner_solid.translate(App.Vector(0, 0, config.WALL_THICKNESS))
    
    # Basic hollow shell
    bin_shell = outer_solid.cut(inner_solid)
    
    # Calculate dimensions at specific heights for accurate cutting/sizing
    def get_dims_at_z(z):
        factor = z / config.BIN_HEIGHT
        w = config.WIDTH_BOTTOM + (config.WIDTH_TOP - config.WIDTH_BOTTOM) * factor
        l = config.LENGTH_BOTTOM + (config.LENGTH_TOP - config.LENGTH_BOTTOM) * factor
        return w, l

    # 5. Liquid Trap (Add inside at bottom)
    trap_outer_w = inner_width_b + 5.0 * config.SCALE
    trap_outer_l = inner_length_b + 5.0 * config.SCALE
    trap_inner_w = inner_width_b - 2*config.TRAP_LIP_WIDTH
    trap_inner_l = inner_length_b - 2*config.TRAP_LIP_WIDTH
    
    trap_outer_solid = create_tapered_box(trap_outer_w, trap_outer_l, trap_outer_w, trap_outer_l, config.TRAP_LIP_HEIGHT, inner_radius + 2.5 * config.SCALE)
    trap_inner_solid = create_tapered_box(trap_inner_w, trap_inner_l, trap_inner_w, trap_inner_l, config.TRAP_LIP_HEIGHT, inner_radius - config.TRAP_LIP_WIDTH)
    
    trap_ring = trap_outer_solid.cut(trap_inner_solid)
    trap_ring.translate(App.Vector(0, 0, config.WALL_THICKNESS))
    
    bin_shell = bin_shell.fuse(trap_ring)
    
    # 5.5 Hinge Knuckles on Bin (+Y side)
    def make_bin_knuckle(hole_radius):
        k_width = 10.0 * config.SCALE
        k_ext = 20.0 * config.SCALE
        k_z = 10.0 * config.SCALE
        
        box = Part.makeBox(k_width, k_ext, k_z)
        cyl = Part.makeCylinder(k_z/2.0, k_width)
        cyl.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90) 
        cyl.translate(App.Vector(0, k_ext, k_z/2.0))
        knuckle = box.fuse(cyl)
        
        hole = Part.makeCylinder(hole_radius, k_width + 2.0)
        hole.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)
        hole.translate(App.Vector(-1.0, k_ext, k_z/2.0))
        return knuckle.cut(hole)

    k1 = make_bin_knuckle(config.HINGE_PIN_RADIUS + config.HINGE_TOLERANCE)
    y_pos = (config.LENGTH_TOP / 2.0) + config.CORNER_RADIUS - 2.0 * config.SCALE
    z_pos = config.BIN_HEIGHT - 10.0 * config.SCALE
    k1.translate(App.Vector(40.0 * config.SCALE, y_pos, z_pos))
    
    k2 = make_bin_knuckle(config.HINGE_PIN_RADIUS + config.HINGE_TOLERANCE)
    k2.translate(App.Vector(-50.0 * config.SCALE, y_pos, z_pos))
    
    bin_shell = bin_shell.fuse([k1, k2])

    # 5.6 Inner Hooks for Compression Ring
    ring_z_pos = config.BIN_HEIGHT - 25.0 * config.SCALE
    factor_z = ring_z_pos / config.BIN_HEIGHT
    
    bin_w_at_z = config.WIDTH_BOTTOM + (config.WIDTH_TOP - config.WIDTH_BOTTOM) * factor_z
    bin_l_at_z = config.LENGTH_BOTTOM + (config.LENGTH_TOP - config.LENGTH_BOTTOM) * factor_z
    
    available_w = bin_w_at_z - 2*config.WALL_THICKNESS
    available_l = bin_l_at_z - 2*config.WALL_THICKNESS
    
    ring_w_outer = available_w - config.RING_TOLERANCE
    ring_l_outer = available_l - config.RING_TOLERANCE
    ring_l_inner = ring_l_outer - 2*config.WALL_THICKNESS

    outer_rad = max(0.1, config.CORNER_RADIUS-config.WALL_THICKNESS)
    inner_rad = max(0.1, config.CORNER_RADIUS-2*config.WALL_THICKNESS)

    y_max_out = ring_l_outer / 2.0 + outer_rad
    y_max_in = ring_l_inner / 2.0 + inner_rad
    rear_y_center = (y_max_out + y_max_in) / 2.0

    bin_inner_y = available_l / 2.0 + outer_rad

    block_w = 20.0 * config.SCALE
    block = Part.makeBox(block_w, bin_inner_y - (rear_y_center - 3.5*config.SCALE) + 2.0*config.SCALE, 15.0*config.SCALE)
    block.translate(App.Vector(-block_w/2.0, rear_y_center - 3.5*config.SCALE, ring_z_pos - 10.0*config.SCALE))

    hole = Part.makeCylinder(3.0 * config.SCALE, block_w + 10.0*config.SCALE)
    hole.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)
    hole.translate(App.Vector(-block_w/2.0 - 5.0*config.SCALE, rear_y_center, ring_z_pos))

    slot = Part.makeBox(block_w + 10.0*config.SCALE, 6.0*config.SCALE, 15.0*config.SCALE)
    slot.translate(App.Vector(-block_w/2.0 - 5.0*config.SCALE, rear_y_center - 3.0*config.SCALE, ring_z_pos))

    hook = block.cut(hole).cut(slot)
    bin_shell = bin_shell.fuse(hook)

    # 5.7 Front Snap Catch for Compression Ring
    ring_top_z = ring_z_pos + 10.0 * config.SCALE
    factor_z_top = ring_top_z / config.BIN_HEIGHT
    bin_l_at_z_top = config.LENGTH_BOTTOM + (config.LENGTH_TOP - config.LENGTH_BOTTOM) * factor_z_top
    available_l_top = bin_l_at_z_top - 2*config.WALL_THICKNESS
    bin_inner_y_top = available_l_top / 2.0 + outer_rad

    catch_w = 40.0 * config.SCALE
    catch_r = 1.5 * config.SCALE
    front_snap = Part.makeCylinder(catch_r, catch_w)
    front_snap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)
    front_snap.translate(App.Vector(-catch_w/2.0, -bin_inner_y_top + 0.5*config.SCALE, ring_top_z))
    bin_shell = bin_shell.fuse(front_snap)

    # 6. Fillets to remove sharp edges
    try:
        edges_to_fillet = []
        for edge in bin_shell.Edges:
            z_mid = (edge.BoundBox.ZMin + edge.BoundBox.ZMax) / 2.0
            # Fillet top rim and bottom edges only (horizontal)
            # We skip vertical edges because the main body is already rounded by CORNER_RADIUS
            if edge.BoundBox.ZLength < 0.1:  # horizontal edges
                if abs(z_mid - config.BIN_HEIGHT) < 0.1 or abs(z_mid) < 0.1:
                    edges_to_fillet.append(edge)
        
        if edges_to_fillet:
            bin_shell = bin_shell.makeFillet(min(config.EDGE_FILLET_RADIUS, config.WALL_THICKNESS/2.0 - 0.1), edges_to_fillet)
    except Exception as e:
        print("Warning: Filleting bin_body failed:", e)
        # Fallback: Try smaller radius if failed
        try:
            if edges_to_fillet:
                 bin_shell = bin_shell.makeFillet(config.EDGE_FILLET_RADIUS/2, edges_to_fillet)
        except:
             pass
    
    os.makedirs(EXPORT_BASE, exist_ok=True)
    bin_shell.exportStep(EXPORT_STEP)
    bin_shell.exportStl(EXPORT_STL)
    print(f"Exported Bin Body to {EXPORT_STEP} and {EXPORT_STL}")

    return bin_shell

def main():
    doc = App.newDocument("BinBody")
    body_shape = construct_bin_body()
    part = doc.addObject("Part::Feature", "BinBodyPart")
    part.Shape = body_shape

if __name__ == "__main__":
    main()
