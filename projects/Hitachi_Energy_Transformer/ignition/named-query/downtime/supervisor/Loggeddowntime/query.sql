SELECT 
      [StartTime]
      ,[EndTime]
  
      ,[Remarks]
   
  FROM [historian].[dbo].[tbl_DowntimeLog] where LogID  = :logID