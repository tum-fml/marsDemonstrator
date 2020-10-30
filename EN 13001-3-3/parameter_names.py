# Variablennamen bitte auf englisch, und zur Strukturiung Klasse named tuple verwenden
# Bei Variablennamen an Formelbezeichnungen in Norm orientieren


from collections import namedtuple

# nur beispielhaft --> unvollständig
# design_parameters: dict mit Parametern die noch berechnet werden müssen
# variable_parameters: Parameter die entweder vorgegeben oder ausgelegt werden können (bisher nur Durchmesser)
Wheel = namedtuple("Wheel", ["material", "geometry", "design_parameters", "variable_parameters"])
Wheel_geometry = namedtuple("Wheel_geometry", ["b"]) # named tuple ist immutable --> daher durchmesser extra
Wheel_material = namedtuple("Wheel_material", ["name", "E", "hardened"])

Rail = None

# wheel_geometry = Wheel_geometry(0.1)
# wheel_material = Wheel_material(None, 210000, True)
# design_parameters_wheel = {
#     "k_c": 1,
#     "i_tot": None,
#     "F_u_f": None,
#     "F_u_s": None
# }

# variable_parameters_wheel = {"d:": None}

# wheel = Wheel(wheel_material, wheel_geometry, design_parameters_wheel, variable_parameters_wheel)

# # input tabellen ebenfalls als named tuple
# wheel_default_material1 = Wheel_material("name1", 210000, True)

# # für parameter die verändert / ausgelegt werden dict verwenden -> mit None initialisieren

# designed_parameters = {
#     "wheel_d": None
# }

# # Zugriff auf Attribute von named tuple

# print(wheel)
# print(f"Wheel material: {wheel.material.E}")
# print(f"K_c: {wheel.design_parameters['k_c']}")

# wheel.geometry.b
