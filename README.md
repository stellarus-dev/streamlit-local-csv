# Stellarus Analytics Dashboard - CSV Version

A professional Streamlit dashboard for visualizing Kansas Member Health Records analytics data from CSV files.

## Features

- **Professional UI**: Custom Stellarus branding with logo, Roboto font, and branded color scheme
- **Real-time Analytics**: KPI tiles showing Website Crossovers, Link Clicks, and Click Conversion
- **Interactive Visualizations**: 
  - Executive Overview with trend analysis
  - Website Crossovers tracking
  - Link Clicks monitoring
- **Filtering**: Date range and browser filtering capabilities
- **CSV Data Source**: Reads data from local `data.csv` file

## Deployment

This dashboard is deployed to Azure App Service and automatically deploys when changes are pushed to the main branch.

### Azure Deployment

The app uses GitHub Actions for CI/CD:
1. Builds with Python 3.12
2. Installs Streamlit and dependencies
3. Packages the virtual environment and CSV data with the app
4. Deploys to Azure App Service

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure `data.csv` is in the project root directory

3. Run the dashboard:
```bash
streamlit run streamlit_csv.py
```

The dashboard will be available at `http://localhost:8501`

## Project Structure

```
.
├── streamlit_csv.py                # Main dashboard application
├── data.csv                        # Analytics data file
├── Stellarus_logo_2C_whiteype.png # Stellarus logo
├── requirements.txt                # Python dependencies
├── runtime.txt                     # Python version for Azure
├── startup.sh                      # Azure startup script
└── .github/workflows/              # CI/CD pipeline
```

## Technology Stack

- **Streamlit**: Dashboard framework
- **Plotly**: Interactive visualizations
- **Pandas**: Data manipulation
- **Python 3.12**: Runtime environment

## Data Format

The `data.csv` file should contain the following columns:
- `event_id`, `event_timestamp`, `event_date`, `event_type`
- `state`, `city`, `zipcode`, `user_id`, `session_id`
- `traffic_source`, `utm_source`, `utm_medium`, `utm_campaign`
- `browser`, `device_type`, `page_path`, `landing_page`
- And other analytics fields as needed
