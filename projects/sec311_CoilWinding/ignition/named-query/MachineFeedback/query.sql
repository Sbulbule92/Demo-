SELECT TOP (8)
       [Workstation_ID],
       [Coil_ID],
       [LSPEC],
       [Style],
       [Operator_ID],
       [Actual_Start],
       [Actual_Finish],
       [Operator_ID2],
       [Actual_Start2],
       [Actual_Finish2]
FROM [LWCTPROD].[dbo].[COILWINDING_FEEDBACK]
WHERE [Workstation_ID] =
      CONCAT('M', LTRIM(RTRIM(:machineNumber)))
  AND [Actual_Finish] IS NOT NULL
ORDER BY [Actual_Finish] DESC;