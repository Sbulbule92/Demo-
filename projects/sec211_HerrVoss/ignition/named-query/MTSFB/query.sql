
DECLARE @StartDate DATE = CAST(DATEADD(DAY, -1, GETDATE()) AS DATE);
DECLARE @EndDate   DATE = CAST(DATEADD(DAY,  1, GETDATE()) AS DATE);

EXEC [EcsSupport].[dbo].[sp_Create_Feedback_Report]
    @StartDate,
    @EndDate,
    '54';