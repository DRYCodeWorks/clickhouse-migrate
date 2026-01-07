SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
SELECT 
    di.[DeviceID]
    ,[VendorImageID]
    ,[IsComplete]
    ,[IsBurstImage]
    ,di.CaptureDateTimeUTC
    ,[Size]
    ,di.[AmbientLight]
    ,[Contrast]
    ,[Brightness]
    ,[Exposure]
    ,[Resolution]
    ,[ImageUrl]
    ,di.[CreateDateTimeUTC]
    ,di.[ModifiedDateTimeUTC]
    ,[ImageID]
    ,[NightClearPavement]
    ,[NightSnowing]
    ,[NightWetPavement]
    ,[NightSnowOnRoad]
    ,[NightPartialSnowOnRoad]
    ,[DaySnowing]
    ,[DayPartialSnowOnRoad]
    ,[DayClearPavement]
    ,[DayWetPavement]
    ,[DaySnowOnRoad]
    ,[Night]
    ,[Sunny]
    ,[Cloudy]
    ,[ClearPavement]
    ,[WetPavement]
    ,[SnowOnRoad]
    ,[PartialSnowOnRoad]
    ,[Snowing]
    ,[Raining]
    ,[ModelVersion]
    ,[IcedLens]
    ,dr.CaptureDateTimeUTC as TransmissionCaptureDateTimeUTC
FROM DeviceImages di
LEFT JOIN ComputerVision cv ON di.ID = cv.ImageID
LEFT JOIN DeviceReadings dr ON dr.ID = di.DeviceReadingID
WHERE di.CaptureDateTimeUTC >= ? AND di.CaptureDateTimeUTC < ?
ORDER BY di.DeviceID, di.CaptureDateTimeUTC DESC