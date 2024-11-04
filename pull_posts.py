
from loguru import logger
from data import database
from data.model.BloggerTweet import BloggerTweet
from data.model.Blogger import Blogger
import time
import requests
import urllib.parse
import json
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # type: ignore
import urllib3
from utils.oss2Utils import upload_to_oss
# 禁用 InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置重试策略
retry_strategy = Retry(
    total=5,  # 总重试次数
    backoff_factor=1,  # 每次重试之间的等待时间（指数递增）
    status_forcelist=[429, 500, 502, 503, 504],  # 针对这些状态码进行重试
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)

# 创建一个 Session 并配置连接池
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

# 初始化缓存，用于保存已经存在的推文的 sortIndex
cached_sort_indexes = set()

# Twitter API接口URL
url_template = "https://x.com/i/api/graphql/Tg82Ez_kxVaJf7OPbUdbCg/UserTweets"

# 设置请求的特性
features = {
        "rweb_tipjar_consumption_enabled": True,
        "responsive_web_graphql_exclude_directive_enabled": True,
        "verified_phone_label_enabled": False,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "communities_web_enable_tweet_community_results_fetch": True,
        "c9s_tweet_anatomy_moderator_badge_enabled": True,
        "articles_preview_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
        "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "responsive_web_twitter_article_tweet_consumption_enabled": True,
        "tweet_awards_web_tipping_enabled": False,
        "creator_subscriptions_quote_tweet_preview_enabled": False,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
        "rweb_video_timestamps_enabled": True,
        "longform_notetweets_rich_text_read_enabled": True,
        "longform_notetweets_inline_media_enabled": True,
        "responsive_web_enhance_cards_enabled": False
    }


# 设置请求头
headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "Content-Type": "application/json",
    "Cookie": "guest_id=v1%3A171314297296205998; night_mode=2; guest_id_marketing=v1%3A171314297296205998; guest_id_ads=v1%3A171314297296205998; g_state={\"i_l\":0}; kdt=rHfG22zMvcz6XLpeI0oJcNBMeDXPdqPhZuIV4qQn; auth_token=260e206cc6c4ad36b98ef567e6acddbb1b0261e7; ct0=800888f3d9efdeac1a630befae2c9b3aa225e52040707d2ca9d5950e1ed6fd7f6fe8919911b51affbf4419eeae461c65488cb316d60881954b3113bf7ccd163dade9db6d232bae7593edb61ef5737fb1; lang=en; twid=u%3D1474431568638664704; personalization_id=\"v1_CrixkwcLDZTvHdZUFe18EA==\"; des_opt_in=Y; _ga=GA1.2.1473131978.1729061442; external_referer=padhuUp37zjSzNXpb3CVCQ%3D%3D|0|8e8t2xd8A2w%3D",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "X-Client-Transaction-ID": "/gSh+3uJ7ECczAOAoc6s2+UpWOiGWB6AXngKrqxnFIar4tzjC+/H8KyW5HzgnNngeEmJNPy6mu1W0bv33AJF4YF4vnEn/Q",
    "X-Client-UUID": "c29f39a6-0af1-459f-8f12-0c9222c7fa35",
    "X-CSRF-Token": "800888f3d9efdeac1a630befae2c9b3aa225e52040707d2ca9d5950e1ed6fd7f6fe8919911b51affbf4419eeae461c65488cb316d60881954b3113bf7ccd163dade9db6d232bae7593edb61ef5737fb1",
    "X-Twitter-Active-User": "yes",
    "X-Twitter-Auth-Type": "OAuth2Session",
    "X-Twitter-Client-Language": "en"
}


def fetch_data_with_retry(url, headers, max_retries=5, backoff_factor=1):
    for retry in range(max_retries):
        try:
            response = session.get(url, headers=headers, verify=False)
            if response.status_code == 429:  # Too Many Requests
                retry_after = int(response.headers.get('Retry-After', backoff_factor))
                time.sleep(retry_after)
            else:
                return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        time.sleep(backoff_factor * (2 ** retry))  # Exponential backoff
    raise Exception("Max retries exceeded")


# 抓取Twitter博主文章的函数
def fetch_latest_tweets(x_id, username):
    # 设置请求的变量
    variables = {
        "userId": f"{x_id}",
        "count": "40",
        "includePromotedContent": True,
        "withQuickPromoteEligibilityTweetFields": True,
        "withVoice": True,
        "withV2Timeline": True
    }

    # 将变量和特性编码为查询字符串
    query_string = (
        f"variables={urllib.parse.quote(json.dumps(variables))}"
        f"&features={urllib.parse.quote(json.dumps(features))}"
        f"&fieldToggles={{\"withArticlePlainText\":false}}"
    )
    url = url_template
    # 完整的请求URL
    request_url = f"{url}?{query_string}"

    try:
        response = fetch_data_with_retry(request_url, headers=headers)
        if response.status_code == 200:
            data = json.loads(response.content)
            return parse_tweets(data, x_id)
        else:
            print(response.content)
            logger.error(f"Failed to fetch tweets for {username}: {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching tweets: {e}")
    return []


