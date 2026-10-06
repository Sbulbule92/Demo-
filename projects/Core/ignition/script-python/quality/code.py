"""
================================================================================
 Project Library Script : quality
 Ignition 8.3  (Jython 2.7)
================================================================================
 All logic for the Quality Checks screen lives here.
 Component events are one-liners that call these functions.

 DESIGN (pattern: data-only functions)
 -------------------------------------
 - All QC inputs on the view are bound BIDIRECTIONALLY to view.custom.qc.*
 - The flex repeater instances are bound BIDIRECTIONALLY to view.custom.wireRows
 - So the entire screen state = two custom props (qc + wireRows).
 - Library functions receive plain dicts/lists, never component references.
 - Only buildContext() touches the session (machine/line/shift/user).
 - All named-query calls go through _runNQ(), which passes the project name
   explicitly so calls work in BOTH Perspective and gateway scope.

 EXPECTED view.custom STRUCTURE
 ------------------------------
 view.custom.qc = {
     "coreShifted":  "",        <-> coreShifted dropdown   props.value
     "insThickness": False,     <-> chkThickness           props.selected
     "insWidth":     False,     <-> chkWidth               props.selected
     "longWound":    None,      <-> longWound              props.value
     "shortWound":   None,      <-> shortWound             props.value
     "comments":     ""         <-> comments text-area     props.text
 }
 view.custom.wireRows  = [ {index, manufacturer, lotNumber, coatingType,
                            diameter, width, thickness, tension}, ... ]
 view.custom.jobStatus = "IN_PROGRESS" | "COMPLETED"

 COMPONENT EVENT WIRING (one-liners)
 -----------------------------------
 btnAddWire        onActionPerformed:
     self.view.custom.wireRows = quality.addWireRow(list(self.view.custom.wireRows))

 root message handler "deleteWireRow" (page scope):
     self.view.custom.wireRows = quality.deleteWireRow(list(self.view.custom.wireRows), payload['index'])

 btnSave           onActionPerformed:
     quality.saveQualityCheck(self.view.params.jobId, dict(self.view.custom.qc),
                              [dict(r) for r in self.view.custom.wireRows],
                              quality.buildContext(self.session))

 btnJobComplete    onActionPerformed:
     done = quality.completeJob(self.view.params.jobId, dict(self.view.custom.qc),
                                [dict(r) for r in self.view.custom.wireRows],
                                quality.buildContext(self.session))
     if done: self.view.custom.jobStatus = 'COMPLETED'

 view onStartup:
     data = quality.loadQualityCheck(self.params.jobId)
     self.custom.qc        = data['qc']
     self.custom.wireRows  = data['wireRows']
     self.custom.jobStatus = data['status']

 Lock screen after completion: bind props.enabled of btnSave / btnAddWire /
 btnJobComplete / row delete to expression:
     {view.custom.jobStatus} != 'COMPLETED'
================================================================================
"""

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

NQ_UPSERT_QC    = "qc/InsertQualityCheck"
NQ_DELETE_WIRES = "qc/DeleteWiresForJob"
NQ_INSERT_WIRE  = "qc/InsertWire"
NQ_GET_QC       = "qc/GetQualityCheckWithWires"
NQ_COMPLETE     = "qc/MarkJobComplete"
# --- with the other NQ_ constants ---
NQ_MFR_OPTIONS     = "qc/GetManufacturerOptions"
NQ_COATING_OPTIONS = "qc/GetCoatingTypeOptions"

POPUP_VIEW = "Project/Pop-Up/Pop-up"
POPUP_ID   = "PopUp"

STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_COMPLETED   = "COMPLETED"

SHIFT_TAG = "[default]Current_Shift/shift_ID"

DEFAULT_WIRE_ROWS = 3



# Datasource for transactions. None = project default database.
# If your gateway has multiple datasources, put the exact name here,
# e.g.  DATASOURCE = "MES_DB"
DATASOURCE = None

LOGGER = system.util.getLogger("quality")

PROJECT = system.util.getProjectName()


# ------------------------------------------------------------------------------
# Named-query wrapper  (fixes scope ambiguity of system.db.runNamedQuery)
# ------------------------------------------------------------------------------
# runNamedQuery has two signatures:
#     Perspective scope : runNamedQuery(path, params)
#     Gateway scope     : runNamedQuery(project, path, params, tx)
# Called from a project library with tx, Ignition resolves the gateway form,
# so the path must be preceded by the project name or you get:
#     "argument path: expected String instance, got PyDictionary"
# This wrapper always supplies the project name explicitly.

