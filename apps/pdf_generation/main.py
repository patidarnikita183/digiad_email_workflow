import json
from pdf_generation.pdf_generator import generate_report_pdf
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
# Add these lines right after your imports in utils.py
import time
from pdf_generation.pdf_utils import *
from pdf_generation.config import *
from flask import Flask,request, jsonify
from utils.general_constants import logger

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
plt.ioff()  # Turn off interactive mode



app = Flask(__name__)


@app.route('/generate_report', methods=['POST'])
def generate_multi_platform_campaign_report(platforms_performance_json_data=None, insights_and_recommendations=None, campaign_info={}):
    """Main function to process JSON data and create charts with plot-specific insights"""
    try:
        if platforms_performance_json_data is None or insights_and_recommendations is None:
            logger.error("Missing required JSON data: 'platforms_performance_json_data' or 'insights_and_recommendations'")
            return {"error": "Missing platform performance or insights data fields in JSON"}

        # Process insights data to maintain detailed structure
        gathered_insights_and_recommendations = gather_platform_wise_data(insights_and_recommendations)

        # Process JSON data into DataFrames
        metric = 'ctr'
        logger.info("PDF-module: Processing platforms performance data...")

        platform_dataframes = process_platform_json_data(platforms_performance_json_data, metric=metric)
        
        # Prepare data with plots
        logger.info("PDF-module: Preparing data with plots...")
        platform_data = prepare_data_with_plots(platform_dataframes, metric=metric)

        if not platform_data:
            logger.error("PDF-module: No valid platform data found.")
            return {"error": "No valid platform data found"}

        if campaign_info:
            campaign_info['platforms'] = list(platform_data.keys())
        else:
            logger.error("PDF-module: Missing required JSON data: 'campaign_info'")
            return {"error": "Missing campaign_info in JSON"}

        # Add plot-specific insights and actions
        logger.info("PDF-module: Adding plot-specific insights and actions...")
        platform_data = add_insights_and_actions_to_plots(
            platform_data=platform_data, 
            json_data=gathered_insights_and_recommendations
        )

        # # Debug: Print structure
        # for platform, info in platform_data.items():
        #     if isinstance(info, dict) and 'plot_insights' in info:
        #         print(f"\n{platform} has {len(info.get('plot_insights', []))} plot insights")
        #         for i, (title, insight) in enumerate(zip(info.get('df_titles', []), info.get('plot_insights', []))):
        #             print(f"  Plot {i+1}: {title}")
        #             print(f"    Insight: {insight}")

        # Generate PDF report
        logger.info("PDF-module: Data prepared for the PDF report...")
        file_name = generate_report_pdf(
            campaign_info=campaign_info,
            platforms_data=platform_data           
        )

        logger.info(f"Generated report: {file_name}")
        return file_name

    except Exception as e:
        logger.error(f"PDF-module: Error:- {e}")
        return {"error": str(e)}

# if __name__ == "__main__":
#     app.run(debug=True)