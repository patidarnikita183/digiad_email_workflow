import requests
from utils.general_constants import logger

def get_snapchat_conversion_data(access_token, platform_campaign_id):
    base_url = f"https://adsapi.snapchat.com/v1/campaigns/{platform_campaign_id}/stats"
    fields = (
        "total_installs,conversion_purchases,conversion_save,conversion_start_checkout,"
        "conversion_add_cart,conversion_view_content,conversion_add_billing,conversion_sign_ups,"
        "conversion_searches,conversion_level_completes,conversion_app_opens,conversion_page_views,"
        "conversion_subscribe,conversion_ad_click,conversion_ad_view,conversion_complete_tutorial,"
        "conversion_invite,conversion_login,conversion_share,conversion_reserve,"
        "conversion_achievement_unlocked,conversion_add_to_wishlist,conversion_spend_credits,"
        "conversion_rate,conversion_start_trial,conversion_list_view,conversion_visit"
    )
    params = {
        "granularity": "TOTAL",
        "fields": fields,
        "conversion_source_types": "total,web,app",
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(base_url, headers=headers, params=params)

    if response.status_code == 200:
        # print(response.text)
        return response.json()
    else:
        # print(response.text)
        return None


def update_snapchat_campaign_hourly_analytics(access_token, platform_campaign_id):
    try:
        base_url = f"https://adsapi.snapchat.com/v1/campaigns/{platform_campaign_id}/stats"
        fields = "impressions,spend,landing_page_views"

        params = {
            "granularity": "TOTAL",
            "fields": fields,
            "conversion_source_types": "total,web,app",
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        logger.info(f"Error fetching Snapchat analytics: {str(e)}")
        return None


def format_snapchat_data(snapchat_data, conversion_object):
    cost = snapchat_data.get("spend", 0) / 1_000_000
    conversions = sum(conversion_object.values())
    landing_page_views = snapchat_data.get("landing_page_views", 0)
    impressions = snapchat_data.get("impressions", 0)
    conversion_rate = (
        (conversions / landing_page_views) * 100 if landing_page_views else 0
    )

    return {
        "snapchat_impr": impressions,
        "snapchat_conversions": conversions,
        "snapchat_cost": cost,
        "snapchat_clicks": landing_page_views,
        "snapchat_ctr": (landing_page_views / impressions) * 100 if impressions else 0,
        "snapchat_cpc": (cost / landing_page_views) if landing_page_views else 0,
    }


def snapchat_data_preparation(data):
    data = data.get("data")
    clicks, impressions, ctr, conversions, cost_per_click, cost = 0, 0, 0, 0, 0, 0
    if data:
        clicks = int(data.get("snapchat_clicks"), 0)
        impressions = int(data.get("snapchat_impr"), 0)
        ctr = float(data.get("snapchat_ctr"), 0)
        conversions = int(data.get("snapchat_conversions"), 0)
        cost_per_click = float(data.get("snapchat_cpc"), 0)
        cost = float(data.get("snapchat_cost"), 0)
    data = {
        "snapchat_clicks": clicks,
        "snapchat_impr": impressions,
        "snapchat_ctr": ctr,
        "snapchat_conversions": conversions,
        "snapchat_cpc": cost_per_click,
        "snapchat_cost": cost,
    }
    return data

############################ AUDIENCE ANALYTICS #################################

def prepare_snapchat_conversion_audience_data(analytics, dimensions):
    """
    Prepares conversion audience data by summing conversion values,
    grouped by one or more dimension keys.

    :param analytics: List of dicts with conversion breakdown.
    :param dimensions: Either a string (single key) or list/tuple of keys (multiple dimensions).
    """
    if isinstance(dimensions, str):
        dimensions = [dimensions]  # normalize to list

    conversion_data = []
    for conversion_object in analytics:
        res = {}

        # extract dimension values
        for dim in dimensions:
            res[dim] = conversion_object[dim]
            conversion_object = {k: v for k, v in conversion_object.items() if k != dim}

        # sum remaining values = conversions
        conversions = sum(conversion_object.values())
        res['conversions'] = conversions

        conversion_data.append(res)

    return conversion_data

def combine_snapchat_audience_data(analytics, conversion_analytics, dimensions):
    """
    Merge Snapchat analytics and conversion_analytics by one or more dimension keys.
    Also calculate cost, CPC, and CTR.

    :param analytics: List of dicts with impressions/spend/swipes etc.
    :param conversion_analytics: List of dicts with conversion info.
    :param dimensions: Either a string (single key) or list/tuple of keys (multiple dimensions).
    """
    if isinstance(dimensions, str):
        dimensions = [dimensions]  # normalize to list

    def get_key(d):
        return tuple(d.get(dim) for dim in dimensions)

    map1 = {get_key(d): d for d in analytics}
    map2 = {get_key(d): d for d in conversion_analytics}

    combined = []
    for key, d1 in map1.items():
        merged = d1.copy()
        if key in map2:
            merged.update(map2[key])

        # ensure conversions default to 0 if impressions exist
        if "impressions" in merged and "conversions" not in merged:
            merged["conversions"] = 0

        # calculate metrics
        spend = merged.get("spend", 0)
        impressions = merged.get("impressions", 0)
        swipes = merged.get("swipes", 0)

        merged["cost"] = round((spend / 1000000),2) if spend else 0
        merged["cpc"] = round((merged["cost"] / swipes),2) if swipes > 0 else 0
        merged["ctr"] = round((swipes / impressions)*100,2) if impressions > 0 else 0

        combined.append(merged)

    return combined

def get_snapchat_audience_analytics_data(access_token,platform_campaign_id,dimension):
    base_url = f"https://adsapi.snapchat.com/v1/campaigns/{platform_campaign_id}/stats"
    fields = "impressions,spend,swipes,swipes"
    
    params = {
        "granularity": "TOTAL",
        "fields": fields,
        "conversion_source_types": "total,web,app",
        "report_dimension" : dimension
    }
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(base_url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()['total_stats'][0]['total_stat']['dimension_stats']
    else:
        logger.info(f"Snapchat response received in the api : {response.text}")
        return []

def get_snapchat_audience_conversion_data(access_token,platform_campaign_id,dimension):
    base_url = f"https://adsapi.snapchat.com/v1/campaigns/{platform_campaign_id}/stats"
    fields = (
    "total_installs,conversion_purchases,conversion_save,conversion_start_checkout,"
    "conversion_add_cart,conversion_view_content,conversion_add_billing,conversion_sign_ups,"
    "conversion_searches,conversion_level_completes,conversion_app_opens,conversion_page_views,"
    "conversion_subscribe,conversion_ad_click,conversion_ad_view,conversion_complete_tutorial,"
    "conversion_invite,conversion_login,conversion_share,conversion_reserve,"
    "conversion_achievement_unlocked,conversion_add_to_wishlist,conversion_spend_credits,"
    "conversion_rate,conversion_start_trial,conversion_list_view,conversion_visit"
    )
    params = {
        "granularity": "TOTAL",
        "fields": fields,
        "conversion_source_types": "total,web,app",
        "report_dimension" : dimension
    }
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(base_url, headers=headers, params=params)
    
    if response.status_code == 200:
        # print(response.text)
        return response.json()['total_stats'][0]['total_stat']['dimension_stats']
    else:
        # print(response.text)
        return []


def get_snapchat_audience_wise_campaign_data(access_token,platform_campaign_id):
    logger.info("Fetching Snapchat audience-wise campaign data...")
    res = {}
    country_analytics = get_snapchat_audience_analytics_data(access_token, platform_campaign_id,"country")
    gender_analytics = get_snapchat_audience_analytics_data(access_token, platform_campaign_id,"gender")
    age_analytics = get_snapchat_audience_analytics_data(access_token, platform_campaign_id,"age")
    os_analytics = get_snapchat_audience_analytics_data(access_token, platform_campaign_id,"os")
    lifestyle_category_analytics = get_snapchat_audience_analytics_data(access_token, platform_campaign_id,"lifestyle_category")
    age_gender_analytics = get_snapchat_audience_analytics_data(access_token, platform_campaign_id,"age,gender")
    # print(lifestyle_category_analytics)
    # print("--------------------------")
    country_conversion_analytics = get_snapchat_audience_conversion_data(access_token, platform_campaign_id,"country")
    gender_conversion_analytics = get_snapchat_audience_conversion_data(access_token, platform_campaign_id,"gender")
    age_conversion_analytics = get_snapchat_audience_conversion_data(access_token, platform_campaign_id,"age")
    os_conversion_analytics = get_snapchat_audience_conversion_data(access_token, platform_campaign_id,"os")
    lifestyle_category_conversion_analytics = get_snapchat_audience_conversion_data(access_token, platform_campaign_id,"lifestyle_category")
    age_gender_conversion_analytics = get_snapchat_audience_conversion_data(access_token, platform_campaign_id,"age,gender")
    # print(lifestyle_category_conversion_analytics)
    # print("--------------------------")
    country_conversion_analytics = prepare_snapchat_conversion_audience_data(country_conversion_analytics,"country")
    gender_conversion_analytics = prepare_snapchat_conversion_audience_data(gender_conversion_analytics,"gender")
    age_conversion_analytics = prepare_snapchat_conversion_audience_data(age_conversion_analytics,"age_bucket")
    os_conversion_analytics = prepare_snapchat_conversion_audience_data(os_conversion_analytics,"operating_system")
    lifestyle_category_conversion_analytics = prepare_snapchat_conversion_audience_data(lifestyle_category_conversion_analytics,"interest_category_id")
    age_gender_conversion_analytics = prepare_snapchat_conversion_audience_data(age_gender_conversion_analytics,["age_bucket","gender"])
    # print(lifestyle_category_conversion_analytics)
    # print("--------------------------")
    country_data = combine_snapchat_audience_data(country_analytics, country_conversion_analytics, "country")
    gender_data = combine_snapchat_audience_data(gender_analytics, gender_conversion_analytics, "gender")
    age_data = combine_snapchat_audience_data(age_analytics, age_conversion_analytics, "age_bucket")
    os_data = combine_snapchat_audience_data(os_analytics, os_conversion_analytics, "operating_system")
    lifestyle_category_data = combine_snapchat_audience_data(lifestyle_category_analytics, lifestyle_category_conversion_analytics, "interest_category_id")
    age_gender_data = combine_snapchat_audience_data(age_gender_analytics, age_gender_conversion_analytics, ["age_bucket","gender"])
    # print(lifestyle_category_data)
    # print("--------------------------")
    logger.info("Snapchat audience-wise campaign data retreival completed.")
    res['country_analytics'] = country_data
    res['gender_analytics'] = gender_data
    res['age_analytics'] = age_data
    res['os_analytics'] = os_data
    res['lifestyle_category_analytics'] = lifestyle_category_data
    res['age_gender_analytics'] = age_gender_data

    return res
