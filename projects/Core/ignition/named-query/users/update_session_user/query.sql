UPDATE Trace_Operator
SET logout_time = :logout_time
WHERE operator = :operator
  AND id = :id;