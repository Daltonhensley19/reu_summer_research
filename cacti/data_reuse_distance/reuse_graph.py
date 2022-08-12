import matplotlib.pyplot as plt
import re
from pathlib import Path
import seaborn as sns
import pandas as pd
import argparse
import matplotlib as mpl

def reuse_dist_wrapper(mode: str):
    rust_reuse_file = Path("rust_reuse.txt")

    addr_regex = re.findall( "Addr: (0x..[0-9a-f\s])", rust_reuse_file.read_text())
    data_regex = re.findall( "Data: (0x...)", rust_reuse_file.read_text())
   

    if mode == "ref":
        # Preprocess addresses
        cleaned_addr_list = list()
        for addr in addr_regex:
            cleaned_addr_list.append(addr.replace('\t', ""))
    else:
        cleaned_data_list = list()
        for data in data_regex:
            cleaned_data_list.append(data.replace('\t', ""))
        
    # Extract reuse distances
    reuse_regex = re.findall(".*Dist: (.*)", rust_reuse_file.read_text())

    # Preprocess reuse distances
    cleaned_reuse_list = list()
    for dist in reuse_regex:
        if dist[0:4] == "Some":
            no_some        = dist.replace("Some", "")
            no_paren_left  = no_some.replace("(", "")
            no_paren_right = no_paren_left.replace(")", "")
            int_dist       = int(no_paren_right)
            cleaned_reuse_list.append(int_dist)
        else:
            cleaned_reuse_list.append(int(-1))

    # print(cleaned_reuse_list)




    cleaned_reuse_df = pd.DataFrame(cleaned_reuse_list, columns=["Reuse Distance"])
    # cleaned_addr_df  = pd.DataFrame(cleaned_addr_list)

    # print(cleaned_reuse_df)
    sns.histplot(cleaned_reuse_df, x="Reuse Distance", stat="percent", cbar=True)
   
    ax = plt.subplot( 111 )
    ax.minorticks_on()
    plt.title("Reuse Distance Analysis")

    plt.savefig('plot.pdf')
    plt.show()



def main():
    # Parser which allows user to enable plots and verbose mode
    parser = argparse.ArgumentParser(
        prog=
        "API which bridges STONNE User Interface and `calculate_energy.py`",
        description="User runs STONNE to gen outfiles then runs this program.",
        epilog="Author: Dalton Hensley")

    parser.add_argument("-m",
                        "--mode",
                        type=str,
                        required=True,
                        default=False,
                        help="Reuse calculator",
                        choices=["data", "ref"])

 
   # Get the user's commandline arguments.
    args = parser.parse_args()
        
    mode = args.mode

    reuse_dist_wrapper(mode)
       
main()
