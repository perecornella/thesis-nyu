import sys
import matplotlib.pyplot as plt
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QRadioButton, QHBoxLayout, QLineEdit, QLabel, QComboBox, QMessageBox, QButtonGroup
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from utils import plot_dashboard, read_in_data
from metrics import lacking_name
from datetime import datetime

class Canvas(FigureCanvas):
    def __init__(self, parent, sample, filename):
        # Create the figure using the plot_dashboard function
        fra_summary, fig = plot_dashboard(sample, metric=lacking_name, filename=filename)
        parent.d = fra_summary[0]
        parent.bf = fra_summary[1]
        parent.th = fra_summary[2]
        super().__init__(fig)  # Pass the figure to the FigureCanvas constructor
        self.setParent(parent)  # Set the parent for the canvas


class AppDemo(QWidget):
    def __init__(self, input_directory=None, input_file=None):

        super().__init__()

        self.input_directory = input_directory
        self.input_file = input_file

        self.set_directory()
        self.load_data_on_checkpoint()
        self.create_widgets()
        self.set_layout()


    def set_directory(self):

        all_done = True
        for i, row in dir_info.iterrows():
            if row['end'] - row['checkpoint'] > 0:
                self.checkpoint = row['checkpoint']
                self.end = row['end']
                self.dir = row['name']
                all_done = False
                break
        if all_done:
            print("All directories have been processed.")
            dir_info.to_csv('metadata/dir_info.csv')
            metadata.to_csv(f'metadata/{datachannel}.csv')
            sys.exit(1)

        if self.input_directory is not None:
            try:
                row = dir_info[dir_info['name'] == self.input_directory].iloc[0]
                self.checkpoint = row['checkpoint']
                self.end = row['end']
                self.dir = row['name']
            except:
                print("There's something wrong with the directory specified.")
                sys.exit(1)
        
        self.batch_size = 10  # this is a parameter
        self.number_of_batches = (self.end - self.checkpoint) // self.batch_size
        self.batch_pointer = 0
        self.counter = 0

    def load_data_on_checkpoint(self):

        all_error = True
        while self.batch_pointer < self.number_of_batches:

            if self.counter == 0:
                if self.input_file is not None:
                    batch = [int(self.input_file[1:]), 1]
                else:
                    if self.end - self.checkpoint > 10:
                        batch = [self.checkpoint, self.checkpoint + 10]
                    else:
                        batch = [self.checkpoint, self.end]

                self.data, self.tonedata, self.error_files = read_in_data(root_dir + self.dir, batch, datachannel, triggerchannel)
                self.df = pd.merge(self.data, self.tonedata, how="left", on="toneid")
                    
                if len(self.error_files) - (batch[1] - batch[0]) == 0:  # All files are error
                    self.batch_pointer += 1
                    self.checkpoint += batch[1] - batch[0]
                    dir_info.loc[dir_info['name'] == self.dir, 'checkpoint'] = self.checkpoint
                    break
                else:
                    self.counter = (batch[1] - batch[0]) - len(self.error_files)
            
            else:
                if self.input_file is not None:
                    self.sample = self.df[self.df["toneid"].str.startswith(self.input_file)]
                    self.filename = f"{self.dir}{self.input_file} channel {datachannel}"
                    all_error = False
                else:
                    while self.checkpoint < self.end:
                        if f"A{self.checkpoint:03d}" not in self.error_files:
                            self.sample = self.df[self.df["toneid"].str.startswith(f"A{self.checkpoint:03d}")]
                            self.filename = f"{self.dir}A{self.checkpoint:03d} channel {datachannel}"
                            all_error = False
                            self.counter -= 1
                            break
                        else:
                            self.checkpoint += 1
                    
                    dir_info.loc[dir_info['name'] == self.dir, 'checkpoint'] = self.checkpoint
                    
                if not all_error:
                    break

        if all_error:
            print(f"All the remaining non-error files in {self.dir} have been processed.")
            dir_info.to_csv('metadata/dir_info.csv')
            metadata.to_csv(f'metadata/{datachannel}.csv')
            sys.exit(1)

    def create_widgets(self):

        # FRA or Traces question for Visualization
        self.visualization_combobox = QComboBox()
        self.visualization_combobox.addItems(["FRA", "Traces"])
        self.visualization_layout = QHBoxLayout()
        self.visualization_layout.addWidget(QLabel("Visualization"))
        self.visualization_layout.addWidget(self.visualization_combobox)

        # Channel 0 or 2 question for Channel
        self.channel_combobox = QComboBox()
        self.channel_combobox.addItems(["Channel 0", "Channel 2"])
        self.channel_layout = QHBoxLayout()
        self.channel_layout.addWidget(QLabel("Channel"))
        self.channel_layout.addWidget(self.channel_combobox)

        # Tuned button
        self.tuned_button_group = QButtonGroup(self)
        self.tuned_layout = QHBoxLayout()
        self.tuned_button_yes = QRadioButton("Yes")
        self.tuned_button_no = QRadioButton("No")
        self.tuned_layout.addWidget(QLabel("Tuned"))
        self.tuned_layout.addWidget(self.tuned_button_yes)
        self.tuned_layout.addWidget(self.tuned_button_no)
        self.tuned_button_group.addButton(self.tuned_button_yes)
        self.tuned_button_group.addButton(self.tuned_button_no)

        # Clear button
        self.clear_button_group = QButtonGroup(self)
        self.clear_layout = QHBoxLayout()
        self.clear_button_yes = QRadioButton("Yes")
        self.clear_button_no = QRadioButton("No")
        self.clear_layout.addWidget(QLabel("Clear"))
        self.clear_layout.addWidget(self.clear_button_yes)
        self.clear_layout.addWidget(self.clear_button_no)
        self.clear_button_group.addButton(self.clear_button_yes)
        self.clear_button_group.addButton(self.clear_button_no)

        # Healthy button
        self.healthy_button_group = QButtonGroup(self)
        self.healthy_layout = QHBoxLayout()
        self.healthy_button_yes = QRadioButton("Yes")
        self.healthy_button_no = QRadioButton("No")
        self.healthy_layout.addWidget(QLabel("Healthy"))
        self.healthy_layout.addWidget(self.healthy_button_yes)
        self.healthy_layout.addWidget(self.healthy_button_no)
        self.healthy_button_group.addButton(self.healthy_button_yes)
        self.healthy_button_group.addButton(self.healthy_button_no)

        # Intra/Extra question for Type
        self.type_combobox = QComboBox()
        self.type_combobox.addItems(["Intra", "Extra"])
        self.type_layout = QHBoxLayout()
        self.type_layout.addWidget(QLabel("Type"))
        self.type_layout.addWidget(self.type_combobox)

        # Coordinates input for x, y, z
        self.x0_input = QLineEdit()
        self.xf_input = QLineEdit()
        self.i_input = QLineEdit()
        self.n_input = QLineEdit()
        self.y_input = QLineEdit()
        self.z_input = QLineEdit()
        self.coord_layout = QHBoxLayout()
        self.coord_layout.addWidget(QLabel("Coordinates"))
        self.coord_layout.addWidget(QLabel("x0:"))
        self.coord_layout.addWidget(self.x0_input)
        self.coord_layout.addWidget(QLabel("xf:"))
        self.coord_layout.addWidget(self.xf_input)
        self.coord_layout.addWidget(QLabel("i:"))
        self.coord_layout.addWidget(self.i_input)
        self.coord_layout.addWidget(QLabel("n:"))
        self.coord_layout.addWidget(self.n_input)
        self.coord_layout.addWidget(QLabel("y:"))
        self.coord_layout.addWidget(self.y_input)
        self.coord_layout.addWidget(QLabel("z:"))
        self.coord_layout.addWidget(self.z_input)

        # Add Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.on_send_clicked)

    def set_layout(self):

        self.layout = QVBoxLayout()

        self.layout.addLayout(self.visualization_layout)
        self.layout.addLayout(self.channel_layout)
        self.chart = Canvas(self, self.sample, self.filename)
        self.layout.addWidget(self.chart)
        self.layout.addLayout(self.tuned_layout)
        self.layout.addLayout(self.clear_layout)
        self.layout.addLayout(self.healthy_layout)
        self.layout.addLayout(self.type_layout)
        self.layout.addLayout(self.coord_layout)
        self.layout.addWidget(self.send_button)
    
        self.setLayout(self.layout)

