def onStartup(session):
	roles = session.props.auth.user.roles
	if "Operator" in roles:
		downtimetaglist=["WOCL_1/Downtime/Ideal_time/log_Active","WOCL_1/Downtime/Ideal_time/logID"]
		downtimetagValue=system.tag.readBlocking(downtimetaglist)
#		extendedlunch=downtimetagValue[0].value
		idealtimeActive=downtimetagValue[0].value
		if idealtimeActive:
		    LogID=downtimetagValue[1].value
		    parameters = {"EndTime":system.date.now(),"LogID":LogID}
		    system.db.runNamedQuery("Hitachi_Energy_Transformer","downtime/Update_downtime", parameters)
		    system.tag.writeBlocking(tagPaths=["WOCL_1/Downtime/Ideal_time/log_Active","WOCL_1/Downtime/Ideal_time/logID"], values=[0,0])