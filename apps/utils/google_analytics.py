##################################################################################################################################
######################################################## FOR GOOGLE AND YOUTUBE ##################################################
##################################################################################################################################


from datetime import datetime

from flask import jsonify
import requests
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from utils.general_constants import log_errors_and_respond

from utils.general_constants import BASE_URL_EMAIL,logger

# Global cache: full_key → client
google_ads_clients = {}

google_required_fields_for_insights=[]

youtube_required_fields_for_insights=[]


###################
# Constants
###################
get_google_campaign_data_url = f"{BASE_URL_EMAIL}/get_google_campaign_data"

QUERY = {
    "GET_CAMPAIGN_DATA_QUERY": "SELECT campaign.resource_name, campaign.id, campaign.name, campaign.status, metrics.impressions, metrics.clicks, metrics.ctr, metrics.cost_micros,metrics.average_cpc, metrics.average_cpv, metrics.video_views, metrics.video_view_rate, metrics.engagements, metrics.engagement_rate, metrics.video_quartile_p25_rate, metrics.video_quartile_p50_rate, metrics.video_quartile_p75_rate, metrics.video_quartile_p100_rate, metrics.conversions, metrics.conversions_value FROM campaign WHERE campaign.id = {campaign_id} {date_filter}",

    "ALL_AGE_QUERY": "SELECT age_range_view.resource_name, metrics.impressions, metrics.clicks, metrics.ctr, metrics.cost_micros,metrics.average_cpc, metrics.average_cpv, metrics.video_views, metrics.video_view_rate, metrics.engagements, metrics.engagement_rate, metrics.video_quartile_p25_rate, metrics.video_quartile_p50_rate, metrics.video_quartile_p75_rate, metrics.video_quartile_p100_rate, metrics.conversions, metrics.conversions_value FROM age_range_view WHERE campaign.id = {campaign_id} {date_filter}",

    "ALL_GENDER_QUERY": "SELECT gender_view.resource_name, metrics.impressions, metrics.clicks, metrics.ctr, metrics.cost_micros,metrics.average_cpc, metrics.average_cpv, metrics.video_views, metrics.video_view_rate, metrics.engagements, metrics.engagement_rate, metrics.video_quartile_p25_rate, metrics.video_quartile_p50_rate, metrics.video_quartile_p75_rate, metrics.video_quartile_p100_rate, metrics.conversions, metrics.conversions_value FROM gender_view WHERE campaign.id = {campaign_id} {date_filter}",

    "GET_DEVICE_PERFORMANCE_QUERY": "SELECT segments.device, metrics.impressions, metrics.clicks, metrics.ctr, metrics.cost_micros,metrics.average_cpc, metrics.average_cpv, metrics.video_views, metrics.video_view_rate, metrics.engagements, metrics.engagement_rate, metrics.video_quartile_p25_rate, metrics.video_quartile_p50_rate, metrics.video_quartile_p75_rate, metrics.video_quartile_p100_rate, metrics.conversions, metrics.conversions_value FROM campaign WHERE campaign.id = {campaign_id} {date_filter}",

    "ALL_TIME_SLOT_QUERY": "SELECT segments.day_of_week, segments.hour, metrics.impressions, metrics.clicks, metrics.ctr, metrics.cost_micros,metrics.average_cpc, metrics.average_cpv, metrics.video_views, metrics.video_view_rate, metrics.engagements, metrics.engagement_rate, metrics.video_quartile_p25_rate, metrics.video_quartile_p50_rate, metrics.video_quartile_p75_rate, metrics.video_quartile_p100_rate, metrics.conversions, metrics.conversions_value FROM campaign WHERE campaign.id = {campaign_id} {date_filter}",

    "GET_PLACEMENT_URL_QUERY": "SELECT group_placement_view.display_name, group_placement_view.placement, group_placement_view.placement_type, group_placement_view.target_url, metrics.impressions, metrics.clicks, metrics.ctr, metrics.cost_micros,metrics.average_cpc, metrics.average_cpv, metrics.video_views, metrics.video_view_rate, metrics.engagements, metrics.engagement_rate, metrics.conversions, metrics.conversions_value FROM group_placement_view WHERE campaign.id = {campaign_id} {date_filter}",

    "GET_KEYWORD_PERFORMANCE_QUERY": "SELECT ad_group.id, ad_group_criterion.criterion_id, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, metrics.impressions, metrics.conversions, metrics.clicks, metrics.cost_micros, metrics.average_cpc, metrics.conversions_value, metrics.ctr FROM keyword_view WHERE campaign.id = {campaign_id} {date_filter}",

    "GET_SEARCH_TERM_PERFORMANCE_QUERY": "SELECT search_term_view.ad_group, search_term_view.search_term, search_term_view.status, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.average_cpc, metrics.ctr, metrics.conversions, metrics.conversions_value, campaign.id, campaign.name, ad_group.id, ad_group.name FROM search_term_view WHERE campaign.id = {campaign_id} {date_filter}",

    "AUDIENCE_SEGMENT_QUERY":"SELECT campaign.id, campaign.name, ad_group.id, ad_group.name, ad_group_criterion.criterion_id, ad_group_criterion.status, ad_group_criterion.user_interest.user_interest_category, metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.average_cpc, metrics.conversions, metrics.conversions_value, metrics.ctr, metrics.cost_per_conversion FROM ad_group_audience_view WHERE campaign.id = {campaign_id} AND ad_group_criterion.type = USER_INTEREST {date_filter}",

    "AUDIENCE_INTEREST_QUERY":"SELECT user_interest.user_interest_id, user_interest.name, user_interest.taxonomy_type FROM user_interest WHERE user_interest.user_interest_id IN ({ids_str})"



}

