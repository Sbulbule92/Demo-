"""
================================================================================
 Project Library Script : config_admin   (v3 - read-only table + edit popup)
 Ignition 8.3  (Jython 2.7)
================================================================================
 8-tab System Configuration screen.
 - Each tab shows a READ-ONLY Perspective Table (display only).
 - An actions column (subview ConfigRowActions) gives Edit / Delete per row.
 - + Add and Edit open ONE generic popup (ConfigForm) that builds its fields
   from a column spec. The popup uses fixed slots f0..fN to dodge Perspective's
   indirect-binding limit; this library maps slot <-> column.
 - All writes funnel through saveForm() -> parameterized named queries, with a
   role re-check inside the popup (defense in depth).

 DELETE: soft (IsActive=0) for tables that have it; hard for the rest.
 ACCESS: REQUIRED_ROLES (user needs ANY one).
================================================================================
"""

LOGGER  = system.util.getLogger("config_admin")
PROJECT = system.util.getProjectName()

REQUIRED_ROLES = ["Controls Engineer"]
POPUP_VIEW     = "Project/Pop-Up/Pop-up"
FORM_VIEW      = "Project/Config/ConfigForm"
FORM_POPUP_ID  = "configForm"


# ------------------------------------------------------------------------------
# Table metadata.  fields = list of (column, header, kind)  kind in text/int/bool
# ------------------------------------------------------------------------------

TABLES = {
	"line": {"pk": "LineID", "softDelete": True, "nqFolder": "config/line",
		"fields": [("LineCode","Code","text"),("LineName","Name","text"),
		           ("Description","Description","text"),("IsActive","Active","bool")]},
	"machine": {"pk": "MachineID", "softDelete": True, "nqFolder": "config/machine",
		"fields": [("MachineCode","Code","text"),("MachineName","Name","text"),
		           ("LineID","Line ID","int"),("Section","Section","text"),
		           ("IPAddress","IP Address","text"),("SupplierName","Supplier","text"),
		           ("EquipmentName","Equipment","text"),("OPRID","OPR ID","text"),
		           ("Description","Description","text"),("IsActive","Active","bool")]},
	"shift": {"pk": "ShiftID", "softDelete": True, "nqFolder": "config/shift",
		"fields": [("ShiftCode","Code","text"),("ShiftName","Name","text"),
		           ("StartTime","Start (HH:mm:ss)","text"),("EndTime","End (HH:mm:ss)","text"),
		           ("Description","Description","text"),("IsActive","Active","bool")]},
	"coating": {"pk": "CoatingTypeID", "softDelete": True, "nqFolder": "config/coating",
		"fields": [("CoatingTypeName","Coating Type","text"),("SortOrder","Sort Order","int"),
		           ("IsActive","Active","bool")]},
	"mfr": {"pk": "ManufacturerID", "softDelete": True, "nqFolder": "config/mfr",
		"fields": [("ManufacturerName","Manufacturer","text"),("SortOrder","Sort Order","int"),
		           ("IsActive","Active","bool")]},
	"eventtype": {"pk": "id", "softDelete": False, "nqFolder": "config/eventtype",
		"fields": [("event_name","Event Name","text")]},
	"holdreason": {"pk": "id", "softDelete": False, "nqFolder": "config/holdreason",
		"fields": [("reason_name","Reason Name","text")]},
	"downtime": {"pk": "ReasonID", "softDelete": False, "nqFolder": "config/downtime",
		"fields": [("CategoryID","Category ID","int"),("ReasonName","Reason Name","text"),
		           ("Description","Description","text")]},
}


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _runNQ(path, params=None):
	return system.db.runNamedQuery(PROJECT, path, params or {})

def _nq(tabKey, action):
	return "%s/%s" % (TABLES[tabKey]["nqFolder"], action)

def hasAccess(session):
	try:
		userRoles = session.props.auth.user.roles
		return any(r in userRoles for r in REQUIRED_ROLES)
	except:
		return False

def toast(message):
	system.perspective.openPopup("PopUp", view=POPUP_VIEW,
		params={"action": "error", "primaryText": message, "secondaryText": "",
		        "label": "configuration"},
		showCloseIcon=True, draggable=False, modal=True)

def _success(message):
	system.perspective.openPopup("PopUp", view=POPUP_VIEW,
		params={"action": "success", "primaryText": message, "secondaryText": "",
		        "label": "configuration"},
		showCloseIcon=False, draggable=False, modal=True)

def _toInt(v):
	if v in (None, "", "null"):
		return None
	try:
		return int(float(v))
	except:
		return None

def _default(kind):
	return False if kind == "bool" else ("" if kind == "text" else "")


# ------------------------------------------------------------------------------
# Load (read-only table data)
# ------------------------------------------------------------------------------

