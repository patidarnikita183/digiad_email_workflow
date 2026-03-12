import time
import copy
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.general_constants import logger
from utils.general_helper import filter_all_platforms_data
# ================= 2nd Sept. 2025 =================

def calculate_cost(completion,model):
    """
    Calculates the cost of using a specific AI model based on token usage.
 
    This function computes the cost of both prompt and completion tokens
    according to the pricing structure of the selected model.
 
    Args:
        completion (object): An object containing token usage information.
            Expected to have the attributes:
            - `usage.prompt_tokens` (int): Number of tokens used in the prompt.
            - `usage.completion_tokens` (int): Number of tokens used in the completion.
        model (str): The name of the AI model used (e.g., "gpt-4o" or "gpt-4o-mini").
 
    Returns:
        float: The total cost in USD based on the token usage and model pricing.
    """
    PRICING = {
    "gpt-4o": {"prompt": 0.00250, "completion": 0.01000},
    "gpt-4o-mini": {"prompt": 0.000150, "completion": 0.000600}
    }
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    prompt_cost = (prompt_tokens / 1000) * PRICING[model]["prompt"]
    completion_cost = (completion_tokens / 1000) * PRICING[model]["completion"]
    total_cost = prompt_cost + completion_cost
 
    return total_cost

def generate_answer(model,prompt,CustomScript,temperature=0.1):
    """
    Generates an answer from an AI model using a custom response format and calculates execution time and cost.
 
    This function sends a prompt to the specified AI model, parses the response based on a custom script format,
    and returns the generated response along with the time taken for execution and the total cost of token usage.
 
    Args:
        model (str): The name of the AI model to be used (e.g., "gpt-4o", "gpt-4o-mini").
        prompt (str): The user-provided input prompt for the AI model.
        CustomScript (str): The custom response format to parse the AI response (e.g., "script", "json").
 
    Returns:
        dict: A dictionary containing the following keys:
            - `response` (str): The generated response parsed from the AI model according to the custom script format.
            - `time_taken` (float): The total time taken to generate the response in seconds.
            - `total_cost` (float): The cost of the AI model usage in USD based on token usage.
    """
    logger.info("Generate answer function called")
    start_time = time.time()
    client = OpenAI()
    completion = client.beta.chat.completions.parse(
        temperature=temperature,
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        response_format=CustomScript,
    )
 
    answer = completion.choices[0].message.parsed
    total_cost = calculate_cost(completion,model)
    end_time = time.time()
    total_time = end_time - start_time
 
    response = {
            "response": answer.dict(),
            "time_taken": total_time,
            "total_cost": total_cost
        }
    return response

def get_age_region_prompt(age_region):

    prompt_template = """
    You are a **Senior Ads Performance Analyst** with deep expertise in cross-platform ad targeting optimization.

    ### Input
    You will receive structured campaign performance data in JSON format, containing `age` segments and `regional_data` for multiple ad platforms (Facebook, Instagram, Google, YouTube, Snapchat, Twitter, TikTok, etc.).

    Age and Regional Data JSON input:
    {age_region}

    ### Task
    1. **Age Segment Analysis**
      - Detect underperforming age groups using clear signals such as:
        - Very low impressions
        - High spend with low clicks or conversions
        - Low engagement (high CPC, low CTR)
      - Recommend **age groups to exclude** from targeting.
      - The recommended target should always be a **single continuous age range** (e.g., 18-44, 25-54). Excluded age groups should fall **outside** this range.

    ### Key Rule
    - If a segment contains only a single value, **do not** recommend excluding, removing, or eliminating it. Example: 'Region – Madhya Pradesh' has only one location, so it must be retained.

    2. **Regional Data Analysis**
      - Identify poorly performing regions using metrics like low engagement, low conversions, and high cost inefficiency.
      - Recommend regions to **exclude** from targeting, following the single-value rule above.

    3. **Output Style Requirements**
      - **Action**: Direct, strong, and concise. Use commanding verbs like *exclude, eliminate, remove* and always reference the specific segment. Example: `"Exclude 45-54 age group to reduce wasted spend from low clicks."`
      - **Insight**: Provide a clear, metric-driven observation in 1–2 sentences, considering **all segments**, not just the excluded ones. Example: `"The 45-54 age group had the highest CPC and the lowest conversions across platforms."`
      - All recommendations must be **clear, data-backed, and business-oriented**, as if by a **Pro Data Analytics Consultant**.

    ---
    ### Output Format
    Return **only valid JSON** exactly in this structure.  
    - Do not add any narrative or extra explanation.  
    - Do not include currency symbols (e.g., $, Rs).

    ```json
    {{
      "age_exclude": 
        {{
          "value": ["<age_range>"],
          "action": "<clear_exclusion_recommendation>",
          "insight": "<data_revealed_about_age_group>"
        }}
      ,
      "regions_exclude": 
        {{
          "value": ["<list_of_region_value>"],
          "action": "<clear_exclusion_recommendation>",
          "insight": "<data_revealed_about_region>"
        }}
    }}
    """
    prompt=prompt_template.format(age_region=age_region)

    return prompt

