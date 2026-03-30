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
    # Bottom wire
    p1_b = App.Vector(-width_b/2, -length_b/2, 0)
    p2_b = App.Vector(width_b/2, -length_b/2, 0)
    p3_b = App.Vector(width_b/2, length_b/2, 0)
    p4_b = App.Vector(-width_b/2, length_b/2, 0)
    poly_b = Part.makePolygon([p1_b, p2_b, p3_b, p4_b, p1_b])
    face_b = Part.Face(poly_b)
    if radius > 0:
        face_b = face_b.makeOffset2D(radius, join=2) # 2=arc joining

    # Top wire
    p1_t = App.Vector(-width_t/2, -length_t/2, height)
    p2_t = App.Vector(width_t/2, -length_t/2, height)
    p3_t = App.Vector(width_t/2, length_t/2, height)
    p4_t = App.Vector(-width_t/2, length_t/2, height)
    poly_t = Part.makePolygon([p1_t, p2_t, p3_t, p4_t, p1_t])
    face_t = Part.Face(poly_t)
    if radius > 0:
        face_t = face_t.makeOffset2D(radius, join=2)
        
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
    inner_solid = create_tapered_box(inner_width_t, inner_length_t, inner_width_b, inner_length_b, config.BIN_HEIGHT, inner_radius)
    
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

    # 3. Anti-vacuum Grooves (Cut from shell)
    # Create tapered lofts for grooves to follow the wall angle
    groove_cuts = []
    
    # Calculate start (bottom) and end (top) positions relative to center
    # Inner wall positions
    iw_b_x = inner_width_b / 2.0
    iw_b_y = inner_length_b / 2.0
    iw_t_x = inner_width_t / 2.0
    iw_t_y = inner_length_t / 2.0
    
    # Groove cutter depth parameter
    # We want the groove to be GROOVE_DEPTH deep into the wall.
    # The cutter should extend from (Wall_Inner - GROOVE_DEPTH) to (Wall_Inner + something)
    # Actually, simpler: Create a cutter centered at the wall surface, with appropriate thickness
    
    # Helper to make a tapered groove cutter
    def make_tapered_cutter(x_bot, x_top, y_bot, y_top, width, height):
        # Create a loft from bottom to top
        # We'll make a semi-circle or box profile? Box is easier for robustness.
        # Profile at bottom
        p_bot = Part.makePolygon([
            App.Vector(x_bot - width/2, y_bot - width/2, 0),
            App.Vector(x_bot + width/2, y_bot - width/2, 0),
            App.Vector(x_bot + width/2, y_bot + width/2, 0),
            App.Vector(x_bot - width/2, y_bot + width/2, 0),
            App.Vector(x_bot - width/2, y_bot - width/2, 0)
        ])
        f_bot = Part.Face(p_bot)
        
        # Profile at top
        p_top = Part.makePolygon([
            App.Vector(x_top - width/2, y_top - width/2, height),
            App.Vector(x_top + width/2, y_top - width/2, height),
            App.Vector(x_top + width/2, y_top + width/2, height),
            App.Vector(x_top - width/2, y_top + width/2, height),
            App.Vector(x_top - width/2, y_top - width/2, height)
        ])
        f_top = Part.Face(p_top)
        
        return Part.makeLoft([f_bot.Wires[0], f_top.Wires[0]], True)

    # Long sides (Grooves along Y axis, varying in X)
    for i in range(config.GROOVE_COUNT_LONG):
        # Y position is constant-ish (linear interpolation would be better but vertical is okay for Y if wall is mostly vertical in that plane? 
        # The bin tapers in BOTH X and Y.
        # So a groove on the long side (face normal to X) moves in X as it goes up.
        # Its Y position scales with the width? No, grooves are usually parallel to Z or fanned?
        # Let's Fan them out to match the scaling.
        
        # Fraction of width (-0.5 to 0.5)
        frac = (i - (config.GROOVE_COUNT_LONG-1)/2.0) / config.GROOVE_COUNT_LONG 
        # Actually spread them over the inner length
        
        y_pos_b = frac * inner_length_b
        y_pos_t = frac * inner_length_t
        
        # X position: On the wall. 
        # Right wall (Positive X)
        x_pos_b = inner_width_b/2.0
        x_pos_t = inner_width_t/2.0
        
        # We need the cutter to penetrate the wall by DEPTH.
        # Center the cutter at (Wall_X - Width/2 + Depth)? 
        # Easier: Center it at Wall_X. Make width = 2*Depth? No.
        # Let's place the cutter so its "inner" edge is at Wall_X - Depth.
        # Cutter Center X = (Wall_X - Depth) + Cutter_Width/2
        
        cutter_w = config.GROOVE_WIDTH # Dimension of the groove on the wall face
        cutter_thick = 10.0 # Arbitrary thickness to ensure it cuts through to the inside
        
        # Pos X for Right Wall
        cx_b = (x_pos_b - config.GROOVE_DEPTH) + cutter_thick/2
        cx_t = (x_pos_t - config.GROOVE_DEPTH) + cutter_thick/2
        
        # Create cutter for Right Wall
        # Note: The "width" arg in make_tapered_cutter is actually just side length of the square profile
        # We need a rectangular profile: Thickness (X) x Width (Y)
        # Custom loft for this
        
        # Right Wall Groove
        # Bottom Rect
        rb1 = App.Vector(cx_b - cutter_thick/2, y_pos_b - cutter_w/2, 0)
        rb2 = App.Vector(cx_b + cutter_thick/2, y_pos_b - cutter_w/2, 0)
        rb3 = App.Vector(cx_b + cutter_thick/2, y_pos_b + cutter_w/2, 0)
        rb4 = App.Vector(cx_b - cutter_thick/2, y_pos_b + cutter_w/2, 0)
        rf_b = Part.Face(Part.makePolygon([rb1, rb2, rb3, rb4, rb1]))
        
        # Top Rect
        rt1 = App.Vector(cx_t - cutter_thick/2, y_pos_t - cutter_w/2, config.BIN_HEIGHT)
        rt2 = App.Vector(cx_t + cutter_thick/2, y_pos_t - cutter_w/2, config.BIN_HEIGHT)
        rt3 = App.Vector(cx_t + cutter_thick/2, y_pos_t + cutter_w/2, config.BIN_HEIGHT)
        rt4 = App.Vector(cx_t - cutter_thick/2, y_pos_t + cutter_w/2, config.BIN_HEIGHT)
        rf_t = Part.Face(Part.makePolygon([rt1, rt2, rt3, rt4, rt1]))
        
        g_cut = Part.makeLoft([rf_b.Wires[0], rf_t.Wires[0]], True)
        groove_cuts.append(g_cut)
        
        # Left Wall Groove (Mirror X)
        # Center X = (-Wall_X + Depth) - Cutter_Width/2
        lx_b = -((x_pos_b - config.GROOVE_DEPTH) + cutter_thick/2)
        lx_t = -((x_pos_t - config.GROOVE_DEPTH) + cutter_thick/2)
        
        g_cut_mir = g_cut.mirror(App.Vector(0,0,0), App.Vector(1,0,0)) # Mirror plane normal to X? No, that's not how mirror works in API conveniently sometimes.
        # Let's just reconstruct
        lb1 = App.Vector(lx_b - cutter_thick/2, y_pos_b - cutter_w/2, 0)
        lb2 = App.Vector(lx_b + cutter_thick/2, y_pos_b - cutter_w/2, 0)
        lb3 = App.Vector(lx_b + cutter_thick/2, y_pos_b + cutter_w/2, 0)
        lb4 = App.Vector(lx_b - cutter_thick/2, y_pos_b + cutter_w/2, 0)
        lf_b = Part.Face(Part.makePolygon([lb1, lb2, lb3, lb4, lb1]))
        
        lt1 = App.Vector(lx_t - cutter_thick/2, y_pos_t - cutter_w/2, config.BIN_HEIGHT)
        lt2 = App.Vector(lx_t + cutter_thick/2, y_pos_t - cutter_w/2, config.BIN_HEIGHT)
        lt3 = App.Vector(lx_t + cutter_thick/2, y_pos_t + cutter_w/2, config.BIN_HEIGHT)
        lt4 = App.Vector(lx_t - cutter_thick/2, y_pos_t + cutter_w/2, config.BIN_HEIGHT)
        lf_t = Part.Face(Part.makePolygon([lt1, lt2, lt3, lt4, lt1]))
        
        groove_cuts.append(Part.makeLoft([lf_b.Wires[0], lf_t.Wires[0]], True))

    # Short sides (Grooves along X axis, varying in Y)
    for i in range(config.GROOVE_COUNT_SHORT):
        frac = (i - (config.GROOVE_COUNT_SHORT-1)/2.0) / config.GROOVE_COUNT_SHORT
        x_pos_b = frac * inner_width_b
        x_pos_t = frac * inner_width_t
        
        y_pos_b = inner_length_b/2.0
        y_pos_t = inner_length_t/2.0
        
        cutter_w = config.GROOVE_WIDTH
        cutter_thick = 10.0
        
        # Front Wall (+Y)
        cy_b = (y_pos_b - config.GROOVE_DEPTH) + cutter_thick/2
        cy_t = (y_pos_t - config.GROOVE_DEPTH) + cutter_thick/2
        
        # Bottom
        fb1 = App.Vector(x_pos_b - cutter_w/2, cy_b - cutter_thick/2, 0)
        fb2 = App.Vector(x_pos_b + cutter_w/2, cy_b - cutter_thick/2, 0)
        fb3 = App.Vector(x_pos_b + cutter_w/2, cy_b + cutter_thick/2, 0)
        fb4 = App.Vector(x_pos_b - cutter_w/2, cy_b + cutter_thick/2, 0)
        ff_b = Part.Face(Part.makePolygon([fb1, fb2, fb3, fb4, fb1]))
        
        # Top
        ft1 = App.Vector(x_pos_t - cutter_w/2, cy_t - cutter_thick/2, config.BIN_HEIGHT)
        ft2 = App.Vector(x_pos_t + cutter_w/2, cy_t - cutter_thick/2, config.BIN_HEIGHT)
        ft3 = App.Vector(x_pos_t + cutter_w/2, cy_t + cutter_thick/2, config.BIN_HEIGHT)
        ft4 = App.Vector(x_pos_t - cutter_w/2, cy_t + cutter_thick/2, config.BIN_HEIGHT)
        ff_t = Part.Face(Part.makePolygon([ft1, ft2, ft3, ft4, ft1]))
        
        groove_cuts.append(Part.makeLoft([ff_b.Wires[0], ff_t.Wires[0]], True))
        
        # Back Wall (-Y)
        cy_b_neg = -((y_pos_b - config.GROOVE_DEPTH) + cutter_thick/2)
        cy_t_neg = -((y_pos_t - config.GROOVE_DEPTH) + cutter_thick/2)
        
        bb1 = App.Vector(x_pos_b - cutter_w/2, cy_b_neg - cutter_thick/2, 0)
        bb2 = App.Vector(x_pos_b + cutter_w/2, cy_b_neg - cutter_thick/2, 0)
        bb3 = App.Vector(x_pos_b + cutter_w/2, cy_b_neg + cutter_thick/2, 0)
        bb4 = App.Vector(x_pos_b - cutter_w/2, cy_b_neg + cutter_thick/2, 0)
        bf_b = Part.Face(Part.makePolygon([bb1, bb2, bb3, bb4, bb1]))
        
        bt1 = App.Vector(x_pos_t - cutter_w/2, cy_t_neg - cutter_thick/2, config.BIN_HEIGHT)
        bt2 = App.Vector(x_pos_t + cutter_w/2, cy_t_neg - cutter_thick/2, config.BIN_HEIGHT)
        bt3 = App.Vector(x_pos_t + cutter_w/2, cy_t_neg + cutter_thick/2, config.BIN_HEIGHT)
        bt4 = App.Vector(x_pos_t - cutter_w/2, cy_t_neg + cutter_thick/2, config.BIN_HEIGHT)
        bf_t = Part.Face(Part.makePolygon([bt1, bt2, bt3, bt4, bt1]))
        
        groove_cuts.append(Part.makeLoft([bf_b.Wires[0], bf_t.Wires[0]], True))
        
    # Shift grooves up by wall thickness so they don't cut the floor?
    # Actually our loft goes from 0 to HEIGHT. The floor is at 0 to WALL_THICKNESS.
    # The grooves should probably start above the floor.
    # But cutting the floor slightly is fine, or we can just subtract them.
    # To be clean, let's translate them up or boolean cut carefully.
    # Current loft is 0 to HEIGHT. Floor is 0 to WALL_THICKNESS.
    # If we cut, we might cut the floor.
    # Let's adjust z of bottom polys to WALL_THICKNESS? 
    # Or just let it be, it's a liquid trap at bottom anyway.
    # Actually, if we cut through the floor edge, it might leak if not careful.
    # The floor is solid `outer_solid` cut by `inner_solid` (which is translated up).
    # `bin_shell` has a floor of thickness `WALL_THICKNESS`.
    # `groove_cuts` start at Z=0.
    # If we cut, we might cut into the floor side walls.
    # They won't cut THROUGH the floor bottom unless groove depth > wall thickness (it isn't).
    # So it's fine.
    
    for g in groove_cuts:
        bin_shell = bin_shell.cut(g)
        
    # Snap-fit grooves / Handle Channels
    # We cut channels from the top down to the ring position.
    # This allows the tabs to slide down (guiding the ring and bag handles)
    # until the ring body wedges against the tapered walls.
    
    snap_tab_width = 10.0 * config.SCALE
    snap_tab_depth = 1.5 * config.SCALE
    ring_z_pos = config.BIN_HEIGHT - 25.0 * config.SCALE
    tab_z_pos = ring_z_pos + 5.0 * config.SCALE

    # Corner radius used for both ring outer solid and bin inner solid
    outer_rad_ring = max(0.1, config.CORNER_RADIUS - config.WALL_THICKNESS)
    
    # Calculate Dimensions at tab_z_pos
    w_at_tab, l_at_tab = get_dims_at_z(tab_z_pos)
    inner_w_at_tab = w_at_tab - 2*config.WALL_THICKNESS
    inner_l_at_tab = l_at_tab - 2*config.WALL_THICKNESS
    
    # Channel Cutters (From Tab Z to Top)
    channel_height = config.BIN_HEIGHT - tab_z_pos
    
    # We use a tapered cutter or just a box that is deep enough?
    # Since the wall tapers OUT as we go up, a vertical box starting at the inner wall of the bottom
    # will cut deeper at the bottom and shallower at the top? No.
    # Wall moves OUT (wider).
    # If we define a box at the Lock Width, it will be INSIDE the air at the top.
    # Wait, Top Width > Lock Width.
    # If I put a box at X = Lock_Width/2 + Depth/2.
    # At Top, Wall X is Top_Width/2.
    # If Lock_Width < Top_Width.
    # The box might be far from the wall at the top?
    # No, we want to cut INTO the wall.
    # We want a channel of constant depth relative to the wall?
    # Or a vertical channel?
    # If vertical channel:
    #   The ring tabs are at fixed X/Y (relative to ring center).
    #   So the channel MUST be vertical (or match the ring, which is vertical walled).
    #   The Ring is a straight extrusion.
    #   So the Tabs are vertical columns.
    #   So the Channel MUST be a vertical cut.
    #   The cut should be positioned to match the Ring Tabs.
    #   Ring Tabs are at `ring_w_outer` (calculated at installation height).
    #   So the cuts should be at the same X/Y location.
    
    # Re-calculate Ring dimensions (from compression_ring logic, or just re-derive)
    # In compression_ring, ring fits at ring_z_pos.
    # Ring Outer = Inner_Bin_At_Ring_Z - Tolerance.
    # Tabs are on top of that.
    
    # So we place the cutters at the Ring Tab location.
    # Ring Outer W at Z=215:
    available_w = inner_w_at_tab # approx
    available_l = inner_l_at_tab
    
    ring_w_outer = available_w - config.RING_TOLERANCE
    ring_l_outer = available_l - config.RING_TOLERANCE
    
    # Channel cutter positions: at the ring's actual outer wall surface (flat face),
    # which = ring_w_outer/2 + outer_rad_ring (offset2D expands the polygon by radius).
    # Tabs protrude snap_tab_depth beyond this surface into the bin wall.
    cutter_d = snap_tab_depth + 2.0 * config.SCALE  # depth through wall: tab depth + clearance
    cutter_w = snap_tab_width + 1.0 * config.SCALE
    cutter_h = channel_height + 1.0 * config.SCALE

    # 4 Cutouts - Vertical Columns aligned to actual ring tab positions
    
    # Right (+X): tab outer face anchored at ring_w_outer/2 + outer_rad_ring
    rx = ring_w_outer/2 + outer_rad_ring
    tcut1 = Part.makeBox(cutter_d, cutter_w, cutter_h)
    tcut1.translate(App.Vector(rx, -cutter_w/2, tab_z_pos))
    
    # Left (-X): mirror of right
    tcut2 = Part.makeBox(cutter_d, cutter_w, cutter_h)
    tcut2.translate(App.Vector(-rx - cutter_d, -cutter_w/2, tab_z_pos))
    
    # Back (+Y): tab outer face anchored at ring_l_outer/2 + outer_rad_ring
    ry = ring_l_outer/2 + outer_rad_ring
    tcut3 = Part.makeBox(cutter_w, cutter_d, cutter_h)
    tcut3.translate(App.Vector(-cutter_w/2, ry, tab_z_pos))
    
    # Front (-Y): mirror of back
    tcut4 = Part.makeBox(cutter_w, cutter_d, cutter_h)
    tcut4.translate(App.Vector(-cutter_w/2, -ry - cutter_d, tab_z_pos))
    
    bin_shell = bin_shell.cut([tcut1, tcut2, tcut3, tcut4])
        
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
            bin_shell = bin_shell.makeFillet(config.EDGE_FILLET_RADIUS, edges_to_fillet)
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
