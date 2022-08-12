import re
from pathlib import Path
import argparse
import fileinput
import subprocess
from time import sleep
from dataclasses import dataclass
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from tabulate import tabulate



@dataclass
class BaseStats:
    cache_size: int
    block_size: int
    assoc: int
    node_size: str


# In Bytes
CACHE_SIZES = [8 * 1024, 16 * 1024, 32 * 1024, 64 * 1024]
BLOCK_SIZES = [4, 8, 16, 32, 64, 128]

# N-Ways
ASSOCIATIVITY = [2, 4, 8, 16]

# Node Tech (lithography process)
NODE_PROCESS = ["0.090", "0.040", "0.032", "0.022"]


def set_base_config(base_config: BaseStats, config_file: Path):

    with fileinput.FileInput(config_file, inplace=True) as f:
        for line in f:
            if ("-size" in line):
                print(line.replace(line,
                                   f"-size (bytes) {base_config.cache_size}"),
                      end='\n')
            else:
                print(line, end='')

    with fileinput.FileInput(config_file, inplace=True) as f:
        for line in f:
            if ("-block" in line):
                print(line.replace(
                    line, f"-block size (bytes) {base_config.block_size}"),
                      end='\n')
            else:
                print(line, end='')

    with fileinput.FileInput(config_file, inplace=True) as f:
        for line in f:
            if ("-associativity" in line):
                print(line.replace(line,
                                   f"-associativity {base_config.assoc}"),
                      end='\n')
            else:
                print(line, end='')
    
    with fileinput.FileInput(config_file, inplace=True) as f:
        for line in f:
            if ("-technology" in line):
                print(line.replace(line,
                                   f"-technology (u) {base_config.node_size}"),
                      end='\n')
            else:
                print(line, end='')

def secondary_mutation(metadata, line, svar):
    
    general_choices = ["cache_s", "block_s", "assoc", "process"]
    
    if metadata == general_choices[3]:
        if ("-technology" in line):
            print(line.replace(line,
            f"-technology (u) {svar}"),
            end='\n')
        else:
            print(line, end='')
    elif metadata == general_choices[2]:
        if ("-associativity" in line):
            print(line.replace(line,
            f"-associativity {svar}"),
            end='\n')
        else:
            print(line, end='')
    elif metadata == general_choices[1]:
        if ("-block" in line):
            print(line.replace(line,
            f"-block size (bytes) {svar}"),
            end='\n')
        else:
            print(line, end='')
    elif metadata == general_choices[0]:
        if ("-size" in line):
            print(line.replace(line,
            f"-size (bytes) {svar}"),
            end='\n')
        else:
            print(line, end='')





def iter_cache_size(base_config: BaseStats, sizes: [int],
        config_file: Path, metadata: str):

    set_base_config(base_config, config_file)
    
    general_choices = ["cache_s", "block_s", "assoc", "process"]
    mutations = [CACHE_SIZES, BLOCK_SIZES, ASSOCIATIVITY, NODE_PROCESS]

    secondary_vars = list()
    for (idx, choice) in enumerate(general_choices):
        if metadata == choice:
            secondary_vars = mutations[idx]

    for svar in secondary_vars:
        with fileinput.FileInput(config_file, inplace=True) as f:
            for line in f:
                secondary_mutation(metadata, line, svar)
        for cache_size in sizes:
            print(f"Cache Size: {cache_size}\t\t{metadata}: {svar}")
            with fileinput.FileInput(config_file, inplace=True) as f:
                for line in f:
                    if ("-size" in line):
                        print(line.replace(line,
                                           f"-size (bytes) {cache_size}"),
                              end='\n')
                    else:
                        print(line, end='')

            with open(
                    f"experiments/cache_size/config_{cache_size}_{svar}",
                    "w") as out:
                _ = subprocess.call(["./cacti", "-infile", config_file],
                                    stdout=out)


