import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Title
st.title("BP Readings Analysis")

# Step 1: Upload the CSV/Excel file
uploaded_file = st.file_uploader("Upload your BP readings CSV/Excel file", type=['csv', 'xlsx'])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    # Filter the dataframe to include only rows where 'rec_id' contains '-B'
    df = df[df['rec_id'].str.contains('-B', na=False)]

    # Check for duplicate rec_id values in df_bp
    duplicate_rec_ids_bp = df[df['rec_id'].duplicated()]['rec_id']
    duplicate_rec_ids_bp_count = duplicate_rec_ids_bp.count()
    st.markdown(f"**Number of duplicate rec_ids in df_bp: {duplicate_rec_ids_bp_count}**")

    if duplicate_rec_ids_bp_count > 0:
        st.markdown("**Duplicate rec_ids in df_bp:**")
        st.write(duplicate_rec_ids_bp)
    
    # Step 2: Ensure 'time_1' column is in datetime format
    df['time_1'] = pd.to_datetime(df['time_1'])

    # Step 3: User inputs for date range
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

    # Step 4: Function to filter the DataFrame based on user-provided date range
    def filter_by_date(df, start_date, end_date):
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1)
        mask = (df['time_1'] >= start_date) & (df['time_1'] < end_date)
        return df[mask]

    # Step 5: Filter the DataFrame based on the selected date range
    filtered_df = filter_by_date(df, start_date, end_date)

    # Step 6: Count number of rows in filtered dataframe
    total_participants = len(filtered_df)
    st.markdown(f"**Total number of participants until {end_date} from {start_date}:** {total_participants}")

    # Step 7: Count and report participants with null values in 'good_readings'
    null_good_readings = filtered_df['good_readings'].isnull().sum()
    st.markdown(f"**Number of participants who didn't get 3 required readings among {total_participants}:** {null_good_readings}")
    st.markdown("---")

    # Step 8: User selection: "Only Good Readings" or "All"
    reading_option = st.radio("Select readings to include", ["Only good readings", "All"])

    # Step 9: Filter based on the user's selection
    if reading_option == "Only good readings":
        filtered_df = filtered_df.dropna(subset=['good_readings'])

    # Step 10: Count number of sits for each participant
    def count_sits(row):
        for i in range(1, 11):
            if pd.isnull(row[f'sys_{i}']):
                return i - 1
        return 10

    filtered_df['total_sits'] = filtered_df.apply(count_sits, axis=1)

    # Step 11: Count good and poor signals for each participant
    def count_signals(row):
        good_signals = row.filter(like='ths_pf_').tolist()
        good_count = good_signals.count('Good')
        poor_count = good_signals.count('Poor')
        return good_count, poor_count

    signal_counts = filtered_df.apply(count_signals, axis=1)
    filtered_df['good_sits'] = signal_counts.apply(lambda x: x[0])
    filtered_df['poor_sits'] = signal_counts.apply(lambda x: x[1])

    # Step 12: Define a function to calculate statistics
    def calculate_statistics(df):
        cumulative_total_sits = df['total_sits'].sum()
        total_good_sits = df['good_sits'].sum()
        total_poor_sits = df['poor_sits'].sum()
        average_total_sits = df['total_sits'].mean()
        average_poor_sits = df['poor_sits'].mean()
        good_sits_percentage = (total_good_sits / cumulative_total_sits) * 100
        poor_sits_percentage = (total_poor_sits / cumulative_total_sits) * 100
        return {
            "1. Cumulative Total Sits": cumulative_total_sits,
            "2. Total Good Sits": total_good_sits,
            "3. Total Poor Sits": total_poor_sits,
            "4. Average Total Sits": round(average_total_sits, 2),
            "5. Average Poor Sits": round(average_poor_sits, 2),
            "6. Good Sits Percentage (%)": round(good_sits_percentage, 2),
            "7. Poor Sits Percentage (%)": round(poor_sits_percentage, 2)
        }

    stats = calculate_statistics(filtered_df)
    #st.markdown("**Statistics:**")
    st.markdown("<h2 style='font-size: larger;'>Statistics:</h2>", unsafe_allow_html=True)
    for key, value in stats.items():
        st.markdown(f"**{key}:** {value}")

    # Step 13: Define a function to get Extra sits due to BP readings not within the required range
    def calculate_extra_sits(row):
        good_signals = row.filter(like='ths_pf_').tolist()
        good_sits = good_signals.count('Good')
        extra_sits = max(0, good_sits - 3)
        return extra_sits

    filtered_df['extra_sits'] = filtered_df.apply(calculate_extra_sits, axis=1)
    avg_extra_sits = round(filtered_df['extra_sits'].mean(), 2)
    st.markdown(f"**8. Average Extra Sits:** {avg_extra_sits}")

    # Visualization Heading
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h2 style='font-size: larger;'>Visualizations:</h2>", unsafe_allow_html=True)

    # Step 14: Visualization functions
    def plot_bar_chart(series, title, xlabel, ylabel, definition):
        plt.figure(figsize=(10, 6))
        counts = series.value_counts().sort_index()
        sns.barplot(x=counts.index, y=counts.values, palette='viridis')
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.ylim(0, counts.max() * 1.2)
        for index, value in enumerate(counts):
            plt.text(index, value + 0.05, f'{value} ({value / len(series) * 100:.2f}%)', ha='center', color='black')
        st.pyplot(plt)
        st.markdown(f"**Definition:** {definition}")

    def create_table(data, column_name):
        table_data = data[data[column_name] > 0][['rec_id', column_name]].reset_index(drop=True)
        table_data = table_data.sort_values(by=column_name, ascending=False)
        return table_data

    # Plotting Frequency of Total Sits
    plot_bar_chart(filtered_df['total_sits'], "Frequency of Total Sits", "Number of Sits", "Frequency", 
                   "Total sits refers to the total number of sits required for each participant to achieve three acceptable BP readings with good signals.")

    # Plotting Frequency of Poor Sits
    plot_bar_chart(filtered_df['poor_sits'], "Frequency of Poor Sits", "Number of Poor Sits", "Frequency", 
                   "Poor sits refer to the number of sits where the signal strength was marked as 'Poor'.")
    poor_sits_table = create_table(filtered_df, 'poor_sits')
    st.markdown("**Table for Poor Sits**")
    st.dataframe(poor_sits_table)

    # Plotting Frequency of Extra Sits
    plot_bar_chart(filtered_df['extra_sits'], "Frequency of Extra Sits", "Number of Extra Sits", "Frequency", 
                   "Extra sits refer to the number of additional sits required because the BP readings were not within the required range, despite having good signal strength.")
    extra_sits_table = create_table(filtered_df, 'extra_sits')
    st.markdown("**Table for Extra Sits**")
    st.dataframe(extra_sits_table)
