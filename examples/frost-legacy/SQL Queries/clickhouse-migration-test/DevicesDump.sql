SELECT
        d.[ID]
      ,[GroupID]
      ,[DeviceKey]
      ,d.[IsActive]
      ,[VendorDeviceID]
      ,[VendorTypeCode]
      ,[VendorSerialNumber]
      ,d.[Name]
      ,d.[Description]
      ,[Notes]
      ,[Zone]
      ,LocationType.Name as LocationType
      ,SurfaceType.Name as SurfaceType
      ,[TransmissionInterval]
      ,[Latitude]
      ,[Longitude]
      ,[Altitude]
      ,[Height]
      ,[Distance]
      ,d.[CreatedDateTimeUTC]
      ,[CreatedUserID]
      ,d.[ModifiedDateTimeUTC]
      ,[ModifiedUserID]
      ,[VendorProductID]
      ,[LastPhotoRequestUTC]
      ,DeviceStateType.DeviceStateName as DeviceState
      ,[DeviceType].Name as DeviceType
      ,FrostDeviceRevisions.Name as Revision
      ,[SensorHeight]
  FROM [frost-db-prd].[dbo].[Devices] d
  LEFT JOIN LocationType ON d.LocationTypeID = LocationType.ID
  LEFT JOIN SurfaceType ON d.SurfaceTypeID = SurfaceType.ID
  LEFT JOIN DeviceType ON d.DeviceType = DeviceType.ID
  LEFT JOIN DeviceStateType ON d.DeviceState = DeviceStateType.ID
  LEFT JOIN FrostDeviceRevisions ON d.Revision = FrostDeviceRevisions.ID
