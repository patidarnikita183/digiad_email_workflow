import uuid
from datetime import timezone
import copy
import requests
from flask import Flask, jsonify, render_template_string, request

from mail.config import Config
from mail.email_service import DomainEmailService
from mail.mail_helpers import render_hbs_template
from utils.email_template import html_content,paused_campaign_mail_html_template
from utils.general_constants import BASE_URL_EMAIL, LOGO_PATH, log_errors_and_respond,logger
from utils.general_helper import (prepare_data_for_mail, get_platform_campaign_performance_metrics, get_platform_campaign_audience_metrics, validate_path,remove_files_if_exists, check_any_platform_active,prepare_data_for_paused_campaign)
from utils.google_analytics import *
from utils.meta_analytics import *
from utils.snapchat_analytics import *
from utils.tiktok_analytics import *
from utils.twitter_analytics import *
from collections import OrderedDict
from pdf_generation.main import generate_multi_platform_campaign_report
from helpers.helper import *
app = Flask(__name__)
app.secret_key = f"{uuid.uuid4()}"
app.config['JSON_SORT_KEYS'] = False

email_service = DomainEmailService()
config = Config()
import datetime


@app.route("/health")
@log_errors_and_respond(status_code=500)
def health():
    return jsonify({"response": "server is running"})


########################## Mail-endpoints ###########################
@app.route("/send-email", methods=["POST"])
@log_errors_and_respond(status_code=500)
def send_email():
    try :
        print("Received request to /send-email endpoint")
        # Get request data
        data = request.get_json()

        # Basic required fields
        required_fields = ["from", "to", "subject"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify(
                        {"status": "error", "message": f"Missing required field: {field}"}
                    ),
                    400,
                )

        # Map 'from' parameter to actual email addresses
        from_type = data["from"].lower()
        if from_type == "sales":
            from_email = config.SALES_EMAIL
        elif from_type == "support":
            from_email = config.SUPPORT_EMAIL
        else:
            from_email = data["from"]  # direct email

        to_email = data["to"]
        subject = data["subject"]
        
        template_name = data.get('template')
        template_name = template_name.lower() if template_name else None
        template_name =  os.path.splitext(os.path.basename(template_name or ""))[0].lower()

        # Determine email_type
        # Priority: 1. data['email_type'], 2. derived from template name
        email_type = data.get("email_type",None)
        print(f"email_type from request: {email_type}, template_name: {template_name}")
        if not email_type and template_name:
            print("Determining email_type based on template_name...")
            if template_name == TEMPLATE_ACTIVATION:
                email_type = 'activation'
            elif template_name == TEMPLATE_WELCOME:
                email_type = 'welcome'
            # Add other mappings as needed
            elif 'activation_reminder' in template_name.lower():
                email_type = 'activation_reminder'
            elif 'activation' in template_name.lower():
                email_type = 'activation'
            elif 'welcome' in template_name.lower():
                email_type = 'welcome'
        # Handle email content: template OR html
        print(f"Determined email_type: {email_type}, template_name: {template_name}")
        if "template" in data:
            html = render_hbs_template(data["template"], data.get("context", {}))
        elif "html" in data:
            html = data["html"]
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": 'Either "template" or "html" must be provided.',
                    }
                ),
                400,
            )

        # Send email
        response = email_service.send_email_from_user(
            from_email=from_email, to_email=to_email, subject=subject, html_content=html,
        attachments=data.get("attachments")
        )
        print(f"Email service response: status_code={response.status_code}, text={response.text}")
        # Handle response
        if response.status_code == 202:
            if email_type:
                try:
                    print("Tracking email event for user...")
                    conn = get_db_connection()
                    user = get_user_by_email(conn, to_email)
                    print(f"User fetched from DB: {user}")
                    conn.close()

                    if user and user.get("user_id"):
                        print("User found, tracking email event...")
                        track_email_event(
                            user_id=user["user_id"],
                            email_type=email_type,
                            template_name=template_name,
                            metadata={"subject": subject, "template": template_name},
                            email_id=to_email
                        )
                        # Append to worker test log for validation
                        append_worker_log({
                            "sent_at":      datetime.datetime.utcnow().isoformat(),
                            "email":        to_email,
                            "user_id":      str(user["user_id"]),
                            "email_type":   email_type,
                            "template":     template_name,
                        })
                except Exception as track_err:
                    print(f"Error tracking email: {track_err}")

         
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Email sent successfully",
                        "from": from_email,
                        "to": to_email,
                        "timestamp": datetime.datetime.now().isoformat(),
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Failed to send email",
                        "details": response.text,
                        "status_code": response.status_code,
                    }
                ),
                500,
            )
    except Exception as e:
        logger.error(f"Error in send-email endpoint: {str(e)}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "An unexpected error occurred while sending email.",
                    "details": str(e),
                }
            ),
            500,
        )

