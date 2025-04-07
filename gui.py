import sys
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from utils import fra_dashboard, read_rs, plot_traces, get_rs_activity, get_filenames
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QRadioButton,
                             QHBoxLayout, QLineEdit, QLabel, QComboBox, QMessageBox,
                             QButtonGroup, QGroupBox, QShortcut)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt

class Canvas(FigureCanvas):

    def __init__(self, parent):

        if len(parent.rs) != 0:
            # Create the figure using the plot_dashboard function
            matrix, activity_frequency, activity_level, spls, freq = get_rs_activity(parent.rs)
            parent.bf_options_list = [f"{round(f/1000,1)} kHz" for f in freq]
            parent.level_options_list = [f"{round(s,0)} dB" for s in spls]

            if parent.visualization == "all traces":
                self.fig = plot_traces(parent.rs, range(len(freq)), filename=parent.chart_title)
        
            elif parent.visualization == "highest activity traces":
                bf_index = np.argmax(activity_frequency)
                min_index = max(0, bf_index - 1)
                max_index = min(len(freq), bf_index + 2)
                self.fig = plot_traces(parent.rs, range(min_index, max_index), filename=parent.chart_title)

            elif parent.visualization == "activity plots":
                self.fig = fra_dashboard(matrix, parent.chart_title, activity_frequency, activity_level, spls, freq)
        else:
            self.fig = plt.figure(figsize=(16,8))
            parent.bf_options_list = []
            parent.level_options_list = []

        super().__init__(self.fig)  # Pass the figure to the FigureCanvas constructor
        self.setParent(parent)  # Set the parent for the canvas

