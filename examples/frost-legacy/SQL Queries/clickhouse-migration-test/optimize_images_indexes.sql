-- Optimized index for CaptureDateTimeUTC range queries
CREATE NONCLUSTERED INDEX IDX_DeviceImages_CaptureDateTimeUTC_Covering
ON DeviceImages (CaptureDateTimeUTC, DeviceID)
INCLUDE (VendorImageID, IsComplete, IsBurstImage, Size, AmbientLight, Contrast, 
         Brightness, Exposure, Resolution, ImageUrl, CreateDateTimeUTC, 
         ModifiedDateTimeUTC, DeviceReadingID)