########################### Main API Endpoints ############################
@app.route("/get_hourly_campaign_report", methods=["POST"])
@log_errors_and_respond(status_code=500)
def get_campaign_report():
    data = request.get_json()
    print("data",data)
    logger.info(f"Request received for hourly campaign- performance, Request data: {data}")
    customer_name = data.get("customer_name")
    campaign_name = data.get("campaign_name")
    to_mail = data.get("to_mail")
    from_mail = data.get("from_mail")
    platforms = data.get("platforms")

    google_credentials = platforms.get("google", {})
    facebook_credentials = platforms.get("facebook", {})
    snapchat_credentials = platforms.get("snapchat", {})
    twitter_credentials = platforms.get("twitter", {})
    tiktok_credentials = platforms.get("tiktok", {})
    youtube_credentials = platforms.get("youtube", {})
    instagram_credentials = platforms.get("instagram", {})

    all_platform_credentials = [
        google_credentials,
        facebook_credentials,
        snapchat_credentials,
        twitter_credentials,
        tiktok_credentials,
        youtube_credentials,
        instagram_credentials
    ]

    is_any_active = check_any_platform_active(all_platform_credentials)
    
    utc_now = datetime.datetime.now(timezone.utc)      # Format like "21-Aug-2025 09:00 AM UTC"
    current_date = utc_now.strftime("%d-%b-%Y %I:%M %p UTC")

    if is_any_active:        
        platforms_data,valid_platforms = get_platform_campaign_performance_metrics(google_credentials,facebook_credentials,snapchat_credentials,twitter_credentials,tiktok_credentials,youtube_credentials,instagram_credentials)
        
        logger.info(f"campaign performace data fetched. valid platforms : {valid_platforms}")
        # Current UTC time
        prepared_data = prepare_data_for_mail(
            customer_name, campaign_name, current_date, platforms_data,platforms_config=platforms
        )

        logger.info(f"data prepared for mail")

        html_template = render_template_string(
            html_content, valid_platforms=valid_platforms, **prepared_data
        )
    else:
        # prepared_data=prepare_data_for_paused_campaign(customer_name, campaign_name,current_date)
        # html_template=render_template_string(
        #     paused_campaign_mail_html_template, **prepared_data
        # )
        response=send_paused_status(data=data)
        return response

    response = email_service.send_email_from_user(
        from_email=from_mail,
        to_email=to_mail,
        subject=f"digiAd Campaign Update | {campaign_name} - {current_date}",
        html_content=html_template,
    )

    # Check response
    if response.status_code == 202:
        logger.info(f"Email sent successfully to {to_mail}, status_code: {response.status_code}")
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Email sent successfully",
                    "from": from_mail,
                    "to": to_mail,
                    "timestamp": datetime.datetime.now().isoformat(),
                }
            ),
            200,
        )
    else:
        logger.error(f"Failed to send email to {to_mail}, status_code: {response.status_code}, details: {response.text}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to send email",
                    "details": response.text,
                    "status_code": response.status_code,
                }
            ),
            500,
        )
            


