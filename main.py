import sys
import os
import json
from PyQt5 import QtWidgets, QtGui, QtCore
from datetime import datetime
import psutil
import platform
import subprocess


class SnapshotApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Dynamically set the snapshot directory based on the platform
        if platform.system() == "Windows":
            self.SNAPSHOT_DIR = os.path.join(os.getenv("APPDATA"), "snapshot_tool", "snapshots")
        else:
            self.SNAPSHOT_DIR = os.path.join(os.path.expanduser("~"), "snapshot_tool", "snapshots")

        # Ensure the snapshot directory exists
        if not os.path.exists(self.SNAPSHOT_DIR):
            os.makedirs(self.SNAPSHOT_DIR)

        # Main horizontal layout to hold the button panel and text area side by side
        main_layout = QtWidgets.QHBoxLayout()

        # Button layout (vertical layout for the buttons on the left)
        button_layout = QtWidgets.QVBoxLayout()

        # Create buttons with fixed widths
        self.create_button = QtWidgets.QPushButton("Create Snapshot")
        self.create_button.setFixedWidth(150)

        self.list_button = QtWidgets.QPushButton("List Snapshots")
        self.list_button.setFixedWidth(150)

        self.restore_button = QtWidgets.QPushButton("Restore Snapshot")
        self.restore_button.setFixedWidth(150)

        self.delete_button = QtWidgets.QPushButton("Delete Snapshot")
        self.delete_button.setFixedWidth(150)

        # Interval selector for automatic snapshots
        self.interval_label = QtWidgets.QLabel("Set Snapshot Interval:")
        self.interval_input = QtWidgets.QComboBox()
        self.interval_input.addItem("1 second")
        self.interval_input.addItem("1 minute")
        self.interval_input.addItem("5 minutes")
        self.interval_input.addItem("15 minutes")
        self.interval_input.addItem("30 minutes")
        self.interval_input.addItem("1 hour")
        self.interval_input.addItem("3 hours")
        self.interval_input.addItem("6 hours")
        self.interval_input.addItem("12 hours")
        self.interval_input.addItem("24 hours")

        # Set up a button to start the automatic snapshot
        self.start_automatic_button = QtWidgets.QPushButton("Start Automatic Snapshots")
        self.start_automatic_button.clicked.connect(self.start_automatic_snapshots)

        # Set up a button to stop automatic snapshots
        self.stop_automatic_button = QtWidgets.QPushButton("Stop Automatic Snapshots")
        self.stop_automatic_button.clicked.connect(self.stop_automatic_snapshots)

        # Clear Text Area button
        self.clear_button = QtWidgets.QPushButton("Clear Text Area")
        self.clear_button.setFixedWidth(150)
        self.clear_button.clicked.connect(self.clear_text_area)

        # Connect buttons to their functions
        self.create_button.clicked.connect(self.create_snapshot)
        self.list_button.clicked.connect(self.list_snapshots)
        self.restore_button.clicked.connect(self.restore_snapshot)
        self.delete_button.clicked.connect(self.delete_snapshot)

        # Add buttons to the button layout
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.list_button)
        button_layout.addWidget(self.restore_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.interval_label)
        button_layout.addWidget(self.interval_input)
        button_layout.addWidget(self.start_automatic_button)
        button_layout.addWidget(self.stop_automatic_button)
        button_layout.addStretch()  # Add stretch to push buttons to the top



        # Display area (text area on the right side)
        self.text_area = QtWidgets.QTextEdit()
        self.text_area.setReadOnly(True)

        # Add button layout and text area to the main layout
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.text_area)

        # Set layout
        container = QtWidgets.QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def delete_snapshot(self):
        # Check if snapshot directory exists and contains snapshots
        if not os.path.exists(self.SNAPSHOT_DIR):
            self.text_area.append("No snapshots available to delete.")
            return

        # Get a list of snapshot files
        snapshots = os.listdir(self.SNAPSHOT_DIR)
        if not snapshots:
            self.text_area.append("No snapshots available to delete.")
            return

        # Add "All" option to the list of snapshots
        snapshots.append("All")

        # Show confirmation dialog with list of snapshots (including "All" option)
        snapshot_name, ok = QtWidgets.QInputDialog.getItem(
            self, "Delete Snapshot", "Select a snapshot to delete:", snapshots, 0, False
        )

        # If the user selected "All" and clicked OK
        if ok and snapshot_name:
            if snapshot_name:
                # Create a Yes/No confirmation dialog before deleting all snapshots
                reply = QtWidgets.QMessageBox.question(
                    self,  # Parent widget
                    "Warning",  # Dialog title
                    "Are you sure you want to delete all snapshots?",  # Message
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,  # Buttons
                    QtWidgets.QMessageBox.No  # Default button
                )

                if reply == QtWidgets.QMessageBox.Yes:
                    # Delete all snapshots
                    for snapshot in snapshots:
                        snapshot_path = os.path.join(self.SNAPSHOT_DIR, snapshot)
                        if os.path.exists(snapshot_path) and snapshot != "All":
                            try:
                                os.remove(snapshot_path)
                            except Exception as e:
                                self.text_area.append("Error deleting {snapshot} : {e}")

                    self.text_area.append("All snapshots deleted successfully.")
                else:
                    self.text_area.append("Deletion canceled.")
            else:
                # Delete the selected snapshot
                snapshot_path = os.path.join(self.SNAPSHOT_DIR, snapshot_name)
                if os.path.exists(snapshot_path):
                    os.remove(snapshot_path)
                    self.text_area.append(f"Snapshot '{snapshot_name}' deleted successfully.")
                else:
                    self.text_area.append(f"Snapshot '{snapshot_name}' not found.")

    def restore_snapshot(self):
        # Check if snapshot directory exists and contains snapshots
        if not os.path.exists(self.SNAPSHOT_DIR):
            self.text_area.append("No snapshots available to restore.")
            return

        # Get a list of snapshot files
        snapshots = os.listdir(self.SNAPSHOT_DIR)
        if not snapshots:
            self.text_area.append("No snapshots available to restore.")
            return

        # Show dropdown dialog with list of snapshots
        snapshot_name, ok = QtWidgets.QInputDialog.getItem(
            self, "Restore Snapshot", "Select a snapshot to restore:", snapshots, 0, False
        )

        # If the user selected a snapshot and clicked OK
        if ok and snapshot_name:
            snapshot_path = os.path.join(self.SNAPSHOT_DIR, snapshot_name)
            try:
                with open(snapshot_path, 'r') as f:
                    snapshot_data = json.load(f)

                # Separate system and user apps based on paths
                system_apps = []
                user_apps = []

                for process in snapshot_data["processes"]:
                    name = process.get("name", "Unknown")
                    cmdline = process.get("cmdline", [])
                    path = cmdline[0] if cmdline else ""

                    if "Windows" in path or "/usr/" in path:  # Adjust for Linux or Windows
                        system_apps.append(name)
                    else:
                        user_apps.append(name)

                # Let the user choose between system and user apps
                category, ok = QtWidgets.QInputDialog.getItem(
                    self,
                    "Application Type",
                    "Select the type of applications to restore:",
                    ["User Apps", "System Apps"],
                    0,
                    False,
                )

                if ok:
                    apps_to_display = user_apps if category == "User Apps" else system_apps

                    # Multi-selection dialog with search
                    dialog = QtWidgets.QDialog(self)
                    dialog.setWindowTitle(f"Select {category} to Restore")
                    layout = QtWidgets.QVBoxLayout(dialog)

                    search_bar = QtWidgets.QLineEdit(dialog)
                    search_bar.setPlaceholderText("Search...")
                    layout.addWidget(search_bar)

                    list_widget = QtWidgets.QListWidget(dialog)
                    list_widget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
                    list_widget.addItems(apps_to_display)
                    layout.addWidget(list_widget)

                    button_box = QtWidgets.QDialogButtonBox(
                        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
                    layout.addWidget(button_box)

                    button_box.accepted.connect(dialog.accept)
                    button_box.rejected.connect(dialog.reject)

                    # Connect search bar to filter items in the list widget
                    def filter_apps():
                        filter_text = search_bar.text().lower()
                        list_widget.clear()
                        for app in apps_to_display:
                            if filter_text in app.lower():
                                list_widget.addItem(app)

                    search_bar.textChanged.connect(filter_apps)

                    if dialog.exec() == QtWidgets.QDialog.Accepted:
                        selected_apps = [item.text() for item in list_widget.selectedItems()]
                        self.text_area.append(f"\nSelected {category.lower()} to restore: {', '.join(selected_apps)}")

                        # Restore selected processes
                        for process in snapshot_data["processes"]:
                            if process.get("name") in selected_apps:
                                cmdline = process.get('cmdline', [])
                                if cmdline:
                                    try:
                                        subprocess.Popen(cmdline)
                                        self.text_area.append(f"  Started: {' '.join(cmdline)}")
                                    except Exception as e:
                                        self.text_area.append(f"  Failed to start: {' '.join(cmdline)}. Error: {e}")
                                else:
                                    self.text_area.append(f"  Skipped: {process['name']} (No command line available)")

            except Exception as e:
                self.text_area.append(f"Error restoring snapshot: {e}")

    def clear_text_area(self):
        self.text_area.clear()

    def create_snapshot(self):
        try:
            # Ensure the snapshot directory exists
            if not os.path.exists(self.SNAPSHOT_DIR):
                os.makedirs(self.SNAPSHOT_DIR, exist_ok=True)

            # Collect system information for the snapshot
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': proc.info['cmdline']
                })

            memory = psutil.virtual_memory()
            connections = psutil.net_connections(kind='inet')

            snapshot_data = {
                'processes': processes,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'connections': [
                    {'fd': conn.fd, 'family': conn.family, 'type': conn.type, 'laddr': conn.laddr, 'raddr': conn.raddr,
                     'status': conn.status}
                    for conn in connections
                ]
            }

            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            snapshot_filename = os.path.join(self.SNAPSHOT_DIR, f'snapshot_{timestamp}.json')

            with open(snapshot_filename, 'w') as snapshot_file:
                json.dump(snapshot_data, snapshot_file)

            self.text_area.append(f"Snapshot created: {snapshot_filename}")

        except Exception as e:
            self.text_area.append(f"Error creating snapshot: {e}")

    def list_snapshots(self):
        try:
            # Check if snapshot directory exists
            if not os.path.exists(self.SNAPSHOT_DIR):
                self.text_area.append("No snapshots available.")
                return

            snapshots = os.listdir(self.SNAPSHOT_DIR)
            if snapshots:
                self.text_area.append("Available snapshots:")
                for snapshot in snapshots:
                    self.text_area.append(f"  {snapshot}")
            else:
                self.text_area.append("No snapshots available.")
        except Exception as e:
            self.text_area.append(f"Error listing snapshots: {e}")

    def start_automatic_snapshots(self):
        # Get the selected interval from the dropdown
        interval = self.interval_input.currentText()

        # Convert the selected interval to seconds
        interval_seconds = self.convert_interval_to_seconds(interval)

        # If the interval is invalid, show a warning
        if interval_seconds is None:
            self.text_area.append("Invalid interval selected.")
            return

        # Display message
        self.text_area.append(f"Automatic snapshots will be taken every {interval}.")

        # Create a QTimer to call create_snapshot() every interval_seconds
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.create_snapshot)
        self.timer.start(interval_seconds * 1000)  # Convert to milliseconds

    def convert_interval_to_seconds(self, interval):
        """Convert the selected interval text to seconds."""
        if interval == "1 second":
            return 1  # 1 second in seconds
        elif interval == "1 minute":
            return 60  # 1 minute in seconds
        elif interval == "5 minutes":
            return 5 * 60  # 5 minutes in seconds
        elif interval == "15 minutes":
            return 15 * 60  # 15 minutes in seconds
        elif interval == "30 minutes":
            return 30 * 60  # 30 minutes in seconds
        elif interval == "1 hour":
            return 60 * 60  # 1 hour in seconds
        elif interval == "3 hours":
            return 3 * 60 * 60  # 3 hours in seconds
        elif interval == "6 hours":
            return 6 * 60 * 60  # 6 hours in seconds
        elif interval == "12 hours":
            return 12 * 60 * 60  # 12 hours in seconds
        elif interval == "24 hours":
            return 24 * 60 * 60  # 24 hours in seconds
        else:
            return None

    def stop_automatic_snapshots(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
            self.text_area.append("Automatic snapshots stopped.")
        else:
            self.text_area.append("Automatic snapshots are not running.")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = SnapshotApp()
    window.setWindowTitle("Snapshot Tool")
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec_())

