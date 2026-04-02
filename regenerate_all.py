"""
Script to re-generate all preprocessed chunks using the latest pipeline logic.
This ensures consistency across all document sources.
"""

import subprocess
import os

SCRIPTS_DIR = "scripts"
SOURCE_SCRIPTS = [
    "clean_fire_safety.py",
    "clean_labour_act.py",
    "clean_machine_manual.py",
    "clean_compliance.py",
    "clean_compliance2.py",
    "clean_sop.py"
]

def main():
    print("Starting regeneration of all chunk files...\n")
    
    # Ensure we are in the Experiment/ directory
    cwd = os.getcwd()
    if not os.path.isdir("scripts") or not os.path.isdir("raw"):
        print("Error: Please run this script from the Experiment/ directory.")
        return

    for script in SOURCE_SCRIPTS:
        script_path = os.path.join(SCRIPTS_DIR, script)
        if not os.path.exists(script_path):
            print(f"Skipping {script}: file not found.")
            continue
            
        print(f"Running {script}...")
        try:
            # We run the script using python3
            result = subprocess.run(["python3", script_path], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  Successfully regenerated chunks for {script}")
            else:
                # Some scripts might complain if the raw PDF is missing (like clean_sop.py)
                print(f"  Error running {script}:")
                print(result.stdout)
                print(result.stderr)
        except Exception as e:
            print(f"  Exception while running {script}: {e}")
        print("-" * 40)

    print("\nAll done!")

if __name__ == "__main__":
    main()