class AppDemo(QWidget):

    def __init__(self, input_directory=None, input_file=None):

        super().__init__()

        self.setFocusPolicy(Qt.StrongFocus)

        self.datachannel = "di0P"
        self.triggerchannel = "di4P"
        self.visualization = "all traces"
        self.set_first_directory_and_checkpoint()
        self.update_files_list()
        self.update_directories_list()
        self.load_data_on_checkpoint()
        self.chart = Canvas(self)
        self.create_widgets()
        self.set_layout()
        self.update_widgets()
        self.define_shortcuts()

    def define_shortcuts(self):
        next_shortcut = QShortcut(QKeySequence(Qt.ALT + Qt.Key_M), self)  
        next_shortcut.setContext(Qt.ApplicationShortcut)
        next_shortcut.activated.connect(self.on_next_clicked)

        back_shortcut = QShortcut(QKeySequence(Qt.ALT + Qt.Key_N), self)  
        back_shortcut.setContext(Qt.ApplicationShortcut)
        back_shortcut.activated.connect(self.on_back_clicked)

        send_shortcut = QShortcut(QKeySequence(Qt.ALT + Qt.Key_Return), self) 
        send_shortcut.setContext(Qt.ApplicationShortcut)
        send_shortcut.activated.connect(self.on_send_clicked)

        discard_shortcut = QShortcut(QKeySequence(Qt.ALT + Qt.Key_Backspace), self) 
        discard_shortcut.setContext(Qt.ApplicationShortcut)
        discard_shortcut.activated.connect(self.on_discard_clicked)

    def set_first_directory_and_checkpoint(self):

        all_checked = True
        for i, row in progress.iterrows():                
            self.non_checked_files = get_filenames(row['non checked files'])
            self.checked_files = get_filenames(row['checked files'])
            if len(self.non_checked_files) > 0:
                self.dir = row['directory']
                all_checked = False 
                break
            elif len(self.checked_files) > 0:
                aux_row = row
        if all_checked:
            print(f"{datetime.now()} - Congrats! You annotated all the files in your dataset.")
            self.dir = aux_row['directory']

        dir_info = progress[progress['directory'] == self.dir].iloc[0]
        self.non_checked_files = get_filenames(dir_info['non checked files'])
        self.checked_files = get_filenames(dir_info['checked files'])
        self.error_files = get_filenames(dir_info['error files'])

        if len(self.non_checked_files) > 0:
            self.checkpoint = self.non_checked_files[0]
        elif len(self.checked_files) > 0:
            self.checkpoint = self.checked_files[0]
        else:
            print(f"{datetime.now()} - Warning: the directory only has error files.")
            QMessageBox.warning(self, "Message", "The directory only has error files.")

    def update_directories_list(self):

        self.directories_with_tags_list = sorted([
            f"{row['directory']} ({len(get_filenames(row['checked files']))}/{len(get_filenames(row['non checked files']))+\
                                                                         len(get_filenames(row['checked files']))})"
            for i, row in progress.iterrows()
        ])

    def update_files_list(self):
        self.files_list = sorted([
            file for file in list(self.non_checked_files) + list(self.checked_files)
            if not any(error_file.startswith(file) for error_file in self.error_files)
        ])
        
        always_full_columns = ['directory', 'filename', 'channel', 'entrydate', 'version']

        self.files_with_tags_list = sorted([
            f"{file}"
            + (" *" if any(
                entry.drop(columns=(['note'] + always_full_columns)).notna().sum().any()
                for entry in [annotations[
                    (annotations['directory'] == self.dir) &
                    (annotations['filename'] == file) &
                    (annotations['channel'] == "di0P")
                ]]
            ) else "")
            + (" **" if any(
                entry.drop(columns=(['note'] + always_full_columns)).notna().sum().any()
                for entry in [annotations[
                    (annotations['directory'] == self.dir) &
                    (annotations['filename'] == file) &
                    (annotations['channel'] == "di2P")
                ]]
            ) else "")
            + (" (note)" if any(
                entry['note'].notna().any()
                for entry in [annotations[
                    (annotations['directory'] == self.dir) &
                    (annotations['filename'] == file) &
                    ((annotations['channel'] == "di0P") | (annotations['channel'] == "di2P"))
                ]]
            ) else "")
            for file in list(self.non_checked_files) + list(self.checked_files)
            if not any(error_file.startswith(file) for error_file in self.error_files)
        ])

        # self.files_with_tags_list = sorted([
        #     f"{file} (checked)" if file in self.checked_files else file
        #     for file in list(self.non_checked_files) + list(self.checked_files)
        #     if not any(error_file.startswith(file) for error_file in self.error_files)
        # ])

    def load_data_on_checkpoint(self):

        while True:
            self.rs, error_files = read_rs(root_dir + self.dir,
                                               [self.checkpoint],
                                               self.datachannel,
                                               self.triggerchannel)

            self.existing_entry = annotations [
                (annotations['directory'] == self.dir) &
                (annotations['filename'] == self.checkpoint) &
                (annotations['channel'] == self.datachannel)
            ]

            if len(error_files) == 0:
                print(f"{datetime.now()} - Message: sucessfully showing file {self.dir}{self.checkpoint}.")
                self.chart_title = f"File {self.dir}{self.checkpoint} showing channel {self.datachannel}, {"Checked" if not self.existing_entry.empty else "Not checked"}"
                break

            else:
                print(f"{datetime.now()} - Message: {self.dir}{self.checkpoint} is an error file, skipping to the next one.")
                
                dir_index = progress[progress['directory'] == self.dir].index
                self.non_checked_files.remove(self.checkpoint)
                self.error_files.append(*error_files)
                progress.at[dir_index[0], 'error files'] = self.error_files
                progress.at[dir_index[0], 'non checked files'] = self.non_checked_files
                progress.to_csv(progress_path, index=False)
                checkpoint_index = self.files_list.index(self.checkpoint)
                self.update_files_list()
                if checkpoint_index < len(self.files_list):
                    self.checkpoint = self.files_list[checkpoint_index]
                elif len(self.non_checked_files) > 0:
                    self.checkpoint = self.non_checked_files[0]
                elif len(self.checked_files) > 0:
                    self.checkpoint = self.checked_files[0]
                else:
                    print(f"{datetime.now()} - Warning: the directory only has error files.")
                    QMessageBox.warning(self, "Message", "The directory only has error files.")
                    break

                aux_checkpoint = self.checkpoint
                self.update_file_combobox()
                self.file_combobox.setCurrentText(next(item for item in self.files_with_tags_list if item.startswith(aux_checkpoint)))

    def create_widgets(self):

        # Directory options
        self.directory_combobox = QComboBox()
        self.directory_combobox.addItems(self.directories_with_tags_list)
        self.directory_combobox.currentIndexChanged.connect(self.on_directory_selected)
        self.directory_layout = QHBoxLayout()
        self.directory_layout.addWidget(self.directory_combobox)
        self.directory_box = QGroupBox("Select directory")
        self.directory_box.setLayout(self.directory_layout)

        # File options
        self.file_combobox = QComboBox()
        self.file_combobox.addItems(self.files_with_tags_list)
        self.file_combobox.currentIndexChanged.connect(self.on_file_selected)
        self.file_layout = QHBoxLayout()
        self.file_layout.addWidget(self.file_combobox)
        self.file_box = QGroupBox("Select file")
        self.file_box.setLayout(self.file_layout)

        # Visualization options
        self.visualization_combobox = QComboBox()
        self.visualization_combobox.addItems(["All traces", "Highest activity traces", "Activity plots"])
        self.visualization_combobox.currentIndexChanged.connect(self.on_vis_selected)
        self.visualization_layout = QHBoxLayout()
        self.visualization_layout.addWidget(self.visualization_combobox)
        self.visualization_box = QGroupBox("Select visualization")
        self.visualization_box.setLayout(self.visualization_layout)

        # Channel options
        self.channel_combobox = QComboBox()
        self.channel_combobox.addItems(["Channel 0", "Channel 2", "Channel 1", "Channel 3", "Channel 4"])
        self.channel_combobox.currentIndexChanged.connect(self.on_channel_selected)
        self.channel_layout = QHBoxLayout()
        self.channel_layout.addWidget(self.channel_combobox)
        self.channel_box = QGroupBox("Select channel")
        self.channel_box.setLayout(self.channel_layout)

        # Chart options layout
        self.vis_options_layout = QHBoxLayout()
        self.vis_options_layout.addWidget(self.directory_box)
        self.vis_options_layout.addWidget(self.file_box)
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
        self.type_combobox.addItems(["-", "Cell-attached", "Extracellular", "Whole-cell"])
        self.type_layout = QHBoxLayout()
        self.type_layout.addWidget(self.type_combobox)
        self.type_box = QGroupBox("Type Options")
        self.type_box.setLayout(self.type_layout)
        
        # Best frequency option
        self.bf_combobox = QComboBox()
        self.bf_combobox.addItems(["-"] + self.bf_options_list)
        self.bf_layout = QHBoxLayout()
        self.bf_layout.addWidget(self.bf_combobox)
        self.bf_box = QGroupBox("Best frequency Options")
        self.bf_box.setLayout(self.bf_layout)

        # Threshold level option
        self.level_combobox = QComboBox()
        self.level_combobox.addItems(["-"] + self.level_options_list)
        self.level_layout = QHBoxLayout()
        self.level_layout.addWidget(self.level_combobox)
        self.level_box = QGroupBox("Threshold level Options")
        self.level_box.setLayout(self.level_layout)

        # Notes box
        self.notes_layout = QHBoxLayout()
        self.note = QLineEdit()
        self.notes_layout.addWidget(self.note)
        self.notes_box = QGroupBox("Note")
        self.notes_box.setLayout(self.notes_layout)
        # self.note.setText(self.existing_entry['note'].iloc[0] if not self.existing_entry.empty else "")

        # Form layout
        self.form_c1_layout = QVBoxLayout()
        self.form_c1_layout.addWidget(self.healthy_box)
        self.form_c1_layout.addWidget(self.type_box)
        self.form_c2_layout = QVBoxLayout()
        self.form_c2_layout.addWidget(self.tuned_box)
        self.form_c2_layout.addWidget(self.clear_box)
        self.form_c3_layout = QVBoxLayout()
        self.form_c3_layout.addWidget(self.bf_box)
        self.form_c3_layout.addWidget(self.level_box)

        # Coordinates input for x, y, z
        self.coord_box = QGroupBox("Coordinates")
        self.x0_input = QLineEdit()
        self.xf_input = QLineEdit()
        self.y_input = QLineEdit()
        self.z_input = QLineEdit()
        self.coord_layout = QHBoxLayout()
        self.coord_layout.addWidget(QLabel("x0:"))
        self.coord_layout.addWidget(self.x0_input)
        self.coord_layout.addWidget(QLabel("xf:"))
        self.coord_layout.addWidget(self.xf_input)
        self.coord_layout.addWidget(QLabel("y:"))
        self.coord_layout.addWidget(self.y_input)
        self.coord_layout.addWidget(QLabel("z:"))
        self.coord_layout.addWidget(self.z_input)
        self.coord_box.setLayout(self.coord_layout)

        # Add Back, Next, Discard & Send buttons in separate boxes
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.on_send_clicked)
        self.send_box = QGroupBox()
        self.send_layout = QVBoxLayout()
        self.send_layout.addWidget(self.send_button)
        self.send_box.setLayout(self.send_layout)

        self.discard_button = QPushButton("Discard")
        self.discard_button.clicked.connect(self.on_discard_clicked)
        self.discard_box = QGroupBox()
        self.discard_layout = QVBoxLayout()
        self.discard_layout.addWidget(self.discard_button)
        self.discard_box.setLayout(self.discard_layout)

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
        default_button_style = """
            QPushButton {
                background-color: #F5F5F5; /* Near white */
                color: black;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                min-width: 70px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #DADADA; /* Slightly darker on hover */
            }
        """

        send_button_style = default_button_style + """
            QPushButton {
                background-color: #C0D8EE; /* Softer pale blue */
            }
            QPushButton:hover {
                background-color: #A8C7E2;
            }
        """

        # Apply styles
        self.send_button.setStyleSheet(send_button_style)   
        self.discard_button.setStyleSheet(default_button_style)  
        self.back_button.setStyleSheet(default_button_style)  
        self.next_button.setStyleSheet(default_button_style)  

        # Combine all button boxes in a horizontal layout
        self.button_layout_1 = QVBoxLayout()
        self.button_layout_2 = QVBoxLayout()
        self.button_layout_1.addWidget(self.next_box)
        self.button_layout_1.addWidget(self.back_box)
        self.button_layout_2.addWidget(self.send_box)
        self.button_layout_2.addWidget(self.discard_box)

    def set_layout(self):

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.vis_options_layout)
        self.layout.addWidget(self.chart)
        self.r1_layout = QHBoxLayout()
        self.r1_layout.addLayout(self.form_c1_layout)
        self.r1_layout.addLayout(self.form_c2_layout)
        self.r1_layout.addLayout(self.form_c3_layout)
        self.r1_layout.addLayout(self.button_layout_2)
        self.r1_layout.addLayout(self.button_layout_1)
        self.layout.addLayout(self.r1_layout)
        self.layout.addWidget(self.coord_box)
        self.layout.addWidget(self.notes_box)
        self.setLayout(self.layout)

    def update_widgets(self):

        self.bf_combobox.clear()
        self.bf_combobox.addItems(["-"] + self.bf_options_list)

        self.level_combobox.clear()
        self.level_combobox.addItems(["-"] + self.level_options_list)

        self.directory_combobox.setCurrentText(self.dir)
        self.file_combobox.setCurrentText(self.checkpoint)

        if self.existing_entry.empty:
            self.tuned_button_group.setExclusive(False)
            self.tuned_button_yes.setChecked(False)
            self.tuned_button_no.setChecked(False)
            self.clear_button_group.setExclusive(False)
            self.clear_button_yes.setChecked(False)
            self.clear_button_no.setChecked(False)
            self.healthy_button_group.setExclusive(False)
            self.healthy_button_yes.setChecked(False)
            self.healthy_button_no.setChecked(False)
            self.tuned_button_group.setExclusive(True)
            self.clear_button_group.setExclusive(True)
            self.healthy_button_group.setExclusive(True)
            self.type_combobox.setCurrentText("-")
            self.level_combobox.setCurrentText("-")
            self.bf_combobox.setCurrentText("-")
            self.note.setText("")

        if not self.existing_entry.empty:
            self.tuned_button_yes.setChecked(self.existing_entry['tuned'].iloc[0] == "Yes")
            self.tuned_button_no.setChecked(self.existing_entry['tuned'].iloc[0] == "No")
            self.clear_button_yes.setChecked(self.existing_entry['clear'].iloc[0] == "Yes")
            self.clear_button_no.setChecked(self.existing_entry['clear'].iloc[0] == "No")
            self.healthy_button_yes.setChecked(self.existing_entry['healthy'].iloc[0] == "Yes")
            self.healthy_button_no.setChecked(self.existing_entry['healthy'].iloc[0] == "No")
            self.type_combobox.setCurrentText(f"{self.existing_entry['type'].iloc[0]}")
            self.level_combobox.setCurrentText(f"{self.existing_entry['level threshold'].iloc[0]} dB")
            self.bf_combobox.setCurrentText(f"{self.existing_entry['best frequency'].iloc[0]} kHz")
            self.note.setText(str(self.existing_entry['note'].iloc[0]) if self.existing_entry['note'].iloc[0] else "")

    def update_file_combobox(self):

        self.file_combobox.clear()
        self.file_combobox.addItems(self.files_with_tags_list)

    def update_dashboard(self):
        plt.close(self.chart.figure)
        self.layout.removeWidget(self.chart)
        self.chart.deleteLater()
        self.chart = Canvas(self)
        self.layout.insertWidget(1, self.chart)

    # Action functions

    def on_send_clicked(self):

        print(f"{datetime.now()} - Action: send button clicked.")

        tuned = "Yes" if self.tuned_button_yes.isChecked() else "No" if self.tuned_button_no.isChecked() else None
        clear = "Yes" if self.clear_button_yes.isChecked() else "No" if self.clear_button_no.isChecked() else None
        healthy = "Yes" if self.healthy_button_yes.isChecked() else "No" if self.healthy_button_no.isChecked() else None
        selected_type = self.type_combobox.currentText() if self.type_combobox.currentText() != "-" else None
        best_frequency = float(self.bf_combobox.currentText()[:-4]) if self.bf_combobox.currentText() != "-" else None
        level_threshold = float(self.level_combobox.currentText()[:-3]) if self.level_combobox.currentText() != "-" else None
        note = str(self.note.text()) if self.note.text() else None
        x0 = float(self.x0_input.text()) if self.x0_input.text() else None
        xf = float(self.xf_input.text()) if self.xf_input.text() else None
        y = float(self.y_input.text()) if self.y_input.text() else None
        z = float(self.z_input.text()) if self.z_input.text() else None

        new_row = {
            'directory': self.dir,
            'filename': self.checkpoint,
            'channel': self.datachannel,
            'tuned': tuned,
            'clear': clear,
            'healthy': healthy,
            'type': selected_type,
            'best frequency': best_frequency,
            'level threshold': level_threshold,
            'note': note,
            'x': x0,
            'xf': xf,
            'y': y,
            'z': z,
            'entrydate': datetime.now(),
            'version': version,
            'user': user
        }

        confirmation_message = f"\
            Tuned: {tuned}\n\
            Clear: {clear}\n\
            Healthy: {healthy}\n\
            Type: {selected_type}\n\
            Best frequency :{best_frequency}\n\
            Level threshold: {level_threshold}\n\
            Coordinates: x={x0}, x={xf}, y={y}, z={z}\n\
            Note: {note}"

        if self.existing_entry.empty:
            annotations.loc[len(annotations)] = new_row
            annotations.to_csv(annotations_path, index=False)
            message_box = QMessageBox()
            message_box.setText(f"Saving the following for {self.dir}{self.checkpoint} at {self.datachannel}\n"
                                f"{confirmation_message}")
            message_box.exec_()

            print(f"{datetime.now()} - Message: successfully submited user's answer for file {self.dir}{self.checkpoint} at {self.datachannel}.")
        else:
            index_to_update = self.existing_entry.index[0]
            annotations.loc[index_to_update] = new_row
            annotations.to_csv(annotations_path, index=False)
            message_box = QMessageBox()
            message_box.setText(f"Overwritting the following for {self.dir}{self.checkpoint} at {self.datachannel}\n"
                                f"{confirmation_message}")
            message_box.exec_()
                                           
            print(f"{datetime.now()} - Message: successfully overwritten user's answer for file {self.dir}{self.checkpoint} at {self.datachannel}.")

        if self.checkpoint in self.non_checked_files:
            self.non_checked_files.remove(self.checkpoint)
        if self.checkpoint not in self.checked_files:
            self.checked_files.append(self.checkpoint)
        dir_index = progress[progress['directory'] == self.dir].index
        progress.at[dir_index[0], 'non checked files'] = self.non_checked_files
        progress.at[dir_index[0], 'checked files'] = self.checked_files
        progress.to_csv(progress_path, index=False)

        self.existing_entry = annotations [
                (annotations['directory'] == self.dir) &
                (annotations['filename'] == self.checkpoint) &
                (annotations['channel'] == self.datachannel)
        ]

        aux_checkpoint = self.checkpoint
        self.update_files_list()
        self.update_file_combobox()
        self.file_combobox.setCurrentText(next(item for item in self.files_with_tags_list if item.startswith(aux_checkpoint)))

    def on_discard_clicked(self):
            
        print(f"{datetime.now()} - Action: discard button clicked.")

        question = QMessageBox.question(self, 'Confirm discard',
                                    "Are you sure you want to discard this file? This action can't be undone.",
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.Yes)

        if question == QMessageBox.Yes:
            print(f"{datetime.now()} - Action: yes button clicked.")

            self.update_files_list()

            checkpoint_index = self.files_list.index(self.checkpoint)

            if self.checkpoint in self.non_checked_files:
                self.non_checked_files.remove(self.checkpoint)
            if self.checkpoint in self.checked_files:
                self.checked_files.remove(self.checkpoint)
            dir_index = progress[progress['directory'] == self.dir].index
            progress.at[dir_index[0], 'non checked files'] = self.non_checked_files
            progress.at[dir_index[0], 'checked files'] = self.checked_files
            progress.to_csv(progress_path, index=False)
            discarded.loc[len(discarded)] = {'directory': self.dir,
                                            'filename': self.checkpoint}
            discarded.to_csv(discarded_path, index=False)

            if checkpoint_index + 1 < len(self.files_list):
                self.checkpoint = self.files_list[checkpoint_index + 1]
                print(f"{datetime.now()} - Message: showing file {self.dir}{self.checkpoint}.")
            else:
                print(f"{datetime.now()} - Message: {self.dir}{self.checkpoint} was the last file.")
                QMessageBox.warning(self, "Message", "You reached the last file in the directory.")
                self.checkpoint = self.files_list[checkpoint_index - 1]
            self.load_data_on_checkpoint()
            self.update_widgets()
            self.update_dashboard()
            self.file_combobox.setCurrentText(next(item for item in self.files_with_tags_list if item.startswith(self.checkpoint)))

        else:
            print(f"{datetime.now()} - Action: no button clicked.")
            print(f"{datetime.now()} - Message: discard cancelled.")

    def on_next_clicked(self):
            
        print(f"{datetime.now()} - Action: next button clicked.")

        self.update_files_list()

        checkpoint_index = self.files_list.index(self.checkpoint)
        if checkpoint_index + 1 < len(self.files_list):
            self.checkpoint = self.files_list[checkpoint_index + 1]
            print(f"{datetime.now()} - Message: showing file {self.dir}{self.checkpoint}.")
            self.load_data_on_checkpoint()
            self.update_widgets()
            self.update_dashboard()
            self.file_combobox.setCurrentText(next(item for item in self.files_with_tags_list if item.startswith(self.checkpoint)))

        else:
            print(f"{datetime.now()} - Message: {self.dir}{self.checkpoint} is the last file.")
            QMessageBox.warning(self, "Message", "You reached the last file in the directory.")

    def on_back_clicked(self):

        print(f"{datetime.now()} - Action: back button clicked.")

        self.update_files_list()

        checkpoint_index = self.files_list.index(self.checkpoint)
        if checkpoint_index - 1 >= 0:
            self.checkpoint = self.files_list[checkpoint_index - 1]
            print(f"{datetime.now()} - Message: showing file {self.dir}{self.checkpoint}.")
            self.load_data_on_checkpoint()
            self.update_widgets()
            self.update_dashboard()
            self.file_combobox.setCurrentText(next(item for item in self.files_with_tags_list if item.startswith(self.checkpoint)))
        else:
            print(f"{datetime.now()} - {self.dir}{self.checkpoint} is the first file.")
            QMessageBox.warning(self, "Message", "You reached the first file in the directory.")

    def on_directory_selected(self, index):

        self.dir = self.directory_combobox.itemText(index).split(' ')[0]
        dir_info = progress[progress['directory'] == self.dir].iloc[0]

        self.non_checked_files = get_filenames(dir_info['non checked files'])
        self.checked_files = get_filenames(dir_info['checked files'])
        self.error_files = get_filenames(dir_info['error files'])
        self.update_files_list()

        if len(self.files_list) == 0:
            print(f"{datetime.now()} - Message: {self.dir} was the last file.")
            QMessageBox.warning(self, "Message", "This directory is empty.")
        else:
            if len(self.non_checked_files) > 0:
                self.checkpoint = self.non_checked_files[0]
            elif len(self.files_list) > 0:
                self.checkpoint = self.files_list[0]

            print(f"{datetime.now()} - Message: successfully changed to {self.dir}{self.checkpoint}")
            self.load_data_on_checkpoint()
            self.update_dashboard()

        self.update_file_combobox()
        self.update_widgets()

    def on_file_selected(self, index):
        selected_text = self.file_combobox.itemText(index)
        if selected_text:  # Ensure it's not empty
            self.checkpoint = selected_text[0:4]
            self.load_data_on_checkpoint()
            self.update_dashboard()
            self.update_widgets()
        else:
            pass

    def on_vis_selected(self, index):
        if self.visualization_combobox.itemText(index) == "All traces":
            self.visualization = "all traces"
        elif self.visualization_combobox.itemText(index) == "Highest activity traces":
            self.visualization = "highest activity traces"
        elif self.visualization_combobox.itemText(index) == "Activity plots":
            self.visualization = "activity plots"

        self.update_dashboard()

    def on_channel_selected(self, index):
        if self.channel_combobox.itemText(index) == "Channel 0":
            self.datachannel = "di0P"
        elif self.channel_combobox.itemText(index) == "Channel 2":
            self.datachannel = "di2P"
        elif self.channel_combobox.itemText(index) == "Channel 1":
            self.datachannel = "di1P"
        elif self.channel_combobox.itemText(index) == "Channel 3":
            self.datachannel = "di3P"
        elif self.channel_combobox.itemText(index) == "Channel 4":
            self.datachannel = "di4P"
        self.load_data_on_checkpoint()
        self.update_files_list()
        self.update_widgets()
        self.update_dashboard()
        # self.update_file_combobox()
        # self.file_combobox.setCurrentText(next(item for item in self.files_with_tags_list if item.startswith(self.checkpoint)))

    def closeEvent(self, event):
        print(f"{datetime.now()} - Action: exit button clicked.")
        question = QMessageBox.question(self, 'Confirm Exit',
                                    "Do you want to exit the program?",
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.Yes)

        if question == QMessageBox.Yes:
            print(f"{datetime.now()} - Action: yes button clicked.")
            event.accept() 
        else:
            print(f"{datetime.now()} - Action: no button clicked.")
            print(f"{datetime.now()} - Message: exit cancelled.")
            event.ignore()

