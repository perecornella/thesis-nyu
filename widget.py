import sys
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from utils import fra_dashboard, read_in_data, all_traces
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QRadioButton, QHBoxLayout,
                              QLineEdit, QLabel, QComboBox, QMessageBox, QButtonGroup, QGroupBox)

class Canvas(FigureCanvas):

    def __init__(self, parent, sample, filename):
        # Create the figure using the plot_dashboard function
        parent.fra_summaries, fig = fra_dashboard(sample, filename=filename)
        if parent.visualization == "traces":
            fig = all_traces(sample, filename=filename)
        super().__init__(fig)  # Pass the figure to the FigureCanvas constructor
        self.setParent(parent)  # Set the parent for the canvas

class AppDemo(QWidget):

    def __init__(self, input_directory=None, input_file=None):

        super().__init__()

        self.input_directory = input_directory
        self.input_file = input_file
        self.datachannel = "di0P"
        self.triggerchannel = "di4P"
        self.visualization = "fra"

        self.batch_size = 10
        self.set_directory()
        self.load_data_on_checkpoint(channel_change=False)
        self.create_widgets()
        self.set_layout()

    def set_directory(self):

        all_done = True
        for i, row in progress.iterrows():
            if row['end'] - row['checkpoint'] > 0:
                self.checkpoint = row['checkpoint']
                self.end = row['end']
                self.dir = row['name']
                all_done = False
                break
        if all_done:
            print(f"{datetime.now()} - All directories have been processed.")
            sys.exit(1)

        if self.input_directory is not None:
            try:
                row = progress[progress['name'] == self.input_directory].iloc[0]
                self.checkpoint = row['checkpoint']
                self.end = row['end']
                self.dir = row['name']
            except:
                print(f"{datetime.now()} - There's something wrong with the directory specified.")
                sys.exit(1)
        
        if self.end - self.checkpoint < self.batch_size:
            self.number_of_batches = 1
        else:
            self.number_of_batches = (self.end - self.checkpoint) // self.batch_size
        
        self.batch_pointer = 0
        self.counter = 0

    def load_data_on_checkpoint(self, channel_change = False):

        all_error = True

        while self.batch_pointer < self.number_of_batches:

            if self.counter == 0 or channel_change:
                
                if self.input_file is not None:
                    self.batch = [int(self.input_file[1:]), 1]
                else:
                    if self.end - self.checkpoint > 10:
                        self.batch = [self.checkpoint, self.checkpoint + 10]
                    else:
                        self.batch = [self.checkpoint, self.end]

                self.data, self.tonedata, self.error_files = read_in_data(root_dir + self.dir, self.batch, self.datachannel, self.triggerchannel)
                self.df = pd.merge(self.data, self.tonedata, how="left", on="toneid")
                
                if len(self.error_files) - (self.batch[1] - self.batch[0]) == 0:  # All files are error
                    self.batch_pointer += 1
                    self.checkpoint += self.batch[1] - self.batch[0]
                    progress.loc[progress['name'] == self.dir, 'checkpoint'] = self.checkpoint
                    break
                else:
                    self.counter = (self.batch[1] - self.batch[0]) - len(self.error_files)
                    channel_change = False
            
            else:
                if self.input_file is not None:
                    self.sample = self.df[self.df["toneid"].str.startswith(self.input_file)]
                    self.filename = f"{self.dir}{self.input_file} channel {self.datachannel}"
                    all_error = False
                else:
                    while self.checkpoint < self.end:
                        if f"A{self.checkpoint:03d}" not in self.error_files:
                            self.sample = self.df[self.df["toneid"].str.startswith(f"A{self.checkpoint:03d}")]
                            self.filename = f"{self.dir}A{self.checkpoint:03d} channel {self.datachannel}"
                            all_error = False
                            self.counter -= 1
                            break
                        else:
                            self.checkpoint += 1
                    
                    progress.loc[progress['name'] == self.dir, 'checkpoint'] = self.checkpoint
                    
                if not all_error:
                    break

        if all_error:
            print(f"{datetime.now()} - All the remaining non-error files in {self.dir} have been processed.")
            progress.loc[progress['name'] == self.dir, 'checkpoint'] = self.end
            progress.to_csv(f'metadata/{user}/progress.csv')
            metadata.to_csv(f'metadata/{user}/results.csv')
            sys.exit(1)

    def create_widgets(self):

        # FRA or Traces question for Visualization
        self.visualization_combobox = QComboBox()
        self.visualization_combobox.addItems(["FRA", "Traces"])
        self.visualization_combobox.currentIndexChanged.connect(self.on_vis_selected)
        self.visualization_layout = QHBoxLayout()
        self.visualization_layout.addWidget(self.visualization_combobox)
        self.visualization_box = QGroupBox("Select visualization")
        self.visualization_box.setLayout(self.visualization_layout)

        # Channel 0 or 2 question for Channel
        self.channel_combobox = QComboBox()
        self.channel_combobox.addItems(["Channel 0", "Channel 2"])
        self.channel_combobox.currentIndexChanged.connect(self.on_channel_selected)
        self.channel_layout = QHBoxLayout()
        self.channel_layout.addWidget(self.channel_combobox)
        self.channel_box = QGroupBox("Select channel")
        self.channel_box.setLayout(self.channel_layout)

        # Chart options layout
        self.vis_options_layout = QHBoxLayout()
        self.vis_options_layout.addWidget(self.visualization_box)
        self.vis_options_layout.addWidget(self.channel_box)

        # Tuned button
        self.tuned_button_group = QButtonGroup(self)
        self.tuned_button_layout = QHBoxLayout()
        self.tuned_button_yes = QRadioButton("Yes")
        self.tuned_button_no = QRadioButton("No")
        self.tuned_button_layout.addWidget(self.tuned_button_yes)
        self.tuned_button_layout.addWidget(self.tuned_button_no)
        self.tuned_button_group.addButton(self.tuned_button_yes)
        self.tuned_button_group.addButton(self.tuned_button_no)
        self.tuned_box = QGroupBox("Tuned Options")
        self.tuned_box.setLayout(self.tuned_button_layout)

        # Clear button
        self.clear_button_group = QButtonGroup(self)
        self.clear_layout = QHBoxLayout()
        self.clear_button_yes = QRadioButton("Yes")
        self.clear_button_no = QRadioButton("No")
        self.clear_layout.addWidget(self.clear_button_yes)
        self.clear_layout.addWidget(self.clear_button_no)
        self.clear_button_group.addButton(self.clear_button_yes)
        self.clear_button_group.addButton(self.clear_button_no)
        self.clear_box = QGroupBox("Clear Options")
        self.clear_box.setLayout(self.clear_layout)

        # Healthy button
        self.healthy_button_group = QButtonGroup(self)
        self.healthy_layout = QHBoxLayout()
        self.healthy_button_yes = QRadioButton("Yes")
        self.healthy_button_no = QRadioButton("No")
        self.healthy_layout.addWidget(self.healthy_button_yes)
        self.healthy_layout.addWidget(self.healthy_button_no)
        self.healthy_button_group.addButton(self.healthy_button_yes)
        self.healthy_button_group.addButton(self.healthy_button_no)
        self.healthy_box = QGroupBox("Healthy Options")
        self.healthy_box.setLayout(self.healthy_layout)

        # Intra/Extra question for Type
        self.type_combobox = QComboBox()
        self.type_combobox.addItems(["Intra", "Extra"])
        self.type_layout = QHBoxLayout()
        self.type_layout.addWidget(self.type_combobox)
        self.type_box = QGroupBox("Type Options")
        self.type_box.setLayout(self.type_layout)

        # Form layout
        self.form_layout = QHBoxLayout()
        self.form_layout.addWidget(self.tuned_box)
        self.form_layout.addWidget(self.clear_box)
        self.form_layout.addWidget(self.healthy_box)
        self.form_layout.addWidget(self.type_box)

        # Coordinates input for x, y, z
        self.x0_input = QLineEdit()
        self.xf_input = QLineEdit()
        self.y_input = QLineEdit()
        self.z_input = QLineEdit()
        self.coord_layout = QHBoxLayout()
        self.coord_layout.addWidget(QLabel("Coordinates"))
        self.coord_layout.addWidget(QLabel("x0:"))
        self.coord_layout.addWidget(self.x0_input)
        self.coord_layout.addWidget(QLabel("xf:"))
        self.coord_layout.addWidget(self.xf_input)
        self.coord_layout.addWidget(QLabel("y:"))
        self.coord_layout.addWidget(self.y_input)
        self.coord_layout.addWidget(QLabel("z:"))
        self.coord_layout.addWidget(self.z_input)

        # Add Back, Next & Send buttons in separate boxes
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.on_send_clicked)
        self.send_box = QGroupBox()
        self.send_layout = QVBoxLayout()
        self.send_layout.addWidget(self.send_button)
        self.send_box.setLayout(self.send_layout)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.on_back_clicked)
        self.back_box = QGroupBox()
        self.back_layout = QVBoxLayout()
        self.back_layout.addWidget(self.back_button)
        self.back_box.setLayout(self.back_layout)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.on_next_clicked)
        self.next_box = QGroupBox()
        self.next_layout = QVBoxLayout()
        self.next_layout.addWidget(self.next_button)
        self.next_box.setLayout(self.next_layout)

        # Combine all button boxes in a horizontal layout
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.send_box)
        self.button_layout.addWidget(self.back_box)
        self.button_layout.addWidget(self.next_box)

    def set_layout(self):

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.vis_options_layout)
        self.chart = Canvas(self, self.sample, self.filename)
        self.layout.addWidget(self.chart)
        self.layout.addLayout(self.form_layout)
        self.layout.addLayout(self.coord_layout)
        self.layout.addLayout(self.button_layout)
    
        self.setLayout(self.layout)

    # Action functions

    def on_send_clicked(self):

        print(f"{datetime.now()} - send button clicked.")
        if self.input_file is not None:
            print(f"{datetime.now()} - Warning. Send on filename inserted.")
            QMessageBox.warning(self, "Warning", "You inserted a filename; only read is allowed.")

        else:
            tuned = "Yes" if self.tuned_button_yes.isChecked() else "No"
            clear = "Yes" if self.clear_button_yes.isChecked() else "No"
            healthy = "Yes" if self.healthy_button_yes.isChecked() else "No"
            selected_type = self.type_combobox.currentText()
            x0 = float(self.x0_input.text()) if self.x0_input.text() else None
            xf = float(self.xf_input.text()) if self.xf_input.text() else None
            y = float(self.y_input.text()) if self.y_input.text() else None
            z = float(self.z_input.text()) if self.z_input.text() else None

            confirmation_message = f"Tuned: {tuned}\nClear: {clear}\nHealthy: {healthy}\nType: {selected_type}\nCoordinates: x={x0}, x={xf}, y={y}, z={z}"
            question = QMessageBox.question(self, 'Confirm your entries', f"Are you sure you want to submit the following values?\n\n{confirmation_message}", 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if question == QMessageBox.Yes:
                new_row = {
                    'directory': self.dir,
                    'filename': f"A{self.checkpoint:03d}",
                    'channel': self.datachannel,
                    'tuned': tuned,
                    'clear': clear,
                    'healthy': healthy,
                    'type': selected_type,
                    'x': x0,
                    'xf': xf,
                    'y': y,
                    'z': z,
                    'entrydate': datetime.now()
                }

                existing_entry = metadata[
                (metadata['directory'] == self.dir) &
                (metadata['filename'] == f"A{self.checkpoint:03d}") &
                (metadata['channel'] == self.datachannel)
]
                if existing_entry.empty:
                    metadata.loc[len(metadata)] = new_row
                    print(f"{datetime.now()} - successful submission.")
                else:
                    question = QMessageBox.question(
                        self, 
                        "Confirmation",
                        "You already submitted a response for this data channel, do you want to overwrite?",
                        QMessageBox.Yes | QMessageBox.No,  
                        QMessageBox.No  
                    )
                    if question == QMessageBox.Yes:
                        index_to_update = existing_entry.index[0]
                        metadata.loc[index_to_update] = new_row
                        print(f"{datetime.now()} - submission has been overwritten.")
            else:
                print(f"{datetime.now()} - submission cancelled.")

    def on_next_clicked(self):

        print(f"{datetime.now()} - next button action clicked.")

        if self.input_file is not None:
            print(f"{datetime.now()} - Warning. Send on filename inserted.")
            QMessageBox.warning(self, "Warning", "You inserted a filename; only read is allowed.")

        else:
            question = QMessageBox.question(
                self, 
                "Confirmation",
                "Do you want to pass to the next file?",
                QMessageBox.Yes | QMessageBox.No,  
                QMessageBox.No  
            )
            if question == QMessageBox.Yes:
                self.checkpoint += 1
                print(f"{datetime.now()} - changing to file {self.dir}{f"A{self.checkpoint:03d}"}.")
                self.load_data_on_checkpoint(channel_change=False)
                self.update_dashboard()
            else:
                print(f"{datetime.now()} - next button action cancelled.")

    def on_back_clicked(self):

        print(f"{datetime.now()} - back button action clicked.")

        if self.input_file is not None:
            print(f"{datetime.now()} - Warning. Send on filename inserted.")
            QMessageBox.warning(self, "Warning", "You inserted a filename; only read is allowed.")

        else:
            question = QMessageBox.question(
                self, 
                "Confirmation",
                "Do you want to go back to the previous file?",
                QMessageBox.Yes | QMessageBox.No,  
                QMessageBox.No  
            )
            if question == QMessageBox.Yes:

                if self.checkpoint - 1 >= self.batch[0]:
                    self.checkpoint -= 1
                    print(f"{datetime.now()} - changing to file {self.dir}/{f"A{self.checkpoint:03d}"}.")
                    self.load_data_on_checkpoint(channel_change=False)
                    self.update_dashboard()
                else:
                    QMessageBox.warning(self, "Warning", "There is no previous file.")
                    print(f"{datetime.now()} - there is no previous file.")
            else:
                print(f"{datetime.now()} - back button action cancelled.")

    def on_vis_selected(self, index):
        if self.visualization_combobox.itemText(index) == "FRA":
            self.visualization = "fra"
        elif self.visualization_combobox.itemText(index) == "Traces":
            self.visualization = "traces"

        self.update_dashboard()

    def on_channel_selected(self, index):
        if self.channel_combobox.itemText(index) == "Channel 0":
            self.datachannel = "di0P"
        elif self.channel_combobox.itemText(index) == "Channel 2":
            self.datachannel = "di2P"

        self.load_data_on_checkpoint(channel_change=True)
        self.update_dashboard()

    def update_dashboard(self):
        plt.close(self.chart.figure)
        self.layout.removeWidget(self.chart)
        self.chart.deleteLater()
        self.chart = Canvas(self, self.sample, self.filename)
        self.layout.insertWidget(1, self.chart)

    def closeEvent(self, event):
        print(f"{datetime.now()} - exit button clicked.")
        question = QMessageBox.question(self, 'Confirm Exit',
                                    "Do you want to save changes before exiting?",
                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
                                    QMessageBox.Yes)

        if question == QMessageBox.Yes:
            print(f"{datetime.now()} - saving the progress...")
            progress.to_csv(f'metadata/{user}/progress.csv')
            metadata.to_csv(f'metadata/{user}/results.csv')
            event.accept() 
        elif question == QMessageBox.No:
            print(f"{datetime.now()} - progress not saved.")
            event.accept()
        else:
            print(f"{datetime.now()} - exit cancelled.")
            event.ignore()


if __name__ == "__main__":
    
    # Define the data and parameters
    user = sys.argv[1]
    if user == "perecornella":
        root_dir = "/Users/perecornella/Library/CloudStorage/GoogleDrive-pere.cornella@estudiantat.upc.edu/My Drive/ReyesLabNYU/"
    elif user == "ar65":
        root_dir = "/Users/ar65/Library/CloudStorage/GoogleDrive-ar65@nyu.edu/My Drive/ReyesLabNYU/"
    else:
        root_dir = "toy_dataset/"

    progress = pd.read_csv(f'metadata/{user}/progress.csv')
    try:
        metadata = pd.read_csv(f'metadata/{user}/results.csv')
    except:
        metadata = pd.DataFrame(columns=['directory', 'filename', 'channel',
                                         'tuned', 'clear', 'healthy','type',
                                         'x', 'xf', 'y', 'z',
                                         'entrydate'])

    app = QApplication(sys.argv)
    
    if len(sys.argv) == 4:
        demo = AppDemo(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3:
        demo = AppDemo(sys.argv[2])
    else:
        demo = AppDemo()

    demo.show()
    demo.closeEvent = demo.closeEvent
    sys.exit(app.exec_())
