logger = system.util.getLogger("PlannedDowntime")

def getLid(basePath, reasonID):
	logIdPath = "/Downtime/planned downtime/meeting/LogId" if reasonID <> 20 else "/Downtime/planned downtime/cleaning/LogId"
	LogIDTag  = basePath + logIdPath
	lId       = system.tag.readBlocking(LogIDTag)[0].value
	return lId, LogIDTag


def start(reasonID):
	logger.debug("start() called with reasonID={}".format(reasonID))
	try:
		machineInfo = machine.getAllmachineinfo()
		if len(machineInfo) == 0:
			logger.warn("start() - No machine info found")
			return
		for row in machineInfo:
			basePath        = row["basePath"]
			planneddtstatus = system.tag.readBlocking([basePath + "/Downtime/Planned_downtime"])[0].value
			cat             = "/Downtime/planned downtime/meeting/Active" if reasonID <> 20 else "/Downtime/planned downtime/cleaning/Active"
			plannedCat      = basePath + cat
			if planneddtstatus == False:
				logger.info("start() - Setting Planned_downtime=True for basePath={}".format(basePath))
				system.tag.writeBlocking([basePath + "/Downtime/Planned_downtime", plannedCat], [True, True])
			else:
				logger.debug("start() - Already True, skipping basePath={}".format(basePath))
	except Exception as e:
		logger.error("start() - Exception: {}".format(str(e)))


def stop():
	"""Only called once at the very end — after meeting update. Sets Planned_downtime=False."""
	logger.debug("stop() called")
	try:
		machineInfo = machine.getAllmachineinfo()
		if len(machineInfo) == 0:
			logger.warn("stop() - No machine info found")
			return
		for row in machineInfo:
			basePath        = row["basePath"]
			planneddtstatus = system.tag.readBlocking([basePath + "/Downtime/Planned_downtime"])[0].value
			if planneddtstatus == True:
				logger.info("stop() - Resetting Planned_downtime=False for basePath={}".format(basePath))
				system.tag.writeBlocking([basePath + "/Downtime/Planned_downtime"], [False])
			else:
				logger.debug("stop() - Already False for basePath={}".format(basePath))
	except Exception as e:
		logger.error("stop() - Exception: {}".format(str(e)))


def insert(reasonID, shiftID):
	"""
	Inserts planned downtime for ALL machines.
	shiftID passed explicitly so we use the correct shift (not re-read mid-rollover).
	Guarded by lId==0 — will not double-insert.
	"""
	logger.debug("insert() called with reasonID={}, shiftID={}".format(reasonID, shiftID))
	try:
		machineInfo = machine.getAllmachineinfo()
		if len(machineInfo) == 0:
			logger.warn("insert() - No machine info found")
			return
		for row in machineInfo:
			basePath  = row["basePath"]
			MachineID = row["MachineID"]
			LineID    = row["LineID"]

			sessionPath   = basePath + "/Session_status/Session_Active"
			SessionActive = system.tag.readBlocking(sessionPath)[0].value
			lId, LogIDTag = getLid(basePath, reasonID)

			logger.debug("insert() - MachineID={}, SessionActive={}, lId={}".format(MachineID, SessionActive, lId))

			if not SessionActive and lId == 0:
				parameters = {
					"ShiftID"        : shiftID,
					"LineID"         : LineID,
					"MachineID"      : MachineID,
					"ReasonID"       : reasonID,
					"StartTime"      : system.date.now(),
					"DowntimeStatus" : 1,
					"categoryID"     : 2,
					"username"       : "System",
					"DowntimeSource" : 1,
					"Remarks"        : "Cleaning" if reasonID == 20 else "Meeting"
				}
				logger.info("insert() - Inserting for MachineID={}, ReasonID={}".format(MachineID, reasonID))
				query  = "downtime/InsertPlannedDtEntryBySystem"
				result = system.db.execQuery(path=query, parameters=parameters)
				logger.debug("insert() - Query returned {} rows".format(len(result)))

				if len(result) > 0:
					newLogID   = result.getValueAt(0, "LogID")
					catPath    = "/Downtime/planned downtime/meeting/Active" if reasonID <> 20 else "/Downtime/planned downtime/cleaning/Active"
					plannedCat = basePath + catPath
					logger.info("insert() - Success. LogID={} for MachineID={}".format(newLogID, MachineID))
					system.tag.writeBlocking([plannedCat, LogIDTag], [True, newLogID])
				else:
					logger.warn("insert() - No rows returned for MachineID={}".format(MachineID))
			else:
				logger.debug("insert() - Skipping MachineID={}: SessionActive={}, lId={}".format(MachineID, SessionActive, lId))
	except Exception as e:
		logger.error("insert() - Exception: {}".format(str(e)))


