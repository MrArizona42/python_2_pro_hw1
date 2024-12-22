import requests
import datetime

import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

import streamlit as st


st.title("🌤 OpenWeatherMap Weather App")

td_m = int(datetime.date.today().strftime('%m'))
st.write(f'today is {datetime.date.today().strftime('%d.%m.%Y')}')

if td_m in [1,2,12]:
    st.session_state.season = 'winter'
elif td_m in [3,4,5]:
    st.session_state.season = 'spring'
elif td_m in [6,7,8]:
    st.session_state.season = 'summer'
else:
    st.session_state.season = 'autumn'

#################################################################################
# Functions
def check_token():
    token = st.session_state.token
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": 'Moscow',
        "appid": token,
        "units": "metric"
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        st.session_state.token_passed = True
    else:
        st.session_state.token_passed = False

def get_weather():
    st.session_state.city_name = st.session_state.city_name.title()
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": st.session_state.city_name,
        "appid": st.session_state.token,
        "units": "metric"
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        st.session_state.weather_checked = True
        st.session_state.weather_data = response.json()
    else:
        st.session_state.weather_checked = False
        st.session_state.weather_data = None

st.sidebar.header("Filter Options")

st.text_input(
    "Enter your token:",
    placeholder="Enter your token ...",
    key='token',
    on_change=check_token
)

#############################################################################################
# Token check
if 'token_passed' not in st.session_state:
    st.session_state.token_passed = False

