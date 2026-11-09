"""Frontend for the Group 8 house price API."""
import math
import os

import requests
import streamlit as st


FIELDS = [
    ('OverallQual', 'Overall quality (1–10)', 1, 10, 6),
    ('GrLivArea', 'Above-ground living area (sq ft)', 100, 20000, 1473),
    ('TotalBsmtSF', 'Basement area (sq ft)', 0, 20000, 997),
    ('GarageCars', 'Garage capacity (cars)', 0, 10, 2),
    ('YearBuilt', 'Year built', 1800, 2010, 1972),
    ('FullBath', 'Full bathrooms above ground (count)', 0, 10, 2),
    ('LotArea', 'Lot area (sq ft)', 100, 1000000, 9600),
    ('OverallCond', 'Overall condition (1–10)', 1, 10, 5),
]
NEIGHBORHOODS = ('Blmngtn', 'Blueste', 'BrDale', 'BrkSide', 'ClearCr', 'CollgCr', 'Crawfor',
                 'Edwards', 'Gilbert', 'IDOTRR', 'MeadowV', 'Mitchel', 'NAmes', 'NPkVill',
                 'NWAmes', 'NoRidge', 'NridgHt', 'OldTown', 'SWISU', 'Sawyer', 'SawyerW',
                 'Somerst', 'StoneBr', 'Timber', 'Veenker')
KITCHEN_LABELS = {'Ex': 'Excellent', 'Gd': 'Good', 'TA': 'Typical', 'Fa': 'Fair'}

st.set_page_config(page_title='INTELLIGENT HOUSE PRICE PREDICTION', page_icon=':material/home:')
st.title('INTELLIGENT HOUSE PRICE PREDICTION')
st.caption('Group 8 · FUSE AI 201 · Sub-module 6.5')
st.info('This demo estimates historical sale prices in Ames, Iowa, using sales from 2006–2010. Consult a qualified appraiser for a current property valuation.')
with st.expander('Who this tool is for'):
    st.write('Classmates and reviewers can compare how property details affect the model’s estimate. Unusual homes can have larger errors. The estimate has no prediction interval and should not be the sole basis for a purchase or lending decision.')

with st.form('house'):
    st.subheader('House details')
    st.write('The form starts with an example house. Edit any details and select Estimate price.')
    house = {}
    for field, label, minimum, maximum, default in FIELDS:
        house[field] = st.number_input(label, min_value=minimum, max_value=maximum,
                                       value=default, step=1, key=field,
                                       help=f'Enter a whole number from {minimum:,} to {maximum:,}.')
    house['Neighborhood'] = st.selectbox('Ames neighborhood code', NEIGHBORHOODS,
                                         index=NEIGHBORHOODS.index('NAmes'), key='Neighborhood')
    house['KitchenQual'] = st.selectbox('Kitchen quality', list(KITCHEN_LABELS), index=2,
                                        format_func=KITCHEN_LABELS.get, key='KitchenQual')
    submitted = st.form_submit_button('Estimate price', type='primary')

if submitted:
    api_url = os.getenv('API_URL', '').strip().rstrip('/')
    if not api_url:
        st.error('The prediction service address is missing. Ask the app owner to configure API_URL.')
        st.stop()
    api_key = os.getenv('API_KEY', '')
    headers = {'X-API-Key': api_key} if api_key else {}
    try:
        with st.spinner('Contacting the prediction service. It may take a moment to wake up after being idle.'):
            response = requests.post(f'{api_url}/predict', json=house, headers=headers,
                                     timeout=(10, 90), allow_redirects=False)
    except requests.Timeout:
        st.error('The prediction service took too long to reply. Wait a moment and try again.')
        st.stop()
    except requests.RequestException:
        st.error('Could not reach the prediction service. Check your connection and try again.')
        st.stop()

    if response.status_code in (400, 422):
        st.warning('The service could not use one or more house details. Check the ranges and selected categories.')
        st.stop()
    if response.status_code in (401, 403):
        st.error('The prediction service denied access. Ask the app owner to check its settings.')
        st.stop()
    if response.status_code != 200:
        st.error('The prediction service could not complete the request. Try again later.')
        st.stop()
    try:
        result = response.json()
        price = result['estimated_price_usd']
        warnings = result['warnings']
        if (type(price) not in (float, int) or not math.isfinite(price) or price <= 0
                or not isinstance(warnings, list) or not all(isinstance(item, str) for item in warnings)):
            raise ValueError('Unexpected response fields')
    except (ValueError, KeyError, TypeError, OverflowError):
        st.error('The prediction service returned an unreadable result. Try again later.')
        st.stop()
    st.metric('Estimated historical sale price', f'${price:,.2f}')
    st.write(f'The model estimates a historical sale price of **${price:,.2f} USD** for these house details.')
    if warnings:
        st.warning('One or more values fall outside the model’s training range. Treat this estimate with extra caution.')
    st.caption('Based on Ames sales from 2006–2010. A current valuation requires a qualified appraisal.')
