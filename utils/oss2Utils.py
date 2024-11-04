import os
import requests
from loguru import logger
from urllib.parse import urlparse
from oss2 import Auth, Bucket
from utils.configUtils import read_config
# 阿里云OSS配置
ACCESS_KEY_ID = read_config('access_key')
ACCESS_KEY_SECRET = read_config('access_secret')
BUCKET_NAME = read_config('bucket')
ENDPOINT = read_config('oss-endpoint')

# 创建OSS客户端
auth = Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
bucket = Bucket(auth, ENDPOINT, BUCKET_NAME)


def upload_to_oss(url):
    """上传媒体文件至OSS并返回文件链接"""
    if url == '':
        return url
    try:
        # 获取文件名
        parsed_url = urlparse(url)
        file_name = os.path.basename(parsed_url.path)

        # 上传文件到OSS
        oss_path = f"twritter/{file_name}"
        if bucket.object_exists(oss_path):
            oss_url = f"http://static.touchbiz.tech/{oss_path}"
            logger.info(f"File already exists on OSS: {oss_url}")
            return oss_url
        # 下载文件内容
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 检查请求成功
        bucket.put_object(oss_path, response.content)      
        # 构造OSS文件的公开URL
        return f"http://static.touchbiz.tech/{oss_path}"
    except Exception as e:
        logger.error(f"Failed to upload {url} to OSS: {e}")
        return None
