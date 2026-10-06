import json
project="Core"    
def sync_ecs_op_status(startDate, endDate):
    # 1. Fetch from ERP
	inprgress_status=["ECS_Sync/op_status_sync_inprogress"]
	system.tag.writeBlocking(inprgress_status,[True])
	params = {"startDate": startDate, "endDate": endDate}
	erp_ds = system.db.execQuery("ecs/OP_status/get_op_status_from_ecs", params)
	if erp_ds.getRowCount() == 0:
		return 0
	logger = system.util.getLogger("OPSTATUS_SYNC")	
	try:
		
		deletData=system.db.execUpdate("ecs/OP_status/ClearStagingTable")
		data = system.dataset.toPyDataSet(erp_ds)
		
		# 🔹 Step 2: Convert dataset → JSON
		rows = []
		
		for row in data:
		    rows.append({"SerialNumber": row["SerialNumber"],
        "OP_Status": int(row["OP_Status"]),
      "Scheduled_Start":system.date.format(row["Scheduled_Start"], "yyyy-MM-dd HH:mm:ss"),
       "ECS_AWAIT": bool(row["ECS_AWAIT"])})
		
		# 🔹 Step 3: Convert to JSON string
		jsonData = json.dumps(rows)
		
		# 🔹 Step 4: Call Stored Procedure
		result = system.db.runPrepQuery("EXEC dbo.sp_Insert_stg_ecs_op_status_JSON @json = ?",[jsonData])
		
		# 🔹 Step 5: Handle response
		if result.getRowCount() > 0:
		    status = result.getValueAt(0, "Status")
		    message = result.getValueAt(0, "Message")
		    count = result.getValueAt(0, "RowsInserted")
		
		    if status == 1:
		    	syncstatus=system.db.execQuery("ecs/OP_status/ProcessStaging")
		    	if syncstatus.getRowCount() > 0:
				    status = syncstatus.getValueAt(0, "Status")
				    message = syncstatus.getValueAt(0, "Message")
				    system.tag.writeBlocking(["ECS_Sync/Opstatus_last_sync_status"], [syncstatus])
				    if status == 1 :
				    	return 1
				#logger.info("Pass: " + message+ str(count))
				#pass
		    else:
		        logger.error("FAILED: " + message)
		
		else:
		    logger.warn("No response from stored procedure")
	
	except Exception as e:
	    logger.error("IGNITION ERROR: " + str(e))
	finally:
		system.tag.writeBlocking(inprgress_status,[False])


def sync_new_workorders(startDate,endDate):
	
	logger = system.util.getLogger("WO_SYNC")
	inprgress_status=["[default]ECS_Sync/WO_sync_inprogress"]
	system.tag.writeBlocking(inprgress_status,[True])
	try:
		params = {"startDate": startDate, "endDate": endDate}
		ds = system.db.execQuery("ecs/workorder/GetECSWorkOrdersByDate", params)
		if ds.getRowCount() == 0:
			logger.info("No data from source")
			return 0
		deletData=system.db.execUpdate("ecs/workorder/ClearStagingTable")
		pyData = system.dataset.toPyDataSet(ds)
		rows = []
		
		# 🔹 Step 3: Build JSON
		for row in pyData:
		    rows.append({
		         "ExternalId": row["ExternalId"],
		        "SerialNumber": row["SerialNumber"],
		        "Item": row["Item"],
		        "Scheduled_Start": system.date.format(row["Scheduled_Start"], "yyyy-MM-dd HH:mm:ss"),
		        "Serial_Status": row["Serial_Status"],
		        "OP_Status": row["OP_Status"],
		        "XFRMR_Serial": row[ "XFRMR_Serial"],
		        "ECS_AWAIT":row["ECS_AWAIT"]
		    })
		
		jsonData = json.dumps(rows)
		
		# 🔹 Step 4: Insert into staging via SP
		result = system.db.runPrepQuery(
		    "EXEC dbo.sp_Insert_stg_WorkOrder_JSON @json = ?",
		    [jsonData]
		)
		
		# 🔹 Step 5: Handle response
		if result.getRowCount() > 0:
		    status = result.getValueAt(0, "Status")
		    count = result.getValueAt(0, "Count")
		    error = result.getValueAt(0, "ErrorMessage")
		
		    if status == 1:
		    	logger.info("SUCCESS → Rows Inserted: " + str(count))
		    	#return 1
		    	syncstatus=system.db.execQuery("ecs/workorder/ProcessStaging")
		    	if syncstatus.getRowCount() > 0:
				    status = syncstatus.getValueAt(0, "Status")
				    message = syncstatus.getValueAt(0, "ErrorMessage")
				    system.tag.writeBlocking(["ECS_Sync/wo_last_sync_status"], [syncstatus])
				    if status == 1 :
				    	logger.info("success → " + str(message))
				    	return 1
		
		    else:
		        logger.error("FAILED → " + str(error))
		else:
		    logger.warn("No response from SP")
	
	except Exception as e:
	    logger.error("IGNITION ERROR: " + str(e))
	finally :
		system.tag.writeBlocking(inprgress_status,[False])	
	
