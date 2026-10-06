import json

def dataset_to_json(dataset):
    """Convert Ignition dataset to a list of dicts (not a string)."""
    headers = [dataset.getColumnName(i) for i in range(dataset.getColumnCount())]
    return [
        {col: dataset.getValueAt(row, col) for col in headers}
        for row in range(dataset.getRowCount())
    ]

def getAllMachines():
    query = "Shift Overview/GetAllMachines"
    try:
        data = system.db.execQuery(query)
        return dataset_to_json(data)
    except Exception as e:
        system.util.getLogger("MachineUtils").error("getAllMachines failed: " + str(e))
        return []

def getCountOfTotalMachines(Line="All"):
	machines = getAllMachines()
	if Line == "All":
	    return len(machines)
	else:
		totalMachines = 0
		for item in machines:
			if item["LineID"]==Line:
				totalMachines+=1
		return totalMachines
    
def getActiveMachines(Line="All"):
    machines = getAllMachines()
    totalMachine = len(machines)
    
    if totalMachine == 0:
        return (0, 0.0)
    
    if Line == "All":
        activeMachines = [m for m in machines if m["IsActive"] == True]
        count = len(activeMachines)
        percent = (float(count) / float(totalMachine)) * 100
        return count, percent
    else:
        activeMachines = [m for m in machines if m["LineID"] == Line and m["IsActive"] == True]
        count = len(activeMachines)
        percent = (float(count) / float(totalMachine)) * 100
        return count, percent

    
def getOperatorPresenceAtMachine(Line="All"):
    logger = system.util.getLogger("OperatorPresence")
    
    try:
        machines = getAllMachines()
        totalMachine = len(machines)
        
        if totalMachine == 0:
            return (0, 0.0)
        
        SESSION_TAG = "/Session_status/Session_Active"
        
        # Filter machines for the line if needed
        if Line == "All":
            filtered = [m for m in machines if m.get("basePath")]
        else:
            filtered = [m for m in machines 
                       if m.get("LineID") == Line 
                       and m.get("IsActive") == True
                       and m.get("basePath")]
        
        if not filtered:
            return (0, 0.0)
        
        # Build all tag paths and read in ONE batch call
        paths = [m["basePath"] + SESSION_TAG for m in filtered]
        
        try:
            tagResults = system.tag.readBlocking(paths)
        except Exception as e:
            logger.error("Tag read failed: " + str(e))
            return (0, 0.0)
        
        # Count machines where operator is present
        operatorPresence = 0
        for i, result in enumerate(tagResults):
            try:
                if result.quality.isGood() and result.value == True:
                    operatorPresence += 1
            except Exception as e:
                logger.warn("Bad tag result at index " + str(i) + ": " + str(e))
                continue
        
        denominator = float(totalMachine if Line == "All" else len(filtered))
        percent = (float(operatorPresence) / denominator) * 100 if operatorPresence > 0 else 0.0
        
        return operatorPresence, percent

    except Exception as e:
        logger.error("getOperatorPresenceAtMachine failed: " + str(e))
        return (0, 0.0)
        
def getInhibitEnabledMachines(Line="All"):
    logger = system.util.getLogger("OperatorPresence")
    
    try:
        machines = getAllMachines()
        totalMachine = len(machines)
        
        if totalMachine == 0:
            return (0, 0.0)
        
        SESSION_TAG = "/Machine Block/MachineBlock"
        
        # Filter machines for the line if needed
        if Line == "All":
            filtered = [m for m in machines if m.get("basePath")]
        else:
            filtered = [m for m in machines 
                       if m.get("LineID") == Line 
                       and m.get("IsActive") == True
                       and m.get("basePath")]
        
        if not filtered:
            return (0, 0.0)
        
        # Build all tag paths and read in ONE batch call
        paths = [m["basePath"] + SESSION_TAG for m in filtered]
        
        try:
            tagResults = system.tag.readBlocking(paths)
        except Exception as e:
            logger.error("Tag read failed: " + str(e))
            return (0, 0.0)
        
        # Count machines where operator is present
        operatorPresence = 0
        for i, result in enumerate(tagResults):
            try:
                if result.quality.isGood() and result.value == True:
                    operatorPresence += 1
            except Exception as e:
                logger.warn("Bad tag result at index " + str(i) + ": " + str(e))
                continue
        
        denominator = float(totalMachine if Line == "All" else len(filtered))
        percent = (float(operatorPresence) / denominator) * 100 if operatorPresence > 0 else 0.0
        
        return operatorPresence, percent

    except Exception as e:
        logger.error("getOperatorPresenceAtMachine failed: " + str(e))
        return (0, 0.0)
        
        
