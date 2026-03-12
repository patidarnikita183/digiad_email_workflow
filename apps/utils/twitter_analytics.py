#twitter_analytics.py
import os
import json
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1
from utils.general_constants import logger

load_dotenv()


def get_twitter_ad_stats(
    account_id,
    campaign_twitter_platform_campaign_id,
    oauth_token,
    oauth_token_secret,
    twitter_consumer_key, 
    twitter_consumer_secret,
    metric_groups,
    start_date,
):
    """
    Fetch Twitter Ads stats for a campaign in 7-day windows.
    If the range is >7 days, it splits into multiple 7-day windows and aggregates results.
    """

    fmt = "%Y-%m-%d"
    start_dt = datetime.strptime(start_date, fmt).date()
    end_dt = (datetime.today() + timedelta(days=1)).date()

    # Helper to call Twitter API for one window
    def fetch_window(s_dt, e_dt):
        url = (
            f"https://ads-api.x.com/12/stats/accounts/{account_id}"
            f"?entity=CAMPAIGN"
            f"&entity_ids={campaign_twitter_platform_campaign_id}"
            f"&start_time={s_dt.strftime(fmt)}"
            f"&end_time={e_dt.strftime(fmt)}"
            f"&granularity=TOTAL"
            f"&placement=ALL_ON_TWITTER"
            f"&metric_groups={metric_groups}"
        )

        auth = OAuth1(
            # os.getenv("TWITTER_CONSUMER_KEY"),
            # os.getenv("TWITTER_CONSUMER_SECRET"),
            twitter_consumer_key, 
            twitter_consumer_secret,
            oauth_token,
            oauth_token_secret,
            signature_type="auth_header",
        )

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        response = requests.get(url, headers=headers, auth=auth)
        response.raise_for_status()
        data = response.json()

        stat_data = data.get("data", [])[0]["id_data"][0]["metrics"]

        # Normalize metrics (sum list values)
        metrics = {}
        for k, v in stat_data.items():
            if isinstance(v, dict) and 'order_quantity' in v:
                # print("k=============",k)
                # print("v=============",v)
                metrics[k] = v['order_quantity']
            elif isinstance(v, list):
                metrics[k] = sum(val for val in v if val is not None)
            else:
                metrics[k] = v
        return metrics
            

    # Iterate over 7-day windows
    aggregated_metrics = {}
    current_start = start_dt
    while current_start < end_dt:
        current_end = min(current_start + timedelta(days=7), end_dt)
        # print(current_start,current_end)
        window_metrics = fetch_window(current_start, current_end)
        # print("===========================")
        # print(window_metrics)
        # print("============================")
        # Aggregate metrics across windows
        for k, v in window_metrics.items():
            if isinstance(v, (int, float)):
                aggregated_metrics[k] = aggregated_metrics.get(k, 0) + v

            else:
                if v == None:
                    v= 0
                    aggregated_metrics[k] = aggregated_metrics.get(k, 0) + v  # fallback
                # print("else -----")
                
        current_start = current_end
    return aggregated_metrics


