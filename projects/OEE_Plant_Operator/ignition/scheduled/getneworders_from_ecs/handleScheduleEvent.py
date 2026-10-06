def handleScheduleEvent():
	today=system.date.now()
	startDate=system.date.addDays(today, -15)
	endDate=system.date.addHours(today, 24)
	ecs.sync.sync_new_workorders(startDate,endDate)