import math
import streamlit as st
import streamlit.components.v1 as components
from app_requests import *
import matplotlib.pyplot as plt
import seaborn as sns
from colour import Color

#  streamlit run /Users/julie/PycharmProjects/home-credit-front/streamlit_app.py

# %% Init

st.set_page_config(page_title='Prêt à dépenser', page_icon=":bank:", layout='wide', initial_sidebar_state='auto')
colors = list(Color("green").range_to(Color("red"), 10))

all_features = get_features_list()

# %% Sidebar filtering

st.sidebar.header('Filters')
selected_features = st.sidebar.multiselect(label='Filter by :', options=all_features)

filters = dict()
active_filters = dict()

for feature in selected_features:
    feature_type, feature_values = get_possible_values(feature)
    if feature_type == 'float64':
        filters[feature] = st.sidebar.slider(label=feature, value=(min(feature_values), max(feature_values)))
        if filters[feature] != (min(feature_values), max(feature_values)):
            active_filters[feature] = (feature_type, filters[feature])
    else:
        filters[feature] = st.sidebar.multiselect(options=feature_values, label=feature)
        if set(filters[feature]) not in [set(feature_values), set()]:
            active_filters[feature] = (feature_type, filters[feature])

# %% Main page content

list_client_ids, targets = get_list_client_ids(active_filters)

nb_available_clients = len(list_client_ids)
if nb_available_clients >= 1:
    client_selector_container, proportion_display_container = st.columns([6, 1])

    # Client Selector
    client_selector_container.subheader('Select a client')
    client_selector_label = str('{:,}'.format(nb_available_clients)) + ' clients matching filters'
    client_selector_container.caption(client_selector_label)
    index_client = client_selector_container.select_slider(options=[None] + list_client_ids, label='')
    valid_client_data = False

    # Current Filters Proportion display
    proportion_display_container.caption('Clients matching filters')
    fig_targets = plt.figure(figsize=(3, 3))
    plt.pie(targets.values(), labels=targets.keys(), autopct='%.0f%%')
    proportion_display_container.pyplot(fig_targets, height=20)

    if index_client is not None:
        valid_prediction, value_prediction, explanation_prediction = get_prediction_client(int(index_client))
        if valid_prediction:
            prediction_color = colors[int((value_prediction * 10) // 1)]
            st.markdown('<p style="color:' + str(prediction_color) + '">Bankrupcy prediction : ' + '{:.2f}%</p>'.format(
                100 * value_prediction), unsafe_allow_html=True)
            components.html(explanation_prediction, height=700)
        else:
            client_selector_container.caption('could not predict')

        valid_client_data, client_data = get_client_data(index_client)

    # Displayed features Selector
    buttons = dict()
    st.sidebar.header('Features to display')
    for i, feature in enumerate(all_features[:20]):
        buttons[feature] = st.sidebar.checkbox(feature)

    features_chosen = [feature for feature in buttons if buttons[feature]]
    nb_features_chosen = len(features_chosen)

    # Features plot
    if len(features_chosen):
        nb_plot_rows = int(math.ceil(nb_features_chosen / 2))
        fig_features, ax = plt.subplots(nb_plot_rows, 2)
        fig_features.set_figheight(5 * nb_plot_rows)
        fig_features.set_figwidth(15)

        for feature_index, feature in enumerate(features_chosen):
            index_col = feature_index % 2
            index_row = feature_index // 2
            this_ax = ax[index_col] if nb_plot_rows == 1 else ax[index_row][index_col]
            feature_data = get_feature_data(feature, active_filters)

            if feature_data['feature_type'] == 'float64' and max([u % 1 for u in set(feature_data['feature'])]) == 0:
                sns.kdeplot(x=feature_data['feature'], hue=feature_data['TARGET'], ax=this_ax, common_norm=False,
                            bw_adjust=2)
            elif feature_data['feature_type'] == 'float64':
                sns.kdeplot(x=feature_data['feature'], hue=feature_data['TARGET'], ax=this_ax, common_norm=False)
            else:
                sns.histplot(x=feature_data['feature'], hue=feature_data['TARGET'], ax=this_ax,
                             multiple="fill", discrete=True, shrink=.8, common_norm=False)
                if set(feature_data['feature']) == {0, 1}:
                    this_ax.set_xticks([0, 1])

            this_ax.set_yticklabels([])
            this_ax.set_title(feature)
            this_ax.set_ylabel('')
            if valid_client_data:
                # noinspection PyUnboundLocalVariable
                this_ax.axvline(x=client_data[feature], color="red", ls="--", lw=2.5)

        st.pyplot(fig_features)

else:
    st.write('No client found')
