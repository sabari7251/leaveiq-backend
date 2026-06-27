from mysql.connector.pooling import MySQLConnectionPool
import os

from config import BASE_DIR

db_pool = None


def _build_db_config():
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USERNAME")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_DATABASE")

    if not all([db_host, db_user, db_password, db_name]):
        raise RuntimeError("Database environment variables are not fully configured")

    db_config = {
        "host": db_host,
        "port": int(os.getenv("DB_PORT", 4000)),
        "user": db_user,
        "password": db_password,
        "database": db_name,
        "ssl_disabled": False,
        "ssl_verify_cert": False,
        "ssl_verify_identity": False,
        "use_pure": True,
    }

    # Use explicit CA cert if provided via env var AND the file exists
    ssl_ca = os.getenv("DB_SSL_CA") or os.getenv("CA")
    if ssl_ca:
        ssl_ca_path = ssl_ca
        if not os.path.isabs(ssl_ca_path):
            candidate = BASE_DIR / ssl_ca_path
            if candidate.exists():
                ssl_ca_path = str(candidate)
        # Only use the CA if the file actually exists on this system
        if os.path.isfile(ssl_ca_path):
            db_config["ssl_ca"] = ssl_ca_path
            db_config["ssl_verify_cert"] = True

    return db_config


def _get_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = MySQLConnectionPool(
            pool_name="leaveiq_pool",
            pool_size=10,
            **_build_db_config()
        )
    return db_pool

def get_db_cursor():
    connection = _get_db_pool().get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
