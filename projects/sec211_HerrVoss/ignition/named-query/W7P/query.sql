
SELECT TOP (1000)
       [Identifier],
       [Date],
       [Part_ID],
       --[Raw_Coil],
       [Additional],
       [Quantity]
       --[ECSQTY],
       --[Source_File],
       --[DownloadTime],
       --[HVIndex]
FROM [Engineering].[dbo].[Herr_Voss_Schedule]
WHERE [Additional] = 'Weid 7'
  AND [Source_File] = 'ECS'
ORDER BY [HVIndex] ASC;
