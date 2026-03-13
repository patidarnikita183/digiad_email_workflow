html_content = """<!DOCTYPE html>
<html lang="en" style="margin:0;padding:0;">
<head>
<meta charset="utf-8" />
<meta name="x-apple-disable-message-reformatting" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>DigiAd Performance Report</title>
<style>
    body{margin:0;padding:0;background:#f5f7fb;font-family:Arial,Helvetica,sans-serif;color:#1f2937;}
    a{color:#2563eb;text-decoration:none;}
    .wrap{max-width:720px;margin:0 auto;padding:16px;}
    .card{background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;box-shadow:0 1px 2px rgba(0,0,0,0.04);padding:20px;margin-bottom:14px;}
    .muted{color:#6b7280;}
    .h1{font-size:20px;line-height:1.3;margin:0;}
    .h2{font-size:16px;margin:0 0 8px 0;}
    .pill{display:inline-block;background:#eef2ff;border:1px solid #e5e7eb;color:#374151;padding:4px 10px;border-radius:999px;font-size:12px;}
    .kpis{display:flex;gap:20px;flex-wrap:wrap;}
    .kpi{flex:1 1 150px;border:1px solid #e5e7eb;border-radius:10px;padding:12px;}
    .kpi .label{font-size:12px;color:#6b7280;margin-bottom:6px;}
    .kpi .value{font-size:18px;font-weight:bold;}
    .kpi .delta{font-size:12px;margin-top:4px;}
    .pos{color:#059669;}
    .neg{color:#dc2626;}
    .flat{color:#6b7280;}
    .table{width:100%;border-collapse:collapse;}
    .table th{background:#f9fafb;color:#374151;font-size:12px;text-align:left;border-bottom:1px solid #e5e7eb;padding:10px;}
    .table td{font-size:13px;border-bottom:1px solid #f1f5f9;padding:10px;vertical-align:top;}
    .tag{display:inline-block;font-size:11px;padding:2px 8px;border-radius:999px;border:1px solid #e5e7eb;background:#f8fafc;color:#334155;}
    .cta{display:inline-block;background:#2563eb;color:#ffffff;padding:10px 14px;border-radius:10px;font-weight:bold;}
    .tips li{margin-bottom:6px;}
    @media (max-width:600px){
      .wrap{padding:8px;}
      .kpis{gap:8px;}
      .kpi{flex:1 1 45%;}
      .hide-mobile{display:none;}
    }
</style>
</head>
<body>
<div class="wrap">
 
    <!-- Header -->
    <div class="card" style="padding:18px 20px; text-align:center;">
        <img src="{{logo_url}}" alt="DigiAd Logo" style="max-width:120px; margin-bottom:10px;">
        <div style="font-weight:bold; font-size:20px; margin-bottom:10px;">
            digiAd Performance Report
        </div>
        <table role="presentation" width="100%" style="text-align:left;">
            <tr>
                <td class="muted" style="padding-top:6px;">
                    Hello <b>{{name}}</b>,<br>
                    Here’s your latest campaign performance report for <b>{{campaign_name}}</b>, 
                    covering results since it launched, up to <b>{{report_datetime}}</b>.
                </td>
            </tr>
        </table>
    </div>
 
    <!-- Aggregate KPIs -->
    <div class="card">
        <div class="h2">Aggregate (All Platforms)</div>
        <div class="kpis">
            <div class="kpi">
                <div class="label">Impressions</div>
                <div class="value">{{agg_impressions}}</div>
            </div>
            <div class="kpi">
                <div class="label">Clicks</div>
                <div class="value">{{agg_clicks}}</div>
            </div>
            <div class="kpi">
                <div class="label">CTR</div>
                <div class="value">{{agg_ctr}}</div>
            </div>
            <div class="kpi">
                <div class="label">Leads/Conv</div>
                <div class="value">{{agg_leads}}</div>
            </div>
            <div class="kpi">
                <div class="label">Avg. CPC</div>
                <div class="value">₹{{agg_cpc}}</div>
            </div>
            <div class="kpi">
                <div class="label">Cost</div>
                <div class="value">₹{{agg_cost}}</div>
            </div>
        </div>
    </div>
 
    <!-- Platform table with % deltas -->
    <div class="card">
        <div class="h2">Platform-wise Performance</div>
        <div style="overflow-x:auto;">
            <table class="table" role="presentation">
                <thead>
                    <tr>
                        <th>Platform</th>
                        <th>Status</th>
                        <th>Impr</th>
                        <th>Clicks</th>
                        <th>CTR</th>
                        <th>Conversions</th>
                        <th>Avg CPC</th>
                        <th>Cost</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Facebook -->
                    {% if "facebook" in valid_platforms %}
                    <tr>
                        <td>Facebook Ads</td>
                        <td><span class="tag" style="background:{% if fb_status == 'enabled' %}#dcfce7; color:#166534; border-color:#bbf7d0{% elif fb_status == 'paused' %}#fef3c7; color:#92400e; border-color:#fde68a{% else %}#f3f4f6; color:#6b7280; border-color:#e5e7eb{% endif %};">{{ fb_status|title }}</span></td>
                        <td>{{ fb_impr }}</td>
                        <td>{{ fb_clicks }}</td>
                        <td>{{ fb_ctr }}</td>
                        <td>{{ fb_leads }}</td>
                        <td>₹{{ fb_cpc }}</td>
                        <td>₹{{ fb_cost }}</td>
                    </tr>
                    {% endif %}

                    <!-- Google -->
                    {% if "google" in valid_platforms %}
                    <tr>
                        <td>Google Ads</td>
                        <td><span class="tag" style="background:{% if google_status == 'enabled' %}#dcfce7; color:#166534; border-color:#bbf7d0{% elif google_status == 'paused' %}#fef3c7; color:#92400e; border-color:#fde68a{% else %}#f3f4f6; color:#6b7280; border-color:#e5e7eb{% endif %};">{{ google_status|title }}</span></td>
                        <td>{{ google_impr }}</td>
                        <td>{{ google_clicks }}</td>
                        <td>{{ google_ctr }}</td>
                        <td>{{ google_leads }}</td>
                        <td>₹{{ google_cpc }}</td>
                        <td>₹{{ google_cost }}</td>
                    </tr>
                    {% endif %}

                    <!-- Snapchat -->
                    {% if "snapchat" in valid_platforms %}
                    <tr>
                        <td>Snapchat Ads</td>
                        <td><span class="tag" style="background:{% if snapchat_status == 'enabled' %}#dcfce7; color:#166534; border-color:#bbf7d0{% elif snapchat_status == 'paused' %}#fef3c7; color:#92400e; border-color:#fde68a{% else %}#f3f4f6; color:#6b7280; border-color:#e5e7eb{% endif %};">{{ snapchat_status|title }}</span></td>
                        <td>{{ snapchat_impr }}</td>
                        <td>{{ snapchat_clicks }}</td>
                        <td>{{ snapchat_ctr }}</td>
                        <td>{{ snapchat_leads }}</td>
                        <td>₹{{ snapchat_cpc }}</td>
                        <td>₹{{ snapchat_cost }}</td>
                    </tr>
                    {% endif %}

                    <!-- Twitter -->
                    {% if "twitter" in valid_platforms %}
                    <tr>
                        <td>Twitter Ads</td>
                        <td><span class="tag" style="background:{% if twitter_status == 'enabled' %}#dcfce7; color:#166534; border-color:#bbf7d0{% elif twitter_status == 'paused' %}#fef3c7; color:#92400e; border-color:#fde68a{% else %}#f3f4f6; color:#6b7280; border-color:#e5e7eb{% endif %};">{{ twitter_status|title }}</span></td>
                        <td>{{ twitter_impr }}</td>
                        <td>{{ twitter_clicks }}</td>
                        <td>{{ twitter_ctr }}</td>
                        <td>{{ twitter_leads }}</td>
                        <td>₹{{ twitter_cpc }}</td>
                        <td>₹{{ twitter_cost }}</td>
                    </tr>
                    {% endif %}

                    <!-- Tiktok -->
                    {% if "tiktok" in valid_platforms %}
                    <tr>
                        <td>Tiktok Ads</td>
                        <td><span class="tag" style="background:{% if tiktok_status == 'enabled' %}#dcfce7; color:#166534; border-color:#bbf7d0{% elif tiktok_status == 'paused' %}#fef3c7; color:#92400e; border-color:#fde68a{% else %}#f3f4f6; color:#6b7280; border-color:#e5e7eb{% endif %};">{{ tiktok_status|title }}</span></td>
                        <td>{{ tiktok_impr }}</td>
                        <td>{{ tiktok_clicks }}</td>
                        <td>{{ tiktok_ctr }}</td>
                        <td>{{ tiktok_leads }}</td>
                        <td>₹{{ tiktok_cpc }}</td>
                        <td>₹{{ tiktok_cost }}</td>
                    </tr>
                    {% endif %}

                    <!-- Youtube -->
                    {% if "youtube" in valid_platforms %}
                    <tr>
                        <td>Youtube Ads</td>
                        <td><span class="tag" style="background:{% if youtube_status == 'enabled' %}#dcfce7; color:#166534; border-color:#bbf7d0{% elif youtube_status == 'paused' %}#fef3c7; color:#92400e; border-color:#fde68a{% else %}#f3f4f6; color:#6b7280; border-color:#e5e7eb{% endif %};">{{ youtube_status|title }}</span></td>
                        <td>{{ youtube_impr }}</td>
                        <td>{{ youtube_clicks }}</td>
                        <td>{{ youtube_ctr }}</td>
                        <td>{{ youtube_leads }}</td>
                        <td>₹{{ youtube_cpc }}</td>
                        <td>₹{{ youtube_cost }}</td>
                    </tr>
                    {% endif %}

                    <!-- Instagram -->
                    {% if "instagram" in valid_platforms %}
                    <tr>
                        <td>Instagram Ads</td>
                        <td><span class="tag" style="background:{% if instagram_status == 'enabled' %}#dcfce7; color:#166534; border-color:#bbf7d0{% elif instagram_status == 'paused' %}#fef3c7; color:#92400e; border-color:#fde68a{% else %}#f3f4f6; color:#6b7280; border-color:#e5e7eb{% endif %};">{{ instagram_status|title }}</span></td>
                        <td>{{ instagram_impr }}</td>
                        <td>{{ instagram_clicks }}</td>
                        <td>{{ instagram_ctr }}</td>
                        <td>{{ instagram_leads }}</td>
                        <td>₹{{ instagram_cpc }}</td>
                        <td>₹{{ instagram_cost }}</td>
                    </tr>
                    {% endif %}

                    {% if valid_platforms | length == 0 %}
                    <tr>
                        <td colspan="8" style="text-align:center; color:#6b7280;">
                            No data available
                        </td>
                    </tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>

    <p style="font-size:14px; color:#333;">
        We’ll continue tracking the campaign’s progress and share regular updates with you.
    </p>
 
    <div style="text-align:center; margin-top:20px; font-size:14px; color:#555;">
        To view your campaign performance in detail, click the button below:
    </div>
 
    <div style="text-align:center; margin-top:10px;">
        <a href="{{campaign_url}}" style="background-color:#007bff; color:#fff; padding:10px 20px; 
                  text-decoration:none; border-radius:5px; display:inline-block;">
            View Campaign Analytics
        </a>
    </div>
 
    <!-- Footer -->
    <div style="font-size:12px; color:#888; text-align:center; margin:10px 0 30px;">
        Sent by digiAd • Need help? 
        <a href="{{support_link}}" style="color:#888; text-decoration:underline;">Contact Support</a>
    </div>
 
</div>
</body>
</html>
"""


