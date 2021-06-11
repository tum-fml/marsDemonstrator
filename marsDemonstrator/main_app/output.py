from typing import Any, Dict, Union
import pathlib

import pandas as pd
from xlsxwriter import Workbook
from xlsxwriter.format import Format
from xlsxwriter.worksheet import Worksheet

from ..designMethods.en_13001_3_3 import ENComputation, MARSInput

format_dict = Dict[str, Union[Format, Dict[str, Union[Format, Dict[str, Format]]]]]


class ResultWriter():

    def __init__(self, en_computation: ENComputation, en_input: MARSInput, res_name: pathlib.Path) -> None:
        self.en_computation = en_computation
        self.en_input = en_input
        self.res_name = res_name
        self.formats: format_dict = {}
        self.summary: Dict[str, pd.DataFrame] = {}
        self.colors = {
            "blue": "#005293",
            "light_blue": "#89C6EA",
            "green": "#A2AD00",
            "orange": "#E37222",
            "grey_dark": "#585858",
            "grey_light": "#9C9C9C"
        }
        self.workbook: Workbook
        self.sheets: Dict[str, Worksheet] = {}

    def create_summary(self) -> None:
        for part in ["wheel_f", "wheel_r", "rail"]:
            current_part = getattr(self.en_computation, part)
            self.summary[part] = pd.DataFrame({
                "Static proof fulfilled": current_part.proofs["static"],
                "Fatigue proof fulfilled Prediction": current_part.proofs["fatigue"]["preds"],
                "Fatigue proof fulfilled Upper Confidence Level": current_part.proofs["fatigue"]["upper"]
            }).T

    def get_formats(self) -> None:
        # set names for first level in result sheet
        first_level_names = ["wheel_f", "rail", "wheel_r", "parameters"]

        # set names for second level in result sheet
        second_level_names = {first_level: ["static", "fatigue"] for first_level in first_level_names} # second level for results
        second_level_names["parameters"] = ["parameters", "configuration"] # second level for inputs

        # init formats dict
        formats: Dict[str, Any] = {
            "first_level": {},
            "second_level": {first_level_name: {} for first_level_name in first_level_names}
        }
        for first_level_name in first_level_names:
            color = self.colors["light_blue"] if first_level_name == "parameters" else self.colors["blue"]
            font_color = "black" if first_level_name == "parameters" else "white"
            formats["first_level"][first_level_name] = self.workbook.add_format({
                "bold": 1,
                "border": 1,
                "bg_color": color,
                "font_color": font_color
            })
            formats["first_level"][first_level_name].set_rotation(90)
            formats["first_level"][first_level_name].set_align("center")
            formats["first_level"][first_level_name].set_align("vcenter")
            for second_level_name in second_level_names[first_level_name]:
                color_2 = self.colors["green"] if second_level_name in ["static", "parameters"] else self.colors["orange"]
                formats["second_level"][first_level_name][second_level_name] = self.workbook.add_format({
                    "bold": 1,
                    "bg_color": color_2
                })
                formats["second_level"][first_level_name][second_level_name].set_rotation(90)
                formats["second_level"][first_level_name][second_level_name].set_align("center")
                formats["second_level"][first_level_name][second_level_name].set_align("vcenter")
        formats["all"] = self.workbook.add_format()
        formats["all"].set_align("center")
        formats["all"].set_align("vcenter")
        formats["all"].set_num_format("0.00000")

        formats["variable_column"] = self.workbook.add_format()
        formats["variable_column"].set_align("center")
        formats["variable_column"].set_align("vcenter")

        self.formats = formats

    # write results and inputs
    def write(self) -> None:

        def write_name() -> None:

            # get the row that has the name and transform to dataframe
            name_row = self.en_input.input_df.iloc[0].to_frame().T
            name_row.iloc[:, 0] = " "
            name_row.to_excel(writer, sheet_name="summary", startrow=0, startcol=0, header=False)
            name_row.to_excel(writer, sheet_name="results", startrow=0, startcol=0, header=False)

        def write_results() -> None:

            for part, part_outname in zip(["wheel_f", "wheel_r", "rail"], ["Front Wheel", "Rear Wheel", "Rail"]):
                # get attributes of current part
                part_cur = getattr(self.en_computation, part)

                # write summary for current part to summary sheet
                end_row_summary = start_rows["summary"] + len(self.summary[part]) - 1
                self.sheets["summary"].merge_range(start_rows["summary"], 1, end_row_summary, 1, part_outname, self.formats["first_level"][part])

                # write summary for current part
                self.summary[part].to_excel(writer, sheet_name="summary", startrow=start_rows["summary"], startcol=2, header=False)

                # write detailed results for current part
                for res_type, res_type_outname in zip(["static", "fatigue"], ["Static", "Fatigue"]):
                    res_cur = part_cur.results[res_type].T

                    # results
                    res_cur.to_excel(writer, sheet_name="results",
                                     startrow=start_rows["second_level_res"], startcol=2, header=False)

                    # merge second level
                    self.sheets["results"].merge_range(start_rows["second_level_res"], 1, (start_rows["second_level_res"] + len(res_cur) - 1), 1,
                                                       res_type_outname, self.formats["second_level"][part][res_type])

                    start_rows["second_level_res"] += len(res_cur)

                # merge first level
                self.sheets["results"].merge_range(start_rows["first_level_res"], 0, start_rows["second_level_res"] - 1, 0,
                                                   part_outname, self.formats["first_level"][part])
                start_rows["first_level_res"] = start_rows["second_level_res"]
                start_rows["summary"] += len(self.summary[part])

            # merge first level of summary sheet
            self.sheets["summary"].merge_range(0, 0, start_rows["summary"] - 1, 0, "Results", self.formats["first_level"]["wheel_f"])

        def write_inputs() -> None:
            row_diff_summary_results = start_rows["second_level_res"] - start_rows["summary"]
            for input_type, input_type_outname in zip(["parameters", "configuration"], ["EN-13001", "SC Configuration"]):
                input_cur = self.en_input.output[input_type]

                # write input to result sheet
                input_cur.to_excel(writer, sheet_name="results", startrow=start_rows["second_level_res"], startcol=2, header=False)
                input_cur.to_excel(writer, sheet_name="summary", startrow=start_rows["second_level_res"] - row_diff_summary_results, startcol=2, header=False)

                # merge second level
                self.sheets["results"].merge_range(
                    start_rows["second_level_res"], 1, (start_rows["second_level_res"] + len(input_cur) - 1), 1,
                    input_type_outname, self.formats["second_level"]["parameters"][input_type]
                )
                self.sheets["summary"].merge_range(
                    start_rows["second_level_res"] - row_diff_summary_results, 1, 
                    (start_rows["second_level_res"] - row_diff_summary_results + len(input_cur) - 1), 1,
                    input_type_outname, self.formats["second_level"]["parameters"][input_type]
                )

                start_rows["second_level_res"] += len(input_cur)

            # merge first level
            self.sheets["results"].merge_range(
                start_rows["first_level_res"], 0, start_rows["second_level_res"] - 1, 0, "Input Variables", self.formats["first_level"]["parameters"]
            )
            self.sheets["summary"].merge_range(
                start_rows["first_level_res"] - row_diff_summary_results, 0, start_rows["second_level_res"] - 1 - row_diff_summary_results, 0, 
                "Input Variables", self.formats["first_level"]["parameters"]
            )

        with pd.ExcelWriter(self.res_name) as writer: # pylint: disable=abstract-class-instantiated
            self.workbook = writer.book
            self.get_formats()

            # initialize results and summary sheet
            init_df = pd.DataFrame({"init": [0, 1]})
            init_df.to_excel(writer, sheet_name="summary")
            init_df.to_excel(writer, sheet_name="results")

            # get sheets
            self.sheets["results"] = writer.sheets["results"]
            self.sheets["summary"] = writer.sheets["summary"]

            # find number of successful computations
            num_computations = len(self.en_computation.wheel_f.results["static"])

            # set row height for summary sheet
            for i in range(9):
                self.sheets["summary"].set_row(i, 27)

            # set column widths
            self.sheets["results"].set_column(2, 2, 70, self.formats["variable_column"])
            self.sheets["summary"].set_column(2, 2, 70, self.formats["variable_column"])
            self.sheets["results"].set_column(3, (num_computations + 3), 25, self.formats["all"])
            self.sheets["summary"].set_column(3, (num_computations + 3), 25, self.formats["all"])

            # set start row for first and second level for summary and results sheets
            start_rows = {
                "second_level_res": 1,
                "first_level_res": 1,
                "summary": 1,
            }

            write_name()

            write_results()

            write_inputs()
