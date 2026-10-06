EXEC dbo.SP_InsertABB_MachineResponse
    :PO_Number,
    :Serial_Number,
    :Equipment,
    :action,
    :ECSUser;

--SELECT 1 AS Result;

-- You can see the data in machineresponse in the 6077 test server
--to make sure it works
--Action 4 to start, 16 to stop