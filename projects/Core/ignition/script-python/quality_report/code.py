"""
================================================================================
 Project Library Script : quality_report   (v2 - real schema)
 Ignition 8.3  (Jython 2.7)
================================================================================
 Jobs Quality Check Report screen.

 DATA SOURCES (confirmed from the database walkthrough)
 ------------------------------------------------------
 work_orders     wo.serial_number  = the Job ID  (joins to quality_checks.job_id)
                 wo.program_name, wo.actual_start, wo.actual_end,
                 wo.scheduled_start, wo.StartUser, wo.machine_id
 quality_checks  qc.job_id, qc.status (IN_PROGRESS/COMPLETED/FAILED),
                 qc.line_id, qc.machine_id, qc.created_by, ...
 hv_wires        one row per wire per job
 tbl_Line        LineID, LineCode
 tbl_Machine     MachineID, MachineCode, LineID

 Report base = work_orders LEFT JOIN quality_checks:
   - a work order with NO qc row  -> Overall Status = Not Started
   - qc.status IN_PROGRESS        -> Pending
   - qc.status COMPLETED          -> Completed
   - qc.status FAILED             -> Failed
 Job Status is derived from work order timestamps:
   actual_end set -> Completed ; actual_start set -> In Progress ; else Not Started

 EVENT WIRING (already inside the view JSON)
 -------------------------------------------
 view onStartup            : set defaultFilters, send 'loadReport'
 root handler 'loadReport' : loadReport(filters) -> rows/counts/options
 Apply Filters             : send 'loadReport'
 Clear                     : filters = defaultFilters(), send 'loadReport'
 table onRowClick          : openJob(dict(event.value))
 Export to Excel           : exportExcel(filters, rows)  -> 3-sheet workbook
================================================================================
"""

NQ_REPORT          = "qc/GetJobsReport"
NQ_LINE_OPTIONS    = "qc/GetLineOptions"
NQ_MACHINE_OPTIONS = "qc/GetMachineOptions"
NQ_EXPORT          = "qc/GetExportData"

# Quality Checks entry screen. Default: popup (matches the operator screen).
QC_VIEW_PATH = "Project/Supervisor/Quality/Quality Check/Quality Checks"
# If you navigate to a page instead, set QC_PAGE and use the navigate line
# inside openJob().
QC_PAGE = "/quality-check/:jobId"

DATE_FMT = "MM/dd/yyyy hh:mm a"
DEFAULT_RANGE_DAYS = 30

LOGGER  = system.util.getLogger("quality_report")
PROJECT = system.util.getProjectName()


def _runNQ(path, params):
	return system.db.runNamedQuery(PROJECT, path, params)


def _fmt(d):
	return system.date.format(d, DATE_FMT) if d else ""


# ------------------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------------------

def defaultFilters():
	now = system.date.now()
	return {
		"startDate": system.date.addDays(system.date.midnight(now), -DEFAULT_RANGE_DAYS),
		"endDate":   now,
		"lineId":    None,
		"machineId": None,
		"qcStatus":  None
	}


def _nqFilterParams(filters):
	"""Translate None ('All') UI values into the NQ sentinel values."""
	return {
		"startDate": filters.get("startDate") or system.date.addDays(system.date.now(), -DEFAULT_RANGE_DAYS),
		"endDate":   filters.get("endDate") or system.date.now(),
		"lineId":    filters.get("lineId") if filters.get("lineId") is not None else -1,
		"machineId": filters.get("machineId") if filters.get("machineId") is not None else -1,
		"qcStatus":  filters.get("qcStatus") or "ALL"
	}


# ------------------------------------------------------------------------------
# Report load
# ------------------------------------------------------------------------------

_QC_DISPLAY = {
	"COMPLETED":   "Completed",
	"IN_PROGRESS": "Pending",
	"FAILED":      "Failed",
	"NOT_STARTED": "Not Started"
}


