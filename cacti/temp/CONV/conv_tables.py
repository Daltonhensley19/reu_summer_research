import pandas as pd 
from tabulate import tabulate
import matplotlib.pyplot as plt
from math import log
import seaborn as sns
sns.set_theme(style="whitegrid")

######################################################################################
# indices = ["4_4", "8_8","16_16", "32_32", "64_64"]
# best_cache = ["8-128-2", "8-128-2", "8-128-2", "8-128-2", "32-128-1"]
# ener_delta = ["-4.4014%", "-4.6134%", "-4.6464%", "-4.6526%", "-4.6528%"]
# avg_reuse_dist = ["87.924", "172.281", "547.066", "1885.156", "6384.796"]

# leak_pdp = {
        # "Optimal Cache": best_cache,
        # "Energy Delta": ener_delta,
        # "Avg. Reuse Dist.": avg_reuse_dist,

# }

# leak_pdp_df = pd.DataFrame(data=leak_pdp, index=indices)
# leak_pdp_df.index.name = "Filter Size"
# leak_pdp_df.style.set_caption("Leakage PDP of DNN Convolutions")
# # print(tabulate(leak_pdp_df, headers="keys", tablefmt="pipe", stralign="center"))

# print(leak_pdp_df.to_latex(label="Power Delay Product of Leakage Energy"))


######################################################################################
# indices = ["4_4", "8_8","16_16", "32_32", "64_64"]
# best_cache = ["8-128-2", "8-128-2", "8-128-2", "8-128-2", "32-128-1"]
# ener_delta = ["-4.6541%", "-4.6543%", "-4.6543%", "-4.6543%", "-4.6543%"]
# avg_reuse_dist = ["87.924", "172.281", "547.066", "1885.156", "6384.796"]

# leak_edp = {
        # "Optimal Cache": best_cache,
        # "Energy Delta": ener_delta,
        # "Avg. Reuse Dist.": avg_reuse_dist,

# }

# leak_edp_df = pd.DataFrame(data=leak_edp, index=indices)
# leak_edp_df.index.name = "Filter Size"
# leak_edp_df.style.set_caption("Leakage EDP of DNN Convolutions")
# # print(tabulate(leak_edp_df, headers="keys", tablefmt="pipe", stralign="center"))

# print(leak_edp_df.to_latex(label="Energy Delay Product of Leakage Energy"))

######################################################################################
# indices = ["4_4", "8_8","16_16", "32_32", "64_64"]
# best_cache = ["8-128-2", "8-128-2", "8-128-2", "8-128-2", "32-128-1"]
# ener_delta = ["-17.6718%", "-14.3325%", "-13.3943%", "-13.0423%", "-12.8894%"]
# avg_reuse_dist = ["87.924", "172.281", "547.066", "1885.156", "6384.796"]

# dyn_pdp = {
        # "Optimal Cache": best_cache,
        # "Energy Delta": ener_delta,
        # "Avg. Reuse Dist.": avg_reuse_dist,

# }

# dyn_pdp_df = pd.DataFrame(data=dyn_pdp, index=indices)
# dyn_pdp_df.index.name = "Filter Size"
# dyn_pdp_df.style.set_caption("Dynamic PDP of DNN Convolutions")
# # print(tabulate(dyn_pdp_df, headers="keys", tablefmt="pipe", stralign="center"))

# print(dyn_pdp_df.to_latex(label="Power Delay Product of Dynamic Energy"))


######################################################################################
indices = ["4_4", "8_8","16_16", "32_32", "64_64"]
best_cache = ["8-128-2", "8-128-2", "8-128-2", "8-128-2", "32-128-1"]
ener_delta = ["-43.1486%", "-34.8672%", "-31.4373%", "-30.0324%", "-29.4038%"]
avg_reuse_dist = ["87.924", "172.281", "547.066", "1885.156", "638796"]

prune_convert = lambda a: -float(a.strip("%")) / 100

print(ener_delta_nums := [prune_convert(elem) for elem in ener_delta])
print(avg_reuse_dist_nums := [log(float(elem)) for elem in avg_reuse_dist])


dyn_edp = {
        "Optimal Cache": best_cache,
        "Energy Delta": ener_delta,
        "Avg. Reuse Dist.": avg_reuse_dist,

}

dyn_edp_df = pd.DataFrame(data=dyn_edp, index=indices)
dyn_edp_df.index.name = "Filter Size"
dyn_edp_df.style.set_caption("Dynamic EDP of DNN Convolutions")
# print(tabulate(dyn_edp_df, headers="keys", tablefmt="pipe", stralign="center"))

plt.scatter(avg_reuse_dist_nums, ener_delta_nums)
plt.show()


print(dyn_edp_df.to_latex(label="Energy Delay Product of Dynamic Energy"))