def iter_block_size(base_config: BaseStats, sizes: [int],
        config_file: Path, metadata: str):

    set_base_config(base_config, config_file)
 
    general_choices = ["cache_s", "block_s", "assoc", "process"]
    mutations = [CACHE_SIZES, BLOCK_SIZES, ASSOCIATIVITY, NODE_PROCESS]

    secondary_vars = list()
    for (idx, choice) in enumerate(general_choices):
        if metadata == choice:
            secondary_vars = mutations[idx]

    for svar in secondary_vars:
        with fileinput.FileInput(config_file, inplace=True) as f:
            for line in f:
                secondary_mutation(metadata, line, svar)
        for block_size in sizes:
            print(f"Block Size: {block_size}\t\t{metadata}: {svar}")
            with fileinput.FileInput(config_file, inplace=True) as f:
                for line in f:
                    if ("-block" in line):
                        print(line.replace(
                            line, f"-block size (bytes) {block_size}"),
                              end='\n')
                    else:
                        print(line, end='')

            with open(
                    f"experiments/block_size/config_{block_size}_{svar}",
                    "w") as out:
                _ = subprocess.call(["./cacti", "-infile", config_file],
                                    stdout=out)


def iter_assoc(base_config: BaseStats, assoc_kinds: [int],
        config_file: Path, metadata: str):

    set_base_config(base_config, config_file)
    
    general_choices = ["cache_s", "block_s", "assoc", "process"]
    mutations = [CACHE_SIZES, BLOCK_SIZES, ASSOCIATIVITY, NODE_PROCESS]

    secondary_vars = list()
    for (idx, choice) in enumerate(general_choices):
        if metadata == choice:
            secondary_vars = mutations[idx]

    for svar in secondary_vars:
        with fileinput.FileInput(config_file, inplace=True) as f:
            for line in f:
                secondary_mutation(metadata, line, svar)
        for assoc_kind in assoc_kinds:
            print(f"Associativity: {assoc_kind}\t\t{metadata}: {svar}")
            with fileinput.FileInput(config_file, inplace=True) as f:
                for line in f:
                    if ("-associativity" in line):
                        print(line.replace(line,
                                           f"-associativity {assoc_kind}"),
                              end='\n')
                    else:
                        print(line, end='')

            with open(f"experiments/associ/config_{assoc_kind}_{svar}",
                      "w") as out:
                _ = subprocess.call(["./cacti", "-infile", config_file],
                                    stdout=out)


def get_cache_corpus() -> [Path]:
    cache_corpus_path = Path("experiments/cache_size/").glob("*")

    return cache_corpus_path


def get_block_corpus() -> [Path]:
    block_corpus_path = Path("experiments/block_size/").glob("*")

    return block_corpus_path


def get_assoc_corpus() -> [Path]:
    assoc_corpus_path = Path("experiments/associ/").glob("*")

    return assoc_corpus_path


def append_label(label_list, tup, metadata_re):
    matcher = re.findall(metadata_re, tup[0])

    label_list.append(matcher[0])

def fix_label_order(label_list, process_list):
    label_list, process_list = zip(
        *sorted(zip(label_list, process_list), key=lambda x: x[0]))
    label_list = list(label_list)
    process_list = list(process_list)

    return label_list, process_list


def generate_df(energy_list, metadata, ylabel, secondary_var):
    
    
    prim_re = r"config_(\d*)_.*"

    general_choices = ["cache_s", "block_s", "assoc"]
    process_choice = ["process"]

    if secondary_var in general_choices:
        meta_re = r"config_\d*_(\d*)"
    elif secondary_var in process_choice:
        meta_re = r"config_\d*_(0.\d*)"

    keys = list()
    for (token, power) in energy_list:
        result = re.findall(meta_re, token)[0]
        keys.append(result)

    keys = list(set(keys))
    
    ener_list = list()
    secondary_list = list()
    primary_list = list()
    for (process, power) in energy_list:
            print(process)
            for key in keys:
                if key in process:
                    ener_list.append(float(power))
                    secondary_list.append(key)
                    append_label(primary_list, (process, power), prim_re)

    data = {
        f'{ylabel}':
        ener_list,
        f'{metadata}':
        primary_list,
        f'{secondary_var}':
        secondary_list,
    }

    df = pd.DataFrame(data)
    df = df.sort_values(by=[f"{ylabel}"])

    return df

