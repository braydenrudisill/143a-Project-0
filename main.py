from pathlib import Path
from itertools import zip_longest
import subprocess

def main():
    sim_folder =  Path("simulator/simulations/")
    correct_output_folder = Path("simulator/correct_output/")
    output_folder = Path("outputs/")

    for sim_file in sim_folder.iterdir():
        correct_file = correct_output_folder / Path(sim_file.name).with_suffix(".txt")
        output_file = output_folder / Path(sim_file.name).with_suffix(".txt")
        subprocess.run(["python", "simulator/simulator.py", sim_file, output_file])

        with open(output_file) as of, open(correct_file) as cf:
            for i, (out, expected) in enumerate(zip_longest(of, cf), start=1):
                if out:
                    out = out.strip()
                if expected:
                    expected = expected.strip()

                if out != expected:
                    print(f"FAIL {sim_file.stem}, line {i}: '{out}' was not '{expected}'")
                else:
                    print(f"PASS {sim_file.stem}, line {i}: '{out}'")

if __name__ == "__main__":
    main()
