class IndexedView:
    def __init__(
        self,
        name,
        definition,
        clustered_index_name=None,
        cluster_index_row_definition=None,
    ):
        self.name = name
        self.definition = definition
        self.clustered_index_name = clustered_index_name
        self.cluster_index_row_definition = cluster_index_row_definition

    def create(self, op):
        op.execute(
            f"""
        CREATE VIEW {self.name}
        WITH SCHEMABINDING
        AS 
        {self.definition}
        """
        )

    def drop(self, op):
        op.execute(
            f"""
        IF OBJECT_ID('{self.name}', 'view') IS NOT NULL
            DROP VIEW {self.name}
        """
        )

    def define_index(self, op):
        op.execute(
            f"""
        CREATE UNIQUE CLUSTERED INDEX {self.clustered_index_name} ON {self.name} (
            {self.cluster_index_row_definition}
        );
        """
        )


LatestNCARForecastsSummaryView = IndexedView(
    "vw_LatestNCARForecastSummary",
    """
    SELECT
        DeviceID,
        GeneratedDateTimeUTC,
        FileName
    FROM
        dbo.forecastsummary fs
    WHERE
        FileName like 'ncpr%'
        and GeneratedDateTimeUTC > 202503060000
    """,
    clustered_index_name="IDX_GeneratedDateTimeUTC",
    cluster_index_row_definition="DeviceID, GeneratedDateTimeUTC DESC, FILENAME",
)

DeviceReadingsView = IndexedView(
    "vw_DeviceReadings",
    """
        SELECT 
            ID, 
            DeviceID,
            CaptureDateTimeUTC,
            VendorReadingID,
            DATEADD(
                MINUTE,
                DATEDIFF(MINUTE, 0, CaptureDateTimeUTC),
                0
            ) as MinuteRoundedCaptureDateTimeUTC
        FROM 
        dbo.DeviceReadings
        WHERE 
            CaptureDateTimeUTC >= CONVERT(DATE, '20240720', 112)
        """,
    clustered_index_name="IDX_DeviceID_CaptureDateTimeUTC",
    cluster_index_row_definition="DeviceID, CaptureDateTimeUTC DESC, VendorReadingID",
)


DeviceImagesView = IndexedView(
    "vw_CompleteDeviceImages",
    """
        SELECT 
            ID, 
            DeviceID,
            CaptureDateTimeUTC,
            VendorImageID,
            DeviceReadingID,
            IsComplete
        FROM 
        dbo.DeviceImages
        WHERE 
            CaptureDateTimeUTC >= CONVERT(DATE, '20240720', 112)
            and IsComplete = 1
        """,
    clustered_index_name="IDX_DeviceID_CaptureDateTimeUTC",
    cluster_index_row_definition="DeviceID, CaptureDateTimeUTC DESC, DeviceReadingID",
)