if st.session_state.token_passed:
    st.info(f"Your Token is good!")

    #########################################################################################
    # entering city
    city_name = st.text_input("Enter the city name:",
                            placeholder="e.g., London",
                            key='city_name',
                            on_change=get_weather)

    if 'weather_checked' not in st.session_state:
        st.session_state.weather_checked = False

    if st.session_state.weather_checked:
        weather_data = st.session_state.weather_data
        if weather_data:
            st.subheader(f"Weather in {st.session_state.city_name}")
            st.write(f"**Temperature:** {weather_data['main']['temp']}°C")
            st.write(f"**Feels Like:** {weather_data['main']['feels_like']}°C")
            st.write(f"**Humidity:** {weather_data['main']['humidity']}%")
            st.write(f"**Description:** {weather_data['weather'][0]['description'].capitalize()}")
        else:
            st.error("Could not fetch weather data. Please check the city name.")

    ###############
    # File uploader
    uploaded_file = st.file_uploader("Upload your weather dataset (.csv)", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        ############################################################################################
        # Preprocessing
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        df['year'] = df['timestamp'].dt.year
        df['day_of_year'] = df['timestamp'].dt.day_of_year

        by_season = df.groupby(['city', 'season'])['temperature'].agg(['mean', 'std'])

        by_season['top_95'] = by_season['mean'] + by_season['std'] * 2
        by_season['bot_95'] = by_season['mean'] - by_season['std'] * 2

        df = pd.merge(
            df, by_season,
            left_on=['city', 'season'],
            right_index=True,
            how='outer'
        )
        
        df['is_outlier'] = (df['temperature'] > df['top_95']) | (df['temperature'] < df['bot_95'])

        ##############################################################################################
        # Sidebar
        cities = st.sidebar.multiselect("Select Cities", df['city'].unique())
        cities.append(st.session_state.city_name)

        st.sidebar.info('You can select cities from your dataset')

        start_date = df['timestamp'].dt.date.min()
        start_date = str(start_date)
        end_date = df['timestamp'].dt.date.max()
        end_date = str(end_date)

        date_range = st.sidebar.select_slider(
            "Select date range:",
            options=df['timestamp'].sort_values().astype('str'),
            value=(start_date, end_date)
        )

        st.sidebar.info('Select the time range for analysis')

        ##########################
        # Filtered df
        filtered_df = df.copy()
        filtered_df = filtered_df[filtered_df['city'].isin(cities)]

        filtered_df = filtered_df[(filtered_df['timestamp'] >= pd.to_datetime(date_range[0])) &
                                (filtered_df['timestamp'] <= pd.to_datetime(date_range[1]))]
        
        ##############################################################################################
        # Rolling mean
        roll = filtered_df.set_index('timestamp').groupby('city')['temperature'].rolling(window=30, center=True).mean()

        roll = roll.reset_index()
        roll['year'] = roll['timestamp'].dt.year
        roll['day_of_year'] = roll['timestamp'].dt.day_of_year

        ##############################################################################################
        # Display raw data
        st.subheader("Raw Data")
        st.dataframe(df)

        # Display filtered data
        st.subheader("Filtered Data")
        st.dataframe(filtered_df)

        ##############################################################################################
        # Visualizations
        if filtered_df.shape[0] > 0:
            ##############
            # Scatter plot
            fig1 = sns.relplot(
                data=filtered_df,
                x='day_of_year',
                y='temperature',
                hue='is_outlier',
                col='city',
                col_wrap=2,
                alpha=0.5
            )

            fig1.figure.suptitle('Daily temperature through the years', y=1.05, fontsize=16)

            for ax in fig1.axes.flat:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%B'))
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                plt.setp(ax.get_xticklabels(), rotation=90, ha='left')

            st.pyplot(fig1)

            if filtered_df.shape[0] >= 30:
                ###################
                # Rilling mean plot
                fig2 = sns.relplot(
                    data=roll,
                    x='day_of_year',
                    y='temperature',
                    hue='city',
                    col='city',
                    col_wrap=2,
                    kind='line',
                    alpha=0.5
                )

                fig2.figure.suptitle('Temperature with rolling mean with 30-day window', y=1.05, fontsize=16)

                for ax in fig2.axes.flat:
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%B'))
                    ax.xaxis.set_major_locator(mdates.MonthLocator())
                    plt.setp(ax.get_xticklabels(), rotation=90, ha='left')

                st.pyplot(fig2)
        
            ##########
            # Bar plot
            avg_temp_by_season = filtered_df.groupby(['city', 'season']).agg(
                mean_temperature=('temperature', 'mean'),
                std=('temperature', 'std')
            ).reset_index()
            
            season_order = ['spring', 'summer', 'autumn', 'winter']

            fig3 = sns.catplot(
                data=avg_temp_by_season,
                x='season',
                y='mean_temperature',
                hue='city',
                col='city',
                col_wrap=2,
                kind='bar',
                order=season_order
            )

            for ax, city in zip(fig3.axes.flat, avg_temp_by_season['city'].unique()):
                city_data = avg_temp_by_season[avg_temp_by_season['city'] == city]
                city_data = city_data.set_index('season').loc[season_order].reset_index()
                lower_error = city_data['std'] * 2
                upper_error = city_data['std'] * 2
                ax.errorbar(
                    x=range(len(city_data['season'])),
                    y=city_data['mean_temperature'], 
                    yerr=[lower_error, upper_error],
                    fmt='none', 
                    ecolor='black', 
                    capsize=3
                )

            fig3.figure.suptitle('Average temperature in different seasons', y=1.05, fontsize=16)

            st.pyplot(fig3)

            ############
            # Statistics
            if st.session_state.season in filtered_df['season'].unique():
                filtered_by_season = filtered_df.groupby(['city', 'season'])['temperature'].agg(['mean', 'std'])

                filtered_by_season['top_95'] = filtered_by_season['mean'] + filtered_by_season['std'] * 2
                filtered_by_season['bot_95'] = filtered_by_season['mean'] - filtered_by_season['std'] * 2

                min_normal = filtered_by_season.loc[(st.session_state.city_name, st.session_state.season), 'bot_95']
                max_normal = filtered_by_season.loc[(st.session_state.city_name, st.session_state.season), 'top_95']

                st.subheader("Insights")
                st.write(f"Highest temperature in {st.session_state.city_name} within the 95% Confidence interval: {max_normal:.1f}°C")
                st.write(f"Lowest temperature in {st.session_state.city_name} within the 95% Confidence interval: {min_normal:.1f}")
                if weather_data['main']['temp'] < min_normal:
                    current_temp_state = 'incredibly low'
                elif weather_data['main']['temp'] > max_normal:
                    current_temp_state = 'incredibly high'
                else:
                    current_temp_state = 'within normal range'
                st.write(f"Current temperature is: {current_temp_state}")
            else:
                st.warning(f"Not enough data about current season. Please, select a wider interval that includes {st.session_state.season} months")

        #################
        # Download button
        st.download_button(
            label="Download Filtered Data",
            data=filtered_df.to_csv(index=False),
            file_name="filtered_weather_data.csv",
            mime="text/csv"
        )