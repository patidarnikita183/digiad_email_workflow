#twitter_audience_analytics.py
import time
import gzip
import json
import requests
from requests_oauthlib import OAuth1
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from datetime import datetime, timedelta
from collections import OrderedDict
from utils.general_constants import logger

# -------------------- Auth helper --------------------
def get_auth(oauth_token, oauth_token_secret, twitter_consumer_key, twitter_consumer_secret):
    return OAuth1(
        # os.getenv("TWITTER_CONSUMER_KEY"),
        # os.getenv("TWITTER_CONSUMER_SECRET"),
        twitter_consumer_key,
        twitter_consumer_secret,
        oauth_token,
        oauth_token_secret,
        signature_type="auth_header"
    )

# -------------------- Split long date ranges --------------------
MAX_DAYS = 45

def split_date_range(start_time, end_time):
    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
        end_dt = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")
        
        total_days = (end_dt - start_dt).days + 1
        if total_days <= MAX_DAYS:
            return [(start_dt.strftime("%Y-%m-%dT00:00:00Z"), end_dt.strftime("%Y-%m-%dT23:00:00Z"))]
        
        ranges = []
        current_start = start_dt

        while current_start <= end_dt:
            current_end = min(current_start + timedelta(days=MAX_DAYS-1), end_dt)
            
            # FIX: Always use 00:00 for start and 23:00 for end
            current_start_str = current_start.strftime("%Y-%m-%dT00:00:00Z")
            current_end_str = current_end.strftime("%Y-%m-%dT23:00:00Z")
            
            ranges.append((current_start_str, current_end_str))
            
            # Next chunk starts at next day
            current_start = current_end + timedelta(days=1)
            
        return ranges
    except Exception as e:
        logger.error(f"twitter : Error splitting date range: {e}")
        raise

