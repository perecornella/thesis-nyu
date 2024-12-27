import sys
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from utils import fra_dashboard, read_in_data, plot_traces, get_recording_activity, get_files
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QRadioButton, QHBoxLayout,
                              QLineEdit, QLabel, QComboBox, QMessageBox, QButtonGroup, QGroupBox)

class Canvas(FigureCanvas):

    def __init__(self, parent, sample, filename):
        # Create the figure using the plot_dashboard function
        matrix, activity_frequency, activity_level, spls, freq = get_recording_activity(sample)
        parent.bf_options_list = [f"{round(f/1000,1)} kHz" for f in freq]
        parent.level_options_list = [f"{round(s,0)} dB" for s in spls]

        if parent.visualization == "activity plots":
            self.fig = fra_dashboard(matrix, filename, activity_frequency, activity_level, spls, freq)

        if parent.visualization == "all traces":
            self.fig = plot_traces(sample, range(len(freq)), filename=filename)
    
        if parent.visualization == "highest activity traces":
            bf_index = np.argmax(activity_frequency)
            self.fig = plot_traces(sample, range(bf_index-1,bf_index+2), filename=filename)

        super().__init__(self.fig)  # Pass the figure to the FigureCanvas constructor
        self.setParent(parent)  # Set the parent for the canvas

