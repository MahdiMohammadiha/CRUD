import psycopg2
from abc import ABC, abstractmethod


class BaseInspector(ABC):
    """
    Abstract base class for database schema inspection.
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
        Initialize connection parameters.

        Args:
            dbname (str): Name of the database.
            user (str): Username to connect.
            password (str): Password for the user.
            host (str): Host address.
            port (int): Port number.
        """
        self.dbname: str = dbname
        self.user: str = user
        self.password: str = password
        self.host: str = host
        self.port: int = port
        self.conn: psycopg2.extensions.connection | None = None
        self.cursor: psycopg2.extensions.cursor | None = None

    @abstractmethod
    def connect(self) -> None:
        """
        Establish a connection to the database.
        Must be implemented in subclasses.
        """
        pass

    def close(self) -> None:
        """
        Close the database connection and cursor.
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
        Retrieve a list of table names from the given schema.

        Args:
            schema (str): Schema name (default is "public").

        Returns:
            list[str]: List of table names.
        """
        pass

    @abstractmethod
    def get_columns(self, table_name: str) -> list[tuple[str, str]]:
        """
        Retrieve column names and data types for a specific table.

        Args:
            table_name (str): Name of the table.

        Returns:
            list[tuple[str, str]]: List of (column_name, data_type) pairs.
        """
        pass

    def __enter__(self) -> "BaseInspector":
        """
        Support for context manager (with statement).
        Automatically connects on entry.
        """
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        """
        Support for context manager (with statement).
        Automatically closes on exit.
        """
        self.close()


class PostgresInspector(BaseInspector):
    """
    Concrete implementation of BaseInspector for PostgreSQL databases.
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
        Initialize the PostgresInspector with default host and port.
        """
        super().__init__(dbname, user, password, host, port)

    def connect(self) -> None:
        """
        Establish a connection to the PostgreSQL database.
        Closes any existing connection first.
        """
        self.close()  # Safely close previous connection if open

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
        Return a list of table names in the specified schema.
        """
        if not self.cursor:
            raise RuntimeError("Connection not established. Call connect() first.")

        self.cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            """,
            (schema,),
        )
        return [row[0] for row in self.cursor.fetchall()]

    def get_columns(self, table_name: str, schema: str = "public") -> list[tuple[str, str]]:
        """
        Return a list of column names and data types for the specified table, in correct order.
        """
        if not self.cursor:
            raise RuntimeError("Connection not established. Call connect() first.")

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
        Return the name of the primary key column for the given table.
        """
        if not self.cursor:
            raise RuntimeError("Connection not established. Call connect() first.")

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
