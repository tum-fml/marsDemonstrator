import pandas as pd


def create_output_file(en_computation, en_input, res_name):

    with pd.ExcelWriter(res_name) as writer:
        workbook = writer.book
        formats = get_formats(workbook)
        init_df = pd.DataFrame({"init": [0, 1]})
        init_df.to_excel(writer, sheet_name="output")
        num_computations = len(en_computation.wheel_f.results["static"])
        sheet = writer.sheets["output"]
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, (num_computations + 3), 18, formats["all"])
        start_row_second_level = 0
        start_row_first_level = 0

        for part in ["wheel_f", "wheel_r", "rail"]:
            part_cur = getattr(en_computation, part)
            for res_type in ["static", "fatigue"]:
                res_cur = part_cur.results[res_type].transpose()
                res_cur.to_excel(writer, sheet_name="output",
                                 startrow=start_row_second_level, startcol=2, header=False)
                sheet.merge_range(start_row_second_level, 1, (start_row_second_level + len(res_cur) - 1), 1,
                                  res_type, formats["second_level"][part][res_type])
                start_row_second_level += len(res_cur)
            sheet.merge_range(start_row_first_level, 0, start_row_second_level - 1, 0,
                              part, formats["first_level"][part])
            start_row_first_level = start_row_second_level

        for input_type in ["parameters", "configuration"]:
            input_cur = en_input.output[input_type]
            input_cur.to_excel(writer, sheet_name="output", startrow=start_row_second_level, startcol=2, header=False)
            sheet.merge_range(start_row_second_level, 1, (start_row_second_level + len(input_cur) - 1), 1,
                              input_type, formats["second_level"]["parameters"][input_type])
            start_row_second_level += len(input_cur)
        sheet.merge_range(start_row_first_level, 0, start_row_second_level - 1, 0, "parameters", formats["first_level"]["parameters"])


def get_formats(workbook):
    colors = {"blue": "#005293",
              "light_blue": "#89C6EA",
              "green": "#A2AD00",
              "orange": "#E37222",
              "grey_dark": "#585858",
              "grey_light": "#9C9C9C"}
    first_level_names = ["wheel_f", "rail", "wheel_r", "parameters"]
    second_level_names = {first_level: ["static", "fatigue"] for first_level in first_level_names}
    second_level_names["parameters"] = ["parameters", "configuration"]
    formats = {"first_level": {},
               "second_level": {first_level_name: {} for first_level_name in first_level_names}}
    for first_level_name in first_level_names:
        color = colors["light_blue"] if first_level_name == "parameters" else colors["blue"]
        formats["first_level"][first_level_name] = workbook.add_format({
            "bold": 1,
            "border": 1,
            "bg_color": color
        })
        formats["first_level"][first_level_name].set_rotation(90)
        formats["first_level"][first_level_name].set_align("center")
        formats["first_level"][first_level_name].set_align("vcenter")
        for second_level_name in second_level_names[first_level_name]:
            color_2 = colors["green"] if second_level_name in ["static", "parameters"] else colors["orange"]
            formats["second_level"][first_level_name][second_level_name] = workbook.add_format({
                "bold": 1,
                "bg_color": color_2
            })
            formats["second_level"][first_level_name][second_level_name].set_rotation(90)
            formats["second_level"][first_level_name][second_level_name].set_align("center")
            formats["second_level"][first_level_name][second_level_name].set_align("vcenter")
    formats["all"] = workbook.add_format()
    formats["all"].set_align("center")
    formats["all"].set_align("vcenter")
    formats["all"].set_num_format("0.00000")
    return formats
