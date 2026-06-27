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
        "ssl_verify_cert": True,
    }

    ssl_ca = os.getenv("DB_SSL_CA") or os.getenv("CA")
    if ssl_ca:
        ssl_ca_path = ssl_ca
        if not os.path.isabs(ssl_ca_path):
            candidate = BASE_DIR / ssl_ca_path
            if candidate.exists():
                ssl_ca_path = str(candidate)
        db_config["ssl_ca"] = ssl_ca_path
    else:
        # Auto-detect CA cert: bundled file first, then common Linux system paths
        ca_candidates = [
            str(BASE_DIR / "isrgrootx1.pem"),
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/pki/tls/certs/ca-bundle.crt",
            "/etc/ssl/ca-bundle.pem",
        ]
        for ca_path in ca_candidates:
            if os.path.isfile(ca_path):
                db_config["ssl_ca"] = ca_path
                break

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
