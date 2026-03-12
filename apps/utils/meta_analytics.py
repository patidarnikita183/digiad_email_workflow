##############################
## For facebook and instagram
#############################
import json
from collections import OrderedDict
import requests
from flask import jsonify
from datetime import datetime, timedelta

# from utils.general_helper import log_errors_and_respond
from utils.general_constants import BASE_URL_EMAIL,log_errors_and_respond,logger

########################
# -------Constants
########################

get_facebook_campaign_data_url = f"{BASE_URL_EMAIL}/get_meta_campaign_data"

fb_params = {"fields": "impressions,clicks,ctr,spend,reach,frequency,cpc,results"}

api_version = "v23.0"

meta_required_fields = ["access_token", "ad_campaign_id"]


BREAKDOWN_CONFIG = {
    "age": {"breakdowns": "age"},
    "gender": {"breakdowns": "gender"},
    "age_and_gender": {"breakdowns": "age,gender"},
    "device_platform": {"breakdowns": "device_platform"},
    "placement": {"breakdowns": "platform_position,publisher_platform"},
    "region": {"breakdowns": "region"},
    "hourly": {"breakdowns": "hourly_stats_aggregated_by_audience_time_zone"}
}

############################
# -------helper functions---
############################
def extract_api_params(request=None, required_fields=None,payload=None):
    """
    Extract and validate common API parameters from request payload

    Args:
        required_fields (list): List of required field names to validate

    Returns:
        tuple: (params_dict, error_response) - error_response is None if valid
    """
    if request:
        payload = request.get_json()

    if not payload:
        return None, (
            jsonify({"success": False, "error": "No JSON payload provided"}),
            400,
        )

    # Extract parameters
    params = {
        "access_token": payload.get("access_token"),
        "api_version": api_version,
        "ad_campaign_id": payload.get("ad_campaign_id"),
        "start_date": payload.get("start_date"),
        "end_date": payload.get("end_date"),
    }

    # Validate required fields
    required_fields = required_fields
    for field in required_fields:
        if not params.get(field):
            return None, (jsonify({"success": False, "error": f"Missing {field}"}), 400)

    # Add time range if both dates are provided
    if params["start_date"] and params["end_date"]:
            start_date = datetime.strptime(params["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(params["end_date"], "%Y-%m-%d")
            
            # Extend the window: subtract 1 day from start, add 1 day to end
            extended_start = start_date - timedelta(days=1)
            extended_end = end_date + timedelta(days=1)
            
            # Update the params with extended dates
            params["start_date"] = extended_start.strftime("%Y-%m-%d")
            params["end_date"] = extended_end.strftime("%Y-%m-%d")
            
            # Create time range with extended dates
            time_range = {
                "since": params["start_date"], 
                "until": params["end_date"]
            }
            params["time_range"] = json.dumps(time_range)

    return params, None


def make_api_request(params, endpoint_type="insights"):
    """Helper function to make API requests with error handling.

    Args:
        endpoint_type (str): Type of endpoint - 'insights', 'campaigns', etc.
        params (dict): Complete params dict containing ad_campaign_id, access_token, api_version,
                      and API-specific params like breakdowns, fields, time_range, etc.

    Returns:
        dict | None: JSON response dict on success; None on failure (after logging error).
    """
    # Extract internal params
    ad_campaign_id = params.get("ad_campaign_id")
    access_token = params.get("access_token")
    api_version = params.get("api_version")

    if not access_token or not ad_campaign_id:
        return None

    # Build endpoint URL
    endpoint = f"{ad_campaign_id}/{endpoint_type}"
    url = f"https://graph.facebook.com/{api_version}/{endpoint}"

    # Prepare API request params (exclude internal params)
    internal_params = {"ad_campaign_id", "api_version", "start_date", "end_date"}
    request_params = {k: v for k, v in params.items() if k not in internal_params}
    # print(f"\n\nMaking request to {url} with params: {request_params}\n\n")
    try:
        response = requests.get(url, params=request_params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error during meta API request: {e}")
        return None


# process api response data to extract results and flatten structure
def process_api_response_data(data):
    """
    Process API response data to extract results and flatten structure
    """
    if not data or "data" not in data:
        return None

    for entry in data["data"]:
        results = entry.pop("results", [])
        if results and isinstance(results, list):
            for res in results:
                indicator = res.get("indicator")
                value_data = res.get("values", [{}])[0]
                value = value_data.get("value")

                # Create new keys in JSON
                entry["result_indicator"] = indicator
                entry["result_value"] = value
    # print(f"=================response data : {data}====================\n\n\n")
    return data["data"]


def create_api_response(data, success_message="Data retrieved successfully"):
    """
    Create standardized API response

    Args:
        data: Processed data or None if failed
        success_message (str): Message for successful response

    Returns:
        tuple: (json_response, status_code)
    """
    if data is not None:
        return {"success": True, "data": data, "message": success_message}

    return  {
                "success": False,
                "error": "No data returned from API",
                "message": "No response from API or processing failed"
            }
        
    
def calculate_cost_per_lead(spend, result_value):
    """
    Calculate cost per lead safely handling empty/null result_value
    """
    # Convert spend to float, default to 0 if invalid
    spend_val = float(spend) if spend is not None and spend != "" else 0.0

    # Handle result_value - it can be empty, None, or invalid
    if result_value is None or result_value == "" or result_value == 0:
        # If no leads, return None or a special indicator
        return (
            None if spend_val == 0 else float("inf")
        )  # inf indicates spend but no leads

    result_val = float(result_value)
    if result_val == 0:
        return float("inf") if spend_val > 0 else None

    return round(spend_val / result_val, 2)


def get_facebook_data(facebook_credentials=None):  ## Same used for Instagram
    facebook_response = {}
    # print("facebook credentials : ",facebook_credentials)
    if facebook_credentials:
        headers = {"Content-Type": "application/json"}
        facebook_response = requests.post(
            get_facebook_campaign_data_url,
            data=json.dumps(facebook_credentials),
            headers=headers,
        ).json()
        # print(f"===================facebook_response : {facebook_response} ===================")
    return facebook_data_preparation(facebook_response)


def facebook_data_preparation(data):
    # print(f"data received in facebook data preparation : {data}")
    data = data.get("data")
    # print("\n\n\npasssseddd data : ", data)

    clicks, impressions, ctr, conversions, cost_per_click, cost = 0, 0, 0, 0, 0, 0

    if data and isinstance(data, list) and len(data) > 0:
        data = data[0]
        clicks = int(data.get("clicks") or 0)
        impressions = int(data.get("impressions") or 0)
        ctr = float(data.get("ctr") or 0)
        conversions = int(data.get("result_value") or 0)
        cost_per_click = float(data.get("cpc") or 0)
        cost = float(data.get("spend") or 0)

    data = {
        "clicks": clicks,
        "impressions": impressions,
        "ctr": ctr,
        "conversions": conversions,
        "cost_per_click": cost_per_click,
        "cost": cost,
    }
    logger.info(f"Meta prepared data : {data}")
    # print(f"prepared facebook data : {data}")
    return data


def prepare_insight_data(
    age_response,
    gender_response,
    age_and_gender_response,
    time_response,
    device_response,
    placement_response,
    regional_response,
):
    """
    Processes multiple API responses and extracts data based on success conditions.
    Returns data if success is True, empty list if success is False.
    """

    def extract_data(response):
        """Extract data from response based on success condition."""
        # print(f"response in extract data : {response}")
        if "success" in response and response["success"]:
            return response["data"]
        else:
            return []

    # Extract data from each response
    age_data = extract_data(age_response)
    # print(f"age data extracted : {age_data}")
    gender_data = extract_data(gender_response)
    age_and_gender_data = extract_data(age_and_gender_response)
    time_data = extract_data(time_response)
    device_data = extract_data(device_response)
    placement_data = extract_data(placement_response)
    regional_data = extract_data(regional_response)

    return (
        age_data,
        gender_data,
        age_and_gender_data,
        time_data,
        device_data,
        placement_data,
        regional_data,
    )



###################################################
# main function to get the audience insights data
###################################################

@log_errors_and_respond(status_code=500,platform="meta")
def get_meta_campaign_audience_metrics(data=None):
    """
    Get comprehensive Facebook insights data for multiple breakdown types
    """
    # data = request.get_json()
    
    # Make API calls for each breakdown type (matching original order)
    BREAKDOWN_TYPES = ["age", "gender", "age_and_gender", "hourly", "device_platform", "placement", "region"]

    params, error = extract_api_params(
     required_fields=meta_required_fields, payload=data
    )
    
    if error:
        raise
    
    params.update(fb_params)
    # print("****************params : ",params)
    raw_responses = []
    for breakdown_type in BREAKDOWN_TYPES:
        breakdown_config = BREAKDOWN_CONFIG[breakdown_type]
        params.update({"breakdowns": breakdown_config["breakdowns"]})
        # print(f"params : {params}")
        
    # try:
        data = make_api_request(params)
        # print(f"\ndata received in response: {data}")
        processed_data = process_api_response_data(data)
        # print(F"\nprocessed data : {processed_data}")

        response_data = create_api_response(processed_data)
        raw_responses.append(response_data)
    # except Exception as e:
        # Handle API errors - you might want to handle this differently
        # raw_responses.append({"error": str(e)})
    
    # Unpack responses to match original function signature
    age_response, gender_response, age_and_gender_response, time_response, device_response, placement_response, regional_response = raw_responses
    
    # print(f"*******************age_response : {age_response}")
    # print(f"*******************gender response : {gender_response}")
    # print(f"********************age and gender response : {age_and_gender_response}")
    # Use the original prepare_insight_data method
    (
        age_data,
        gender_data,
        age_and_gender_data,
        time_data,
        device_data,
        placement_data,
        regional_data,
    ) = prepare_insight_data(
        age_response,
        gender_response,
        age_and_gender_response,
        time_response,
        device_response,
        placement_response,
        regional_response,
    )
    # print(f"\n\n\n*******************age_data : {age_data}")
    return  OrderedDict({
            "age": age_data,
            "gender": gender_data,
            "age_and_gender": age_and_gender_data,
            "hourly_data": time_data,
            "device": device_data,
            "placement": placement_data,
            "regional_data": regional_data,
        })
    