def extract_tweet_data(content, blogger_id: str):
    """提取推文的详细信息"""
    if "items" in content:
        content = content["items"][0]["item"]
    tweet_data = content.get("itemContent", {}).get("tweet_results", {}).get("result", {}).get("legacy", {})

    if not tweet_data:
        return None
    media_urls = [media_item.get("media_url_https") for media_item in tweet_data.get("extended_entities", {}).get("media", [])]
    media_url = ','.join(filter(None, media_urls))  # 将所有非 None 的 media_url_https 连接为字符串

    symbols = [symbol["text"] for symbol in tweet_data.get("entities", {}).get("symbols", [])]
    tweet_id = tweet_data["id_str"]
    return BloggerTweet(
                id=tweet_id,
                content=tweet_data["full_text"],
                image_url=media_url,
                symbol=','.join(symbols),
                published_at=convert_to_timestamp(tweet_data["created_at"]),
                favorite_count=tweet_data["favorite_count"],
                reply_count=tweet_data["reply_count"],
                retweet_count=tweet_data["retweet_count"],
                bookmark_count=tweet_data["bookmark_count"],
            )


def parse_tweets(data, blogger_id):
    """解析推文数据"""
    tweets = []
    try:
        for entry in data["data"]["user"]["result"]["timeline_v2"]["timeline"]["instructions"]:
            if entry["type"] == "TimelineAddEntries":
                for item in entry["entries"]:
                    content = item.get("content")
                    if not content:
                        continue
                    # 提取推文内容
                    tweet_data = extract_tweet_data(content, blogger_id)
                    if tweet_data:
                        tweets.append(tweet_data)
    except Exception as e:
        logger.error(f"Error parsing tweets: {e}")
    return tweets


# 替换推文中的媒体URL为OSS链接
def replace_media_urls_with_oss(tweet):
    """替换推文中的媒体URL为OSS链接"""
    media_urls = tweet.image_url.split(',')  # 以逗号分割URL
    oss_urls = [upload_to_oss(url) for url in media_urls if url]
    tweet.image_url = ','.join(filter(None, oss_urls))  # 拼接新的OSS链接


# 存入数据库的函数
def save_posts_to_db(db_sess, tweets, blogger_id, refresh_mode=False):
    for tweet in tweets:
        # 如果 tweet.id 已经在缓存中，跳过处理
        if tweet.id in cached_sort_indexes:
            continue
        try:
            # 查询是否已存在相同ID的推文
            existing_tweet = db_sess.query(BloggerTweet).filter_by(id=tweet.id).first()
            # 替换推文中的媒体 URL
            replace_media_urls_with_oss(tweet)
            # 如果推文存在且处于刷新模式，更新推文信息
            if existing_tweet and refresh_mode:
                existing_tweet.content = tweet.content
                existing_tweet.image_url = tweet.image_url
                existing_tweet.published_at = tweet.published_at
                existing_tweet.reply_count = tweet.reply_count
                existing_tweet.favorite_count = tweet.favorite_count
                existing_tweet.retweet_count = tweet.retweet_count
                existing_tweet.bookmark_count = tweet.bookmark_count
                existing_tweet.url = tweet.url
                db_sess.merge(existing_tweet)     
            # 如果推文不存在，直接添加为新记录
            elif not existing_tweet:
                tweet.blogger_id = blogger_id
                tweet.image_url = tweet.image_url
                db_sess.add(tweet)
            # 提交事务并缓存推文ID
            db_sess.commit()
            cached_sort_indexes.add(tweet.id)     
        except Exception as e:
            # 记录异常并继续处理下一个推文
            logger.error(f"Failed to process tweet ID {tweet.id}: {e}")
            db_sess.rollback()  # 回滚事务以保持会话的稳定性


def convert_to_timestamp(created_at):
    # 如果 created_at 是字符串，则进行解析
    if isinstance(created_at, str):
        dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
    else:
        dt = created_at  # 如果已经是 datetime 对象，直接返回
    
    # 返回数据库友好的 datetime 对象（去掉时区信息）
    return dt.astimezone(tz=None).replace(tzinfo=None, microsecond=0)


if __name__ == "__main__":
    # 必须要通过app上下文去启动数据库
    database.global_init()

    while True:
        with database.create_database_session() as db_sess:
            bloggers = db_sess.query(Blogger).all()  # 假设你有一个 Blogger 表
            for blogger in bloggers:
                username = blogger.username  # 获取博主的用户名
                print(f'Fetching posts for: {username}, {blogger.x_id}')
                tweets = fetch_latest_tweets(blogger.x_id, username)
                if tweets:
                    save_posts_to_db(db_sess, tweets, blogger.id, True)
            db_sess.close()
            print('同步结束')
            time.sleep(300)  # 每1分钟执行一次
