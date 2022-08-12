import pandas as pd 
import numpy as np
from tabulate import tabulate
import seaborn as sns
import matplotlib.pyplot as plt
######################################################################################
# indices = ["4_4", "8_8","16_16", "32_32", "64_64", "128_128"]
# best_cache = ["4-32-2", "4-32-2", "8-64-1", "8-128-2","8-128-2", "16-128-2"]
# ener_delta = ["-26.3900%", "-35.4855%", "-37.3727%", "-38.9140%", "-39.4063%", "-39.6074%"]
# avg_reuse = ["49.919", "107.744", "266.211", "495.945", "1039.392", "2120.008"]

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
# indices = ["4_4", "8_8","16_16", "32_32", "64_64", "128_128"]
# best_cache = ["4-32-2", "4-32-2", "8-64-1", "8-128-2","8-128-2", "16-128-2"]
# ener_delta = ["-39.3439%", "-39.4626%", "-39.4729%", "-39.4746%", "-39.4747%", "-39.4747%"]

# avg_reuse = ["49.919", "107.744", "266.211", "495.945", "1039.392", "2120.008"]
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
# indices = ["4_4", "8_8","16_16", "32_32", "64_64", "128_128"]
# best_cache = ["4-32-2", "4-32-2", "8-64-1", "8-128-2","8-128-2", "16-128-2"]
# ener_delta = ["-32.7171%", "-30.7420%", "-29.6645%", "-29.1002%", "-28.8115%", "-28.6659%"]

# avg_reuse = ["49.919", "107.744", "266.211", "495.945", "1039.392", "2120.008"]
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
indices = ["4x4", "8x8","16x16", "32x32", "64x64", "128x128"]
best_cache = ["4-32-2", "4-32-2", "8-64-1", "8-128-2","8-128-2", "16-128-2"]
ener_delta = ["-70.9201%", "-66.5369%", "-64.0168%", "-62.6658%", "61.9664","-61.6106%"]


trial1 = [1, 2, 4, 8, 16, 32, 64, 128]


misses = [[16, 8, 4, 2, 1, 1, 1, 1],
    [32, 16, 8, 4, 2, 1, 1, 1],
    [64, 32, 16, 8, 4, 2, 1, 1],
    [256, 128, 64, 32, 16, 8, 4, 2],
    [1024, 512, 256, 128, 64, 32, 16, 8],
    [4096, 2048, 1024, 512, 256, 128, 64, 32]]

misses = np.asarray(misses)
data = {'4x4': 100, '8x8': 328, '16x16': 1168, '32x32': 4384, '64x64': 16960, '128x128': 66688}
names = list(data.keys())
values = list(data.values())
fig = plt.figure(dpi=1200)
ax = plt.subplot( 111 )
ax.minorticks_on()
ax.grid()
ax.set_xlabel('Workload Intensity')
ax.set_ylabel('Number of Cycles for GEMMs' )
ax.set_title('Computational Explosion of MAC Ops.')
plt.yticks(fontsize=14,)

plt.xticks(fontsize=14,)
plt.plot(names, values, marker='o',linestyle='--')
ax.legend()
plt.savefig("comps.png", dpi=1200)
plt.show()


# x = np.linspace(0, 66688, 6)
# print(x)
# fig = plt.figure()
# ax = plt.subplot( 111 )
# ax.minorticks_on()
# ax.grid()
# ax.set_xlabel( 'Block Size (Bytes)' )
# ax.set_ylabel( 'Cache Misses (Read + Write)' )
# ax.set_title('Cache Misses w.r.t Block Size' )

# plt.plot(x, misses.T, marker='o',linestyle='--', label=indices)
# ax.legend()
# plt.savefig("block.pdf", bbox_inches='tight')
# plt.show()

# avg_reuse = ["49.919", "107.744", "266.211", "495.945", "1039.392", "2120.008"]
# dyn_edp = {
        # "Optimal Cache": best_cache,
        # "Energy Delta": ener_delta,
        # "Avg. Reuse Dist.": avg_reuse,

# }

# dyn_edp_df = pd.DataFrame(data=dyn_edp, index=indices)
# dyn_edp_df.index.name = "Input Neuron Count"
# dyn_edp_df.style.set_caption("Dynamic EDP of DNN Convolutions")
# # print(tabulate(dyn_edp_df, headers="keys", tablefmt="pipe", stralign="center"))


# print(dyn_edp_df.to_latex(label="Energy Delay Product of Dynamic Energy"))
