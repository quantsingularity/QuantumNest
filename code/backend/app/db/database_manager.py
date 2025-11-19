import threading
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Generator, Optional

from app.core.config import get_database_url, get_settings
from app.core.logging import get_logger, performance_logger
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = get_logger(__name__)


class DatabaseManager:
    """Advanced database manager with connection pooling, monitoring, and optimization"""

    def __init__(self):
        self.settings = get_settings()
        self.database_url = get_database_url(self.settings)
        self.engine = None
        self.SessionLocal = None
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "query_count": 0,
            "slow_queries": 0,
            "last_reset": datetime.utcnow(),
        }
        self._slow_query_threshold = 1.0  # seconds
        self._lock = threading.Lock()

    def initialize(self):
        """Initialize database engine and session factory"""
        try:
            # Create engine with optimized settings
            engine_kwargs = {
                "poolclass": QueuePool,
                "pool_size": self.settings.DATABASE_POOL_SIZE,
                "max_overflow": self.settings.DATABASE_MAX_OVERFLOW,
                "pool_timeout": self.settings.DATABASE_POOL_TIMEOUT,
                "pool_recycle": self.settings.DATABASE_POOL_RECYCLE,
                "pool_pre_ping": True,  # Verify connections before use
                "echo": self.settings.DEBUG,  # Log SQL queries in debug mode
                "echo_pool": self.settings.DEBUG,  # Log pool events in debug mode
            }

            # SQLite specific optimizations
            if self.database_url.startswith("sqlite"):
                engine_kwargs.update(
                    {
                        "poolclass": pool.StaticPool,
                        "connect_args": {
                            "check_same_thread": False,
                            "timeout": 20,
                            "isolation_level": None,  # Enable autocommit mode
                        },
                    }
                )

            self.engine = create_engine(self.database_url, **engine_kwargs)

            # Set up event listeners for monitoring
            self._setup_event_listeners()

            # Configure SQLite for better performance
            if self.database_url.startswith("sqlite"):
                self._configure_sqlite()

            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

            logger.info(
                "Database manager initialized successfully",
                extra={"database_url": self.database_url.split("@")[-1]},
            )  # Hide credentials

        except Exception as e:
            logger.error(
                f"Failed to initialize database manager: {str(e)}", exc_info=True
            )
            raise

    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for monitoring"""

        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            with self._lock:
                self._connection_stats["total_connections"] += 1
                self._connection_stats["active_connections"] += 1

            logger.debug("Database connection established")

        @event.listens_for(self.engine, "close")
        def on_close(dbapi_connection, connection_record):
            with self._lock:
                self._connection_stats["active_connections"] -= 1

            logger.debug("Database connection closed")

        @event.listens_for(self.engine, "close_detached")
        def on_close_detached(dbapi_connection):
            with self._lock:
                self._connection_stats["active_connections"] -= 1

        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            context._query_start_time = time.time()

        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            total_time = time.time() - context._query_start_time

            with self._lock:
                self._connection_stats["query_count"] += 1
                if total_time > self._slow_query_threshold:
                    self._connection_stats["slow_queries"] += 1

            # Log slow queries
            if total_time > self._slow_query_threshold:
                logger.warning(
                    f"Slow query detected: {total_time:.3f}s",
                    extra={
                        "query_time": total_time,
                        "statement": (
                            statement[:200] + "..."
                            if len(statement) > 200
                            else statement
                        ),
                    },
                )

            # Log to performance logger
            performance_logger.log_database_query(
                statement.split()[0] if statement else "UNKNOWN", total_time
            )

    def _configure_sqlite(self):
        """Configure SQLite for better performance"""

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()

            # Performance optimizations
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes
            cursor.execute("PRAGMA cache_size=10000")  # Larger cache
            cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory map

            # Foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")

            cursor.close()

    @contextmanager
    def get_db_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        if not self.SessionLocal:
            raise RuntimeError("Database manager not initialized")

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}", exc_info=True)
            raise
        finally:
            session.close()

    def get_db(self) -> Generator[Session, None, None]:
        """FastAPI dependency for getting database session"""
        with self.get_db_session() as session:
            yield session

    def execute_raw_sql(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute raw SQL query"""
        try:
            with self.get_db_session() as session:
                result = session.execute(text(query), params or {})
                if query.strip().upper().startswith("SELECT"):
                    return result.fetchall()
                return result.rowcount
        except Exception as e:
            logger.error(f"Error executing raw SQL: {str(e)}", exc_info=True)
            raise

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get database connection statistics"""
        with self._lock:
            stats = self._connection_stats.copy()

        # Add engine pool stats if available
        if hasattr(self.engine.pool, "size"):
            stats.update(
                {
                    "pool_size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow(),
                    "invalid": self.engine.pool.invalid(),
                }
            )

        return stats

    def reset_stats(self):
        """Reset connection statistics"""
        with self._lock:
            self._connection_stats.update(
                {
                    "total_connections": 0,
                    "active_connections": self._connection_stats[
                        "active_connections"
                    ],  # Keep current active
                    "failed_connections": 0,
                    "query_count": 0,
                    "slow_queries": 0,
                    "last_reset": datetime.utcnow(),
                }
            )

        logger.info("Database statistics reset")

    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            start_time = time.time()

            with self.get_db_session() as session:
                # Simple query to test connectivity
                result = session.execute(text("SELECT 1"))
                result.fetchone()

            response_time = time.time() - start_time

            return {
                "status": "healthy",
                "response_time": response_time,
                "timestamp": datetime.utcnow().isoformat(),
                "stats": self.get_connection_stats(),
            }

        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def optimize_database(self):
        """Perform database optimization tasks"""
        try:
            if self.database_url.startswith("sqlite"):
                self._optimize_sqlite()
            else:
                self._optimize_postgresql()

            logger.info("Database optimization completed")

        except Exception as e:
            logger.error(f"Database optimization failed: {str(e)}", exc_info=True)

    def _optimize_sqlite(self):
        """SQLite-specific optimizations"""
        with self.get_db_session() as session:
            # Analyze database for query optimization
            session.execute(text("ANALYZE"))

            # Vacuum to reclaim space and defragment
            session.execute(text("VACUUM"))

            # Update statistics
            session.execute(text("PRAGMA optimize"))

    def _optimize_postgresql(self):
        """PostgreSQL-specific optimizations"""
        with self.get_db_session() as session:
            # Analyze tables for query optimization
            session.execute(text("ANALYZE"))

            # Note: VACUUM would typically be run by a maintenance job
            # session.execute(text("VACUUM ANALYZE"))

    def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            if self.database_url.startswith("sqlite"):
                return self._backup_sqlite(backup_path)
            else:
                logger.warning("Backup not implemented for this database type")
                return False

        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}", exc_info=True)
            return False

    def _backup_sqlite(self, backup_path: str) -> bool:
        """Create SQLite backup"""
        import shutil

        try:
            # Extract database path from URL
            db_path = self.database_url.replace("sqlite:///", "")

            # Simple file copy for SQLite
            shutil.copy2(db_path, backup_path)

            logger.info(f"SQLite database backed up to {backup_path}")
            return True

        except Exception as e:
            logger.error(f"SQLite backup failed: {str(e)}")
            return False

    def close(self):
        """Close database connections and cleanup"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}")


