// CORDIC simulator window: runs ../cordic-sim-py through the `sim` context property
// (SimBackend) and prints the iteration report. Opened from Main.qml.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: simWin
    width: 820
    height: 600
    title: "CORDIC Simulator (cordic-sim-py)"

    // === ACTIONS ===

    // Opens the window with t prefilled and brings it to the front.
    function openWith(t_text) {
        if (t_text.trim().length > 0)
            tField.text = t_text
        simWin.show()
        simWin.raise()
        simWin.requestActivate()
    }

    // Runs the simulator with the current form values; shows the report and timing line.
    function runSim() {
        var out = sim.run(funcBox.currentText, tField.text, nBox.value, fixedBox.checked,
                          fracBox.value, widthBox.value, parseFloat(clockField.text))
        report.text = out.report
        timingLabel.text = out.timing
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        RowLayout {
            spacing: 8
            Label { text: "Function" }
            ComboBox { id: funcBox; model: sim.funcs }
            Label { text: "t" }
            TextField {
                id: tField
                Layout.preferredWidth: 110
                text: "0.5"
                onAccepted: simWin.runSim()
            }
            Label { text: "n" }
            SpinBox { id: nBox; from: 1; to: 64; value: 16; editable: true }
            Item { Layout.fillWidth: true }
            Button { text: "Run"; highlighted: true; onClicked: simWin.runSim() }
        }

        RowLayout {
            spacing: 8
            CheckBox { id: fixedBox; text: "Fixed-point"; checked: true }
            Label { text: "frac"; enabled: fixedBox.checked }
            SpinBox {
                id: fracBox; from: 0; to: widthBox.value - 1; value: 14
                editable: true; enabled: fixedBox.checked
            }
            Label { text: "width"; enabled: fixedBox.checked }
            SpinBox {
                id: widthBox; from: 2; to: 64; value: 16
                editable: true; enabled: fixedBox.checked
            }
            Label {
                text: fixedBox.checked ? "Q" + (widthBox.value - fracBox.value) + "." + fracBox.value
                                       : "float"
                color: "#757575"
            }
            Item { Layout.fillWidth: true }
            Label { text: "FPGA clock (MHz)" }
            TextField {
                id: clockField
                Layout.preferredWidth: 70
                text: "50"   // DE1 CLOCK_50
                validator: DoubleValidator { bottom: 0.001; top: 1000 }
                onAccepted: simWin.runSim()
            }
        }

        Label {
            id: timingLabel
            Layout.fillWidth: true
            elide: Text.ElideRight
            font.family: "Consolas"
            color: "#1565c0"
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            background: Rectangle { color: "#111111"; radius: 4 }
            TextArea {
                id: report
                readOnly: true
                wrapMode: TextArea.NoWrap
                font.family: "Consolas"
                font.pixelSize: 13
                color: "#33ff66"
                selectByMouse: true
                background: null
                placeholderText: "Press Run."
                placeholderTextColor: "#555555"
            }
        }
    }
}