# -------------------- Create async job --------------------
def create_job(account_id, campaign_id, oauth_token, oauth_token_secret, twitter_consumer_key, twitter_consumer_secret, segmentation_type, metric_groups, start_time, end_time):
    url = f"https://ads-api.x.com/12/stats/jobs/accounts/{account_id}"
    if isinstance(metric_groups, str):
        metric_groups = [metric_groups]

    payload = {
        "entity": "CAMPAIGN",
        "entity_ids": [campaign_id],
        "start_time": start_time,
        "end_time": end_time,
        "granularity": "TOTAL",
        "placement": "ALL_ON_TWITTER",
        "segmentation_type": segmentation_type,
        "metric_groups": metric_groups
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        # print("Sending payload:", json.dumps(payload, indent=2))
        response = requests.post(
            url,
            headers=headers,
            auth=get_auth(oauth_token, oauth_token_secret, twitter_consumer_key, twitter_consumer_secret),
            data=payload
        )
        # print("CREATE JOB Response Status:", response.status_code)
        # print("CREATE JOB Response:", response.text)
        response.raise_for_status()
        response_data = response.json()
        if "data" not in response_data:
            raise Exception(f"Unexpected response format: {response_data}")
        return response_data["data"]["id"]
    except Exception as e:
        logger.error(f"twitter : Error creating job: {e}")
        raise

# -------------------- Poll job status --------------------
def poll_job(account_id, job_id, oauth_token, oauth_token_secret, twitter_consumer_key, twitter_consumer_secret):
    url = f"https://ads-api.x.com/12/stats/jobs/accounts/{account_id}?job_ids={job_id}"
    while True:
        try:
            response = requests.get(url, auth=get_auth(oauth_token, oauth_token_secret,twitter_consumer_key, twitter_consumer_secret))
            response.raise_for_status()
            data = response.json()["data"][0]
            # print(f"Job {job_id} status: {data['status']}")
            if data["status"] == "SUCCESS":
                return data["url"]
            elif data["status"] in ["FAILED", "EXPIRED"]:
                raise Exception(f"Job {job_id} failed with status {data['status']}")
            time.sleep(5)
        except Exception as e:
            # print(f"Error polling job: {e}")
            raise

# -------------------- Download and decompress --------------------
def download_results(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        decompressed_data = gzip.decompress(response.content)
        return json.loads(decompressed_data.decode("utf-8"))
    except Exception as e:
        logger.error(f"twitter : Error downloading results: {e}")
        raise

# -------------------- Flatten response (FIXED) --------------------
def flatten_twitter_response(raw_data):
    cleaned = {}
    # Remove billed_charge_local_micro from key_metrics since we only want cost
    key_metrics = ["clicks", "impressions", "conversions"]

    for seg_type, seg_data in raw_data.items():
        cleaned[seg_type] = []
        for item in seg_data.get("data", []):
            for id_data in item.get("id_data", []):
                metrics = id_data.get("metrics", {})

                flat = {k: (metrics.get(k)[0] if isinstance(metrics.get(k), list) else metrics.get(k)) 
                        for k in key_metrics}

                # Sum conversions
                conversions = sum(
                    sum(v if isinstance(v, (int, float)) else 0 for v in (conv_data or {}).values())
                    for k, conv_data in metrics.items()
                    if k.startswith("conversion_") or k.startswith("mobile_conversion_")
                )

                clicks = flat.get("clicks") or 0
                impressions = flat.get("impressions") or 0
                # Get billed_charge_local_micro for cost calculation but don't include it in output
                cost_micro = metrics.get("billed_charge_local_micro")
                if isinstance(cost_micro, list):
                    cost_micro = cost_micro[0] if cost_micro else 0
                cost_micro = cost_micro or 0
                cost = cost_micro / 1_000_000

                flat.update({
                    "cost": cost,
                    "cpc": (cost / clicks) if clicks else 0,
                    "ctr": (clicks / impressions * 100) if impressions else 0,
                    "conversions": conversions
                }) 

                cleaned[seg_type].append({
                    seg_type: id_data.get("segment", {}).get("segment_name"), 
                    **flat
                })

    return cleaned

def aggregate_metrics(metrics_list, seg_type):
    """
    Aggregate metrics from multiple time chunks for the same segmentation type.
    """
    if not metrics_list:
        return []
        
    aggregated = {}
    
    # Remove billed_charge_local_micro from sum_metrics since we don't want it in output
    sum_metrics = ["clicks", "impressions", "conversions", "cost"]

    for item in metrics_list:
        seg_name = item.get(seg_type)
        if not seg_name:
            continue
            
        if seg_name not in aggregated:
            # First occurrence - copy all data
            aggregated[seg_name] = item.copy()
        else:
            # Aggregate numeric metrics
            for metric in sum_metrics:
                if metric in item and isinstance(item[metric], (int, float)) and item[metric] is not None:
                    existing_val = aggregated[seg_name].get(metric, 0) or 0
                    aggregated[seg_name][metric] = existing_val + item[metric]

    # Recalculate derived metrics (CPC, CTR) after aggregation - cost is already summed
    for seg_name, data in aggregated.items():
        clicks = data.get("clicks", 0) or 0
        impressions = data.get("impressions", 0) or 0
        cost = data.get("cost", 0) or 0  # Use aggregated cost directly
        
        data.update({
            "cpc": (cost / clicks) if clicks else 0,
            "ctr": (clicks / impressions * 100) if impressions else 0
        })

    return list(aggregated.values())
def separate_billing_call(account_id, campaign_id, oauth_token, oauth_token_secret, twitter_consumer_key, twitter_consumer_secret, segmentation_type, start_time, end_time):
    """
    Solution 1: Make separate calls for ENGAGEMENT and BILLING metrics
    Sometimes billing data is only available when requested separately
    """
    
    # First call: Get engagement data
    engagement_job_id = create_job(
        account_id, campaign_id, oauth_token, oauth_token_secret,
        twitter_consumer_key, twitter_consumer_secret,
        segmentation_type, ["ENGAGEMENT"], start_time, end_time
    )
    engagement_url = poll_job(account_id, engagement_job_id, oauth_token, oauth_token_secret, twitter_consumer_key, twitter_consumer_secret)
    engagement_data = download_results(engagement_url)
    
    # Second call: Get billing data  
    billing_job_id = create_job(
        account_id, campaign_id, oauth_token, oauth_token_secret,
        twitter_consumer_key, twitter_consumer_secret,
        segmentation_type, ["BILLING"], start_time, end_time
    )
    billing_url = poll_job(account_id, billing_job_id, oauth_token, oauth_token_secret, twitter_consumer_key, twitter_consumer_secret)
    billing_data = download_results(billing_url)
    
    # Merge the data
    merged_data = merge_engagement_billing_data(engagement_data, billing_data, segmentation_type)
    return merged_data


def merge_engagement_billing_data(engagement_data, billing_data, segmentation_type):
    """Merge engagement and billing data by segment"""
    
    # Create lookup for billing data by segment
    billing_lookup = {}
    if billing_data and 'data' in billing_data:
        for item in billing_data['data']:
            for id_data in item.get('id_data', []):
                segment_name = id_data.get('segment', {}).get('segment_name')
                if segment_name:
                    billing_lookup[segment_name] = id_data.get('metrics', {})
    
    # Merge with engagement data
    merged_result = {"data": []}
    if engagement_data and 'data' in engagement_data:
        for item in engagement_data['data']:
            merged_item = {"id_data": []}
            
            for id_data in item.get('id_data', []):
                segment_name = id_data.get('segment', {}).get('segment_name')
                engagement_metrics = id_data.get('metrics', {})
                
                # Add billing metrics if available
                billing_metrics = billing_lookup.get(segment_name, {})
                
                merged_metrics = {**engagement_metrics, **billing_metrics}
                
                merged_id_data = {
                    **id_data,
                    'metrics': merged_metrics
                }
                merged_item['id_data'].append(merged_id_data)
            
            merged_result['data'].append(merged_item)
    
    return merged_result

def get_twitter_insights(account_id, campaign_id, oauth_token, oauth_token_secret, start_time, end_time, twitter_consumer_key, twitter_consumer_secret):
    """
    Enhanced version to get billing data
    """
    
    segmentation_types = ["AGE","GENDER","INTERESTS","LOCATIONS","LANGUAGES","PLATFORMS"]
    combined = OrderedDict()
    
    try:
        date_ranges = split_date_range(start_time, end_time)
        
    except Exception as e:
        logger.error(f"twitter : Error splitting date range: {str(e)}")
        return {"error": f"Error splitting date range: {str(e)}"}

    for seg in segmentation_types:
        # print(f"\nProcessing segmentation: {seg}")
        seg_combined = []
        errors = []
        
        try:
            for chunk_idx, (start_time_2, end_time_2) in enumerate(date_ranges):
                # print(f"Processing chunk {chunk_idx+1}/{len(date_ranges)}: {s} to {e}")
                
                try:
                    # Try Solution 1: Separate calls
                    try:
                        data = separate_billing_call(
                            account_id, campaign_id, oauth_token, oauth_token_secret,
                            twitter_consumer_key, twitter_consumer_secret, seg, start_time_2, end_time_2
                        )
                        
                    except Exception as e:
                        logger.error(f"twitter : Error in twitter: {str(e)}")
                    
                    # Process the data
                    chunk_data = flatten_twitter_response({seg: data})[seg]
                    seg_combined.extend(chunk_data)
                                            
                except Exception as chunk_error:
                    error_msg = f"Chunk {chunk_idx+1} ({start_time_2} to {end_time_2}): {str(chunk_error)}"
                    errors.append(error_msg)
                    logger.error(f"twitter : Error in chunk: {error_msg}")
            
            # Aggregate results from all chunks
            if seg_combined:
                combined[seg] = aggregate_metrics(seg_combined, seg)
                if errors:
                    combined[seg + "_errors"] = errors
            else:
                combined[seg] = []
                
        except Exception as e:
            logger.error(f"twitter : Error processing {seg}: {str(e)}")
            combined[seg] = {"error": str(e)}

    return combined


