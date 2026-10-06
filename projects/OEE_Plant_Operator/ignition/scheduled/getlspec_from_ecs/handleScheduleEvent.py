def handleScheduleEvent():
	endDate=system.date.addDays(system.date.now(), 2)
	startDate=system.date.addDays(endDate, -28)
	#endDate=startDate
	ecs.sync.synclspec_from_ECS(startDate,endDate)