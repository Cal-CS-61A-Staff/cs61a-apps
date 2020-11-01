from gui_files.common_server import start
from hog_gui import DEFAULT_SERVER, GUI_FOLDER, PORT

app = start(PORT, DEFAULT_SERVER, GUI_FOLDER)

if __name__ == "__main__":
    app.run()
