INSERT INTO [wo_event_history] (
    serial_number,
    event_type_id,
    userName,
    wip,
    actual_num_turns,
    machine_id,
    update_time,
    remarks
)
VALUES (
    :serial_number,
    :event_type_id,
    :userName,
    :wip,
    :actual_num_turns,
    :machine_id,
     GETDATE(),
    :remarks
)