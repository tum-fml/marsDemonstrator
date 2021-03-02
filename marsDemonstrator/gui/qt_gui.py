import itertools
import pathlib

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QComboBox, QFileDialog, QGridLayout,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTextEdit, QWidget)

# from .main_functions import (init_gps, read_input_file,
#                              run_computation_and_create_output, Main_application)

from .main_functions import Main_application


class I_O_Widgets():

    def __init__(self):
        self.message_box = None
        self.dropdown_config = None

    def get_current_config(self):
        configs = {"1 Mast": "m1", "2 Masts": "m2"}
        configuration = configs[str(self.dropdown_config.currentText())]
        return configuration


class MarsQTGui(QWidget):

    def __init__(self):
        super().__init__()
        # self.main_application = Run_vars()
        self.main_application = Main_application()
        self.io_widgets = I_O_Widgets()
        self.io_widgets.message_box = QTextEdit()
        self.create_config_box()
        self.create_file_dialog_box()
        self.create_start_button()
        main_layout = QGridLayout()
        main_layout.addWidget(self.config_box)
        main_layout.addWidget(self.file_dialog_box)
        main_layout.addWidget(self.btn_start)
        main_layout.addWidget(self.io_widgets.message_box)
        self.setLayout(main_layout)
        self.fatal_error = None
        # self.app.font().setPointSize(18)

        # set general font size
        self.setGeometry(100, 100, 1000, 500)
        self.setFont(QFont("Arial", 9))
        self.show()

    def create_config_box(self):

        def update_config():
            # self.io_widgets.message_box.clear()
            self.io_widgets.message_box.clear()
            self.io_widgets.message_box.setText("Updating configuration. This may take up to 30 seconds")
            self.io_widgets.message_box.repaint()
            self.main_application.input.config = self.io_widgets.get_current_config()
            self.main_application.init_gps()
            # init_gps(self.main_application)
            self.io_widgets.message_box.setText("Configuration updated")

        self.config_box = QGroupBox()
        layout_config_box = QHBoxLayout() 
        self.io_widgets.dropdown_config = QComboBox()
        self.io_widgets.dropdown_config.addItems(["1 Mast", "2 Masts"])
        btn_config = QPushButton("Update Configuration")
        btn_config.clicked.connect(update_config)
        layout_config_box.addWidget(QLabel("Choose configuration"))
        layout_config_box.addWidget(self.io_widgets.dropdown_config)
        layout_config_box.addWidget(btn_config)
        # layout_config_box.addStretch(3)
        self.config_box.setLayout(layout_config_box)

    def create_file_dialog_box(self):
        def open_file_dialog():
            self.io_widgets.message_box.clear()
            path_file_dialog_box.clear()
            self.main_application.input_file_path = None
            self.main_application.input_file_path, _ = QFileDialog.getOpenFileName(caption="Choose input file")
            self.main_application.input_file_path = pathlib.Path(self.main_application.input_file_path)
            self.fatal_error = None
            try:
                # read_input_file(self.main_application.input_file_path, self.main_application.input)
                self.fatal_error = self.main_application.read_input_file(self.main_application.input_file_path)
                if self.fatal_error:
                    self.io_widgets.message_box.setText("Fatal error in input file")
                    self.io_widgets.message_box.append(self.fatal_error)
                    if self.main_application.input.error_report:
                        self.write_error_reports()
                    return

                path_file_dialog_box.setText(str(self.main_application.input_file_path))
            except Exception as e:
                self.io_widgets.message_box.setText("Invalid Input File, unknown error")
                self.io_widgets.message_box.append(e.__repr__())
                self.fatal_error = True

        self.file_dialog_box = QGroupBox()
        layout_file_dialog_box = QHBoxLayout()
        btn_file_dialog_box = QPushButton("Choose input file")
        btn_file_dialog_box.clicked.connect(open_file_dialog)
        path_file_dialog_box = QLineEdit()
        layout_file_dialog_box.addWidget(btn_file_dialog_box)
        layout_file_dialog_box.addWidget(path_file_dialog_box)
        self.file_dialog_box.setLayout(layout_file_dialog_box)

    def create_start_button(self):

        def start():
            self.io_widgets.message_box.clear()
            if self.main_application.input_file_loaded is None or self.fatal_error is not None:
                self.io_widgets.message_box.setText("Please upload an input file!")
                self.main_application.input_file_loaded = None
                return
            self.io_widgets.message_box.setText("Computation started, please wait")
            self.io_widgets.message_box.repaint()
            if self.main_application.config_loaded is None:
                self.main_application.input.config = self.io_widgets.get_current_config()
                # init_gps(self.main_application)
                self.io_widgets.message_box.setText("Updating configuration. This may take up to 30 seconds")
                self.io_widgets.message_box.repaint()
                self.main_application.init_gps()
                self.io_widgets.message_box.setText("Configuration updated")
                self.io_widgets.message_box.repaint()

            # run_computation_and_create_output(self.main_application, 1, self.main_application)
            self.main_application.run_computation_and_create_output(1)
            self.io_widgets.message_box.setText(f"Generated output file: output_no{self.main_application.num_run}.xlsx")
            self.write_error_reports()

        self.btn_start = QPushButton("Start computation")
        self.btn_start.clicked.connect(start)

    def write_error_reports(self):
        error_reports = list(itertools.chain(*self.main_application.input.error_report))

        if len(error_reports) > 0:
            self.io_widgets.message_box.append("\nErrors found:")
            for error in error_reports:
                self.io_widgets.message_box.append(error)
