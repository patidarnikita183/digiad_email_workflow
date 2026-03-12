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
                        <td colspan="6" style="text-align:center; color:#6b7280;">
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
