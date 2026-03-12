from utils.google_analytics import get_google_data,google_data_preparation,youtube_data_preparation,get_google_audience_data
from utils.meta_analytics import get_facebook_data,facebook_data_preparation,get_meta_campaign_audience_metrics
from utils.snapchat_analytics import snapchat_data_preparation
from utils.tiktok_analytics import tiktok_data_preparation
from utils.twitter_analytics import twitter_data_preparation,get_twitter_audience_data
from utils.general_constants import BASE_URL_EMAIL,logger
from typing import Optional,Union
import os
import requests
from typing import Dict, List, Any, Optional
# from google.ads.googleads.client import GoogleAdsClient
# from google.ads.googleads.errors import GoogleAdsException



def validate_path(path: Union[str, os.PathLike, int]) -> Optional[str]:
    """
    Checks if the given path exists.

    Args:
        path: The path to validate.

    Returns:
        Optional[str]: The path if it exists, otherwise None.
    """
    if isinstance(path, (str, bytes, os.PathLike, int)):
        return [path] if os.path.exists(path) else None
    return None

def remove_files_if_exists(file_path):
    """Removes the file at the specified path if it exists."""
    for file_path in file_path:
        if os.path.exists(file_path):
            os.remove(file_path)

####### Data preparation for email ##########
def prepare_data_for_mail(customer_name, campaign_name, current_date, platforms_data):

    google_imp = platforms_data["google"]["google_impr"]
    google_click = platforms_data["google"]["google_clicks"]
    google_ctr = platforms_data["google"]["google_ctr"]
    google_conversions = platforms_data["google"]["google_conversions"]
    google_cpc = platforms_data["google"]["google_cpc"]
    google_cost = platforms_data["google"]["google_cost"]

    facebook_imp = platforms_data["facebook"]["impressions"]
    facebook_click = platforms_data["facebook"]["clicks"]
    facebook_ctr = platforms_data["facebook"]["ctr"]
    facebook_conversions = platforms_data["facebook"]["conversions"]
    facebook_cpc = platforms_data["facebook"]["cost_per_click"]
    facebook_cost = platforms_data["facebook"]["cost"]

    snapchat_imp = platforms_data["snapchat"]["snapchat_impr"]
    snapchat_click = platforms_data["snapchat"]["snapchat_clicks"]
    snapchat_ctr = platforms_data["snapchat"]["snapchat_ctr"]
    snapchat_conversions = platforms_data["snapchat"]["snapchat_conversions"]
    snapchat_cpc = platforms_data["snapchat"]["snapchat_cpc"]
    snapchat_cost = platforms_data["snapchat"]["snapchat_cost"]

    twitter_imp = platforms_data["twitter"]["twitter_impr"]
    twitter_click = platforms_data["twitter"]["twitter_clicks"]
    twitter_ctr = platforms_data["twitter"]["twitter_ctr"]
    twitter_conversions = platforms_data["twitter"]["twitter_conversions"]
    twitter_cpc = platforms_data["twitter"]["twitter_cpc"]
    twitter_cost = platforms_data["twitter"]["twitter_cost"]

    tiktok_imp = platforms_data["tiktok"]["tiktok_impr"]
    tiktok_click = platforms_data["tiktok"]["tiktok_clicks"]
    tiktok_ctr = platforms_data["tiktok"]["tiktok_ctr"]
    tiktok_conversions = platforms_data["tiktok"]["tiktok_conversions"]
    tiktok_cpc = platforms_data["tiktok"]["tiktok_cpc"]
    tiktok_cost = platforms_data["tiktok"]["tiktok_cost"]

    youtube_imp = platforms_data["youtube"]["youtube_impr"]
    youtube_click = platforms_data["youtube"]["youtube_clicks"]
    youtube_ctr = platforms_data["youtube"]["youtube_ctr"]
    youtube_conversions = platforms_data["youtube"]["youtube_conversions"]
    youtube_cpc = platforms_data["youtube"]["youtube_cpc"]
    youtube_cost = platforms_data["youtube"]["youtube_cost"]

    instagram_imp = platforms_data["instagram"]["impressions"]
    instagram_click = platforms_data["instagram"]["clicks"]
    instagram_ctr = platforms_data["instagram"]["ctr"]
    instagram_conversions = platforms_data["instagram"]["conversions"]
    instagram_cpc = platforms_data["instagram"]["cost_per_click"]
    instagram_cost = platforms_data["instagram"]["cost"]

    agg_impr = (
        google_imp
        + facebook_imp
        + snapchat_imp
        + twitter_imp
        + tiktok_imp
        + youtube_imp
        + instagram_imp
    )

    agg_clicks = (
        google_click
        + facebook_click
        + snapchat_click
        + twitter_click
        + tiktok_click
        + youtube_click
        + instagram_click
    )

    agg_ctr = (
        google_ctr
        + facebook_ctr
        + snapchat_ctr
        + twitter_ctr
        + tiktok_ctr
        + youtube_ctr
        + instagram_ctr
    )

    agg_leads = (
        google_conversions
        + facebook_conversions
        + snapchat_conversions
        + twitter_conversions
        + tiktok_conversions
        + youtube_conversions
        + instagram_conversions
    )

    agg_cpc = (
        google_cpc
        + facebook_cpc
        + snapchat_cpc
        + twitter_cpc
        + tiktok_cpc
        + youtube_cpc
        + instagram_cpc
    )

    agg_cost = (
        google_cost
        + facebook_cost
        + snapchat_cost
        + twitter_cost
        + tiktok_cost
        + youtube_cost
        + instagram_cost
    )

    data = {
        "name": customer_name,
        "logo_url": "https://digiad.ai/_next/image?url=%2Fimages%2FDIGIADai.png&w=256&q=75",
        "campaign_name": campaign_name,
        "report_datetime": current_date,
        # Aggregate KPIs
        "agg_impressions": agg_impr,
        "agg_clicks": agg_clicks,
        "agg_ctr": round(agg_ctr, 2),
        "agg_leads": agg_leads,
        "agg_cpc": round(agg_cpc, 2),
        "agg_cost": round(agg_cost),
        # Facebook
        "fb_impr": facebook_imp,
        "fb_clicks": facebook_click,
        "fb_ctr": round(facebook_ctr, 2),
        "fb_leads": facebook_conversions,
        "fb_cpc": round(facebook_cpc, 2),
        "fb_cost": round(facebook_cost, 2),
        # Google
        "google_impr": google_imp,
        "google_clicks": google_click,
        "google_ctr": round(google_ctr, 2),
        "google_leads": google_conversions,
        "google_cpc": round(google_cpc, 2),
        "google_cost": round(google_cost),
        # Snapchat
        "snapchat_impr": snapchat_imp,
        "snapchat_clicks": snapchat_click,
        "snapchat_ctr": round(snapchat_ctr, 2),
        "snapchat_leads": snapchat_conversions,
        "snapchat_cpc": round(snapchat_cpc, 2),
        "snapchat_cost": round(snapchat_cost),
        # Twitter
        "twitter_impr": twitter_imp,
        "twitter_clicks": twitter_click,
        "twitter_ctr": round(twitter_ctr, 2),
        "twitter_leads": twitter_conversions,
        "twitter_cpc": round(twitter_cpc, 2),
        "twitter_cost": round(twitter_cost),
        # Tiktok
        "tiktok_impr": tiktok_imp,
        "tiktok_clicks": tiktok_click,
        "tiktok_ctr": round(tiktok_ctr, 2),
        "tiktok_leads": tiktok_conversions,
        "tiktok_cpc": round(tiktok_cpc, 2),
        "tiktok_cost": round(tiktok_cost),
        # Youtube
        "youtube_impr": youtube_imp,
        "youtube_clicks": youtube_click,
        "youtube_ctr": round(youtube_ctr, 2),
        "youtube_leads": youtube_conversions,
        "youtube_cpc": round(youtube_cpc, 2),
        "youtube_cost": round(youtube_cost),
        # Instagram
        "instagram_impr": instagram_imp,
        "instagram_clicks": instagram_click,
        "instagram_ctr": round(instagram_ctr, 2),
        "instagram_leads": instagram_conversions,
        "instagram_cpc": round(instagram_cpc, 2),
        "instagram_cost": round(instagram_cost),
        # Links
        "deep_link_report": "https://your-digiad-platform.com/report/123",
        "support_link": "https://digiad.ai/contact",
        "campaign_url": "https://digiad.ai/",
    }
    # print(data)
    return data


