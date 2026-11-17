"""Qt bridge between SimWindow.qml and sim_runner (cordic-sim-py)."""

from PySide6.QtCore import Property, QObject, Slot

from sim_runner import FUNCS, formatDuration, fpgaCycles, fpgaTime, simulateTimed


class SimBackend(QObject):
    """Stateless: QML calls run() with the form values and shows the returned texts."""

    # === SELECTOR ===

    def _getFuncs(self):
        """Returns the function names cordic-sim-py supports, in display order."""
        return list(FUNCS)

    funcs = Property("QVariantList", _getFuncs, constant=True)

    # === SIMULATION ===

    @Slot(str, str, int, bool, int, int, float, result="QVariantMap")
    def run(self, func, t_text, n, use_fixed, frac, width, clock_mhz):
        """Returns {"report": iteration table, "timing": one-line Python time + FPGA estimate}.

        On invalid form values report is "Error: ..." and timing is "". A bad clock only
        blanks the FPGA part of timing. No side effects.
        """
        try:
            report, seconds = simulateTimed(func, t_text, n, use_fixed, frac, width)
        except ValueError as err:
            return {"report": f"Error: {err}.", "timing": ""}
        timing = f"Python compute: {formatDuration(seconds)}"
        try:
            fpga = formatDuration(fpgaTime(n, clock_mhz))
            timing += (f"    |    FPGA estimate: {fpgaCycles(n)} cycles @ {clock_mhz:g} MHz"
                       f" = {fpga}  (iterative: 1 load + {n} iterations)")
        except ValueError as err:
            timing += f"    |    FPGA estimate: {err}"
        return {"report": report, "timing": timing}