# Action functions

    def on_send_clicked(self):
        if self.input_file is not None:
            QMessageBox.warning(self, "Warning", "You inserted a filename; changes cannot be persisted.")

        else:
            tuned = "Yes" if self.tuned_button_yes.isChecked() else "No"
            clear = "Yes" if self.clear_button_yes.isChecked() else "No"
            healthy = "Yes" if self.healthy_button_yes.isChecked() else "No"
            selected_type = self.type_combobox.currentText()
            x0 = float(self.x0_input.text()) if self.x0_input.text() else None
            xf = float(self.xf_input.text()) if self.xf_input.text() else None
            i = float(self.i_input.text()) if self.i_input.text() else None
            n = float(self.n_input.text()) if self.n_input.text() else None
            y = float(self.y_input.text()) if self.y_input.text() else None
            z = float(self.z_input.text()) if self.z_input.text() else None

            if None not in [x0, xf, i, n]:
                x = x0 + i * (xf - x0) // n
            else:
                x = None

            confirmation_message = f"Tuned: {tuned}\nClear: {clear}\nHealthy: {healthy}\nType: {selected_type}\nCoordinates: x={x0 + i * (xf - x0) // n}, y={y}, z={z}"
            question = QMessageBox.question(self, 'Confirm your entries', f"Are you sure you want to submit the following values?\n\n{confirmation_message}", 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if question == QMessageBox.Yes:
                new_row = {
                    'directory': self.dir,
                    'filename': f"A{self.checkpoint:03d}",
                    'tuned': tuned,
                    'clear': clear,
                    'healthy': healthy,
                    'type': selected_type,
                    'x': x,
                    'y': y,
                    'z': z,
                    'd': self.d,
                    'bf': self.bf,
                    'th': self.th,
                    'entrydate': datetime.now()
                }

                metadata.loc[len(metadata)] = new_row
                self.checkpoint += 1
                self.load_data_on_checkpoint()
                self.update_dashboard()

            else:
                print("Submission cancelled.")

    def update_dashboard(self):
        plt.close(self.chart.figure)
        self.layout.removeWidget(self.chart)
        self.chart.deleteLater()
        self.chart = Canvas(self, self.sample, self.filename)
        self.layout.insertWidget(0, self.chart)

    def closeEvent(self, event):
        question = QMessageBox.question(self, 'Confirm Exit',
                                    "Do you want to save changes before exiting?",
                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
                                    QMessageBox.Yes)

        if question == QMessageBox.Yes:
            dir_info.to_csv('metadata/dir_info.csv')
            metadata.to_csv(f'metadata/{datachannel}.csv')
            event.accept()  # Close the window
        elif question == QMessageBox.No:
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    
    # Define the data and parameters
    datachannel = 'di0P'
    triggerchannel = 'di4P'
    root_dir = "/Users/perecornella/Library/CloudStorage/GoogleDrive-pere.cornella@estudiantat.upc.edu/My Drive/ReyesLabNYU/"
    dir_info = pd.read_csv('metadata/dir_info.csv')

    try:
        metadata = pd.read_csv('metadata/{datachannel}.csv')
    except:
        metadata = pd.DataFrame(columns=['directory', 'filename', 'tuned', 'clear', 'healthy', 'type', 'x', 'y', 'z', 'd', 'bf', 'th', 'entrydate'])

    app = QApplication(sys.argv)
    
    if len(sys.argv) == 3:
        demo = AppDemo(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
        demo = AppDemo(sys.argv[1])
    else:
        demo = AppDemo()

    demo.show()
    demo.closeEvent = demo.closeEvent
    sys.exit(app.exec_())
