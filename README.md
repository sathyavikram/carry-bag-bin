# Carry Bag Bin

“Grocery Bag Optimized Trash Bin”

A trash bin engineered specifically to reuse grocery bags — no slipping, no sagging, no hassle.
The bin is built around grocery bags as the primary bag system. It guides bag handles into channels and locks them in place using a smart lock system (compression ring). 

## Component Parts
- **Bin Body (`part_01_bin_body.py`):** The main container with dedicated geometry to fit grocery bags.
- **Compression Ring (`part_02_compression_ring.py`):** An internal locking mechanism with snap tabs to secure the bag over the edges so it never falls inside.
- **Top Lid (`part_03_top_lid.py`):** A top cover to keep the aesthetic clean and contain odors.

## Project Structure & Generation

This project uses FreeCAD's Python API to parametrically generate the 3D models. All dimensions and scaling are controlled via `config.py`.

To generate the `.stl` and `.step` files along with an interactive FreeCAD file, run the assembly script through FreeCAD's headless command line.

For macOS users, run the following in your terminal:

```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd assembly.py
```

The script intelligently loads existing `.step` files to save time, or regenerates them from scratch using the individual part scripts if they are missing.

The generated files are saved into the `exports/` directory:
- Individual parts ready for 3D printing or inspection (`part_01_bin_body.stl/.step`, etc.).
- A combined `assembly.step` and `assembly.stl`.

Additionally, the script puts an `assembly.FCStd` file in the main directory. You can open this directly in the FreeCAD GUI to toggle parts on/off as solid bodies and visually inspect the assembly.

## Assembly & Usage Instructions

Once you have 3D printed the three main parts, follow these steps to use the bin:

1. **Prepare the Bin:** Place the **Bin Body** on a flat surface.
2. **Insert the Bag:** Place a standard grocery plastic bag inside the bin.
3. **Secure the Edges:** Stretch the handles and the top edges of the bag over the outside rim of the bin body.
4. **Lock in Place:** Take the **Compression Ring** and align it with the inner rim. Push it fully down. The outer snap tabs will connect securely, pinning the bag taut against the inner walls to prevent slipping when under load.
5. **Cover the Bin:** Place the **Top Lid** onto the top of the bin. The lid provides clearance over the compression ring.
