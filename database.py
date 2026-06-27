from mysql.connector.pooling import MySQLConnectionPool
import os

from config import BASE_DIR

db_config = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 4000)),  # Port must be converted to an integer
    "user": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE"),
    "ssl_verify_cert": True                    # Keeps connection secure over the internet
}

ssl_ca = os.getenv("DB_SSL_CA") or os.getenv("CA")
if ssl_ca:
    ssl_ca_path = ssl_ca
    if not os.path.isabs(ssl_ca_path):
        candidate = BASE_DIR / ssl_ca_path
        if candidate.exists():
            ssl_ca_path = str(candidate)
    db_config["ssl_ca"] = ssl_ca_path

db_config["ssl_ca"] = Path(__file__).parent / "isrgrootx1.pem"


db_pool = MySQLConnectionPool(
    pool_name="leaveiq_pool",
    pool_size=10,
    **db_config
)

def get_db_cursor():
    connection = db_pool.get_connection()
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