###################
# helper functions
###################

def safe_api_call(url, data):
    """Make API call and return empty list if there's an error"""
    try:
        response = requests.post(url=url, json=data)
        result = response.json()
        
        # Check if response contains error or if the response field contains error strings
        if "error" in result or (isinstance(result.get("response"), str) and "error" in result.get("response", "").lower()):
            return []
        
        # Return the response data or empty list if None
        return result.get("response", [])
    except Exception as e:
        # If any exception occurs, return empty list
        return []


def get_google_data(google_credentials,platform):
    google_config = {
        "customer_id": google_credentials.get("customer_id"),
        "campaign_id": google_credentials.get("campaign_id"),
        "developer_token": google_credentials.get("developer_token"),
        "client_id": google_credentials.get("client_id"),
        "client_secret": google_credentials.get("client_secret"),
        "refresh_token": google_credentials.get("refresh_token"),
        "start_date": google_credentials.get("start_date"),
        "end_date": google_credentials.get("end_date"),
    }

    google_response = requests.post(
        get_google_campaign_data_url, json=google_config
    ).json()

    if platform =='google':
        return google_data_preparation(google_response)
    else:
        return youtube_data_preparation(google_response)


def get_or_create_google_ads_client(credentials_dict):
    """
    If refresh_token changed for the same developer_token+client_id,
    evict the old client to free memory, then create and cache the new one.
    """
    try:
        # Identify the logical user (developer_token + client_id)
        user_key = f"{credentials_dict['developer_token']}|{credentials_dict['client_id']}"
        # Include refresh_token so each distinct token has its own full_key
        full_key = f"{user_key}|{credentials_dict['refresh_token']}"

        # Evict old client if any exists for this user_key but with different token
        for existing_full_key in list(google_ads_clients):
            if existing_full_key.startswith(user_key) and existing_full_key != full_key:
                del google_ads_clients[existing_full_key]
        # Create and cache new client if not already present
        if full_key not in google_ads_clients:
            config = {
                "developer_token": credentials_dict["developer_token"],
                "client_id": credentials_dict["client_id"],
                "client_secret": credentials_dict["client_secret"],
                "refresh_token": credentials_dict["refresh_token"],
                "use_proto_plus": True,
            }
            google_ads_clients[full_key] = GoogleAdsClient.load_from_dict(config)

        # print(f"\n\nfull key loaded for the google............\n\n, {full_key}")

        return google_ads_clients[full_key]
    except Exception as e:
        logger.error(f"Error creating Google Ads client: {e}")
        # print(f"Error creating Google Ads client: {e}")
        return None

def process_campaign_data(client, customer_id, campaign_id, start_date, end_date):
    # client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")

    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'"

    query = QUERY.get("GET_CAMPAIGN_DATA_QUERY").format(
        campaign_id=campaign_id, date_filter=date_filter
    )

    response = ga_service.search(customer_id=customer_id, query=query)
    campaign_data = {}
    for row in response:
        campaign_name = row.campaign.name
        campaign_status = row.campaign.status.name
        impressions = row.metrics.impressions
        clicks = row.metrics.clicks
        cost_micros = row.metrics.cost_micros
        conversions = row.metrics.conversions
        conversions_value = row.metrics.conversions_value
        ctr = row.metrics.ctr
        avg_cpc = row.metrics.average_cpc

        # Video-specific metrics
        average_cpv = row.metrics.average_cpv
        video_views = row.metrics.video_views
        video_view_rate = row.metrics.video_view_rate
        engagements = row.metrics.engagements
        engagement_rate = row.metrics.engagement_rate
        video_quartile_p25_rate = row.metrics.video_quartile_p25_rate
        video_quartile_p50_rate = row.metrics.video_quartile_p50_rate
        video_quartile_p75_rate = row.metrics.video_quartile_p75_rate
        video_quartile_p100_rate = row.metrics.video_quartile_p100_rate

        # Calculated metrics
        cost = cost_micros / 1_000_000 if cost_micros else 0
        cpl = cost / conversions if conversions else 0
        cpv = average_cpv / 1_000_000 if average_cpv else 0
        average_cpc = avg_cpc / 1_000_000 if avg_cpc else 0

        campaign_data = {
            "campaign_name": campaign_name,
            "campaign_status": campaign_status,
            "impressions": impressions,
            "clicks": clicks,
            "cost_micros": cost_micros,
            "cost": cost,
            "conversions": conversions,
            "conversions_value": conversions_value,
            "avg_cpc": average_cpc,
            # Video-specific metrics
            "video_views": video_views,
            "video_view_rate": (
                round(video_view_rate * 100, 2) if video_view_rate else 0
            ),  # Convert to percentage
            "engagements": engagements,
            "engagement_rate": (
                round(engagement_rate * 100, 2) if engagement_rate else 0
            ),  # Convert to percentage
            "average_cpv": cpv,  # Cost per view in dollars
            # Video quartile rates (percentage of people who watched to each quartile)
            "video_quartile_25_rate": (
                round(video_quartile_p25_rate * 100, 2)
                if video_quartile_p25_rate
                else 0
            ),
            "video_quartile_50_rate": (
                round(video_quartile_p50_rate * 100, 2)
                if video_quartile_p50_rate
                else 0
            ),
            "video_quartile_75_rate": (
                round(video_quartile_p75_rate * 100, 2)
                if video_quartile_p75_rate
                else 0
            ),
            "video_quartile_100_rate": (
                round(video_quartile_p100_rate * 100, 2)
                if video_quartile_p100_rate
                else 0
            ),
            # Calculated performance metrics
            "cpl": cpl,  # Cost per lead/conversion
            "ctr": (
                round(ctr * 100, 2) if ctr else 0
            ),  # Click-through rate as percentage
            "conversion_rate": (
                (conversions / clicks * 100) if clicks > 0 else 0
            ),  # Conversion rate as percentage
            "roas": conversions_value / cost if cost > 0 else 0,  # Return on ad spend
            "view_through_rate": (
                (video_quartile_p100_rate * 100) if video_quartile_p100_rate else 0
            ),  # Complete view rate
        }

    return campaign_data