def get_recommendation_exclude_prompt(platform,performance_data):
    
    if platform in ("google","youtube"):
        output_json="""
        {{
      "gender": 
        {{
          "value": ["<list_of_gender_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      "device": 
        {{
          "value": ["<list_of_device_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      "placements": 
        {{
          "value": ["<list_of_placements_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
        "audience": 
        {{
          "value": ["<list_of_audience_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }}
                
        }}
        """
    elif platform in ("facebook","instagram"):
        output_json="""
        {{
      "gender": 
        {{
          "value": ["<list_of_gender_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }}
      ,
      "placements": 
        {{
          "value": ["<list_of_placement_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }}
      ,
      "devices": 
        {{
          "value": ["<list_of_device_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }}
        }}
        """
    elif platform =="snapchat":
        output_json="""
        {{
      "gender": 
        {{
          "value": ["<list_of_gender_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      "devices":
        {{
          "value": ["<list_of_device_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      "lifestyle_category": 
        {{
          "value": ["<list_of_lifestyle_category_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      "countries":
        {{
          "value": ["<list_of_country_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      "os":
        {{
          "value": ["<list_os_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }}
        }}
        """
    elif platform =="twitter":
        output_json="""
        {{
      "gender": 
        {{
          "value": ["<list_of_gender_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      "devices":
        {{
          "value": ["<list_of_device_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      {{
      "languages": 
        {{
          "value": ["<list_of_languages_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      "platforms":
        {{
          "value": ["<list_of_platforms_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      "interests":
        {{
          "value": ["<list_of_interests_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }}
        }}
        """
    elif platform =="tiktok":
        output_json="""
        {{
      "gender": 
        {{
          "value": ["<list_of_gender_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      "languages":
        {{
          "value": ["<list_of_language_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      "interest": 
        {{
          "value": ["<list_of_interest_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }},
      "platforms":
        {{
          "value": ["<list_of_platform_value>"],
          "action": "<concise_metric_based_action>",
          "insight":"<based_on_overall_data>"
        }}
        }}
        """
    prompt_template="""
    You are a **Senior Ads Performance Analyst** specializing in detecting and eliminating underperforming campaign segments.

    ---
    ### Campaign Performance Data
    {performance_data}

    ---
    ### Goal
    - Analyze structured campaign data across **gender, device, placement and etc.**.  
    - Identify only **clearly underperforming segments** by combining multiple metrics.  
    - Recommend segments to **exclude, remove, or eliminate** to stop budget leakage.  
    - Provide both:
      - **Action** → Direct, concise, and forceful. Use imperative verbs like *Exclude, Remove, Eliminate*. Always specify the segment name (e.g., *"Exclude Male segment to reduce wasted spend"*).  
        - **Important:** If a segment has only a single value (e.g., 'Region – Madhya Pradesh'), do **not** suggest exclude/remove/eliminate.  
      - **Insight** → Short (1–2 sentences) summary of what the data shows, highlighting performance trends across all segments without prescribing action.

    Write like a professional Digital Marketing Data Analytics Consultant. Be decisive, concise, and actionable.

    ---
    ### Evaluation Criteria
    Flag a segment only if it **clearly underperforms compared to dataset averages/medians** across multiple metrics:  

    - **High Spend + Low Results** → Indicates wasted budget.  
    - **Low CTR vs. Average** → Signals weak engagement.  
    - **High CPC / High Cost per Result + Low Conversions** → Inefficient spend with poor ROI.  
    - **No Meaningful Engagement** → Impressions exist, but conversions/clicks are negligible.  

    ---
    ### Rules & Safeguards
    - Do **not** exclude for high CPC if CTR/conversions are strong.  
    - Do **not** infer insights for missing data.  
    - Segments with very low impressions (<500) → label as `"Needs more data"`.  
    - Always combine **at least two weak signals** before flagging.  
    - **Actions must use imperative language** (Exclude, Eliminate, Remove).  
    - **Insights must explain performance trends only**, never prescribe actions.  
    - If a segment has only one value, do **not** suggest exclude/remove/eliminate.

    ---
    ### Output Format
    Return **only valid JSON** using the schema below.  
    - Do not include any explanation, text, or narrative outside JSON.  
    - Do not include currency symbols (e.g., $, Rs).  
    {output_json}
    """
    prompt=prompt_template.format(
       performance_data=performance_data,output_json=output_json
    )
    return prompt

