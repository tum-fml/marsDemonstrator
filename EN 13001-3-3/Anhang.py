from collections import namedtuple
import numpy as np

wheel_standard=namedtuple("wheel_standard",'name norm material_number condition f_y HB E')
rail_standard=namedtuple("rail_standard",'name norm material_number condition f_y HB E')

wheel_dict={}
wheel_dict["GE 300"]=wheel_standard("GE 300", "EN 10293",1.0558, "+N",520 , 155 , 210000  )
wheel_dict["EN-GJS 600-3"]=wheel_standard( "EN-GJS 600-3","EN 1563",0.7060 ,"Gusszustand", 600, 210, 177000)
wheel_dict["EN-GJS-700-2"]=wheel_standard("EN-GJS-700-2","EN 1563",0.7070,"Gusszustand",700 ,245, 180000)
wheel_dict["25CrMo4"]=wheel_standard("25CrMo4","EN 10083-3",1.7218,"+QT",650 ,190, 210000)
wheel_dict["34CrMo4"]=wheel_standard("34CrMo4","EN 10083-3",1.7220,"+QT",700 ,210,210000)
wheel_dict["42CrMo4"]=wheel_standard("42CrMo4","EN 10083-3",1.7225,"+QT",750 ,225,210000)
wheel_dict["33NiCrMoV14-5"]=wheel_standard("33NiCrMoV14-5","EN 10280-3",1.6956,"+QT",1000 ,295,210000)
wheel_dict["42CrMo4"]=wheel_standard("42CrMo4","EN 10083-3",1.7225,"+N, oberflächengehärtet",420 ,252,210000)


rail_dict={}
rail_dict["S235"]=rail_standard("S235","EN 10025-2","unknown","+N",360 ,125,210000)
rail_dict["S275"]=rail_standard("S275","EN 10025-2","unknown","+N",410 ,145,210000)
rail_dict["S355"]=rail_standard("S355","EN 10025-2","unknown","+N",520 ,175,210000)
rail_dict["S690Q"]=rail_standard("S690Q","EN 10025-6","1.8928","+yQT",760 ,225,210000)
rail_dict["C35E"]=rail_standard("C35E","EN 10083-2","1.1181","+N",520 ,155,210000)
rail_dict["C55"]=rail_standard("C55","EN 10083-2","1.0535","+N",640 ,190,210000)
rail_dict["R260Mn"]=rail_standard("R260Mn","EN 13674-1","1.0624","+N",870 ,260,210000)