def getMachineStatus(Line="All"):
    logger = system.util.getLogger("MachineStatus")
    try:
        machines = getAllMachines()
        totalMachine = len(machines)
        
        if totalMachine == 0:
            return []
#        [default]Sec 511/UDT_WOCL_1071_OEE/Machine Block/MachineBlockOveride
        BLOCK_TAG   = "/Machine Block/MachineBlockOveride"
        COIL_TAG    = "/WO/serial_number"
        WIP_TAG     = "/ProductionData/WIP"
        SESSION_TAG = "/Session_status/Session_Active"
#        DOWNTIME_TAG = "/Downtime/Ongoingbreakdown"
#        DOWNTIME_DURATION ="/Downtime/ActiveTime"
        
        # Filter machines — always check IsActive and basePath
        if Line == "All":
            filtered = [m for m in machines 
                       if m.get("basePath") 
                       and m.get("IsActive") == True]
        else:
            filtered = [m for m in machines
                       if m.get("LineID") == Line
                       and m.get("IsActive") == True
                       and m.get("basePath")]
        
        if not filtered:
            logger.info("No active machines found for Line: " + str(Line))
            return []
        
        # Build all tag paths in one flat list — 4 tags per machine
        paths = []
        for m in filtered:
            base = m["basePath"]
            paths.append(base + BLOCK_TAG)
            paths.append(base + COIL_TAG)
            paths.append(base + WIP_TAG)
            paths.append(base + SESSION_TAG)
#            paths.append(base + DOWNTIME_TAG)
#            paths.append(base + DOWNTIME_DURATION)
        
        try:
            tagResults = system.tag.readBlocking(paths)
        except Exception as e:
            logger.error("Tag read failed: " + str(e))
            return []
        
        # tagResults is flat — step through 4 at a time
        result = []
        for i, m in enumerate(filtered):
            idx = i * 4
            try:
                blockResult   = tagResults[idx]
                coilResult    = tagResults[idx + 1]
                wipResult     = tagResults[idx + 2]
                sessionResult = tagResults[idx + 3]
#                downtime      = tagResults[idx + 4]
#                downtime_duration = tagResults[idx + 5]
                
                result.append({
                    "MachineCode"   : m.get("MachineCode"),
                    "LineID"        : m.get("LineID"),
                    "IsActive"      : m.get("IsActive"),
                    "BasePath"      : m.get("basePath"),
                    "MachineBlock"  : blockResult.value   if blockResult.quality.isGood()   else None,
                    "SerialNumber"  : coilResult.value    if coilResult.quality.isGood()    else None,
                    "WIP"           : wipResult.value     if wipResult.quality.isGood()     else None,
                    "SessionActive" : sessionResult.value if sessionResult.quality.isGood() else None
                })
            except Exception as e:
                logger.warn("Failed to process machine " + str(m.get("MachineCode")) + ": " + str(e))
                continue
        
        return result

    except Exception as e:
        logger.error("getMachineStatus failed: " + str(e))
        return []
        
        
def logInhibitChange(machineName, line, previousValue, modifiedValue, modifiedBy, reason):
    logger = system.util.getLogger("InhibitLog")
    query = """
        INSERT INTO tbl_MachineInhibitLogs 
            (MachineName, Line, PreviousValue, ModifiedValue, ModifiedBy, Reason)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    DATABASE = "Ignition_DEV-WOCL-Ignition"
    args = [machineName, line, previousValue, modifiedValue, modifiedBy, reason]
    
    try:
        rows = system.db.runPrepUpdate(query, args )
#        system.db.runPrepUpdate(query, args, database, tx, getKey, skipAudit)
        if rows > 0:
            return 1
        else:
            logger.warn("Insert affected 0 rows for machine: " + str(machineName))
            return 0
    except Exception as e:
        logger.error("logInhibitChange failed: " + str(e))
        return 0