SELECT Req.session_id,
	InBuf.event_info
FROM sys.dm_exec_requests AS Req
INNER JOIN sys.dm_exec_sessions AS Ses
	ON Ses.session_id = Req.session_id
CROSS APPLY sys.dm_exec_input_buffer(Req.session_id, Req.request_id) AS InBuf
WHERE Ses.session_id > 50
	AND Ses.is_user_process = 1
GO