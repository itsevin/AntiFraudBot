from nonebot import logger, get_plugin_config
from utils.config import Config as utils_Config

from alibabacloud_green20220302.client import Client
from alibabacloud_green20220302 import models
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util import models as util_models
import asyncio
import json
import uuid
import time


utils_config = get_plugin_config(utils_Config)

access_key_id = utils_config.alibaba_cloud_acess_key_id
access_key_secret = utils_config.alibaba_cloud_acess_key_secret

endpoint = 'green-cip.cn-shanghai.aliyuncs.com'


# 创建请求客户端
def create_client():
    config = Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        # 设置http代理。
        # http_proxy='http://10.10.xx.xx:xxxx',
        # 设置https代理。
        # https_proxy='https://10.10.xx.xx:xxxx',
        # 接入区域和地址请根据实际情况修改。
        endpoint=endpoint
    )
    return Client(config)


def invoke_function_post(url):
    # 注意：此处实例化的client请尽可能重复使用，避免重复建立连接，提升检测性能。
    client = create_client()
    # 创建RuntimeObject实例并设置运行参数。
    runtime = util_models.RuntimeOptions()

    # 检测参数构造。
    service_parameters = {
        # 公网可访问的url。
        'url': url,
        # 数据唯一标识
        'dataId': str(uuid.uuid1()),
        # 检测结果回调通知您的URL。
        'callback': 'http://www.aliyun.com',
        # 随机字符串，该值用于回调通知请求中的签名。
        'seed': 'itsevin666',
        # 使用回调通知时（callback），设置对回调通知内容进行签名的算法。
        'cryptType': 'SM3'
    }

    url_image_moderation_request = models.UrlAsyncModerationRequest(
        # url检测service,示例：url_detection_pro
        service='url_detection_pro',
        service_parameters=json.dumps(service_parameters)
    )

    try:
        return client.url_async_moderation_with_options(url_image_moderation_request, runtime)
    except Exception as err:
        logger.error(f"链接{url}检测api调用失败，报错： {err}")


def post(url):
    response = invoke_function_post(url)
    if response and response.status_code == 200:
        # 调用成功。
        # 获取结果ReqId。
        result = response.body
        if result.code == 200:
            return result.data
        elif result.code == 408:
            logger.error(f"链接{url}检测api调用失败,返回码：{result.code},即阿里云接口信息无正确权限，请检查配置项")
            return None
        else:
            logger.error(f"链接{url}检测api调用失败,返回码：{result.code}")
            return None
    else:
        logger.error(f"链接{url}检测api调用失败,post返回为空或请求失败")
        return None


def invoke_function_get(req_id, url):
    # 注意：此处实例化的client请尽可能重复使用，避免重复建立连接，提升检测性能。
    client = create_client()
    # 创建RuntimeObject实例并设置运行参数。
    runtime = util_models.RuntimeOptions()

    # 构造请求入参。
    describe_result_request = models.DescribeUrlModerationResultRequest(
        # 将提交异步检测任务时返回值中的ReqId作为获取结果的入参。例如：DFEXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX44
        req_id=req_id,
    )

    try:
        return client.describe_url_moderation_result_with_options(describe_result_request, runtime)
    except Exception as err:
        logger.error(f"链接{url}检测api调用失败，报错： {err}")
        return None


def get(req_id, url):
    response = invoke_function_get(req_id, url)
    # 打印结果。
    if response is not None:
        if response.status_code == 200:
            # 调用成功。
            # 获取审核结果。
            result = response.body
            if result.code == 200:
                return result.data
            elif result.code == 280: # 280为任务仍在检测中
                return 280
            else:
                logger.error("链接检测api调用失败,返回码：280")
        else:
            logger.error("链接检测api调用失败")
            return None


def sync_function(url):
    req_id = post(url)
    if req_id is None:
        logger.error("链接检测api调用失败，post无返回 req_id 信息")
        return None
    req_id = req_id.req_id
    result = get(req_id, url)
    # 检测未结束就一直检测
    while result == 280:
        time.sleep(2)
        result = get(req_id, url)
    return result.result[0].label


async def url_detection_api(url):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, lambda: sync_function(url))
    return result
