import pandas as pd 
from tabulate import tabulate


######################################################################################
# indices = ["20_40", "40_20","40_80", "80_40", "80_160", "160_80"]
# best_cache = ["8-128-2", "8-128-2", "8-128-2", "8-128-2","16-128-2", "16-128-2"]
# ener_delta = ["-2.2565%", "-2.2767%", "-2.3737%", "-2.3768%", "-2.3961%", "-2.3966%"]
# reuse_dist = ["284.203", "918.453", "796.897", "772.089", "5471.917", "3797.557"]


# leak_pdp = {
        # "Optimal Cache": best_cache,
        # "Energy Delta": ener_delta,
          # "Avg. Reuse Dist.": reuse_dist

# }

# leak_pdp_df = pd.DataFrame(data=leak_pdp, index=indices)
# leak_pdp_df.index.name = "Row and Col. Size"
# leak_pdp_df.style.set_caption("Leakage PDP of DNN Convolutions")
# # print(tabulate(leak_pdp_df, headers="keys", tablefmt="pipe", stralign="center"))

# print(leak_pdp_df.to_latex(label="Power Delay Product of Leakage Energy"))


######################################################################################
# indices = ["20_40", "40_20","40_80", "80_40", "80_160", "160_80"]
# best_cache = ["8-128-2", "8-128-2", "8-128-2", "8-128-2","16-128-2", "16-128-2"]
# ener_delta = ["-2.4168%", "-2.4169%", "-2.4170%", "-2.4170%", "-2.4170%", "-2.4170%"]

# reuse_dist = ["284.203", "918.453", "796.897", "772.089", "5471.917", "3797.557"]
# leak_edp = {
        # "Optimal Cache": best_cache,
        # "Energy Delta": ener_delta,
          # "Avg. Reuse Dist.": reuse_dist

# }

# leak_edp_df = pd.DataFrame(data=leak_edp, index=indices)
# leak_edp_df.index.name = "Row and Col. Size"
# leak_edp_df.style.set_caption("Leakage EDP of DNN Convolutions")
# # print(tabulate(leak_edp_df, headers="keys", tablefmt="pipe", stralign="center"))

# print(leak_edp_df.to_latex(label="Energy Delay Product of Leakage Energy"))

######################################################################################
# indices = ["20_40", "40_20","40_80", "80_40", "80_160", "160_80"]
# best_cache = ["8-128-2", "8-128-2", "8-128-2", "8-128-2","16-128-2", "16-128-2"]
# ener_delta = ["-12.8716%", "-13.8660%", "-13.1110%", "-13.4559%", "-13.0112%", "-12.9724%"]

# reuse_dist = ["284.203", "918.453", "796.897", "772.089", "5471.917", "3797.557"]
# dyn_pdp = {
        # "Optimal Cache": best_cache,
        # "Energy Delta": ener_delta,
          # "Avg. Reuse Dist.": reuse_dist

# }

# dyn_pdp_df = pd.DataFrame(data=dyn_pdp, index=indices)
# dyn_pdp_df.index.name = "Row and Col. Size"
# dyn_pdp_df.style.set_caption("Dynamic PDP of DNN Convolutions")
# # print(tabulate(dyn_pdp_df, headers="keys", tablefmt="pipe", stralign="center"))

# print(dyn_pdp_df.to_latex(label="Power Delay Product of Dynamic Energy"))


######################################################################################
indices = ["20_40", "40_20","40_80", "80_40", "80_160", "160_80"]
best_cache = ["8-128-2", "8-128-2", "8-128-2", "8-128-2","16-128-2", "16-128-2"]
ener_delta = ["-86.4208%", "-87.9636%", "-86.5984%", "-87.2112%", "-86.3589%", "-86.4269%"]

reuse_dist = ["284.203", "918.453", "796.897", "772.089", "5471.917", "3797.557"]
dyn_edp = {
        "Optimal Cache": best_cache,
        "Energy Delta": ener_delta,
          "Avg. Reuse Dist.": reuse_dist

}

dyn_edp_df = pd.DataFrame(data=dyn_edp, index=indices)
dyn_edp_df.index.name = "Row and Col. Size"
dyn_edp_df.style.set_caption("Dynamic EDP of DNN Convolutions")
# print(tabulate(dyn_edp_df, headers="keys", tablefmt="pipe", stralign="center"))


print(dyn_edp_df.to_latex(label="Energy Delay Product of Dynamic Energy"))
