INSERT INTO Trace_Operator
(
    machineID,
    lineID,
    login_time,
    operator
)

OUTPUT INSERTED.id
VALUES
(
    :machineID,
    :lineID,
    :login_time,
   
    :operator
)