def synclspec_from_ECS(startDate,endDate):
	
	inprgress_status=["ECS_Sync/lspec_sync_inprogress"]
	system.tag.writeBlocking(inprgress_status,[True])
	params = {"startDate": startDate, "endDate": endDate}
	erp_ds = system.db.execQuery("ecs/lspec/GetLspecfromecs", params) 
	if erp_ds.getRowCount() == 0:
		return 0
	logger = system.util.getLogger("LSPEC_SYNC")	
	try:
		
		deletData=system.db.execUpdate("ecs/lspec/ClearStagingTable")
		data = system.dataset.toPyDataSet(erp_ds)
		
		# 🔹 Step 2: Convert dataset → JSON
		rows = []
		
		for row in data:
		    rows.append({
		        "LSPEC": row["LSPEC"],
		        "LV_Winding": row["LV_Winding"] or None,
		        "HV_Winding": row["HV_Winding"] or None,
		        "Total_Coil_Time": row["Total_Coil_Time"] or None,
		        "Total_Winding_Time": row["Total_Winding_Time"] or None,
		        "Source": row["Source"] or None,
		        "KVA": row["KVA"] or None,
		        "hv1_bil": row["hv1_bil"] or None,
		        "PRODCOMP": row["PRODCOMP"] or None
		    })
		
		# 🔹 Step 3: Convert to JSON string
		jsonData = json.dumps(rows)
		
		# 🔹 Step 4: Call Stored Procedure
		result = system.db.runPrepQuery("EXEC dbo.sp_Insert_stg_lspec_JSON @json = ?",[jsonData])
		
		# 🔹 Step 5: Handle response
		if result.getRowCount() > 0:
		    status = result.getValueAt(0, "Status")
		    message = result.getValueAt(0, "Message")
		    count = result.getValueAt(0, "RowsInserted")
		
		    if status == 1:
		    	syncstatus=system.db.execQuery("ecs/lspec/ProcessStaging")
		    	if syncstatus.getRowCount() > 0:
				    status = syncstatus.getValueAt(0, "Status")
				    message = syncstatus.getValueAt(0, "ErrorMessage")
				    system.tag.writeBlocking(["ECS_Sync/lspec_last_sync_status"], [syncstatus])
				    if status == 1 :
				    	return 1
		    else:
		        logger.error("FAILED: " + message)
		
		else:
		    logger.warn("No response from stored procedure")
	
	except Exception as e:
	    logger.error("IGNITION ERROR: " + str(e))
	finally:
		system.tag.writeBlocking(inprgress_status,[False])

		
def sync_xfr_status_from_ECS():
    logger = system.util.getLogger("XFR_SYNC")
    inprgress_status=["ECS_Sync/xfr_status_sync_inprogress"]
    system.tag.writeBlocking(inprgress_status,[True])
    try:
        # 🔹 Step 1: Fetch data (Named Query)
        ds = system.db.execQuery("ecs/XFR_status/GetStatus")

        if ds.getRowCount() == 0:
            logger.info("No data from source")
            return 0
        deletData=system.db.execUpdate("ecs/XFR_status/ClearStagingTable")
        pyData = system.dataset.toPyDataSet(ds)
        rows = []

        # 🔹 Step 3: Build JSON
        for row in pyData:
            rows.append({
                "XFR_Serial_Number": row["XFR_Serial_Number"],
                "Tank_Status": row["Tank_Status"] or "Ready",
                "Core_Status": row["Core_Status"] or "Ready"
            })

        jsonData = json.dumps(rows)

        # 🔹 Step 4: Insert into staging via SP
        result = system.db.runPrepQuery(
            "EXEC dbo.sp_Insert_stg_xfr_status_JSON @json = ?",
            [jsonData]
        )

        # 🔹 Step 5: Handle response
        if result.getRowCount() > 0:
            status = result.getValueAt(0, "Status")
            count = result.getValueAt(0, "Count")
            error = result.getValueAt(0, "ErrorMessage")

            if status == 1:
            	logger.info("SUCCESS → Rows Inserted: " + str(count))
            	syncstatus=system.db.execQuery("ecs/XFR_status/ProcessStaging")
            	if syncstatus.getRowCount() > 0:
				    status = syncstatus.getValueAt(0, "Status")
				    message = syncstatus.getValueAt(0, "ErrorMessage")
				    system.tag.writeBlocking(["ECS_Sync/xfr_last_sync_status"], [syncstatus])
				    if status == 1 :
				    	return 1

            else:
                logger.error("FAILED → " + str(error))
        else:
            logger.warn("No response from SP")

    except Exception as e:
        logger.error("IGNITION ERROR: " + str(e))
    finally :
		system.tag.writeBlocking(inprgress_status,[False])