def parse_perf(corpus: [Path], metadata: str, secondary_var: str, plotstyle: str):
    access_time_regex = r"Access time \(ns\): (\d*.\d*)"


    access_time_list = list(tuple())

    try: 
        for file in corpus:
            access_time_list.append(
                (file.name, re.findall(access_time_regex, file.read_text())[0]))
    except:
        print("FATAL ERROR: RANGE OF MUTATIONS ARE NOT INVALID.")
        
    access_data = generate_df(access_time_list, metadata, "Access Time (ns)", secondary_var)
    print("Access Time Cache Analysis\n")
    print(
        tabulate(access_data, headers="keys", tablefmt="pipe",
                 stralign="center"))
    
    access_data = access_data.astype({f"{metadata}":"int32"})
    sns.set_theme(style="whitegrid")
    
    if plotstyle == "line":
        sns.lineplot(data=access_data,
                     x=f"{metadata}",
                     y="Access Time (ns)",
                     hue=f"{secondary_var}",
                     style=f"{secondary_var}",
                     markers=True,
                     dashes=False, 
                     ci=False)
    elif plotstyle == "bar":
        sns.barplot(data=access_data,
                     x=f"{metadata}",
                     y="Access Time (ns)",
                     hue=f"{secondary_var}",
                     ci=False)

    plt.title("Access Time Cache Analysis")
    plt.show()

def parse_energy(corpus: [Path], metadata: str, secondary_var: str, plotstyle: str):
    dynamic_read_regex = r"Total dynamic read energy per access \(nJ\): (\d.\d*)"
    dynamic_write_regex = r"Total dynamic write energy per access \(nJ\): (\d.\d*)"
    leakage_regex = r"Total leakage power of a bank \(mW\): (\d*.\d*)"

    dynamic_read_list = list(tuple())
    dynamic_write_list = list(tuple())
    leakage_list = list(tuple())
    for file in corpus:
        leakage_list.append(
            (file.name, re.findall(leakage_regex, file.read_text())[0]))
        dynamic_read_list.append(
            (file.name, re.findall(dynamic_read_regex,
                                      file.read_text())[0]))
        dynamic_write_list.append(
            (file.name, re.findall(dynamic_write_regex,
                                      file.read_text())[0]))

    # print(leakage_list)

    leak_data = generate_df(leakage_list, metadata, "Power (mW)", secondary_var)
    print("Leakage Cache Analysis\n")
    print(
        tabulate(leak_data, headers="keys", tablefmt="pipe",
                 stralign="center"))

    leak_data = leak_data.astype({f"{metadata}":"int32"})
    sns.set_theme(style="whitegrid")
       
    if plotstyle == "line":
        sns.lineplot(data=leak_data,
                     x=f"{metadata}",
                     y="Power (mW)",
                     hue=f"{secondary_var}",
                     style=f"{secondary_var}",
                     markers=True,
                     dashes=False, 
                     ci=False)
    elif plotstyle == "bar":
        sns.barplot(data=leak_data,
                     x=f"{metadata}",
                     y="Power (mW)",
                     hue=f"{secondary_var}",
                     ci=False)

    plt.title("Leakage Cache Analysis")
    plt.show()

    read_data = generate_df(dynamic_read_list, metadata, "Energy (nJ)", secondary_var)
    print("Dynamic Read Cache Analysis\n")
    print(
        tabulate(read_data, headers="keys", tablefmt="pipe",
                 stralign="center"))

    read_data = read_data.astype({f"{metadata}":"int32"})
    sns.set_theme(style="whitegrid")
       
    if plotstyle == "line":
        sns.lineplot(data=read_data,
                     x=f"{metadata}",
                     y="Energy (nJ)",
                     hue=f"{secondary_var}",
                     style=f"{secondary_var}",
                     markers=True,
                     dashes=False, 
                     ci=False)
    elif plotstyle == "bar":
        sns.barplot(data=read_data,
                     x=f"{metadata}",
                     y="Energy (nJ)",
                     hue=f"{secondary_var}",
                     ci=False)


    plt.title("Dynamic Read Cache Analysis")
    plt.show()

    write_data = generate_df(dynamic_write_list, metadata, "Energy (nJ)", secondary_var)
    print("Dynamic Write Cache Analysis\n")
    print(
        tabulate(write_data,
                 headers="keys",
                 tablefmt="pipe",
                 stralign="center"))

    write_data = write_data.astype({f"{metadata}":"int32"})
    sns.set_theme(style="whitegrid")
   
    if plotstyle == "line":
        sns.lineplot(data=write_data,
                     x=f"{metadata}",
                     y="Energy (nJ)",
                     hue=f"{secondary_var}",
                     style=f"{secondary_var}",
                     markers=True,
                     dashes=False, 
                     ci=False)
    elif plotstyle == "bar":
        sns.barplot(data=write_data,
                     x=f"{metadata}",
                     y="Energy (nJ)",
                     hue=f"{secondary_var}",
                     ci=False)


    plt.title("Dynamic Write Cache Analysis")
    plt.show()

