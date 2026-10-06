from java.util import Date

# Logger for this script module
logger = system.util.getLogger("OEE_Dashboard.IdealVsActual")

def getMaxDate(dataset, dateColumnName):
    """
    Returns the maximum date value from a specified column in a dataset.
    
    Args:
        dataset: Ignition dataset to search through
        dateColumnName: Name of the date column to evaluate
    
    Returns:
        The maximum Date object found, or None if all values are null
    """
    maxDate = None
    
    for row in range(dataset.rowCount):
        cellValue = dataset.getValueAt(row, dateColumnName)
        # Skip null values
        if cellValue is not None:
            # Update maxDate if current cell is later than the current max
            if maxDate is None or cellValue.after(maxDate):
                maxDate = cellValue
    
    return maxDate


def getIdealVsActualData(startTime, endTime, machineid):
    """
    Calculates ideal vs actual production time for each serial number
    within the given shift window.

    Handles 4 cases based on where actual_start and actual_end fall
    relative to the shift window [startTime, endTime]:
        1. Both inside  → full ideal time
        2. Both outside → full ideal time (uses shift change data)
        3. Start inside, End outside → partial ideal time based on WIP at shift end
        4. Start outside, End inside → partial ideal time based on WIP at shift start

    Args:
        startTime: Shift start datetime
        endTime:   Shift end datetime
        machineid: ID of the machine (used in production query)

    Returns:
        List of dicts with keys: serial_number, id, actual_time, ideal_time
    """

    # Named query path for fetching production data
    p_query = 'OEE_Dashboard/getProductionData'
    p_params = {
        "MachineID": machineid,
        "StartTime": startTime,
        "EndTime"  : endTime
    }

    # Execute production data query
    p_data = system.db.execQuery(path=p_query, parameters=p_params)

    index = 0
    data  = []
    logger = system.util.getLogger("oee")
    if p_data is not None and p_data.rowCount > 0:
        for row in p_data:
            # Log key row info for traceability
            logger.debug("Processing serial_number: " + str(row["serial_number"]))
            logger.debug("actual_start: " + str(row["actual_start"]))
            logger.debug("actual_end: "   + str(row["actual_end"]))

            # Default ideal time to the full winding minutes for this part
            ideal_time = row["hv_winding_minutes"]

            # Default WIP percentage (100% = full production within shift)
            m_wip = 100

            # Named query paths for event history and shift change data
            e_query = 'OEE_Dashboard/New/Get_EventHistory_By_SerialNumber'
            s_query = 'OEE_Dashboard/New/Get_ShiftChangeData'
            params  = {"SerialNumber": row["serial_number"]}
            
            actual_start = row["actual_start"] if row["actual_start"] is not None else row["effective_start"]
            actual_end = row["actual_end"] if row["actual_end"] is not None else row["effective_end"]

            # ── Case 1: Both actual_start and actual_end are within the shift window ──
            if (system.date.isBetween(actual_start, startTime, endTime) and
                system.date.isBetween(actual_end,   startTime, endTime)):

                # Full part produced within this shift → use full ideal time
                ideal_time = row["hv_winding_minutes"]
                logger.debug("Case 1 (fully inside shift) - serial: " + str(row["serial_number"]))

            # ── Case 2: Both actual_start and actual_end are outside the shift window ──
            elif (not system.date.isBetween(actual_start, startTime, endTime) and
                  not system.date.isBetween(actual_end, startTime, endTime)):

                # Part spans across this shift entirely → use full ideal time
                ideal_time = row["hv_winding_minutes"]
                logger.debug("Case 2 (fully outside shift) - serial: " + str(row["serial_number"]))

                # Fetch shift change data to log shift boundary events
#                s_data = system.db.execQuery(path=s_query, parameters=params)
#                for item in s_data:
#                    logger.debug("Shift change CreatedOn: " + str(item["CreatedOn"]))

            # ── Case 3: actual_start is inside shift, actual_end is outside (crosses shift end) ──
            elif (system.date.isBetween(actual_start, startTime, endTime) and
                  not system.date.isBetween(actual_end, startTime, endTime)):

                s_data = system.db.execQuery(path=s_query, parameters=params)

                if s_data is not None and s_data.rowCount > 0:
                    for item in s_data:
                        # Check for a shift change record just after shift end (within 1 minute)
                        nextShift = system.date.addMinutes(endTime, 1)
                        if system.date.isBetween(item["CreatedOn"], endTime, nextShift):
                            wip        = item["WIP"]
                            m_wip      = wip

                            # Prorate ideal time by WIP% completed within this shift
                            ideal_time = (float(row["hv_winding_minutes"]) * wip) / 100
                            ratio      = ideal_time / row["winding_minutes"]

                            logger.debug("Case 3 - WIP ratio: " + str(ratio))
                            logger.debug("Case 3 - Max shift change date: " + str(getMaxDate(s_data, "CreatedOn")))
                else:
                    # No shift change data → fall back to event history for last known state
                    e_data = system.db.execQuery(path=e_query, parameters=params)
                    logger.debug("Case 3 fallback - Max event update_time: " + str(getMaxDate(e_data, "update_time")))

            # ── Case 4: actual_start is outside shift, actual_end is inside (crosses shift start) ──
            elif (not system.date.isBetween(actual_start, startTime, endTime) and
                  system.date.isBetween(actual_end, startTime, endTime)):

                s_data = system.db.execQuery(path=s_query, parameters=params)

                if s_data is not None and s_data.rowCount > 0:
                    for item in s_data:
                        # Check for a shift change record just after shift start (within 1 minute)
                        pastShift = system.date.addMinutes(startTime, 1)
                        if system.date.isBetween(item["CreatedOn"], startTime, pastShift):
                            # Invert WIP% → portion remaining to be done in this shift
                            wip        = 100 - item["WIP"]
                            m_wip      = wip

                            # Prorate ideal time by remaining WIP% in this shift
                            ideal_time = (float(row["hv_winding_minutes"]) * wip) / 100
                            ratio      = ideal_time / row["winding_minutes"]

                            logger.debug("Case 4 - WIP ratio: " + str(ratio))
                            logger.debug("Case 4 - Max shift change date: " + str(getMaxDate(s_data, "CreatedOn")))
                else:
                    # No shift change data → fall back to event history for last known state
                    e_data = system.db.execQuery(path=e_query, parameters=params)
                    logger.debug("Case 4 fallback - Max event update_time: " + str(getMaxDate(e_data, "update_time")))

            # Build result row for this serial number
            content = {
                "serial_number": row["serial_number"],
                "id"           : index + 1,
                "actual_time"  : row["winding_minutes"],
                "ideal_time"   : int(ideal_time),
                "wip"          : m_wip,
                "ratio"        : float(ideal_time/row["winding_minutes"]) if float(ideal_time/row["winding_minutes"])<= 1 else 1
            }
            data.append(content)
            index += 1
    return data

def getPerformance(startTime, endTime, machineid):
	data = getIdealVsActualData(startTime, endTime, machineid)
	ActualProdCount = 0 
	p = 0
	for row in data:
		ActualProdCount = ActualProdCount + row["ratio"]
	if len(data)>0 and ActualProdCount <>0:
		p = (ActualProdCount/len(data))* 100
	return p