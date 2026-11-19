// CORDIC simulator window: runs ../cordic-sim-py through the `sim` context property
// (SimBackend) and prints the iteration report. Opened from Main.qml.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: simWin
    width: 820
    height: 680
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

    // Runs the simulator with the current form values; shows the report, the timing line,
    // redraws the error-vs-iterations plot for n = 1 .. current n, and shows the smallest n
    // that keeps |error| <= tolerance.
    function runSim() {
        let out = sim.run(funcBox.currentText, tField.text, nBox.value, fixedBox.checked,
                          fracBox.value, widthBox.value, parseFloat(clockField.text))
        report.text = out.report
        timingLabel.text = out.timing

        let sw = sim.sweep(funcBox.currentText, tField.text, nBox.value, fixedBox.checked,
                           fracBox.value, widthBox.value, tolField.text)
        plot.fixedPts = sw.fixed
        plot.idealPts = sw.ideal
        plot.nMax = nBox.value
        plot.lsb = fixedBox.checked ? Math.pow(2, -fracBox.value) : 0
        plot.fracBits = fracBox.value
        plot.tol = sw.tol
        plot.minN = fixedBox.checked ? sw.minFixed : sw.minIdeal
        if (sw.error.length > 0)
            plot.message = sw.error
        else if (sw.ideal.length === 0)
            plot.message = "Expected value is undefined for this t: no error to plot."
        else
            plot.message = ""
        plot.requestPaint()
        minLabel.text = simWin.minText(sw)
    }

    // Returns the one-line summary of the smallest n meeting the tolerance, for minLabel.
    function minText(sw) {
        if (sw.error.length > 0 || sw.ideal.length === 0)
            return ""
        if (sw.tolError.length > 0)
            return "Error: " + sw.tolError + "."
        let part = function (name, m) {
            return name + ": " + (m > 0 ? "n = " + m
                                        : "not reached by n = " + nBox.value + " (raise n)")
        }
        let s = "Min iterations with |error| <= " + sw.tol + " (and staying under, up to n = "
                + nBox.value + ")    "
        if (fixedBox.checked)
            s += part("fixed", sw.minFixed) + "    |    "
        return s + part("float", sw.minIdeal)
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
            Label { text: "max |error|" }
            TextField {
                id: tolField
                Layout.preferredWidth: 80
                text: "1e-3"
                onAccepted: simWin.runSim()
            }
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

        Label {
            id: minLabel
            Layout.fillWidth: true
            elide: Text.ElideRight
            font.family: "Consolas"
            font.bold: true
            color: "#c62828"
        }

        TabBar {
            id: tabs
            Layout.fillWidth: true
            TabButton { text: "Iteration report" }
            TabButton { text: "Error vs iterations" }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabs.currentIndex

            ScrollView {
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

            Rectangle {
                color: "#111111"
                radius: 4

                Canvas {
                    id: plot
                    anchors.fill: parent
                    anchors.margins: 4

                    property var fixedPts: []   // [[n, |error|], ...] fixed-point run
                    property var idealPts: []   // same, ideal float arithmetic
                    property int nMax: 1
                    property real lsb: 0        // 2^-frac in fixed mode, 0 = no LSB line
                    property int fracBits: 0
                    property real tol: 0        // tolerance line, 0 = none
                    property int minN: 0        // marked min-iterations n, 0 = none
                    property string message: "Press Run."

                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    onPaint: drawPlot(getContext("2d"), width, height)

                    // Returns the x pixel of iteration count n inside the plot box.
                    function xPix(n, left, pw) {
                        return left + (nMax > 1 ? (n - 1) / (nMax - 1) : 0.5) * pw
                    }

                    // Returns the y pixel of error e on a log10 axis from 10^eLo to 10^eHi.
                    // Errors at or below 10^eLo (including exact 0) sit on the bottom edge.
                    function yPix(e, eLo, eHi, top, ph) {
                        let le = e > 0 ? Math.max(Math.log10(e), eLo) : eLo
                        return top + (eHi - le) / (eHi - eLo) * ph
                    }

                    // Draws one series as a line with dots. Draws on ctx only.
                    function drawSeries(ctx, pts, color, eLo, eHi, box) {
                        if (pts.length === 0)
                            return
                        ctx.strokeStyle = color
                        ctx.fillStyle = color
                        ctx.lineWidth = 2
                        ctx.beginPath()
                        for (let i = 0; i < pts.length; i++) {
                            let x = xPix(pts[i][0], box.l, box.w)
                            let y = yPix(pts[i][1], eLo, eHi, box.t, box.h)
                            if (i === 0)
                                ctx.moveTo(x, y)
                            else
                                ctx.lineTo(x, y)
                        }
                        ctx.stroke()
                        for (let j = 0; j < pts.length; j++) {
                            ctx.beginPath()
                            ctx.arc(xPix(pts[j][0], box.l, box.w),
                                    yPix(pts[j][1], eLo, eHi, box.t, box.h), 3, 0, 2 * Math.PI)
                            ctx.fill()
                        }
                    }

                    // Draws axes, log grid, both series, the 1-LSB and tolerance lines, the
                    // min-n marker and the legend. Shows `message` instead when it is not
                    // empty. Draws on ctx only.
                    function drawPlot(ctx, w, h) {
                        ctx.reset()
                        ctx.font = "12px Consolas"
                        if (message.length > 0) {
                            ctx.fillStyle = "#888888"
                            ctx.fillText(message, 16, 28)
                            return
                        }

                        let lo = Infinity, hi = 0
                        let all = idealPts.concat(fixedPts)
                        for (let i = 0; i < all.length; i++) {
                            if (all[i][1] > 0) {
                                lo = Math.min(lo, all[i][1])
                                hi = Math.max(hi, all[i][1])
                            }
                        }
                        if (lsb > 0) {
                            lo = Math.min(lo, lsb)
                            hi = Math.max(hi, lsb)
                        }
                        if (tol > 0) {
                            lo = Math.min(lo, tol)
                            hi = Math.max(hi, tol)
                        }
                        if (hi === 0) {     // every error exactly 0
                            lo = 1e-16
                            hi = 1
                        }
                        let eLo = Math.floor(Math.log10(lo))
                        let eHi = Math.ceil(Math.log10(hi))
                        if (eHi <= eLo)
                            eHi = eLo + 1

                        let box = { l: 64, t: 34, w: w - 64 - 20, h: h - 34 - 44 }

                        // Horizontal grid: one line per decade (thinned if many).
                        let eStep = Math.max(1, Math.ceil((eHi - eLo) / 12))
                        ctx.lineWidth = 1
                        for (let e = eLo; e <= eHi; e += eStep) {
                            let y = yPix(Math.pow(10, e), eLo, eHi, box.t, box.h)
                            ctx.strokeStyle = "#2a2a2a"
                            ctx.beginPath()
                            ctx.moveTo(box.l, y)
                            ctx.lineTo(box.l + box.w, y)
                            ctx.stroke()
                            ctx.fillStyle = "#aaaaaa"
                            ctx.fillText("1e" + e, 18, y + 4)
                        }

                        // Vertical grid: iteration counts.
                        let nStep = Math.max(1, Math.ceil(nMax / 16))
                        for (let n = 1; n <= nMax; n += nStep) {
                            let x = xPix(n, box.l, box.w)
                            ctx.strokeStyle = "#2a2a2a"
                            ctx.beginPath()
                            ctx.moveTo(x, box.t)
                            ctx.lineTo(x, box.t + box.h)
                            ctx.stroke()
                            ctx.fillStyle = "#aaaaaa"
                            ctx.fillText("" + n, x - 4, box.t + box.h + 16)
                        }

                        ctx.strokeStyle = "#777777"
                        ctx.strokeRect(box.l, box.t, box.w, box.h)
                        ctx.fillStyle = "#cccccc"
                        ctx.fillText("iterations n", box.l + box.w / 2 - 40, h - 8)
                        ctx.fillText("|error| (log)", 8, 18)

                        if (lsb > 0) {
                            let yl = yPix(lsb, eLo, eHi, box.t, box.h)
                            ctx.strokeStyle = "#ffb74d"
                            ctx.lineWidth = 1
                            ctx.setLineDash([6, 4])
                            ctx.beginPath()
                            ctx.moveTo(box.l, yl)
                            ctx.lineTo(box.l + box.w, yl)
                            ctx.stroke()
                            ctx.setLineDash([])
                            ctx.fillStyle = "#ffb74d"
                            ctx.fillText("1 LSB = 2^-" + fracBits, box.l + box.w - 120, yl - 6)
                        }

                        if (tol > 0) {
                            let yt = yPix(tol, eLo, eHi, box.t, box.h)
                            ctx.strokeStyle = "#ef5350"
                            ctx.lineWidth = 1
                            ctx.setLineDash([2, 3])
                            ctx.beginPath()
                            ctx.moveTo(box.l, yt)
                            ctx.lineTo(box.l + box.w, yt)
                            ctx.stroke()
                            ctx.setLineDash([])
                            ctx.fillStyle = "#ef5350"
                            ctx.fillText("max |error| = " + tol, box.l + 6, yt - 6)
                        }
                        if (minN > 0) {
                            let xm = xPix(minN, box.l, box.w)
                            ctx.strokeStyle = "#ef5350"
                            ctx.lineWidth = 2
                            ctx.beginPath()
                            ctx.moveTo(xm, box.t)
                            ctx.lineTo(xm, box.t + box.h)
                            ctx.stroke()
                            ctx.fillStyle = "#ef5350"
                            ctx.fillText("n = " + minN, Math.min(xm + 6, box.l + box.w - 50),
                                         box.t + 14)
                        }

                        drawSeries(ctx, idealPts, "#4fc3f7", eLo, eHi, box)
                        drawSeries(ctx, fixedPts, "#33ff66", eLo, eHi, box)

                        // Legend.
                        ctx.fillStyle = "#4fc3f7"
                        ctx.fillRect(box.l + 130, 10, 14, 3)
                        ctx.fillText("float (ideal)", box.l + 150, 16)
                        if (fixedPts.length > 0) {
                            ctx.fillStyle = "#33ff66"
                            ctx.fillRect(box.l + 270, 10, 14, 3)
                            ctx.fillText("fixed-point", box.l + 290, 16)
                        }
                    }
                }
            }
        }
    }
}
