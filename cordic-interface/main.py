import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from serial_backend import SerialBackend
from sim_backend import SimBackend

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    serial = SerialBackend()
    sim = SimBackend()
    engine.rootContext().setContextProperty("serial", serial)
    engine.rootContext().setContextProperty("sim", sim)
    # QML module "CordicUI" lives next to this file; sys.path[0] is not reliable (imports may
    # prepend paths, and it is "" under some launchers).
    engine.addImportPath(str(Path(__file__).resolve().parent))
    engine.loadFromModule("CordicUI", "Main")
    if not engine.rootObjects():
        sys.exit(-1)
    exit_code = app.exec()
    del engine
    sys.exit(exit_code)