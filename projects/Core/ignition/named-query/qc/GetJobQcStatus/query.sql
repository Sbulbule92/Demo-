SELECT COALESCE(
    (SELECT qc.status
     FROM quality_checks qc
     WHERE qc.job_id = :jobId),
    'NOT_STARTED'
) AS qc_status;