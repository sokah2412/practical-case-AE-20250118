import pandas as pd
import streamlit as st

# Load datasets. Only load columns which are useful after
journeys = pd.read_csv(
    "data/journeys.csv", usecols=['driver_uid', 'status', 'route_id', 'cancel_reason', '_id'])
routes = pd.read_csv(
    "data/routes.csv", usecols=['driver_uid', 'status', '_id'])

# Get filters enum base on values in the datasets
journeys_status_enum = list(journeys['status'].unique())
routes_status_enum = list(routes['status'].unique())

# Define sidebar
with st.sidebar:
    routes_status = st.multiselect(
        "Status du trajet", options=routes_status_enum, default="DONE")
    journeys_status = st.multiselect(
        "Status du covoiturage", options=journeys_status_enum, default="VALIDATED")
    min_passengers = st.slider(
        "Nombre minimal de passage par trajet", value=1, max_value=5)

# Filtered datasets to apply transform only on the wanted data subsets
filtered_journeys = journeys[journeys.status.isin(journeys_status)]
filtered_routes = routes[routes.status.isin(routes_status)]

# Get number of passenger in each routes
nb_passengers_by_routes_id = filtered_journeys.groupby('route_id')\
    .count()[['_id']]\
    .reset_index()
nb_passengers_by_routes = filtered_routes.merge(
    nb_passengers_by_routes_id, left_on="_id", right_on="route_id", how='left').rename(columns={"_id_y": "nb_passengers"})
nb_passengers_by_routes.loc[pd.isna(
    nb_passengers_by_routes.nb_passengers), "nb_passengers"] = 0

# Count covoit by driver. A covoit is defined as routes with minimum of {min_passengers} passengers
covoit_routes = nb_passengers_by_routes[nb_passengers_by_routes.nb_passengers >= min_passengers]
nb_covoit_by_driver = covoit_routes.groupby('driver_uid').count()[
    ['_id_x']].reset_index()


# Format data to get number of drivers who made at least x covoits, for each x
nb_covoits_frequency = nb_covoit_by_driver.groupby('_id_x').count().reset_index()\
    .rename(columns={"_id_x": "nb_covoits_by_driver", "driver_uid": "nb_driver"})
nb_covoits_frequency['inverted_cumsum'] = nb_covoits_frequency.loc[::-
                                                                   1, 'nb_driver'].cumsum()[::-1]

# Compute drop after bonus
nb_driver_at_least_10 = nb_covoits_frequency.loc[nb_covoits_frequency.nb_covoits_by_driver ==
                                                 10, "inverted_cumsum"].values[0]
nb_driver_at_least_11 = nb_covoits_frequency.loc[nb_covoits_frequency.nb_covoits_by_driver ==
                                                 11, "inverted_cumsum"].values[0]
bonus_drop = 1 - (nb_driver_at_least_11 / nb_driver_at_least_10)

# Displayed data
st.write("### Nombre de conducteurs ayant réalisé au moins x trajets")
st.line_chart(
    nb_covoits_frequency,
    x="nb_covoits_by_driver", x_label="nombre de trajets",
    y="inverted_cumsum", y_label="nombre de conducteurs",
)
st.write(
    f"Nombre de trajets correspondant aux filtres : {covoit_routes.shape[0]}")
st.write(
    f"Nombre de conducteurs ayant fait x trajets correspondant aux filtres : {nb_covoits_frequency['nb_driver'].sum()}")
st.write(
    f"=> Perte de {int(bonus_drop * 100)}% des conducteurs après l'obtention de la prime")