@app.route("/send_paused_status", methods=["POST"])
def send_paused_status(data=None):
    if data is None:
        data = request.get_json()
    customer_name = data.get("customer_name")
    campaign_name = data.get("campaign_name")
    to_mail = data.get("to_mail")
    from_mail = data.get("from_mail")
    # platforms = data.get("platforms")
    utc_now = datetime.datetime.now(timezone.utc)      # Format like "21-Aug-2025 09:00 AM UTC"
    current_date = utc_now.strftime("%d-%b-%Y %I:%M %p UTC")
    data=prepare_data_for_paused_campaign(customer_name, campaign_name,current_date)
    html_template=render_template_string(
        paused_campaign_mail_html_template, **data
    )
    response = email_service.send_email_from_user(
        from_email=from_mail,
        to_email=to_mail,
        subject=f"digiAd Campaign Update | {campaign_name} - {current_date}",
        html_content=html_template,
    )

    # Check response
    if response.status_code == 202:
        logger.info(f"Email sent successfully to {to_mail}, status_code: {response.status_code}")
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Email sent successfully",
                    "from": from_mail,
                    "to": to_mail,
                    "timestamp": datetime.datetime.now().isoformat(),
                }
            ),
            200,
        )
    else:
        logger.error(f"Failed to send email to {to_mail}, status_code: {response.status_code}, details: {response.text}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to send email",
                    "details": response.text,
                    "status_code": response.status_code,
                }
            ),
            500,
        )