def get_platform_campaign_performance_metrics(google_credentials,facebook_credentials,snapchat_credentials,twitter_credentials,tiktok_credentials,youtube_credentials,instagram_credentials):
    ## valid list of platforms on which campaign-published
    valid_platforms = []

    if google_credentials:
        valid_platforms.append("google")
        google_data = get_google_data(google_credentials,'google')

    else:
        google_data = google_data_preparation({})

    if facebook_credentials:
        valid_platforms.append("facebook")
        facebook_data = get_facebook_data(facebook_credentials)
    else:
        facebook_data = facebook_data_preparation({})

    if snapchat_credentials:
        valid_platforms.append("snapchat")
        snapchat_url = (
            BASE_URL_EMAIL + "/get_snapchat_campaign_data"
        )  # replace with your server URL
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            snapchat_url, json=snapchat_credentials, headers=headers
        )
        # print(f"Snapchat Response  : {response.json()}")
        snapchat_data = response.json()#["response"]
        if "response" in snapchat_data:
            snapchat_data = snapchat_data["response"]
        else:
            snapchat_data = snapchat_data_preparation({})

    else:
        snapchat_data = snapchat_data_preparation({})

    if twitter_credentials:
        valid_platforms.append("twitter")
        twitter_url = (
            BASE_URL_EMAIL + "/get_twitter_campaign_data"
        )  # replace with your server URL
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            twitter_url,
            json=twitter_credentials,
            headers=headers,
        )
        response_data = response.json()
        if "response" in response_data:
            twitter_data = response.json()["response"]
        else:
            twitter_data = twitter_data_preparation({})

    else:
        twitter_data = twitter_data_preparation({})

    if tiktok_credentials:
        valid_platforms.append("tiktok")
        tiktok_url = (
            BASE_URL_EMAIL + "/get_tiktok_campaign_data"
        )  # replace with your server URL
        headers = {"Content-Type": "application/json"}
        response = requests.post(tiktok_url, json=tiktok_credentials, headers=headers)
        response_data = response.json()
        if "response" in response_data:
            tiktok_data = response_data["response"]
        else:
            tiktok_data = tiktok_data_preparation({})
    else:
        tiktok_data = tiktok_data_preparation({})

    if youtube_credentials:
        valid_platforms.append("youtube")
        youtube_data = get_google_data(youtube_credentials,'youtube')
    else:
        youtube_data = youtube_data_preparation({})

    if instagram_credentials:
        valid_platforms.append("instagram")
        instagram_data = get_facebook_data(
            instagram_credentials
        )  # this function is same for instagram
    else:
        instagram_data = facebook_data_preparation({})

    
    platforms_data = {
        "google": google_data,
        "facebook": facebook_data,
        "snapchat": snapchat_data,
        "twitter": twitter_data,
        "tiktok": tiktok_data,
        "youtube": youtube_data,
        "instagram": instagram_data,
    }

    return platforms_data,valid_platforms


