html_content_audience = """
<!DOCTYPE html>
<html lang="en" style="margin:0;padding:0;">

<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>DigiAd Daily Performance Report</title>
    <style>
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

<body style="margin:0;padding:0;background:#f5f7fb;font-family:Arial,Helvetica,sans-serif;color:#333;">

    <!-- Container -->
    <table align="center" width="100%" cellpadding="0" cellspacing="0" border="0"
        style="max-width:600px;margin:auto;background:#f5f7fb;border-radius:12px;box-shadow:0 2px 6px rgba(0,0,0,0.1);">
        <tr>
            <td style="padding:24px;text-align:center;background:#2c3e50;border-radius:12px 12px 0 0;">
                <img src="https://digiad.ai/_next/image?url=%2Fimages%2FdigiAd-logo.png&w=256&q=75" alt="DigiAd Logo"
                    style="max-width:120px; margin-bottom:10px;">
                <h1 style="margin:0;font-size:22px;color:#ffffff;">DigiAd Daily Performance Report</h1>
            </td>
        </tr>
        <tr>
            <td class="muted" style="padding:20px;">
                Hello <b>{{name}}</b>,<br><br>
                Here’s your Daily Campaign Performance Summary for <b>{{campaign_name}}</b> from <b> {{reporting_period}}</b>, with key highlights and
                recommendations to guide your next steps:
            </td>
        </tr>

        <!-- Highlights -->
        <tr>
            <td style="padding:0px 10px 10px 10px;">
                <div style="background:#fff;
                    border-radius:12px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);
                    padding:10px;">
                    <h2 style="font-size:18px;color:#2c3e50;margin-bottom:10px;font-weight:600;">📊 Performance
                        Highlights (All Platforms)</h2>
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
                            <div class="label">Leads / Conversions</div>
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
                    <strong>
                        <p style="font-size:13px;color:#666;">See attached PDF for a detailed breakdown by platform and
                            audience segments.</p>
                    </strong>
                </div>
            </td>
        </tr>

        <tr>
        <td style="padding:0px 10px 10px 10px;">
        <!-- Platform table with % deltas -->
    <div class="card">
    <h2 style="font-size:18px;color:#2c3e50;margin-bottom:10px;font-weight:600;">📈 Platform-wise Performance</h2>
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


                    {% if not fb_impr and not google_impr %}
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
        </td>
        </tr>

        <!-- Insights -->
        <tr>
            <td style="padding:0px 10px 10px 10px;">
                <div style="background:#fff;
                    border-radius:12px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);
                    padding:10px;">
                    <h2 style="font-size:18px;
                    color:#2c3e50;
                    margin-bottom:10px;
                    font-weight:600;">
                        🔎 Insights
                    </h2>
                    <ul style="padding-left:20px;
                    margin:0;
                    font-size:14px;
                    line-height:1.6;
                    color:#4a4a4a;">
                        {{insights_html | safe}}
                    </ul>
                </div>
            </td>
        </tr>


        <!-- Actions -->
        <tr>
            <td style="padding:0px 10px 10px 10px;">
                <div style="background:#fff;
                    border-radius:12px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);
                    padding:10px;">
                    <h2 style="font-size:18px;color:#2c3e50;margin-bottom:10px;font-weight:600;">✅ Recommended Next
                        Actions</h2>
                    <ol style="padding-left:20px;margin:0;font-size:14px;line-height:1.6;">
                        {{actions_html | safe}}
                    </ol>
                </div>
            </td>
        </tr>
        <tr>
            <td>
                <div style="text-align:center; margin-top:20px; font-size:14px; color:#555;">
                    To view your campaign performance in detail, click the button below:
                </div>
                <div style="text-align:center; margin-top:10px;">
                    <a href="{{campaign_url}}" style="background-color:#007bff; color:#fff; padding:10px 20px; 
                  text-decoration:none; border-radius:5px; display:inline-block;">
                        View Campaign Analytics
                    </a>
                </div>
            </td>
        </tr>


        <tr>
            <td style="padding:20px;">
                <p style="font-size:14px;margin:0 0 15px 0;">
                    Best regards,<br />
                    <strong>Team DigiAd</strong>
                </p>
            </td>

        </tr>


        <!-- Footer -->
        <tr>
            <td style="padding:20px;text-align:center;background:#2c3e50;border-radius:0 0 12px 12px;">
                <p style="color:#ffffff;font-size:13px;margin:0 0 10px 0;">Follow us on</p>
                <a href="https://www.facebook.com/profile.php?id=61576900078236"
                    style="margin:0 8px;display:inline-block;">
                    <img src="https://cdn-icons-png.flaticon.com/24/733/733547.png" width="24" alt="Facebook" />
                </a>
                <a href="https://www.instagram.com/digiadai/" style="margin:0 8px;display:inline-block;">
                    <img src="https://cdn-icons-png.flaticon.com/512/2111/2111463.png" width="24" alt="Instagram" />
                </a>
                <a href="https://x.com/digiAd_AI" style="margin:0 8px;display:inline-block;">
                    <img src="https://cdn-icons-png.flaticon.com/512/5969/5969020.png" width="24" alt="X" />
                </a>
                <a href="https://www.tiktok.com/@digiadai?lang=en" style="margin:0 8px;display:inline-block;">
                    <img src="https://cdn-icons-png.flaticon.com/512/3046/3046120.png" width="24" alt="Tiktok" />
                </a>
                <a href="https://in.linkedin.com/company/digiad-ai" style="margin:0 8px;display:inline-block;">
                    <img src="https://cdn-icons-png.flaticon.com/24/733/733561.png" width="24" alt="LinkedIn" />
                </a>
                <p style="color:#bdc3c7;font-size:12px;margin-top:12px;">© 2025 DigiAd. All rights reserved.</p>
            </td>
        </tr>
    </table>

</body>

</html>
"""