def update(reasonID, resetPlannedDT=False):
	"""
	Updates EndTime + resets category/LogId tags for ALL machines.
	resetPlannedDT=False → keep Planned_downtime=True  (after cleaning, meeting still coming)
	resetPlannedDT=True  → set  Planned_downtime=False (after meeting, 30min window done)
	Guarded by lID>0 — will not double-update.
	"""
	logger.debug("update() called with reasonID={}, resetPlannedDT={}".format(reasonID, resetPlannedDT))
	try:
		machineInfo = machine.getAllmachineinfo()
		if len(machineInfo) == 0:
			logger.warn("update() - No machine info found")
			return
		for row in machineInfo:
			basePath  = row["basePath"]
			MachineID = row["MachineID"]
			lID, LogIDTag = getLid(basePath, reasonID)
			logger.debug("update() - MachineID={}, lID={}".format(MachineID, lID))

			if lID > 0:
				parameters = {"LogID": lID, "EndTime": system.date.now()}
				logger.info("update() - Updating LogID={} for MachineID={}".format(lID, MachineID))
				result = system.db.execUpdate(path="downtime/UpdateDowntimeCompletion", parameters=parameters)
				logger.debug("update() - execUpdate result={}".format(result))

				if result == 1:
					catPath    = "/Downtime/planned downtime/meeting/Active" if reasonID <> 20 else "/Downtime/planned downtime/cleaning/Active"
					plannedCat = basePath + catPath
					if resetPlannedDT:
						plannedDtTag = basePath + "/Downtime/Planned_downtime"
						logger.info("update() - Full reset (Planned_downtime=False) for MachineID={}".format(MachineID))
						system.tag.writeBlocking([plannedCat, LogIDTag, plannedDtTag], [False, 0, False])
					else:
						logger.info("update() - Partial reset (Planned_downtime stays True) for MachineID={}".format(MachineID))
						system.tag.writeBlocking([plannedCat, LogIDTag], [False, 0])
				else:
					logger.warn("update() - execUpdate returned {} for MachineID={}".format(result, MachineID))
			else:
				logger.debug("update() - lID=0, nothing to update for MachineID={}".format(MachineID))
	except Exception as e:
		logger.error("update() - Exception: {}".format(str(e)))