def get_insight_action_prompt(insight_action_dict):
    
    prompt_template="""You are a **Top-Tier Data Analyst** specializing in **cross-platform campaign performance optimization**.  
    You will be given raw campaign {insight_action_dict} data from multiple platforms (Google, Meta, Twitter, Snapchat, TikTok, etc.).  

    ### Task  
    1. Extract the **core insights** and write them as **short, crisp, user-friendly bullet points**.  
      - Maximum one sentence per insight.  
      - Focus on the *most important takeaways*.  
      - Insights: Clearly explain what the campaign performance data reveals, without suggesting actions.
      - You can use the <b> tag to display the important word only not full sentence.

    2. Extract the **recommended actions** and write them as **direct, actionable bullet points**. 
      - Avoid jargon, keep it clear and actionable.   
      - Use imperative tone, make only needed changes.  
      - Keep each action **short and precise**.  
      - You can use the <b> tag to display the important word only not full sentence.

    ### Output Format  
    ```json
    {{
      "insights": [ <list of five insights>  ],
      "actions": [ <list of five actions>  ]
    }}
    """

    prompt=prompt_template.format(insight_action_dict=insight_action_dict)

    return prompt

# =================== Pydantic =======================

from typing import List
from pydantic import BaseModel

class Segment(BaseModel):
    value:List[str]
    action:str
    insight:str

class CampaignCommonRecommendations(BaseModel):
    age_exclude: Segment
    regions_exclude:Segment

#Google
class ExcludeTargetingGoogle(BaseModel):
    gender_exclude: Segment
    device_exclude:Segment
    placements_exclude:Segment
    audience_exclude:Segment
#Meta
class ExcludeTargetingMeta(BaseModel):
    gender_exclude: Segment
    devices_exclude:Segment
    placements_exclude:Segment
#Snapchat
class ExcludeTargetingSnapchat(BaseModel):
    gender_exclude: Segment
    devices_exclude:Segment
    lifestyle_category_exclude:Segment
    countries_exclude:Segment
    os_exclude:Segment
#Twitter
class ExcludeTargetingTwitter(BaseModel):
    gender_exclude: Segment
    interests_exclude:Segment
    languages_exclude:Segment
    platforms_exclude:Segment
    devices_exclude:Segment
#TikTok
class ExcludeTargetingTikTok(BaseModel):
    gender_exclude: Segment
    languages_exclude:Segment
    interest_category:Segment
    platforms_exclude:Segment

#Insights and Actions
class InsightsAndActions(BaseModel):
    insights_html: List[str]
    actions_html:List[str]

OUTPUT_PARSER_PLATFORMS={
                          "facebook":ExcludeTargetingMeta,
                          "instagram":ExcludeTargetingMeta,
                          "google":ExcludeTargetingGoogle,
                          "youtube":ExcludeTargetingGoogle,
                          "snapchat":ExcludeTargetingSnapchat,
                          "twitter":ExcludeTargetingTwitter,
                          "tiktok":ExcludeTargetingTikTok
                      }

# ====================== End Pydantic ========================


# ====================== Helper Functions ==================