########################### Main API Endpoints ############################
@app.route("/get_daily_audience_campaign_report", methods=["POST"])
@log_errors_and_respond(status_code=500)
def get_daily_audience_campaign_report():
    data = request.get_json()
    customer_name = data.get("customer_name",'customer')
    campaign_name = data.get("campaign_name")
    to_mail = data.get("to_mail")
    from_mail = data.get("from_mail")
    platforms = data.get("platforms")
    start_date = data.get("start_date") #'2024-03-01'
    brand_name = data.get("brand_name","Your Brand")
    campaign_objective = data.get("campaign_objective","Campaign Objective")

    google_credentials = platforms.get("google", {})
    facebook_credentials = platforms.get("facebook", {})
    snapchat_credentials = platforms.get("snapchat", {})
    twitter_credentials = platforms.get("twitter", {})
    tiktok_credentials = platforms.get("tiktok", {})
    youtube_credentials = platforms.get("youtube", {})
    instagram_credentials = platforms.get("instagram", {})
    logger.info(f"Request received for daily audience campaign report, Request data: {data}")
    platforms_data,valid_platforms = get_platform_campaign_performance_metrics(google_credentials,facebook_credentials,snapchat_credentials,twitter_credentials,tiktok_credentials,youtube_credentials,instagram_credentials)
    logger.info(f"campaign performace data fetched. valid platforms : {valid_platforms}")
    # print("platforms_data",platforms_data)
    # print("valid_platforms",valid_platforms)
    logger.info(f"Fetching audience data for platforms: {valid_platforms}, it takes time loger than usual, max: 5-8 mins")
    platforms_audience_data = get_platform_campaign_audience_metrics(google_credentials,facebook_credentials,snapchat_credentials,twitter_credentials,tiktok_credentials,youtube_credentials,instagram_credentials)
    logger.info(f"Audience data fetched for platforms: {valid_platforms}")
    # print(f"###########platforms_audience_data : {platforms_audience_data['facebook'].keys()}")
    # platforms_audience_data = None
    # Current UTC time
    utc_now = datetime.datetime.now(timezone.utc)      # Format like "21-Aug-2025 09:00 AM UTC"
    current_date = utc_now.strftime("%d-%b-%Y %I:%M %p UTC")
    # Campaign information
    campaign_info = {
        'campaign_name': campaign_name,
        'brand_name': brand_name,
        'customer_name': customer_name,
        'objective': campaign_objective,
        'logo_path': LOGO_PATH,
        'platforms': valid_platforms,
        'start_date': start_date,
        'end_date': current_date
    }
    # print("campaign_info",campaign_info)

    from utils.campaign_audience_insights import generate_campaign_audience_insights_actions
    # print("\n\n\nDATA for audience insights ##########",platforms_audience_data)
    # filtered_data = filter_all_platforms_data(platforms_audience_data)
    # print(f"filtered-data : {filtered_data}")
    logger.info(f"Generating insights and actions for platforms: {valid_platforms}, it takes time loger than usual, max: 2-3 mins")
    pdf_insights_actions , mail_insights_action, total_cost, time_taken = generate_campaign_audience_insights_actions(platforms_audience_data)
    logger.info(f"Insights and actions generated, cost: {total_cost}, time_taken: {time_taken} seconds")
    # print(f"pdf insights : {pdf_insights_actions}")
    # print(f"mail insights : {mail_insights_action}")
    # print(f"After insights generation")
    # print(platforms_audience_data['facebook'])
    # return ("ok",200)
    # print("================pdf_insights_actions",pdf_insights_actions)
    # print("total_cost",total_cost)
    # print("time_taken",time_taken)
    # print("=====================mail_insights_action",mail_insights_action)
    # print("mail_insights_action",mail_insights_action)

    pdf_response = generate_multi_platform_campaign_report(platforms_audience_data,pdf_insights_actions,campaign_info)

    filepath = validate_path(pdf_response)

    if filepath is None:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to generate PDF report",
                    "detailes": pdf_response
                }
            ),
            500,
        )


    data = prepare_data_for_mail(
        customer_name, campaign_name, current_date, platforms_data
    )


    data['insights_html'] = "".join([f"<li>{item}</li>" for item in mail_insights_action['insights_html']])
    data['actions_html'] = "".join([f"<li>{item}</li>" for item in mail_insights_action['actions_html']])
    data['reporting_period'] = f"{start_date} to {current_date}"

    from utils.audience_email_template import html_content_audience
    html_template = render_template_string(
        html_content_audience, valid_platforms=valid_platforms, **data
    )

    logger.info("=================================sending mail=================================")
    # print("filepath",filepath)
    response = email_service.send_email_from_user(
        from_email=from_mail,
        to_email=to_mail,
        subject=f"Daily Campaign Insights & Recommendations – | {campaign_name} - {data['reporting_period']}",
        html_content=html_template,
        attachments = filepath
    )

    # Check response
    if response.status_code == 202:
        logger.info(f"Email sent successfully to {to_mail}, status_code: {response.status_code}, file_name : {filepath}")
        remove_files_if_exists(filepath)  # Delete the file after sending the email
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Email sent successfully",
                    "from": from_mail,
                    "to": to_mail,
                    "timestamp": datetime.datetime.now().isoformat(),
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to send email",
                    "details": response.text,
                    "status_code": response.status_code,
                }
            ),
            500,
        )


########################### Google API Endpoints ###########################
@app.route("/get_google_campaign_data", methods=["POST"])
@log_errors_and_respond(status_code=500)
def get_google_campaign_data():

    data = request.get_json()
    customer_id = data.get("customer_id")
    campaign_id = data.get("campaign_id")
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    config = {
        "developer_token": data.get("developer_token"),
        "client_id": data.get("client_id"),
        "client_secret": data.get("client_secret"),
        "refresh_token": data.get("refresh_token"),
        "use_proto_plus": True,
    }
    if not customer_id and not campaign_id:
        logger.error("Google : customer_id and campaign_id are required")

        return jsonify({"error": "customer_id and campaign_id are required"}), 400

    google_ads_client = get_or_create_google_ads_client(config)
    if not google_ads_client:
        logger.error("Google : Failed to initialize Google Ads client")
        return jsonify({"error": "Failed to initialize Google Ads client"}), 500
    # Placeholder for campaign data processing
    result = process_campaign_data(
        google_ads_client, customer_id, campaign_id, start_date, end_date
    )
    return jsonify({"response": result}), 200


