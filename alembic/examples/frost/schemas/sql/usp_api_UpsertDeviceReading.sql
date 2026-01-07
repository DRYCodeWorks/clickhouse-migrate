CREATE PROCEDURE [dbo].[usp_api_UpsertDeviceReading] @VendorDeviceID VARCHAR(50), -- Vendor device unique identifier
	@VendorReadingID VARCHAR(50), -- Vendor reading unique identifier
	@CaptureDateTimeUTC DATETIME,
	@SurfaceTemp DECIMAL(6, 2),
	@AirTemp DECIMAL(6, 2),
	@DewPoint DECIMAL(6, 2),
	@Humidity DECIMAL(6, 2),
	@HeaterTemp DECIMAL(6, 2),
	@AmbientLight INT,
	@DeviceID BIGINT OUTPUT,
	@DeviceReadingID BIGINT OUTPUT,
	@ErrorCode INT OUTPUT,
	@ErrorMessage VARCHAR(2000) OUTPUT
AS
BEGIN
	SET NOCOUNT ON;
	SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

	-- Validate inputs
	IF @VendorDeviceID IS NULL
		OR @VendorReadingID IS NULL
		OR @CaptureDateTimeUTC IS NULL
		OR @SurfaceTemp IS NULL
		OR @AirTemp IS NULL
		OR @DewPoint IS NULL
		OR @Humidity IS NULL
		OR @HeaterTemp IS NULL
		OR @AmbientLight IS NULL
	BEGIN
		SET @ErrorCode = 400;
		SET @ErrorMessage = 'Required input parameters are missing.';

		RETURN;
	END

	BEGIN TRY
		-- Declare variables
		DECLARE @OldDeviceReadingID BIGINT = NULL;
		DECLARE @DeviceType SMALLINT;
		DECLARE @DeviceTypeName VARCHAR(50);
		DECLARE @SupportedSensorTypes TABLE (ID SMALLINT);

		INSERT INTO @SupportedSensorTypes (ID)
		SELECT ID
		FROM DeviceType
		WHERE Name = 'Mini RWIS';

		-- Retrieve DeviceID and related data
		SELECT @DeviceID = d.ID,
			@OldDeviceReadingID = r.ID,
			@DeviceType = d.DeviceType,
			@DeviceTypeName = dt.Name
		FROM Devices d
		LEFT JOIN DeviceReadings r
			ON r.DeviceID = d.ID
				AND r.VendorReadingID = @VendorReadingID
		INNER JOIN DeviceType dt
			ON d.DeviceType = dt.ID
		WHERE d.VendorDeviceID = @VendorDeviceID;

		IF @DeviceID IS NULL
		BEGIN
			SET @ErrorCode = 100;
			SET @ErrorMessage = 'Device not found for VendorDeviceID ' + @VendorDeviceID;

			RETURN;
		END

		IF NOT EXISTS (
				SELECT 1
				FROM @SupportedSensorTypes
				WHERE ID = @DeviceType
			)
		BEGIN
			SET @ErrorCode = 204;
			SET @ErrorMessage = 'Unsupported Device Type ' + @DeviceTypeName + ' does not support sensor data.';

			RETURN;
		END

		IF @OldDeviceReadingID IS NOT NULL
		BEGIN
			SET @ErrorCode = 200
			SET @ErrorMessage = 'Vendor Device reading ID already exists, duplicate reading key ' + @VendorReadingID
			RETURN @ErrorCode
		END


		DECLARE @OutputRow TABLE (DeviceReadingID BIGINT);

		INSERT INTO [dbo].[DeviceReadings] (
			[DeviceID],
			[VendorReadingID],
			[CaptureDateTimeUTC],
			[SurfaceTemp],
			[AirTemp],
			[DewPoint],
			[Humidity],
			[CreatedDateTimeUTC],
			[HeaterTemp],
			[AmbientLight]
		)
		VALUES (
			@DeviceID,
			@VendorReadingID,
			@CaptureDateTimeUTC,
			@SurfaceTemp,
			@AirTemp,
			@DewPoint,
			@Humidity,
			CURRENT_TIMESTAMP,
			@HeaterTemp,
			@AmbientLight
		) 

		-- Retrieve output values
		SET @DeviceReadingID = SCOPE_IDENTITY();

		SET @ErrorCode = 0;
		SET @ErrorMessage = 'SUCCESS';
	END TRY

	BEGIN CATCH
		-- Error handling
		SET @ErrorCode = ERROR_NUMBER();
		SET @ErrorMessage = ERROR_MESSAGE();
	END CATCH

	RETURN @ErrorCode;
END


