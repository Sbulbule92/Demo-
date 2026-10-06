def onStartup(session):
	ipaddress=session.props.address
	# Get All machine details
	parameters = { "ipaddress":ipaddress}
	machineInfo=system.db.runNamedQuery("Machines/GetMachineByName", parameters)
	if machineInfo.getRowCount() > 0:
		machineCode = machineInfo.getValueAt(0,"MachineCode")
		basePath=machineInfo.getValueAt(0,"basePath")
		session.custom.machineInfo.EquipmentName=machineInfo.getValueAt(0,"EquipmentName")
		session.custom.machineInfo.OPRID=machineInfo.getValueAt(0,"OPRID")
		session.custom.machineInfo.section=machineInfo.getValueAt(0,"Section")
		session.custom.machineInfo.basePath=basePath
		session.custom.machineInfo.ID=machineInfo.getValueAt(0,"MachineID")
		machineID=machineInfo.getValueAt(0,"MachineID")
		session.custom.machineInfo.lineID=machineInfo.getValueAt(0,"LineID")
		lineID=machineInfo.getValueAt(0,"LineID")
		session.custom.machineInfo.Name =machineInfo.getValueAt(0,"MachineName")
		session.custom.machineInfo.Code=machineCode
		session.custom.machine=machineCode
		
		sessionbasePath = "{}/Session_status".format(basePath)
		sessiontagList = [
		    "{}/Session_start_time".format(sessionbasePath),
		    "{}/UserActive".format(sessionbasePath),
		    "{}/Session_Active".format(sessionbasePath),
		    "{}/session_ID".format(sessionbasePath)
		]
		starttime=system.date.now()
		sessionActive=True
		userActive=session.props.auth.user.userName
		sessionid=session.props.id
		system.tag.writeBlocking(sessiontagList,[starttime,userActive,sessionActive,sessionid])
		parameters={"machineID":machineID,"lineID":lineID,"operator":userActive,"login_time":starttime}
		sessionlogID=system.db.execQuery('users/insert_session_user', parameters)
		session.custom.sessionLogID=sessionlogID.getValueAt(0,0)
		basepathdowntime = "{}/Downtime".format(basePath)
		downtimetaglist = [
		    "{}/Lunch/Over".format(basepathdowntime),
		    "{}/Ideal_time/log_Active".format(basepathdowntime),
		    "{}/Ideal_time/logID".format(basepathdowntime),
		    "{}/Break/Active".format(basepathdowntime),
		    "{}/Break/logID".format(basepathdowntime),
		    "{}/Lunch/extendend_lunch_ID".format(basepathdowntime)
			]
		downtimetagValue=system.tag.readBlocking(downtimetaglist)
		extendedlunch=downtimetagValue[0].value
		idealtimeActive=downtimetagValue[1].value
		breakActive=downtimetagValue[3].value
		if idealtimeActive:
			LogID=downtimetagValue[2].value
			parameters = {"EndTime":system.date.now(),"LogID":LogID}
			system.db.runNamedQuery("downtime/UpdateDowntimeCompletion", parameters)
			system.tag.writeBlocking(tagPaths=["{}/Downtime/Ideal_time/log_Active".format(basePath),"{}/Downtime/Ideal_time/logID".format(basePath)], values=[0,0])
		elif breakActive:
			LogID=downtimetagValue[4].value
			parameters = {"EndTime":system.date.now(),"LogID":LogID}
			system.db.runNamedQuery("downtime/UpdateDowntimeCompletion", parameters)
			system.tag.writeBlocking(tagPaths=["{}/Downtime/Break/Active".format(basePath),"{}/Downtime/Break/logID".format(basePath)], values=[0,0])
		if extendedlunch:
			LogID=downtimetagValue[5].value
			parameters = {"EndTime":system.date.now(),"LogID":LogID}
			system.db.runNamedQuery("downtime/UpdateDowntimeCompletion", parameters)	
			system.tag.writeBlocking(["{}/Lunch/extendend_lunch_ID".format(basepathdowntime)],[0])
	else:
		#system.perspective.logout(message="Unauthorised device to access the operator project")
		session.custom.WrongDevice =True
		
#=========================================================================================================================================================	
	
		
	"""New session announces itself; older sessions on the same IP will self-close."""

	def norm(addr):
	    a = str(addr).strip().lstrip('/')
	    if a.count(':') == 1:
	        a = a.split(':')[0]
	    if a in ('0:0:0:0:0:0:0:1', '::1'):
	        a = '127.0.0.1'
	    return a
	
	KIOSK_IPS = ['10.117.3.49','10.117.3.225' ]   # empty = enforce everywhere (testing); later: ['10.72.57.24', ...]
	
	myAddr = norm(session.props.address)
	if KIOSK_IPS and myAddr not in KIOSK_IPS:
	    return
	
	system.util.sendMessage(
	    project        = system.util.getProjectName(),
	    messageHandler = 'kioskTakeover',
	    payload        = {'newId': str(session.props.id), 'addr': myAddr},
	    scope          = 'S')   # broadcast to all Perspective sessions of this project