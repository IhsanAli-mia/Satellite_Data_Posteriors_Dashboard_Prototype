import json
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

# Load JSON file
with open("cloud_data.json") as f:
    raw_data = json.load(f)


df = pd.DataFrame(raw_data)

# print(df)

# Convert to DataFrame
# data = []
# for meta, (dt, cloud), (lon, lat, cloud_val) in zip(raw_data["metadata"], raw_data["cloud_covers"], raw_data["centroids"]):
#     data.append({
#         "metadata_available": meta,
#         "date": dt,
#         "cloud_cover": cloud,
#         "lon": lon,
#         "lat": lat,
#     })

app = Dash(__name__, external_stylesheets=[
    dbc.themes.DARKLY,
    'https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap',
    '/assets/custom.css'
])

df_filtered = df[~df['date_only'].str.startswith('2025')]

min_res = 0
max_res = 100


filtered = df[df['gsd'].between(min_res, max_res)]

# print(filtered)
# Sum the lengths of all tilewise_cloud_cover arrays


app.layout = html.Div([
    html.H1("Cloud Cover Dashboard", className='dashboard-title'),
    html.Div([
        html.Div([
            html.P("Total Tiles", className='stat-label'),
            html.P(id='total_tiles', className='stat-value')
        ], className='stat-card'),
        html.Div([
            html.P("Date Range", className='stat-label'),
            html.P(f"{df_filtered['date_only'].min()} to {df_filtered['date_only'].max()}", className='stat-value')
        ], className='stat-card'),
        html.Div([
            html.P("Mean Cloud Cover", className='stat-label'),
            html.P(id='mean-cloud', className='stat-value')
        ], className='stat-card'),
        html.Div([
            html.P("Metadata Available", className='stat-label'),
            html.P(id='metadata-available', className='stat-value')
        ], className='stat-card'),
        html.Div([
        html.Div(
            "Image Resolution",
            className="resolution-label"
        ),
        dcc.RadioItems(
            id='resolution-selector',
            options=[
                {'label': 'All Resolutions(1-30m)', 'value': 1},
                {'label': 'High (≤10m)', 'value': 10},
                {'label': 'Medium (10-30m)', 'value': 30}
            ],
            value=1,
            labelClassName="resolution-option",
            inputClassName="resolution-option-input",
            className="resolution-options"
        ),
    ], className="resolution-selector-container")
    ], className='stats-container'),
    
    html.Hr(className='divider'),
    
    html.Div(
        dcc.DatePickerRange(
            id='date-range',
            start_date=df_filtered['date_only'].min(),
            end_date=df_filtered['date_only'].max(),
            display_format='YYYY-MM-DD',
            className='date-picker'
        ),
        style={'textAlign': 'center'}
    ),

    dcc.RangeSlider(
        id='cloud-range',
        min=0, max=100, step=1,
        value=[0, 100],
        marks={i: str(i) for i in range(0, 101, 20)},
        className='range-slider'
    ),

    dcc.Graph(id='histogram', className='graph'),
    dcc.Graph(id='scatter', className='graph'),
    dcc.Graph(id='map', className='graph')
])

@app.callback(
    [Output('histogram', 'figure'),
     Output('scatter', 'figure'),
     Output('map', 'figure'),
     Output('total_tiles', 'children'),
     Output('mean-cloud', 'children'),
     Output('metadata-available', 'children')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('cloud-range', 'value'),
     Input('resolution-selector', 'value')]
)
def update_charts(start_date, end_date, cloud_range,selected_resolution):
    if selected_resolution == 1:
        min_res = 0
        max_res = 30
    elif selected_resolution == 10:
        min_res = 0
        max_res = 10
    else:
        min_res = 10
        max_res = 30
        
    
    res_filtered = df[df['gsd'].between(min_res, max_res)]
    
    mask = (
    ((res_filtered['date_only'] >= start_date) & (res_filtered['date_only'] <= end_date) &
     (res_filtered['cloud_cover'] >= cloud_range[0]) & (res_filtered['cloud_cover'] <= cloud_range[1]))
    ) | (
        (res_filtered['date_only'].str.startswith('2025')) & 
        (res_filtered['cloud_cover'] >= cloud_range[0]) & (res_filtered['cloud_cover'] <= cloud_range[1])  # Same cloud range
    )

        
    res_filtered = res_filtered[mask]
    filtered = res_filtered[~res_filtered['date_only'].str.startswith('2025')]
    
    total_tiles = res_filtered['tilewise_cloud_cover'].apply(len).sum()
    
    mean_cloud = f"{res_filtered['cloud_cover'].mean():.2f}%"
    
    metadata_available = f"{((res_filtered['metadata_available'].eq(True))*(res_filtered['tilewise_cloud_cover'].apply(len))).sum()} / {total_tiles}"

    # f"{df['cloud_cover'].mean():.2f}%"
    # f"{((filtered['metadata_available'].eq(True))*(filtered['tilewise_cloud_cover'].apply(len))).sum()} / {filtered['tilewise_cloud_cover'].apply(len).sum()}"

    # Shared dark layout
    dark_layout = dict(
        paper_bgcolor='#2f3640',
        plot_bgcolor='#2f3640',
        font=dict(color='white', family='Roboto'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', zeroline=False),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', zeroline=False),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
        title_font=dict(size=18, color='white'),
        hoverlabel=dict(bgcolor='#2f3640', font_color='white'),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    cloud_cover_values = [item for sublist in res_filtered['tilewise_cloud_cover'] for item in sublist]

    # Histogram
    hist = px.histogram(
        x = cloud_cover_values, nbins=40, title='Cloud Cover Distribution',
        color_discrete_sequence=["#6173d8"]
    )
    hist.update_layout(dark_layout)

    scatter = px.strip(
        filtered,
        x='date_only',
        y='cloud_cover',
        title='Individual Cloud Cover Measurements',
        color_discrete_sequence=["#6173d8"],
        stripmode='overlay'  # Overlap points slightly
    )
    scatter.update_traces(jitter=0.3)  # Add jitter
    scatter.update_layout(dark_layout)


    
    # Updated map to match dark theme
    map_fig = px.scatter_mapbox(
        res_filtered,
        lat='lat_center',
        lon='lon_center',
        color='cloud_cover',
        color_continuous_scale='Viridis',
        mapbox_style='carto-darkmatter',  # No token required, works well
        zoom=2,
        title='Geospatial Cloud Cover'
    )
    map_fig.update_layout(
        paper_bgcolor='#2f3640',
        font=dict(color='white', family='Roboto'),
        title_font=dict(size=18, color='white'),
        margin=dict(l=10, r=10, t=40, b=10),
        hoverlabel=dict(bgcolor='#2f3640', font_color='white')
    )
    

    return hist, scatter, map_fig,total_tiles,mean_cloud,metadata_available


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
