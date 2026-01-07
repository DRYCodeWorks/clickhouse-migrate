SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [dbo].[usp_utl_InsertDebugLog] @SourceName VARCHAR(100),
	@SourceKey VARCHAR(100),
	@ErrorCode INT,
	@ErrorMessage VARCHAR(5000),
	@DebugData VARCHAR(max)
AS
BEGIN
	SET NOCOUNT ON;

	IF (@SourceKey LIKE 'e00fce681eceae6a9a5fe4df%')
	BEGIN
		INSERT INTO [dbo].[DebugLog] (
			[SourceName],
			[SourceKey],
			[ErrorCode],
			[ErrorMessage],
			[DebugData],
			[CreatedDateTimeUTC]
		)
		VALUES (
			@SourceName,
			@SourceKey,
			@ErrorCode,
			@ErrorMessage,
			@DebugData,
			CURRENT_TIMESTAMP
		)
	END
END
GO


