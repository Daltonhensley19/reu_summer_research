import pathlib as path
from pathlib import Path
import uuid
import argparse
import subprocess
import re
import matplotlib.pyplot as plt
from decimal import Decimal
import seaborn as sns
import pandas as pd


# Function which extracts `output*` files
def get_out_files() -> list[path.Path]:
    outfile_paths = path.Path()

    outfile_paths = list(outfile_paths.glob("output*"))

    # We check to see if there is any `outfiles` because they exist after
    # running STONNE.
    if len(outfile_paths) == 0:
        print("ERROR: No outfile paths found. Run STONNE first!")
        exit()
    else:
        return outfile_paths


# Function which stores `output*` files in a uuid-tagged directory
def store_out_files(outfiles: list[path.Path],
                    energy_report: path.Path) -> path.Path:
    outfiles_dir = path.Path("outfiles/") / str(uuid.uuid4())
    root = path.Path(".")

    if not outfiles_dir.exists():
        outfiles_dir.mkdir()

    # Store energy report first
    energy_report.rename(root / outfiles_dir / energy_report.name)

    # Store remaining `output*` files in uuid directory
    for outfile in outfiles:
        outfile.rename(root / outfiles_dir / outfile.name)

    return root / outfiles_dir


# Function which calls `calculate_energy.py` to gen. `energy_report`
def generate_energy_report(outfiles: list[path.Path],
        verbose: bool, mode: str) -> path.Path:
    
    # create list of just `.counter` files.
    # NOTE: Make sure you process only one `.counters` file at a time.
    counter_outfiles = list(
        filter(lambda outfile: ".counters" in outfile.name, outfiles))
    calculate_energy_program = path.Path("energy_tables/calculate_energy.py")
    energy_values_file = path.Path("energy_tables/energy_model.txt")

    # Verbose mode generates an energy report with a detailed energy breakdown
    if verbose:
        for counter_outfile in counter_outfiles:
            process = subprocess.Popen([
                calculate_energy_program, "-v",
                f"-table_file={energy_values_file}",
                f"-counter_file={counter_outfile}",
                f"mode={mode}",
            ],
                                       stdout=subprocess.PIPE)

            print(process.communicate()[0])
    # Generate an energy report without verbose mode
    else:
        for counter_outfile in counter_outfiles:
            process = subprocess.Popen([
                calculate_energy_program, f"-table_file={energy_values_file}",
                f"-counter_file={counter_outfile}",
                f"-mode={mode}",
            ],
                                       stdout=subprocess.PIPE)

            print(process.communicate()[0])

    # Extract the energy report which was just generated inside the root
    # directory.
    energy_report = list(path.Path().glob("*.energy"))

    # We return the energy_report for later parsing in the
    # `parse_energy_report` function. We only support one energy_report at a
    # time.
    return energy_report[0]

# Function which adds the energy values to each of the rectangles on the bar
# charts.
def addlabels(x,y):
    for i in range(len(x)):
        plt.text(i, y[i], y[i], ha = 'center',
                 bbox = dict(facecolor = 'red', alpha =.8))

