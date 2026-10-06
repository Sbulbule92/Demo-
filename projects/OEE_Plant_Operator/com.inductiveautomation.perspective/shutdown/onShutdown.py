def onShutdown(session):
	basePath = session.custom.machineInfo.basePath
	sessionbasePath = "{}/Session_status".format(basePath)
	sessiontagList = [
	    "{}/Session_start_time".format(sessionbasePath),
	    "{}/UserActive".format(sessionbasePath),
	    "{}/Session_Active".format(sessionbasePath),
	    "{}/session_ID".format(sessionbasePath),
	    "{}/LastUserActive".format(sessionbasePath)
	]
	starttime=''
	sessionActive=False
	userActive=''
	sessionID=''
	lastUserActive=session.props.auth.user.userName
	system.tag.writeBlocking(sessiontagList,[starttime,userActive,sessionActive,sessionID,lastUserActive])
	
	parameters={"id":session.custom.sessionLogID,"operator":session.props.auth.user.userName,"logout_time":system.date.now()}
	system.db.execUpdate('users/update_session_user', parameters)