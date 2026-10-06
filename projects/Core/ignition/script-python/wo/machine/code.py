def get_machine_status(tagPaths):
	try :
		result = system.tag.readBlocking(tagPaths)
		return result
	except :
		return -1
def update_machine_status(tagPaths,tagvalues):
	try :
		result = system.tag.writeBlocking(tagPaths,tagvalues)
		return result
	except :
		return -1
def build_tagpath_RW(basepath):
	#This function is used to get all the required Read and Write tagpath
	try :
		taglist=[
			    "{}/WO/PO".format(basepath),  # [0] tagpath PO number 
			    "{}/WO/serial_number".format(basepath),# [1] tagpath Serial number 
			    "{}/WO/Start_time".format(basepath),# [2] tagpath StartDate
			    "{}/WO/status".format(basepath),# [3] tagpath Machine workstatus
			    "{}/Supervisor/Job_Cancel_requested".format(basepath),# [4] tagpath job cancel requests
			    "{}/WO/Program_Name".format(basepath),# [5] tagpath program name for machine
			   "{}/Supervisor/LastAction".format(basepath)
			]
		return taglist
	except :
		return -1
		
def build_tagpath_RO(basepath):
	#This function is used to get all the required Read only tagpath
	try :
		taglist=[
			    "{}/ProductionData/WIP".format(basepath),# [0] tagpath for work inprogress percentage value
			    "{}/ProductionData/ActualTurnNumber".format(basepath)# [1] tagpath for Actual number of turn value
			    
			]
		return taglist
	except :
		return -1		
		
		
def isOpcConnected(serverName):
	state = system.opc.getServerState(serverName)
	if state == "CONNECTED":
		return True
	else:
		return False