import pandas as pd 

wheel_f = en_computation.wheel_f
wheel_r = en_computation.wheel_r
rail = en_computation.rail
wheel_f.results = {}

wheel_f.results["static"] = pd.DataFrame({
    "F_sd_s": wheel_f.F_sd,
    "F_rd_s": wheel_f.F_rd["F_rd_s"],
    "Fulfilled": wheel_f.proofs["static"]
    })

wheel_f.results["fatigue"] = {"prediction": {}, "upper_confidence": {}}
wheel_f.results["fatigue"] = pd.DataFrame({
    "F_sd_f": wheel_f.F_sd,
    "F_u": wheel_f.F_rd["F_u"],
    "v_c": wheel_f.load_collective["v_c"],
    "k_c_pred": wheel_f.load_collective["k_c"]["preds"],
    "s_c_pred": wheel_f.load_collective["s_c"]["preds"],
    "F_rd_f_pred": wheel_f.F_rd["F_rd_f"]["preds"],
    "Fulfilled_pred": wheel_f.proofs["fatigue"]["preds"],
    "k_c_upper": wheel_f.load_collective["k_c"]["upper"],
    "s_c_upper": wheel_f.load_collective["s_c"]["upper"],
    "F_rd_f_upper": wheel_f.F_rd["F_rd_f"]["upper"],
    "Fulfilled_upper": wheel_f.proofs["fatigue"]["preds"]
})
