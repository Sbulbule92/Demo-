from datetime import datetime
# =====================================================
# SHIFT TIME CALCULATION UTILITIES
# =====================================================
def getShift(A_start='06:00:00', B_start='14:00:00', C_start='23:00:00'):
    """
    Determines current shift (A, B, or C)
    Handles night shift crossing midnight correctly.
    """

    # Current system time (offset used for testing)
    now = system.date.now()#system.date.addHours(system.date.now(), 16)  # replace with system.date.now() in production
    print "Current Time :", now

    # Get current hour (24-hour format)
    current_hour = system.date.getHour24(now)

    # ---------------------------------------
    # If time is between midnight and 7 AM
    # Treat it as continuation of previous day shifts
    # ---------------------------------------
    if 0 <= current_hour < 7:
        prev_day = system.date.addDays(now, -1)
        prev_day_str = system.date.format(prev_day, "yyyy-MM-dd")

        shift_a_start_str = prev_day_str + " " + A_start
        shift_b_start_str = prev_day_str + " " + B_start
        shift_c_start_str = prev_day_str + " " + C_start
        shift_c_end_str   = system.date.format(now, "yyyy-MM-dd") + " " + A_start

    # ---------------------------------------
    # Normal day shift handling
    # ---------------------------------------
    else:
        today_str = system.date.format(now, "yyyy-MM-dd")

        shift_c_start_str = today_str + " " + C_start
        shift_c_end_str   = system.date.format(
                                system.date.addDays(now, 1),
                                "yyyy-MM-dd"
                            ) + " " + A_start

        shift_a_start_str = today_str + " " + A_start
        shift_b_start_str = today_str + " " + B_start

    # Parse shift datetime values
    A = system.date.parse(shift_a_start_str)
    B = system.date.parse(shift_b_start_str)
    C = system.date.parse(shift_c_start_str)

    # Shift C duration assumed as 8 hours
    C_end = system.date.addHours(C, 8)

    # ---------------------------------------
    # Determine active shift
    # ---------------------------------------
    if system.date.isBetween(now, A, B):
        return 'A'

    elif system.date.isBetween(now, B, C):
        return 'B'

    elif system.date.isBetween(now, C, C_end):
        return 'C'

    # Fallback (should never happen)
    return None


# =====================================================
# 	
# =====================================================
def startDownTime():
	import random
	return random.randint(0,150)

def shiftChangeDT():
	query = """
		INSERT INTO DowntimeLog (
		    ShiftID,
		    LineID,
		    MachineID,
		    CategoryID,
		    ReasonID,
		    StartTime,
		    DowntimeStatus,
		    UserName
		)
		OUTPUT INSERTED.logId
		VALUES (?, ?, ?, ?, ?, ?, ?, ?)
		"""
	updateQuery = """
		UPDATE Completed_Jobs
		SET EndTime = ?, DowntimeStatus = ?, remarks = ?
		WHERE LogID = ?"""
	trigger = system.tag.readBlocking('[default]Project/Simulation/shiftChangedTrigger')[0].value
	if trigger:
		params = [
			1,
			1,
			1,
			1,
			3,
			system.date.now(),
			1,
			system.tag.readBlocking('[default]Project/Simulation/user')[0].value		
		]
		dtId = system.db.runPrepQuery(query, params, "Historian")
		system.tag.writeBlocking('[default]Project/Simulation/DtID', dtId)
		val = system.tag.readBlocking('[default]Project/Simulation/ShiftChangedDT')[0].value
		val= val +1
		system.tag.writeBlocking('[default]Project/Simulation/ShiftChangedDT', val)
	currentDT = val = system.tag.readBlocking('[default]Project/Simulation/ShiftChangedDT')[0].value
	if currentDT > 35:
		params = [
			system.date.now(),
			0,
			"Shift Change"
		]
		system.tag.writeBlocking('[default]Project/Simulation/shiftChangedTrigger', False)
		system.tag.writeBlocking('[default]Project/Simulation/ShiftChangedDT', 0)
		system.tag.writeBlocking('[default]Project/Simulation/DtID', 0)
		

def getRandomInt(low, high):
	import random as r
	return r.randint(low, high)
	
def getRandomFloat(low, high):
	import random as r
	return r.uniform(low, high)
	