# Global database manager instance
db_manager = DatabaseManager()


# Convenience function for FastAPI dependency injection
def get_database() -> Generator[Session, None, None]:
    """FastAPI dependency for database session"""
    yield from db_manager.get_db()


# Database initialization function
def init_database():
    """Initialize database manager"""
    db_manager.initialize()


# Database cleanup function
def close_database():
    """Close database connections"""
    db_manager.close()


class DatabaseMiddleware:
    """Middleware for database session management and monitoring"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        # Add database session to scope if needed
        scope["db_manager"] = db_manager

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Log database stats for this request
                duration = time.time() - start_time
                if duration > 1.0:  # Log slow requests
                    logger.warning(
                        f"Slow request: {duration:.3f}s",
                        extra={
                            "request_duration": duration,
                            "path": scope.get("path", "unknown"),
                        },
                    )
            await send(message)

        await self.app(scope, receive, send_wrapper)


# Query optimization utilities
class QueryOptimizer:
    """Utilities for query optimization and analysis"""

    @staticmethod
    def explain_query(session: Session, query) -> Dict[str, Any]:
        """Get query execution plan"""
        try:
            # This would be database-specific
            if hasattr(query, "statement"):
                stmt = str(
                    query.statement.compile(compile_kwargs={"literal_binds": True})
                )
                result = session.execute(text(f"EXPLAIN QUERY PLAN {stmt}"))
                return {"query": stmt, "plan": [dict(row) for row in result]}
            return {"error": "Unable to analyze query"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_table_stats(session: Session, table_name: str) -> Dict[str, Any]:
        """Get table statistics"""
        try:
            # Get row count
            count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            row_count = count_result.scalar()

            # Get table info (SQLite specific)
            info_result = session.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [dict(row) for row in info_result]

            return {
                "table_name": table_name,
                "row_count": row_count,
                "columns": columns,
            }
        except Exception as e:
            return {"error": str(e)}


# Connection pool monitoring
class PoolMonitor:
    """Monitor database connection pool health"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.alerts_sent = set()

    def check_pool_health(self) -> Dict[str, Any]:
        """Check connection pool health and return status"""
        stats = self.db_manager.get_connection_stats()
        alerts = []

        # Check for high connection usage
        if hasattr(self.db_manager.engine.pool, "size"):
            pool_size = self.db_manager.engine.pool.size()
            checked_out = self.db_manager.engine.pool.checkedout()

            if pool_size > 0:
                utilization = checked_out / pool_size
                if utilization > 0.8:  # 80% utilization
                    alert = "High connection pool utilization"
                    alerts.append(alert)
                    if alert not in self.alerts_sent:
                        logger.warning(alert, extra={"utilization": utilization})
                        self.alerts_sent.add(alert)

        # Check for slow queries
        if stats["slow_queries"] > 10:
            alert = "High number of slow queries detected"
            alerts.append(alert)
            if alert not in self.alerts_sent:
                logger.warning(alert, extra={"slow_queries": stats["slow_queries"]})
                self.alerts_sent.add(alert)

        # Clear alerts if conditions improve
        if not alerts:
            self.alerts_sent.clear()

        return {
            "status": "warning" if alerts else "healthy",
            "alerts": alerts,
            "stats": stats,
        }
