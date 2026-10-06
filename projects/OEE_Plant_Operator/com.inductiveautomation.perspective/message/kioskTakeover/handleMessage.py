def handleMessage(session, payload):
	logger = system.util.getLogger('KioskSession')

	myAddr = str(session.props.address).strip().lstrip('/')
	if myAddr.count(':') == 1:
		myAddr = myAddr.split(':')[0]
	if myAddr in ('0:0:0:0:0:0:0:1', '::1'):
		myAddr = '127.0.0.1'
	
	myId = str(session.props.id)
	
	if myId == payload['newId']:
		pass
	elif myAddr == payload['addr']:
		# Find one of MY page ids (getSessionInfo may show a shortened session id,
		# so compare on the first 8 hex chars)
		pid = None
		myShort = myId.replace('-', '').upper()[:8]
		try:
			for info in system.perspective.getSessionInfo(projectFilter=system.util.getProjectName()):
				infoShort = str(info['id']).replace('-', '').upper()[:8]
				if infoShort == myShort:
					pages = info['pageIds']
					if pages and len(pages) > 0:
						pid = str(pages[0])
					break
		except Exception, e:
			logger.warn('Could not read page ids: %s' % str(e))
	
		if pid:
			logger.info('Takeover: logging out session %s page %s' % (myId, pid))
			system.perspective.logout(sessionId=myId, pageId=pid)
		else:
			logger.info('Takeover: no page found, closing session %s' % myId)
			system.perspective.closeSession('A new session was started on this workstation.')