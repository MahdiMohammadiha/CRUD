import psycopg2
from abc import ABC, abstractmethod


class BaseInspector(ABC):
    """
    Abstract base class for database schema inspection.

    This class defines a consistent interface for connecting to a database,
    retrieving table information, and managing resources.
    Subclasses must implement the abstract methods `connect`, `get_tables`,
    and `get_columns` according to the database type.
    """

    def __init__(
        self,
        dbname: str,
        user: str,
        password: str,
        host: str,
        port: int,
    ) -> None:
        """
        Store database connection parameters without connecting yet.

        Args:
            dbname: Name of the database.
            user: Database username.
            password: Password for the database user.
            host: Database server host.
            port: Database server port.
        """
        self.dbname: str = dbname
        self.user: str = user
        self.password: str = password
        self.host: str = host
        self.port: int = port

        # Connection and cursor will be set when connect() is called
        self.conn: psycopg2.extensions.connection | None = None
        self.cursor: psycopg2.extensions.cursor | None = None

    @abstractmethod
    def connect(self) -> None:
        """
        Establish a connection to the database.
        Must be implemented in subclasses for the specific database type.
        """
        pass

    def close(self) -> None:
        """
        Close the database connection and cursor if they are open.
        """
        if self.cursor:
            self.cursor.close()
            self.cursor = None

        if self.conn:
            self.conn.close()
            self.conn = None

    @abstractmethod
    def get_tables(self, schema: str = "public") -> list[str]:
        """
        Retrieve the names of all tables in the given schema.

        Args:
            schema: Name of the schema (default "public").

        Returns:
            A list of table names.
        """
        pass

    @abstractmethod
    def get_columns(self, table_name: str) -> list[tuple[str, str]]:
        """
        Retrieve column names and their data types for a given table.

        Args:
            table_name: The table to inspect.

        Returns:
            A list of tuples: (column_name, data_type).
        """
        pass

    def __enter__(self) -> "BaseInspector":
        """
        Context manager entry point.
        Calls connect() automatically when used with `with` statement.
        """
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        """
        Context manager exit point.
        Closes the connection automatically.
        """
        self.close()


class PostgresInspector(BaseInspector):
    """
    Inspector for PostgreSQL databases.

    This class implements the abstract methods of BaseInspector
    specifically for PostgreSQL using psycopg2.
    """

    def __init__(
        self,
        dbname: str,
        user: str,
        password: str,
        host: str = "localhost",
        port: int = 5432,
    ) -> None:
        """
        Initialize the PostgresInspector with PostgreSQL defaults.
        """
        super().__init__(dbname, user, password, host, port)

    def connect(self) -> None:
        """
        Connect to the PostgreSQL database using psycopg2.
        Any existing connection will be closed first.
        """
        self.close()  # Close any old connection to avoid leaks

        self.conn = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        )
        self.cursor = self.conn.cursor()

    def get_tables(self, schema: str = "public") -> list[str]:
        """
        Get all table names from a given schema.

        Args:
            schema: Schema name (default "public").

        Returns:
            A list of table names.
        """
        if not self.cursor:
            raise RuntimeError("No active connection. Call connect() first.")

        self.cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            """,
            (schema,),
        )
        return [row[0] for row in self.cursor.fetchall()]

    def get_columns(
        self, table_name: str, schema: str = "public"
    ) -> list[tuple[str, str]]:
        """
        Get column names and their data types for a table.

        Args:
            table_name: Table name.
            schema: Schema name (default "public").

        Returns:
            List of (column_name, data_type) tuples in order of definition.
        """
        if not self.cursor:
            raise RuntimeError("No active connection. Call connect() first.")

        self.cursor.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = %s
            ORDER BY ordinal_position
            """,
            (table_name, schema),
        )
        return self.cursor.fetchall()

    def get_primary_key(self, table_name: str, schema: str = "public") -> str | None:
        """
        Get the primary key column name for a given table.

        Args:
            table_name: Name of the table.
            schema: Schema name (default "public").

        Returns:
            The primary key column name if found, else None.
        """
        if not self.cursor:
            raise RuntimeError("No active connection. Call connect() first.")

        self.cursor.execute(
            """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_name = %s
            AND tc.table_schema = %s
            LIMIT 1
            """,
            (table_name, schema),
        )

        row = self.cursor.fetchone()
        return row[0] if row else None
