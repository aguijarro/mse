import random
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# List of vendors
vendors_list = ['Encompass', 'Marcone', 'Reliable']

# Score of Vendors
vendors_score = {
    "vendor_trust_score": {
        "Amazon": 10,
        "Marcone": 10,
        "Encompass": 10,
        "Reliable": 5,
        "Tribbles": 5
    },
    "shipping_speed_score": {
        "Marcone": 25,
        "Encompass": 25,
        "Amazon": 0,
        "Reliable": 0,
        "Tribbles": 0
    },
    "returnability_score": {
        "Amazon": 100,
        "Marcone": 100,
        "Encompass": 100,
        "Reliable": 0,
        "Tribbles": 0
    }
}


def transform_column(column):
    column = column.str.replace('$', '', regex=False)
    column = column.str.replace(',', '', regex=False)
    return column.astype(float)


def transform_uploaded_file(df_uploaded_file):
    for column_name in ['Encompass', 'Marcone', 'Reliable']:
        df_uploaded_file[column_name] = transform_column(df_uploaded_file[column_name])
    return df_uploaded_file


def generate_random_order_id():
    random_number = random.randint(10000, 99999)
    return random_number


def generate_current_datetime():
    return datetime.now()


def add_vendor_scores(df, config, vendors):
    for vendor in vendors:
        add_vendor_columns(df, config, vendor)
    return df


def add_vendor_columns(df, config, vendor):
    for score_type, scores in config.items():
        column_name = f"{score_type}_{vendor}"
        score = scores.get(vendor, 0)
        df[column_name] = score/100


def calculate_cost_scores(df, vendors):
    df['best_price'] = df[vendors].min(axis=1)
    for vendor in vendors:
        cost_score_col = f"cost_score_{vendor}"
        df[cost_score_col] = (df['best_price'] / df[vendor])
    return df


def calculate_total_score_calculation(df, vendors, cost_weight, shipping_speed_weight,
                                      returnability_weight, vendor_trust_weight):
    for vendor in vendors:
        total_score_col = f"total_score_{vendor}"
        df[total_score_col] = (df[f'cost_score_{vendor}'] * int(cost_weight) / 100
                               + df[f'shipping_speed_score_{vendor}'] * int(shipping_speed_weight) / 100
                               + df[f'vendor_trust_score_{vendor}'] * int(vendor_trust_weight) / 100
                               + df[f'returnability_score_{vendor}'] * int(returnability_weight) / 100) * 100
    return df


# Function to highlight the maximum value in each row
def highlight_max(s):
    is_max = s == s.max()
    return ['background-color: green' if v else '' for v in is_max]



def generate_sample_data(df_for_sample, number_of_rows, cost_weight,
                     shipping_speed_weight, returnability_weight, vendor_trust_weight,
                     technicians_number_parameter, days_number_parameter,
                     same_day_parameter, day_1_parameter, day_2_parameter, day_3_parameter,
                     day_4_parameter):
    order_id = generate_random_order_id()
    order_timestamp = generate_current_datetime()
    returnability_values = ['Yes', 'No']
    shipping_speed_values = ['same day', '1 day', '2 days', '3 days', '4 days+']

    df_sample = df_for_sample.sample(int(number_of_rows), weights='Installs', random_state=1)
    df_sample['order_id'] = order_id
    df_sample['order_timestamp'] = order_timestamp
    # df_sample['returnability'] = np.random.choice(returnability_values, size=len(df_sample))
    # df_sample['shipping_speed_values'] = np.random.choice(shipping_speed_values, size=len(df_sample))

    # Add scores to the dataframe
    df_sample = add_vendor_scores(df_sample, vendors_score, vendors_list)
    # Calculate cost scores
    df_sample = calculate_cost_scores(df_sample, vendors_list)
    # Calculate total scores
    df_sample = calculate_total_score_calculation(df_sample, vendors_list, cost_weight, shipping_speed_weight,
                                      returnability_weight, vendor_trust_weight)
    # Apply the highlight_max function to the dataframe
    df_sample = df_sample.style.apply(highlight_max, subset=[f"total_score_{vendor}" for vendor in vendors_list], axis=1)

    return df_sample


def main():

    logo_path = "../assets/images/sears.png"  # Replace with your logo file path

    ## Sidebar functionality

    st.sidebar.markdown("### Orders Generator")
    number_of_parts = st.sidebar.text_input(label="Number of Parts", placeholder="0", key="Number of Parts")

    st.sidebar.markdown("### Criteria Weights")
    cost_weight = st.sidebar.text_input(label="Price", placeholder="45", key="Price")
    shipping_speed_weight = st.sidebar.text_input(label="Shipping speed", placeholder="40", key="Shipping speed")
    returnability_weight = st.sidebar.text_input(label="Returnability", placeholder="5", key="Returnability")
    vendor_trust_weight = st.sidebar.text_input(label="Vendor trust", placeholder="10", key="Vendor trust")

    st.sidebar.markdown("### Simulation Parameters")
    technicians_number_parameter = st.sidebar.text_input(label="Number of Technicians", placeholder="200", key="Number of Technicians")
    days_number_parameter = st.sidebar.text_input(label="Number of Days", placeholder="2", key="Number of Days")

    st.sidebar.markdown("#### Shipping speed scale")
    same_day_parameter = st.sidebar.text_input(label="Same day", placeholder="100", key="Same day")
    day_1_parameter = st.sidebar.text_input(label="1 day", placeholder="75", key="1 day")
    day_2_parameter = st.sidebar.text_input(label="2 days", placeholder="50", key="2 days")
    day_3_parameter = st.sidebar.text_input(label="3 days", placeholder="25", key="3 days")
    day_4_parameter = st.sidebar.text_input(label="4 days+", placeholder="0", key="4 days+")


    # Main Content

    st.title('Multisourcing Decision Engine')

    st.markdown(""" 
     * Use the menu at left to select data and set plot parameters
     * Your plots will appear below
    """)

    # st.header("Upload your CSV data file")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, sep=';')
        # transform df
        df = transform_uploaded_file(df)
        st.write("Uploaded CSV file:")
        st.dataframe(df.head(5))

        if st.button("Generate Order"):
            # Validate input parameters
            input_params = [
                number_of_parts, cost_weight, shipping_speed_weight,
                returnability_weight, vendor_trust_weight, technicians_number_parameter,
                days_number_parameter, same_day_parameter, day_1_parameter,
                day_2_parameter, day_3_parameter, day_4_parameter
            ]

            # Check if all input parameters are provided and valid
            if all(input_params) and int(number_of_parts) > 0:
                # Create sample data
                sample_df = generate_sample_data(
                    df, number_of_parts, cost_weight, shipping_speed_weight,
                    returnability_weight, vendor_trust_weight, technicians_number_parameter,
                    days_number_parameter, same_day_parameter, day_1_parameter,
                    day_2_parameter, day_3_parameter, day_4_parameter
                )
                st.write("Sample DataFrame:")
                st.dataframe(sample_df)
            else:
                st.write(
                    "Please provide valid inputs for all parameters and ensure the number of parts is greater than zero.")


if __name__ == "__main__":
    main()