def _runNQ(path, params, tx=None):
	if tx is None:
		return system.db.runNamedQuery(PROJECT, path, params)
	return system.db.runNamedQuery(PROJECT, path, params, tx=tx)


def _beginTx():
	"""Open a DB transaction on the configured datasource (or project default)."""
	if DATASOURCE:
		return system.db.beginTransaction(DATASOURCE, timeout=10000)
	return system.db.beginTransaction(timeout=10000)


# ------------------------------------------------------------------------------
# Blank-state factories  (also used by onStartup for brand-new jobs)
# ------------------------------------------------------------------------------

def blankQC():
	"""Empty qc dict matching the view.custom.qc structure."""
	return {
		"coreShifted":  "",
		"insThickness": False,
		"insWidth":     False,
		"longWound":    None,
		"shortWound":   None,
		"comments":     ""
	}


def blankWireRow(index):
	"""Empty wire row dict matching the repeater instance structure."""
	return {
		"index":        index,
		"manufacturer": "",
		"lotNumber":    "",
		"coatingType":  "",
		"diameter":     None,
		"width":        None,
		"thickness":    None,
		"tension":      None
	}


# ------------------------------------------------------------------------------
# Session context  (the ONLY function that touches the session)
# ------------------------------------------------------------------------------

def buildContext(session):
	"""
	Collect line / machine / shift / user once at the event call site.
	Returns a plain dict so everything downstream is data-only.
	"""
	return {
		"lineId":    session.custom.machineInfo.lineID,
		"machineId": session.custom.machineInfo.ID,
		"shiftId":   system.tag.readBlocking(SHIFT_TAG)[0].value,
		"username":  session.props.auth.user.userName
	}


# ------------------------------------------------------------------------------
# Wire row list manipulation  (pure functions: list in -> list out)
# ------------------------------------------------------------------------------

def addWireRow(rows):
	"""Append a blank row. Returns the new list (assign back to custom prop)."""
	rows = list(rows)
	rows.append(blankWireRow(len(rows) + 1))
	return rows


def deleteWireRow(rows, index):
	"""Remove row by its index value and renumber. Returns the new list."""
	rows = [dict(r) for r in rows if r["index"] != index]
	for i, r in enumerate(rows):
		r["index"] = i + 1
	return rows


# ------------------------------------------------------------------------------
# Popups
# ------------------------------------------------------------------------------

def _popup(action, primary, secondary=""):
	"""Standard project popup. action: 'success' | 'error'."""
	system.perspective.openPopup(POPUP_ID, view=POPUP_VIEW,
		params={
			"action":        action,
			"primaryText":   primary,
			"secondaryText": secondary,
			"label":         "quality check"
		},
		showCloseIcon=False,
		draggable=False,
		modal=True)


# ------------------------------------------------------------------------------
# Persistence
# ------------------------------------------------------------------------------

def saveQualityCheck(jobId, qc, wireRows, context, silent=False):
	"""
	Lenient draft save. Persists whatever is currently filled (nulls allowed).
	Upserts the quality_checks row; replaces the hv_wires set.
	Safe to call repeatedly - re-save updates the same rows.

	jobId    : str
	qc       : dict  (see blankQC for keys)
	wireRows : list of dicts (see blankWireRow for keys)
	context  : dict from buildContext(session)
	silent   : suppress the success popup (used internally by completeJob)

	Returns True on success, False on failure.
	"""
	if not jobId:
		if not silent:
			_popup("error", "Save failed", "Job ID is missing")
		return False

	tx = _beginTx()
	try:
		_runNQ(NQ_UPSERT_QC, {
			"jobId":        jobId,
			"lineId":       context["lineId"],
			"machineId":    context["machineId"],
			"shiftId":      context["shiftId"],
			"username":     context["username"],
			"coreShifted":  qc["coreShifted"],
			"insThickness": qc["insThickness"],
			"insWidth":     qc["insWidth"],
			"longWound":    qc["longWound"],
			"shortWound":   qc["shortWound"],
			"comments":     qc["comments"]
		}, tx=tx)

		# replace the wire set for this job so edits/deletes stay in sync
		_runNQ(NQ_DELETE_WIRES, {"jobId": jobId}, tx=tx)

		for r in wireRows:
			_runNQ(NQ_INSERT_WIRE, {
				"jobId":   jobId,
				"wireSeq": r["index"],
				"mfr":     r["manufacturer"],
				"lot":     r["lotNumber"],
				"coating": r["coatingType"],
				"dia":     r["diameter"],
				"width":   r["width"],
				"thick":   r["thickness"],
				"tension": r["tension"]
			}, tx=tx)

		system.db.commitTransaction(tx)
		LOGGER.info("Quality check saved for job %s (%d wires)" % (jobId, len(wireRows)))
		if not silent:
			_popup("success", "Saved successfully")
		return True

	except Exception, e:
		system.db.rollbackTransaction(tx)
		LOGGER.error("Save failed for job %s : %s" % (jobId, str(e)))
		if not silent:
			_popup("error", "Save failed", str(e))
		return False

	finally:
		system.db.closeTransaction(tx)