def clean():
    subprocess.call(["./clean2.sh"], shell=True)

def main():
    parser = argparse.ArgumentParser(
        prog=
        "API which runs experiments through Cacti.",
        description="Cacti experiment generator.",
        epilog="Author: Dalton Hensley")

    parser.add_argument("-m",
                        "--mode",
                        type=str,
                        required=True,
                        help="Choose which parameter to measure.",
                        choices=["cache_s", "block_s", "assoc"])

    parser.add_argument("-d",
                        "--depvar",
                        type=str,
                        required=True,
                        help="Choose which dependent var. to measure.",
                        choices=["perf", "energy"])
    
    parser.add_argument("-s",
                        "--secondary",
                        type=str,
                        required=True,
                        help="Choose which secondary var. to measure.",
                        choices=["cache_s", "block_s", "assoc", "process"])  

    parser.add_argument("-p",
                        "--plotstyle",
                        type=str,
                        required=True,
                        help="Choose which type of graph to make.",
                        choices=["bar", "line"])





    args = parser.parse_args()

    # Extract config file from Cacti
    cacti_config_path = Path("mock_cache.cfg")

    # Set base config
    base_config = BaseStats(cache_size=64 * 1024, block_size=4, assoc=2, node_size="0.022")

    mode   = args.mode 
    depvar = args.depvar 
    secvar = args.secondary
    plotstyle = args.plotstyle

    assert mode != secvar

    label_choices = ["Cache_size (bytes)", "Block_size (bytes)", "Associativity"] 
    if mode == "cache_s":
        iter_cache_size(base_config, CACHE_SIZES, cacti_config_path, secvar)
        cache_corpus = get_cache_corpus()
        if depvar == "energy":
            parse_energy(cache_corpus, label_choices[0], secvar, plotstyle)
        elif depvar == "perf":
            parse_perf(cache_corpus, label_choices[0], secvar, plotstyle)
    elif mode == "block_s":
        iter_block_size(base_config, BLOCK_SIZES, cacti_config_path, secvar)
        block_corpus = get_block_corpus()
        if depvar == "energy":
            parse_energy(block_corpus, label_choices[1], secvar, plotstyle)
        elif depvar == "perf":
            parse_perf(block_corpus, label_choices[1], secvar, plotstyle)
    elif mode == "assoc":
        iter_assoc(base_config, ASSOCIATIVITY, cacti_config_path, secvar)
        assoc_corpus = get_assoc_corpus()
        if depvar == "energy":
            parse_energy(assoc_corpus, label_choices[2], secvar, plotstyle)
        elif depvar == "perf":
            parse_perf(assoc_corpus, label_choices[2], secvar, plotstyle)

    
    clean()

main()
