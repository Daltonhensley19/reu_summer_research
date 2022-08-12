import pandas as pd
import subprocess
import re
from pathlib import Path
import os
import fileinput
import shutil
import tqdm
from tqdm import tqdm
from tabulate import tabulate
from time import sleep
import glob
import logging as log
import argparse
import shortuuid

CAPACITY = [4, 8, 16, 32, 64]
BSIZE = [4, 8, 16, 32, 64, 128, 256, 512]
ASSOC = [1, 2, 4, 8, 16]


def run_exper(workload_file: Path):
    print("RUNNING EXPERIMENTS IN N-WAY-SET-ASSOCIATIVE-L1-CACHE")
    sleep(3)
    for cap in CAPACITY:
        for bs in BSIZE:
            for assoc in ASSOC:
                print(f"{cap}\t{bs}\t{assoc}")
                if cap == 4 and bs == 512 and assoc == 17:
                    continue
                os.system(
                    f"./Cache -c{cap} -b{bs} -a{assoc} < {workload_file} > output.txt"
                )

                with open("output.txt", "r") as ifile, open(
                        f"N-Way-Set-Associative-L1-Cache/experiments/config_{cap}_{bs}_{assoc}",
                        "w") as ofile:
                    data = ifile.read()
                    ofile.write(data)

                _ = subprocess.run(["./clean.sh"], shell=True)


def prune_corpus(config_corpus):

    with tqdm(total=len(config_corpus), desc="Pruning config_corpus") as pro_bar:
        for file in config_corpus:
            sleep(0.01)
            with open(file, "r") as ifile:
                data = ifile.read()
                if len(data) > 0:
                    # print(f"file: {file.name}\t length: {len(data)} [OK]\n")
                    pass
                else:
                    # print(
                        # f"file: {file.name}\t length: {len(data)} [PRUNING FILE]\n"
                    # )
                    os.remove(file)
            pro_bar.update(1)


def run_cacti(cacti_path: str, config_file: str, clean_corpus: [Path]):

    config_regex = r"config_(\d*)_(\d*)_(\d*)"

    settings = list()
    for file in clean_corpus:
        print(file.name)
        settings.append(re.findall(config_regex, str(file.name))[0])
    
    # print(settings)


    for (cap, bs, assoc) in tqdm(settings, desc="Running Cacti"):

        try:
            with fileinput.FileInput(config_file, inplace=True) as f:
                for line in f:
                    if ("-size" in line):
                        print(line.replace(line,
                                           f"-size (bytes) {int(cap) * 1024}"),
                              end='\n')
                    else:
                        print(line, end='')

            with fileinput.FileInput(config_file, inplace=True) as f:
                for line in f:
                    if ("-block" in line):
                        print(line.replace(
                            line, f"-block size (bytes) {bs}"),
                              end='\n')
                    else:
                        print(line, end='')

            with fileinput.FileInput(config_file, inplace=True) as f:
                for line in f:
                    if ("-associativity" in line):
                        print(line.replace(line,
                                           f"-associativity {assoc}"),
                              end='\n')
                    else:
                        print(line, end='') 
            with open(f"N-Way-Set-Associative-L1-Cache/experiments/cacti_{cap}_{bs}_{assoc}", "w") as ofile:
                _ = subprocess.call([cacti_path, "-infile", config_file], stdout=ofile)
        except Exception as e:
            print(e.with_traceback())
            print(f"Invalid configuration: {cap}\t {bs}\t{assoc}")

def prune_cacti(cacti_corpus: [Path]):
    dynamic_read_regex = r"Total dynamic read energy per access \(nJ\): (\d.\d*)"
    dynamic_write_regex = r"Total dynamic write energy per access \(nJ\): (\d.\d*)"
    leakage_regex = r"Total leakage power of a bank \(mW\): (\d*.\d*)"
    cacti_regex = r"cacti_(\d*)_(\d*)_(\d*)"

    for file in cacti_corpus:
        (cap, bs, assoc) = re.match(cacti_regex, file.name).groups()

        if re.findall(dynamic_read_regex, file.read_text()) == []:
            print("Pruning: ", (cap, bs, assoc))
            os.remove(file)
            os.remove(f"N-Way-Set-Associative-L1-Cache/experiments/config_{cap}_{bs}_{assoc}")