def loadQualityCheck(jobId):
	"""
	Read a job from DB. Returns a plain dict the view assigns to its
	custom props in onStartup:
	    { 'qc': {...}, 'wireRows': [...], 'status': 'IN_PROGRESS'|'COMPLETED' }
	A brand-new job (no DB row yet) returns blanks with IN_PROGRESS.
	"""
	result = {
		"qc":       blankQC(),
		"wireRows":  [blankWireRow(i + 1) for i in range(DEFAULT_WIRE_ROWS)],
		"status":   STATUS_IN_PROGRESS
	}
	if not jobId:
		return result

	ds = _runNQ(NQ_GET_QC, {"jobId": jobId})
	if ds.getRowCount() == 0:
		return result

	# QC fields repeat on every joined row - take row 0
	result["qc"] = {
		"coreShifted":  ds.getValueAt(0, "core_shifted") or "",
		"insThickness": bool(ds.getValueAt(0, "ins_thickness_ok")),
		"insWidth":     bool(ds.getValueAt(0, "ins_width_ok")),
		"longWound":    ds.getValueAt(0, "long_wound_in"),
		"shortWound":   ds.getValueAt(0, "short_wound_in"),
		"comments":     ds.getValueAt(0, "comments") or ""
	}
	result["status"] = ds.getValueAt(0, "status") or STATUS_IN_PROGRESS

	rows = []
	for i in range(ds.getRowCount()):
		# LEFT JOIN: wire columns are null if the job has no wires yet
		if ds.getValueAt(i, "wire_seq") is not None:
			rows.append({
				"index":        ds.getValueAt(i, "wire_seq"),
				"manufacturer": ds.getValueAt(i, "wire_manufacturer") or "",
				"lotNumber":    ds.getValueAt(i, "lot_number") or "",
				"coatingType":  ds.getValueAt(i, "coating_type") or "",
				"diameter":     ds.getValueAt(i, "round_wire_diameter"),
				"width":        ds.getValueAt(i, "width_inches"),
				"thickness":    ds.getValueAt(i, "thickness_inches"),
				"tension":      ds.getValueAt(i, "hv_wire_tension")
			})
	result["wireRows"] = rows
	return result


# ------------------------------------------------------------------------------
# Validation + completion
# ------------------------------------------------------------------------------

def validateQualityCheck(qc, wireRows):
	"""
	Strict completeness check used only by Job Complete.
	Pure function: dicts in, list of error strings out. Empty list = valid.
	NOTE: numeric fields treat 0 as 'not entered'. If 0 is ever a legitimate
	measured value for a field, change that field's check to 'is None'.
	"""
	errors = []

	if qc["coreShifted"] not in ("yes", "no"):
		errors.append("Core Visual Check: select Yes or No")
	if not qc["insThickness"]:
		errors.append("HV Insulation: Thickness check not confirmed")
	if not qc["insWidth"]:
		errors.append("HV Insulation: Width check not confirmed")
	if qc["longWound"] in (None, 0):
		errors.append("Coil Measurement: Long Wound is missing")
	if qc["shortWound"] in (None, 0):
		errors.append("Coil Measurement: Short Wound is missing")

	if len(wireRows) < 1:
		errors.append("HV Wire: at least one wire row is required")
	else:
		for r in wireRows:
			missing = []
			if not r["manufacturer"]:        missing.append("manufacturer")
			if not r["lotNumber"]:           missing.append("lot number")
			if not r["coatingType"]:         missing.append("coating type")
			if r["diameter"]  in (None, 0):  missing.append("diameter")
			if r["width"]     in (None, 0):  missing.append("width")
			if r["thickness"] in (None, 0):  missing.append("thickness")
			if r["tension"]   in (None, 0):  missing.append("tension")
			if missing:
				errors.append("Wire row %d: missing %s" % (r["index"], ", ".join(missing)))

	return errors


