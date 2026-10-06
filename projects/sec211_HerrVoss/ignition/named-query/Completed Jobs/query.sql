SELECT TOP (1000) 
      [Identifier],
      [Date],
      [Part_ID],
      [Raw_Coil],
      [Additional],
      [Quantity],
      [ECSQTY],
      [Source_File],
      [DownloadTime],
      [HVIndex]
FROM [Engineering].[dbo].[Herr_Voss_Completed_Jobs]
ORDER BY [DownloadTime] DESC;