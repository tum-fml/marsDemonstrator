import math
from collections import namedtuple
import pandas as pd
from Standard_materials import materials


class User_input():

    def __init__(self):
        self.data = None
        self.loaded = False

    def read_data(self, filename):
        self.data = pd.read_excel(filename, index_col=None, header=None)
        self.loaded = True

    def rearrange_data(self):
        self.data = self.data.transpose()
        self.data.columns = self.data.iloc[0]
        self.data = self.data.drop(self.data.index[0])


class Part():

    def __init__(self, chosen_material, chosen_hardened, part_type):
        Material = namedtuple("Material", ["name", "E", "hardened", "HB", "f_y"])
        self.material = Material(chosen_material, materials[part_type][chosen_material].E, chosen_hardened, materials[part_type][chosen_material].HB, materials[part_type][chosen_material].f_y)
        self.F_sd_f = None
        self.F_sd_s = None
        self.F_rd_s = None
        self.F_rd_f = None
        self.fullfilment_fatigue_strength = None
        self.fullfilment_static_strength = None

    def compute_k_c(self):
        return 0.8

    def compute_s_c(self):
        return self.compute_k_c() * self.compute_v_c()

    def compute_F_rd_f(self, factors, coefficients, b, E_m):
        s_c = self.compute_s_c()
        F_u = self.compute_F_u(coefficients, b, E_m)
        self.F_rd_f = (F_u*factors["f_f"]) / (coefficients.Y_cf*(s_c**(1/coefficients.m)))
        return self.F_rd_f

    def compute_F_rd_s(self, factors, coefficients, b, E_m):
        if self.material.hardened == 'False':
            denominator = E_m*coefficients.Y_m
            numerator = (((7*self.material.HB)**2)*math.pi*self.d*b*factors["f_1"]*factors["f_2"]*(1-coefficients.v**2))
            self.F_rd_s = numerator / denominator
        else:
            denominator = E_m*coefficients.Y_m
            numerator = (4.2*self.material.HB)**2*math.pi*self.d*b*factors["f_1"]*factors["f_2"]*(1-coefficients.v**2)
            self.F_rd_s = numerator / denominator
        return self.F_rd_s

    def compute_F_sd_s(self):
        self.F_sd_s = 18000

    def compute_F_sd_f(self):
        self.F_sd_f = 18000

    def compute_F_u(self, coefficients, b, E_m):
        if self.material.hardened == 'False':
            F_u = ((3*self.material.HB)**2*math.pi*self.d*b*(1-coefficients.v**2))/E_m
        else:
            F_u = ((1.8*self.material.f_y)**2*math.pi*self.d*b*(1-coefficients.v**2))/E_m
        return F_u

    def compute_v_c(self):
        i_tot = 1e10
        return i_tot / 1e6

    def compute_min_d_f(self, factors, coefficients, b, E_m):
        s_c = self.compute_s_c()
        if self.material.hardened == 'False':
            denominator = factors["f_f"]*math.pi*(3*self.material.HB)**2*b*(1-coefficients.v**2)
            numerator = (self.F_sd_f*coefficients.Y_cf*s_c**(1/coefficients.m)*E_m)
            min_d_f = numerator / denominator
        else:
            denominator = (factors["f_f"]*math.pi*(1.8*self.material.f_y)**2*b*(1-coefficients.v**2))
            numerator = (self.F_sd_f*coefficients.Y_cf*s_c**(1/coefficients.m)*E_m)
            min_d_f = numerator / denominator
        return min_d_f

    def compute_min_d_s(self, factors, coefficients, b, E_m):
        if self.material.hardened == 'False':
            numerator = self.F_sd_s*coefficients.Y_m * E_m
            denominator = (7*self.material.HB)**2*math.pi*b*(1-coefficients.v**2)*factors["f_1"]*factors["f_2"]
            min_d_s = numerator / denominator
        else:
            numerator = self.F_sd_s*coefficients.Y_m*E_m
            denominator = (4.2*self.material.f_y)**2*math.pi*b*(1-coefficients.v**2)*factors["f_1"]*factors["f_2"]
            min_d_s = numerator / denominator
        return min_d_s


