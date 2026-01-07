
INSERT INTO paired_latest_image_transmissions 
WITH SelectTransmissions as (
	SELECT * FROM transmissions t where (t.DeviceID, t.CaptureDateTimeUTC) in (SELECT (i.DeviceID, i.TransmissionCaptureDateTimeUTC) FROM get_latest_images i)
)
SELECT
    -- Shared
	i.DeviceID,
    i.DeviceID as LocationID,
	i.VendorDeviceID,
	i.AmbientLight,
	-- transmissions
	t.ID,
	t.CaptureTimestampUTC,
	t.CaptureDateTimeUTC as TransmissionDateTimeUTC,
	t.SurfaceTemp,
	t.AirTemp,
	t.DewPoint,
	t.Humidity,
	t.HeaterTemp,
	-- images
	i.VendorImageID,
	i.CameraVersion,
	i.ImageBucket,
	i.ImageFormat,
	i.ModifiedDateTimeUTC,
	i.CaptureDateTimeUTC as ImageCaptureDateTimeUTC,
    i.ImageAssembledDateTimeUTC,
    i.CVAssessmentDateTimeUTC,
	i.IsComplete,
	i.Contrast,
	i.Brightness,
	i.Exposure,
	i.Resolution,
	i.ImageUrl,
	i.ImageID,
	i.NightClearPavement,
	i.NightSnowing,
	i.NightWetPavement,
	i.NightSnowOnRoad,
	i.NightPartialSnowOnRoad,
	i.DaySnowing,
	i.DayPartialSnowOnRoad,
	i.DayClearPavement,
	i.DayWetPavement,
	i.DaySnowOnRoad,
	i.Night,
	i.Sunny,
	i.Cloudy,
	i.ClearPavement,
	i.WetPavement,
	i.SnowOnRoad,
	i.PartialSnowOnRoad,
	i.Snowing,
	i.Raining,
	i.ModelVersion,
	i.IcedLens,
	i.Version,
    i.IsBurstImage,
    2 as TransmissionType
FROM SelectTransmissions t 
INNER JOIN latest_images i FINAL
    ON  t.DeviceID = i.DeviceID
    AND  t.CaptureDateTimeUTC = i.TransmissionCaptureDateTimeUTC
