# Money Manager 💰

A comprehensive personal finance management application built with Streamlit and Python. Track expenses, manage budgets, analyze spending patterns, and generate detailed financial reports.

## 🌟 Features

### Core Functionality
- **Transaction Management**: Add, edit, and delete both regular and recurring transactions
- **Budget Planning**: Set and monitor category-wise monthly budgets
- **Financial Reports**: Generate detailed monthly and yearly reports
- **Data Visualization**: Interactive charts and graphs for financial analysis
- **Category Tracking**: Monitor spending across different categories
- **Export Options**: Export data and reports to CSV or Excel formats

### Key Components
- **Data Entry**: Easy-to-use interface for adding transactions
- **Transaction View**: Comprehensive transaction history with search and filter options
- **Budget Tracking**: Visual representation of budget utilization
- **Financial Analytics**: Detailed analysis of spending patterns
- **Reports Generation**: Customizable financial reports

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/money-manager.git
cd money-manager
```

2. Create and activate a virtual environment (recommended):
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/MacOS
python3 -m venv .venv
source .venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run Home.py
```

## 📁 Project Structure

```
money_manager/
├── Home.py                 # Main application entry point
├── pages/                  # Streamlit pages
│   ├── 1_data_entry.py            # Transaction entry interface
│   ├── 2_view_transactions.py     # Transaction viewing and management
│   ├── 3_data_visualization.py    # Data visualization and analytics
│   ├── 4_Settings.py              # Application settings
│   ├── 5_Budget_Planning.py       # Budget management
│   ├── 6_Transaction_Management.py # Advanced transaction management
│   └── 7_Reports.py               # Financial reports generation
├── database/              # Database management
│   ├── __init__.py
│   └── db_manager.py     # Database operations
├── utils/                # Utility functions
│   ├── __init__.py
│   └── helpers.py       # Helper functions
├── data/                # Data storage (created automatically)
│   └── transactions.db  # SQLite database
├── requirements.txt     # Project dependencies
└── README.md           # Project documentation
```

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: SQLite
- **Data Processing**: Pandas
- **Visualization**: Plotly
- **Export Functionality**: openpyxl

## 📊 Features in Detail

### Transaction Management
- Add regular and recurring transactions
- Categorize transactions
- Add comments and details
- Edit or delete existing transactions
- Search and filter functionality

### Budget Planning
- Set monthly budgets by category
- Track budget utilization
- Receive overspending alerts
- Visual budget progress indicators

### Financial Reports
- Monthly and yearly summaries
- Category-wise breakdown
- Spending pattern analysis
- Growth rate calculations
- Export capabilities

### Data Visualization
- Interactive charts and graphs
- Spending pattern visualization
- Budget vs actual comparisons
- Category distribution analysis

## 🔐 Security

- Local data storage using SQLite
- No external data transmission
- All sensitive information stays on your machine

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Your Name - *Initial work* - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- Streamlit team for the amazing framework
- All contributors who participate in this project
- The open source community for their invaluable resources

## 📧 Contact

Your Name - your.email@example.com

Project Link: [https://github.com/yourusername/money-manager](https://github.com/yourusername/money-manager)
