def displayConfirmation(message):
	"""Script to open a confirmation popup in Perspective.
	
	Args:
		message - string message to display to user while asking for confirmation to proceed.
	"""
	title = 'Are you sure?'
	params = { 'title' : title, 'message' : message }
	system.perspective.openPopup('confirmPopup', 'Exchange/ZPL Label Printing/Popups/Confirm Popup', params=params, title=title, showCloseIcon=True, modal=True, overlayDismiss=True)



def displayMessage(title, message):
	"""Script to open a popup and display a title and message in Perspective.
	
	Args:
		title - string to display on the header of the popup
		message - string message to display to user
	"""
	params = { 'title' : title, 'message' : message }
	system.perspective.openPopup('messagePopup', 'Exchange/ZPL Label Printing/Popups/Message Popup', params=params, title=title, showCloseIcon=True, modal=True, overlayDismiss=True)



def displayError(message):
	"""Wrapper around base message display to show an error message.
	
	Args:
		message - string error message to display to user
	"""
	displayMessage('An Error Occurred', message)