def generate_df(total_corpus: [Path]):
    regex_array = [
        r"Total Cache Accesses = (\d*)", 
        r"Cache Reads: (\d*)",
        r"Cache Writes: (\d*)", 
        r"Misses: Total (\d*)", 
        r"DataReads (\d*)",
        r"DataWrites (\d*)", 
        r"Totalrio (0.\d*)", 
        r"Readrio (0.\d*)",
        r"Writerio (0.\d*)", 
        r"the Cache: (\d*)",
        r"Total leakage power of a bank \(mW\): (\d*.\d*)",
        r"Total dynamic write energy per access \(nJ\): (\d*.\d*)",
        r"Total dynamic read energy per access \(nJ\): (\d*.\d*)",
        r"Cache_size: (\d*)",
        r"Block_size: (\d*)",
        r"Assoc: (\d*)",
        r"Cycle time \(ns\):  (\d*.\d*)"
        ]

    data = {
        "Total_cache_access": list(),
        "Cache_reads": list(),
        "Cache_writes": list(),
        "Total_cache_miss": list(),
        "Read_misses": list(),
        "Write_misses": list(),
        "Total_miss_rate": list(),
        "Read_miss_rate": list(),
        "Write_miss_rate": list(),
        "Lines_evicted": list(),
        "Leakage_cost (mW)": list(),
        "Write_cost (nJ)": list(),
        "Read_cost (nJ)": list(),
        "Cache_size (Kib)": list(),
        "Block_size (bytes)": list(),
        "Assoc": list(),
        "Cycle_time (ns)": list(),
    }


    data2 = {
        "Total_cache_miss": list(),
        "Cache_size (Kib)": list(),
        "Block_size (bytes)": list(),
        "Assoc": list(),
    }


    data_keys = data.keys()
    data_keys = list(data_keys)
    for file in total_corpus:
           for (idx, regex) in enumerate(regex_array):
                z2 = re.search(regex, file.read_text())
                if z2 != None:
                    data[data_keys[idx]].extend(list(z2.groups()))

    # for key, value in data.items():
        # print(f"key: {key}\t length: {len(value)}")./stonne -FC -K=64 -N=4 -T_K=1 -T_N=1 -num_ms=64 -dn_bw=8
    
    df = pd.DataFrame(data)

    df['Total_cache_access'] = df['Total_cache_access'].astype('int32')
    df['Cache_reads'] = df['Cache_reads'].astype('int32')
    df['Cache_writes'] = df['Cache_writes'].astype('int32')
    df['Total_cache_miss'] = df['Total_cache_miss'].astype('int32')
    df['Read_misses'] = df['Read_misses'].astype('int32')
    df['Write_misses'] = df['Write_misses'].astype('int32')
    df['Total_miss_rate'] = df['Total_miss_rate'].astype('float32')
    df['Read_miss_rate'] = df['Read_miss_rate'].astype('float32')
    df['Write_miss_rate'] = df['Write_miss_rate'].astype('float32')
    df['Lines_evicted'] = df['Lines_evicted'].astype('int32')
    df['Leakage_cost (mW)'] = df['Leakage_cost (mW)'].astype('float32')
    df['Write_cost (nJ)'] = df['Write_cost (nJ)'].astype('float32')
    df['Read_cost (nJ)'] = df['Read_cost (nJ)'].astype('float32')
    df['Cycle_time (ns)'] = df['Cycle_time (ns)'].astype('float32')

    return df
def merge_files():
    clean_cacti_corpus = Path("N-Way-Set-Associative-L1-Cache/experiments/").glob("cacti_*")
    clean_config_corpus = Path("N-Way-Set-Associative-L1-Cache/experiments/").glob("config_*")
    
    zipped_list = list()
    for files in zip(sorted(clean_cacti_corpus), sorted(clean_config_corpus)):
        zipped_list.append(files)

    for idx, fpair in enumerate(zipped_list):
        with open(f'N-Way-Set-Associative-L1-Cache/experiments/{idx}', 'w') as outfile:
            for fname in fpair:
                with open(fname) as infile:
                    outfile.write(infile.read())

    _ = os.system("rm N-Way-Set-Associative-L1-Cache/experiments/c*")
        
def main():
    parser = argparse.ArgumentParser(
        prog=
        "API which runs experiments through Cacti and N-Way.",
        description="Experiment generator.",
        epilog="Author: Dalton Hensley")

    parser.add_argument("-w",
                        "--workload",
                        type=str,
                        required=True,
                        help="Choose which workload to analyze.",
                        choices=["CONV", "FC", "DENSE", "SPARSE"])

    parser.add_argument("-a",
                        "--annotation",
                        type=str,
                        required=True,
                        help="Provide a helpful annotation of the workload.")

    args = parser.parse_args()
    
    os.rename("cache.trace", f"{args.workload}.trace")
    workload_file = Path(f"{args.workload}.trace")
    print(workload_file)

    run_exper(workload_file)

    config_corpus = glob.glob("N-Way-Set-Associative-L1-Cache/experiments/config_*")

    prune_corpus(config_corpus)
    
    clean_config_corpus = Path("N-Way-Set-Associative-L1-Cache/experiments/").glob("config_*")
    config_path = Path("mock_cache.cfg")
    run_cacti("./cacti", "mock_cache.cfg", clean_config_corpus)

    clean_cacti_corpus = Path("N-Way-Set-Associative-L1-Cache/experiments/").glob("cacti_*")
    prune_cacti(clean_cacti_corpus)
    
    merge_files()

    total_corpus = Path("N-Way-Set-Associative-L1-Cache/experiments/").glob("*")
    data = generate_df(total_corpus)
    
    data = data.sort_values(by=["Total_cache_miss", 
                                "Leakage_cost (mW)"])
    

    with open(f"temp/{args.workload}/data_table_{args.annotation}_{shortuuid.random(length=3)}.txt", "w") as ofile:
        ofile.write(tabulate(data, headers="keys", tablefmt="pipe", stralign="center"))
    
    print("DATA TABLE HAS BEEN SAVED TO DISK!")
    os.remove(f"{args.workload}.trace")

main()
