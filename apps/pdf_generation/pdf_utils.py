import functools
import re
import logging
import numpy as np
from typing import Callable, Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime, timezone
from pdf_generation.config import *
from utils.general_constants import logger
import textwrap

###########################################################
################       General utils    ###################
###########################################################
def generate_fle_name(campaign_name):
    # return f"{campaign_name.replace(' ', '_').lower()}_{datetime.now(timezone.utc).strftime('%d_%b_%Y_%H_%M')}_report.pdf"
    return f"{campaign_name.replace(' ', '_').lower()}_{datetime.now(timezone.utc).strftime('%d_%b_%Y')}_report.pdf"

def load_json_data(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def match_insight_to_plot(df_name: str, x_column: str, insights_data: dict, platform: str = None) -> dict:
    """
    Match insights and actions to specific plots based on dataframe name, x_column, and platform.
    Returns dict with 'insight' and 'action' for the specific plot.
    
    Args:
        df_name: Name of the dataframe
        x_column: Column used for x-axis in plot
        insights_data: Dictionary containing all insights
        platform: Platform name (google, meta, snapchat, twitter, tiktok)
    """
    plot_insights = {"insight": None, "action": None}
    
    # Platform-specific insight mapping
    platform_mappings = {
        "google": {
            "gender": ["gender_exclude"],
            "device": ["device_exclude"],
            "placement": ["placements_exclude"],
            "platform_position": ["placements_exclude"],
            "display_name":["display_name_exclude","placements_exclude"],
            "audience_segment":["audience_exclude"]
        },
        "youtube": {
            "gender": ["gender_exclude"],
            "device": ["device_exclude"],
            "placement": ["placements_exclude"],
            "platform_position": ["placements_exclude"],
            "display_name":["display_name_exclude","placements_exclude"],
            "audience_segment":["audience_exclude"]
        },
        
        "facebook": {
            "gender": ["gender_exclude"],
            "device": ["devices_exclude"],
            "device_platform": ["devices_exclude"],
            "placement": ["placements_exclude"],
            "platform_position": ["placements_exclude"]
        },
        
        "instagram": {
            "GENDER": ["gender_exclude"],
            "device": ["devices_exclude"],
            "device_platform": ["devices_exclude"],
            "placement": ["placements_exclude"],
            "platform_position": ["placements_exclude"]
        },
        
        "snapchat": {
            "gender": ["gender_exclude"],
            "device": ["devices_exclude"],
            "device_platform": ["devices_exclude"],
            "lifestyle_category": ["lifestyle_category_exclude"],
            "country": ["countries_exclude"],
            "os": ["os_exclude"],
            "operating_system": ["os_exclude"]
        },
        
        "twitter": {
            "gender": ["gender_exclude"],
            "INTERESTS": ["interests_exclude"],
            "LANGUAGES": ["languages_exclude"],
            "LOCATIONS":["locations_exclude"],
            "PLATFORMS": ["platforms_exclude"],
            "device": ["devices_exclude"],
            "device_platform": ["devices_exclude"]
        },
        
        "tiktok": {
            "gender": ["gender_exclude"],
            "language": ["languages_exclude"],
            "country_code":["country_code_exclude","country_exclude"],
            "interest_category": ["interest_category"],
            "interest": ["interest_category"],
            "platform": ["platforms_exclude"],
            "device": ["platforms_exclude"],  # TikTok uses platforms for device data
            "device_platform": ["platforms_exclude"]
        }
    }
    
    # Generic mapping (fallback when platform not specified or not in platform_mappings)
    # generic_mapping = {
    #     # Age-related plots
    #     "age": ["age_exclude", "age_optimize", "age_targeting"],
    #     "age_range": ["age_exclude", "age_optimize", "age_targeting"],
    #     "age_bucket": ["age_exclude", "age_optimize", "age_targeting"],
    #     "AGE": ["age_exclude", "age_optimize", "age_targeting"],
        
    #     # Gender-related plots
    #     "gender": ["gender_exclude", "gender_optimize", "gender_targeting"],
    #     "GENDER": ["gender_exclude", "gender_optimize", "gender_targeting"],
        
    #     # Device-related plots
    #     "device": ["devices_exclude", "device_exclude", "device_optimize", "device_targeting"],
    #     "device_platform": ["devices_exclude", "device_exclude", "device_optimize", "device_targeting"],
        
    #     # Placement-related plots
    #     "placement": ["placements_exclude", "placement_optimize", "placement_targeting"],
    #     "platform_position": ["placements_exclude", "placement_optimize", "placement_targeting"],
        
    #     # Regional/Location plots
    #     "region": ["regions_exclude", "countries_exclude", "region_optimize", "location_targeting"],
    #     "regional_data": ["regions_exclude", "countries_exclude", "region_optimize", "location_targeting"],
    #     "country": ["regions_exclude", "countries_exclude", "region_optimize", "location_targeting"],
    #     "country_code": ["regions_exclude", "countries_exclude", "region_optimize", "location_targeting"],
    #     "LOCATIONS": ["regions_exclude", "countries_exclude", "region_optimize", "location_targeting"],
        
    #     # Interest-related plots
    #     "interest": ["interest_exclude", "interests_exclude", "interest_category", "interest_optimize", "interest_targeting"],
    #     "interests": ["interest_exclude", "interests_exclude", "interest_category", "interest_optimize", "interest_targeting"],
    #     "INTERESTS": ["interest_exclude", "interests_exclude", "interest_category", "interest_optimize", "interest_targeting"],
    #     "interest_category_name": ["interest_exclude", "interests_exclude", "interest_category", "interest_optimize", "interest_targeting"],
    #     "interest_category": ["interest_exclude", "interests_exclude", "interest_category", "interest_optimize", "interest_targeting"],
        
    #     # Time-related plots
    #     "time": ["time_optimize", "schedule_optimize"],
    #     "time_slot": ["time_optimize", "schedule_optimize"],
    #     "hour": ["time_optimize", "schedule_optimize"],
        
    #     # Creative/Display name plots
    #     "display_name": ["creative_optimize", "ad_creative_insights"],
        
    #     # Platform-related plots
    #     "platform": ["platform_exclude", "platforms_exclude", "platform_optimize"],
    #     "PLATFORMS": ["platform_exclude", "platforms_exclude", "platform_optimize"],
        
    #     # Language plots
    #     "language": ["language_optimize", "languages_exclude", "language_targeting"],
    #     "LANGUAGES": ["language_optimize", "languages_exclude", "language_targeting"],
        
    #     # Operating System
    #     "os": ["os_exclude", "os_optimize"],
    #     "operating_system": ["os_exclude", "os_optimize"],
        
    #     # Lifestyle (Snapchat specific)
    #     "lifestyle_category": ["lifestyle_category_exclude"]
    # }
    
    # Determine which mapping to use
    if platform and platform.lower() in platform_mappings:
        relevant_categories = platform_mappings[platform.lower()].get(x_column.lower(), [])
        # If no platform-specific mapping found, fall back to generic
    #     if not relevant_categories:
    #         relevant_categories = generic_mapping.get(x_column.lower(), [])
    # else:
    #     relevant_categories = generic_mapping.get(x_column.lower(), [])
    
    # Look for matching insights in the insights_data
    for category in relevant_categories:
        if category in insights_data:
            insight_item = insights_data[category]
            if isinstance(insight_item, dict):
                plot_insights["insight"] = insight_item.get("insight")
                plot_insights["action"] = insight_item.get("action")
                break
            elif isinstance(insight_item, str):
                plot_insights["insight"] = insight_item
                break
    
    # Enhanced fallback: if no specific match, try pattern matching
    if not plot_insights["insight"]:
        # Look for any insight that might be relevant using pattern matching
        x_column_lower = x_column.lower()
        
        for key, value in insights_data.items():
            key_lower = key.lower()
            
            # Direct substring match
            if x_column_lower in key_lower or key_lower in x_column_lower:
                if x_column_lower=='age':
                    continue  # skip age to mapp with the  language keyword

                if isinstance(value, dict):
                    plot_insights["insight"] = value.get("insight")
                    plot_insights["action"] = value.get("action")
                    break
                elif isinstance(value, str):
                    plot_insights["insight"] = value
                    break
            
            # # Semantic matching for common variations
            # semantic_matches = {
            #     "gender": ["gender", "sex", "male", "female"],
            #     "device": ["device", "platform", "mobile", "desktop", "tablet"],
            #     "language": ["language", "lang", "locale"],
            #     "interest": ["interest", "category", "topic"],
            #     "country": ["country", "location", "geo", "region"],
            #     "age": ["age", "demographic"]
            # }
            
            # for semantic_key, variations in semantic_matches.items():
            #     if x_column_lower in variations or any(var in x_column_lower for var in variations):
            #         if any(var in key_lower for var in variations):
            #             if isinstance(value, dict):
            #                 plot_insights["insight"] = value.get("insight")
            #                 plot_insights["action"] = value.get("action")
            #                 break
            #             elif isinstance(value, str):
            #                 plot_insights["insight"] = value
            #                 break
            
            if plot_insights["insight"]:
                break
    
    return plot_insights



# def match_insight_to_plot(df_name: str, x_column: str, insights_data: dict) -> dict:
#     """
#     Match insights and actions to specific plots based on dataframe name and x_column.
#     Returns dict with 'insight' and 'action' for the specific plot.
#     """
#     plot_insights = {"insight": None, "action": None}
    
#     # Define mapping between plot characteristics and insight categories
#     insight_mapping = {
#         # Age-related plots
#         "age": ["age_exclude", "age_optimize", "age_targeting"],
#         "age_range": ["age_exclude", "age_optimize", "age_targeting"],
#         "age_bucket": ["age_exclude", "age_optimize", "age_targeting"],
#         "AGE": ["age_exclude", "age_optimize", "age_targeting"],
        
#         # Gender-related plots
#         "gender": ["gender_exclude", "gender_optimize", "gender_targeting"],
#         "GENDER": ["gender_exclude", "gender_optimize", "gender_targeting"],
        
#         # Device-related plots
#         "device": ["devices_exclude", "device_optimize", "device_targeting"],
#         "device_platform": ["devices_exclude","device_platform_exclude", "device_optimize", "device_targeting"],
        
#         # Placement-related plots
#         "placement": ["placements_exclude", "placement_optimize", "placement_targeting"],
#         "platform_position": ["placements_exclude", "placement_optimize", "placement_targeting"],
        
#         # Regional/Location plots
#         "region": ["regions_exclude", "region_optimize", "location_targeting"],
#         "regional_data": ["regions_exclude", "region_optimize", "location_targeting"],
#         "country": ["regions_exclude", "region_optimize", "location_targeting"],
#         "country_code": ["regions_exclude", "region_optimize", "location_targeting"],
#         "LOCATIONS": ["regions_exclude", "region_optimize", "location_targeting"],
        
#         # Interest-related plots
#         "interest": ["interest_exclude", "interest_optimize", "interest_targeting"],
#         "interests": ["interest_exclude", "interest_optimize", "interest_targeting"],
#         "INTERESTS": ["interest_exclude", "interest_optimize", "interest_targeting"],
#         "interest_category_name": ["interest_exclude", "interest_optimize", "interest_targeting"],
        
#         # Time-related plots
#         "time": ["time_optimize", "schedule_optimize"],
#         "time_slot": ["time_optimize", "schedule_optimize"],
#         "hour": ["time_optimize", "schedule_optimize"],
        
#         # Creative/Display name plots
#         "display_name": ["creative_optimize","placements_exclude", "ad_creative_insights"],
        
#         # Platform-related plots
#         "platform": ["platform_exclude", "platform_optimize"],
#         "PLATFORMS": ["platform_exclude", "platform_optimize"],
        
#         # Language plots
#         "language": ["language_optimize", "language_targeting"],
#         "LANGUAGES": ["language_optimize", "language_targeting"],
#     }
    
#     # Find relevant insight categories for this x_column
#     relevant_categories = insight_mapping.get(x_column.lower(), [])
    
#     # Look for matching insights in the insights_data
#     for category in relevant_categories:
#         if category in insights_data:
#             insight_item = insights_data[category]
#             if isinstance(insight_item, dict):
#                 plot_insights["insight"] = insight_item.get("insight")
#                 plot_insights["action"] = insight_item.get("action")
#                 break
#             elif isinstance(insight_item, str):
#                 plot_insights["insight"] = insight_item
#                 break
    
#     # Fallback: if no specific match, try to find general insights
#     if not plot_insights["insight"]:
#         # Look for any insight that might be relevant
#         for key, value in insights_data.items():
#             if isinstance(value, dict) and x_column.lower() in key.lower():
#                 plot_insights["insight"] = value.get("insight")
#                 plot_insights["action"] = value.get("action")
#                 break
    
#     return plot_insights

def add_insights_and_actions_to_plots(platform_data, json_data):
    """
    Enhanced version that adds insights and actions to individual plots/tables
    instead of at the platform level.
    """
    for platform_name in platform_data.keys():
        platform_key = platform_name.lower()
        
        if platform_key in json_data:
            platform_insights = json_data[platform_key]
            
            # Get platform info
            platform_info = platform_data[platform_name]
            
            # Initialize lists for plot-specific insights
            if 'plot_insights' not in platform_info:
                platform_info['plot_insights'] = []
            if 'plot_actions' not in platform_info:
                platform_info['plot_actions'] = []
            
            # Process each dataframe/plot
            for i, (df, df_title) in enumerate(zip(platform_info['dataframes'], platform_info['df_titles'])):
                # Detect the x_column for this plot
                chart_config = detect_chart_columns(df, metric='ctr')
                x_column = chart_config.get('x_column', '')
                
                # Match insights to this specific plot
                plot_insights = match_insight_to_plot(df_title, x_column, platform_insights,platform_name.lower())
                
                # Store plot-specific insights and actions
                platform_info['plot_insights'].append(plot_insights.get("insight"))
                platform_info['plot_actions'].append(plot_insights.get("action"))
    
    # Add campaign-level insights if available
    if "campaign_level" in json_data:
        platform_data['campaign_level'] = json_data['campaign_level']
    
    # Add HTML insights for general use if needed
    if "html_insights_and_actions" in json_data:
        platform_data['html_insights_and_actions'] = json_data["html_insights_and_actions"]
        
    return platform_data

def gather_platform_wise_data(data: Dict[str, Any]) -> Dict[str, Dict[str, list]]:
    """
    Enhanced version that maintains the structure for plot-specific insights
    """
    platforms = ["facebook","instagram","google","youtube", "snapchat", "tiktok", "twitter","html_insights_and_actions"]
    required_data = {}

    for platform in platforms:
        platform_data = data.get(platform, {})
        
        # Keep the original structure for backward compatibility
        insights, actions = [], []
        
        # Also keep the detailed structure for plot-specific matching
        detailed_insights = {}
        
        for category, items in platform_data.items():
            if isinstance(items, list):  # could be list of dicts OR list of strings
                for item in items:
                    if isinstance(item, dict):  # dict with keys
                        insights.append(item.get("insight"))
                        actions.append(item.get("action"))
                    elif isinstance(item, str):  # plain string (HTML case)
                        if "insight" in category:
                            insights.append(item)
                        elif "action" in category:
                            actions.append(item)
            elif isinstance(items, dict):  # single dict
                # Store detailed structure for plot matching
                detailed_insights[category] = items
                
                insights.append(items.get("insight"))
                actions.append(items.get("action"))

        required_data[platform] = {
            "insights": [i for i in insights if i],
            "actions": [a for a in actions if a],
            "detailed": detailed_insights  # Keep detailed structure
        }
        
        # Merge detailed insights into the main structure for easier access
        required_data[platform].update(detailed_insights)

    return required_data

def add_insights_and_actions(platform_data,json_data):
    for platform_name in platform_data.keys():
            platform_key = platform_name.lower()
            if platform_key in json_data and 'insights' in json_data[platform_key]:
                platform_data[platform_name]['insights'] = json_data[platform_key]['insights']
            if platform_key in json_data and 'actions' in json_data[platform_key]:
                platform_data[platform_name]['actions'] = json_data[platform_key]['actions']
    if "html_insights_and_actions" in json_data:
        platform_data['html_insights_and_actions'] = json_data["html_insights_and_actions"]
    if "campaign_level" in json_data:
        platform_data['campaign_level'] = json_data['campaign_level']
        
    #return platform data with insights and actions added
    return platform_data

def trim_display_name(name: str) -> str:
    """Trim display_name values depending on category (Mobile App, Website, YouTube Video)."""
    if not isinstance(name, str):
        return name

    if name.startswith("Mobile App:"):
        # Remove prefix and (Google Play)
        name = name.replace("Mobile App:", "").strip()
        name = name.replace("(Google Play)", "").strip()
        # Keep only App Name (ignore publisher after 'by')
        # name = name.split("by")[0].strip()
        # name = re.sub(r",?\s*by.*$", "", name).strip()
        name = re.sub(r",?\s*(by.*)?$", "", name).strip()
        return name

    # Case 2: Website
    if name.startswith("Website:"):
        # Extract domain only
        url = name.replace("Website:", "").strip()
        domain = re.sub(r"^https?://", "", url)  # remove http/https
        domain = domain.split("/")[0]  # keep only domain
        return domain

    # Case 3: YouTube Video
    if name.startswith("YouTube Video:"):
        name = name.replace("YouTube Video:", "").strip()
        # Keep only title (before first "|")
        title = name.split("|")[0].strip()
        return title

    return name

def merge_performance_and_insights_data(performance_data: dict, insights_data: dict) -> dict:
    """
    Merge insights and actions into the performance data for each platform,
    and also keep campaign-level insights/actions.
    """
    merged_data = performance_data.copy()

    for platform, data in insights_data.items():
        if platform == "html_insights_and_actions":
            # Add campaign-level insights and actions separately
            merged_data["html_insights_and_actions"] = {
                "insights": data.get("insights", []),
                "actions": data.get("actions", []),
            }
        elif platform in merged_data:
            # Add insights/actions inside each platform
            merged_data[platform]["insights"] = data.get("insights", [])
            merged_data[platform]["actions"] = data.get("actions", [])
        else:
            # If platform is only in insights_data (like instagram, youtube)
            merged_data[platform] = {
                "insights": data.get("insights", []),
                "actions": data.get("actions", []),
            }

###########################################################
#################     Dataframe utils   ###################
###########################################################

def sort_and_limit(df: pd.DataFrame, limit: int = 10, sort_col: str = "ctr") -> pd.DataFrame:
    # print("inside sort and limit")
    if sort_col in df.columns and len(df) > limit:
        df = df.sort_values(by=sort_col, ascending=False)#.head(10)
    # print("returned from sortinggg")
    return df.round(2)

def filter_columns(df: pd.DataFrame, required_cols: List[str], cat_cols: List[str]) -> pd.DataFrame:
    """
    Keep required columns and only those categorical columns that exist in the dataframe.
    
    Args:
        df (pd.DataFrame): Input dataframe
        required_cols (List[str]): Columns that must be included (if available)
        cat_cols (List[str]): Optional categorical columns to include if present
    
    Returns:
        pd.DataFrame: Filtered dataframe with selected columns
    """
    # Include required + available categorical columns
    final_cols = [col for col in cat_cols if col in df.columns] + required_cols 
    # Safeguard: only keep those actually in dataframe
    final_cols = [col for col in final_cols if col in df.columns]
    
    return df[final_cols]


def trim_string_column(df, column_name, max_length=20):
    """
    Trims the strings in the specified column of the DataFrame to a maximum length.
    
    Parameters:
    df (pd.DataFrame): The DataFrame containing the column to trim.
    column_name (str): The name of the column to trim.
    max_length (int): The maximum length of the string (default is 20).
    
    Returns:
    pd.DataFrame: The DataFrame with the modified column.
    """
    df[column_name] = df[column_name].apply(
        lambda x: x[:max_length] + '...' if isinstance(x, str) and len(x) > max_length else x
    )
    return df

###########################################################
############     Platform data processing utils   #########
###########################################################
def process_meta_json(facebook_data: Dict[str, Any], sort_col: str = "ctr", limit: int = 5) -> Dict[str, pd.DataFrame]:
    """Process Facebook JSON data into DataFrames"""
    dataframes = {}
    
    numeric_cols = ['clicks', 'cpc', 'ctr', 'impressions', 'reach', 'spend', 'frequency']

    for data_key,data in facebook_data.items():
        """Helper to create, clean, filter, and sort dataframe."""

        if data_key in ["insights", "actions"]:
            continue

        if data_key in facebook_data:
            df = pd.DataFrame(data)

            if 'hourly_stats_aggregated_by_audience_time_zone' in df.columns:
                df.rename(columns={'hourly_stats_aggregated_by_audience_time_zone': 'hour'}, inplace=True)

            # Convert numerics
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            # Sort & limit
            df = sort_and_limit(df, limit=limit, sort_col=sort_col)
            # Filter columns
            df = filter_columns(df, meta_required_columns, meta_categorical_cols)
            dataframes[data_key] = df
    return dataframes

def process_tiktok_json(tiktok_data: Dict[str, Any], sort_col: str = "ctr", limit: int = 5) -> Dict[str, pd.DataFrame]:
    """Process TikTok JSON data into DataFrames"""
    dataframes = {}
    
    numeric_cols = ['clicks','conversion','spend','cpc','ctr','impressions','cost_per_result']
    
    for data_key, data in tiktok_data.items():
        if data_key in ["insights", "actions"]:
            continue
        df = pd.DataFrame(data)
        # Convert numeric columns
        for col in tiktok_required_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        # Filter required columns
        df = filter_columns(df, tiktok_required_columns, tiktok_categorical_cols)
        # Sort & limit
        df = sort_and_limit(df, limit=limit, sort_col=sort_col)
        dataframes[data_key] = df
    
    return dataframes

def process_twitter_json(twitter_data: Dict[str, Any], sort_col: str = "ctr", limit: int = 5) -> Dict[str, pd.DataFrame]:
    """Process Twitter JSON data into DataFrames"""
    dataframes = {}
    
    numeric_cols = ['impressions', 'clicks', 'ctr', 'spend', 'cpc']
    
    for data_key, data in twitter_data.items():
        if data_key in ["insights", "actions"]:
            continue
        df = pd.DataFrame(data)
        # Convert numeric columns
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        # Filter required columns
        df = filter_columns(df, twitter_required_columns, twitter_categorical_cols)
        # Sort & limit
        df = sort_and_limit(df, limit=limit, sort_col=sort_col)
        dataframes[data_key] = df
    
    return dataframes

def process_snapchat_json(snapchat_data: Dict[str, Any], sort_col: str = "ctr", limit: int = 5) -> Dict[str, pd.DataFrame]:
    """Process Snapchat JSON data into DataFrames"""
    dataframes = {}
    
    numeric_cols = ['impressions', 'clicks', 'ctr', 'spend', 'cpc','swipes']
    
    for data_key, data in snapchat_data.items():
        if data_key in ["insights", "actions"]:
            continue

        df = pd.DataFrame(data)
        # Convert numeric columns
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        # Filter required columns
        df = filter_columns(df, snapchat_required_columns, snapchat_categorical_cols)
        # Sort & limit
        df = sort_and_limit(df, limit=limit, sort_col=sort_col)
        dataframes[data_key] = df
    
    return dataframes

def process_google_json(google_data: Dict[str, Any], sort_col: str = "ctr", limit: int = 5) -> Dict[str, pd.DataFrame]:
    dataframes = {}
    
    numeric_cols = ['impressions', 'clicks', 'ctr', 'spend', 'cpc']
    
    for data_key, data in google_data.items():
        if data_key in ["insights", "actions"]:
            continue
        # print(f"\n\nProcessing Google data key: {data_key} with {len(data)} records\n\n")
        df = pd.DataFrame(data)
        # Convert numeric columns
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if "display_name" in df.columns:
            df["display_name"] = df["display_name"].apply(trim_display_name)
        
        # if "audience_segment" in df.columns:
        # if "audience_segment" in df.columns:
        #     df = trim_string_column(df, "audience_segment", max_length=30)

        # Filter required columns
        df = filter_columns(df, google_required_columns, google_categorical_cols)
        # Sort & limit
        df = sort_and_limit(df, limit=limit, sort_col=sort_col)
        dataframes[data_key] = df
    
    return dataframes    

# @handle_exception()
def process_platform_json_data(json_data: Dict[str, Any], metric='ctr') -> Dict[str, Dict[str, pd.DataFrame]]:
    """Process JSON data for multiple platforms"""
    platform_dataframes = {}

    if 'facebook' in json_data and json_data['facebook']:
        # print("Processing Facebook data...")
        dataframes = process_meta_json(json_data['facebook'], sort_col=metric)
        if dataframes:
            platform_dataframes['facebook'] = dataframes

    if 'tiktok' in json_data and json_data['tiktok']:
        dataframes = process_tiktok_json(json_data['tiktok'], sort_col=metric)
        if dataframes:
            platform_dataframes['tiktok'] = dataframes

    if 'snapchat' in json_data and json_data['snapchat']:
        dataframes = process_snapchat_json(json_data['snapchat'], sort_col=metric)
        if dataframes:
            platform_dataframes['snapchat'] = dataframes

    if 'twitter' in json_data and json_data['twitter']:
        dataframes = process_twitter_json(json_data['twitter'], sort_col=metric)
        if dataframes:
            platform_dataframes['twitter'] = dataframes

    if 'instagram' in json_data and json_data['instagram']:
        dataframes = process_meta_json(json_data['instagram'], sort_col=metric)
        if dataframes:
            platform_dataframes['instagram'] = dataframes

    if 'google' in json_data and json_data['google']:
        dataframes = process_google_json(json_data['google'], sort_col=metric)
        if dataframes:
            platform_dataframes['google'] = dataframes

    if 'youtube' in json_data and json_data['youtube']:
        dataframes = process_google_json(json_data['youtube'], sort_col=metric)
        if dataframes:
            platform_dataframes['youtube'] = dataframes

    return platform_dataframes


###########################################################
#################   Graph plotting utils  #################
###########################################################
def detect_chart_columns(df: pd.DataFrame,metric = 'ctr') -> Dict[str, str]:
    """Automatically detect appropriate columns for chart creation"""
    chart_config = {}
    
    # Common categorical columns (x-axis candidates)
    categorical_candidates = ['age','time_slot','audience_segment',"time","age_range",'gender','display_name','device','placement','regional_data', 
                            'region', 'platform_position', 'device_platform', 
                            'interest_category_name', 'country', 'operating_system',
                            'interest', 'age_bucket', 'segment_name', 'country_code', 
                            'platform', 'language', 'interests', 'locations', 
                            'platforms', 'lifestyle_category',"AGE","GENDER",
                            "INTERESTS","LANGUAGES","LOCATIONS","PLATFORMS","hour"]
    
    twitter=["AGE","GENDER","INTERESTS","LANGUAGES","LOCATIONS","PLATFORMS"]
    google=['display_name','age_range','device','gender','time_slot','audience_segment']
    
    # Common metric columns (y-axis candidates)
    metric_candidates = ['ctr', 'cpc', 'clicks', 'impressions', 'spend', 'reach', 
                        'conversions', 'cost', 'swipes']
    
    # Priority mapping for grouped charts (age-related as primary x-axis)
    age_columns = ['age', 'age_bucket', 'AGE']
    gender_columns = ['gender', 'GENDER']
    
    # Find categorical columns
    available_cats = [col for col in categorical_candidates if col in df.columns]
    
    # Check for age + gender combination for grouped charts
    age_col = next((col for col in age_columns if col in available_cats), None)
    gender_col = next((col for col in gender_columns if col in available_cats), None)
    
    if age_col and gender_col:
        chart_config['x_column'] = age_col
        chart_config['grouped_col'] = gender_col
        chart_config['chart_style'] = 'grouped'
    else:
        # Find single categorical column
        for col in categorical_candidates:
            if col in df.columns:
                chart_config['x_column'] = col
                break
    
    # Find metric column (prefer CTR if available)
    if metric in df.columns:
        chart_config['y_column'] = metric
    else:
        for col in metric_candidates:
            if col in df.columns:
                chart_config['y_column'] = col
                break
    
    return chart_config

def determine_chart_type(df: pd.DataFrame, x_column: str, chart_config: Dict) -> str:
    """Determine the best chart type based on data characteristics"""
    if chart_config.get('chart_style') == 'grouped':
        return 'grouped_bar'
    
    if x_column in df.columns:
        unique_values = df[x_column].nunique()
        # Use pie chart for categorical data with few categories (2-5)
        if unique_values <= 3:
            return 'pie'
        # Use bar chart for everything else
        else:
            return 'bar'
    return 'bar' 

def create_grouped_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, grouped_col: str, 
                           palette: str = 'modern_blues', title: str = None, top_n=None) -> Tuple[plt.Figure, plt.Axes]:
    """Create grouped bar chart with modern styling"""
    
    # 🔹 Take only first n records if requested
    if top_n is not None and top_n > 0:
        df = df.head(top_n)
    
    # Color palettes
    # Color palettes
    color_palettes = {
        'modern_blues': ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c'],
        'emerald_tones': ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00'],
        'purple_gradient': ['#ffd1dc', '#c1e1c1', '#fef3bd', '#a3d2ca', '#ffb347'],
        'ocean_breeze': ['#ff6ec7', '#ffde59', '#3df4f4', '#00ff9f', '#ff3c38'],
        'warm_sunset': ['#FF6B6B', '#FF5252', '#F44336', '#E53935'],
        'professional': ['#d73027', '#4575b4', '#91bfdb', '#fdae61', '#a6d96a']
        }
    
    colors = color_palettes.get(palette, color_palettes['modern_blues'])
    
    # Prepare data for grouped bar chart
    grouped_data = df.groupby([x_col, grouped_col])[y_col].mean().unstack(fill_value=0)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Get unique groups and x categories
    groups = grouped_data.columns
    x_categories = grouped_data.index
    
    # Set width of bars and positions
    bar_width = 0.35
    x_pos = np.arange(len(x_categories))
    
    # Create bars for each group
    for i, group in enumerate(groups):
        values = grouped_data[group].values
        bars = ax.bar(x_pos + i * bar_width, values, bar_width, 
                     label=group, color=colors[i % len(colors)], 
                     alpha=0.8, edgecolor='white', linewidth=1)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if pd.notna(height) and height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.3f}' if height < 1 else f'{height:.0f}',
                       ha='center', va='bottom', fontsize=16, fontweight='bold')
    
    # Customize the chart
    ax.set_xlabel(x_col.replace('_', ' ').title(), labelpad=20)
    ax.set_ylabel(y_col.upper(), labelpad=20)
    ax.set_xticks(x_pos + bar_width / 2)
    ax.set_xticklabels(x_categories)
    ax.legend(title=grouped_col.replace('_', ' ').title(), loc='upper right')
    
    # Styling
    ax.set_facecolor('#FAFAFA')
    ax.grid(True, alpha=0.3, axis='y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return fig, ax

def create_enhanced_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, palette: str = 'modern_blues', title: str = None, top_n=None, wrap_labels=True, max_label_width=25) -> Tuple[plt.Figure, plt.Axes]:
    """Create enhanced bar chart with modern styling and label wrapping"""
    
    # 🔹 Take only first n records if requested
    if top_n is not None and top_n > 0:
        df = df.head(top_n)
    
    # Color palettes
    # color_palettes = {
    #     'modern_blues': ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c'],
    #     'emerald_tones': ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00'],
    #     'purple_gradient': ['#ffd1dc', '#c1e1c1', '#fef3bd', '#a3d2ca', '#ffb347'],
    #     'ocean_breeze': ['#ff6ec7', '#ffde59', '#3df4f4', '#00ff9f', '#ff3c38'],
    #     'warm_sunset': ['#FF6B6B', '#FF5252', '#F44336', '#E53935'],
    #     'professional': ['#d73027', '#4575b4', '#91bfdb', '#fdae61', '#a6d96a']
    # }
    color_palettes = {
    'modern_blues': ['#FF6B35', '#F7931E', '#FFD23F', '#06FFA5', '#118AB2'],
    'bold_spectrum': ['#E63946', '#F77F00', '#FCBF49', '#06D6A0', '#118AB2'],
    'professional': ['#D62828', '#F77F00', '#FCBF49', '#003049', '#669BBC'],
    'purple_gradient': ['#F72585', '#B5179E', '#7209B7', '#480CA8', "#E92424"],
    'warm_sunset': ['#FF8500', '#FF6D00', '#FF5722', '#4CAF50', '#2196F3'],
    'maximum_distinction': ['#FF1744', '#FF9100', '#FFEB3B', '#4CAF50', '#2196F3'],
    'emerald_tones': ['#8B4513', '#DAA520', '#228B22', '#4682B4', '#9932CC'],
    'neon_pop': ['#FF073A', '#FF8C00', '#32CD32', '#00CED1', '#9400D3'],
    'ocean_breeze': ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD'],
    'pastel_contrast': ['#FFB3BA', '#FFDFBA', '#FFFFBA', '#BAFFC9', '#BAE1FF']
    }
    
    # Get colors from palette
    colors = color_palettes.get(palette, color_palettes['modern_blues'])
    
    fig, ax = plt.subplots(figsize=(12, 7))  # Slightly larger figure
    
    # Wrap labels if requested
    if wrap_labels:
        wrapped_labels = [textwrap.fill(str(label), width=max_label_width) for label in df[x_col]]
    else:
        wrapped_labels = df[x_col]
    
    # Create bar chart
    bars = ax.bar(range(len(df)), df[y_col], color=colors[:len(df)], alpha=0.8, edgecolor='white', linewidth=1)
    
    # Set custom x-axis labels
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(wrapped_labels, rotation=45, ha='right', fontsize=20)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if pd.notna(height):
            ax.text(bar.get_x() + bar.get_width()/2., height, 
                   f'{height:.3f}' if height < 1 else f'{height:.0f}', 
                   ha='center', va='bottom', fontweight='bold')  # Reduced font size
    
    # Styling
    ax.set_facecolor('#FAFAFA')
    ax.grid(True, alpha=0.3, axis='y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Set axis labels
    ax.set_xlabel('Audience Segment', fontsize=20, fontweight='bold')
    ax.set_ylabel('CTR', fontsize=20, fontweight='bold')
    
    if title:
        ax.set_title(title, fontsize=20, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return fig, ax

def create_pie_chart(df: pd.DataFrame, x_col: str, y_col: str, 
                    palette: str = 'modern_blues', title: str = None) -> plt.Figure:
    """Create pie chart with multiple colors, ignoring zero values"""
    # Color palettes
    # color_palettes = {
    #     'modern_blues': ['#4A90E2', '#357ABD', '#2C5F96', '#1E4570', '#5B9BD5'],
    #     'emerald_tones': ['#50C878', '#45B868', '#3AA858', '#2F9848', '#66D98A'],
    #     'purple_gradient': ['#8B5FBF', '#7A4FB5', '#693FAB', '#582FA1', '#9C6FD1'],
    #     'ocean_breeze': ['#4FA8C5', '#459CB8', '#3B90AB', '#31849E', '#5BB2D7'],
    #     'warm_sunset': ['#FF6B6B', '#FF5252', '#F44336', '#E53935', '#FF7D7D'],
    #     'professional': ['#34495E', '#2C3E50', '#566573', '#5D6D7E', '#485F70']
    # }

    color_palettes = {
    'modern_blues': ['#FF6B35', '#F7931E', '#FFD23F', '#06FFA5', '#118AB2'],
    'bold_spectrum': ['#E63946', '#F77F00', '#FCBF49', '#06D6A0', '#118AB2'],
    'professional': ['#D62828', '#F77F00', '#FCBF49', '#003049', '#669BBC'],
    'purple_gradient': ['#F72585', '#B5179E', '#7209B7', '#480CA8', '#3A0CA3'],
    'warm_sunset': ['#FF8500', '#FF6D00', '#FF5722', '#4CAF50', '#2196F3'],
    'maximum_distinction': ['#FF1744', '#FF9100', '#FFEB3B', '#4CAF50', '#2196F3'],
    'emerald_tones': ['#8B4513', '#DAA520', '#228B22', '#4682B4', '#9932CC'],
    'neon_pop': ['#FF073A', '#FF8C00', '#32CD32', '#00CED1', '#9400D3'],
    'ocean_breeze': ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD'],
    'pastel_contrast': ['#FFB3BA', '#FFDFBA', '#FFFFBA', '#BAFFC9', '#BAE1FF']
    }

    colors = color_palettes.get(palette, color_palettes['modern_blues'])

    # 🔹 Filter out rows where y_col == 0
    df_filtered = df[df[y_col] > 0].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(8, 8))

    # Create pie chart only with non-zero values
    wedges, texts, autotexts = ax.pie(
        df_filtered[y_col], 
        labels=df_filtered[x_col], 
        autopct='%1.1f%%',
        colors=colors[:len(df_filtered)],  # trim colors to match categories
        startangle=90, 
        explode=[0.05] * len(df_filtered)
    )

    # Styling
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')

    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

    plt.tight_layout()
    return fig

def should_create_chart(df, x_column):
    """Helper function to check if chart should be created"""
    return (
        x_column in df.columns
        and len(df) > 0
        and df[x_column].nunique() > 1
    )

# @handle_exception()
def prepare_data_with_plots(platform_dataframes: Dict[str, Dict[str, pd.DataFrame]],metric) -> Dict[str, Any]:
    """Create charts dynamically from processed JSON data"""
    
    platform_data = {}
    
    # Set matplotlib parameters
    plt.rcParams.update({
        'axes.titlesize': 16,
        'font.size': 16,
        'axes.labelsize': 18,
        'xtick.labelsize': 18,
        'ytick.labelsize': 18,
        'figure.facecolor': 'white',
        'axes.facecolor': '#FAFAFA'
    })
    
    for platform_name, dataframes in platform_dataframes.items():
        
        platform_info = {
            'dataframes': [],
            'df_titles': [],
            'figures': [],
            'figure_titles': [],
            'x_columns': []
        }
        
        for df_name, df in dataframes.items():
            # print(f"platform_name : {platform_name} df : {df_name},")
                
            # Detect appropriate columns and chart type
            chart_config = detect_chart_columns(df,metric=metric)
            

            #columns
            x_col = chart_config.get('x_column')
            y_col = chart_config.get('y_column')
            grouped_col = chart_config.get('grouped_col')

            if not x_col or not y_col:
                logger.warning(f"platform-name : {platform_name} skipped dataframe {df_name} because of chart_config : {chart_config}, existing columns : {df.columns}")
                continue

            # titles
            if grouped_col:
                fig_title = f"{x_col.replace('_', ' ').title()} and {grouped_col.title()}-wise {y_col.upper()} plot"
                df_title = f"Performance by {x_col.replace('_', ' ').title()} and {grouped_col.replace('_', ' ').title()}"
            else:
                fig_title = f"{x_col.replace('_', ' ').title()}-wise {y_col.upper()} plot"
                df_title = f"Performance by {x_col.replace('_', ' ').title()}"

            fig = None

            if should_create_chart(df,x_col):
                # print(f"platform-name : {platform_name} skipped dataframe: {df_name} because create chart returned:false")            
            
                chart_type = determine_chart_type(df, x_col,chart_config=chart_config)
                

                
                # Choose palette based on platform and chart type
                palette_map = {
                    'facebook': ['modern_blues', 'purple_gradient', 'emerald_tones','ocean_breeze','warm_sunset'],
                    'instagram': ['warm_sunset','professional', 'modern_blues','emerald_tones'],
                    'snapchat': ['ocean_breeze', 'modern_blues', 'emerald_tones','ocean_breeze'],
                    'tiktok': ['purple_gradient', 'warm_sunset', 'professional', 'modern_blues'],
                    'google': ['emerald_tones', 'purple_gradient','warm_sunset','professional'],
                    'youtube': ['modern_blues', 'purple_gradient', 'emerald_tones','ocean_breeze','warm_sunset'],
                    'linkedin': ['warm_sunset','professional', 'modern_blues','emerald_tones']
                }
                
                palettes = palette_map.get(platform_name, ['modern_blues'])
                palette_idx = len(platform_info['figures']) % len(palettes)
                palette = palettes[palette_idx]
                
                # Create chart
                if chart_type == 'pie':
                    fig = create_pie_chart(df, x_col, y_col, palette=palette)
                elif chart_type == 'grouped_bar':
                    fig,ax= create_grouped_bar_chart(df,x_col=x_col,y_col=y_col,grouped_col=grouped_col,palette=palette,top_n=5)

                    ax.set_xlabel(x_col.replace('_', ' ').title(), labelpad=20)
                    ax.set_ylabel(y_col.upper(), labelpad=20)

                    if df[x_col].astype(str).str.len().max() > 10:
                        ax.tick_params(axis='x', rotation=45)
                        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

                else:  # bar chart
                    fig, ax = create_enhanced_bar_chart(df, x_col, y_col, palette=palette,top_n=5)

                    ax.set_xlabel(x_col.replace('_', ' ').title(), labelpad=20)
                    ax.set_ylabel(y_col.upper(), labelpad=20)
                    
                    # Handle x-axis rotation for long labels
                    if df[x_col].astype(str).str.len().max() > 10:
                        ax.tick_params(axis='x', rotation=45)
                        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
            # if platform_name == "google":
            #     # Special case: rename to google_ads
            #     print("Chart type:", chart_type)
            #     print("X column:", x_col, "Y column:", y_col)
            #     print("Unique X values:", df[x_col].unique())
            #     print("Figure created?", fig is not None)

            # Store chart information
            platform_info['dataframes'].append(df)
            platform_info['df_titles'].append(df_title)
            platform_info['figures'].append(fig)
            platform_info['x_columns'].append(x_col)
            platform_info['figure_titles'].append(fig_title)
        
        # Add the platform data in the main data
        if platform_info['dataframes']:
            platform_data[platform_name.title()] = platform_info
    
    return platform_data

