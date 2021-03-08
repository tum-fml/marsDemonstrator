# from marsDemonstrator.gui import build_graphical_interface

# interface = build_graphical_interface()
# interface.mainloop()

from PyQt5.QtWidgets import QApplication
from marsDemonstrator.gui.qt_gui import MarsQTGui

app = QApplication([])
gui = MarsQTGui()
app.exec_()