Geometry = namedtuple("Geometry", ["b", "r"])


class Wheel(Part):

    def __init__(self, input_df, chosen_material, chosen_hardened):
        super().__init__(chosen_material, chosen_hardened, "wheel")
        self.geometry = Geometry(input_df.b_w, input_df.r_w)
        self.d = input_df.D_w
        self.min_d = None


class Rail(Part):

    def __init__(self, input_df, chosen_material, chosen_hardened):
        super().__init__(chosen_material, chosen_hardened, "rail")
        self.geometry = Geometry(input_df.b_r, input_df.r_r)
        self.d = input_df.D_w


Coefficients = namedtuple("Coefficients", ["Y_m", "Y_cf", "m", "v", "Y_p"])


class RBG():

    # functions
    def __init__(self, input_df, chosen):
        self.input_df = input_df
        self.wheel = Wheel(input_df, chosen["wheel"]["material"], chosen["wheel"]["hardened"])
        self.rail = Rail(input_df, chosen["rail"]["material"], chosen["rail"]["hardened"])
        f_f = self.input_df.f_f1 * self.input_df.f_f2 * self.input_df.f_f3 * self.input_df.f_f4
        self.factors = {"f_1": None, "f_2": None, "f_f": f_f}
        self.coefficients = Coefficients(1.1, 1.1, 10/3, 0.3, 1)
        self.E_m = None
        self.b = None
        self.w = None

    def compute_f2(self):  # tolerance class: wie können die vom Benutzer übergeben werden?
        self.factors["f_2"] = f_2[input_df.wheel_condition][input_df.tolerance_class]

    def compute_f1(self):
        if self.rail.geometry.b < self.wheel.geometry.b:
            r3 = self.rail.geometry.r
        else:
            r3 = self.wheel.geometry.r
        self.w = abs(self.rail.geometry.b - self.wheel.geometry.b)
        if (r3/self.w) <= 0.1:
            self.factors["f_1"] = 0.85
        elif (r3/self.w) < 0.8 and 0.1 < (r3/self.w):
            self.factors["f_1"] = (0.58 + (0.15*(r3/self.w)))/0.7
        else:
            self.factors["f_1"] = 1

    def compute_min_d(self):
        min_d_r_s = self.rail.compute_min_d_s()
        min_d_r_f = self.rail.compute_min_d_f()
        min_d_w_s = self.wheel.compute_min_d_s()
        min_d_w_f = self.wheel.compute_min_d_f()
        self.wheel.min_d = max(min_d_r_s, min_d_r_f, min_d_w_s, min_d_w_f)

    def compute_b(self):
        self.b = min(self.wheel.geometry.b, self.rail.geometry.b)

    def get_contact_type(self):
        if self.wheel.geometry.r_k < (5*self.b):
            contact = "point"
        else:
            contact = "line"
        return contact

    def compute_E_m(self):
        self.E_m = (2*self.wheel.material.E*self.rail.material.E) / (self.rail.material.E + self.wheel.material.E)

    def compute_condition_fullfilment(self):

        if self.wheel.F_sd_f <= self.wheel.F_rd_f:
            self.wheel.fullfilment_fatigue_strength = True
        else:
            self.wheel.fullfilment_fatigue_strength = False

        if self.wheel.F_sd_s <= self.wheel.F_rd_s:
            self.wheel.fullfilment_static_strength = True
        else:
            self.wheel.fullfilment_static_strength = False

        if self.rail.F_sd_f <= self.rail.F_rd_f:
            self.rail.fullfilment_fatigue_strength = True
        else:
            self.rail.fullfilment_fatigue_strength = False
   
        if self.rail.F_sd_s <= self.rail.F_rd_s():
            self.rail.fullfilment_static_strength = True
        else:
            self.rail.fullfilment_static_strength = False
