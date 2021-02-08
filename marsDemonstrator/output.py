import pandas as pd


def create_output_file(en_computation, res_name):

    with pd.ExcelWriter(res_name) as writer:
        first_row = 0
        first_col = 1
        for part in ["wheel_f", "wheel_r", "rail"]:
            part_cur = getattr(en_computation, part)
            for res_type in ["static", "fatigue"]:
                result = part_cur.results[res_type].transpose()
                result.to_excel(writer, header=False, startrow=first_row, startcol=first_col)
                first_row = first_row + len(result)

