def onTagChange(initialChange, newValue, previousValue, event, executionCount):
	if not initialChange:
		import random
		
		if newValue.value:
		    params = {
		        "ShiftID":1,
		        "LineID":1,
		        "MachineID":1,
		        "CategoryID":1,
		        "ReasonID":3,
		        "StartTime": system.date.now(),
		        "DowntimeStatus": 1,
		        "UserName": system.tag.readBlocking(
		            ['[default]Project/Simulation 1/user']
		        )[0].value
		    }
		    dtId = system.db.execQuery('OEE_Dashboard/InsertDT', params)
		    system.util.getLogger("insert").info(str(dtId))
		    system.tag.writeBlocking('[default]Project/Simulation 1/DtID', dtId[0][0])
		
		else:
		    dtId = system.tag.readBlocking(
		        ['[default]Project/Simulation 1/DtID']
		    )[0].value
		    system.util.getLogger("update").info(str(dtId))
		    if dtId > 0:
		    	r = random.randint(1,16)
#		    	mid = random.randint(1,2)
		    	reason = system.db.execQuery('OEE_Dashboard/GetReason', {"ReasonID": r})
		        params = {
		            "EndTime": system.date.now(),
		            "DowntimeStatus":0,
		            "Remarks": reason[0][0],
		           	"LogID": dtId,
		           	"MachineID": 2
		        }
		        system.db.execQuery('OEE_Dashboard/UpdateDT', params)
		        system.tag.writeBlocking('[default]Project/Simulation 1/DtID', 0)