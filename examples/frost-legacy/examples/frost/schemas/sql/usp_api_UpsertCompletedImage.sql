CREATE PROCEDURE [dbo].[usp_api_UpsertCompletedImage] @VendorDeviceID VARCHAR(50),
	@VendorImageID VARCHAR(50),
	@CorrectedVendorImageID VARCHAR(50),
	@CaptureDateTimeUTC DATETIME,
	@Size INT,
	@AmbientLight VARCHAR(5) = NULL,
	@Contrast VARCHAR(5) = NULL,
	@Brightness VARCHAR(5) = NULL,
	@Exposure VARCHAR(5) = NULL,
	@Resolution INT = NULL,
	@ImageUrl VARCHAR(5000) = NULL,
	@PacketIndex SMALLINT,
	@PacketCount SMALLINT,
	@BodyLength INT,
	@ImageData VARCHAR(5), -- not used, just for backwards compatibility
	@IsBurstImage BIT = 0,
	@DeviceID BIGINT OUTPUT,
	@DeviceImageID BIGINT OUTPUT,
	@IsComplete BIT OUTPUT,
	@ErrorCode INT OUTPUT,
	@ErrorMessage VARCHAR(2000) OUTPUT
AS
BEGIN
	SET NOCOUNT ON;

	DECLARE @ProcName VARCHAR = 'usp_api_UpsertCompletedImage';
	DECLARE @DeviceReadingID BIGINT,
		@DebugMessage VARCHAR(max),
		@DeviceImagePacketID BIGINT,
		@DeviceRequestID BIGINT,
		@CreatedUserID UNIQUEIDENTIFIER,
		@DeviceType SMALLINT,
		@DeviceTypeName VARCHAR(50);
	
	Declare @SupportedTypes TABLE (ID SMALLINT)

	INSERT INTO @SupportedTypes (ID)
	SELECT ID
	FROM DeviceType
	WHERE Name = 'Mini RWIS';

	SELECT @DebugMessage = CONCAT (
			@VendorDeviceID,
			'~',
			@VendorImageID,
			'~',
			@CaptureDateTimeUTC,
			'~',
			@Size,
			'~',
			@AmbientLight,
			'~',
			@Contrast,
			'~',
			@Brightness,
			'~',
			@Exposure,
			'~',
			@Resolution,
			'~',
			@ImageUrl,
			'~',
			@PacketIndex,
			'~',
			@PacketCount,
			'~',
			@BodyLength,
			'~',
			''
		)

	SET @IsComplete = 1
	SET @ErrorCode = 0
	SET @ErrorMessage = 'DEBUG'

	--Step 0, Check if Device exists in DB
	SELECT @DeviceID = d.ID,
		@DeviceType = d.DeviceType,
		@DeviceTypeName = dt.Name
	FROM Devices(READUNCOMMITTED) d
	INNER JOIN DeviceType(READUNCOMMITTED) dt
		ON d.DeviceType = dt.ID
	WHERE d.VendorDeviceID = @VendorDeviceID

	IF (@DeviceID IS NULL)
	BEGIN
		SET @ErrorCode = 100
		SET @ErrorMessage = 'Device Does not Exist in Database'

		RETURN @ErrorCode
	END

	BEGIN TRY
		BEGIN
			--Step 1, Upsert row in DeviceImages Table
			SET @ErrorCode = 200
			SET @ErrorMessage = 'usp_utl_InsertDeviceImages Failed'

			EXEC [dbo].[usp_utl_InsertDeviceImages] @DeviceID,
				@VendorImageID,
				@CorrectedVendorImageID,
				@IsComplete,
				@CaptureDateTimeUTC,
				@Size,
				@AmbientLight,
				@Contrast,
				@Brightness,
				@Exposure,
				@Resolution,
				@ImageUrl,
				@IsBurstImage,
				@DeviceImageID OUTPUT
		END

		IF EXISTS(
				SELECT 1
				FROM @SupportedTypes
				WHERE ID = @DeviceType
			)
		BEGIN
			SET @ErrorCode = 210
			SET @ErrorMessage = 'dbo.fn_GetLatestDeviceReadingID Failed'
			SET @DeviceReadingID = (
					SELECT ID
					FROM dbo.fn_GetLatestDeviceReadingID(@DeviceID)
				)
			SET @ErrorCode = 211
			SET @ErrorMessage = 'dbo.usp_UpdateDeviceImages Failed'

			-- Update the DeviceImages table with the DeviceReadingID
			EXEC usp_UpdateDeviceImages @DeviceImageID,
				@DeviceReadingID,
				@IsComplete
		END
		SET @ErrorCode = 0
		SET @ErrorMessage = 'SUCCESS'
	END TRY

	BEGIN CATCH
		SET @ErrorMessage = CONCAT (
				cast(ERROR_NUMBER() AS VARCHAR(20)),
				'~',
				ERROR_MESSAGE()
			)
	END CATCH

	RETURN @ErrorCode
END