def extract_campaign_common_values(data):
    age_region={}
    for platform in data:
        temp={}
        # print("PLAATFORM ",platform)
        temp["age"]=data[platform].get("age",'')
        if temp["age"]:
            data[platform].pop("age")  # delete the age of individual platform
        temp["regional_data"]=data[platform].get("regional_data",'')
        if temp["regional_data"]:
            data[platform].pop("regional_data") # delete the region of individual platform
        age_region[platform]=temp
    return age_region,data

def process_platform(platform, data, model, output_parsar_platforms):
            prompt = get_recommendation_exclude_prompt(platform, data[platform])
            # print(f"\n{platform}_ Level Prompt @@@@@@@@@@@@@@@#####",prompt)
            response = generate_answer(model, prompt, output_parsar_platforms[platform])
            return platform, response["response"],response["total_cost"],response["time_taken"]

def extract_insights_and_actions(data: dict) -> dict:
    insights, actions = [], []

    def traverse(obj):
        if isinstance(obj, dict):
            if "insight" in obj and "action" in obj:
                insights.append(obj["insight"])
                actions.append(obj["action"])
            for v in obj.values():
                traverse(v)
        elif isinstance(obj, list):
            for item in obj:
                traverse(item)

    traverse(data)
    return {"Insights": insights, "Actions": actions}

def check_data(data):
    for platform in list(data.keys()):
        value = data[platform]
        if isinstance(value, dict):
            # Check if all values in the dict are empty lists
            if all(isinstance(v, list) and not v for v in value.values()):
                data.pop(platform)
        elif not value:
            # Still remove if value is None or falsy and not a dict
            data.pop(platform)
    return data

# ====================== End Helper Functions ==================

# ====================== Main Function ===================== 

# def generate_campaign_audience_insights_actions(platforms_data):
  
