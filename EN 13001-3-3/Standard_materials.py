from collections import namedtuple

Material_standard = namedtuple("Material_standard", ["name", "norm", "material_number", "hardened", "f_y", "HB", "E", "v"])

materials = {"wheel": dict(), "rail": dict()}
materials["wheel"]["GE 300"] = Material_standard("GE 300", "EN 10293", 1.0558, "+N", 520, 155, 210000, 0.3)
materials["wheel"]["EN-GJS 600-3"] = Material_standard("EN-GJS 600-3", "EN 1563", 0.7060, "Gusszustand", 600, 210, 177000, 0.3)
materials["wheel"]["EN-GJS-700-2"] = Material_standard("EN-GJS-700-2", "EN 1563", 0.7070, "Gusszustand", 700, 245, 180000, 0.3)
materials["wheel"]["25CrMo4"] = Material_standard("25CrMo4", "EN 10083-3", 1.7218, "+QT", 650, 190, 210000, 0.3)
materials["wheel"]["34CrMo4"] = Material_standard("34CrMo4", "EN 10083-3", 1.7220, "+QT", 700, 210, 210000, 0.3)
materials["wheel"]["42CrMo4"] = Material_standard("42CrMo4", "EN 10083-3", 1.7225, "+QT", 750, 225, 210000, 0.3)
materials["wheel"]["33NiCrMoV14-5"] = Material_standard("33NiCrMoV14-5", "EN 10280-3", 1.6956, "+QT", 1000, 295, 210000, 0.3)
materials["wheel"]["42CrMo4"] = Material_standard("42CrMo4", "EN 10083-3", 1.7225, "+N, oberflächengehärtet", 420, 252, 210000, 0.3)

materials["rail"]["S235"] = Material_standard("S235", "EN 10025-2", "unknown", "+N", 360, 125, 210000, 0.3)
materials["rail"]["S275"] = Material_standard("S275", "EN 10025-2", "unknown", "+N", 410, 145, 210000, 0.3)
materials["rail"]["S355"] = Material_standard("S355", "EN 10025-2", "unknown", "+N", 520, 175, 210000, 0.3)
materials["rail"]["S690Q"] = Material_standard("S690Q", "EN 10025-6", "1.8928", "+yQT", 760, 225, 210000, 0.3)
materials["rail"]["C35E"] = Material_standard("C35E", "EN 10083-2", "1.1181", "+N", 520, 155, 210000, 0.3)
materials["rail"]["C55"] = Material_standard("C55", "EN 10083-2", "1.0535", "+N", 640, 190, 210000, 0.3)
materials["rail"]["R260Mn"] = Material_standard("R260Mn", "EN 13674-1", "1.0624", "+N", 870, 260, 210000, 0.3)

f_2 = {"Räder mit selbstausrichtender Aufhängung": dict(), "Nicht selbstausrichtende Aufhängung der Räder, Schiene montiert auf einer elastischen Unterlage": dict(), "Nicht selbstausrichtende Aufhängung der Räder, Schiene montiert auf einer starren unterlage": dict()}

f_2["Räder mit selbstausrichtender Aufhängung"][1] = 1
f_2["Räder mit selbstausrichtender Aufhängung"][2] = 1
f_2["Räder mit selbstausrichtender Aufhängung"][3] = 0.95
f_2["Räder mit selbstausrichtender Aufhängung"][4] = 0.9

f_2["Nicht selbstausrichtende Aufhängung der Räder, Schiene montiert auf einer elastischen Unterlage"][1] = 0.95
f_2["Nicht selbstausrichtende Aufhängung der Räder, Schiene montiert auf einer elastischen Unterlage"][2] = 0.95
f_2["Nicht selbstausrichtende Aufhängung der Räder, Schiene montiert auf einer elastischen Unterlage"][3] = 0.95
f_2["Nicht selbstausrichtende Aufhängung der Räder, Schiene montiert auf einer elastischen Unterlage"][4] = 0.95

f_2["Nicht selbstausrichtende Aufhängung der Räder, Schiene montiert auf einer starren unterlage"][1] = 0.9
f_2["Nicht selbstausrichtende Aufhängung der Räder, Schiene montiert auf einer starren unterlage"][2] = 0.85
f_2["Nicht selbstausrichtende Aufhängung der Räder, Schiene montiert auf einer starren unterlage"][3] = 0.8
f_2["Nicht selbstausrichtende Aufhängung der Räder, Schiene montiert auf einer starren unterlage"][4] = 0.75