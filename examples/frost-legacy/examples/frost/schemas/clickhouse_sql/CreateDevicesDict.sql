CREATE DICTIONARY devices (
    ID	UInt32,
    GroupID	UInt64,
    DeviceKey	String,
    IsActive	Boolean,
    VendorDeviceID	String,
    VendorTypeCode	String,
    Name	String,
    Description	String,
    Notes	String,
    Zone	String,
    Latitude  Float32,
    Longitude  Float32,
    ModifiedDateTimeUTC	DateTime64,
    CreatedDateTimeUTC DateTime64,
    Altitude	Float32,
    Height	Float32,
    SensorHeight	Float32,
    Distance	Float32,
    CreatedUserID String,
    ModifiedUserID String,
    VendorProductID String,
    LastPhotoRequestUTC DateTime64,
    TransmissionInterval Int8,
    LocationType	String,
    SurfaceType	String,
    DeviceState	String,
    DeviceType	String,
    Revision	String
    )
PRIMARY KEY ID
SOURCE(HTTP(url '@dpa_url/clickhouse/devices'
format 'JSONEachRow'
headers(header(name 'api-key' value '@api_key'))
))
LIFETIME(600)
LAYOUT(Flat())
