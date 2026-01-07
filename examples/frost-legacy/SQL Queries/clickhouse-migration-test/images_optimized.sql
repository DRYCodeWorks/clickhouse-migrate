-- Optimized version of the images query
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

-- Option 1: Using existing indexes more efficiently
WITH FilteredImages AS (
    SELECT 
        di.ID, di.DeviceID, di.VendorImageID, di.IsComplete, di.IsBurstImage, 
        di.CaptureDateTimeUTC, di.Size, di.AmbientLight, di.Contrast, 
        di.Brightness, di.Exposure, di.Resolution, di.ImageUrl,
        di.CreateDateTimeUTC, di.ModifiedDateTimeUTC, di.DeviceReadingID
    FROM DeviceImages di WITH (NOLOCK, INDEX(IDX_DeviceImages_CaptureDateTimeUTC))
    WHERE di.CaptureDateTimeUTC >= ? AND di.CaptureDateTimeUTC < ?
)
SELECT 
    fi.DeviceID, fi.VendorImageID, fi.IsComplete, fi.IsBurstImage, fi.CaptureDateTimeUTC,
    fi.Size, fi.AmbientLight, fi.Contrast, fi.Brightness, fi.Exposure, fi.Resolution, fi.ImageUrl,
    fi.CreateDateTimeUTC, fi.ModifiedDateTimeUTC, fi.ID as ImageID,
    cv.NightClearPavement, cv.NightSnowing, cv.NightWetPavement, cv.NightSnowOnRoad, cv.NightPartialSnowOnRoad,
    cv.DaySnowing, cv.DayPartialSnowOnRoad, cv.DayClearPavement, cv.DayWetPavement, cv.DaySnowOnRoad,
    cv.Night, cv.Sunny, cv.Cloudy, cv.ClearPavement, cv.WetPavement, cv.SnowOnRoad, cv.PartialSnowOnRoad,
    cv.Snowing, cv.Raining, cv.ModelVersion, cv.IcedLens,
    dr.CaptureDateTimeUTC as TransmissionCaptureDateTimeUTC
FROM FilteredImages fi
LEFT JOIN ComputerVision cv WITH (NOLOCK) ON fi.ID = cv.ImageID
LEFT JOIN DeviceReadings dr WITH (NOLOCK) ON dr.ID = fi.DeviceReadingID
ORDER BY fi.DeviceID, fi.CaptureDateTimeUTC DESC

-- Option 2: Direct optimized query (recommended if you create the covering index)
SELECT 
    di.DeviceID, di.VendorImageID, di.IsComplete, di.IsBurstImage, di.CaptureDateTimeUTC,
    di.Size, di.AmbientLight, di.Contrast, di.Brightness, di.Exposure, di.Resolution, di.ImageUrl,
    di.CreateDateTimeUTC, di.ModifiedDateTimeUTC, di.ID as ImageID,
    cv.NightClearPavement, cv.NightSnowing, cv.NightWetPavement, cv.NightSnowOnRoad, cv.NightPartialSnowOnRoad,
    cv.DaySnowing, cv.DayPartialSnowOnRoad, cv.DayClearPavement, cv.DayWetPavement, cv.DaySnowOnRoad,
    cv.Night, cv.Sunny, cv.Cloudy, cv.ClearPavement, cv.WetPavement, cv.SnowOnRoad, cv.PartialSnowOnRoad,
    cv.Snowing, cv.Raining, cv.ModelVersion, cv.IcedLens,
    dr.CaptureDateTimeUTC as TransmissionCaptureDateTimeUTC
FROM DeviceImages di WITH (NOLOCK, INDEX(IDX_DeviceImages_CaptureDateTimeUTC_Covering))
LEFT JOIN ComputerVision cv WITH (NOLOCK) ON di.ID = cv.ImageID  
LEFT JOIN DeviceReadings dr WITH (NOLOCK) ON dr.ID = di.DeviceReadingID
WHERE di.CaptureDateTimeUTC >= ? AND di.CaptureDateTimeUTC < ?
ORDER BY di.DeviceID, di.CaptureDateTimeUTC DESC;
