import argparse
import os
import subprocess

# Function which loads config for stonne sim. and energy api and runs the
# experiments using the configs.
def run_experiment(stonne_config: [str], api_config: [str]):
    sim_process = subprocess.Popen(stonne_config, stdout=subprocess.PIPE)
    print(sim_process.communicate()[0].decode("utf-8"), end="\n\n\n")

    api_process = subprocess.Popen(api_config, stdout=subprocess.PIPE)
    print(api_process.communicate()[0].decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(
        prog="Program to run STONNE experiment templates.",
        description=
        "User may choose a given experiment based on shape and sparsity levels",
        epilog="Author: Dalton Hensley")

    parser.add_argument("-i",
                        "--shape_type",
                        type=str,
                        required=True,
                        help="Choose an experiment.",
                        choices=["regular", "irregular"])

    parser.add_argument("-s",
                        "--sparse_type",
                        type=str,
                        required=True,
                        help="Choose an experiment.",
                        choices=["sparse", "dense"])

    args = parser.parse_args()

    shape_choice = args.shape_type
    sparse_choice = args.sparse_type

    irr_and_sparse_config = [
        "./stonne", "-SparseGEMM", "-M=64", "-N=1", "-K=128", "-num_ms=64",
        "-dn_bw=64", "-rn_bw=32", "-MK_sparsity=80", "-KN_sparsity=90",
        "-dataflow=MK_STA_KN_STR", "-print_stats=1", "-optimize=0"
    ]

    irr_and_dense_config = [
        "./stonne", "-SparseGEMM", "-M=64", "-N=1", "-K=128", "-num_ms=64",
        "-dn_bw=64", "-rn_bw=32", "-MK_sparsity=0", "-KN_sparsity=0",
        "-dataflow=MK_STA_KN_STR", "-print_stats=1", "-optimize=0"
    ]

    reg_and_dense_config = [
        "./stonne", "-SparseGEMM", "-M=32", "-N=32", "-K=128", "-num_ms=64",
        "-dn_bw=64", "-rn_bw=32", "-MK_sparsity=0", "-KN_sparsity=0",
        "-dataflow=MK_STA_KN_STR", "-print_stats=1", "-optimize=0"
    ]

    reg_and_sparse_config = [
        "./stonne", "-SparseGEMM", "-M=32", "-N=32", "-K=128", "-num_ms=64",
        "-dn_bw=64", "-rn_bw=32", "-MK_sparsity=80", "-KN_sparsity=90",
        "-dataflow=MK_STA_KN_STR", "-print_stats=1", "-optimize=0"
    ]

    stonne_energy_api_config = ["python3", "stonne_to_energy.py", "-p", "True"]

    if shape_choice == "regular" and sparse_choice == "dense":
        run_experiment(reg_and_dense_config, stonne_energy_api_config)
    elif shape_choice == "irregular" and sparse_choice == "dense":
        run_experiment(irr_and_dense_config, stonne_energy_api_config)
    elif shape_choice == "irregular" and sparse_choice == "sparse":
        run_experiment(irr_and_sparse_config, stonne_energy_api_config)
    elif shape_choice == "regular" and sparse_choice == "sparse":
        run_experiment(reg_and_sparse_config, stonne_energy_api_config)
    else:
        print("ERROR: Invaild config.")


main()
