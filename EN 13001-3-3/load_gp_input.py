import pandas as pd
import joblib
import torch 
import numpy as np

config = "m1"

gp_input = pd.read_excel("Test.xlsx", index_col=None, header=None)
gp_input.drop(gp_input.columns[0], axis=1, inplace=True)
gp_input = gp_input.transpose()
gp_input.columns = gp_input.iloc[0]
gp_input.drop(gp_input.index[0], inplace=True)

input_scale = joblib.load("input_scale.pkl")
input_scale = input_scale[config]

if config == "m1":
    gp_input["LiftCG"] = (gp_input["LiftCG"] - gp_input["MastCenterOfGravityX"]) * gp_input["TraverseWheelDistance"]
gp_input = gp_input.to_numpy()
for idx, row in enumerate(gp_input):
    gp_input[idx, :] = (row - input_scale["min"]) / input_scale["diff"]

gp_input = torch.from_numpy(np.vstack(gp_input[:, :]).astype(np.float64)).double()
