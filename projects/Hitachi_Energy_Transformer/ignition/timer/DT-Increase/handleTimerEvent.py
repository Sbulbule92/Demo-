def handleTimerEvent():
	if system.tag.readBlocking('[default]Project/Simulation 1/startDt')[0].value:
		val = system.tag.readBlocking('[default]Project/Simulation 1/DTinSec')[0].value
		val+=1
		system.tag.writeBlocking('[default]Project/Simulation 1/DTinSec', val)
		
	if system.tag.readBlocking('[default]Project/Simulation/startDt')[0].value:
		val = system.tag.readBlocking('[default]Project/Simulation/DTinSec')[0].value
		val+=1
		system.tag.writeBlocking('[default]Project/Simulation/DTinSec', val)