def plannedDT():
	"""
	Gateway Timer Script — run every 1 minute.

	Windows (all based on CURRENT shift tags at time of execution):

	  CLEANING INSERT : [ShiftEnd - 15min] → [ShiftEnd - 1min]
	  CLEANING UPDATE : [ShiftEnd -  1min] → [ShiftEnd]          (1 min before shift flips)

	  MEETING  INSERT : [ShiftStart + 1min] → [ShiftStart + 15min]  (1 min after shift flips)
	  MEETING  UPDATE : outside meeting window AND meetingLid > 0

	Timeline:
	  17:45 → cleaningInsertWindow=True  → start(20) + insert(20)
	  17:59 → cleaningUpdateWindow=True  → update(20, resetPlannedDT=False)  [tags not flipped yet]
	  18:00 → SHIFT FLIPS → ShiftStart=18:00, ShiftEnd=02:00
	  18:01 → meetingInsertWindow=True   → start(21) + insert(21)  [reads new shift tags]
	  18:15 → meetingInsertWindow=False, meetingLid>0 → update(21, resetPlannedDT=True) + stop()
	"""
	logger.debug("plannedDT() called")
	now = system.date.now()
	logger.info("plannedDT() - now={}".format(system.date.format(now, "yyyy-MM-dd HH:mm:ss")))

	machineInfo = machine.getAllmachineinfo()
	if len(machineInfo) == 0:
		logger.warn("plannedDT() - No machine info, skipping")
		return

	# Read current shift tags (whatever shift is active RIGHT NOW)
	shiftdata = system.tag.readBlocking(["Current_Shift/Start_time", "Current_Shift/End_time", "[default]Current_Shift/shift_ID"])
	rawStart  = shiftdata[0].value
	rawEnd    = shiftdata[1].value
	shiftID   = shiftdata[2].value
	logger.debug("plannedDT() - ShiftID={}, Start={}, End={}".format(shiftID, rawStart, rawEnd))

	shiftStart = system.date.parse(rawStart, "yyyy-MM-dd HH:mm:ss.SSS")
	shiftEnd   = system.date.parse(rawEnd,   "yyyy-MM-dd HH:mm:ss.SSS")

	# ── Define all 4 windows ──────────────────────────────────────────────────

	# CLEANING: insert from [ShiftEnd-15] to [ShiftEnd-1]
	cleaningInsertStart = system.date.addMinutes(shiftEnd, -15)
	cleaningInsertEnd   = system.date.addMinutes(shiftEnd,  -1)

	# CLEANING: update from [ShiftEnd-1] to [ShiftEnd]  ← before shift flips
	cleaningUpdateStart = system.date.addMinutes(shiftEnd, -1)
	cleaningUpdateEnd   = shiftEnd

	# MEETING: insert from [ShiftStart+1] to [ShiftStart+15]  ← after shift flips
	meetingInsertStart  = system.date.addMinutes(shiftStart,  1)
	meetingInsertEnd    = system.date.addMinutes(shiftStart, 15)

	logger.info("plannedDT() - Cleaning INSERT window : {} → {}".format(
		system.date.format(cleaningInsertStart, "HH:mm:ss"),
		system.date.format(cleaningInsertEnd,   "HH:mm:ss")
	))
	logger.info("plannedDT() - Cleaning UPDATE window : {} → {}".format(
		system.date.format(cleaningUpdateStart, "HH:mm:ss"),
		system.date.format(cleaningUpdateEnd,   "HH:mm:ss")
	))
	logger.info("plannedDT() - Meeting  INSERT window : {} → {}".format(
		system.date.format(meetingInsertStart, "HH:mm:ss"),
		system.date.format(meetingInsertEnd,   "HH:mm:ss")
	))

	# ── Read lIds from first machine as representative ─────────────────────────
	firstBasePath  = machineInfo[0]["basePath"]
	cleaningLid, _ = getLid(firstBasePath, 20)
	meetingLid,  _ = getLid(firstBasePath, 21)
	logger.debug("plannedDT() - cleaningLid={}, meetingLid={}".format(cleaningLid, meetingLid))

	# ── CLEANING INSERT ────────────────────────────────────────────────────────
	inCleaningInsert = system.date.isBetween(now, cleaningInsertStart, cleaningInsertEnd)
	logger.debug("plannedDT() - inCleaningInsert={}".format(inCleaningInsert))

	if inCleaningInsert :
		logger.info("plannedDT() - [CLEANING INSERT] → start(20) + insert(20)")
		downtime.Planned.start(20)
		downtime.Planned.insert(20, shiftID)

	elif inCleaningInsert :
		logger.debug("plannedDT() - [CLEANING INSERT] Already inserted (lId={}), skipping".format(cleaningLid))

	# ── CLEANING UPDATE ────────────────────────────────────────────────────────
	# Runs 1 min before shift end — shift tags still show OLD shift
	inCleaningUpdate = system.date.isBetween(now, cleaningUpdateStart, cleaningUpdateEnd)
	logger.debug("plannedDT() - inCleaningUpdate={}, cleaningLid={}".format(inCleaningUpdate, cleaningLid))

	if inCleaningUpdate :
		# resetPlannedDT=False → keep Planned_downtime=True for upcoming meeting
		logger.info("plannedDT() - [CLEANING UPDATE] → update(20, resetPlannedDT=False)")
		downtime.Planned.update(20, resetPlannedDT=False)

	elif inCleaningUpdate :
		logger.warn("plannedDT() - [CLEANING UPDATE] In update window but cleaningLid=0, insert may have been missed!")

	# ── MEETING INSERT ─────────────────────────────────────────────────────────
	# Starts 1 min after shift start — shift tags have now flipped to NEW shift
	inMeetingInsert = system.date.isBetween(now, meetingInsertStart, meetingInsertEnd)
	logger.debug("plannedDT() - inMeetingInsert={}, meetingLid={}".format(inMeetingInsert, meetingLid))

	if inMeetingInsert :
		logger.info("plannedDT() - [MEETING INSERT] → start(21) + insert(21)")
		downtime.Planned.start(21)
		downtime.Planned.insert(21, shiftID)  # shiftID is now NEW shift

	elif inMeetingInsert :
		logger.debug("plannedDT() - [MEETING INSERT] Already inserted (lId={}), skipping".format(meetingLid))

	# ── MEETING UPDATE ─────────────────────────────────────────────────────────
	# Outside meeting insert window AND lId still set → meeting window ended
	afterMeetingInsert = system.date.isAfter(now, meetingInsertEnd)
	logger.debug("plannedDT() - afterMeetingInsert={}, meetingLid={}".format(afterMeetingInsert, meetingLid))

	if afterMeetingInsert and meetingLid > 0 :
		# resetPlannedDT=True → this is final step, set Planned_downtime=False
		logger.info("plannedDT() - [MEETING UPDATE] → update(21, resetPlannedDT=True) + stop()")
		downtime.Planned.update(21, resetPlannedDT=True)
		downtime.Planned.stop()

	logger.debug("plannedDT() - Completed")