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

        # Create the main layout
        self.layout = QVBoxLayout()

        # Create QButtonGroup instances for each category
        self.tuned_button_group = QButtonGroup(self)
        self.clear_button_group = QButtonGroup(self)
        self.healthy_button_group = QButtonGroup(self)

        # Initialize with the first sample
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

        if input_directory is not None:
            try:
                row = dir_info[dir_info['name'] == input_directory].iloc[0]
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
        
        # Add the initial dashboard (Canvas) to the layout
        self.chart = Canvas(self, self.sample, self.filename)
        self.layout.addWidget(self.chart)

        # Create horizontal layouts for Yes/No buttons
        self.tuned_layout = QHBoxLayout()
        self.clear_layout = QHBoxLayout()
        self.healthy_layout = QHBoxLayout()

        # Yes/No buttons for Tuned, clear, Healthy
        self.tuned_button_yes = QRadioButton("Yes")
        self.tuned_button_no = QRadioButton("No")
        self.clear_button_yes = QRadioButton("Yes")
        self.clear_button_no = QRadioButton("No")
        self.healthy_button_yes = QRadioButton("Yes")
        self.healthy_button_no = QRadioButton("No")

        # Intra/Extra question for Type
        self.type_combobox = QComboBox()
        self.type_combobox.addItems(["Intra", "Extra"])

        # Coordinates input for x, y, z
        self.x0_input = QLineEdit()
        self.xf_input = QLineEdit()
        self.i_input = QLineEdit()
        self.n_input = QLineEdit()
        self.y_input = QLineEdit()
        self.z_input = QLineEdit()

        # Add the radio buttons horizontally to the layouts
        self.tuned_layout.addWidget(QLabel("Tuned"))
        self.tuned_layout.addWidget(self.tuned_button_yes)
        self.tuned_layout.addWidget(self.tuned_button_no)

        self.clear_layout.addWidget(QLabel("Clear"))
        self.clear_layout.addWidget(self.clear_button_yes)
        self.clear_layout.addWidget(self.clear_button_no)

        self.healthy_layout.addWidget(QLabel("Healthy"))
        self.healthy_layout.addWidget(self.healthy_button_yes)
        self.healthy_layout.addWidget(self.healthy_button_no)

        # Add radio buttons to the button groups to ensure only one is selected at a time
        self.tuned_button_group.addButton(self.tuned_button_yes)
        self.tuned_button_group.addButton(self.tuned_button_no)
        self.clear_button_group.addButton(self.clear_button_yes)
        self.clear_button_group.addButton(self.clear_button_no)
        self.healthy_button_group.addButton(self.healthy_button_yes)
        self.healthy_button_group.addButton(self.healthy_button_no)

        # Add the layouts to the main layout
        self.layout.addLayout(self.tuned_layout)
        self.layout.addLayout(self.clear_layout)
        self.layout.addLayout(self.healthy_layout)

        # Add Type ComboBox in a horizontal layout
        self.type_layout = QHBoxLayout()
        self.type_layout.addWidget(QLabel("Type"))
        self.type_layout.addWidget(self.type_combobox)
        self.layout.addLayout(self.type_layout)

        # Add Coordinates inputs in a horizontal layout
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
        self.layout.addLayout(self.coord_layout)

        # Add Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.on_send_clicked)

        # Add the Send button to the layout
        self.layout.addWidget(self.send_button)

        # Set the layout for the QWidget
        self.setLayout(self.layout)

    def on_send_clicked(self):
        if self.input_file is not None:
            QMessageBox.warning(self, "Warning", "You inserted a filename; changes cannot be persisted.")

        else:
            # Get the selected Yes/No values
            tuned = "Yes" if self.tuned_button_yes.isChecked() else "No"
            clear = "Yes" if self.clear_button_yes.isChecked() else "No"
            healthy = "Yes" if self.healthy_button_yes.isChecked() else "No"

            # Get the selected Type
            selected_type = self.type_combobox.currentText()

            # Get the coordinates
            x0 = float(self.x0_input.text())
            xf = float(self.xf_input.text())
            i = float(self.i_input.text())
            n = float(self.n_input.text())
            y = float(self.y_input.text())
            z = float(self.z_input.text())

            # Prepare the message for the confirmation pop-up
            confirmation_message = f"Tuned: {tuned}\nClear: {clear}\nHealthy: {healthy}\nType: {selected_type}\nCoordinates: x={x0 + i * (xf - x0) // n}, y={y}, z={z}"

            # Show the confirmation pop-up
            reply = QMessageBox.question(self, 'Confirm your entries', f"Are you sure you want to submit the following values?\n\n{confirmation_message}", 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                new_row = {
                    'directory': self.dir,
                    'filename': f"A{self.checkpoint:03d}",
                    'tuned': tuned,
                    'clear': clear,
                    'healthy': healthy,
                    'type': selected_type,
                    'x': x0 + i * (xf - x0) // n,
                    'y': y,
                    'z': z,
                    'd': self.d,
                    'bf': self.bf,
                    'th': self.th,
                    'entrydate': datetime.now()
                }

                # Add the new row to the DataFrame
                metadata.loc[len(metadata)] = new_row


                # If user clicked Yes, proceed with sending the data
                # print(f"Confirmed: {confirmation_message}")
                self.checkpoint += 1
                all_error = True
                while self.batch_pointer < self.number_of_batches:
                    if self.counter == 0:
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

                self.update_dashboard()
            else:
                # If user clicked No, just print the message
                print("Submission cancelled.")

    def update_dashboard(self):
        plt.close(self.chart.figure)
        
        # Remove the old canvas
        self.layout.removeWidget(self.chart)
        self.chart.deleteLater()

        # Create a new canvas with updated data
        self.chart = Canvas(self, self.sample, self.filename)
        self.layout.insertWidget(0, self.chart)

    def closeEvent(self, event):
        # Create a message box asking for confirmation
        reply = QMessageBox.question(self, 'Confirm Exit',
                                    "Do you want to save changes before exiting?",
                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
                                    QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            # If the user selects Yes, save the files
            dir_info.to_csv('metadata/dir_info.csv')
            metadata.to_csv(f'metadata/{datachannel}.csv')
            event.accept()  # Close the window
        elif reply == QMessageBox.No:
            # If the user selects No, close without saving
            event.accept()
        else:
            # If the user selects Cancel, do nothing (keep the window open)
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
