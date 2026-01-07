-- =============================================
-- Author:		Outliant
-- Create date: 2022-10-04
-- Description:	Called by API to Upsert Device sensor readings from vendor (particle.io)
-- =============================================
CREATE PROCEDURE [dbo].[usp_api_UpsertDeviceReading]
	@VendorDeviceID varchar(50), --vendor device unqiue identifier (i.e. particle device id)
	@VendorReadingID varchar(50), --vendor reading unique identifier (i.e. particle image/event id)
	@CaptureDateTimeUTC datetime,	
	@SurfaceTemp decimal(6,2) = null,	
	@AirTemp decimal(6,2) = null,	
	@DewPoint decimal(6,2) = null,	
	@Humidity decimal(6,2) = null,	
	@HeaterTemp decimal(6,2) = null,	
	@AmbientLight int = null,	
	@DeviceID bigint out, --device id for retreiving image quicker and logging
	@DeviceReadingID bigint out, --device reading id for retreiving reading quicker and logging
	@ErrorCode int out, --indicates status of the results
	@ErrorMessage varchar(2000) out
	
AS
BEGIN
	SET NOCOUNT ON;

	declare @DebugMessage varchar(max),
			@DeviceImagePacketID bigint,
			@OldDeviceReadingID bigint

	select @DebugMessage = 
						concat(@VendorDeviceID , '~',
						@VendorReadingID , '~',
						@CaptureDateTimeUTC ,'~',
						@SurfaceTemp ,'~',
						@AirTemp ,'~',
						@DewPoint ,'~',
						@Humidity ,'~',
						@HeaterTemp ,'~',
						@AmbientLight)

	exec usp_utl_InsertDebugLog 'usp_api_UpsertDeviceReading', @VendorReadingID, 0, 'DEBUG', @DebugMessage

	set @DeviceID = 0			
	set @ErrorCode = 999

	select @DeviceID = d.ID,
			@OldDeviceReadingID = r.ID			
	from Devices (nolock) d
		left outer join DeviceReadings (nolock) r on r.DeviceID = d.ID and r.VendorReadingID = @VendorReadingID
	where d.VendorDeviceID = @VendorDeviceID

	if(isnull(@DeviceID,0) = 0)
	begin
		set @ErrorCode = 100
		set @ErrorMessage = 'Device not found by VendorDeviceID ' + @VendorDeviceID

		exec usp_utl_InsertDebugLog 'usp_api_UpsertDeviceReading', @VendorReadingID, @ErrorCode, @ErrorMessage, null

		return @ErrorCode
	end	

	if(isnull(@OldDeviceReadingID,0) > 0)
	begin
		set @ErrorCode = 200
		set @ErrorMessage = 'Vendor Device reading ID already exists, duplicate reading key ' + @VendorReadingID

		exec usp_utl_InsertDebugLog 'usp_api_UpsertDeviceReading', @VendorReadingID, @ErrorCode, @ErrorMessage, null

		return @ErrorCode
	end	
	   
BEGIN TRY
		
		set @ErrorCode = 300

		INSERT INTO [dbo].[DeviceReadings]
					([DeviceID]
					,[VendorReadingID]
					,[CaptureDateTimeUTC]
					,[SurfaceTemp]
					,[AirTemp]
					,[DewPoint]
					,[Humidity]
					,[CreatedDateTimeUTC]
					,[HeaterTemp]
					,[AmbientLight])
				VALUES
					(@DeviceID
					,@VendorReadingID
					,@CaptureDateTimeUTC
					,@SurfaceTemp
					,@AirTemp
					,@DewPoint
					,@Humidity
					,CURRENT_TIMESTAMP
					,@HeaterTemp
					,@AmbientLight)

			  
		select @DeviceReadingID = @@IDENTITY

		exec usp_utl_InsertDebugLog 'usp_api_UpsertDeviceReading', @VendorReadingID, 0, 'INSERT-DeviceReadings', @DeviceReadingID

		--set success
		set @ErrorCode = 0
		set @ErrorMessage = 'SUCCESS'
END TRY
BEGIN CATCH
	set @ErrorMessage = concat(cast(ERROR_NUMBER() as varchar(20)), '~', ERROR_MESSAGE())

	exec usp_utl_InsertDebugLog 'usp_api_UpsertDeviceReading', @VendorReadingID, @ErrorCode,  'CATCH', @ErrorMessage
END CATCH

return @ErrorCode

END