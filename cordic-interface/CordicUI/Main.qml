// CORDIC interface: input t, Send over UART, FPGA ASCII replies shown in a console.
// `serial` is the SerialBackend context property set in main.py.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 720
    height: 520
    visible: true
    title: "CORDIC Interface"

    // === CONSOLE HELPERS ===

    // Appends raw text to the console and keeps the view scrolled to the bottom.
    function appendConsole(text) {
        consoleText.insert(consoleText.length, text)
        consoleText.cursorPosition = consoleText.length
    }

    // Appends an app status line, starting it on a fresh line.
    function logLine(text) {
        var needs_break = consoleText.length > 0 && consoleText.text.slice(-1) !== "\n"
        appendConsole((needs_break ? "\n" : "") + "[app] " + text + "\n")
    }

    // Created hidden; the Simulator button shows it with the current t.
    SimWindow { id: simWindow }

    Connections {
        target: serial
        function onReceived(text) { root.appendConsole(text) }
        function onLogged(text) { root.logLine(text) }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        // Port row
        RowLayout {
            spacing: 8
            Label { text: "Port" }
            ComboBox {
                id: portBox
                Layout.preferredWidth: 140
                model: serial.ports
                enabled: !serial.connected
            }
            Button {
                text: "Refresh"
                enabled: !serial.connected
                onClicked: serial.refreshPorts()
            }
            Label { text: "Baud" }
            TextField {
                id: baudField
                Layout.preferredWidth: 90
                text: serial.defaultBaud
                enabled: !serial.connected
                validator: IntValidator { bottom: 300; top: 4000000 }
            }
            Button {
                text: serial.connected ? "Disconnect" : "Connect"
                onClicked: serial.connected ? serial.closePort()
                                            : serial.openPort(portBox.currentText, parseInt(baudField.text))
            }
            Item { Layout.fillWidth: true }
            Label {
                text: serial.connected ? "● connected" : "○ disconnected"
                color: serial.connected ? "#2e7d32" : "#9e9e9e"
            }
        }

        // Input row
        RowLayout {
            spacing: 8
            Label { text: "t" }
            TextField {
                id: tField
                Layout.fillWidth: true
                placeholderText: "e.g. 0.5"
                onAccepted: sendButton.clicked()
            }
            Label { text: "End" }
            ComboBox {
                id: lineEndBox
                model: serial.lineEnds
                currentIndex: 1   // LF
            }
            Button {
                id: sendButton
                text: "Send"
                enabled: serial.connected && tField.text.trim().length > 0
                onClicked: serial.sendT(tField.text, lineEndBox.currentText)
            }
            Button {
                text: "Simulator"
                onClicked: simWindow.openWith(tField.text)
            }
        }

        // Console
        RowLayout {
            Label { text: "Console (RX from FPGA)"; font.bold: true }
            Item { Layout.fillWidth: true }
            Button { text: "Clear"; onClicked: consoleText.clear() }
        }
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            background: Rectangle { color: "#111111"; radius: 4 }
            TextArea {
                id: consoleText
                readOnly: true
                wrapMode: TextArea.WrapAnywhere
                font.family: "Consolas"
                font.pixelSize: 14
                color: "#33ff66"
                selectByMouse: true
                background: null
            }
        }
    }
}
