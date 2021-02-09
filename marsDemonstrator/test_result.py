import pandas as pd 

import xlsxwriter
import openpyxl


def output_template(input_parameters):

    workbook1 = xlsxwriter.Workbook('outputparameterss.xlsx')
    inputandoutput = workbook1.add_worksheet(name="Output")
    output_parameters = ["F_rd_s", "F_sd_s", "F_rd_f", "F_sd_f", "Fatigue strength condition", "Static strength condition"]
    input_parameters.extend(["wheel material", "wheel E", "wheel hardeness", "wheel f_y", "rail material", "rail E", "rail hardeness", "rail f_y"])

    # design, Lage, farbe schrift und zelle
    cell_format = workbook1.add_format({'align': 'center', 'valign': 'center'})
    cell_format2 = workbook1.add_format({"fg_color": "yellow", 'bold': True, 'align': 'center', 'valign': 'center'})
    cell_format3 = workbook1.add_format({'fg_color': "green", 'bold': True, 'align': 'center', 'valign': 'center'})
    inputandoutput.set_column(1, 1, 30)

    merge_format = workbook1.add_format({
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'silver'})
    merge_format.set_rotation(90)
    inputandoutput.merge_range(1, 0, len(input_parameters), 0, 'parameters', merge_format)
    inputandoutput.merge_range(len(input_parameters)+1, 0, len(output_parameters)+len(input_parameters) + 9, 0, 'results', merge_format)

    # Erstellen der Vorlage
    inputandoutput.write(0, 1, "Configuration", cell_format3)
    inputandoutput.write(len(input_parameters)+1, 1, "Rail", cell_format2)
    inputandoutput.write(len(input_parameters)+8, 1, "Wheel", cell_format2)

    for parameter_in in range(len(input_parameters)):
        inputandoutput.write(1+parameter_in, 1, input_parameters[parameter_in], cell_format)

    for cell in [len(input_parameters)+2, len(input_parameters)+9]:
        for parameter_out in range(len(output_parameters)):
            inputandoutput.write(cell+parameter_out, 1, output_parameters[parameter_out], cell_format)

    workbook1.close()


def output_results(rbg, configuration_number, user_input_data):

    output = openpyxl.load_workbook(filename='ouput.xlsx', read_only=False, keep_vba=True)

    # write the configuration numbers
    output.write(0, configuration_number+1, configuration_number)

    # results
    results_wheel = [rbg.wheel.F_rd_s, rbg.wheel.F_sd_s, rbg.wheel.F_rd_f, rbg.wheel.F_sd_f, rbg.wheel.fullfilment_fatigue_strength, rbg.wheel.fullfilment_static_strength, rbg.wheel.min_d]
    results_rail = [rbg.rail.F_rd_s, rbg.rail.F_sd_s, rbg.rail.F_rd_f, rbg.rail.F_sd_f, rbg.rail.fullfilment_fatigue_strength, rbg.rail.fullfilment_static_strength]

    # writing parameters
    for wheelresult in range(len(results_wheel)):
        output.write(wheelresult+len(user_input_data)+3, configuration_number+1, results_wheel[wheelresult])

    for railresult in range(len(results_rail)):
        output.write(railresult+len(user_input_data)+len(results_wheel)+5, configuration_number+1, results_rail[railresult])

    output.write(len(user_input_data)+len(results_rail)+len(results_wheel)+5, configuration_number+1, rbg.wheel.min_d)
    output.save('output.xlsx')