def completeJob(jobId, qc, wireRows, context):
	"""
	Validate everything; if valid, save final state then mark COMPLETED.
	Returns True if the job was completed (caller sets view.custom.jobStatus),
	False otherwise.
	"""
	errors = validateQualityCheck(qc, wireRows)
	if errors:
		_popup("error", "Cannot complete job", "\n".join(errors))
		return False

	# persist the final screen state first; its own popup suppressed
	if not saveQualityCheck(jobId, qc, wireRows, context, silent=True):
		return False

	try:
		_runNQ(NQ_COMPLETE, {
			"jobId":    jobId,
			"username": context["username"]
		})
	except Exception, e:
		LOGGER.error("MarkJobComplete failed for job %s : %s" % (jobId, str(e)))
		_popup("error", "Could not mark job complete", str(e))
		return False

	LOGGER.info("Job %s completed by %s" % (jobId, context["username"]))
	_popup("success", "Job completed successfully!")
	return True
	
	
#================================================================================================================================================================


# Minimum fully-filled wire rows for the wire section to be complete
MIN_WIRE_ROWS = 3

# Section status values
SEC_COMPLETED   = "COMPLETED"
SEC_PENDING     = "PENDING"      # partially filled
SEC_NOT_STARTED = "NOT_STARTED"


def _status(filledCount, totalCount):
	if filledCount == 0:
		return SEC_NOT_STARTED
	if filledCount < totalCount:
		return SEC_PENDING
	return SEC_COMPLETED


def coreVisualStatus(qc):
	return SEC_COMPLETED if qc["coreShifted"] in ("yes", "no") else SEC_NOT_STARTED


def insulationStatus(qc):
	filled = int(bool(qc["insThickness"])) + int(bool(qc["insWidth"]))
	return _status(filled, 2)


def coilStatus(qc):
	filled = int(qc["longWound"] not in (None, 0)) + int(qc["shortWound"] not in (None, 0))
	return _status(filled, 2)


def _wireRowFilled(r):
	"""True only if EVERY field of the row is filled."""
	return (bool(r["manufacturer"]) and bool(r["lotNumber"]) and bool(r["coatingType"])
	        and r["diameter"]  not in (None, 0)
	        and r["width"]     not in (None, 0)
	        and r["thickness"] not in (None, 0)
	        and r["tension"]   not in (None, 0))


def _wireRowTouched(r):
	"""True if ANY field of the row has something in it."""
	return (bool(r["manufacturer"]) or bool(r["lotNumber"]) or bool(r["coatingType"])
	        or r["diameter"] or r["width"] or r["thickness"] or r["tension"])


def wireStatus(wireRows):
	"""
	COMPLETED   : at least MIN_WIRE_ROWS rows, every existing row fully filled
	PENDING     : something entered but not yet meeting the above
	NOT_STARTED : nothing entered anywhere
	"""
	rows = [dict(r) for r in wireRows]
	if not any(_wireRowTouched(r) for r in rows):
		return SEC_NOT_STARTED
	if len(rows) >= MIN_WIRE_ROWS and all(_wireRowFilled(r) for r in rows):
		return SEC_COMPLETED
	return SEC_PENDING


def allSectionStatuses(qc, wireRows):
	"""One call returning every section status - bind targets read from this."""
	return {
		"coreVisual": coreVisualStatus(qc),
		"wires":      wireStatus(wireRows),
		"insulation": insulationStatus(qc),
		"coil":       coilStatus(qc)
	}
	
	
	
	
# ------------------------------------------------------------------------------
# Dropdown option lists  (wire manufacturer / coating type)
# ------------------------------------------------------------------------------

def getManufacturerOptions():
	"""Active wire manufacturers as Perspective dropdown options."""
	ds = _runNQ(NQ_MFR_OPTIONS, {})
	return [{"value": ds.getValueAt(i, "ManufacturerName"),
	         "label": ds.getValueAt(i, "ManufacturerName")}
	        for i in range(ds.getRowCount())]


def getCoatingTypeOptions():
	"""Active coating types as Perspective dropdown options."""
	ds = _runNQ(NQ_COATING_OPTIONS, {})
	return [{"value": ds.getValueAt(i, "CoatingTypeName"),
	         "label": ds.getValueAt(i, "CoatingTypeName")}
	        for i in range(ds.getRowCount())]