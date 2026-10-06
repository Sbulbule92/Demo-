def plannedDT1():
	machineInfo = machine.getAllmachineinfo()
	if len(machineInfo) == 0:
		logger.warn("plannedDT() - No machine info, skipping")
		return
	else: 
		return machineInfo