def start(machine):
	base_path = '[default]Project/Simulation' if machine == 1 else "[default]Project/Simulation" + ' 1'
	
	system.tag.writeBlocking(base_path + "/Machine", machine)
	runnigJob = system.tag.readBlocking(base_path + '/jobId')[0].value
	jobId = system.tag.readBlocking(base_path + '/jobId')[0].value
	job_sr = system.tag.readBlocking(base_path + '/Job_serial_no')[0].value
	Percentage = system.tag.readBlocking(base_path + '/Percentage')[0].value
	shift = system.tag.readBlocking(base_path + '/Shift')[0].value
	sequence = system.tag.readBlocking(base_path + '/Sequence')[0].value
	loop = system.tag.readBlocking(base_path + '/loopValue')[0].value
	restarted = system.tag.readBlocking(base_path + '/restarted')[0].value
	if sequence == 'restart':
		data = []
		if Percentage>0:
			q = """
				Select * from Completed_jobs where jobId = ?
				"""
			data = system.db.runPrepQuery(q,[runnigJob], "Historian")
		loop = system.tag.readBlocking(base_path + '/loopValue')[0].value
		reStarted = True
		jobId = runnigJob
		stop = False
		job_sr = str(data[0][1])
		Done = False
		idealCT = int(data[0][8])
		targetCT = getRandomInt(idealCT, int(idealCT * getRandomFloat(1.05,1.35)))
		system.tag.writeBlocking(base_path + '/Sequence', 'running') if len(data)>0 else system.tag.writeBlocking(base_path + '/Sequence', 'Done')
		system.tag.writeBlocking(base_path + '/Job_status', 'Shift Changed')
		system.tag.writeBlocking(base_path + '/jobId', jobId)
		system.tag.writeBlocking(base_path + '/Job_serial_no', job_sr)
		system.tag.writeBlocking(base_path + '/TargetCt', targetCT)
		system.tag.writeBlocking(base_path + '/restarted', True)
	elif sequence == 'done':
		reStarted = False
		data = system.db.execQuery('OEE_Dashboard/getJob')
		print sequence + '1'
		jobId = int(data[0][0])
		reStarted = False
		loop = 0
		stop = False
		job_sr = str(data[0][1])
		Done = False
		idealCT = int(data[0][8])
		targetCT = getRandomInt(idealCT, int(idealCT * getRandomFloat(1.05,1.35)))
		system.tag.writeBlocking(base_path + '/loopValue', 0)
		system.tag.writeBlocking(base_path + '/Sequence', 'running')
		system.tag.writeBlocking(base_path + '/Job_status', 'Shift Changed')
		system.tag.writeBlocking(base_path + '/jobId', jobId)
		system.tag.writeBlocking(base_path + '/Job_serial_no', job_sr)
		system.tag.writeBlocking(base_path + '/TargetCt', targetCT * 60)
		system.tag.writeBlocking(base_path + '/restarted', False)
	
	
	updateQuery = """
		UPDATE Completed_Jobs
		SET status = ?, remarks = ?, percentage = ?, shift = ?, operator = ?
		WHERE jobId = ?"""
	
	deleteQuery = """
	    DELETE TankPrograms
	    WHERE id = ?"""
	
	query = """
		INSERT INTO Completed_Jobs (
		    serial_number,
		    program_name,
		    priority,
		    tank_status,
		    core_status,
		    status,
		    remarks,
		    idealCT
		)
		SELECT
		    serial_number,
		    program_name,
		    priority,
		    tank_status,
		    core_status,
		    status,
		    remarks,
		    idealCT
		FROM TankPrograms
		WHERE id = ?"""
		
	query1 = """
		INSERT INTO Completed_Jobs (
		    serial_number,
		    program_name,
		    priority,
		    tank_status,
		    core_status,
		    status,
		    remarks,
		    idealCT
		)
		SELECT
		    serial_number,
		    program_name,
		    priority,
		    tank_status,
		    core_status,
		    status,
		    remarks,
		    idealCT
		FROM TankPrograms
		WHERE serial_number = ?"""
		
	abort = system.tag.readBlocking(base_path + '/Abort')[0].value or system.tag.readBlocking('[default]Project/Cancelled')[0].value
	shift1 = system.tag.readBlocking(base_path + '/Shift')[0].value
	system.tag.writeBlocking(base_path + '/Percentage', Percentage )
#	system.tag.writeBlocking('[default]Project/Simulation/loopValue', loop)
	
	
#		print 'deleted' # ✅ commit!
#	timer()
	if sequence == "running" and not abort:
		loop = loop + 1
		system.tag.writeBlocking(base_path + '/loopValue', loop)
		targetCT = system.tag.readBlocking(base_path + '/TargetCt')[0].value 
		system.tag.writeBlocking(base_path + '/Job_status', 'Running')
		if loop>targetCT:
			system.tag.writeBlocking(base_path + '/Sequence', 'Database')
		Percentage = int((float(loop)/targetCT)*100) if loop>0 else 0
		system.tag.writeBlocking(base_path + '/Percentage', Percentage)
		
	if abort:
		try:
