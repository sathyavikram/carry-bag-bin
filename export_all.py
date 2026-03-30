import os
import glob
import subprocess
import sys
import shutil

def run_part_scripts():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all part scripts
    part_files = sorted(glob.glob(os.path.join(script_dir, "part_*.py")))
    
    if not part_files:
        print("No part_*.py files found in the current directory.")
        return
        
    print(f"Found {len(part_files)} part files to execute.")
    print("=" * 40)
    
    success_count = 0
    freecad_cmd = "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"
    
    # Check if freecadcmd exists
    if not os.path.exists(freecad_cmd):
        print(f"Error: Could not find FreeCAD at {freecad_cmd}")
        print("Please ensure FreeCAD is installed.")
        return
        
    # Clear the exports directory before generating new files
    exports_dir = os.path.join(script_dir, "exports")
    if os.path.exists(exports_dir):
        print("Clearing existing files in exports/ directory...")
        for item in os.listdir(exports_dir):
            item_path = os.path.join(exports_dir, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"Failed to delete {item_path}. Reason: {e}")
    else:
        os.makedirs(exports_dir)
    
    for part_file in part_files:
        filename = os.path.basename(part_file)
        print(f"Running {filename}... (this may take a minute or two)")
        
        # We use runpy to ensure __name__ == '__main__' is respected by FreeCAD
        script_cmd = f"import runpy; runpy.run_path('{part_file}', run_name='__main__')"
        
        # We stream output using subprocess.Popen to see progress in real-time
        process = subprocess.Popen(
            [freecad_cmd, "-c", script_cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # Optionally print output or just key messages
                if "Exporting" in output or "Error" in output:
                    print(f"  > {output.strip()}")
        
        return_code = process.poll()
        
        if return_code == 0:
            print(f"✅ Successfully exported parts from {filename}")
            success_count += 1
        else:
            print(f"❌ Failed to run {filename} (Exit code: {return_code})")
            
        print("-" * 40)
        
    print(f"Finished! Successfully ran {success_count}/{len(part_files)} scripts.")
    print(f"Generated STL and STEP files should be in the exports/ directory.")

if __name__ == "__main__":
    run_part_scripts()