if __name__ == "__main__":

    user = sys.argv[1]
    version = sys.argv[2]
    shape, channel, mean, symmetry = sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]

    if user == "perecornella":
        root_dir = "/Users/perecornella/Library/CloudStorage/GoogleDrive-pere.cornella@estudiantat.upc.edu/My Drive/ReyesLabNYU/"
    elif user == "ar65":
        root_dir = "/Users/ar65/Library/CloudStorage/GoogleDrive-ar65@nyu.edu/My Drive/ReyesLabNYU/"
    else:
        sys.exit(1) # TODO

    progress_path = root_dir + f'Pere/metadata/progress/{shape}_{channel}_{mean}_{symmetry}_progress.csv'
    annotations_path = root_dir + f'Pere/metadata/annotations.csv'
    discarded_path = root_dir + f'Pere/metadata/progress/{shape}_{channel}_{mean}_{symmetry}_discarded.csv'
    progress = pd.read_csv(progress_path)
    try:
        annotations = pd.read_csv(annotations_path)
    except:
        annotations = pd.DataFrame(columns=['directory', 'filename', 'channel',
                                         'tuned', 'clear', 'healthy','type',
                                         'best frequency', 'level threshold','note',
                                         'x', 'xf', 'y', 'z',
                                         'entrydate', 'version', 'user'])
    progress = pd.read_csv(progress_path)
    try:
        discarded = pd.read_csv(discarded_path)
    except:
        discarded = pd.DataFrame(columns=['directory', 'filename'])

    app = QApplication(sys.argv)

    demo = AppDemo()
    demo.show()
    demo.closeEvent = demo.closeEvent
    sys.exit(app.exec_())
