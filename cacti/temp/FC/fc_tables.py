import pandas as pd 
from tabulate import tabulate


######################################################################################
# indices = ["i4", "i8","i16", "i32", "i64", "i128", "i256", "i512", "i1024"]
# best_cache = ["4-32-2", "4-32-2", "4-32-2", "4-32-2","8-64-1", "8-128-2", "8-128-2", "8-128-2", "8-128-2"]
# ener_delta = ["-3.5199%", "-4.0871%", "-4.3707%", "-4.5125%", "-4.5213%", "-4.5877%", "-4.6210%", "-4.6377%", "-4.6460%"]
# avg_reuse = ["4.266", "6.156", "9.117", "13.193", "20.020", "32.908", "58.239", "108.711", "202.923"]


# leak_pdp = {
        # "Optimal Cache": best_cache,
        # "Energy Delta": ener_delta,
        # "Avg. Reuse Dist.": avg_reuse,

# }

# leak_pdp_df = pd.DataFrame(data=leak_pdp, index=indices)
# leak_pdp_df.index.name = "Input Neuron Count"
# leak_pdp_df.style.set_caption("Leakage PDP of DNN Convolutions")
# # print(tabulate(leak_pdp_df, headers="keys", tablefmt="pipe", stralign="center"))

# print(leak_pdp_df.to_latex(label="Power Delay Product of Leakage Energy"))


######################################################################################
# indices = ["i4", "i8","i16", "i32", "i64", "i128", "i256", "i512", "i1024"]
# best_cache = ["4-32-2", "4-32-2", "4-32-2", "4-32-2","8-64-1", "8-128-2", "8-128-2", "8-128-2", "8-128-2"]
# ener_delta = ["-4.6460%", "-4.6522%", "-4.6538%", "-4.6542%", "-4.6543%", "-4.6543%", "-4.6543%", "-4.6543%", "-4.6543%"]
# avg_reuse = ["4.266", "6.156", "9.117", "13.193", "20.020", "32.908", "58.239", "108.711", "202.923"]


# leak_edp = {
        # "Optimal Cache": best_cache,
        # "Energy Delta": ener_delta,
        # "Avg. Reuse Dist.": avg_reuse,

# }

# leak_edp_df = pd.DataFrame(data=leak_edp, index=indices)
# leak_edp_df.index.name = "Input Neuron Count"
# leak_edp_df.style.set_caption("Leakage EDP of DNN Convolutions")
# # print(tabulate(leak_edp_df, headers="keys", tablefmt="pipe", stralign="center"))

# print(leak_edp_df.to_latex(label="Energy Delay Product of Leakage Energy"))

######################################################################################
# indices = ["i4", "i8","i16", "i32", "i64", "i128", "i256", "i512", "i1024"]
# best_cache = ["4-32-2", "4-32-2", "4-32-2", "4-32-2","8-64-1", "8-128-2", "8-128-2", "8-128-2", "8-128-2"]
# ener_delta = ["-26.0943%", "-26.3515%", "-26.4801%", "-26.5444%", "-26.5766%", "-26.5927%", "-26.5927%", "-26.5947%", "-26.5937%"]

# avg_reuse = ["4.266", "6.156", "9.117", "13.193", "20.020", "32.908", "58.239", "108.711", "202.923"]
# dyn_pdp = {
        # "Optimal Cache": best_cache,
        # "Energy Delta": ener_delta,
        # "Avg. Reuse Dist.": avg_reuse,

# }

# dyn_pdp_df = pd.DataFrame(data=dyn_pdp, index=indices)
# dyn_pdp_df.index.name = "Input Neuron Count"
# dyn_pdp_df.style.set_caption("Dynamic PDP of DNN Convolutions")
# # print(tabulate(dyn_pdp_df, headers="keys", tablefmt="pipe", stralign="center"))

# print(dyn_pdp_df.to_latex(label="Power Delay Product of Dynamic Energy"))


######################################################################################
indices = ["i4", "i8","i16", "i32", "i64", "i128", "i256", "i512", "i1024"]
best_cache = ["4-32-2", "4-32-2", "4-32-2", "4-32-2","8-64-1", "8-128-2", "8-128-2", "8-128-2", "8-128-2"]
ener_delta = ["-27.1073%", "-27.1155%", "-27.1179%", "-27.1187%", "-27.1190%", "-27.1192%", "-27.1190%", "-27.1190%", "-27.1193%"]

avg_reuse = ["4.266", "6.156", "9.117", "13.193", "20.020", "32.908", "58.239", "108.711", "202.923"]
dyn_edp = {
        "Optimal Cache": best_cache,
        "Energy Delta": ener_delta,
        "Avg. Reuse Dist.": avg_reuse,

}

dyn_edp_df = pd.DataFrame(data=dyn_edp, index=indices)
dyn_edp_df.index.name = "Input Neuron Count"
dyn_edp_df.style.set_caption("Dynamic EDP of DNN Convolutions")
# print(tabulate(dyn_edp_df, headers="keys", tablefmt="pipe", stralign="center"))


print(dyn_edp_df.to_latex(label="Energy Delay Product of Dynamic Energy"))