def get_platform_campaign_audience_metrics(google_credentials,facebook_credentials,snapchat_credentials,twitter_credentials,tiktok_credentials,youtube_credentials,instagram_credentials):
    
    if google_credentials:
        # print(f"calling the api of google\n\ngoogle_credentials:  {google_credentials}\n\n")
        # google_url = (
        #     BASE_URL_EMAIL + "/get_google_deep_insight"
        # )  # replace with your server URL
        # headers = {"Content-Type": "application/json"}
        # response = requests.post(
        #     google_url, json=google_credentials, headers=headers
        # )
        google_data = get_google_audience_data(google_credentials) #response.json()
        # print("done google data",google_data.keys())
        logger.info("done google data")

    else:
        google_data = None

    if facebook_credentials:
     
        facebook_data = get_meta_campaign_audience_metrics(facebook_credentials)
        # print(f"===============response.keys",facebook_data.keys())
        # print(f"===============facebook_data:  {facebook_data}========")
        logger.info("done fb data")
    else:
        facebook_data = None

    if snapchat_credentials:
        snapchat_url = (
            BASE_URL_EMAIL + "/get_snapchat_audience_campaign_data"
        )  # replace with your server URL
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            snapchat_url, json=snapchat_credentials, headers=headers
        )
        snapchat_data = response.json()
        logger.info("done snapchat data")

    else:
        snapchat_data = None

    if twitter_credentials:
        # twitter_url = (
        #     BASE_URL_EMAIL + "/get_twitter_audience_campaign_data"
        # )  # replace with your server URL
        # headers = {"Content-Type": "application/json"}
        # response = requests.post(
        #     twitter_url,
        #     json={"twitter_credentials": twitter_credentials},
        #     headers=headers,
        # )
        twitter_data = get_twitter_audience_data(twitter_credentials)
        logger.info("done twitter data")
    else:
        twitter_data = None

    if tiktok_credentials:
        tiktok_url = (
            BASE_URL_EMAIL + "/get_tiktok_audience_campaign_data"
        )  # replace with your server URL
        headers = {"Content-Type": "application/json"}
        response = requests.post(tiktok_url, json=tiktok_credentials, headers=headers)
        tiktok_data = response.json()
        logger.info("done tiktok data")
    else:
        tiktok_data = None

    if youtube_credentials:
        # youtube_url = (
        #     BASE_URL_EMAIL + "/get_google_deep_insight"
        # )  # replace with your server URL
        # headers = {"Content-Type": "application/json"}
        # response = requests.post(
        #     youtube_url, json=youtube_credentials, headers=headers
        # )
        youtube_data = get_google_audience_data(youtube_credentials)
        logger.info("done youtube data")
    else:
        youtube_data = None

    if instagram_credentials:
        instagram_data = get_meta_campaign_audience_metrics(instagram_credentials)
        logger.info("done instagram data")
    else:
        instagram_data = None

    
    audience_platforms_data = {
        "google": google_data,
        "facebook": facebook_data,
        "snapchat": snapchat_data,
        "twitter": twitter_data,
        "tiktok": tiktok_data,
        "youtube": youtube_data,
        "instagram": instagram_data,
    }
    # print("=========================")
    # print(audience_platforms_data)
    # print("===========================")

    return audience_platforms_data




