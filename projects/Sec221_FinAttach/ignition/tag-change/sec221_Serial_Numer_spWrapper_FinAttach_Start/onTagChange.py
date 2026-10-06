def onTagChange(initialChange, newValue, previousValue, event, executionCount):
	

	# dynamic tag value, Serial number
	SerialNo = system.tag.readBlocking(["[default]Sec221/FinAttach/FInAttach/DataAutomation/OPC_TankID"])[0].value
		
	# Define the stored procedure and parameters
	query = "EXEC dbo.spWrapper_FinAttach_Start ?"
	params = [SerialNo]
	
	# Execute the stored procedure
	results = system.db.runPrepQuery(query, params, "ECSMachineReady")
	
	# Initialize result string
	result_string = 'No data or Entered In Incorrectly'  # Default value
	
	# Check if results exist and PART_ID is present
	if results and results[0]['PART_ID']:
	    row_strings = []
	    for row in results:
	        row_string = ', '.join([
	            str(SerialNo), str(row['TANK_MATL']), str(row['TANK_MATL_THK']),
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
	
	# Write result to tag, Data to Machine
	system.tag.writeBlocking(["[default]Sec221/FinAttach/FInAttach/DataAutomation/OPC_TankData"], [result_string])
	#system.tag.writeBlocking(["[default]Sec221/FinAttach/OPC_TankDataRequest"], 0)
	
	# Print and log the result
	#system.util.getLogger("FinAttachmentLogger").info("Concatenated Result: " + result_string)
	