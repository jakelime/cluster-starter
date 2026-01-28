import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Self

import pandas as pd
import pymongo as pymg
from pymongo import MongoClient, errors
from pymongo.write_concern import WriteConcern

logger = logging.getLogger("django")


def chunked(
    iterable: List[Dict[str, Any]], size: int
) -> Iterable[List[Dict[str, Any]]]:
    """Yield successive chunks of given size from a list."""
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


class DbHelperTemplate(ABC):
    """Use this constructor to create
    database helpers for databases"""

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def insert_one(self):
        pass

    def obscure_password(
        self, connection_str: str, mask: str = "***", partial: bool = False
    ) -> str:
        """
        Return a copy of the connection str URI with the password obscured.

        Examples
        --------
        >>> obscure_mongodb_password("mongodb://pproot:sFdDNzT5fyFPDaHSjEsS8x@localhost:27008/")
        'mongodb://pproot:***@localhost:27008/'

        >>> obscure_mongodb_password("mongodb+srv://user:Top$ecret@cluster0.example.net/db?retryWrites=true")
        'mongodb+srv://user:***@cluster0.example.net/db?retryWrites=true'

        >>> obscure_mongodb_password("mongodb://pproot@s1.example.net,s2.example.net/db")
        'mongodb://pproot@s1.example.net,s2.example.net/db'   # no password present -> unchanged

        Parameters
        ----------
        uri : str
            The MongoDB connection string.
        mask : str
            The replacement text for the password. Use only URL-safe characters if you
            care about strict RFC compliance; letters/numbers are safe. Default "REDACTED".
        partial : bool
            If True, only partially mask (keep first and last character when available).

        Notes
        -----
        * We rely on the fact that MongoDB credentials appear as:
            scheme://<username>:<password>@<hosts>[/...]
        We only modify the substring before the first '@' within the authority section.
        * If no password (no ':' in userinfo), the URI is returned unchanged.
        """
        uri = connection_str
        if not uri:
            raise KeyError("mongo_uri is not definted in the MongoLader")
        scheme_sep = "://"
        scheme_idx = uri.find(scheme_sep)
        if scheme_idx == -1:
            return uri  # Not a URI we recognize; leave unchanged.

        auth_start = scheme_idx + len(scheme_sep)

        # Determine where the authority (userinfo + hosts) segment ends
        # (first of '/', '?', or '#' after the scheme).
        end_authority = len(uri)
        for sep in ("/", "?", "#"):
            pos = uri.find(sep, auth_start)
            if pos != -1:
                end_authority = min(end_authority, pos)

        at_idx = uri.find("@", auth_start, end_authority)
        if at_idx == -1:
            return uri  # No userinfo -> nothing to mask.

        userinfo = uri[auth_start:at_idx]
        colon_idx = userinfo.find(":")
        if colon_idx == -1:
            return uri  # Username only -> nothing to mask.

        username = userinfo[:colon_idx]
        password = userinfo[colon_idx + 1 :]

        if partial and password:
            if len(password) == 1:
                masked = "*"
            elif len(password) == 2:
                masked = password[0] + "*"
            else:
                masked = password[0] + ("*" * (len(password) - 2)) + password[-1]
        else:
            masked = mask

        masked_userinfo = f"{username}:{masked}"
        return uri[:auth_start] + masked_userinfo + uri[at_idx:]

    def check_read_write_access(self) -> None:
        """
        Read: list DBs or collections.
        Write: insert + delete in a temporary collection.
        """
        logger.info("Verifying read/write access...")
        try:
            # Read check
            _ = self.client.list_database_names()
            _ = self.db.list_collection_names()

            # Write check using a temp collection
            temp_coll_name = "__dbsd_rw_check__"
            temp_coll = self.db.get_collection(
                temp_coll_name, write_concern=WriteConcern(w=1)
            )
            res = temp_coll.insert_one(
                {"_ts": datetime.now(timezone.utc), "_type": "rw_check"}
            )
            _ = temp_coll.delete_one({"_id": res.inserted_id})
            # Clean up: drop temp collection (best effort)
            try:
                self.db.drop_collection(temp_coll_name)
            except errors.PyMongoError:
                pass

            logger.info("Read/Write access: OK")
        except errors.PyMongoError as e:
            raise Exception("Read/Write access check failed.") from e


class DbHelper(DbHelperTemplate):
    """Placeholder for SQL Databases"""

    pass


