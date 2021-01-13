from Computation_classes_new import RBG
from output import output_results, output_template


def main_computation(mode, chosen, user_input_data):
    output_template()
    configuration_number = 0
    for row in user_input_data.data.itertuples():
        configuration_number += 1

        rbg = RBG(row, chosen)
        general_computation(rbg)

        if mode == 1:
            mode1()

        elif mode == 2:
            mode2()

        else:
            print("please select the desired mode")
        output_results(results, configuration_number)


def mode1(rbg):
    rbg.wheel.compute_F_sd_s()
    rbg.wheel.compute_F_sd_f()
    rbg.wheel.compute_F_rd_s(rbg.factors, rbg.coefficients, rbg.b, rbg.E_m)
    rbg.wheel.compute_F_rd_f(rbg.factors, rbg.coefficients, rbg.b, rbg.E_m)
    rbg.rail.compute_F_sd_s()
    rbg.rail.compute_F_sd_f()
    rbg.rail.compute_F_rd_s(rbg.factors, rbg.coefficients, rbg.b, rbg.E_m)
    rbg.rail.compute_F_rd_f(rbg.factors, rbg.coefficients, rbg.b, rbg.E_m)
    rbg.compute_condition_fullfilment


def mode2(rbg):
    return rbg.compute_min_d()


def general_computation(rbg):
    rbg.compute_f2()
    rbg.compute_f1()
    rbg.compute_b()
    rbg.get_contact_type()
    rbg.compute_E_m()
