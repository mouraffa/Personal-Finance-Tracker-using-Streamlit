import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path
import calendar
import plotly.graph_objects as go
import plotly.express as px
import io

# Add the root directory to Python path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from database.db_manager import get_transactions, get_category_thresholds
from utils.helpers import format_currency

st.set_page_config(
    page_title="Financial Reports - Money Manager",
    page_icon="📊",
    layout="wide"
)

st.title("Financial Reports 📊")

# Create tabs for monthly and yearly reports
tab1, tab2 = st.tabs(["Monthly Report", "Yearly Report"])

# Monthly Report Tab
with tab1:
    st.subheader("Monthly Financial Report")
    
    # Get all transactions first
    all_transactions_df = get_transactions()
    
    if not all_transactions_df.empty:
        # Convert date to datetime for processing
        all_transactions_df['date'] = pd.to_datetime(all_transactions_df['date'])
        
        # Get available years and months
        years = sorted(all_transactions_df['date'].dt.year.unique(), reverse=True)
        
        # Date selection
        col1, col2 = st.columns(2)
        
        with col1:
            selected_year = st.selectbox(
                "Select Year",
                years,
                key="monthly_year"
            )
        
        with col2:
            # Get available months for selected year
            available_months = sorted(
                all_transactions_df[
                    all_transactions_df['date'].dt.year == selected_year
                ]['date'].dt.month.unique()
            )
            
            selected_month = st.selectbox(
                "Select Month",
                available_months,
                format_func=lambda x: calendar.month_name[x],
                key="monthly_month"
            )
        
        # Filter transactions for selected month
        mask = (all_transactions_df['date'].dt.year == selected_year) & \
               (all_transactions_df['date'].dt.month == selected_month)
        df = all_transactions_df[mask].copy()
        
        if not df.empty:
            # Calculate summary metrics
            total_income = df[df['type'] == 'Income']['amount'].sum()
            total_expenses = abs(df[df['type'] == 'Expense']['amount'].sum())
            net_income = total_income - total_expenses
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Income",
                    format_currency(total_income)
                )
            
            with col2:
                st.metric(
                    "Total Expenses",
                    format_currency(total_expenses)
                )
            
            with col3:
                st.metric(
                    "Net Income",
                    format_currency(net_income),
                    delta=format_currency(net_income),
                    delta_color="normal" if net_income >= 0 else "inverse"
                )
            
            with col4:
                st.metric(
                    "Transactions",
                    len(df)
                )
            
            # Category Breakdown
            st.subheader("Category Breakdown")
            
            # Calculate expense breakdown by category
            expense_by_category = df[
                df['type'] == 'Expense'
            ].groupby('category')['amount'].sum().abs()
            
            # Create pie chart for expenses
            if not expense_by_category.empty:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig_category = px.pie(
                        values=expense_by_category.values,
                        names=expense_by_category.index,
                        title="Expenses by Category"
                    )
                    fig_category.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig_category, use_container_width=True)
                
                with col2:
                    # Display category breakdown table
                    st.write("Category Details")
                    category_df = pd.DataFrame({
                        'Category': expense_by_category.index,
                        'Amount': expense_by_category.values
                    }).sort_values('Amount', ascending=False)
                    
                    category_df['Amount'] = category_df['Amount'].apply(format_currency)
                    category_df['Percentage'] = (
                        expense_by_category / expense_by_category.sum() * 100
                    ).round(1).astype(str) + '%'
                    
                    st.dataframe(
                        category_df,
                        hide_index=True,
                        use_container_width=True
                    )
            
            # Daily Spending Pattern
            st.subheader("Daily Spending Pattern")
            
            daily_expenses = df[
                df['type'] == 'Expense'
            ].groupby('date')['amount'].sum().abs()
            
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
            
            # Budget vs Actual
            st.subheader("Budget vs Actual")
            
            # Get budget thresholds
            budget_df = get_category_thresholds()
            
            if not budget_df.empty:
                budget_data = []
                
                for category in expense_by_category.index:
                    budget_limit = budget_df[
                        budget_df['category'] == category
                    ]['monthly_limit'].iloc[0] if len(budget_df[
                        budget_df['category'] == category
                    ]) > 0 else 0.0
                    
                    spent = expense_by_category[category]
                    
                    if budget_limit > 0:  # Only include categories with budget set
                        budget_data.append({
                            'Category': category,
                            'Budget': budget_limit,
                            'Spent': spent,
                            'Remaining': max(0, budget_limit - spent),
                            'Percentage': (spent / budget_limit * 100) if budget_limit > 0 else 0
                        })
                
                if budget_data:
                    budget_comparison_df = pd.DataFrame(budget_data)
                    
                    # Create budget comparison chart
                    fig_budget = go.Figure()
                    
                    fig_budget.add_trace(go.Bar(
                        name='Budget',
                        x=budget_comparison_df['Category'],
                        y=budget_comparison_df['Budget'],
                        marker_color='#2ecc71'
                    ))
                    
                    fig_budget.add_trace(go.Bar(
                        name='Actual',
                        x=budget_comparison_df['Category'],
                        y=budget_comparison_df['Spent'],
                        marker_color='#e74c3c'
                    ))
                    
                    fig_budget.update_layout(
                        title="Budget vs Actual Spending",
                        barmode='group',
                        height=400
                    )
                    
                    st.plotly_chart(fig_budget, use_container_width=True)
                    
                    # Display budget status table
                    st.write("Budget Status Details")
                    status_df = budget_comparison_df.copy()
                    status_df['Budget'] = status_df['Budget'].apply(format_currency)
                    status_df['Spent'] = status_df['Spent'].apply(format_currency)
                    status_df['Remaining'] = status_df['Remaining'].apply(format_currency)
                    status_df['Percentage'] = status_df['Percentage'].round(1).astype(str) + '%'
                    
                    st.dataframe(
                        status_df,
                        hide_index=True,
                        use_container_width=True
                    )
            else:
                st.info("No budget limits set. Set budgets in the Budget Planning page.")
            
            # Export options
            st.subheader("Export Report")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Export to CSV"):
                    try:
                        # Prepare data for export
                        export_df = df.copy()
                        export_df['date'] = export_df['date'].dt.strftime('%Y-%m-%d')
                        export_df['amount'] = export_df['amount'].apply(format_currency)
                        
                        csv = export_df.to_csv(index=False)
                        st.download_button(
                            "Download CSV",
                            csv,
                            f"monthly_report_{selected_year}_{selected_month:02d}.csv",
                            "text/csv"
                        )
                        st.success("CSV file ready for download!")
                    except Exception as e:
                        st.error(f"Error preparing CSV export: {str(e)}")
            
            with col2:
                if st.button("Export to Excel"):
                    try:
                        buffer = io.BytesIO()
                        
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            # Transactions sheet
                            export_df = df.copy()
                            export_df['date'] = export_df['date'].dt.strftime('%Y-%m-%d')
                            export_df['amount'] = export_df['amount'].apply(format_currency)
                            export_df.to_excel(writer, sheet_name='Transactions', index=False)
                            
                            # Summary sheet
                            summary_data = pd.DataFrame([
                                ['Total Income', format_currency(total_income)],
                                ['Total Expenses', format_currency(total_expenses)],
                                ['Net Income', format_currency(net_income)],
                                ['Transaction Count', len(df)]
                            ], columns=['Metric', 'Value'])
                            summary_data.to_excel(writer, sheet_name='Summary', index=False)
                            
                            # Category breakdown sheet
                            if not expense_by_category.empty:
                                category_df.to_excel(
                                    writer,
                                    sheet_name='Categories',
                                    index=False
                                )
                            
                            # Budget comparison sheet
                            if 'status_df' in locals():
                                status_df.to_excel(
                                    writer,
                                    sheet_name='Budget Status',
                                    index=False
                                )
                        
                        buffer.seek(0)
                        st.download_button(
                            "Download Excel",
                            buffer,
                            f"monthly_report_{selected_year}_{selected_month:02d}.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        st.success("Excel file ready for download!")
                    except Exception as e:
                        st.error(f"Error preparing Excel export: {str(e)}")
        else:
            st.info(f"No transactions found for {calendar.month_name[selected_month]} {selected_year}")
    else:
        st.info("No transactions found. Add some transactions to generate reports.")

# Yearly Report Tab
with tab2:
    st.subheader("Yearly Financial Report")
    
    if not all_transactions_df.empty:
        # Year selection
        selected_year = st.selectbox(
            "Select Year",
            years,
            key="yearly_year"
        )
        
        # Filter transactions for selected year
        yearly_df = all_transactions_df[
            all_transactions_df['date'].dt.year == selected_year
        ].copy()
        
        if not yearly_df.empty:
            # Calculate yearly metrics
            yearly_income = yearly_df[yearly_df['type'] == 'Income']['amount'].sum()
            yearly_expenses = abs(yearly_df[yearly_df['type'] == 'Expense']['amount'].sum())
            yearly_net = yearly_income - yearly_expenses
            
            # Display yearly summary
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Income",
                    format_currency(yearly_income)
                )
            
            with col2:
                st.metric(
                    "Total Expenses",
                    format_currency(yearly_expenses)
                )
            
            with col3:
                st.metric(
                    "Net Income",
                    format_currency(yearly_net),
                    delta=format_currency(yearly_net),
                    delta_color="normal" if yearly_net >= 0 else "inverse"
                )
            
            with col4:
                st.metric(
                    "Monthly Avg. Savings",
                    format_currency(yearly_net / 12)
                )
            
            # Monthly Trends
            st.subheader("Monthly Trends")
            
            # Calculate monthly totals
            monthly_data = yearly_df.groupby(
                [yearly_df['date'].dt.month, 'type']
            )['amount'].sum().unstack(fill_value=0)
            
            # Create monthly trends chart
            fig_trends = go.Figure()
            
            fig_trends.add_trace(go.Bar(
                name='Income',
                x=[calendar.month_name[m] for m in monthly_data.index],
                y=monthly_data['Income'],
                marker_color='#2ecc71'
            ))
            
            fig_trends.add_trace(go.Bar(
                name='Expenses',
                x=[calendar.month_name[m] for m in monthly_data.index],
                y=abs(monthly_data['Expense']),
                marker_color='#e74c3c'
            ))
            
            # Calculate and add net income line
            monthly_net = monthly_data['Income'] - abs(monthly_data['Expense'])
            
            fig_trends.add_trace(go.Scatter(
                name='Net Income',
                x=[calendar.month_name[m] for m in monthly_data.index],
                y=monthly_net,
                mode='lines+markers',
                line=dict(color='#3498db', width=2),
                marker=dict(size=8)
            ))
            
            fig_trends.update_layout(
                title=f'Monthly Trends - {selected_year}',
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
            
            st.plotly_chart(fig_trends, use_container_width=True)
            
            # Category Analysis
            st.subheader("Yearly Category Analysis")
            
            # Calculate yearly category totals
            yearly_categories = yearly_df[
                yearly_df['type'] == 'Expense'
            ].groupby('category')['amount'].sum().abs()
            
            if not yearly_categories.empty:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Create pie chart for yearly expenses
                    fig_category = px.pie(
                        values=yearly_categories.values,
                        names=yearly_categories.index,
                        title=f"Expense Distribution - {selected_year}"
                    )
                    fig_category.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig_category, use_container_width=True)
                
                with col2:
                    # Display category breakdown table
                    st.write("Category Details")
                    yearly_category_df = pd.DataFrame({
                        'Category': yearly_categories.index,
                        'Amount': yearly_categories.values
                    }).sort_values('Amount', ascending=False)
                    
                    yearly_category_df['Amount'] = yearly_category_df['Amount'].apply(format_currency)
                    yearly_category_df['Percentage'] = (
                        yearly_categories / yearly_categories.sum() * 100
                    ).round(1).astype(str) + '%'
                    
                    st.dataframe(
                        yearly_category_df,
                        hide_index=True,
                        use_container_width=True
                    )
            
            # Growth Analysis
            st.subheader("Monthly Growth Analysis")
            
            # Calculate month-over-month growth rates
            growth_rates = monthly_net.pct_change() * 100
            
            fig_growth = go.Figure()
            fig_growth.add_trace(go.Bar(
                x=[calendar.month_name[m] for m in growth_rates.index],
                y=growth_rates.values,
                marker_color=growth_rates.apply(
                    lambda x: '#2ecc71' if x >= 0 else '#e74c3c'
                )
            ))
            
            fig_growth.update_layout(
                title="Month-over-Month Growth Rate (%)",
                yaxis_title="Growth Rate (%)",
                height=400
            )
            
            st.plotly_chart(fig_growth, use_container_width=True)
            
            # Yearly Insights
            st.subheader("Yearly Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Best performing month
                best_month_idx = monthly_net.idxmax()
                best_month = {
                    'month': calendar.month_name[best_month_idx],
                    'income': monthly_data.loc[best_month_idx, 'Income'],
                    'expense': abs(monthly_data.loc[best_month_idx, 'Expense']),
                    'net': monthly_net[best_month_idx]
                }
                
                st.success(f"""
                💰 Best performing month: **{best_month['month']}**
                - Income: {format_currency(best_month['income'])}
                - Expenses: {format_currency(best_month['expense'])}
                - Net Income: {format_currency(best_month['net'])}
                """)
            
            with col2:
                # Month with lowest net income
                worst_month_idx = monthly_net.idxmin()
                worst_month = {
                    'month': calendar.month_name[worst_month_idx],
                    'income': monthly_data.loc[worst_month_idx, 'Income'],
                    'expense': abs(monthly_data.loc[worst_month_idx, 'Expense']),
                    'net': monthly_net[worst_month_idx]
                }
                
                st.error(f"""
                📉 Month with lowest net income: **{worst_month['month']}**
                - Income: {format_currency(worst_month['income'])}
                - Expenses: {format_currency(worst_month['expense'])}
                - Net Income: {format_currency(worst_month['net'])}
                """)
            
            # Additional insights
            st.markdown("### Key Takeaways")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Calculate and display growth metrics
                avg_monthly_growth = growth_rates.mean()
                positive_months = (monthly_net > 0).sum()
                
                st.info(f"""
                📊 Growth Metrics:
                - Average monthly growth: {avg_monthly_growth:.1f}%
                - Months with positive net income: {positive_months}/12
                - Average monthly income: {format_currency(yearly_income/12)}
                - Average monthly expenses: {format_currency(yearly_expenses/12)}
                """)
            
            with col2:
                # Display expense insights
                top_expense_category = yearly_categories.idxmax()
                top_expense_amount = yearly_categories.max()
                expense_percentage = (top_expense_amount / yearly_expenses * 100)
                
                st.info(f"""
                💡 Expense Insights:
                - Highest expense category: {top_expense_category}
                - Amount spent: {format_currency(top_expense_amount)}
                - Percentage of total expenses: {expense_percentage:.1f}%
                - Monthly average spending: {format_currency(yearly_expenses/12)}
                """)
            
            # Export options
            st.subheader("Export Report")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Export to CSV", key="yearly_csv"):
                    try:
                        # Prepare data for export
                        export_df = yearly_df.copy()
                        export_df['date'] = export_df['date'].dt.strftime('%Y-%m-%d')
                        export_df['amount'] = export_df['amount'].apply(format_currency)
                        
                        csv = export_df.to_csv(index=False)
                        st.download_button(
                            "Download CSV",
                            csv,
                            f"yearly_report_{selected_year}.csv",
                            "text/csv"
                        )
                        st.success("CSV file ready for download!")
                    except Exception as e:
                        st.error(f"Error preparing CSV export: {str(e)}")
            
            with col2:
                if st.button("Export to Excel", key="yearly_excel"):
                    try:
                        buffer = io.BytesIO()
                        
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            # Transactions sheet
                            export_df = yearly_df.copy()
                            export_df['date'] = export_df['date'].dt.strftime('%Y-%m-%d')
                            export_df['amount'] = export_df['amount'].apply(format_currency)
                            export_df.to_excel(writer, sheet_name='Transactions', index=False)
                            
                            # Summary sheet
                            summary_data = pd.DataFrame([
                                ['Total Income', format_currency(yearly_income)],
                                ['Total Expenses', format_currency(yearly_expenses)],
                                ['Net Income', format_currency(yearly_net)],
                                ['Monthly Avg Income', format_currency(yearly_income/12)],
                                ['Monthly Avg Expenses', format_currency(yearly_expenses/12)],
                                ['Transaction Count', len(yearly_df)]
                            ], columns=['Metric', 'Value'])
                            summary_data.to_excel(writer, sheet_name='Summary', index=False)
                            
                            # Monthly breakdown sheet
                            monthly_export = pd.DataFrame({
                                'Month': [calendar.month_name[m] for m in monthly_data.index],
                                'Income': monthly_data['Income'].apply(format_currency),
                                'Expenses': monthly_data['Expense'].abs().apply(format_currency),
                                'Net Income': monthly_net.apply(format_currency)
                            })
                            monthly_export.to_excel(writer, sheet_name='Monthly Breakdown', index=False)
                            
                            # Category breakdown sheet
                            if not yearly_categories.empty:
                                yearly_category_df.to_excel(
                                    writer,
                                    sheet_name='Categories',
                                    index=False
                                )
                            
                            # Growth analysis sheet
                            growth_df = pd.DataFrame({
                                'Month': [calendar.month_name[m] for m in growth_rates.index],
                                'Growth Rate (%)': growth_rates.round(1)
                            })
                            growth_df.to_excel(writer, sheet_name='Growth Analysis', index=False)
                        
                        buffer.seek(0)
                        st.download_button(
                            "Download Excel",
                            buffer,
                            f"yearly_report_{selected_year}.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        st.success("Excel file ready for download!")
                    except Exception as e:
                        st.error(f"Error preparing Excel export: {str(e)}")
        else:
            st.info(f"No transactions found for {selected_year}")
    else:
        st.info("No transactions found. Add some transactions to generate reports.")