#   pdf_insights={
#   "campaign_level": {
#     "age_exclude": {
#       "value": ["35-64"],
#       "action": "Exclude 35-64 age group to reduce wasted spend from low clicks and high CPC.",
#       "insight": "The 35-64 age group had zero clicks and the highest CPC across platforms, indicating poor engagement and inefficiency."
#     },
#     "regions_exclude": {
#       "value": ["Haryana"],
#       "action": "Exclude Haryana region to improve cost efficiency and engagement.",
#       "insight": "Haryana had the highest CPC and the lowest CTR, \nresulting in inefficient spend and low engagement."
#     }
#   },
#   "google": {
#     "gender_exclude": {
#       "value": ["Female"],
#       "action": "Exclude Female segment to reduce wasted spend",
#       "insight": "The Female segment shows high spend with low results, indicating inefficient budget allocation."
#     },
#     "device_exclude": {
#       "value": ["Tablet"],
#       "action": "Remove Tablet segment to improve ROI",
#       "insight": "Tablet devices have high CPC and low conversions, leading to poor return on investment."
#     },
#     "placements_exclude": {
#       "value": ["Sidebar Ads"],
#       "action": "Eliminate Sidebar Ads to enhance engagement",
#       "insight": "Sidebar Ads exhibit low CTR and negligible conversions, suggesting weak audience engagement."
#     }
#   },
#   "facebook": {
#     "gender_exclude": {
#       "value": ["female"],
#       "action": "Exclude Female segment to reduce wasted spend",
#       "insight": "The female segment shows high spend with negligible results, indicating inefficient budget allocation."
#     },
#     "devices_exclude": {
#       "value": ["desktop"],
#       "action": "Exclude Desktop segment to prevent budget leakage",
#       "insight": "The desktop segment has no meaningful engagement, with impressions but no clicks or conversions."
#     },
#     "placements_exclude": {
#       "value": [
#         "facebook_profile_feed",
#         "facebook_reels",
#         "facebook_stories",
#         "instream_video",
#         "marketplace",
#         "video_feeds"
#       ],
#       "action": "Exclude underperforming placements to optimize spend",
#       "insight": "Multiple placements show high impressions with no clicks, indicating poor \nengagement and wasted budget."
#     }
#   },
#   "twitter": {
#     "gender_exclude": {
#       "value": ["Unknown"],
#       "action": "Exclude Unknown gender segment to reduce wasted spend",
#       "insight": "The Unknown gender segment shows no engagement with zero clicks and conversions, indicating inefficiency."
#     },
#     "interests_exclude": {
#       "value": [
#         "Fine dining",
#         "Board gaming",
#         "Men's pants",
#         "Motorcycles",
#         "Spa and medical spa",
#         "Health, mind, and body",
#         "Newlyweds",
#         "Reggae",
#         "Green solutions",
#         "Needlework",
#         "Luxury travel",
#         "Language learning",
#         "Insurance",
#         "Screenwriting",
#         "Australia and New Zealand",
#         "Greece",
#         "Design",
#         "Skin care",
#         "Men's formal wear",
#         "Sporting goods",
#         "Honeymoons and getaways",
#         "Figure skating",
#         "Men's accessories",
#         "Men's beachwear",
#         "Men's outerwear",
#         "Men's jeans",
#         "Men's tops",
#         "Men's shoes",
#         "Women's bags",
#         "Women's intimates and hosiery",
#         "Women's pants",
#         "Women's shoes",
#         "Women's beachwear",
#         "Women's outerwear",
#         "Women's tops"
#       ],
#       "action": "Exclude these interest segments to eliminate budget leakage",
#       "insight": "These interest segments have zero engagement with no clicks or conversions, indicating poor performance."
#     },
#     "languages_exclude": {
#       "value": [
#         "Turkish",
#         "French",
#         "Polish",
#         "Kannada",
#         "Danish",
#         "Thai",
#         "Bengali",
#         "Gujarati",
#         "Hebrew",
#         "Russian",
#         "Italian",
#         "Czech",
#         "Hungarian",
#         "Persian",
#         "Romanian",
#         "Vietnamese",
#         "Dutch",
#         "Urdu",
#         "Ukrainian",
#         "Latvian",
#         "Greek",
#         "Finnish",
#         "Norwegian",
#         "German",
#         "Spanish",
#         "Basque",
#         "Arabic",
#         "Catalan",
#         "Japanese",
#         "Serbian",
#         "Bulgarian",
#         "Malay",
#         "Swedish",
#         "Korean",
#         "Chinese"
#       ],
#       "action": "Exclude these language segments to optimize targeting",
#       "insight": "These language segments show no engagement with zero clicks and conversions, indicating inefficiency."
#     },
#     "platforms_exclude": {
#       "value": ["iOS devices"],
#       "action": "Exclude iOS devices to reduce wasted spend",
#       "insight": "iOS devices show low engagement with a CTR significantly below average, indicating inefficiency."
#     },
#     "devices_exclude": {
#       "value": ["Desktop and laptop computers"],
#       "action": "Exclude Desktop and laptop computers to optimize budget",
#       "insight": "This segment shows low engagement with a CTR below average, indicating poor performance."
#     }
#   },
#    "google": {
#     "gender_exclude": {
#       "value": ["Undetermined"],
#       "action": "Exclude Undetermined gender segment to reduce wasted spend",
#       "insight": "The Undetermined gender segment has a high cost with no conversions, indicating ineffective budget allocation."
#     },
#     "device_exclude": {
#       "value": ["DESKTOP"],
#       "action": "Exclude Desktop device segment to eliminate inefficient spend",
#       "insight": "The Desktop segment shows negligible clicks and conversions, resulting in wasted budget with no meaningful engagement."
#     },
#     "placements_exclude": {
#       "value": ["kikibom.com", "newspointapp.com", "twinsfun.com", "tempcut.com", "udayavani.com"],
#       "action": "Remove underperforming placements to stop budget leakage",
#       "insight": "These placements have high impressions but no conversions, indicating poor performance and ineffective ad spend."
#     },
#     "audience_exclude": {
#       "value": [
#         "Commercial Properties",
#         "Business & Productivity Software",
#         "Technology Education",
#         "Travel",
#         "Advertising & Marketing Services",
#         "Business Services",
#         "Business Professionals",
#         "Business & Industrial Products"
#       ],
#       "action": "Eliminate underperforming audience segments to optimize budget",
#       "insight": "These audience segments have low conversions despite spending, indicating they are not yielding a positive return on investment."
#     }
#   },
#   "html_insights_and_actions": {
#     "insights_html": [
#       "<b>35-64 age group</b> shows zero clicks and high CPC, indicating poor engagement.",
#       "<b>Haryana</b> has the highest CPC and lowest CTR, leading to inefficient spending.",
#       "<b>Female segment</b> has high spend with low results, showing inefficient budget allocation.",
#       "<b>Tablet devices</b> have high CPC and low conversions, resulting in poor ROI.",
#       "<b>Sidebar Ads</b> exhibit low CTR and negligible conversions, suggesting weak engagement."
#     ],
#     "actions_html": [
#       "<b>Exclude</b> the 35-64 age group to reduce wasted spend.",
#       "<b>Exclude</b> Haryana region to improve cost efficiency.",
#       "<b>Remove</b> the Female segment to optimize budget allocation.",
#       "<b>Remove</b> Tablet segment to enhance ROI.",
#       "<b>Eliminate</b> Sidebar Ads to boost audience engagement."
#     ]
#   }
# }

  
  