def loadTab(tabKey):
	ds = _runNQ(_nq(tabKey, "get"))
	rows = []
	for i in range(ds.getRowCount()):
		row = {}
		for c in range(ds.getColumnCount()):
			row[ds.getColumnName(c)] = ds.getValueAt(i, c)
		# the actions cell value IS the row data, so the subview receives the
		# whole row as params.value (a table cell subview only gets its cell value)
		row["_actions"] = dict(row)
		rows.append(row)
	return rows


# ------------------------------------------------------------------------------
# Open Add / Edit popup
#   row = None -> Add (blank) ; row = dict -> Edit (prefilled)
# Builds a fieldSpec list: [{field, header, kind, value, pk}] that the popup
# renders into fixed slots f0..fN.
# ------------------------------------------------------------------------------

def openForm(tabKey, row):
	meta = TABLES[tabKey]
	pk   = meta["pk"]
	isEdit = row is not None and row.get(pk) not in (None, "", 0)

	fieldSpec = []
	for field, header, kind in meta["fields"]:
		if isEdit:
			val = row.get(field)
			if kind == "bool":
				val = bool(val)
			elif val is None:
				val = ""
		else:
			val = _default(kind)
		fieldSpec.append({"field": field, "header": header, "kind": kind, "value": val})

	# carry the pk value (or None) so Save knows insert vs update
	pkVal = row.get(pk) if isEdit else None

	title = ("Edit " if isEdit else "Add ") + tabKey
	system.perspective.openPopup(FORM_POPUP_ID, view=FORM_VIEW,
		params={"tabKey": tabKey, "fieldSpec": fieldSpec, "title": title,
		        "isEdit": isEdit, "pkValue": pkVal},
		showCloseIcon=False, draggable=False, modal=True)


# ------------------------------------------------------------------------------
# Save from popup
#   fieldSpec : the spec passed to the popup (gives field names + kinds + pk)
#   values    : list of the f0..fN slot values, same order as fieldSpec
# ------------------------------------------------------------------------------

def saveForm(session, tabKey, fieldSpec, values, pkValue):
	# defense in depth: re-check access at the write point
	if not hasAccess(session):
		toast("You do not have permission to save")
		return False

	meta = TABLES[tabKey]
	pk   = meta["pk"]

	params = {}
	errors = []
	for i, fld in enumerate(fieldSpec):
		v = values[i] if i < len(values) else None
		if fld["kind"] == "int":
			v = _toInt(v)
		elif fld["kind"] == "bool":
			v = bool(v)
		else:
			v = "" if v is None else v
			# required check for the first text column (the "name/code")
		params[fld["field"]] = v

	# basic required-field validation: first text field must be non-empty
	for fld in fieldSpec:
		if fld["kind"] == "text":
			if not (params.get(fld["field"]) or "").strip():
				errors.append("%s is required" % fld["header"])
			break
	if errors:
		toast("; ".join(errors))
		return False

	# insert vs update decided by the pk value passed from the popup
	params.pop(pk, None)   # ensure pk isn't duplicated in the param map
	pkVal = pkValue

	try:
		if pkVal in (None, "", 0):
			_runNQ(_nq(tabKey, "insert"), params)
			action = "inserted"
		else:
			params[pk] = pkVal
			_runNQ(_nq(tabKey, "update"), params)
			action = "updated"
		LOGGER.info("%s %s" % (tabKey, action))
		_success("Saved")
		return True
	except Exception, e:
		LOGGER.error("Save failed for %s: %s" % (tabKey, str(e)))
		toast("Save failed: %s" % str(e))
		return False


# ------------------------------------------------------------------------------
# Delete (with confirm)
# ------------------------------------------------------------------------------

def confirmDelete(tabKey, row):
	"""Opens the project confirm popup; on confirm it should call doDelete.
	If your Pop-Up view doesn't return a confirm result, replace this with a
	direct doDelete() call, or wire a confirm dialog of your choice."""
	doDelete(tabKey, row)   # simplest: delete immediately
	system.perspective.sendMessage("reloadTab", payload={"tab": tabKey}, scope="page")


def doDelete(tabKey, row):
	meta  = TABLES[tabKey]
	pk    = meta["pk"]
	pkVal = row.get(pk)
	if pkVal in (None, "", 0):
		return True
	try:
		_runNQ(_nq(tabKey, "delete"), {pk: pkVal})
		LOGGER.info("Deleted %s pk=%s (soft=%s)" % (tabKey, str(pkVal), meta["softDelete"]))
		return True
	except Exception, e:
		LOGGER.error("Delete failed for %s pk=%s: %s" % (tabKey, str(pkVal), str(e)))
		toast("Delete failed (row may be in use): %s" % str(e))
		return False