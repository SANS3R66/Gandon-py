import sys
import gandon

from PySide6.QtWidgets import (QApplication, QWidget, QPushButton,
                                QVBoxLayout, QLineEdit, QFileDialog,
                                QSpacerItem, QSizePolicy, QCheckBox,
                                QLabel)
from PySide6.QtCore import (Slot, Qt)
from PySide6.QtGui import QIcon

class GandonGui(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gandon")

        self.gan_text_edit = QLineEdit()
        self.gan_text_edit.setPlaceholderText("Путь до гандона")
        self.button = QPushButton("Выбрать гандона")
        self.button.clicked.connect(self.open_gan_dialog)

        self.gan_text_output_edit = QLineEdit()
        self.gan_text_output_edit.setPlaceholderText("Путь вывода")
        self.button_output = QPushButton("Директория для вывода")
        self.button_output.clicked.connect(self.open_gan_dir_dialog)

        self.button_decrypt = QPushButton("Дешифровать")
        self.button_decrypt.clicked.connect(self.qt_decrypt)

        self.check_decompile = QCheckBox("Использовать декомпиляцию файлов .lu через Java")
        self.decompile_warning = QLabel("(очень плохая декомпиляция)")
        self.decompile_warning.setStyleSheet("color: gray;")
        self.decompile_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #self.check_decompile.toggle()

        layout = QVBoxLayout()
        layout.addWidget(self.gan_text_edit)
        layout.addWidget(self.button)

        layout.addWidget(self.gan_text_output_edit)
        layout.addWidget(self.button_output)

        spacer = QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)

        layout.addWidget(self.check_decompile)
        layout.addWidget(self.decompile_warning)
        layout.addWidget(self.button_decrypt)

        self.setLayout(layout)

    @Slot()
    def open_gan_dialog(self):
        filename = QFileDialog.getOpenFileName(self, "выбери файл .gan (без полного xor)")[0]
        self.gan_text_edit.setText(filename)
        if self.gan_text_output_edit.text() == "":
            self.gan_text_output_edit.setText(filename + ".decrypted")

    @Slot()
    def open_gan_dir_dialog(self):
        dirname = QFileDialog.getExistingDirectory(self, "выбери директорию для вывода файлов .lu")
        self.gan_text_output_edit.setText(dirname)

    @Slot()
    def qt_decrypt(self):
        gandon.gan_decrypt(self.gan_text_edit.text(), self.gan_text_output_edit.text(), self.check_decompile.isChecked())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = GandonGui()
    widget.show()
    sys.exit(app.exec())