paused_campaign_mail_html_template="""<!DOCTYPE html>
<html lang="en" style="margin:0;padding:0;">
<head>
<meta charset="utf-8" />
<meta name="x-apple-disable-message-reformatting" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>DigiAd Campaign Paused</title>
<style>
    body{margin:0;padding:0;background:#f5f7fb;font-family:Arial,Helvetica,sans-serif;color:#1f2937;}
    a{color:#2563eb;text-decoration:none;}
    .wrap{max-width:720px;margin:0 auto;padding:16px;}
    .card{background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;box-shadow:0 1px 2px rgba(0,0,0,0.04);padding:20px;margin-bottom:14px;}
    .muted{color:#6b7280;}
    .h1{font-size:20px;line-height:1.3;margin:0;}
    .h2{font-size:16px;margin:0 0 8px 0;}
    .alert-box{background:#fef3c7;border:1px solid #fbbf24;border-radius:10px;padding:16px;margin:20px 0;}
    .alert-icon{font-size:24px;margin-bottom:8px;}
    .kpis{display:flex;gap:20px;flex-wrap:wrap;}
    .kpi{flex:1 1 150px;border:1px solid #e5e7eb;border-radius:10px;padding:12px;}
    .kpi .label{font-size:12px;color:#6b7280;margin-bottom:6px;}
    .kpi .value{font-size:18px;font-weight:bold;}
    .cta{display:inline-block;background:#2563eb;color:#ffffff;padding:10px 14px;border-radius:10px;font-weight:bold;text-decoration:none;}
    .cta-secondary{display:inline-block;background:#ffffff;color:#2563eb;border:2px solid #2563eb;padding:10px 14px;border-radius:10px;font-weight:bold;text-decoration:none;}
    .info-list{background:#f9fafb;border-radius:8px;padding:16px;margin:16px 0;}
    .info-list li{margin-bottom:10px;line-height:1.6;}
    @media (max-width:600px){
      .wrap{padding:8px;}
      .kpis{gap:8px;}
      .kpi{flex:1 1 45%;}
    }
</style>
</head>
<body>
<div class="wrap">
 
    <!-- Header -->
    <div class="card" style="padding:18px 20px; text-align:center;">
        <img src="{{logo_url}}" alt="DigiAd Logo" style="max-width:120px; margin-bottom:10px;">

        <div style="font-weight:bold; font-size:20px; margin-bottom:10px;">
            Campaign Status Update
        </div>
        <table role="presentation" width="100%" style="text-align:left;">
            <tr>
                <td class="muted" style="padding-top:6px;">
                    Hello <b>{{name}}</b>,<br>
                    This is an important update regarding your campaign <b>{{campaign_name}}</b>.
                </td>
            </tr>
        </table>
    </div>

    <!-- Pause Alert -->
        <div class="alert-box">
            <div class="alert-icon">⏸️</div>
            <div style="font-size:18px; font-weight:bold; color:#92400e; margin-bottom:8px;">
                Campaign Paused
            </div>
            <div style="font-size:14px; color:#78350f; line-height:1.6;">
                Your campaign <b>{{campaign_name}}</b> has been paused as of <b>{{pause_datetime}}</b>.
                {% if pause_reason %}
                <br><br>
                <b>Reason:</b> {{pause_reason}}
                {% endif %}
            </div>
        </div>


    <!-- What This Means -->
    <div class="card">
        <div class="h2">What This Means</div>
        <div class="info-list">
            <ul style="margin:0; padding-left:20px;">
                <li>Your campaign has been <b>paused by you</b> and will remain inactive until resumed.</li>
                <li>Performance metrics will be temporarily unavailable while the campaign is paused and will automatically resume upon reactivation.</li>
                <li>You can resume your campaign anytime from your digiAd dashboard.</li>
            </ul>
        </div>
    </div>

    <!-- Performance Summary (Till Pause) - COMMENTED FOR FUTURE USE -->
    <!-- <div class="card">
        <div class="h2">Performance Summary (Till Pause)</div>
        <div style="font-size:13px; color:#6b7280; margin-bottom:12px;">
            Campaign ran from <b>{{campaign_start_date}}</b> to <b>{{pause_datetime}}</b>
        </div>
        <div class="kpis">
            <div class="kpi">
                <div class="label">Total Impressions</div>
                <div class="value">{{total_impressions}}</div>
            </div>
            <div class="kpi">
                <div class="label">Total Clicks</div>
                <div class="value">{{total_clicks}}</div>
            </div>
            <div class="kpi">
                <div class="label">Overall CTR</div>
                <div class="value">{{overall_ctr}}</div>
            </div>
            <div class="kpi">
                <div class="label">Total Leads/Conv</div>
                <div class="value">{{total_leads}}</div>
            </div>
            <div class="kpi">
                <div class="label">Total Spend</div>
                <div class="value">₹{{total_cost}}</div>
            </div>
            <div class="kpi">
                <div class="label">Avg. CPC</div>
                <div class="value">₹{{avg_cpc}}</div>
            </div>
        </div>
    </div> -->

    <!-- Next Steps 
    <div class="card">
        <div class="h2">Next Steps</div>
        <p style="font-size:14px; color:#374151; line-height:1.6; margin-top:12px;">
            If you'd like to resume your campaign or make any changes, you can do so at any time through your dashboard. 
            Our team is here to help if you have any questions or need assistance.
        </p>
    </div> -->

    <div style="text-align:center; margin-top:20px; font-size:14px; color:#555;">
       To resume your campaign or make any changes, click the button below:
    </div>

    <!-- CTA Buttons - COMMENTED FOR FUTURE USE -->
    <div style="text-align:center; margin:15px 0;">
     <!--   <a href="{{campaign_url}}" class="cta" style="margin:0 8px 10px 8px;">
            View Campaign Details
        </a>
        <br> -->
        <a href="{{campaign_resume_url}}" style="background-color:#007bff; color:#fff; padding:10px 20px; 
                  text-decoration:none; border-radius:5px; display:inline-block;">
            Resume Campaign
        </a>
    </div>

    <!-- Support Section -->
    <div class="card" style="background:#f9fafb; text-align:center;">
        <div style="font-size:14px; color:#374151; margin-bottom:12px;">
            <b>Need Help?</b>
        </div>
        <div style="font-size:13px; color:#6b7280; line-height:1.6;">
            Have questions about your paused campaign? Our support team is ready to assist you.
        </div>
        <div style="margin-top:12px;">
            <a href="{{support_link}}" style="color:#2563eb; text-decoration:underline; font-weight:bold;">
                Contact Support
            </a>
        </div>
    </div>
 
 
</div>
</body>
</html>"""




