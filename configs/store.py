DATABASE_TYPE = "mysql"

default_database = {
    "mysql": {
        "driver": "aiomysql",
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "root",
        "database": "chatbot",
        "charset": "utf8mb4"
    }
}


def get_database_url(database_type:str="mysql"):
    database = default_database.get(database_type)
    return f"{database_type}+{database['driver']}://{database['user']}:{database['password']}@{database['host']}:{database['port']}/{database['database']}?charset={database['charset']}"