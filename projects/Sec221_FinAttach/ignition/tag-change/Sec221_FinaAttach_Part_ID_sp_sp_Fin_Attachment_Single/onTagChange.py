def onTagChange(initialChange, newValue, previousValue, event, executionCount):
	# Set partID manually for testing
	#partID = 'J433'  # Change this value as needed
	# Uncomment the line below to use dynamic tag value instead
	partID = system.tag.readBlocking(["[default]Sec221/FinAttach/OPC_TankDataRequest[default]Sec221/FinAttach/FInAttach/DataAutomation/OPC_TankID"])[0].value
	
	# Construct the full part ID
	fullpartID = 'J433' + str(partID)
	#print fullpartID
	
	# Define the stored procedure and parameters
	query = "EXEC dbo.sp_Fin_Attachment_Single ?"
	params = [fullpartID]
	
	# Execute the stored procedure
	results = system.db.runPrepQuery(query, params, "ECSMachineReady")
	
	# Initialize result string
	result_string = 'No data or Entered In Incorrectly'  # Default value
	
	# Check if results exist and PART_ID is present
	if results and results[0]['PART_ID']:
	    row_strings = []
	    for row in results:
	        row_string = ', '.join([
	            str(row['PART_ID']), str(row['TANK_MATL']), str(row['TANK_MATL_THK']),
	            str(row['FIN_MATL_THK']), str(row['FIN_MATL']), str(row['TANK_HEIGHT']),
	            str(row['TANK_BP_WIDTH']), str(row['TANK_DEPTH']), str(row['BACK_FIN_HEIGHT']),
	            str(row['BACK_FIN_WIDTH']), str(row['BACK_FIN_J']), str(row['BACK_FIN_K']),
	            str(row['TANK_HV_EXT']), str(row['LEFT_FIN_HEIGHT']), str(row['LEFT_FIN_WIDTH']),
	            str(row['LEFT_FIN_J']), str(row['LEFT_FIN_K']), str(row['TANK_LV_EXT']),
	            str(row['RIGHT_FIN_HEIGHT']), str(row['RIGHT_FIN_WIDTH']),
	            str(row['RIGHT_FIN_J']), str(row['RIGHT_FIN_K'])
	        ])
	        row_strings.append(row_string)
	
	    # Final concatenated result
	    result_string = ' | '.join(row_strings)
	
	# Write result to tag
	system.tag.writeBlocking(["[default]Sec221/FinAttach/OPC_TankDataRequest[default]Sec221/FinAttach/FInAttach/DataAutomation/OPC_TankData"], [result_string])
	
	# Print and log the result
	#print(result_string)
	system.util.getLogger("FinAttachmentLogger").info("Concatenated Result: " + result_string)