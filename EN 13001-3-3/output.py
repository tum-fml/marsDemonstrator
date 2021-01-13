from pandas import xlsxwriter, read_excel


def output_template():

    # Erstellen von excel Datei
    workbook = xlsxwriter.Workbook('output.xlsx')
    worksheet = workbook.add_worksheet()
    bold = workbook.add_format({'bold': True})

    # Erstellen der Vorlage
    worksheet.write(1, 1, bold, "Configuration")
    worksheet.write(2, 1, bold, "Rail")
    worksheet.write(9, 1, bold, "Wheel")

    for i in [3, 10]:
        worksheet.write(i, 1, "F_rd_s")
        worksheet.write(i+1, 1, "F_sd_s")
        worksheet.write(i+2, 1, "F_rd_f")
        worksheet.write(i+3, 1, "F_sd_f")
        worksheet.write(i+4, 1, "Fatigue strength condition fulfilled")
        worksheet.write(i+5, 1, "Fatigue strength condition fulfilled")
    worksheet.write(16, 1, "Minimal diameter")


def output_results(rbg, configuration_number):
    output = read_excel("ouput.xlsx")

    output.write(1, configuration_number+1, configuration_number)
    # writing rail results
    output.write(3, configuration_number+1, rbg.rail.F_rd_s)
    output.write(4, configuration_number+1, rbg.rail.F_sd_s)
    output.write(5, configuration_number+1, rbg.rail.F_rd_f)
    output.write(6, configuration_number+1, rbg.rail.F_sd_f)
    output.write(7, configuration_number+1, rbg.rail.fullfilment_fatigue_strength)
    output.write(8, configuration_number+1, rbg.rail.fullfilment_static_strength)
    # writing wheel results
    output.write(10, configuration_number+1, rbg.wheel.F_rd_s)
    output.write(11, configuration_number+1, rbg.wheel.F_sd_s)
    output.write(12, configuration_number+1, rbg.wheel.F_rd_f)
    output.write(13, configuration_number+1, rbg.wheel.F_sd_f)
    output.write(14, configuration_number+1, rbg.wheel.fullfilment_fatigue_strength)
    output.write(15, configuration_number+1, rbg.wheel.fullfilment_static_strength)    
    output.write(16, configuration_number+1, rbg.wheel.min_d)
