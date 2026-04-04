You are an expert in FreeCAD Python scripting and parametric CAD design.
Your task is to generate clean, modular, and parametric FreeCAD Python 
code to do following

Design a “Grocery Bag Optimized Trash Bin” with the following requirements.
Bin is built around grocery bags as the primary system
Guides bag Handle Smart Lock System handles into channels , Locks them in place
A trash bin engineered specifically to reuse grocery bags — no slipping, no sagging, no hassle.

-----------------------------------
GENERAL INSTRUCTIONS
-----------------------------------
- Use FreeCAD Python API (Part, PartDesign, Sketcher as needed)
- Split into parts to fit 3D printed build plate 256*256*256mm when sclae=1
- All paramaters should be driven by scale
- Code must be:
  - Fully parametric (all dimensions defined as variables at top)
  - Modular - generate separate file for each part
  - Generate final assembly file to use parts and create final assembly model 
  - Clean and readable
- The design should be robust and not rely on fragile geometry references
- Use proper thickness for real world daily use
- Avoid overly complex dependencies
- Prefer simple solids + boolean operations where possible
- Ensure the model recomputes without errors
- When part code is executed, also generate step and stl files into export folder
- When assembly is executed, also generate step and stl files into export/assembly folder. Generate files for each part and final assembly
- use execute_freecad_script mcp tool to visual verify designs in different angles
- visual verify using execute_freecad_script mcp tool of each part in different angles
- visual verify using execute_freecad_script mcp tool of assembly different angles

-----------------------------------
FEATURES TO IMPLEMENT
-----------------------------------

1. BIN BODY
- Rectangular with rounded corners
- Slight taper:
  - Wider at top
  - Slightly narrower mid-section
- Smooth internal walls
- Hollow interior with uniform wall thickness
- Depending on length and width, split into [arts or one part to fit 256*256*256mm 3D printer build plate when sclae=1

2. BAG RETENTION SYSTEM
- one-hand friendly
- bag tight + centered
- Snap-In Compression Ring
- Drop bag in, Push ring → clamps bag against bin wall
- Separate part
- Fits inside top opening
- Applies pressure to hold bag
- Include snap-fit features:
  - Small protrusions or tabs
  - Matching grooves in bin

3. ANTI-VACUUM GROOVES
- Add vertical grooves on inner walls
- Depth: ~1–2 mm
- Evenly spaced on all sides

4. DRIP EDGE / LIQUID TRAP
- Add small raised internal lip near bottom
- Prevents liquid spreading

7. TOP CLOSURE (OPTIONAL BUT PREFERRED)
Choose ONE simple mechanism:
- Weighted lid OR
- Pivoting flap

Keep it simple and printable:
- Minimal parts
- No complex hinges unless necessary

-----------------------------------
ASSEMBLY
-----------------------------------
- Place all parts in correct relative positions
- Ensure proper clearances:
  - Snap fits
  - Lid movement
- Use tolerances suitable for FDM printing

-----------------------------------
IMPORTANT
-----------------------------------
- Do NOT overcomplicate geometry
- Focus on functional, printable design
- Ensure all parts are manufacturable using standard FDM printers

-----------------------------------

Now generate the complete FreeCAD Python code following the above requirements.