import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Maximum number of orders a user can simulate
max_orders_simulation = 2000

# List of vendors
vendors_list = ['Encompass', 'Marcone', 'Reliable', 'Amazon', 'ItemMaster']

# Attributes of Vendors
vendors_attributes = {
    "vendor_trust_score": {
        "Amazon": 100,
        "Marcone": 100,
        "Encompass": 100,
        "ItemMaster": 50,
        "Reliable": 50
    },
    "average_shipping_speed": {
        "Marcone": 2,
        "Encompass": 4,
        "Amazon": 1,
        "ItemMaster": 5,
        "Reliable": 4
    },
    "returnability_score": {
        "Amazon": 100,
        "Marcone": 100,
        "Encompass": 100,
        "ItemMaster": 0,
        "Reliable": 0
    }
}


def transform_column(column):
    column = column.str.replace('$', '', regex=False)
    column = column.str.replace(',', '', regex=False)
    return column.astype(float)


def transform_uploaded_file(df_uploaded_file):
    for column_name in ['Encompass', 'Marcone', 'Reliable', 'Amazon']:
        df_uploaded_file[column_name] = transform_column(df_uploaded_file[column_name])
    return df_uploaded_file


def add_vendor_scores(df, config, vendors):
    for vendor in vendors:
        add_vendor_columns(df, config, vendor)
    return df


def add_vendor_columns(df, config, vendor):
    for score_type, scores in config.items():
        # Shipping speed need a calculation see: calculate_shipping_scores method
        if score_type != "average_shipping_speed":
            column_name = f"{score_type}_{vendor}"
            score = scores.get(vendor, 0)
            df[column_name] = score / 100


def calculate_shipping_scores(df, vendors, same_day_parameter, day_1_parameter, day_2_parameter, day_3_parameter, day_4_parameter):
    for vendor in vendors:
        shipping_score_col = f"shipping_score_{vendor}"
        if vendors_attributes["average_shipping_speed"][vendor] == 0:
            df[shipping_score_col] = int(same_day_parameter)/100
        elif vendors_attributes["average_shipping_speed"][vendor] == 1:
            df[shipping_score_col] = int(day_1_parameter)/100
        elif vendors_attributes["average_shipping_speed"][vendor] == 2:
            df[shipping_score_col] = int(day_2_parameter)/100
        elif vendors_attributes["average_shipping_speed"][vendor] == 3:
            df[shipping_score_col] = int(day_3_parameter)/100
        else:
            df[shipping_score_col] = int(day_4_parameter)/100
    return df


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
                               + df[f'shipping_score_{vendor}'] * int(shipping_speed_weight) / 100
                               + df[f'vendor_trust_score_{vendor}'] * int(vendor_trust_weight) / 100
                               + df[f'returnability_score_{vendor}'] * int(returnability_weight) / 100) * 100
    return df


# Function to highlight the maximum value in each row
def highlight_max(s):
    is_max = s == s.max()
    return ['background-color: green' if v else '' for v in is_max]


def generate_sample_data(df_for_sample, number_of_rows, cost_weight,
                         shipping_speed_weight, returnability_weight, vendor_trust_weight,
                         same_day_parameter, day_1_parameter, day_2_parameter, day_3_parameter,
                         day_4_parameter, random_seed):

    # Sample the source file based on the number of Installs
    df_sample = df_for_sample.sample(int(number_of_rows), replace=True, weights='Installs', random_state=int(random_seed))

    # Add scores to the dataframe
    df_sample = add_vendor_scores(df_sample, vendors_attributes, vendors_list)
    
    # Calculate cost scores
    df_sample = calculate_cost_scores(df_sample, vendors_list)

    # Calculate shipping score
    df_sample = calculate_shipping_scores(df_sample, vendors_list, same_day_parameter, day_1_parameter, day_2_parameter, day_3_parameter, day_4_parameter)


    # Calculate total scores
    df_sample = calculate_total_score_calculation(df_sample, vendors_list, cost_weight, shipping_speed_weight,
                                                  returnability_weight, vendor_trust_weight)

    df_partial_result = df_sample[['Part', 'Title'] + [f"total_score_{vendor}" for vendor in vendors_list]]
    df_result_table = df_partial_result.melt(
        id_vars=['Part', 'Title'],
        var_name="Order Won",
        value_name="Value")

    # Apply the highlight_max function to the dataframe
    df_sample.reset_index(inplace=True)
    df_sample = df_sample.style.apply(highlight_max, subset=[f"total_score_{vendor}" for vendor in vendors_list],
                                      axis=1)

    return df_sample, df_result_table


def main():
    logo_path = "../assets/images/sears.png"  # Replace with your logo file path

    ## Sidebar functionality

    st.sidebar.markdown("### Orders Generator")
    number_of_orders = st.sidebar.text_input(label="Number of Orders", value="100", key="Number of Orders")
    random_seed = st.sidebar.text_input(label="Random Seed", value="1", key="Random Seed")

    st.sidebar.markdown("### Criteria Weights")
    cost_weight = st.sidebar.text_input(label="Price", value="45", key="Price")
    shipping_speed_weight = st.sidebar.text_input(label="Shipping speed", value="40", key="Shipping speed")
    returnability_weight = st.sidebar.text_input(label="Returnability", value="5", key="Returnability")
    vendor_trust_weight = st.sidebar.text_input(label="Vendor trust", value="10", key="Vendor trust")

    st.sidebar.markdown("#### Shipping speed scale")
    same_day_parameter = st.sidebar.text_input(label="Same day", value="100", key="Same day")
    day_1_parameter = st.sidebar.text_input(label="1 day", value="75", key="1 day")
    day_2_parameter = st.sidebar.text_input(label="2 days", value="50", key="2 days")
    day_3_parameter = st.sidebar.text_input(label="3 days", value="25", key="3 days")
    day_4_parameter = st.sidebar.text_input(label="4 days+", value="0", key="4 days+")

    # Main Content

    st.title('Multisourcing Decision Engine')
    st.markdown(f"""Current known limitations:  
                - We do not generate OEM parts only orders  
                - One part per order  
                - Maximum number of orders is {max_orders_simulation}
                """)
    st.markdown("Parameters", help=str(vendors_attributes))

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
                number_of_orders, cost_weight, shipping_speed_weight,
                returnability_weight, vendor_trust_weight, same_day_parameter, day_1_parameter,
                day_2_parameter, day_3_parameter, day_4_parameter, random_seed
            ]

            # Check if all input parameters are provided and valid
            if all(input_params) and int(number_of_orders) > 0 and int(number_of_orders) <= max_orders_simulation:
                # Create sample data

                sample_df, result_table_df = generate_sample_data(
                    df, number_of_orders, cost_weight, shipping_speed_weight,
                    returnability_weight, vendor_trust_weight, same_day_parameter, day_1_parameter,
                    day_2_parameter, day_3_parameter, day_4_parameter, random_seed
                )
                st.markdown("***")
                st.write("Calculations Data:")
                st.dataframe(sample_df)

                st.markdown("***")
                st.write("Result Table:")
                st.dataframe(result_table_df)

            else:
                st.write(
                    f"Please provide valid inputs for all parameters and ensure the number of parts is greater than zero. Maximum number of orders is {max_orders_simulation}.")


if __name__ == "__main__":
    main()