@app.route("/get_google_deep_insight", methods=["POST"])
@log_errors_and_respond(status_code=500,platform="google")
def get_google_deep_insight():
    data = request.get_json()
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
    "device": [],
    "placement": [],
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
        return jsonify(audience_data), 400


    google_ads_audiece_client = get_or_create_google_ads_client(config)
    # print("google_ads_audiece_client",google_ads_audiece_client)
    if not google_ads_audiece_client:
        logger.error("Google : Failed to initialize Google Ads client")
        return jsonify(audience_data), 500
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

    audience_data.update({"age": age_data,"gender":gender_data,"time":time_data,"device":device_data,"audience":interest_data})

    if campaign_type in ["display", "demand_gen", "performance_max"]:
        logger.info(f"Google audience placement data is being fetched")
        placement_data = process_google_placements_url(
            google_ads_audiece_client, customer_id, campaign_id, start_date, end_date)
        
        audience_data.update({"placement":placement_data})
        return jsonify(audience_data)

    elif campaign_type == "search":
        logger.info(f"Google audience keyword and search-terms data is being fetched")
        keyword_data = process_google_keyword_performance(
            google_ads_audiece_client, customer_id, campaign_id, start_date, end_date)
        search_term_data = process_google_search_term_performance(
            google_ads_audiece_client, customer_id, campaign_id, start_date, end_date)
        

        audience_data.update({"keywords":keyword_data,"search_terms":search_term_data})
        return jsonify(audience_data)

    # Default fallback (though this shouldn't be reached due to campaign_type validation)
    return jsonify({
        "age": age_data,
        "gender": gender_data,
        "time": time_data,
        "device": device_data,
    })

##############################################################################
########################### Facebook API Endpoints ###########################
##############################################################################
@app.route("/get_meta_campaign_data", methods=["POST"])
@log_errors_and_respond(status_code=500)
def get_meta_campaign_data():
    params, error = extract_api_params(
        request=request, required_fields=meta_required_fields
    )
    if error:
        logger.error(f"Error occured in Meta : {error}")
    params.update(fb_params)
    data = make_api_request(params)
    processed_data = process_api_response_data(data)
    return create_api_response(processed_data)


@app.route("/get_meta_deep_insight", methods=["POST"])
@log_errors_and_respond(status_code=500)
def get_meta_deep_insight():
    data = request.get_json()
    response_data = get_meta_campaign_audience_metrics(data=data)
    return response_data


########################### Snapchat API Endpoints ###########################


@app.route("/get_snapchat_campaign_data", methods=["POST"])
@log_errors_and_respond(status_code=500)
def get_snapchat_data():
    try:
        data = request.get_json()
        access_token = data.get("access_token")
        platform_campaign_id = data.get("platform_campaign_id")

        if not access_token and not platform_campaign_id:
            logger.error("Snapchat : access_token and campaign_id are required")

            return jsonify({"error": "access_token and campaign_id are required"}), 400

        analytics = update_snapchat_campaign_hourly_analytics(
            access_token, platform_campaign_id
        )
        conversion_analytics = get_snapchat_conversion_data(
            access_token, platform_campaign_id
        )
        if analytics == None or conversion_analytics == None:
            logger.error("Snapchat : No Data Available - Unauthorized")
            return jsonify({"error": "No Data Available - Unauthorized"}), 400

        snapchat_data = analytics["total_stats"][0]["total_stat"]["stats"]
        conversion_object = conversion_analytics["total_stats"][0]["total_stat"][
            "stats"
        ]

        snapchat_data = format_snapchat_data(snapchat_data, conversion_object)
        return jsonify({"response": snapchat_data}), 200
    except Exception as e:
        logger.error(f"Error in snapchat api: {str(e)}")
        return jsonify({"error": str(e)}), 400