#		    system.db.runPrepUpdate(updateQuery, params, tx=tx)
#			insert = system.db.runPrepUpdate(query1,[system.tag.readBlocking(base_path + '/Job_serial_no')[0].value], "Historian")
#			system.perspective.print('Inserted')
			
			params = {"status":"Cancelled",
					"remarks":"Job Cancelled",
					"percentage":Percentage,
					"shift":shift1, 
					"operator":'Virat',
					"time": system.date.now(),
					"jobId": jobId,
					"job_sr": job_sr}
#			update = system.db.execQuery('OEE_Dashboard/updatedJob', parameters = params)#system.db.runPrepUpdate(updateQuery, params, "Historian")
#			system.util.getLogger('simulation').info(str(update))
			
#			delete = system.db.runPrepUpdate(deleteQuery, [jobId], "Historian")
			system.tag.writeBlocking(base_path + '/Percentage', 0)
			system.tag.writeBlocking(base_path + '/loopValue', 0)
			system.tag.writeBlocking(base_path + '/Job_status', '')
			system.tag.writeBlocking(base_path + '/jobId', 0)
			system.tag.writeBlocking(base_path + '/Job_serial_no', '')
			system.tag.writeBlocking(base_path + '/Sequence', 'done')
			system.tag.writeBlocking(base_path + '/TargetCt', 0)
			system.tag.writeBlocking(base_path + '/restarted', False)
			system.util.getLogger('simulation').info(str("done"))
#			print 'deleted' # ✅ commit
		except Exception as e:
			system.util.getLogger('simulation').info(str(e))
		
	if shift!=shift1:
		try:
#		    system.db.runPrepUpdate(updateQuery, params, tx=tx)
			insert = system.db.runPrepUpdate(query1,[system.tag.readBlocking(base_path + '/Job_serial_no')[0].value], "Historian")
			print 'Inserted'
			
			params = {"status":"In-process",
					"remarks":"Job Done in Time",
					"percentage":Percentage,
					"shift":shift1, 
					"operator":'Virat',
					"time": system.date.now(),
					"jobId": jobId,
					"job_sr": job_sr}
			update = system.db.execQuery('OEE_Dashboard/updatedJob', parameters = params)#system.db.runPrepUpdate(updateQuery, params, "Historian")
			print update
			
			delete = system.db.runPrepUpdate(deleteQuery, [jobId], "Historian")
			system.tag.writeBlocking(base_path + '/Percentage', Percentage )
			system.tag.writeBlocking(base_path + '/loopValue', loop)
			system.tag.writeBlocking(base_path + '/Job_status', 'Shift Changed')
			system.tag.writeBlocking(base_path + '/jobId', jobId)
			system.tag.writeBlocking(base_path + '/Job_serial_no', job_sr)
			system.tag.writeBlocking(base_path + '/Sequence', 'restart')
			system.tag.writeBlocking(base_path + '/restarted', True)
			print 'restarted'
		except:
			system.util.getLogger('simulation').info('shift')

	if sequence == 'Database':
		try:
#		    system.db.runPrepUpdate(updateQuery, params, tx=tx)
			if not restarted:
				insert = system.db.runPrepUpdate(query1,[system.tag.readBlocking(base_path + '/Job_serial_no')[0].value], "Historian")
				system.util.getLogger('simulation').info(str(insert))
			
			params = {"status":"Completed",
					"remarks":"Job restarted" if restarted else "Job Done!",
					"percentage":Percentage,
					"shift":system.tag.readBlocking(base_path + '/Shift')[0].value, 
					"operator":'Virat',
					"time": system.date.now(),
					"jobId": system.tag.readBlocking(base_path + '/jobId')[0].value,
					"job_sr": system.tag.readBlocking(base_path + '/Job_serial_no')[0].value,
					"MachineID": machine
					}
			update = system.db.execQuery('OEE_Dashboard/updatedJob', parameters = params)#system.db.runPrepUpdate(updateQuery, params, "Historian")
			print update
			
			delete = system.db.runPrepUpdate(deleteQuery, [jobId], "Historian")
			system.tag.writeBlocking(base_path + '/Percentage', 0)
			system.tag.writeBlocking(base_path + '/loopValue', 0)
			system.tag.writeBlocking(base_path + '/Job_status', '')
			system.tag.writeBlocking(base_path + '/jobId', 0)
			system.tag.writeBlocking(base_path + '/Job_serial_no', '')
			system.tag.writeBlocking(base_path + '/Sequence', 'done')
			system.tag.writeBlocking(base_path + '/TargetCt', 0)
			system.tag.writeBlocking(base_path + '/restarted', False)
			print 'Saved' # ✅ commit!
		except Exception, e:
			system.util.getLogger('simulation').info('error' + str(e))