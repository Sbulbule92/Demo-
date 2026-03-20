UPDATE Inprocess_Jobs
SET status = :status , remarks = :remarks , percentage = :percentage , shift = :shift , operator = :operator , time = :time , jobId =  :jobId 
output inserted.jobId
WHERE serial_number = :job_sr

--[jobId, percentage, shift, time, remarks, operator, status]