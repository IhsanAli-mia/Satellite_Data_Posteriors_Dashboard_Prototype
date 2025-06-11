import json
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

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

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Cloud Cover Dashboard"),

    html.Div([
        html.Div(f"Total Tiles: {len(df)}"),
        html.Div(f"Date Range: {df['date'].min()} to {df['date'].max()}"),
        html.Div(f"Mean Cloud Cover: {df['cloud_cover'].mean():.2f}%"),
        html.Div(f"Metadata Available: {df['metadata_available'].eq('true').sum()} / {len(df)}")
    ], style={'display': 'flex', 'gap': '2rem'}),

    html.Hr(),

    dcc.DatePickerRange(
        id='date-range',
        start_date=df['date'].min(),
        end_date=df['date'].max(),
        display_format='YYYY-MM-DD'
    ),

    dcc.RangeSlider(
        id='cloud-range',
        min=0, max=100, step=1,
        value=[0, 100],
        marks={i: str(i) for i in range(0, 101, 20)}
    ),

    dcc.Graph(id='histogram'),
    dcc.Graph(id='line-chart'),
    dcc.Graph(id='map'),

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

    hist = px.histogram(filtered, x='cloud_cover', nbins=20, title='Cloud Cover Distribution')
    line = px.line(filtered.groupby('date')['cloud_cover'].mean().reset_index(), 
                   x='date', y='cloud_cover', title='Daily Mean Cloud Cover')
    map_fig = px.scatter_mapbox(
        filtered, lat='lat', lon='lon', color='cloud_cover',
        mapbox_style='carto-positron', zoom=2, title='Geospatial Cloud Cover'
    )

    return hist, line, map_fig

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)
