import json
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

# Load JSON file
with open("cloud_data.json") as f:
    raw_data = json.load(f)

# Convert to DataFrame
data = []
for meta, (dt, cloud), (lon, lat, cloud_val) in zip(raw_data["metadata"], raw_data["cloud_covers"], raw_data["centroids"]):
    data.append({
        "metadata_available": meta,
        "date": dt,
        "cloud_cover": cloud,
        "lon": lon,
        "lat": lat,
    })
df = pd.DataFrame(data)

app = Dash(__name__, external_stylesheets=[
    dbc.themes.DARKLY,
    'https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap',
    '/assets/custom.css'
])

df_filtered = df[~df['date'].str.startswith('2025')]

app.layout = html.Div([
    html.H1("Cloud Cover Dashboard", className='dashboard-title'),
    html.Div([
        html.Div([
            html.P("Total Tiles", className='stat-label'),
            html.P(f"{len(df)}", className='stat-value')
        ], className='stat-card'),
        html.Div([
            html.P("Date Range", className='stat-label'),
            html.P(f"{df_filtered['date'].min()} to {df_filtered['date'].max()}", className='stat-value')
        ], className='stat-card'),
        html.Div([
            html.P("Mean Cloud Cover", className='stat-label'),
            html.P(f"{df['cloud_cover'].mean():.2f}%", className='stat-value')
        ], className='stat-card'),
        html.Div([
            html.P("Metadata Available", className='stat-label'),
            html.P(f"{df['metadata_available'].eq(True).sum()} / {len(df)}", className='stat-value')
        ], className='stat-card')
    ], className='stats-container'),
    
    html.Hr(className='divider'),
    
    html.Div(
        dcc.DatePickerRange(
            id='date-range',
            start_date=df_filtered['date'].min(),
            end_date=df_filtered['date'].max(),
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
    dcc.Graph(id='line-chart', className='graph'),
    dcc.Graph(id='map', className='graph')
])

@app.callback(
    [Output('histogram', 'figure'),
     Output('line-chart', 'figure'),
     Output('map', 'figure')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('cloud-range', 'value')]
)
def update_charts(start_date, end_date, cloud_range):
    mask = (df['date'] >= start_date) & (df['date'] <= end_date) & \
           (df['cloud_cover'] >= cloud_range[0]) & (df['cloud_cover'] <= cloud_range[1])
    filtered = df[mask]

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

    # Histogram
    hist = px.histogram(
        filtered, x='cloud_cover', nbins=20, title='Cloud Cover Distribution',
        color_discrete_sequence=["#6173d8"]
    )
    hist.update_layout(dark_layout)

    # Line chart
    line = px.line(
        filtered.groupby('date')['cloud_cover'].mean().reset_index(),
        x='date', y='cloud_cover', title='Daily Mean Cloud Cover',
        color_discrete_sequence=["#6173d8"]
    )
    line.update_layout(dark_layout)

    # Updated map to match dark theme
    map_fig = px.scatter_mapbox(
        filtered,
        lat='lat',
        lon='lon',
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
    

    return hist, line, map_fig

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
