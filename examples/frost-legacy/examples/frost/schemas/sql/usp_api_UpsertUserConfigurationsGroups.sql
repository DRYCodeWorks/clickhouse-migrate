CREATE PROCEDURE
    [dbo].[usp_api_UpsertUserConfigurationsGroups] @Email NVARCHAR(100),
    @DefaultViewGroupID INT = NULL,
    @EmployedAtGroupID INT = NULL,
    @ForecastIntervalHours INT = NULL,
    @SuccessCode INT = 0 OUTPUT,
    @UserID UNIQUEIDENTIFIER = NULL OUTPUT AS BEGIN TRAN USER_CONFIG_UPDATE_GROUPS
SET
    @UserID = (
        SELECT
            u.ID
        FROM
            UserConfigurations
        WITH
            (UPDLOCK, SERIALIZABLE)
            JOIN Users u ON UserConfigurations.UserID = u.ID
        WHERE
            Email = @Email
    ) IF @UserID IS NOT NULL BEGIN
UPDATE UserConfigurations
SET
    DefaultViewGroupID = CASE
        WHEN @DefaultViewGroupID IS NOT NULL THEN @DefaultViewGroupID
        ELSE DefaultViewGroupID
    END,
    EmployedAtGroupID = CASE
        WHEN @EmployedAtGroupID IS NOT NULL THEN @EmployedAtGroupID
        ELSE EmployedAtGroupID
    END,
    ForecastIntervalHours = CASE
        WHEN @ForecastIntervalHours IS NOT NULL THEN @ForecastIntervalHours
        ELSE ForecastIntervalHours
    END
WHERE
    UserID = @UserID
SET
    @SuccessCode = 200 END ELSE BEGIN
SET
    @UserID = (
        SELECT
            ID
        FROM
            USERS
        WHERE
            EMAIL = @Email
    )
INSERT INTO
    UserConfigurations (UserID, DefaultViewGroupID, EmployedAtGroupID, ForecastIntervalHours)
VALUES
    (
        @UserID,
        @DefaultViewGroupID,
        @EmployedAtGroupID,
        CASE
            WHEN @ForecastIntervalHours IS NOT NULL THEN @ForecastIntervalHours
            ELSE 72
        END
    )
SET
    @SuccessCode = 201 END COMMIT TRAN USER_CONFIG__GROUPS