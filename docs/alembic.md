### alembic

- 下载依赖
```shell
uv add alembic
```

- init
```shell
- alembic init --template async alembic
```

- 修改配置

```shell
# alembic.ini
添加数据库连接信息

# alembic/env.py
添加Base模型

```

- 创建迁移文件

```shell
alembic revision --autogenerate -m "init"
```

- 运行迁移文件
```shell
alembic upgrade head
```