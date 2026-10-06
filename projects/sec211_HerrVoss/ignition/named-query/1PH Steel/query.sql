DECLARE @CurrentDate DATETIME;
SET @CurrentDate = GETDATE();

EXECUTE EcsSupport.[dbo].[spRPT_SetHervoss1phSteel] @CurrentDate