def get_twitter_data(twitter_credentials):
    # account_id = twitter_credentials["account_id"]
    # campaign_twitter_platform_campaign_id = twitter_credentials[
    #     "campaign_twitter_platform_campaign_id"
    # ]
    # oauth_token = twitter_credentials["oauth_token"]
    # oauth_token_secret = twitter_credentials["oauth_token_secret"]
    # twitter_consumer_key = twitter_credentials["twitter_consumer_key"]
    # twitter_consumer_secret = twitter_credentials["twitter_consumer_secret"]

    account_id = twitter_credentials.get("account_id")
    campaign_twitter_platform_campaign_id = twitter_credentials.get("campaign_twitter_platform_campaign_id")
    oauth_token = twitter_credentials.get("oauth_token")
    oauth_token_secret = twitter_credentials.get("oauth_token_secret")
    twitter_consumer_key = twitter_credentials.get("twitter_consumer_key")
    twitter_consumer_secret = twitter_credentials.get("twitter_consumer_secret")
    start_date = twitter_credentials.get("start_date")


    stats = get_twitter_ad_stats(
        account_id=account_id,
        campaign_twitter_platform_campaign_id=campaign_twitter_platform_campaign_id,
        oauth_token=oauth_token,
        oauth_token_secret=oauth_token_secret,
        twitter_consumer_key=twitter_consumer_key,
        twitter_consumer_secret=twitter_consumer_secret,
        metric_groups="ENGAGEMENT,BILLING",
        start_date=start_date
    )
    res = {}
    res["twitter_conversions"] = 0
    if stats["clicks"]:
        # print("Inside If")
        conversion_stats = get_twitter_ad_stats(
            account_id=account_id,
            campaign_twitter_platform_campaign_id=campaign_twitter_platform_campaign_id,
            oauth_token=oauth_token,
            oauth_token_secret=oauth_token_secret,
            twitter_consumer_key=twitter_consumer_key,
            twitter_consumer_secret=twitter_consumer_secret,
            metric_groups="WEB_CONVERSION,MOBILE_CONVERSION",
            start_date=start_date
        )
        res["twitter_conversions"] = sum(conversion_stats.values())

    logger.info("Fetching Twitter Data...(may take time longer than usual)")


    res["twitter_impr"] = stats["impressions"]
    res["twitter_clicks"] = stats["clicks"]
    res["twitter_cost"] = round(stats["billed_charge_local_micro"] / 1_000_000,2)
    res["twitter_ctr"] = round((
        (stats["clicks"] / stats["impressions"]) * 100 if stats["clicks"] else 0
    ),2)
    res["twitter_cpc"] = round((res["twitter_cost"] / stats["clicks"]),2) if stats["clicks"] else 0
    

    return res


def twitter_data_preparation(data):
    data = data.get("data")
    clicks, impressions, ctr, conversions, cost_per_click, cost = 0, 0, 0, 0, 0, 0
    if data:
        clicks = int(data.get("clicks"), 0)
        impressions = int(data.get("impressions"), 0)
        ctr = float(data.get("ctr"), 0)
        conversions = int(data.get("result_value"), 0)
        cost_per_click = float(data.get("cpc"), 0)
        cost = float(data.get("spend"), 0)
    data = {
        "twitter_clicks": clicks,
        "twitter_impr": impressions,
        "twitter_ctr": ctr,
        "twitter_conversions": conversions,
        "twitter_cpc": cost_per_click,
        "twitter_cost": cost,
    }
    return data

############################ AUDIENCE ANALYTICS #################################
from utils.twitter_audience_analytics import get_twitter_insights

def get_twitter_audience_data(twitter_credentials):
    account_id = twitter_credentials.get("account_id")
    campaign_id = twitter_credentials.get("campaign_twitter_platform_campaign_id")
    oauth_token = twitter_credentials.get("oauth_token")
    oauth_token_secret = twitter_credentials.get("oauth_token_secret")
    twitter_consumer_key = twitter_credentials.get("twitter_consumer_key")
    twitter_consumer_secret = twitter_credentials.get("twitter_consumer_secret")

    if campaign_id is None or account_id is None or oauth_token is None or oauth_token_secret is None or twitter_consumer_key is None or twitter_consumer_secret is None:
        logger.error("Missing required Twitter credentials. Required fields: 'campaign_twitter_platform_campaign_id', 'accound_id', 'oauth_token', 'oauth_token_secret', 'twitter_consumer_key', 'twitter_consumer_secret'")

        return {"error": "Missing 'campaign_twitter_platform_campaign_id' or 'accound_id' or 'oauth_token' or 'oauth_token_secret' or 'twitter_consumer_key' or 'twitter_consumer_secret' in credentials."}

    start_time = twitter_credentials.get("start_date", datetime.utcnow().strftime("%Y-%m-%d"))
    end_time = twitter_credentials.get("end_time", datetime.utcnow().strftime("%Y-%m-%d"))

    # Convert YYYY-MM-DD to ISO format
    if len(start_time) == 10:
        start_time = datetime.strptime(start_time, "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00Z")
    if len(end_time) == 10:
        # FIXED: Use 23:00:00 (no fractional hours) to include the full end day
        end_time = datetime.strptime(end_time, "%Y-%m-%d").strftime("%Y-%m-%dT23:00:00Z")
    logger.info("Fetching Twitter Data...(may take time longer than usual)")

    result = get_twitter_insights(account_id, campaign_id, oauth_token, oauth_token_secret, start_time, end_time, twitter_consumer_key, twitter_consumer_secret)
    result = json.loads(json.dumps(result).replace("null", "0"))
    return result