########################### TikTok API Endpoints #############################
@app.route("/get_tiktok_campaign_data", methods=["POST"])
@log_errors_and_respond(status_code=500)
def get_tiktok_data():
    try:
        data = request.get_json()
        access_token = data.get("access_token")
        customer_id = data.get("customer_id")
        date_str_start = data.get("date_str_start")
        date_str_end = data.get("date_str_end")
        platform_campaign_id = data.get("platform_campaign_id")

        if not access_token and not platform_campaign_id and not customer_id:
            return (
                jsonify(
                    {
                        "error": "access_token and campaign_id and customer_id are required"
                    }
                ),
                400,
            )

        report_data = fetch_tiktok_report(
            access_token=access_token,
            customer_id=customer_id,
            date_str_start=date_str_start,
            date_str_end=date_str_end,
        )
        structured = structure_tiktok_analytics_data(
            report_data, user_campaign_id=platform_campaign_id
        )

        return jsonify({"response": structured}), 200
    except Exception as e:
        logger.error(f"Error in tiktok api: {str(e)}")
        return tiktok_data_preparation({})
        # return jsonify({"error": str(e)}), 400


########################### Twitter API Endpoints ############################
@app.route("/get_twitter_campaign_data", methods=["POST"])
@log_errors_and_respond(status_code=500)
def get_twitter_campaign_data():
    try:
        data = request.get_json()
        # twitter_credentials = data.get("twitter_credentials")
        # # print(twitter_credentials)
        # if not twitter_credentials:
        #     return jsonify({"error": "Twitter Credentials are required"}), 400
        response = get_twitter_data(data)
        return jsonify({"response": response}), 200
    except Exception as e:
        logger.error(f"Error in twitter api: {str(e)}")
        return jsonify({"error": str(e)}), 400
    

########################### Tiktok Audience API Endpoint ###########################
@app.route("/get_tiktok_audience_campaign_data", methods=["POST"])
@log_errors_and_respond(status_code=500,platform="tiktok")
def get_tiktok_audience_campaign_data():
# try:
    data = request.get_json()
    access_token = data.get("access_token")
    customer_id = data.get("customer_id")
    date_str_start = data.get("date_str_start")
    date_str_end = data.get("date_str_end")
    platform_campaign_id = data.get("platform_campaign_id")
    # print(f"data:{data}")

    if not access_token and not platform_campaign_id and not customer_id:
        return (
            jsonify(
                {
                    "error": "access_token and campaign_id and customer_id are required"
                }
            ),
            400,
        )

    response = get_tiktok_audience_metrics(access_token, customer_id,date_str_start, date_str_end,platform_campaign_id)

    return jsonify(response), 200
# except Exception as e:
    # print("Error in tiktok audience api:", str(e))
    # return jsonify({"error": str(e)}), 400
    
########################### Snapchat Audience API Endpoint ###########################
@app.route("/get_snapchat_audience_campaign_data", methods=["POST"])
@log_errors_and_respond(status_code=500,platform="snapchat")
def get_snapchat_audience_campaign_data():
    try:
        data = request.get_json()
        access_token = data.get("access_token")
        platform_campaign_id = data.get("platform_campaign_id")

        if not access_token and not platform_campaign_id:
            return jsonify({"error": "access_token and campaign_id are required"}), 400
        
        response = get_snapchat_audience_wise_campaign_data(access_token,platform_campaign_id)
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error in snapchat audience api: {str(e)}")
        return jsonify({"error": str(e)}), 400
    
########################### Twitter Audience API Endpoints ###########################
@app.route("/get_twitter_audience_campaign_data", methods=["POST"])
@log_errors_and_respond(status_code=500,platform="twitter")
def get_twitter_audience_campaign_data():
    try:
        data = request.get_json()
        # twitter_credentials = data.get("twitter_credentials")
        # if not twitter_credentials:
        #     return jsonify({"error": "Twitter Credentials are required"}), 400

        response = get_twitter_audience_data(data)
        
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=6000)
    