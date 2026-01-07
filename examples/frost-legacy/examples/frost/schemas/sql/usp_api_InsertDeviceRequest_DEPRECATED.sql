CREATE PROCEDURE [dbo].[usp_api_InsertDeviceRequest]

	@DeviceID bigint,	
    @RequestTypeCode varchar(30),
    @RequestData  varchar(max) = NULL,	
    @ResultCode  varchar(50) = NULL,
    @ResultData  varchar(max) = NULL,
    @ReferenceNr varchar(50) = null,
    @StartDateTimeUTC datetime = NULL,
    @EndDateTimeUTC datetime = NULL,
    @CreatedUserID  uniqueidentifier,
	@DeviceRequestID bigint out,
	@ErrorCode int out, --indicates status of the results
	@ErrorMessage varchar(2000) out
	
AS
BEGIN
	SET NOCOUNT ON;

	declare @DebugMessage varchar(max),
			@CreateDateTimeUTC datetime = CURRENT_TIMESTAMP,
			@dateTimeInt bigint = 0,
			@dateTimeStr varchar(14),
			@NotifyDuration int = 0, --minutes
			@NotificationTypeID smallint

	set @ErrorCode = 999
		
	select @DebugMessage = concat(@RequestTypeCode, '~', @ReferenceNr, '~', @RequestData)

	exec usp_utl_InsertDebugLog 'usp_api_InsertDeviceRequest', @DeviceID, 0, 'DEBUG', @DebugMessage

BEGIN TRY	
	set @StartDateTimeUTC = isnull(@StartDateTimeUTC, CURRENT_TIMESTAMP)
			
	INSERT INTO [dbo].[DeviceRequests]
           ([DeviceID]
           ,[RequestTypeCode]
           ,[RequestData]
           ,[ResultCode]
           ,[ResultData]
           ,[ReferenceNr]
           ,[StartDateTimeUTC]
           ,[EndDateTimeUTC]           
           ,[CreatedUserID])
     VALUES
           (@DeviceID,	
			@RequestTypeCode,
			@RequestData,	
			@ResultCode,
			@ResultData,
			@ReferenceNr,
			isnull(@StartDateTimeUTC, CURRENT_TIMESTAMP),
			@EndDateTimeUTC,
			@CreatedUserID)
	
		select @DeviceRequestID = @@IDENTITY

		exec usp_utl_InsertDebugLog 'usp_api_InsertDeviceRequest', @DeviceID, 0, 'INSERT-DeviceRequests', @DeviceRequestID

		set @ErrorCode = 100
		set @ErrorMessage = 'Inserted device request'

		if (isnull(@RequestTypeCode,'') = 'DEVICE_REQUEST_PHOTO')
		begin	
			--if photo request type set last photo date 
			update Devices set LastPhotoRequestUTC = @StartDateTimeUTC where ID = @DeviceID
		
			exec usp_utl_InsertDebugLog 'usp_api_InsertDeviceRequest', @DeviceID, 0, 'INSERT-DeviceRequests', @DeviceRequestID			
		end

		--send notification photo upload requested (specific user if applicable)
		INSERT INTO [dbo].[Notifications]
				([DeviceID]
				,[NotificationMethodID]
				,[NotificationTypeID]
				,[NotificationStatusID]
				,[ReferenceTypeID]
				,[ReferenceKey]
				,[NotifyDateTimeUTC]
				,[SentDateTimeUTC]
				,[Data]
				,[TriggeredUserID]
				,[CreateDateTimeUTC])
			VALUES
				(@DeviceID
				,3 --WEB
				,CASE 
					WHEN @RequestTypeCode = 'DEVICE_REQUEST_PHOTO' THEN 5 --REQUEST_PHOTO_STARTED
					WHEN @RequestTypeCode = 'EVENT_REQUEST_WORK' THEN 6 --REQUEST_WORK_STARTED				
					WHEN @RequestTypeCode = 'DEVICE_REQUEST_DEFROST' THEN 8 --REQUEST_DEFROST_STARTED
					WHEN @RequestTypeCode = 'DEVICE_REQUEST_STORM' THEN 10 --REQUEST_STORM_STARTED
					END
				,1 --NEW
				,2 --DEVICEREQUESTS_ID
				,@DeviceRequestID
				,CURRENT_TIMESTAMP
				,null
				,null
				,@CreatedUserID
				,CURRENT_TIMESTAMP)

		if @RequestTypeCode = 'DEVICE_REQUEST_DEFROST' or @RequestTypeCode = 'DEVICE_REQUEST_STORM'
		BEGIN
			--determine duration of when notify date should be based on configurations

			if  @RequestTypeCode = 'DEVICE_REQUEST_DEFROST'
				select @NotificationTypeID = 9, --REQUEST_DEFROST_COMPLETED
						@NotifyDuration = isnull(SettingValue,0) 
				from CustomSettings (nolock) 
				where SettingCode = 'DEVICE_DEFROST_DURATION' 

			else if @RequestTypeCode = 'DEVICE_REQUEST_STORM'
				select @NotificationTypeID = 11, --REQUEST_STORM_COMPLETED
						@NotifyDuration = isnull(SettingValue,0) 
				from CustomSettings (nolock) 
				where SettingCode = 'DEVICE_STORM_DURATION'

			--send notification photo upload requested (specific user if applicable)
			INSERT INTO [dbo].[Notifications]
					([DeviceID]
					,[NotificationMethodID]
					,[NotificationTypeID]
					,[NotificationStatusID]
					,[ReferenceTypeID]
					,[ReferenceKey]
					,[NotifyDateTimeUTC]
					,[SentDateTimeUTC]
					,[Data]
					,[TriggeredUserID]
					,[CreateDateTimeUTC])
				VALUES
					(@DeviceID
					,3 --WEB
					,@NotificationTypeID					
					,1 --NEW
					,2 --DEVICEREQUESTS_ID
					,@DeviceRequestID
					,dateadd(minute, @NotifyDuration, CURRENT_TIMESTAMP)
					,null
					,null
					,@CreatedUserID
					,CURRENT_TIMESTAMP)
		end

		--set success
		set @ErrorCode = 0
		set @ErrorMessage = 'SUCCESS'
END TRY
BEGIN CATCH
	set @ErrorMessage = @DebugMessage + concat(cast(ERROR_NUMBER() as varchar(20)), '~', ERROR_MESSAGE())

	exec usp_utl_InsertDebugLog 'usp_api_InsertDeviceRequest', @DeviceID, @ErrorCode, 'CATCH', @ErrorMessage	
END CATCH

return @ErrorCode

END