# Function which parses energy report and displays optional plots
def parse_energy_report(outfiles_dir: path.Path, enable_plots: bool, hint, mode):

    # Get `energy_report` from `outfiles_dir`
    energy_report = list(outfiles_dir.glob("*.energy"))[0]

    # Generate a regex for static energy
    static_energy_regex = re.findall("(.*): STATIC=([0-9]*.[0-9]*)",
                                     energy_report.read_text())

    # Generate a regex for dynamic energy
    dynamic_energy_regex = re.findall(
        "(.*): STATIC=[0-9]*.[0-9]* AREA=[0-9]*.[0-9]* DYNAMIC=([0-9]*.[0-9]*)",
        energy_report.read_text())




    b_cache_path = Path(f"/home/dalton/desktop/cacti/temp/DENSE/best_cache_{hint}.txt")

    b_cache_meta = re.findall("\d*[\.]?\d*[e]?[-]?[0-9]?[0-9]?", b_cache_path.read_text())
    
    b_cache_meta = [value for value in b_cache_meta if value != "" and value != "-" and value !="e"]
    print(b_cache_meta)
    

 # counter_outfiles = list(
        # filter(lambda outfile: ".counters" in outfile.name, outfiles))



    # Convert list of tuples into a list of lists. Easier to use.
    dynamic_energy_regex = [list(x) for x in dynamic_energy_regex]
    static_energy_regex = [list(x) for x in static_energy_regex]

    # Accumlate total static energy
    total_dynamic_energy = Decimal()
    for list_comp in dynamic_energy_regex:
        for item in list_comp:
            if item.isalpha():
                pass
            else:
                total_dynamic_energy += Decimal(item)

    


    # Accumlate total dynamic energy
    total_static_energy = Decimal()
    for list_comp in static_energy_regex:
        for item in list_comp:
            if item.isalpha():
                pass
            else:
                total_static_energy += Decimal(item)

    # Print dynamic energy info
    print("\n\n")
    print("Dynamic Energy Breakdown:")
    print(dynamic_energy_regex, end="\n\n")

    print(f"Total Dynamic Energy: {total_dynamic_energy}μJ")

    # Print static energy info
    print("\n\n")
    print("Static Energy Breakdown:")
    print(static_energy_regex, end="\n\n")
    print(f"Total Static Energy: {total_static_energy}μJ")

    # Extract static energy values and component names which will be used for
    # plotting.
    static_energies = list()
    static_lables = list()
    for list_comp in static_energy_regex:
        for item in list_comp:
            if item.isalpha():
                static_lables.append(item)
            else:
                static_energies.append(Decimal(item))

    # Extract dynamic energy values and component names which will be used for
    # plotting.
    dynamic_energies = list()
    dynamic_lables = list()
    for list_comp in dynamic_energy_regex:
        for item in list_comp:
            if item.isalpha():
                dynamic_lables.append(item)
            else:
                dynamic_energies.append(Decimal(item))
                
    opt_dyn    = dynamic_energy_regex
    opt_static = static_energy_regex
    

    miss_cost = (Decimal(b_cache_meta[4]) * 44000) + (Decimal(b_cache_meta[5]) * 44000)
    cache_cost = (Decimal(b_cache_meta[2]) * Decimal(b_cache_meta[13])) + (Decimal(b_cache_meta[3]) * Decimal(b_cache_meta[12])) 

    opt_dyn[3][1] = str((float(cache_cost) + float(miss_cost)) / 1e6)
    opt_dyn[3][0] = 'GBPlusCache'
    
    print(opt_dyn)
    opt_dyn_total = Decimal()
    for list_comp in opt_dyn:
        for item in list_comp:
            if item.isalpha():
                pass
            else:
                opt_dyn_total += Decimal(item)
    
    opt_static[3][1] = str(float(b_cache_meta[11]))
    opt_static[3][0] = 'GBPlusCache'

    opt_static_total = Decimal()
    for list_comp in opt_static:
        for item in list_comp:
            if item.isalpha():
                pass
            else:
                opt_static_total += Decimal(item)


    # Set plot style. Useful for clean plots.
    sns.set_theme(style="whitegrid")

    # Set dynamic energy values, labels, and plotting config. 
    # plt.subplot(1, 2, 1)
    # plt.bar(dynamic_lables, dynamic_energies, color='navy')
    # plt.xlabel('Components')
    # plt.ylabel('Dynamic Energy (mJ/s)')
    # plt.title("Dynamic Energy Analysis")
    # addlabels(dynamic_lables, dynamic_energies)
    

    dynamic_meta = {
            "Accelerator Dyn. Config.": ["GlobalBuffer", "GlobalBuffer+Cache"], 
            f"Normalized Dyn. Energy": [total_dynamic_energy / total_dynamic_energy, 
               (total_dynamic_energy - (total_dynamic_energy - opt_dyn_total)) / total_dynamic_energy]
            }
    
    dynamic_df = pd.DataFrame(dynamic_meta)
    print(dynamic_df)

    ax1 = sns.barplot(data=dynamic_df,
                     x="Accelerator Dyn. Config.",
                     y="Normalized Dyn. Energy",
                     hue="Accelerator Dyn. Config.",
                     ci=False)
    for container in ax1.containers:
        ax1.bar_label(container)

    # # Set static energy values, labels, and plotting config. 
    # plt.subplot(1, 2, 2)
    # plt.bar(static_lables, static_energies, color='navy')
    # plt.xlabel('Components')
    # plt.ylabel('Static Energy (mJ/s)')
    # plt.title("Static Energy Analysis")
    # addlabels(static_lables, static_energies)

    # Draw plots to the user's screen. 
    if mode == "PDP":
        plt.title(f"Normalized Power Delay Product ({mode}) of Dyn.")
    elif mode == "EDP":
        plt.title(f"Normalized Energy Delay Product ({mode}) of Dyn.")
    plt.legend(loc="upper center")
    plt.show()

    leak_meta = {
            "Accelerator Leak. Config.": ["GlobalBuffer", "GlobalBuffer+Cache"], 
            f"Normalized Leak. Energy": [total_static_energy / total_static_energy, 
               (total_static_energy - (total_static_energy - opt_static_total)) / total_static_energy]
            }
    
    leak_df = pd.DataFrame(leak_meta)
    print(leak_df)
    ax2 = sns.barplot(data=leak_df,
                     x="Accelerator Leak. Config.",
                     y="Normalized Leak. Energy",
                     hue="Accelerator Leak. Config.",
                     ci=False)
    for container in ax2.containers:
        ax2.bar_label(container)
   
    if mode == "PDP":
        plt.title(f"Normalized Power Delay Product ({mode}) of Leakage")
    elif mode == "EDP":
        plt.title(f"Normalized Energy Delay Product ({mode}) of Leakage")
    plt.legend(loc="upper center")
    plt.show()


def main():
    
    # Parser which allows user to enable plots and verbose mode
    parser = argparse.ArgumentParser(
        prog=
        "API which bridges STONNE User Interface and `calculate_energy.py`",
        description="User runs STONNE to gen outfiles then runs this program.",
        epilog="Author: Dalton Hensley")

    parser.add_argument("-v",
                        "--verbose",
                        type=bool,
                        required=False,
                        default=False,
                        help="Enables verbose mode for detailed info.",
                        choices=[True, False])

    parser.add_argument("-p",
                        "--plot",
                        type=bool,
                        required=False,
                        default=False,
                        help="Enables plot mode for detailed info.",
                        choices=[True, False])

    parser.add_argument("-m",
                        "--mode",
                        type=str,
                        required=True,
                        help="PDP or EDP",
                        choices=["PDP", "EDP"])
    
    parser.add_argument("-c",
                        "--hint",
                        type=str,
                        required=True)



 
   # Get the user's commandline arguments.
    args = parser.parse_args()
    
    is_verbose = args.verbose
    plot_enabled = args.plot
    mode = args.mode

    outfiles = get_out_files()
    energy_report = generate_energy_report(outfiles, is_verbose, mode)
    # print(energy_report)

    outfiles_dir = store_out_files(outfiles, energy_report)
    # print(outfiles_dir)

    parse_energy_report(outfiles_dir, plot_enabled, args.hint, mode)


main()