class AppDemo(QWidget):

    def __init__(self, input_directory=None, input_file=None):

        super().__init__()

        self.input_directory = input_directory
        self.input_file = input_file
        self.datachannel = "di0P"
        self.triggerchannel = "di4P"
        self.visualization = "activity plots"

        self.batch_size = 10
        self.set_directory()
        self.load_data_on_checkpoint()
        self.chart = Canvas(self, self.sample, self.filename)
        self.create_widgets()
        self.set_layout()

    def set_directory(self):

        if self.input_directory is not None:
            self.dir = self.input_directory
        else:
            for i, row in progress.iterrows():
                self.non_checked_files = get_files(row['non checked files'])
                if len(self.non_checked_files) > 0:
                    self.dir = row['name']
                    break
        
        dir_info = progress[progress['name'] == self.dir].iloc[0]
        if dir_info.empty:
            print(f"{datetime.now()} - Error: There's something wrong with the directory {self.input_directory}.")
            sys.exit(1)

        self.non_checked_files = get_files(dir_info['non checked files'])
        self.checked_files = get_files(dir_info['checked files'])
        self.error_files = get_files(dir_info['error files'])

        filtered_files = [file for file in list(self.non_checked_files) + list(self.checked_files) \
                          if file not in self.error_files]

        self.checkpoint = self.input_file if self.input_file is not None else self.non_checked_files[0]
        if self.checkpoint not in filtered_files:
            print(f"{datetime.now()} - Error: There's something wrong with the file {self.input_directory}{self.checkpoint}.")
            self.checkpoint = self.non_checked_files[0]
            sys.exit(1)
        else:
            print(f"{datetime.now()} - Message: showing file {self.dir}{self.checkpoint}.")
        

    def load_data_on_checkpoint(self):
        
        all_error = True
        while all_error:
            self.sample, error_files = read_in_data(root_dir + self.dir, [self.checkpoint], self.datachannel, self.triggerchannel)

            self.existing_entry = metadata[
            (metadata['directory'] == self.dir) &
            (metadata['filename'] == self.checkpoint) &
            (metadata['channel'] == self.datachannel)
            ]

            checked_message = "Checked" if not self.existing_entry.empty else "Not Checked"
            if len(error_files) == 0:
                self.filename = f"{self.dir}{self.checkpoint} channel {self.datachannel} | {checked_message}"
                all_error = False
            elif self.checkpoint not in self.error_files:
                    self.error_files.add(*error_files)
                    progress.loc[progress['name'] == self.dir, 'error files'] = [self.error_files]

        if all_error:

            question = QMessageBox.warning(self, "Message", 
                                        f"All the remaining files in {self.dir} are error files.\n\
                                          The program will close. Do you want to save your answers?",
                                        QMessageBox.Yes | QMessageBox.No, 
                                        QMessageBox.Yes)

            if question == QMessageBox.Yes:
                print(f"{datetime.now()} - Action: yes button clicked.")
                print(f"{datetime.now()} - Message: answers saved in metadata.")
                progress.to_csv(progress_path)
                metadata.to_csv(metadata_path)
                sys.exit(1)  

            else:
                print(f"{datetime.now()} - Action: no button clicked.")
                print(f"{datetime.now()} - Message: answers discarded .")
                sys.exit(1)

    def create_widgets(self):

        # FRA or Traces question for Visualization
        self.visualization_combobox = QComboBox()
        self.visualization_combobox.addItems(["Activity plots", "All traces", "Highest activity traces"])
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
        self.exemplar_button_group = QButtonGroup(self)
        self.exemplar_layout = QHBoxLayout()
        self.exemplar_button_yes = QRadioButton("Yes")
        self.exemplar_button_no = QRadioButton("No")
        self.exemplar_layout.addWidget(self.exemplar_button_yes)
        self.exemplar_layout.addWidget(self.exemplar_button_no)
        self.exemplar_button_group.addButton(self.exemplar_button_yes)
        self.exemplar_button_group.addButton(self.exemplar_button_no)
        self.exemplar_box = QGroupBox("Exemplar Options")
        self.exemplar_box.setLayout(self.exemplar_layout)

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
        self.type_combobox.addItems(["Extracellular", "Intracellular"])
        self.type_layout = QHBoxLayout()
        self.type_layout.addWidget(self.type_combobox)
        self.type_box = QGroupBox("Type Options")
        self.type_box.setLayout(self.type_layout)
        
        # Best frequency option
        self.bf_combobox = QComboBox()
        self.bf_combobox.addItems(self.bf_options_list)
        self.bf_layout = QHBoxLayout()
        self.bf_layout.addWidget(self.bf_combobox)
        self.bf_box = QGroupBox("Best frequency Options")
        self.bf_box.setLayout(self.bf_layout)

        # Threshold level option
        self.level_combobox = QComboBox()
        self.level_combobox.addItems(self.level_options_list)
        self.level_layout = QHBoxLayout()
        self.level_layout.addWidget(self.level_combobox)
        self.level_box = QGroupBox("Threshold level Options")
        self.level_box.setLayout(self.level_layout)

        # Form layout
        self.form_layout = QHBoxLayout()
        self.form_layout.addWidget(self.tuned_box)
        self.form_layout.addWidget(self.exemplar_box)
        self.form_layout.addWidget(self.healthy_box)
        self.form_layout.addWidget(self.type_box)
        self.form_layout.addWidget(self.bf_box)
        self.form_layout.addWidget(self.level_box)

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
        self.layout.addWidget(self.chart)
        self.layout.addLayout(self.form_layout)
        self.layout.addLayout(self.coord_layout)
        self.layout.addLayout(self.button_layout)
    
        self.setLayout(self.layout)

    # Action functions

    def on_send_clicked(self):

        print(f"{datetime.now()} - Action: send button clicked.")

        tuned = "Yes" if self.tuned_button_yes.isChecked() else "No" if self.tuned_button_no.isChecked() else None
        exemplar = "Yes" if self.exemplar_button_yes.isChecked() else "No" if self.exemplar_button_no.isChecked() else None
        healthy = "Yes" if self.healthy_button_yes.isChecked() else "No" if self.healthy_button_no.isChecked() else None
        selected_type = self.type_combobox.currentText()
        best_frequency = float(self.bf_combobox.currentText()[:-4])
        level_threshold = float(self.level_combobox.currentText()[:-3])
        x0 = float(self.x0_input.text()) if self.x0_input.text() else None
        xf = float(self.xf_input.text()) if self.xf_input.text() else None
        y = float(self.y_input.text()) if self.y_input.text() else None
        z = float(self.z_input.text()) if self.z_input.text() else None

        confirmation_message = f"\
            Tuned: {tuned}\n\
            Clear: {exemplar}\n\
            Healthy: {healthy}\n\
            Type: {selected_type}\n\
            Best frequency :{best_frequency}\n\
            Level threshold: {level_threshold}\n\
            Coordinates: x={x0}, x={xf}, y={y}, z={z}"
        question = QMessageBox.question(self, 
                                        'Confirm your entries',
                                        f"Are you sure you want to submit the following values for {self.filename}?\n\n{confirmation_message}", 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if question == QMessageBox.Yes:
            print(f"{datetime.now()} - Action: yes button clicked.")
            new_row = {
                'directory': self.dir,
                'filename': self.checkpoint,
                'channel': self.datachannel,
                'tuned': tuned,
                'exemplar': exemplar,
                'healthy': healthy,
                'type': selected_type,
                'best frequency': best_frequency,
                'level threshold': level_threshold,
                'x': x0,
                'xf': xf,
                'y': y,
                'z': z,
                'entrydate': datetime.now()
            }

            if self.existing_entry.empty:
                metadata.loc[len(metadata)] = new_row
                print(f"{datetime.now()} - Message: successful submission for file {self.dir}{self.filename}/{self.datachannel}.")
            else:
                print(f"{datetime.now()} - Message: there is an existing submission for file {self.dir}{self.filename}/{self.datachannel}.")
                question = QMessageBox.question(
                    self, 
                    "Confirmation",
                    "You already submitted a response for this data channel, do you want to overwrite?",
                    QMessageBox.Yes | QMessageBox.No,  
                    QMessageBox.No  
                )
                if question == QMessageBox.Yes:
                    print(f"{datetime.now()} - Action: yes button clicked.")
                    index_to_update = self.existing_entry.index[0]
                    metadata.loc[index_to_update] = new_row
                    print(f"{datetime.now()} - Message: submission overwritten.")
                else: 
                    print(f"{datetime.now()} - Action: button clicked.")
                    print(f"{datetime.now()} - Message: decided not to overwrite.")



            if self.checkpoint in self.non_checked_files:
                self.non_checked_files.remove(self.checkpoint)
            if self.checkpoint not in self.checked_files:
                self.checked_files.append(self.checkpoint)
            dir_index = progress[progress['name'] == self.dir].index
            progress.at[dir_index[0], 'non checked files'] = self.non_checked_files
            progress.at[dir_index[0], 'checked files'] = self.checked_files

        else:
            print(f"{datetime.now()} - Action: other button clicked.")

    def on_next_clicked(self):
            
        print(f"{datetime.now()} - Action: next button clicked.")

        filtered_files = [
            file for file in sorted(list(self.checked_files) + list(self.non_checked_files))
            if file not in self.error_files
        ]
        checkpoint_index = filtered_files.index(self.checkpoint)
    
        if checkpoint_index + 1 < len(filtered_files):
            self.checkpoint = filtered_files[checkpoint_index + 1]
            print(f"{datetime.now()} - showing file {self.dir}{self.checkpoint}.")
            self.load_data_on_checkpoint()
            self.update_dashboard()
        else:
            print(f"{datetime.now()} - Message: {self.dir}{self.checkpoint} is the last file.")
            QMessageBox.warning(self, "Message", "You reached the last file in the directory.")


    def on_back_clicked(self):

        print(f"{datetime.now()} - Action: back button clicked.")

        filtered_files = [
            file for file in sorted(list(self.checked_files) + list(self.non_checked_files))
            if file not in self.error_files
        ]
        checkpoint_index = filtered_files.index(self.checkpoint)

        if checkpoint_index - 1 >= 0:
            self.checkpoint = filtered_files[checkpoint_index - 1]
            print(f"{datetime.now()} - Message: showing file {self.dir}{self.checkpoint}.")
            self.load_data_on_checkpoint()
            self.update_dashboard()
        else:
            print(f"{datetime.now()} - {self.dir}{self.checkpoint} is the first file.")
            QMessageBox.warning(self, "Message", "You reached the first file in the directory.")


    def on_vis_selected(self, index):
        if self.visualization_combobox.itemText(index) == "Activity plots":
            self.visualization = "activity plots"
        elif self.visualization_combobox.itemText(index) == "All traces":
            self.visualization = "all traces"
        elif self.visualization_combobox.itemText(index) == "Highest activity traces":
            self.visualization = "highest activity traces"

        self.update_dashboard()

    def on_channel_selected(self, index):
        if self.channel_combobox.itemText(index) == "Channel 0":
            self.datachannel = "di0P"
        elif self.channel_combobox.itemText(index) == "Channel 2":
            self.datachannel = "di2P"
        self.load_data_on_checkpoint()
        self.update_dashboard()

    def update_dashboard(self):
        plt.close(self.chart.figure)
        self.layout.removeWidget(self.chart)
        self.chart.deleteLater()
        self.chart = Canvas(self, self.sample, self.filename)
        self.layout.insertWidget(1, self.chart)

    def closeEvent(self, event):
        print(f"{datetime.now()} - Action: exit button clicked.")
        question = QMessageBox.question(self, 'Confirm Exit',
                                    "Do you want to save changes before exiting?",
                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
                                    QMessageBox.Yes)

        if question == QMessageBox.Yes:
            print(f"{datetime.now()} - Action: yes button clicked.")
            print(f"{datetime.now()} - Message: saving the progress...")
            progress.to_csv(progress_path)
            metadata.to_csv(metadata_path)
            event.accept() 
        elif question == QMessageBox.No:
            print(f"{datetime.now()} - Action: no button clicked.")
            print(f"{datetime.now()} - Message: progress not saved.")
            event.accept()
        else:
            print(f"{datetime.now()} - Action: cancel button clicked.")
            print(f"{datetime.now()} - Message: exit cancelled.")
            event.ignore()


if __name__ == "__main__":

    user = sys.argv[1]
    version = sys.argv[2]

    if user == "perecornella":
        root_dir = "/Users/perecornella/Library/CloudStorage/GoogleDrive-pere.cornella@estudiantat.upc.edu/My Drive/ReyesLabNYU/"
    elif user == "ar65":
        root_dir = "/Users/ar65/Library/CloudStorage/GoogleDrive-ar65@nyu.edu/My Drive/ReyesLabNYU/"
    else:
        root_dir = "toy_dataset/"

    progress_path = f'metadata/{user}/{version}/progress.csv'
    metadata_path = f'metadata/{user}/{version}/results.csv'

    progress = pd.read_csv(progress_path)
    try:
        metadata = pd.read_csv(metadata_path)
    except:
        metadata = pd.DataFrame(columns=['directory', 'filename', 'channel',
                                         'tuned', 'exemplar', 'healthy','type',
                                         'best frequency', 'level threshold',
                                         'x', 'xf', 'y', 'z',
                                         'entrydate'])

    app = QApplication(sys.argv)
    
    if len(sys.argv) > 4:
        demo = AppDemo(sys.argv[3], sys.argv[4])
    elif len(sys.argv) > 3:
        demo = AppDemo(sys.argv[3])
    else:
        demo = AppDemo()

    demo.show()
    demo.closeEvent = demo.closeEvent
    sys.exit(app.exec_())