#   mail_insights_action={
#     "insights_html": [
#       "<b>35-64 age group</b> shows no engagement with high costs.",
#       "<b>Haryana</b> region is cost-inefficient with low engagement.",
#       "<b>Unknown gender</b> segment has no interaction.",
#       "<b>Desktop and mobile web</b> segments lack engagement.",
#       "<b>Underperforming placements</b> lead to inefficient spending."
#     ],
#     "actions_html": [
#       "<b>Exclude</b> the 35-64 age group to cut costs.",
#       "<b>Remove</b> Haryana from the target regions.",
#       "<b>Eliminate</b> the unknown gender segment.",
#       "<b>Exclude</b> desktop and mobile web segments.",
#       "<b>Remove</b> underperforming placements."
#     ]
#   }
#   return pdf_insights, mail_insights_action,0,0

def generate_campaign_audience_insights_actions(platforms_data):
    try:
        data=copy.deepcopy(platforms_data)
        # print("===================Initial Data :",data.keys())
        data=filter_all_platforms_data(data)
        data=check_data(data)
        # print("Checked Data :",list(data.keys()))
        if not data:
            raise ValueError("Insights-module :No valid data found in any platform.")
        age_region, data = extract_campaign_common_values(data)

        model = "gpt-4o-mini"
        temperature=0.1
        total_cost=0
        time_taken=0

        # Preparing the prompt for identifying the worst-performing age and region segments
        prompt_age_region = get_age_region_prompt(age_region)
        # print("PROMPT AGE REGION ",prompt_age_region)
        response = generate_answer(
            model=model,
            prompt=prompt_age_region,
            CustomScript=CampaignCommonRecommendations,
            temperature=temperature
        )

        output_parsar_platforms = OUTPUT_PARSER_PLATFORMS
        final_response = {}
        final_response["pdf_insights_actions"]={}
        final_response["pdf_insights_actions"]["campaign_level"] = response["response"]
        total_cost+=response["total_cost"]
        time_taken+=response["total_cost"]


        # Preparing the prompt for each platform and calling the LLM model in parallel with threading
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(process_platform, platform, data, model, output_parsar_platforms): platform
                for platform in data
            }
            for future in as_completed(futures):
                platform, result,cost,time = future.result()
                final_response["pdf_insights_actions"][platform] = result
                total_cost+=cost
                time_taken+=time

        final_response["mail_insights_action"]=extract_insights_and_actions(final_response)

        # Preparing the prompt and calling the LLM Model for Refine Insights and Actions  
        prompt_insight_n_action=get_insight_action_prompt(final_response["mail_insights_action"])
        # print("INSIGHTS AND ACTION PROMPT :#####",prompt_insight_n_action)
        response_insight_actions=generate_answer(model=model,prompt=prompt_insight_n_action,CustomScript=InsightsAndActions,temperature=0.15)

        final_response["mail_insights_action"]=response_insight_actions["response"]
        total_cost+=response_insight_actions["total_cost"]
        time_taken+=response_insight_actions["time_taken"]

        final_response["pdf_insights_actions"]["html_insights_and_actions"]=response_insight_actions["response"]

        final_response["total_cost"]=total_cost
        final_response["time_taken"]=time_taken

    except Exception as e:
      raise
      return {"error": str(e)}

    return final_response["pdf_insights_actions"], final_response["mail_insights_action"], final_response["total_cost"], final_response["time_taken"]


