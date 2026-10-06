def handleTimerEvent():
	enddate=system.date.now()
	startDate=system.date.addDays(enddate, -2)
	ecs.sync.sync_ecs_op_status(startDate, enddate)