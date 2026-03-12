
import json
from urllib.parse import quote
import requests
from utils.general_constants import logger

with open("utils/tiktok_interest.json", "r") as f:
    interests = json.load(f)

def get_tiktok_campaign_report(
    access_token, customer_id, date_str_start, date_str_end, page, dimensions, metrics
):
    base_url = "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/"

    url = (
        f"{base_url}"
        f"?advertiser_id={customer_id}"
        f"&report_type=BASIC"
        f"&data_level=AUCTION_CAMPAIGN"
        f"&dimensions={quote(json.dumps(dimensions))}"
        f"&metrics={quote(json.dumps(metrics))}"
        f"&start_date={date_str_start}"
        f"&end_date={date_str_end}"
        f"&page_size=1000"
        f"&page={page}"
        f"&order_type=DESC"
        f"&order_field=spend"
        f"&service_type=AUCTION"
    )

    headers = {"Access-Token": access_token, "Content-Type": "application/json"}

    # print(url)
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def fetch_tiktok_report(access_token, customer_id, date_str_start, date_str_end):
    """
    Fetch paginated TikTok report data between start_time and end_time.
    Returns a combined list of all data items.
    """
    page = 1
    report_data = []
    dimensions = ["campaign_id"]
    metrics = [
        "spend",
        "cpc",
        "cpm",
        "impressions",
        "clicks",
        "ctr",
        "reach",
        "cost_per_1000_reached",
        "frequency",
        "conversion",
        "cost_per_conversion",
        "conversion_rate_v2",
        "real_time_conversion",
        "real_time_cost_per_conversion",
        "real_time_conversion_rate_v2",
        "result",
        "cost_per_result",
        "result_rate",
        "real_time_result",
        "real_time_cost_per_result",
        "real_time_result_rate",
    ]

    while True:
        response = get_tiktok_campaign_report(
            access_token=access_token,
            customer_id=customer_id,
            date_str_start=date_str_start,
            date_str_end=date_str_end,
            page=page,
            dimensions=dimensions,
            metrics=metrics,
        )

        # Handle API failure
        if response.get("code") != 0:
            logger.error(f"Tiktok : API Error: {response.get('message')}")
            break

        data_list = response.get("data", {}).get("list", [])
        report_data.extend(data_list)

        page_info = response.get("data", {}).get("page_info", {})
        total_page = page_info.get("total_page", 0)

        if page >= total_page:
            break

        page += 1

    return report_data


def structure_tiktok_analytics_data(report_data, user_campaign_id):
    """
    Convert raw TikTok API report data into structured analytics dictionary.
    """
    structured_data = {
        "tiktok_impr": 0,
        "tiktok_clicks": 0,
        "tiktok_cost": 0,
        "tiktok_conversions": 0,
        "tiktok_ctr": 0,
        "tiktok_cpc": 0
    }
    if not report_data:
        return structured_data # to handle the key error.
        # return {"message": "No data available", "campaigns": []}

    for entry in report_data:
        campaign_id = entry.get("dimensions").get("campaign_id")
        if campaign_id == user_campaign_id:
            structured_data["tiktok_impr"] = int(
                entry.get("metrics").get("impressions", 0)
            )
            structured_data["tiktok_clicks"] = int(
                entry.get("metrics").get("clicks", 0)
            )
            structured_data["tiktok_cost"] = float(entry.get("metrics").get("spend", 0))
            structured_data["tiktok_conversions"] = int(
                entry.get("metrics").get("conversions", 0)
            )
            structured_data["tiktok_ctr"] = float(entry.get("metrics").get("ctr", 0))
            structured_data["tiktok_cpc"] = float(entry.get("metrics").get("cpc", 0))

    return structured_data


def tiktok_data_preparation(data):
    clicks, impressions, ctr, conversions, cost_per_click, cost = 0, 0, 0, 0, 0, 0
    data = {
        "tiktok_clicks": clicks,
        "tiktok_impr": impressions,
        "tiktok_ctr": ctr,
        "tiktok_conversions": conversions,
        "tiktok_cpc": cost_per_click,
        "tiktok_cost": cost,
    }
    return data

############################ AUDIENCE ANALYTICS #################################

def get_interest_audience(interest_audience_tiktok,interests):
  res = []
  for entry in interest_audience_tiktok:
      interest_id = entry.get("dimensions", {}).get("interest_category_v2")
      interest_name = interests.get(interest_id)  # None if not found
      entry["metrics"]["interest"] = interest_name
      entry.pop('dimensions', None)
      res.append(entry["metrics"])
  return res

def get_tiktok_campaign_report_audience(access_token, customer_id, date_str_start, date_str_end, page, dimensions, metrics,campaign_id):
    base_url = "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/"
    filters = [
        {
            "field_name": "campaign_ids",
            "filter_type": "IN",
            "filter_value": f"[{campaign_id}]"  # use list, not string
        }
    ]

    url = (
        f"{base_url}"
        f"?advertiser_id={customer_id}"
        f"&report_type=AUDIENCE"
        f"&data_level=AUCTION_CAMPAIGN"
        f"&dimensions={quote(json.dumps(dimensions))}"
        f"&metrics={quote(json.dumps(metrics))}"
        f"&start_date={date_str_start}"
        f"&end_date={date_str_end}"
        f"&page_size=1000"
        f"&page={page}"
        f"&order_type=DESC"
        f"&order_field=spend"
        f"&service_type=AUCTION"
        f"&filtering={quote(json.dumps(filters))}"
    )

    headers = {
        "Access-Token": access_token,
        "Content-Type": "application/json"
    }

    # print(url)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()


