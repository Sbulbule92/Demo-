def getAllmachineinfo():
	try:
		allmachineinfo = system.db.execQuery("Machines/GetAllMachines")
		if allmachineinfo.getRowCount() == 0:
	#logger.info("No data from source")
			return 0
		return 	system.dataset.toPyDataSet(allmachineinfo)
	except :
		return -1
		
def checkiflunchexist(MachineID):
	try:
		shiftdata=system.tag.readBlocking(["Current_Shift/Start_time","Current_Shift/End_time"])
		startTime=shiftdata[0].value
		endTime=shiftdata[1].value
		params={"startTime": startTime,"endTime": endTime,"MachineID": MachineID}
		result = system.db.runNamedQuery( "downtime/CheckActiveLunch",params)
		LunchExists = result.getValueAt(0, "LunchExists")   
		if LunchExists == 1:
		    return 1
		else:
			return 0
	except :
		return -1
		
def sendlunchnotification():
	try:
		machineInfo = machine.getAllmachineinfo()  
		
		if len(machineInfo) == 0:
			return 0
		else:
			for row in machineInfo:
				basePath = row["basePath"]
				machineID = row["MachineID"]
				lunchstatus=machine.checkiflunchexist(machineID)
				if lunchstatus==0:
					system.tag.writeBlocking([basePath+"/Downtime/Lunch/Overdue"], [True])
				# Your logic here
				#print basePath, machineID
				
	except Exception as e:
		#print e
		return -1