class MongoDbHelperTemplate(DbHelperTemplate):
    @abstractmethod
    def connect_to_collection(self):
        raise NotImplementedError()

    def insert_one(
        self, record: Dict[str, Any], ordered: bool = True
    ) -> Optional[pymg.results.InsertOneResult]:
        """
        Insert a single document into the collection.
        Returns the result of the insert operation.
        """
        try:
            result = self.collection.insert_one(record)
            logger.debug(f"Inserted one document: {result.inserted_id}")
            return result
        except errors.PyMongoError as e:
            logger.error(f"Insert one failed: {e=}")
            return None

    def report_insert_error_details(self, e: errors.BulkWriteError) -> None:
        logger.warning("Bulk write error, some docs may have failed.")
        logger.warning(f"Error code: {e.code}:")
        for k, v in e.details.items():
            text = str(v)
            if len(text) > 50:
                text = text[:50] + "..."
            logger.warning(f"  {k}: {text}")

    def insert_data_chunked(self, data: list[Dict], debug_mode: bool = False) -> int:
        """
        Insert data using a pd.DataFrame or a list[Dict]
        Returns number of documents inserted.
        """
        total = 0
        logger.info(
            f"Inserting {len(data)} documents into '{self.collection.database.name}.{self.collection.name}' in batches of {self.batch_size}..."
        )
        for batch in chunked(data, self.batch_size):
            try:
                result = self.collection.insert_many(batch, ordered=False)
                total += len(result.inserted_ids)
            except errors.BulkWriteError as e:
                if debug_mode:
                    self.report_insert_error_details(e)
                if e.details:
                    total += e.details.get("nInserted", 0)
            except errors.PyMongoError as e:
                logger.exception(f"An error occurred during batch insert: {e}")
                break
        logger.info(f"  Done -> total documents inserted: {total}")
        return total

    def insert_dataframe_chunked(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        records = df.to_dict(orient="records")
        return self.insert_data_chunked(records)

    def query_data(
        self, query: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Read documents from the collection based on a query.

        Parameters
        ----------
        query : Dict[str, Any], optional
            A dictionary specifying the selection criteria. If None, all documents
            in the collection will be returned. The default is None.  1

        Returns
        -------
        List[Dict[str, Any]]
            A list of documents matching the query.
        """
        if self.db is None or self.collection is None:
            raise RuntimeError("Database or collection not initialized.")
        if query is None:
            query = {}
        logger.info(
            f"Reading data from '{self.collection.database.name}.{self.collection.name}' with query: {query}"
        )
        try:
            cursor = self.collection.find(query)
            data = list(cursor)
            logger.info(f"fetched {len(data)} documents from {self.collection.name}")
            return data
        except errors.PyMongoError as e:
            logger.error(f"Failed to read data: {e}")
            return []


class MongoDbHelper(MongoDbHelperTemplate):
    def __init__(
        self,
        connection_str: str,
        collection_name: str = "default_collection",
        batch_size: int = 1000,
        connect_timeout_ms: int = 5000,
        server_selection_timeout_ms: int = 5000,
    ):
        self.connection_str = connection_str
        self.collection_name = collection_name
        self.batch_size = batch_size
        self.client: Optional[MongoClient] = None
        self.collection = None
        self.db = None
        self._client_kwargs = {
            "connectTimeoutMS": connect_timeout_ms,
            "serverSelectionTimeoutMS": server_selection_timeout_ms,
        }

    def connect(self) -> Self:
        logger.info(
            f"Connecting to MongoDB({self.obscure_password(self.connection_str)})..."
        )
        try:
            self.client = MongoClient(self.connection_str, **self._client_kwargs)
            # Quick connectivity check
            self.client.admin.command("ping")
            logger.info("Connected to MongoDB.")
        except errors.PyMongoError as e:
            logger.exception("Failed to connect to MongoDB.")
            raise SystemExit(2) from e

        self.db = self.client.get_database()
        self.connect_to_collection(self.collection_name)
        return self

    def connect_to_collection(self, collection_name: Optional[str] = None) -> None:
        if self.db is None:
            raise RuntimeError("db not initialized yet.")
        if collection_name:
            self.collection_name = collection_name
        self.collection = self.db.get_collection(
            self.collection_name, write_concern=WriteConcern(w=1)
        )

    def init_collection(
        self,
        collection_name: Optional[str] = None,
        index_names: Optional[list[str]] = ["data_hash"],
    ) -> None:
        cname = collection_name or self.collection_name
        self.connect_to_collection(cname)
        if index_names:
            for id_name in index_names:
                self.collection.create_index(
                    [(id_name, pymg.ASCENDING)],
                    unique=True,
                    name=f"idx_unique_{id_name}",
                )
                logger.info(f"Index created successfully on '{id_name}'.")
