import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
from datetime import datetime
import calendar

# Add the root directory to Python path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from database.db_manager import get_transactions
from utils.helpers import format_currency

st.set_page_config(
    page_title="Financial Analytics - Money Manager",
    page_icon="📈",
    layout="wide"
)

st.title("Financial Analytics 📈")

# Get transactions
df = get_transactions()

if not df.empty:
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Add month and year columns for easier filtering
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Year filter
    years = sorted(df['year'].unique())
    selected_year = st.sidebar.selectbox("Select Year", years, index=len(years)-1)
    
    # Month filter
    months = sorted(df[df['year'] == selected_year]['month'].unique())
    selected_month = st.sidebar.selectbox(
        "Select Month",
        months,
        index=len(months)-1,
        format_func=lambda x: calendar.month_name[x]
    )
    
    # Filter data for selected month
    mask = (df['year'] == selected_year) & (df['month'] == selected_month)
    monthly_data = df[mask].copy()
    
    if not monthly_data.empty:
        # 1. Income vs Expenses Overview
        st.subheader(f"Income vs Expenses - {calendar.month_name[selected_month]} {selected_year}")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Calculate totals
            income_total = monthly_data[monthly_data['type'] == 'Income']['amount'].sum()
            expense_total = abs(monthly_data[monthly_data['type'] == 'Expense']['amount'].sum())
            
            # Create bar chart
            fig_overview = go.Figure(data=[
                go.Bar(name='Income', x=['Income'], y=[income_total], marker_color='#2ecc71'),
                go.Bar(name='Expenses', x=['Expenses'], y=[expense_total], marker_color='#e74c3c')
            ])
            
            fig_overview.update_layout(
                barmode='group',
                height=400,
                yaxis_title="Amount",
                showlegend=True
            )
            st.plotly_chart(fig_overview, use_container_width=True)
        
        with col2:
            # Display metrics
            st.metric("Total Income", format_currency(income_total))
            st.metric("Total Expenses", format_currency(expense_total))
            balance = income_total - expense_total
            st.metric(
                "Net Balance",
                format_currency(balance),
                delta=format_currency(balance) if balance != 0 else None,
                delta_color="normal" if balance >= 0 else "inverse"
            )
        
        # 2. Expenses by Category
        st.subheader("Expenses by Category")
        col3, col4 = st.columns([2, 1])
        
        with col3:
            # Group expenses by category
            expense_by_cat = monthly_data[monthly_data['type'] == 'Expense'].groupby('category')['amount'].sum().abs()
            
            if not expense_by_cat.empty:
                # Create pie chart
                fig_expenses = px.pie(
                    values=expense_by_cat.values,
                    names=expense_by_cat.index,
                    title=f"Expense Distribution - {calendar.month_name[selected_month]} {selected_year}"
                )
                fig_expenses.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_expenses, use_container_width=True)
        
        with col4:
            # Display category breakdown table
            if not expense_by_cat.empty:
                st.write("Category Breakdown")
                expense_table = pd.DataFrame({
                    'Category': expense_by_cat.index,
                    'Amount': expense_by_cat.values
                }).sort_values('Amount', ascending=False)
                expense_table['Amount'] = expense_table['Amount'].apply(format_currency)
                st.dataframe(expense_table, hide_index=True, use_container_width=True)
        
        # 3. Daily Spending Pattern
        st.subheader("Daily Spending Pattern")
        daily_expenses = monthly_data[monthly_data['type'] == 'Expense'].groupby('date')['amount'].sum().abs()
        
        fig_daily = go.Figure()
        fig_daily.add_trace(go.Scatter(
            x=daily_expenses.index,
            y=daily_expenses.values,
            mode='lines+markers',
            name='Daily Expenses',
            line=dict(color='#e74c3c')
        ))
        
        fig_daily.update_layout(
            title=f"Daily Spending Pattern - {calendar.month_name[selected_month]} {selected_year}",
            xaxis_title="Date",
            yaxis_title="Amount",
            height=400
        )
        st.plotly_chart(fig_daily, use_container_width=True)

        # 4. Yearly Overview
        st.subheader("Yearly Overview 📅")
        
        # Get yearly data
        yearly_data = df[df['year'] == selected_year].copy()
        
        # Calculate monthly totals
        monthly_totals = yearly_data.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)
        
        # Create month labels
        month_labels = [calendar.month_name[m] for m in range(1, 13)]
        
        # Prepare data for all months (filling missing months with 0)
        full_year_data = []
        for month_num in range(1, 13):
            month_name = calendar.month_name[month_num]
            income = monthly_totals.get('Income', {}).get(month_num, 0)
            expense = abs(monthly_totals.get('Expense', {}).get(month_num, 0))
            net = income - expense
            full_year_data.append({
                'month_num': month_num,
                'Month': month_name,
                'Income': income,
                'Expense': expense,
                'Net': net
            })
        
        yearly_df = pd.DataFrame(full_year_data)
        
        # Create the yearly overview chart
        fig_yearly = go.Figure()
        
        # Add Income bars
        fig_yearly.add_trace(go.Bar(
            name='Income',
            x=yearly_df['Month'],
            y=yearly_df['Income'],
            marker_color='#2ecc71'
        ))
        
        # Add Expense bars
        fig_yearly.add_trace(go.Bar(
            name='Expenses',
            x=yearly_df['Month'],
            y=yearly_df['Expense'],
            marker_color='#e74c3c'
        ))
        
        # Add Net Income line
        fig_yearly.add_trace(go.Scatter(
            name='Net Income',
            x=yearly_df['Month'],
            y=yearly_df['Net'],
            mode='lines+markers',
            line=dict(color='#3498db', width=2),
            marker=dict(size=8),
            yaxis='y2'
        ))
        
        # Update layout
        fig_yearly.update_layout(
            title=f'Monthly Income vs Expenses Overview - {selected_year}',
            yaxis=dict(
                title='Amount',
                titlefont=dict(color='#1f77b4'),
                tickfont=dict(color='#1f77b4')
            ),
            yaxis2=dict(
                title='Net Income',
                titlefont=dict(color='#3498db'),
                tickfont=dict(color='#3498db'),
                overlaying='y',
                side='right'
            ),
            xaxis_title='Month',
            barmode='group',
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Display the chart
        st.plotly_chart(fig_yearly, use_container_width=True)
        
        # Display monthly breakdown table
        st.subheader("Monthly Breakdown Table")
        
        display_df = yearly_df.copy()
        display_df['Income'] = display_df['Income'].apply(format_currency)
        display_df['Expenses'] = display_df['Expense'].apply(format_currency)
        display_df['Net Income'] = display_df['Net'].apply(format_currency)
        display_df = display_df[['Month', 'Income', 'Expenses', 'Net Income']]
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Monthly Insights
        st.subheader("Monthly Insights")
        
        col5, col6 = st.columns(2)
        
        with col5:
            best_month = yearly_df.loc[yearly_df['Net'].idxmax()]
            st.success(f"""
            💰 Best performing month: **{best_month['Month']}**
            - Income: {format_currency(best_month['Income'])}
            - Expenses: {format_currency(best_month['Expense'])}
            - Net Income: {format_currency(best_month['Net'])}
            """)
        
        with col6:
            worst_month = yearly_df.loc[yearly_df['Net'].idxmin()]
            st.error(f"""
            📉 Month with lowest net income: **{worst_month['Month']}**
            - Income: {format_currency(worst_month['Income'])}
            - Expenses: {format_currency(worst_month['Expense'])}
            - Net Income: {format_currency(worst_month['Net'])}
            """)
        
        # 5. Financial Forecasting
        st.subheader("Financial Forecasting 🔮")

        # Calculate 3-month moving averages for smoother forecasting
        forecast_data = yearly_df.copy()
        forecast_data['MA3_Income'] = forecast_data['Income'].rolling(window=3).mean()
        forecast_data['MA3_Expense'] = forecast_data['Expense'].rolling(window=3).mean()

        # Create the forecast visualization
        fig_forecast = go.Figure()

        # Historical data
        fig_forecast.add_trace(go.Scatter(
            name='Income (Historical)',
            x=forecast_data['Month'][:len(forecast_data)],
            y=forecast_data['Income'],
            mode='lines+markers',
            line=dict(color='#2ecc71', dash='dot')
        ))

        fig_forecast.add_trace(go.Scatter(
            name='Expenses (Historical)',
            x=forecast_data['Month'][:len(forecast_data)],
            y=forecast_data['Expense'],
            mode='lines+markers',
            line=dict(color='#e74c3c', dash='dot')
        ))

        # Forecasted data (using moving averages)
        fig_forecast.add_trace(go.Scatter(
            name='Income (Forecast)',
            x=forecast_data['Month'][len(forecast_data)-3:],
            y=forecast_data['MA3_Income'].tail(3),
            mode='lines',
            line=dict(color='#27ae60', width=3)
        ))

        fig_forecast.add_trace(go.Scatter(
            name='Expenses (Forecast)',
            x=forecast_data['Month'][len(forecast_data)-3:],
            y=forecast_data['MA3_Expense'].tail(3),
            mode='lines',
            line=dict(color='#c0392b', width=3)
        ))

        fig_forecast.update_layout(
            title='3-Month Financial Forecast',
            xaxis_title='Month',
            yaxis_title='Amount',
            height=500,
            showlegend=True
        )

        st.plotly_chart(fig_forecast, use_container_width=True)

        # Forecast insights
        st.subheader("Forecast Insights")
        col1, col2 = st.columns(2)

        with col1:
            # Calculate average monthly growth rates
            income_growth = forecast_data['Income'].pct_change().mean() * 100
            expense_growth = forecast_data['Expense'].pct_change().mean() * 100
            
            st.info(f"""
            📈 **Growth Trends**
            - Average monthly income growth: {income_growth:.1f}%
            - Average monthly expense growth: {expense_growth:.1f}%
            """)

        with col2:
            # Calculate next month's forecasted values
            next_month_income = forecast_data['MA3_Income'].iloc[-1]
            next_month_expense = forecast_data['MA3_Expense'].iloc[-1]
            
            st.info(f"""
            🔮 **Next Month Forecast**
            - Projected Income: {format_currency(next_month_income)}
            - Projected Expenses: {format_currency(next_month_expense)}
            - Projected Net: {format_currency(next_month_income - next_month_expense)}
            """)
    else:
        st.info(f"No transactions found for {calendar.month_name[selected_month]} {selected_year}")

else:
    st.error("""
    No transactions found. Please add some transactions in the Data Entry page.
    """)