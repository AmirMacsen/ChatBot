class SingletonMeta(type):
    """
    线程安全的单例元类
    """
    _instances = {}
    _lock = None

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # 使用局部导入避免在没有线程模块的环境中出错
            if cls._lock is None:
                from threading import Lock
                cls._lock = Lock()

            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]