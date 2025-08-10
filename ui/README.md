# 🎨 Enhanced SEM Strategy Generator UI

A comprehensive, modular web interface for the AI-powered SEM Strategy Generator with advanced visualization, detailed analytics, and multiple export options.

## ✨ Features

### 🎯 **Dual Input Methods**

- **📝 Form Input**: Interactive form with validation and real-time feedback
- **📁 Config File Upload**: Upload YAML configuration files with preview

### 📊 **Comprehensive Results Display**

- **Dashboard**: High-level KPIs and strategic insights
- **Detailed Analysis**: Filterable keyword tables with advanced metrics
- **Visual Analytics**: Interactive charts and graphs
- **Strategic Recommendations**: AI-powered campaign optimization suggestions

### 💾 **Multiple Export Formats**

- **CSV Files**: Individual campaign data for direct Google Ads import
- **JSON Summary**: Complete analysis for API integration
- **Excel Reports**: Multi-sheet comprehensive reports
- **Real-time Downloads**: Instant file generation and download

## 🚀 Quick Start

### Prerequisites

```bash
pip install -r requirements.txt
```

### Run the UI

```bash
streamlit run ui/app.py
```

The UI will open at `http://localhost:8501`

## 📋 Input Methods

### 1. Form Input

Fill out the interactive form with:

- **Brand & Competitor URLs**: Main website and competitor analysis
- **Service Locations**: Geographic targeting
- **Budget Configuration**: Search, Shopping, and PMax budgets
- **Project Settings**: Conversion rates and volume thresholds
- **Advanced Settings**: SERP queries, seed keywords, LLM context

### 2. Config File Upload

Upload a YAML configuration file:

```yaml
brand_url: "https://www.example.com"
competitor_urls:
  - "https://www.competitor1.com"
  - "https://www.competitor2.com"
service_locations:
  - "United States"
  - "United Kingdom"
ad_budgets:
  search_ads_budget: 5000
  shopping_ads_budget: 3000
  pmax_ads_budget: 7000
project_settings:
  assumed_conversion_rate: 0.02
  min_search_volume_threshold: 500
```

## 📊 Results Sections

### 1. 📈 Dashboard

- **Key Performance Indicators**: Total keywords, search volume, CPC, budget
- **Campaign Distribution**: Budget allocation and keyword intent distribution
- **Top Performing Keywords**: Ranked by search volume and performance
- **Strategic Insights**: AI-generated recommendations and budget optimization

### 2. 📋 Detailed Results

- **Search Campaign Analysis**:
  - Filterable keyword table with ad groups
  - CPC ranges and ROI potential
  - Competition and intent analysis
  - Interactive visualizations
- **PMax Themes**: Categorized campaign themes with descriptions
- **Shopping Campaign**: CPC strategy and recommendations

### 3. 📈 Analytics

- **Ad Group Distribution**: Pie charts showing keyword clustering
- **Intent Analysis**: Bar charts of keyword intent distribution
- **Competition Analysis**: Competition level breakdown
- **Volume vs CPC**: Scatter plots for bid optimization

## 💾 Export Options

### Individual Files (CSV)

- **Search Keywords**: Complete keyword list with metrics
- **PMax Themes**: Campaign themes and categories
- **Shopping CPC**: CPC recommendations and analysis

### Comprehensive Reports

- **JSON Summary**: Complete analysis with strategic insights
- **Excel Report**: Multi-sheet report with all data (requires openpyxl)

## 🏗️ Modular Architecture

### Components Structure

```
ui/
├── app.py                 # Main application
├── components/
│   ├── form.py           # Input forms and validation
│   ├── results.py        # Results display and analytics
│   ├── dashboard.py      # Dashboard and KPIs
│   └── downloads.py      # Export functionality
└── README.md
```

### Key Components

#### `form.py`

- `render_input_form()`: Main configuration form
- `render_config_upload()`: File upload interface
- `_validate_form_inputs()`: Input validation

#### `results.py`

- `render_comprehensive_results()`: Main results display
- `_create_search_dataframe()`: Keyword data processing
- `_render_search_analytics()`: Visualization generation

#### `dashboard.py`

- `render_dashboard()`: KPI dashboard
- Strategic insights and recommendations

#### `downloads.py`

- Multiple export format generation
- CSV, JSON, and Excel report creation

## 🎨 UI Features

### Interactive Elements

- **Progress Tracking**: Real-time pipeline progress
- **Filtering**: Dynamic keyword filtering by ad group, intent, competition
- **Expandable Sections**: Detailed data in collapsible sections
- **Tooltips**: Helpful information on hover

### Visual Design

- **Modern Styling**: Clean, professional interface
- **Color Coding**: Intuitive color schemes for different data types
- **Responsive Layout**: Adapts to different screen sizes
- **Professional Typography**: Clear, readable text hierarchy

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Google Gemini API for enhanced results
export GEMINI_API_KEY="your_api_key_here"
```

### Customization

- Modify `_accent()` in `form.py` for custom styling
- Adjust chart configurations in `results.py`
- Customize export formats in `downloads.py`

## 📱 Usage Workflow

1. **Choose Input Method**: Form or file upload
2. **Configure Settings**: Brand, competitors, budgets, parameters
3. **Run Analysis**: Click "Generate SEM Strategy"
4. **Review Dashboard**: High-level overview and KPIs
5. **Analyze Details**: Filter and explore keyword data
6. **Export Results**: Download in preferred format

## 🛠️ Development

### Testing

```bash
python test_ui.py
```

### Adding New Features

1. Create new component in `ui/components/`
2. Import and integrate in `app.py`
3. Update requirements.txt if needed
4. Test with sample data

### Styling

- Use Streamlit's built-in components
- Custom CSS in `_accent()` function
- Consistent color scheme and spacing

## 📊 Data Flow

```
User Input → Validation → Pipeline → Results → Display → Export
    ↓           ↓           ↓         ↓         ↓        ↓
Form/File → Config → Analysis → Dashboard → Details → Downloads
```

## 🔍 Troubleshooting

### Common Issues

- **Import Errors**: Ensure all dependencies are installed
- **Chart Display**: Check plotly installation
- **Excel Export**: Install openpyxl for Excel reports
- **Memory Issues**: Reduce max_serp_queries for large datasets

### Performance Tips

- Use appropriate max_serp_queries values
- Enable caching for repeated analysis
- Optimize chart rendering for large datasets

## 📈 Future Enhancements

- **Real-time Collaboration**: Multi-user support
- **Advanced Visualizations**: More interactive charts
- **Custom Templates**: User-defined export formats
- **API Integration**: Direct Google Ads API connection
- **Mobile Optimization**: Enhanced mobile experience

## 📄 License

For internal use; ensure compliance with all third-party site terms.

---

**Enhanced UI Version** - Professional-grade interface with comprehensive analytics and export capabilities.
