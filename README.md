# DigiAd Campaign Reporting API

A Flask-based API service that aggregates campaign performance data from Google Ads and Facebook Ads platforms and sends automated email reports to clients.

## 🚀 Features

- **Multi-Platform Integration**: Supports both Google Ads and Facebook Ads data retrieval
- **Automated Email Reports**: Generates and sends HTML email reports with campaign performance metrics
- **Flexible Configuration**: Easy setup with environment variables
- **Real-time Data Processing**: Fetches fresh campaign data for accurate reporting
- **Professional Email Templates**: Clean, responsive HTML email templates
- **Domain Email Service**: Microsoft Graph API integration for enterprise email delivery

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Contributing](#contributing)

## 🏗️ Architecture Overview

The DigiAd Campaign Reporting API follows a modular architecture designed for scalability and maintainability. Here's how the campaign report generation and delivery process works:

### Report Generation Flow

```
Client Request → Data Aggregation → Report Generation → Email Delivery
      ↓               ↓                    ↓               ↓
  API Endpoint → Platform APIs → HTML Template → Microsoft Graph
```

#### 1. **Request Processing**
- Client sends campaign report request via `/get_hourly_campaign_report` endpoint
- Flask app validates request parameters and platform credentials
- Determines which platforms (Google Ads, Facebook Ads) to query based on provided credentials

#### 2. **Data Aggregation**
- **Google Ads Integration**: Uses Google Ads API with OAuth 2.0 authentication
  - Executes custom queries to fetch campaign metrics (impressions, clicks, conversions, cost)
  - Processes data through `process_campaign_data()` helper function
- **Facebook Ads Integration**: Uses Facebook Graph API with access tokens
  - Retrieves insights data using predefined field parameters
  - Calculates cost-per-lead and other derived metrics

#### 3. **Data Processing & Normalization**
- Platform-specific data is normalized into common metrics format
- Aggregates data across platforms (total impressions, clicks, CTR, conversions, CPL)
- Handles edge cases like missing data, zero divisions, and API failures gracefully

#### 4. **Report Generation**
- Populates responsive HTML email template with campaign performance data
- Template includes:
  - Client branding and campaign information
  - Aggregate KPIs across all platforms
  - Platform-wise performance breakdown table
  - Professional styling with mobile responsiveness

#### 5. **Email Delivery**
- **Authentication**: Uses Microsoft Graph API with application permissions
- **Token Management**: Automatically handles token refresh and expiry
- **Email Service**: Sends HTML emails on behalf of domain users (`@digiad.ai`)

### Key Components

- **Flask App (`app.py`)**: Main application with REST API endpoints
- **Data Helpers (`helper.py`)**: Platform-specific data processing utilities  
- **Email Services (`mail/`)**: Microsoft Graph integration for enterprise email delivery
- **Templates (`email_template.py`)**: Professional HTML email template
- **Configuration (`configuration_service.py`)**: Centralized config management


## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd digiad-campaign-reporting
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

Create a `.env` file in the root directory with the following variables:

```env
# Microsoft Graph API Configuration
CLIENT_ID=your_microsoft_app_client_id
CLIENT_SECRET=your_microsoft_app_client_secret
TENANT_ID=your_microsoft_tenant_id

# Email Service Configuration
BASE_URL_EMAIL=http://localhost:6000
LOGO_URL=https://your-domain.com/logo.png

# Application Configuration
PORT=6000

# Auto-generated (don't set manually)
app_access_token=
app_expires_at=
```

### Microsoft Graph API Setup

1. Register an application in Azure AD
2. Configure API permissions:
   - `Mail.Send` (Application permission)
   - `User.Read.All` (Application permission)
3. Grant admin consent for the permissions
4. Create a client secret

## 🔌 API Endpoints

### 1. Generate Campaign Report
**POST** `/get_hourly_campaign_report`

Generates and sends an email report with aggregated campaign performance data.

#### Request Body
```json
{
  "customer_name": "Client Name",
  "campaign_name": "Campaign Name",
  "to_mail": "client@example.com",
  "from_mail": "reports@digiad.ai",
  "platforms": {
    "google": {
      "customer_id": "1234567890",
      "campaign_id": "987654321",
      "developer_token": "google_ads_developer_token",
      "client_id": "google_oauth_client_id",
      "client_secret": "google_oauth_client_secret",
      "refresh_token": "google_oauth_refresh_token",
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    },
    "facebook": {
      "access_token": "facebook_access_token",
      "ad_campaign_id": "facebook_campaign_id",
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    }
  }
}
```

#### Response
```json
{
  "status": "success",
  "message": "Email sent successfully",
  "from": "reports@digiad.ai",
  "to": "client@example.com",
  "timestamp": "2024-01-31T10:30:00Z"
}
```

### 2. Get Google Ads Data
**POST** `/get_google_campaign_data`

Retrieves campaign performance data from Google Ads.

#### Request Body
```json
{
  "customer_id": "1234567890",
  "campaign_id": "987654321",
  "developer_token": "your_developer_token",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "refresh_token": "your_refresh_token",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

### 3. Get Facebook Ads Data
**POST** `/get_facebook_campaign_data`

Retrieves campaign performance data from Facebook Ads.

#### Request Body
```json
{
  "access_token": "facebook_access_token",
  "ad_campaign_id": "facebook_campaign_id",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

## 📊 Usage Examples

### Basic Campaign Report Generation

```python
import requests

url = "http://localhost:6000/get_hourly_campaign_report"
payload = {
    "customer_name": "Acme Corp",
    "campaign_name": "Q1 Brand Campaign",
    "to_mail": "marketing@acmecorp.com",
    "from_mail": "reports@digiad.ai",
    "platforms": {
        "google": {
            "customer_id": "1234567890",
            "campaign_id": "987654321",
            # ... other Google Ads credentials
        },
        "facebook": {
            "access_token": "your_fb_token",
            "ad_campaign_id": "23851028410960174",
            # ... other Facebook Ads parameters
        }
    }
}

response = requests.post(url, json=payload)
print(response.json())
```

### Google Ads Only Report

```python
payload = {
    "customer_name": "Tech Startup",
    "campaign_name": "Lead Generation",
    "to_mail": "cmo@techstartup.com",
    "from_mail": "reports@digiad.ai",
    "platforms": {
        "google": {
            "customer_id": "1234567890",
            "campaign_id": "987654321",
            "developer_token": "your_token",
            "client_id": "your_client_id",
            "client_secret": "your_secret",
            "refresh_token": "your_refresh_token",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
    }
}
```

## 📁 Project Structure

```
digiad-campaign-reporting/
├── app.py                          # Main Flask application
├── utils/
│   ├── email_template.py           # HTML email template
│   ├── helper.py                   # Data processing utilities
│   ├── query.py                    # Database queries and API parameters
│   └── mail/
│       ├── authorization_service.py # Microsoft Graph authentication
│       ├── configuration_service.py # Configuration management
│       └── email_service.py        # Email sending service
├── requirements.txt                # Python dependencies
├── .env                          # Environment variables (create this)
└── README.md                     # This file
```

## 📦 Dependencies

### Core Dependencies
- **Flask**: Web framework for API endpoints
- **requests**: HTTP library for external API calls
- **python-dotenv**: Environment variable management
- **google-ads**: Google Ads API client library

### Email Service Dependencies
- **Microsoft Graph SDK**: For enterprise email delivery
- **Jinja2**: Template rendering (included with Flask)


## 🚦 Running the Application

### Development Mode
```bash
python app.py
```

The API will be available at `http://localhost:6000`


## 🔐 Security Considerations

- Store sensitive credentials in environment variables
- Use application-level permissions for Microsoft Graph

## 📝 Email Template Customization

You can customize:

- **Styling**: Modify CSS styles in the template
- **Layout**: Adjust the HTML structure
- **Branding**: Update logo URL and company information
- **Content**: Modify text content and formatting

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify Microsoft Graph API credentials
   - Check if admin consent is granted
   - Ensure token hasn't expired

2. **Google Ads API Errors**
   - Validate developer token and OAuth credentials
   - Check campaign ID format
   - Verify API quota limits

3. **Facebook API Errors**
   - Ensure access token has required permissions
   - Verify campaign ID format
   - Check API version compatibility
   
---

**DigiAd** - Streamlining campaign performance reporting with smart automation and insights.