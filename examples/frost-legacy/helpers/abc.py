class ABCFunction:
    def __init__(self, name, create_sqltext, version=None, grant_users=None):
        self.sql = create_sqltext
        self.base_name = name
        self.version = version
        self.grant_users = grant_users or ["vendor_feeds", "frost_api"]
        
        # Build full name with version suffix if provided
        self.name = f"{name}_v{version}" if version else name

    def create_function(self, op):
        op.execute(self.sql)
        
        # Generate grant permissions if users specified
        if self.grant_users:
            users_list = ", ".join(self.grant_users)
            op.execute(
                f"""
                -- Grant permissions to the table-valued function
                IF EXISTS
                (
                    SELECT 
                        1
                    FROM sys.objects 
                    WHERE type IN ('TF', 'IF', 'FT')
                        AND name = '{self.name}'
                )
                -- If the function is a table-valued function, grant SELECT permissions
                BEGIN
                    GRANT SELECT ON OBJECT::{self.name}
                        TO {users_list};
                END
                -- If the function is scalar function, grant EXECUTE permissions
                ELSE 
                BEGIN
                    GRANT EXECUTE ON OBJECT::{self.name}
                        TO {users_list};
                END;
                """
            )

    def drop_function(self, op): ...
