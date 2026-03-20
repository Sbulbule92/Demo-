def handleTimerEvent():
	dt = system.tag.readBlocking('[default]Project/Simulation/startDt')[0].value
	if not dt:
		Project.HE.ProjectScript.start(1)
#	Project.HE.ProjectScript.shiftChangeDT()