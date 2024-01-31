class Config(object):
    DEBUG = True
    FLASK_SLOW_DB_QUERY_TIME= 0.5
    SQLALCHEMY_RECORD_QUERIES= True # 启用缓慢查询记录功能的配置-启用记录查询统计数据的功能