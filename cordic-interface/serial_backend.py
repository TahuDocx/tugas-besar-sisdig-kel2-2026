"""Qt bridge between Main.qml and the FPGA UART (QSerialPort). Byte format lives in serial_codec."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from serial_codec import LINE_ENDS, decodeRx, encodeT

DEFAULT_BAUD = 9600  # uart_rx.vhd prescaler 5208 at 50 MHz


class SerialBackend(QObject):
    """Owns one QSerialPort. QML calls the slots; console text arrives through `received`."""

    portsChanged = Signal()
    connectedChanged = Signal()
    received = Signal(str)  # decoded RX text, append to console as-is
    logged = Signal(str)    # status/error line from the app itself

    # === CONSTRUCTOR ===

    def __init__(self, parent=None):
        """Creates the backend with a closed port and fills the port list. No I/O on the port."""
        super().__init__(parent)
        self._port = QSerialPort(self)
        self._port.readyRead.connect(self._onReadyRead)
        self._port.errorOccurred.connect(self._onError)
        self._ports = []
        self.refreshPorts()

    # === SELECTOR ===

    def _getPorts(self):
        """Returns the port names found by the last refreshPorts() call."""
        return self._ports

    def _getConnected(self):
        """Returns True while the serial port is open."""
        return self._port.isOpen()

    def _getLineEnds(self):
        """Returns the line-end names accepted by sendT(), in display order."""
        return list(LINE_ENDS)

    def _getDefaultBaud(self):
        """Returns the baud rate the FPGA UART runs at."""
        return DEFAULT_BAUD

    ports = Property("QVariantList", _getPorts, notify=portsChanged)
    connected = Property(bool, _getConnected, notify=connectedChanged)
    lineEnds = Property("QVariantList", _getLineEnds, constant=True)
    defaultBaud = Property(int, _getDefaultBaud, constant=True)

    # === MUTATOR ===

    @Slot()
    def refreshPorts(self):
        """Rescans the system serial ports and emits portsChanged."""
        self._ports = [info.portName() for info in QSerialPortInfo.availablePorts()]
        self.portsChanged.emit()

    @Slot(str, int)
    def openPort(self, name, baud):
        """Opens `name` at `baud`, 8N1, no flow control. Logs the result; emits connectedChanged.

        Closes any port already open first.
        """
        if self._port.isOpen():
            self.closePort()
        if not name:
            self.logged.emit("No port selected.")
            return
        self._port.setPortName(name)
        self._port.setBaudRate(baud)
        self._port.setDataBits(QSerialPort.DataBits.Data8)
        self._port.setParity(QSerialPort.Parity.NoParity)
        self._port.setStopBits(QSerialPort.StopBits.OneStop)
        self._port.setFlowControl(QSerialPort.FlowControl.NoFlowControl)
        if self._port.open(QSerialPort.OpenModeFlag.ReadWrite):
            self.logged.emit(f"Opened {name} @ {baud} 8N1.")
        else:
            self.logged.emit(f"Cannot open {name}: {self._port.errorString()}")
        self.connectedChanged.emit()

    @Slot()
    def closePort(self):
        """Closes the port if open. Logs it and emits connectedChanged."""
        if self._port.isOpen():
            name = self._port.portName()
            self._port.close()
            self.logged.emit(f"Closed {name}.")
        self.connectedChanged.emit()

    @Slot(str, str)
    def sendT(self, text, line_end):
        """Encodes t with serial_codec.encodeT and writes it to the port.

        Logs the sent bytes, or the reason nothing was sent (port closed, invalid t).
        """
        if not self._port.isOpen():
            self.logged.emit("Not connected.")
            return
        try:
            data = encodeT(text, line_end)
        except ValueError as err:
            self.logged.emit(f"Not sent: {err}.")
            return
        self._port.write(data)
        self.logged.emit(f"TX {data!r}")

    # === EVENT HANDLER ===

    def _onReadyRead(self):
        """Reads every pending byte and emits it as decoded console text."""
        text = decodeRx(bytes(self._port.readAll().data()))
        if text:
            self.received.emit(text)

    def _onError(self, error):
        """Logs a serial error. On resource errors (cable pulled) closes the port."""
        if error == QSerialPort.SerialPortError.NoError:
            return
        self.logged.emit(f"Serial error: {self._port.errorString()}")
        if error == QSerialPort.SerialPortError.ResourceError:
            self.closePort()
