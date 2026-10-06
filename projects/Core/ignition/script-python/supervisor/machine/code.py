def getBooleanTagDuration(machine_id, startTime, endTime):
    """
    Calculate ON and OFF duration (in minutes) for a boolean historian tag.

    Args:
        tagPath   (str)      : Full tag path e.g. '[default]Machines/Machine1/Running'
        startTime (Date)     : Start of query window
        endTime   (Date)     : End of query window

    Returns:
        dict: {'on_minutes': float, 'off_minutes': float, 'total_minutes': float}
    """
    logger = system.util.getLogger("BooleanTagDuration")

    try:
    	if machine_id is not None:
		    logger.debug("machine_id is not None, fetching basePath for machine_id={}".format(machine_id))
		
		    # Get the tag base path for this machine from the database
		    query    = "Machines/GetMachineByID"
		    data     = system.db.execQuery(path=query, parameters={"ID": machine_id})
		    basePath = data.getValueAt(0, "basePath")
		    logger.debug("basePath resolved: {}".format(basePath))
    	
    	tagPath = '[default]' + basePath + '/MachineData/AutomaticMode'
        # No aggregationMode, no interval = raw stored values (every state change)
        results = system.tag.queryTagHistory(
            paths        = [tagPath],
            startDate    = startTime,
            endDate      = endTime,
            returnSize   = -1,
            returnFormat = "Wide"
        )

        rowCount    = results.rowCount
        colCount    = results.columnCount
        colNames    = [results.getColumnName(c) for c in range(colCount)]

        # --- DIAGNOSTIC: Print dataset shape ---
#        print("rowCount  : {}".format(rowCount))
#        print("colCount  : {}".format(colCount))
#        print("columns   : {}".format(colNames))
#
#        if rowCount == 0:
#            print("ERROR: No rows returned. Possible causes:")
#            print("  1. Tag path is wrong (check provider name and spelling)")
#            print("  2. History not enabled on this tag")
#            print("  3. No data exists in the given time range")
#            return {'on_minutes': 0.0, 'off_minutes': 0.0, 'total_minutes': 0.0}

        # --- DIAGNOSTIC: Print first 5 rows ---
        print("--- First 5 rows ---")
        for i in range(min(5, rowCount)):
            ts  = results.getValueAt(i, 0)
            val = results.getValueAt(i, 1)
#            print("  row[{}] ts={} | value={} | type={}".format(
#                i, ts, val, type(val)
#            ))

        on_ms  = 0.0
        off_ms = 0.0

        for i in range(rowCount):
            currentTime  = results.getValueAt(i, 0)
            currentValue = results.getValueAt(i, 1)

            if i < rowCount - 1:
                nextTime = results.getValueAt(i + 1, 0)
            else:
                nextTime = endTime

            # Guard: skip rows where value or timestamp is None
            if currentTime is None or currentValue is None:
                print("WARN: None value at row {}, skipping.".format(i))
                continue

            segmentMs = nextTime.getTime() - currentTime.getTime()

            if segmentMs < 0:
                print("WARN: Negative segment at row {}, skipping.".format(i))
                continue

            if currentValue:
                on_ms  += segmentMs
            else:
                off_ms += segmentMs

        MS_PER_MIN    = 60000.0
        on_minutes    = round(on_ms  / MS_PER_MIN, 3)
        off_minutes   = round(off_ms / MS_PER_MIN, 3)
        total_minutes = round((on_ms + off_ms) / MS_PER_MIN, 3)

        print("RESULT -> ON: {} | OFF: {} | Total: {}".format(
            on_minutes, off_minutes, total_minutes
        ))

        return {
            'on_minutes'   : on_minutes,
            'off_minutes'  : off_minutes,
            'total_minutes': total_minutes
        }

    except Exception as e:
        import traceback
        print("EXCEPTION: {}".format(str(e)))
        print(traceback.format_exc())       # <-- Full stack trace
        return {'on_minutes': 0.0, 'off_minutes': 0.0, 'total_minutes': 0.0}