def google_data_preparation(data):
    google_res = {
    "google_impr": 0,
    "google_clicks": 0,
    "google_ctr": 0,
    "google_conversions": 0,
    "google_cpc": 0,
    "google_cost": 0,
    }
    data = data.get("response")
    if isinstance(data,dict):
        google_res['google_clicks'] = int(data.get("clicks") or 0)
        google_res['google_impr'] = int(data.get("impressions") or 0)
        google_res['google_ctr'] = float(data.get("ctr") or 0)
        google_res['google_conversions'] = int(data.get("conversions") or 0)
        google_res['google_cpc'] = float(data.get("avg_cpc") or 0)
        google_res['google_cost'] = float(data.get("cost") or 0)
        logger.info(f"Google data prepared: {google_res}")
    return google_res

def youtube_data_preparation(data):
    youtube_res = {
            "youtube_impr": 0,
            "youtube_clicks": 0,
            "youtube_ctr": 0,
            "youtube_conversions": 0,
            "youtube_cpc": 0,
            "youtube_cost": 0,
        }
    data = data.get("response")
    if isinstance(data,dict):
        youtube_res['youtube_clicks'] = int(data.get("clicks") or 0)
        youtube_res['youtube_impr'] = int(data.get("impressions") or 0)
        youtube_res['youtube_ctr'] = float(data.get("ctr") or 0)
        youtube_res['youtube_conversions'] = int(data.get("conversions") or 0)
        youtube_res['youtube_cpc'] = float(data.get("avg_cpc") or 0)
        youtube_res['youtube_cost'] = float(data.get("cost") or 0)
        logger.info(f"Google data prepared: {youtube_res}")
    return youtube_res


def decode_age_range(resource_name):
    """
    Decode age range from resource name
    Format: customers/CUSTOMER_ID/ageRangeViews/CAMPAIGN_ID~AGE_RANGE_ID
    """
    age_range_mapping = {
        "503001": "18-24",
        "503002": "25-34",
        "503003": "35-44",
        "503004": "45-54",
        "503005": "55-64",
        "503006": "64+",
        "503999": "Undetermined",
    }

    if "~" in resource_name:
        age_range_id = resource_name.split("~")[-1]
        return age_range_mapping.get(age_range_id, f"Unknown({age_range_id})")
    return "Unknown"