def loadReport(filters):
	"""Run the filtered report; return rows + KPI counts + dropdown options."""
	ds = _runNQ(NQ_REPORT, _nqFilterParams(filters))

	rows = []
	counts = {"total": 0, "completed": 0, "pending": 0, "failed": 0, "notStarted": 0}

	for i in range(ds.getRowCount()):
		qcStatus = ds.getValueAt(i, "qc_status")   # NOT_STARTED already derived in SQL
		rows.append({
			"jobId":     ds.getValueAt(i, "job_id"),
			"program":   ds.getValueAt(i, "program_name") or "",
			"line":      ds.getValueAt(i, "line_code") or "",
			"machine":   ds.getValueAt(i, "machine_code") or "",
			"jobStart":  _fmt(ds.getValueAt(i, "job_start")),
			"jobEnd":    _fmt(ds.getValueAt(i, "job_end")),
			"operator":  ds.getValueAt(i, "operator") or "",
			"jobStatus": ds.getValueAt(i, "job_status") or "",
			"qcStatus":  _QC_DISPLAY.get(qcStatus, qcStatus)
		})
		counts["total"] += 1
		if qcStatus == "COMPLETED":
			counts["completed"] += 1
		elif qcStatus == "IN_PROGRESS":
			counts["pending"] += 1
		elif qcStatus == "FAILED":
			counts["failed"] += 1
		else:
			counts["notStarted"] += 1

	lds = _runNQ(NQ_LINE_OPTIONS, {})
	lineOptions = [{"value": lds.getValueAt(i, "LineID"),
	                "label": lds.getValueAt(i, "LineCode")}
	               for i in range(lds.getRowCount())]

	lineId = filters.get("lineId") if filters.get("lineId") is not None else -1
	mds = _runNQ(NQ_MACHINE_OPTIONS, {"lineId": lineId})
	machineOptions = [{"value": mds.getValueAt(i, "MachineID"),
	                   "label": mds.getValueAt(i, "MachineCode")}
	                  for i in range(mds.getRowCount())]

	LOGGER.info("Report loaded: %d rows" % counts["total"])
	return {"rows": rows, "counts": counts,
	        "lineOptions": lineOptions, "machineOptions": machineOptions}


# ------------------------------------------------------------------------------
# Row click -> open the Quality Checks screen for that job
# ------------------------------------------------------------------------------

def openJob(rowValue):
	jobId = rowValue["jobId"]
	system.perspective.openPopup("qcPopup",
		view=QC_VIEW_PATH,
		params={"jobId": jobId},
		showCloseIcon=False, draggable=False, modal=True)
	# Page-navigation alternative:
	# system.perspective.navigate(page=QC_PAGE.replace(":jobId", jobId))


# ------------------------------------------------------------------------------
# Export to Excel  (3 sheets)
# ------------------------------------------------------------------------------
#  Sheet 1  Jobs Summary    : exactly the on-screen table rows
#  Sheet 2  Quality Checks  : every QC field, one row per serial number
#  Sheet 3  HV Wires        : every wire row, with its serial number
# All sheets respect the SAME filters currently applied on screen.

