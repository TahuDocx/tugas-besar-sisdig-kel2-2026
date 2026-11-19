"""Qt bridge between SimWindow.qml and sim_runner (cordic-sim-py)."""

from PySide6.QtCore import Property, QObject, Slot

from sim_runner import (FUNCS, errorSweep, formatDuration, fpgaCycles, fpgaTime, minIterations,
                        simulateTimed)


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

    @Slot(str, str, int, bool, int, int, str, result="QVariantMap")
    def sweep(self, func, t_text, n_max, use_fixed, frac, width, tol_text):
        """Returns the error-vs-iterations data for n = 1 .. n_max (errorSweep) as
        {"fixed": [[n, err], ...], "ideal": [[n, err], ...], "error": text,
         "tol": float, "minFixed": int, "minIdeal": int, "tolError": text}.

        "fixed" is [] when use_fixed is False; "ideal" is always the ideal-arithmetic
        reference. minFixed/minIdeal are minIterations(series, tol): smallest n whose error
        stays <= tol up to n_max, 0 = not reached. On invalid form values both lists are []
        and error is "Error: ..."; on a bad tolerance tol is 0, both mins are 0 and tolError
        says why. No side effects.
        """
        out = {"fixed": [], "ideal": [], "error": "", "tol": 0.0, "minFixed": 0, "minIdeal": 0,
               "tolError": ""}
        try:
            out["ideal"] = errorSweep(func, t_text, n_max, False, frac, width)
            if use_fixed:
                out["fixed"] = errorSweep(func, t_text, n_max, True, frac, width)
        except ValueError as err:
            out["ideal"], out["fixed"] = [], []
            out["error"] = f"Error: {err}."
            return out
        try:
            tol = float(tol_text.strip())
            out["minIdeal"] = minIterations(out["ideal"], tol)
            out["minFixed"] = minIterations(out["fixed"], tol)
            out["tol"] = tol
        except ValueError:
            out["minIdeal"], out["minFixed"] = 0, 0
            out["tolError"] = "tolerance must be a finite number > 0"
        return out
