import pandas as pd
import subprocess
import re
from pathlib import Path
import os
import fileinput

CAPACITY = [4, 8, 16, 32, 64]
BSIZE = [4, 8, 16, 32, 64, 128, 256, 512]
ASSOC = [1, 2, 4, 8, 16]


def run_exper(workload_file: Path):
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
                        f"experiments/config_{cap}_{bs}_{assoc}",
                        "w") as ofile:
                    data = ifile.read()
                    ofile.write(data)

                _ = subprocess.run(["./clean.sh"], shell=True)


def prune_corpus(config_corpus: [Path]):
    for file in config_corpus:
        with open(file, "r") as ifile:
            data = ifile.read()
            if len(data) > 0:
                print(f"file: {file.name}\t length: {len(data)} [OK]\n")
            else:
                print(
                    f"file: {file.name}\t length: {len(data)} [PRUNING FILE]\n"
                )
                os.remove(file)


def generate_df(config_corpus: [Path]):
    regex_array = [
        r"Total Cache Accesses = (\d*)", r"Cache Reads: (\d*)",
        r"Cache Writes: (\d*)", r"Misses: Total (\d*)", r"DataReads (\d*)",
        r"DataWrites (\d*)", r"Totalrio (0.\d*)", r"Readrio (0.\d*)",
        r"Writerio (0.\d*)", r"the Cache: (\d*)"
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
        "Lines_evicted": list()
    }

    data_keys = data.keys()
    data_keys = list(data_keys)
    indices = list()
    for file in config_corpus:
        indices.append(file.name)
        for (idx, regex) in enumerate(regex_array):
            data[data_keys[idx]].extend(re.findall(regex, file.read_text()))

    df = pd.DataFrame(data, index=indices)

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

    return df


def run_cacti(cacti_path: str, config_file: str, clean_corpus: [Path]):

    config_regex = r"config_(\d*)_(\d*)_(\d*)"

    settings = list()
    for file in clean_corpus:
        print(file.name)
        settings.append(re.findall(config_regex, str(file.name))[0])
    
    print(settings)


    for (cap, bs, assoc) in settings:

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
            with open(f"experiments/cacti_{cap}_{bs}_{assoc}", "w") as ofile:
                _ = subprocess.call([cacti_path, "-infile", config_file], stdout=ofile)
        except Exception as e:
            print(e.with_traceback())
            print(f"Invalid configuration: {cap}\t {bs}\t{assoc}")

           
def main():

    workload_file = Path("cache.trace")
    print(workload_file)

    run_exper(workload_file)

    config_corpus = Path("").glob("config_*")

    prune_corpus(config_corpus)

    clean_corpus = Path("experiments/").glob("config_*")
    data = generate_df(clean_corpus)

    data = data.sort_values(by=["Read_miss_rate", "Write_miss_rate"])
    print(data)
    
    clean_corpus = Path("experiments/").glob("config_*")
    config_path = Path("mock_cache.cfg")
    run_cacti("~/desktop/cacti/./cacti", "~/desktop/cacti/mock_cache.cfg", clean_corpus)

main()