def process_google_age_range(client, customer_id, campaign_id, start_date, end_date):

    # client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")

    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'"

    query = QUERY.get("ALL_AGE_QUERY").format(
        campaign_id=campaign_id, date_filter=date_filter
    )
    response = ga_service.search(customer_id=customer_id, query=query)
    age_data = {}

    for row in response:
        resource = row.age_range_view.resource_name
        impressions = row.metrics.impressions
        clicks = row.metrics.clicks
        cost_micros = row.metrics.cost_micros
        conversions = row.metrics.conversions
        conversions_value = row.metrics.conversions_value
        ctr = row.metrics.ctr
        avg_cpc = row.metrics.average_cpc

        # Video-specific metrics
        average_cpv = row.metrics.average_cpv
        video_views = row.metrics.video_views
        video_view_rate = row.metrics.video_view_rate
        engagements = row.metrics.engagements
        engagement_rate = row.metrics.engagement_rate
        video_quartile_p25_rate = row.metrics.video_quartile_p25_rate
        video_quartile_p50_rate = row.metrics.video_quartile_p50_rate
        video_quartile_p75_rate = row.metrics.video_quartile_p75_rate
        video_quartile_p100_rate = row.metrics.video_quartile_p100_rate

        # Calculated metrics
        cost = cost_micros / 1_000_000 if cost_micros else 0
        cpl = cost / conversions if conversions else 0
        cpv = average_cpv / 1_000_000 if average_cpv else 0
        average_cpc = avg_cpc / 1_000_000 if avg_cpc else 0

        age_range = decode_age_range(resource)
        if age_range not in age_data:
            age_data[age_range] = {
                "impressions": 0,
                "clicks": 0,
                "ctr": 0,
                "cost_micros": 0,
                "cost": 0.0,
                "cpl": 0,
                "cpv": 0,
                "conversions": 0.0,
                "conversions_value": 0.0,
                "cpc_micros": 0,
                "cost_per_conversion": 0.0,
                "cpc": 0,
                "roas": 0.0,
                "resources_count": 0,
                # "video_views": 0,
                "video_views": 0,
                "video_view_rate": 0,
                "engagements": 0,
                "engagement_rate": 0,
                "video_quartile_p25_rate": 0,
                "video_quartile_p50_rate": 0,
                "video_quartile_p75_rate": 0,
                "video_quartile_p100_rate": 0,
                "age_range":age_range
            }
        age_data[age_range]["age_range"] = age_range
        age_data[age_range]["impressions"] += impressions
        age_data[age_range]["ctr"] += round(ctr * 100, 2)
        age_data[age_range]["clicks"] += clicks
        age_data[age_range]["cpc"] += average_cpc
        age_data[age_range]["cost_micros"] += cost_micros
        age_data[age_range]["cost"] += cost
        age_data[age_range]["conversions"] += conversions
        age_data[age_range]["conversions_value"] += conversions_value
        age_data[age_range]["cpl"] += cpl
        age_data[age_range]["video_views"] += video_views
        age_data[age_range]["video_view_rate"] += (
            round(video_view_rate * 100, 2) if video_view_rate else 0
        )
        age_data[age_range]["engagements"] += engagements
        age_data[age_range]["engagement_rate"] += (
            round(engagement_rate * 100, 2) if engagement_rate else 0
        )
        age_data[age_range]["video_quartile_p25_rate"] += (
            round(video_quartile_p25_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        age_data[age_range]["video_quartile_p50_rate"] += (
            round(video_quartile_p50_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        age_data[age_range]["video_quartile_p75_rate"] += (
            round(video_quartile_p75_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        age_data[age_range]["video_quartile_p100_rate"] += (
            round(video_quartile_p100_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        age_data[age_range]["cpv"] += cpv
        age_data[age_range]["resources_count"] += 1

    # Calculate derived metrics
    for age_range, data in age_data.items():
        data["cost_per_conversion"] = (
            data["cost"] / data["conversions"] if data["conversions"] > 0 else 0
        )
        data["roas"] = (
            data["conversions_value"] / data["cost"] if data["cost"] > 0 else 0
        )
     # Convert dict -> list
    age_data_list = list(age_data.values())
    return age_data_list


def decode_gender(resource_name):
    """
    Decode gender from resource name
    Format: customers/CUSTOMER_ID/genderViews/CAMPAIGN_ID~GENDER_ID
    """
    gender_mapping = {"10": "Male", "11": "Female", "20": "Undetermined"}

    if "~" in resource_name:
        gender_id = resource_name.split("~")[-1]
        return gender_mapping.get(gender_id, f"Unknown({gender_id})")
    return "Unknown"


def process_google_gender_data(client, customer_id, campaign_id, start_date, end_date):
    # client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")

    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'"

    query = QUERY.get("ALL_GENDER_QUERY").format(
        campaign_id=campaign_id, date_filter=date_filter
    )
    response = ga_service.search(customer_id=customer_id, query=query)

    gender_data = {}

    for row in response:
        resource = row.gender_view.resource_name
        impressions = row.metrics.impressions
        clicks = row.metrics.clicks
        cost_micros = row.metrics.cost_micros
        conversions = row.metrics.conversions
        conversions_value = row.metrics.conversions_value
        ctr = row.metrics.ctr
        avg_cpc = row.metrics.average_cpc

        # Video-specific metrics
        average_cpv = row.metrics.average_cpv
        video_views = row.metrics.video_views
        video_view_rate = row.metrics.video_view_rate
        engagements = row.metrics.engagements
        engagement_rate = row.metrics.engagement_rate
        video_quartile_p25_rate = row.metrics.video_quartile_p25_rate
        video_quartile_p50_rate = row.metrics.video_quartile_p50_rate
        video_quartile_p75_rate = row.metrics.video_quartile_p75_rate
        video_quartile_p100_rate = row.metrics.video_quartile_p100_rate

        # Calculated metrics
        cost = cost_micros / 1_000_000 if cost_micros else 0
        cpl = cost / conversions if conversions else 0
        cpv = average_cpv / 1_000_000 if average_cpv else 0
        average_cpc = avg_cpc / 1_000_000 if avg_cpc else 0

        gender = decode_gender(resource)

        if gender not in gender_data:
            gender_data[gender] = {
                "gender" : gender,
                "impressions": 0,
                "clicks": 0,
                "ctr": 0,
                "cost_micros": 0,
                "cost": 0.0,
                "conversions": 0.0,
                "conversions_value": 0.0,
                "cost_per_conversion": 0.0,
                "roas": 0.0,
                "resources_count": 0,
                "cpc": 0,
                "cpl": 0,
                "cpv": 0,
                "video_views": 0,
                "video_view_rate": 0,
                "engagements": 0,
                "engagement_rate": 0,
                "video_quartile_p25_rate": 0,
                "video_quartile_p50_rate": 0,
                "video_quartile_p75_rate": 0,
                "video_quartile_p100_rate": 0,
            }
        gender_data[gender]["gender"] = gender
        gender_data[gender]["impressions"] += impressions
        gender_data[gender]["ctr"] += round(ctr * 100, 2)
        gender_data[gender]["clicks"] += clicks
        gender_data[gender]["cost_micros"] += cost_micros
        gender_data[gender]["conversions"] += conversions
        gender_data[gender]["conversions_value"] += conversions_value
        gender_data[gender]["cpc"] += average_cpc
        gender_data[gender]["video_quartile_p25_rate"] += (
            round(video_quartile_p25_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        gender_data[gender]["video_quartile_p50_rate"] += (
            round(video_quartile_p50_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        gender_data[gender]["video_quartile_p75_rate"] += (
            round(video_quartile_p75_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        gender_data[gender]["video_quartile_p100_rate"] += (
            round(video_quartile_p100_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        gender_data[gender]["video_views"] += video_views
        gender_data[gender]["video_view_rate"] += (
            round(video_view_rate * 100, 2) if video_view_rate else 0
        )
        gender_data[gender]["cpv"] += cpv
        gender_data[gender]["cpl"] += cpl
        gender_data[gender]["engagements"] += engagements
        gender_data[gender]["engagement_rate"] += (
            round(engagement_rate * 100, 2) if engagement_rate else 0
        )

    # Calculate derived metrics
    for gender, data in gender_data.items():
        data["cost"] = data["cost_micros"] / 1_000_000
        data["roas"] = (
            data["conversions_value"] / data["cost"] if data["cost"] > 0 else 0
        )
        data["cost_per_conversion"] = (
            data["cost"] / data["conversions"] if data["conversions"] > 0 else 0
        )
    # Convert dict -> list
    gender_data_list = list(gender_data.values())
    return gender_data_list


def process_google_device_performance(
    client, customer_id, campaign_id, start_date, end_date
):
    # client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")

    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'"

    query = QUERY.get("GET_DEVICE_PERFORMANCE_QUERY").format(
        campaign_id=campaign_id, date_filter=date_filter
    )

    response = ga_service.search(customer_id=customer_id, query=query)
    device_data = {}
    for row in response:
        device = row.segments.device.name
        impressions = row.metrics.impressions
        clicks = row.metrics.clicks
        cost_micros = row.metrics.cost_micros
        conversions = row.metrics.conversions
        conversions_value = row.metrics.conversions_value
        ctr = row.metrics.ctr
        avg_cpc = row.metrics.average_cpc

        # Video-specific metrics
        average_cpv = row.metrics.average_cpv
        video_views = row.metrics.video_views
        video_view_rate = row.metrics.video_view_rate
        engagements = row.metrics.engagements
        engagement_rate = row.metrics.engagement_rate
        video_quartile_p25_rate = row.metrics.video_quartile_p25_rate
        video_quartile_p50_rate = row.metrics.video_quartile_p50_rate
        video_quartile_p75_rate = row.metrics.video_quartile_p75_rate
        video_quartile_p100_rate = row.metrics.video_quartile_p100_rate

        # Calculated metrics
        cost = cost_micros / 1_000_000 if cost_micros else 0
        cpl = cost / conversions if conversions else 0
        cpv = average_cpv / 1_000_000 if average_cpv else 0
        average_cpc = avg_cpc / 1_000_000 if avg_cpc else 0

        d = device_data.setdefault(
            device,
            {
                "impressions": 0,
                "clicks": 0,
                "ctr": 0,
                "cost_micros": 0,
                "conversions": 0,
                "conversions_value": 0,
            },
        )
        d["impressions"] += impressions
        d["ctr"] += round(ctr * 100, 2)
        d["clicks"] += clicks
        d["cost_micros"] += cost_micros
        d["conversions"] += conversions
        d["conversions_value"] += conversions_value
        d["cpc"] = average_cpc
        d["cpl"] = cpl
        d["cost"] = cost
        d["cpv"] = cpv
        d["video_views"] = video_views
        d["video_view_rate"] = round(video_view_rate * 100, 2) if video_view_rate else 0
        d["engagements"] = engagements
        d["engagement_rate"] = round(engagement_rate * 100, 2) if engagement_rate else 0
        d["video_quartile_p25_rate"] = (
            round(video_quartile_p25_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        d["video_quartile_p50_rate"] = (
            round(video_quartile_p50_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        d["video_quartile_p75_rate"] = (
            round(video_quartile_p75_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        d["video_quartile_p100_rate"] = (
            round(video_quartile_p100_rate * 100, 2) if video_quartile_p25_rate else 0
        )

    # Compute derived metrics
    output_rows = []
    for device, vals in device_data.items():
        conv_rate_pct = (
            (vals["conversions"] / vals["clicks"] * 100) if vals["clicks"] > 0 else 0
        )
        cost_per_conv = (
            (vals["cost"] / vals["conversions"]) if vals["conversions"] > 0 else 0
        )
        roas = (vals["conversions_value"] / vals["cost"]) if vals["cost"] > 0 else 0

        output_rows.append(
            {
                "device": device,
                "impressions": vals["impressions"],
                "clicks": vals["clicks"],
                "cost": round(vals["cost"], 2),
                "conversions": vals["conversions"],
                "conv_value": round(vals["conversions_value"], 2),
                "cpc": round(vals["cpc"], 2),
                "conv_rate_pct": round(conv_rate_pct, 2),
                "cost_per_conversion": round(cost_per_conv, 2),
                "ctr": vals["ctr"],
                "conversion_rate": round(conv_rate_pct, 2),
                "roas": round(roas, 2),
                "video_views": vals["video_views"],
                "video_view_rate": vals["video_view_rate"],
                "engagements": vals["engagements"],
                "engagement_rate": vals["engagement_rate"],
                "video_quartile_p25_rate": vals["video_quartile_p25_rate"],
                "video_quartile_p50_rate": vals["video_quartile_p50_rate"],
                "video_quartile_p75_rate": vals["video_quartile_p75_rate"],
                "video_quartile_p100_rate": vals["video_quartile_p100_rate"],
                "cpv": vals["cpv"],
                "cpl": vals["cpl"],
            }
        )

    return output_rows


def hour_to_12h_range(hour):
    start = datetime.strptime(f"{hour}:00", "%H:%M").strftime("%I:%M %p")
    end_hour = (hour + 1) % 24
    end = datetime.strptime(f"{end_hour}:00", "%H:%M").strftime("%I:%M %p")
    return f"{start}-{end}"


def day_of_week_mapping(day_of_week):
    """Map Google Ads day_of_week enum (1-7) to day names"""
    day_map = {
        1: "Sunday",
        2: "Monday",
        3: "Tuesday",
        4: "Wednesday",
        5: "Thursday",
        6: "Friday",
        7: "Saturday",
    }
    return day_map.get(day_of_week, f"Unknown({day_of_week})")


def process_google_time_slots_data(
    client, customer_id, campaign_id, start_date, end_date
):

    # client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")

    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'"

    query = QUERY.get("ALL_TIME_SLOT_QUERY").format(
        campaign_id=campaign_id, date_filter=date_filter
    )
    response = ga_service.search(customer_id=customer_id, query=query)

    time_slot_data = {}
    for row in response:
        # Video-specific metrics
        average_cpv = row.metrics.average_cpv
        video_views = row.metrics.video_views
        video_view_rate = row.metrics.video_view_rate
        engagements = row.metrics.engagements
        engagement_rate = row.metrics.engagement_rate
        video_quartile_p25_rate = row.metrics.video_quartile_p25_rate
        video_quartile_p50_rate = row.metrics.video_quartile_p50_rate
        video_quartile_p75_rate = row.metrics.video_quartile_p75_rate
        video_quartile_p100_rate = row.metrics.video_quartile_p100_rate

        # Calculated metrics
        cost_micros = row.metrics.cost_micros
        conversions = row.metrics.conversions
        avg_cpc = row.metrics.average_cpc
        cost = cost_micros / 1_000_000 if cost_micros else 0
        cpl = cost / conversions if conversions else 0
        cpv = average_cpv / 1_000_000 if average_cpv else 0
        average_cpc = avg_cpc / 1_000_000 if avg_cpc else 0

        hour = row.segments.hour  # integer 0–23
        day_of_week = row.segments.day_of_week  # integer 1-7
        slot = hour_to_12h_range(hour)
        d = time_slot_data.setdefault(
            slot,
            {
                "impressions": 0,
                "clicks": 0,
                "ctr": 0,
                "cost_micros": 0,
                "conversions": 0,
                "conversions_value": 0,
            },
        )

        d["impressions"] += row.metrics.impressions
        d["ctr"] += round(row.metrics.ctr * 100, 2)
        d["clicks"] += row.metrics.clicks
        d["cost_micros"] += cost_micros
        d["conversions"] += conversions
        d["conversions_value"] += row.metrics.conversions_value
        d["cpc"] = average_cpc
        d["cpl"] = cpl
        d["cpv"] = cpv
        d["video_views"] = video_views
        d["video_view_rate"] = round(video_view_rate * 100, 2) if video_view_rate else 0
        d["engagements"] = engagements
        d["engagement_rate"] = round(engagement_rate * 100, 2) if engagement_rate else 0
        d["video_quartile_p25_rate"] = (
            round(video_quartile_p25_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        d["video_quartile_p50_rate"] = (
            round(video_quartile_p50_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        d["video_quartile_p75_rate"] = (
            round(video_quartile_p75_rate * 100, 2) if video_quartile_p25_rate else 0
        )
        d["video_quartile_p100_rate"] = (
            round(video_quartile_p100_rate * 100, 2) if video_quartile_p25_rate else 0
        )

        d["day_of_week"] = day_of_week_mapping(day_of_week)

    # Compute derived metrics and prepare CSV rows
    output_rows = []
    for slot, vals in sorted(time_slot_data.items()):
        cost_usd = vals["cost_micros"] / 1_000_000
        conv_rate_pct = (
            (vals["conversions"] / vals["clicks"] * 100) if vals["clicks"] > 0 else 0
        )
        cost_per_conversion = (
            (cost_usd / vals["conversions"]) if vals["conversions"] > 0 else 0
        )
        value_per_conv = (
            (vals["conversions_value"] / vals["conversions"])
            if vals["conversions"] > 0
            else 0
        )
        roas = (vals["conversions_value"] / cost_usd) if cost_usd > 0 else 0

        output_rows.append(
            {
                "time_slot": slot,
                "day_of_week": vals["day_of_week"],
                "impressions": vals["impressions"],
                "clicks": vals["clicks"],
                "cost": round(cost_usd, 2),
                "conversions": vals["conversions"],
                "conv_value_usd": round(vals["conversions_value"], 2),
                "ctr": vals["ctr"],
                "cpc": round(vals["cpc"], 2),
                "conv_rate_pct": round(conv_rate_pct, 2),
                "cost_per_conversion": round(cost_per_conversion, 2),
                "value_per_conv_usd": round(value_per_conv, 2),
                "roas": round(roas, 2),
                "video_views": vals["video_views"],
                "video_view_rate": vals["video_view_rate"],
                "engagements": vals["engagements"],
                "engagement_rate": vals["engagement_rate"],
                "video_quartile_p25_rate": vals["video_quartile_p25_rate"],
                "video_quartile_p50_rate": vals["video_quartile_p50_rate"],
                "video_quartile_p75_rate": vals["video_quartile_p75_rate"],
                "video_quartile_p100_rate": vals["video_quartile_p100_rate"],
                "cpv": vals["cpv"],
                "cpl": vals["cpl"],
            }
        )

    return output_rows


def process_google_placements_url(
    client, customer_id, campaign_id, start_date, end_date
):
    # client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")

    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'"

    query = QUERY.get("GET_PLACEMENT_URL_QUERY").format(
        campaign_id=campaign_id, date_filter=date_filter
    )

    response = ga_service.search(customer_id=customer_id, query=query)
    # Collect data from all placements
    placement_data = {}
    total_rows = 0

    for row in response:
        total_rows += 1
        # Get placement details - target_url is the actual URL
        display_name = row.group_placement_view.display_name or "(unknown)"
        placement_id = row.group_placement_view.placement or "(unknown)"
        target_url = row.group_placement_view.target_url or "(unknown)"
        placement_type = (
            row.group_placement_view.placement_type.name
            if row.group_placement_view.placement_type
            else "UNKNOWN"
        )
        avg_cpc = row.metrics.average_cpc
        average_cpv = row.metrics.average_cpv
        video_views = row.metrics.video_views
        video_view_rate = row.metrics.video_view_rate
        engagements = row.metrics.engagements
        engagement_rate = row.metrics.engagement_rate
        # Use target_url as the primary key since it contains the actual URL
        key = target_url

        d = placement_data.setdefault(
            key,
            {
                "impressions": 0,
                "clicks": 0,
                "cost_micros": 0,
                "conversions": 0,
                "cost": 0,
                "cpc": avg_cpc / 1_000_000 if avg_cpc else 0,
                "ctr": 0,
                "cost_per_conversion":0,
                "roas": 0,
                "conversions_value": 0,
                "placement_type": placement_type,
                "display_name": display_name,
                "placement_id": placement_id,
                "target_url": target_url,
                "cpv": average_cpv / 1_000_000 if average_cpv else 0,
                "video_views": video_views,
                "video_view_rate": (
                    round(video_view_rate * 100, 2) if video_view_rate else 0
                ),
                "engagements": engagements,
                "engagement_rate": (
                    round(engagement_rate * 100, 2) if engagement_rate else 0
                ),
            },
        )
        d['placement'] = key
        # Aggregate metrics
        d["impressions"] += row.metrics.impressions
        d["clicks"] += row.metrics.clicks
        d["ctr"] = round(row.metrics.ctr * 100, 2)
        d["cost"] += row.metrics.cost_micros / 1_000_000
        d["conversions"] += row.metrics.conversions
        d["conversions_value"] += row.metrics.conversions_value
        d["roas"] = (d["conversions_value"] / d["cost"]) if d["cost"] > 0 else 0
        d["cost_per_conversion"] = (
            d["cost"] / d["conversions"] if d["conversions"] > 0 else 0
        )

    # Convert dict to list for easier handling
    placement_data = list(placement_data.values())
    return placement_data


def process_google_keyword_performance(
    client, customer_id, campaign_id, start_date, end_date
):
    # client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")

    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'"

    query = QUERY.get("GET_KEYWORD_PERFORMANCE_QUERY").format(
        campaign_id=campaign_id, date_filter=date_filter
    )

    response = ga_service.search(customer_id=customer_id, query=query)
    results = []

    for row in response:
        criterion = row.ad_group_criterion
        keyword = criterion.keyword
        metrics = row.metrics
        cost = metrics.cost_micros / 1_000_000 if metrics.cost_micros else 0

        results.append(
            {
                "ad_group_id": row.ad_group.id,
                "criterion_id": criterion.criterion_id,
                "keyword_text": keyword.text,
                "match_type": keyword.match_type.name,
                "impressions": metrics.impressions,
                "conversions": metrics.conversions,
                "clicks": metrics.clicks,
                "cost": cost,
                "conversions_value": metrics.conversions_value,
                "ctr": metrics.ctr,
                "cpc": (cost / metrics.clicks) if metrics.clicks > 0 else 0,
                "cost_per_conversion" : cost/metrics.conversions if metrics.conversions > 0 else 0
            }
        )
        
    return results


def process_google_search_term_performance(
    client, customer_id, campaign_id, start_date, end_date
):
    # client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")

    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'"

    query = QUERY.get("GET_SEARCH_TERM_PERFORMANCE_QUERY").format(
        campaign_id=campaign_id, date_filter=date_filter
    )
    response = ga_service.search(customer_id=customer_id, query=query)
    results = []

    for row in response:
        metrics = row.metrics
        search_term = row.search_term_view.search_term
        cost = metrics.cost_micros / 1_000_000 if metrics.cost_micros else 0
        results.append(
            {
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "ad_group_id": row.ad_group.id,
                "ad_group_name": row.ad_group.name,
                "search_term": search_term,
                "status": row.search_term_view.status.name,
                "impressions": metrics.impressions,
                "clicks": metrics.clicks,
                "cost": cost,
                "conversions_value": metrics.conversions_value,
                "conversions": metrics.conversions,
                "cpc": (cost / metrics.clicks) if metrics.clicks > 0 else 0,
                "ctr": (
                    round(metrics.ctr * 100, 2) if metrics.ctr else 0
                ),  # Convert to percentage
                "cost_per_conversion" : cost/metrics.conversions if metrics.conversions > 0 else 0,
                "roas": (metrics.conversions_value / cost) if cost > 0 else 0,
            }
        )

    return results


def process_google_audience_segments(client,
                                    customer_id,
                                    campaign_id,
                                    start_date,
                                    end_date):
    ga_service = client.get_service("GoogleAdsService")
    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'"

    query= QUERY.get("AUDIENCE_SEGMENT_QUERY").format(
        campaign_id=campaign_id,date_filter=date_filter)
    
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    
    data = []
    user_interest_ids = set()
    
    for batch in response:
        for row in batch.results:
            user_interest_resource = row.ad_group_criterion.user_interest.user_interest_category
            user_interest_id = None
            
            if user_interest_resource:
                parts = user_interest_resource.split('/')
                if len(parts) >= 4 and parts[-2] == 'userInterests':
                    user_interest_id = int(parts[-1])
                    user_interest_ids.add(user_interest_id)
            
            data.append({
                'date': row.segments.date,
                'campaign_id': row.campaign.id,
                'campaign_name': row.campaign.name,
                'ad_group_id': row.ad_group.id,
                'ad_group_name': row.ad_group.name,
                'criterion_id': row.ad_group_criterion.criterion_id,
                'criterion_status': row.ad_group_criterion.status.name,
                'user_interest_id': user_interest_id,
                'clicks': row.metrics.clicks,
                'impressions': row.metrics.impressions,
                'cost': row.metrics.cost_micros / 1_000_000,
                'conversions': row.metrics.conversions,
                'ctr': round(row.metrics.ctr * 100, 2),
                'cost_per_conversion': row.metrics.cost_per_conversion / 1_000_000 if row.metrics.cost_per_conversion > 0 else 0
            })
    
    if data and user_interest_ids:
        # print(f"Found {len(user_interest_ids)} unique user interest IDs, resolving names...")
        
        # Get user interest names
        user_interest_mapping = get_user_interest_details_batch(client, customer_id, list(user_interest_ids))
        
        # Add resolved names to data
        for row in data:
            user_interest_id = row['user_interest_id']
            if user_interest_id and user_interest_id in user_interest_mapping:
                row['audience_segment'] = user_interest_mapping[user_interest_id]['name']
                row['taxonomy_type'] = user_interest_mapping[user_interest_id]['taxonomy_type']
            else:
                row['audience_segment'] = f"User Interest ID: {user_interest_id}" if user_interest_id else "Unknown"
                row['taxonomy_type'] = "Unknown"
        
        # df = pd.DataFrame(data)
        # resolved_count = sum(1 for name in df['audience_segment'] if not name.startswith('User Interest ID:'))
        # print(f"✓ Resolved {resolved_count}/{len(df)} audience segment names")
        
        return data
    
    return data
    

def get_user_interest_details_batch(client,customer_id, user_interest_ids):
    """
    Get user interest details for multiple IDs in one query
    """
    # client = GoogleAdsClient.load_from_storage("google-ads.yaml")
    
    # Convert list to comma-separated string for IN clause
    ids_str = ','.join(map(str, user_interest_ids))
    
    query = QUERY.get("AUDIENCE_INTEREST_QUERY").format(ids_str=ids_str)
    
    ga_service = client.get_service("GoogleAdsService")
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    
    mapping = {}
    for batch in response:
        for row in batch.results:
            mapping[row.user_interest.user_interest_id] = {
                'name': row.user_interest.name,
                'taxonomy_type': row.user_interest.taxonomy_type.name
            }
    
    return mapping
    

@log_errors_and_respond(status_code=500,platform="google")
def get_google_audience_data(data = None):
    # data = request.get_json()
    campaign_type = data.get("campaign_type","place_holder")
    developer_token = data.get("developer_token")
    client_id = data.get("client_id")
    client_secret = data.get("client_secret")
    refresh_token = data.get("refresh_token")
    customer_id = data.get("customer_id")
    campaign_id = data.get("campaign_id")
    start_date = data.get("start_date")
    end_date = data.get("end_date")


    audience_data={
    "age": [],
    "gender": [],
    "time": [],
    "placement": [],
    "device": [],
    }
    

    config = {
        "developer_token": developer_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "use_proto_plus": True,
    }
    # Normalize campaign_type
    campaign_type = campaign_type.lower()

    # Define valid campaign types
    valid_campaign_types = ["display", "search", "demand_gen", "performance_max"]

    if campaign_type not in valid_campaign_types:
        logger.error(f"Invalid campaign_type. Valid types: {valid_campaign_types}")
        return audience_data


    google_ads_audiece_client = get_or_create_google_ads_client(config)
    # print("google_ads_audiece_client",google_ads_audiece_client)
    if not google_ads_audiece_client:
        logger.error("Google : Failed to initialize Google Ads client")
        return audience_data
    # Make safe API calls
    logger.info(f"Google audience age data is being fetched")
    age_data = process_google_age_range(
        google_ads_audiece_client, customer_id, campaign_id, start_date, end_date
    )
    logger.info(f"Google audience gender data is being fetched")
    gender_data = process_google_gender_data(
        google_ads_audiece_client, customer_id, campaign_id, start_date, end_date
    )
    logger.info(f"Google audience time-slots data is being fetched")
    time_data = process_google_time_slots_data(
        google_ads_audiece_client, customer_id, campaign_id, start_date, end_date
    )
    logger.info(f"Google audience device data is being fetched")
    device_data = process_google_device_performance(
        google_ads_audiece_client, customer_id, campaign_id, start_date, end_date)
    logger.info(f"Google audience interests data is being fetched")
    interest_data = process_google_audience_segments(
        google_ads_audiece_client, customer_id, campaign_id, start_date, end_date
    )

    audience_data.update({"age": age_data,"gender":gender_data,"time":time_data,"audience":interest_data,"device":device_data})

    if campaign_type in ["display", "demand_gen", "performance_max"]:
        logger.info(f"Google audience placement data is being fetched")
        placement_data = process_google_placements_url(
            google_ads_audiece_client, customer_id, campaign_id, start_date, end_date)
        
        audience_data.update({"placement":placement_data})
        return audience_data

    elif campaign_type == "search":
        logger.info(f"Google audience keyword and search-terms data is being fetched")
        keyword_data = process_google_keyword_performance(
            google_ads_audiece_client, customer_id, campaign_id, start_date, end_date)
        search_term_data = process_google_search_term_performance(
            google_ads_audiece_client, customer_id, campaign_id, start_date, end_date)
        

        audience_data.update({"keywords":keyword_data,"search_terms":search_term_data})
        return audience_data

    # Default fallback (though this shouldn't be reached due to campaign_type validation)
    return {
        "age": age_data,
        "gender": gender_data,
        "time": time_data,
        "device": device_data,
    }