def filter_platform_data(data: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """
    Filter platform advertising data based on required columns and categorical columns.
    
    Args:
        data: The complete data dictionary containing all platform data
        platform: Platform name ('facebook', 'snapchat', 'tiktok', 'twitter', 'google')
        required_columns: List of required column names to keep (optional, uses defaults if None)
        categorical_cols: List of categorical column names to process (optional, uses defaults if None)
    
    Returns:
        Dictionary containing filtered data for the specified platform
    """

    platform_configs = {
        'facebook': {
            'required_columns': ["impressions", "clicks", "ctr", "spend", "reach", "cpc", "result_value","date_start","date_stop"],
            'categorical_cols': ['age', 'device', 'device_platform', 'platform_position', 'region', 'gender'],
            "segments_to_remove":["hourly_data","age_and_gender"],
            'data_key': 'facebook'
        },
        'instagram': {
            'required_columns': ["impressions", "clicks", "ctr", "spend", "reach", "cpc", "result_value","date_start","date_stop"],
            'categorical_cols': ['age', 'device', 'device_platform', 'platform_position', 'region', 'gender'],
            "segments_to_remove":["hourly_data","age_and_gender"],
            'data_key': 'instagram'
        },
        'snapchat': {
            'required_columns': ["impressions", "clicks", "ctr", "cost", "cpc", "swipes", "conversions"],
            'categorical_cols': ["age_bucket", "gender", "country", "interest_category_name", "operating_system"],
            "segments_to_remove":["age_gender_analytics"],
            'data_key': 'snapchat'
        },
        'tiktok': {
            'required_columns': ['impressions', 'clicks', 'ctr', 'spend', 'reach', 'cpc', 'conversion','cost_per_conversion','cpm','result'],
            'categorical_cols': ["age", "country_code", "gender", "interest", "language", "platform"],
            "segments_to_remove":["hour","age_and_gender"],
            'data_key': 'tiktok'
        },
        'twitter': {
            'required_columns': ["impressions", "clicks", "ctr", "cost", "cpc", "conversions"],
            'categorical_cols': ["AGE", "GENDER", "INTERESTS", "LANGUAGES", "LOCATIONS", "PLATFORMS"],
            "segments_to_remove":[],
            'data_key': 'twitter'
        },
        'google': {
            'required_columns': ["impressions", "clicks", "ctr", "cost", "cpc", "conversions","cost_per_conversion"],
            'categorical_cols': ["age_range", "device", "gender", "display_name", "platform", "audience_segment"],
            "segments_to_remove":["time"],
            'data_key': 'google'
        },
        'youtube': {
            'required_columns': ["impressions", "clicks", "ctr", "cost", "cpc", "conversions","cost_per_conversion","video_views","video_view_rate"],
            'categorical_cols': ["age_range", "device", "gender", "display_name", "time_slot", "platform", "audience_segment"],
            "segments_to_remove":["time"],
            'data_key': 'youtube'
        }
    }
    
    # Validate platform
    if platform.lower() not in platform_configs:
        raise ValueError(f"Platform '{platform}' not supported. Supported platforms: {list(platform_configs.keys())}")
    
    platform_lower = platform.lower()
    config = platform_configs[platform_lower]
    
    # Use provided columns or defaults
    req_cols = config['required_columns']
    cat_cols = config['categorical_cols']
    
    # Get platform data - FIXED: Check if data exists first
    platform_data = data.get(config['data_key'], {})
    if not platform_data:
        # print("data not found")
        return {}
    # else:
    #     print("\n======data found")
    #     print(platform_data)
        
    segments_to_remove = config.get('segments_to_remove', [])
    
    # REMOVED: undefined variables 'categorical_candidates' and 'df'
    # available_cats = [col for col in categorical_candidates if col in df.columns]
    
    filtered_data = {}
    
    # Process each categorical breakdown - FIXED: Removed undefined cat_col variable
    for category_name, category_data in platform_data.items():
        if category_name in segments_to_remove:  # filter out segment
            # print(f"\ncategory filtered: {category_name}")
            continue

        if isinstance(category_data, list):
            filtered_records = []
            for record in category_data:
                if isinstance(record, dict):
                    # Filter record to only include required columns
                    filtered_record = {}
                    for col in req_cols:
                        if col in record:
                            filtered_record[col] = record[col]
                    
                    # Add categorical identifier columns - FIXED: Use cat_cols instead of undefined cat_col
                    for key, value in record.items():
                        if key in cat_cols:
                            filtered_record[key] = value
                    
                    if filtered_record:  # Only add if not empty
                        filtered_records.append(filtered_record)
            
            if filtered_records:
                filtered_data[category_name] = filtered_records
    
    return filtered_data



def filter_all_platforms_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter data for all platforms using their default configurations.
    
    Args:
        data: The complete data dictionary containing all platform data
    
    Returns:
        Dictionary containing filtered data for all platforms
    """
    logger.info(f"filtering data for insights and action generation")
    platforms = ['facebook', 'snapchat', 'tiktok', 'twitter', 'google','youtube','instagram']
    filtered_all = {}
    for platform in platforms:
        try: 
            filtered_platform_data = filter_platform_data(data, platform)
            if filtered_platform_data:
                filtered_all[platform] = filtered_platform_data
            # break
        except Exception as e:
            logger.error(f"Warning: Could not filter data for {platform}: {str(e)}")
            continue
    
    return filtered_all

# def get_platform_campaign_audience_metrics(google_credentials,facebook_credentials,snapchat_credentials,twitter_credentials,tiktok_credentials,youtube_credentials,instagram_credentials):
#     if google_credentials:
#         google_url = (
#             BASE_URL_EMAIL + "/get_google_deep_insight"
#         )  # replace with your server URL
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(
#             google_url, json=google_credentials, headers=headers
#         )
#         google_data = response.json()
#         print("done google data")

#     else:
#         print("else google data")
#         google_data = None

#     if facebook_credentials:
#         facebook_url = (
#             BASE_URL_EMAIL + "/get_facebook_deep_insight"
#         )  # replace with your server URL
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(
#             facebook_url, json=facebook_credentials, headers=headers
#         )
#         facebook_data = response.json()
#         print(f"===============response.keys",facebook_data.keys())
#         print("done fb data")
#     else:
#         facebook_data = None
#         print("else fb data")

#     if snapchat_credentials:
#         snapchat_url = (
#             BASE_URL_EMAIL + "/get_snapchat_audience_campaign_data"
#         )  # replace with your server URL
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(
#             snapchat_url, json=snapchat_credentials, headers=headers
#         )
#         snapchat_data = response.json()
#         print("done snapchat data")

#     else:
#         snapchat_data = None
#         print("else snapchat data")

#     if twitter_credentials:
#         twitter_url = (
#             BASE_URL_EMAIL + "/get_twitter_audience_campaign_data"
#         )  # replace with your server URL
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(
#             twitter_url,
#             json={"twitter_credentials": twitter_credentials},
#             headers=headers,
#         )
#         twitter_data = response.json()
#         print("done twitter data")

#     else:
#         twitter_data = None
#         print("else twitter data")

#     if tiktok_credentials:
#         tiktok_url = (
#             BASE_URL_EMAIL + "/get_tiktok_audience_campaign_data"
#         )  # replace with your server URL
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(tiktok_url, json=tiktok_credentials, headers=headers)
#         tiktok_data = response.json()
#         print("done tiktok data")
#     else:
#         tiktok_data = None
#         print("else tiktok data")

#     if youtube_credentials:
#         youtube_url = (
#             BASE_URL_EMAIL + "/get_google_deep_insight"
#         )  # replace with your server URL
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(
#             youtube_url, json=youtube_credentials, headers=headers
#         )
#         youtube_data = response.json()
#         print("done youtube data")
#     else:
#         youtube_data = None
#         print("else youtube data")

#     if instagram_credentials:
#         instagram_url = (
#             BASE_URL_EMAIL + "/get_instagram_deep_insight"
#         )  # replace with your server URL
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(
#             instagram_url, json=instagram_credentials, headers=headers
#         )
#         instagram_data = response.json()
#         print("done instagram data")
#     else:
#         instagram_data = None
#         print("else instagram data")

    
#     audience_platforms_data = {
#         "google": google_data,
#         "facebook": facebook_data,
#         "snapchat": snapchat_data,
#         "twitter": twitter_data,
#         "tiktok": tiktok_data,
#         "youtube": youtube_data,
#         "instagram": instagram_data,
#     }
#     # print("=========================")
#     # print(audience_platforms_data)
#     # print("===========================")

#     return audience_platforms_data

