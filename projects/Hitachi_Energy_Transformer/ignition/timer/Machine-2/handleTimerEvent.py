def handleTimerEvent():
	dt = system.tag.readBlocking('[default]Project/Simulation1/startDt')[0].value
	if not dt:
		Project.HE.ProjectScript.start(2)