def exportExcel(filters, screenRows):
	# ---- Sheet 1 : what the operator sees ----
	h1 = ["Job ID", "Program", "Line", "Machine", "Job Start Time",
	      "Job End Time", "Operator", "Job Status", "Overall Status"]
	d1 = [[r["jobId"], r["program"], r["line"], r["machine"], r["jobStart"],
	       r["jobEnd"], r["operator"], r["jobStatus"], r["qcStatus"]]
	      for r in screenRows]
	ds1 = system.dataset.toDataSet(h1, d1)

	# ---- Sheets 2+3 : full QC + wire detail per serial number ----
	eds = _runNQ(NQ_EXPORT, _nqFilterParams(filters))

	h2 = ["Serial Number (Job ID)", "Line", "Machine", "Shift",
	      "Core Shifted", "Insulation Thickness OK", "Insulation Width OK",
	      "Long Wound (in)", "Short Wound (in)", "Comments", "QC Status",
	      "Created By", "Created At", "Completed By", "Completed At"]
	h3 = ["Serial Number (Job ID)", "Wire #", "Manufacturer", "Lot Number",
	      "Coating Type", "Round Wire Dia (in)", "Width (in)",
	      "Thickness (in)", "HV Tension (lbs)"]

	d2, d3, seenQC = [], [], set()
	for i in range(eds.getRowCount()):
		jobId = eds.getValueAt(i, "job_id")

		# QC sheet: one row per serial number (export query repeats qc per wire)
		if jobId not in seenQC:
			seenQC.add(jobId)
			d2.append([
				jobId,
				eds.getValueAt(i, "line_code") or "",
				eds.getValueAt(i, "machine_code") or "",
				eds.getValueAt(i, "shift_id"),
				eds.getValueAt(i, "core_shifted") or "",
				eds.getValueAt(i, "ins_thickness_ok"),
				eds.getValueAt(i, "ins_width_ok"),
				eds.getValueAt(i, "long_wound_in"),
				eds.getValueAt(i, "short_wound_in"),
				eds.getValueAt(i, "comments") or "",
				_QC_DISPLAY.get(eds.getValueAt(i, "status"), eds.getValueAt(i, "status") or ""),
				eds.getValueAt(i, "created_by") or "",
				_fmt(eds.getValueAt(i, "created_at")),
				eds.getValueAt(i, "completed_by") or "",
				_fmt(eds.getValueAt(i, "completed_at"))
			])

		# Wire sheet: one row per wire
		if eds.getValueAt(i, "wire_seq") is not None:
			d3.append([
				jobId,
				eds.getValueAt(i, "wire_seq"),
				eds.getValueAt(i, "wire_manufacturer") or "",
				eds.getValueAt(i, "lot_number") or "",
				eds.getValueAt(i, "coating_type") or "",
				eds.getValueAt(i, "round_wire_diameter"),
				eds.getValueAt(i, "width_inches"),
				eds.getValueAt(i, "thickness_inches"),
				eds.getValueAt(i, "hv_wire_tension")
			])

	ds2 = system.dataset.toDataSet(h2, d2)
	ds3 = system.dataset.toDataSet(h3, d3)

	xlsxBytes = system.dataset.toExcel(True, [ds1, ds2, ds3])
	fileName = "QualityCheckReport_%s.xlsx" % system.date.format(system.date.now(), "yyyyMMdd_HHmm")
	system.perspective.download(fileName, xlsxBytes)
	LOGGER.info("Exported: %d summary rows, %d QC rows, %d wire rows"
	            % (len(d1), len(d2), len(d3)))
	            
	            
def machineValidForLine(machineId, machineOptions):
	"""True if the selected machine is in the current line's option list."""
	if machineId is None:
		return True
	return any(o["value"] == machineId for o in machineOptions)
	


# ------------------------------------------------------------------------------
# Single-job QC status lookup
# ------------------------------------------------------------------------------

NQ_JOB_STATUS = "qc/GetJobQcStatus"     # put with the other NQ_ constants at the top


def getJobQcStatus(jobId, display=True):
	
	"""
	Quality check status for one serial number (jobId).
	Returns 'COMPLETED' / 'IN_PROGRESS' / 'FAILED' / 'NOT_STARTED'
	(or the display form when display=True). No QC record -> NOT_STARTED.
	"""
	if not jobId:
		raw = "NOT_STARTED"
	else:
		ds = system.db.runNamedQuery("qc/GetJobQcStatus", {"jobId": jobId})
		raw = ds.getValueAt(0, 0)   # row 0, column 0 - works regardless of column name

	return _QC_DISPLAY.get(raw, raw) if display else raw
#	return ds