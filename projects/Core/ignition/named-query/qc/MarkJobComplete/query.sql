UPDATE quality_checks
SET status       = 'COMPLETED',
    completed_at = GETDATE(),
    completed_by = :username
WHERE job_id = :jobId
  AND status <> 'COMPLETED';