def fetch_tiktok_report_audience(access_token, customer_id,date_str_start, date_str_end,dimensions,campaign_id):
    """
    Fetch paginated TikTok report data between start_time and end_time.
    Returns a combined list of all data items.
    """
    page = 1
    report_data = []
    metrics = ['spend', 'cpc', 'cpm','impressions','clicks','ctr','conversion']

    try:
        while True:
            response = get_tiktok_campaign_report_audience(
              access_token=access_token,
              customer_id=customer_id,
              date_str_start=date_str_start,
              date_str_end = date_str_end,
              page=page,
              dimensions=dimensions,
              metrics=metrics,
              campaign_id=campaign_id
            )

            # Handle API failure - return empty list instead of breaking
            if response.get("code") != 0:
                logger.error(f"Tiktok : API Error: {response.get('message')}")
                return []  # Return empty list instead of breaking

            data_list = response.get("data", {}).get("list", [])
            report_data.extend(data_list)

            page_info = response.get("data", {}).get("page_info", {})
            total_page = page_info.get("total_page", 0)

            if page >= total_page:
                break

            page += 1

    except Exception as e:
        logger.error(f"Exception in fetch_tiktok_report_audience: {e}")
        return []  # Return empty list on exception

    return report_data

def get_tiktok_audience_metrics(access_token, customer_id,date_str_start, date_str_end,campaign_id):
    final_res = {}
    dimensions = [["age"],["gender"],["country_code"],["language"],["platform"]]
    
    try:
        # Handle interest category separately
        interest_audience_tiktok = fetch_tiktok_report_audience(access_token, customer_id,date_str_start, date_str_end,['interest_category'],campaign_id)
        tiktok_audience_interest_data = get_interest_audience(interest_audience_tiktok,interests)
        final_res['interest_category'] = tiktok_audience_interest_data if tiktok_audience_interest_data else []
        
        # Handle other dimensions
        for dimension in dimensions:
            temp = fetch_tiktok_report_audience(access_token, customer_id,date_str_start, date_str_end,dimension,campaign_id)

            res = []
            if temp:  # Only process if temp is not empty
                for data in temp:
                    value = data.get('dimensions', {}).get(dimension[0])
                    data['metrics'][dimension[0]] = value
                    data.pop('dimensions', None)
                    res.append(data['metrics'])

            final_res[dimension[0]] = res  # Will be empty list if temp was empty

    except Exception as e:
        logger.error(f"Exception in get_tiktok_audience_metrics: {e}")
        # Return structure with empty lists for all dimensions
        final_res = {
            'interest_category': [],
            'age': [],
            'gender': [],
            'country_code': [],
            'language': [],
            'platform': []
        }

    return final_res


# def fetch_tiktok_report_audience(access_token, customer_id,date_str_start, date_str_end,dimensions,campaign_id):
#     """
#     Fetch paginated TikTok report data between start_time and end_time.
#     Returns a combined list of all data items.
#     """
#     page = 1
#     report_data = []
#     # metrics = [   'spend',
#     #           'cpc',
#     #           'cpm',
#     #           'impressions',
#     #           'clicks',
#     #           'ctr',
#     #           'reach',
#     #           'cost_per_1000_reached',
#     #           'frequency',
#     #           'conversion',
#     #           'cost_per_conversion',
#     #           'conversion_rate_v2',
#     #           'real_time_conversion',
#     #           'real_time_cost_per_conversion',
#     #           'real_time_conversion_rate_v2',
#     #           'result',
#     #           'cost_per_result',
#     #           'result_rate',
#     #           'real_time_result',
#     #           'real_time_cost_per_result',
#     #           'real_time_result_rate',
#     #         ]

#     metrics = ['spend', 'cpc', 'cpm','impressions','clicks','ctr','conversion']

#     while True:
#         response = get_tiktok_campaign_report_audience(
#           access_token=access_token,
#           customer_id=customer_id,
#           date_str_start=date_str_start,
#           date_str_end = date_str_end,
#           page=page,
#           dimensions=dimensions,
#           metrics=metrics,
#           campaign_id=campaign_id
#         )

#         # Handle API failure
#         if response.get("code") != 0:
#             print(f"API Error: {response.get('message')}")
#             break

#         data_list = response.get("data", {}).get("list", [])
#         report_data.extend(data_list)

#         page_info = response.get("data", {}).get("page_info", {})
#         total_page = page_info.get("total_page", 0)

#         if page >= total_page:
#             break

#         page += 1

#     return report_data

# def get_tiktok_audience_metrics(access_token, customer_id,date_str_start, date_str_end,campaign_id):
#     final_res = {}
#     dimensions = [["age"],["gender"],["country_code"],["language"],["platform"]]
#     interest_audience_tiktok = fetch_tiktok_report_audience(access_token, customer_id,date_str_start, date_str_end,['interest_category'],campaign_id)
#     tiktok_audience_interest_data = get_interest_audience(interest_audience_tiktok,interests)
#     final_res['interest_category'] = tiktok_audience_interest_data
#     for dimension in dimensions:

#         temp = fetch_tiktok_report_audience(access_token, customer_id,date_str_start, date_str_end,dimension,campaign_id)

#         res =[]
#         for data in temp:
#             value = data.get('dimensions', {}).get(dimension[0])
#             # print(value)
#             data['metrics'][dimension[0]] = value
#             data.pop('dimensions', None)
#             res.append(data['metrics'])

#         final_res[dimension[0]] = res
#     return final_res


