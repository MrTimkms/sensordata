from datetime import datetime
import os
import sqlite3
import dash
import plotly.express as px
from dash import dcc, html
from config import IMAP_CONFIG, DOWNLOAD_PATH, TELEGRAM_CONFIG, ALLOWED_USERS, Mail_CONFIG, localDASH_CONFIG
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from flask import send_file
import logging
import plotly.express as px
import plotly.graph_objects as go
# Импорт модулей с функциями
NOlocalDASH=localDASH_CONFIG["NOlocalDASH"]
# Создание экземпляра Dash приложения
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# Путь к базе данных SQLite
DATABASE_PATH = os.path.join(os.getcwd(), '1.3_SolarData_ExpU.db')
db_path_cloud= os.path.join(os.getcwd(),  '1.2_WeatherData_VS-1_2024-03-20_.db')
# Отключение логирования Dash
logging.getLogger('dash').setLevel(logging.ERROR)
# Отключение логирования Dash и Flask
logging.getLogger('dash').setLevel(logging.CRITICAL)
logging.getLogger('werkzeug').setLevel(logging.CRITICAL)
def create_graphs():
    import datetime
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    if NOlocalDASH:
        current_date = datetime.datetime.now()
        start_of_last_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)
        start_of_current_month = start_of_last_month.replace(day=1)
        end_of_last_month = start_of_current_month

        cursor.execute(
            "SELECT datetime, temperature, humidity, solar_radiation FROM weathergis WHERE datetime BETWEEN ? AND ?",
            (end_of_last_month, current_date))
    else:
        cursor.execute("SELECT datetime, temperature, humidity, solar_radiation FROM weathergis")
    rows = cursor.fetchall()

    dates, temperatures, humidities, solar_radiations = zip(*rows)

    if NOlocalDASH:
        cursor.execute(
            "SELECT datetime, solar_input_I, solar_input_W, solar_input_kWh, extern_input_V, bat_charge_V, bat_charge_I, bat_charge_W, bat_total_kWh, bat_capacity FROM additional_data WHERE datetime BETWEEN ? AND ?",
            (end_of_last_month, current_date))
    else:
        cursor.execute(
            "SELECT datetime, solar_input_I, solar_input_W, solar_input_kWh, extern_input_V, bat_charge_V, bat_charge_I, bat_charge_W, bat_total_kWh, bat_capacity FROM additional_data")
    rows_additional = cursor.fetchall()

    dates_additional, solar_input_I, solar_input_W, solar_input_kWh, extern_input_V, bat_charge_V, bat_charge_I, bat_charge_W, bat_total_kWh, bat_capacity = zip(*rows_additional)

    conn.close()

    conn = sqlite3.connect(db_path_cloud)
    cursor = conn.cursor()
    if NOlocalDASH:
        cursor.execute("SELECT datetime, clouds FROM screenshots WHERE datetime BETWEEN ? AND ?", (end_of_last_month, current_date))
    else:
        cursor.execute("SELECT datetime, clouds FROM screenshots")
    cloud_rows = cursor.fetchall()

    cloud_dates, cloud_values = zip(*cloud_rows) if cloud_rows else ([], [])

    conn.close()

    return (
        dates, temperatures, humidities, solar_radiations,
        dates_additional, solar_input_I, solar_input_W, solar_input_kWh, extern_input_V, bat_charge_V, bat_charge_I, bat_charge_W, bat_total_kWh, bat_capacity, cloud_dates, cloud_values
    )
def create_figures():
    data = create_graphs()

    dates, temperatures, humidities, solar_radiations, dates_additional, solar_input_I, solar_input_W, solar_input_kWh, extern_input_V, bat_charge_V, bat_charge_I, bat_charge_W, bat_total_kWh, bat_capacity, cloud_dates, cloud_values = data

    fig1 = px.line(x=dates, y=solar_radiations, title='Солнечная радиация')
    fig1.update_xaxes(title_text='Дата')
    fig1.update_yaxes(title_text='Солнечная радиация (W/m²)')
    fig1.update_traces(line=dict(color='orange'))

    fig2 = px.line(x=dates, y=temperatures, title='Температура')
    fig2.update_xaxes(title_text='Дата')
    fig2.update_yaxes(title_text='Температура (°C)')

    fig3 = px.line(x=dates, y=humidities, title='Влажность')
    fig3.update_xaxes(title_text='Дата')
    fig3.update_yaxes(title_text='Влажность (%)')
    fig3.update_traces(line=dict(color='blue'))

    fig4 = px.line(x=dates_additional, y=solar_input_I, title='Входной ток I (additional_data)', labels={'x': 'Дата', 'y': 'Solar Input I'})
    fig4.update_xaxes(title_text='Дата')
    fig4.update_yaxes(title_text='Solar Input I')

    fig5 = px.line(x=dates_additional, y=solar_input_W, title='Входная мощность W (additional_data)')
    fig5.update_xaxes(title_text='Дата')
    fig5.update_yaxes(title_text='Solar Input W')

    fig6 = px.line(x=dates_additional, y=solar_input_kWh, title='Входная энергия KwH (additional_data)', labels={'x': 'Дата', 'y': 'Solar Input KwH'})
    fig6.update_xaxes(title_text='Дата')
    fig6.update_yaxes(title_text='Solar Input KwH')

    fig7 = px.line(x=dates_additional, y=extern_input_V, title='Входное напряжение V (additional_data)', labels={'x': 'Дата', 'y': 'Input V'})
    fig7.update_xaxes(title_text='Дата')
    fig7.update_yaxes(title_text='Input V')

    fig8 = px.line(x=dates_additional, y=bat_charge_V, title='Напряжение на батарее V (additional_data)', labels={'x': 'Дата', 'y': 'BatV'})
    fig8.update_xaxes(title_text='Дата')
    fig8.update_yaxes(title_text='BatV')

    fig9 = px.line(x=dates_additional, y=bat_charge_I, title='Ток на батарее I (additional_data)', labels={'x': 'Дата', 'y': 'bat charge I'})
    fig9.update_xaxes(title_text='Дата')
    fig9.update_yaxes(title_text='bat charge I')

    fig10 = px.line(x=dates_additional, y=bat_charge_W, title='Мощность батареи W (additional_data)', labels={'x': 'Дата', 'y': 'Bat Charge W'})
    fig10.update_xaxes(title_text='Дата')
    fig10.update_yaxes(title_text='bat_charge_W')

    fig11 = px.line(x=dates_additional, y=bat_total_kWh, title='Энергия батареи kWh (additional_data)', labels={'x': 'Дата', 'y': 'Bat Total KwH'})
    fig11.update_xaxes(title_text='Дата')
    fig11.update_yaxes(title_text='Bat Total KwH')

    fig12 = px.line(x=dates_additional, y=bat_capacity, title='Емкость батареи (additional_data)', labels={'x': 'Дата', 'y': 'Bat Capacity'})
    fig12.update_xaxes(title_text='Дата')
    fig12.update_yaxes(title_text='Bat Capacity')

    fig13 = px.line(x=cloud_dates, y=cloud_values, title='Облачность %', labels={'x': 'Дата', 'y': 'Облачность %'})
    fig13.update_xaxes(title_text='Дата')
    fig13.update_yaxes(title_text='Облачность %')

    # Создание комбинированного графика для облачности и солнечной радиации
    fig_combined = go.Figure()
    fig_combined.add_trace(go.Scatter(x=cloud_dates, y=cloud_values, mode='lines', name='Облачность %', yaxis='y2', line=dict(color='blue')))
    fig_combined.add_trace(go.Scatter(x=dates, y=solar_radiations, mode='lines', name='Солнечная радиация (W/m²)', line=dict(color='orange')))

    fig_combined.update_layout(
        title='Облачность и Солнечная радиация',
        xaxis_title='Дата',
        yaxis=dict(title='Солнечная радиация (W/m²)', titlefont=dict(color='orange'), tickfont=dict(color='orange')),
        yaxis2=dict(title='Облачность %', titlefont=dict(color='blue'), tickfont=dict(color='blue'), anchor='free', overlaying='y', side='right', position=1, autorange='reversed')
    )

    return fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11, fig12, fig13, fig_combined
def func(n_clicks):
    if n_clicks is not None:
        return {
            "content": None,
            "filename": "1.3_SolarData_ExpU.db"
        }
    raise dash.exceptions.PreventUpdate

# Callback для обновления отображаемых графиков
@app.callback(
    Output('graph-container', 'children'),
    [Input('graph-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_graphs(selected_graphs, n_intervals):
    fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11, fig12, fig13, fig_combined = create_figures()

    graphs = {
        'Солнечная радиация': dcc.Graph(id='graph1', figure=fig1),
        'Температура': dcc.Graph(id='graph2', figure=fig2),
        'Влажность': dcc.Graph(id='graph3', figure=fig3),
        'Входной ток I': dcc.Graph(id='graph4', figure=fig4),
        'Входная мощность W': dcc.Graph(id='graph5', figure=fig5),
        'Входная энергия KwH': dcc.Graph(id='graph6', figure=fig6),
        'Входное напряжение V': dcc.Graph(id='graph7', figure=fig7),
        'Напряжение на батарее V ': dcc.Graph(id='graph8', figure=fig8),
        'Ток на батарее I': dcc.Graph(id='graph9', figure=fig9),
        'Мощность батареи W ': dcc.Graph(id='graph10', figure=fig10),
        'Энергия батареи kWh': dcc.Graph(id='graph11', figure=fig11),
        'Емкость батареи': dcc.Graph(id='graph12', figure=fig12),
        'Облачность %': dcc.Graph(id='graph13', figure=fig13),
        'Облачность и Солнечная радиация': dcc.Graph(id='graph14', figure=fig_combined),
    }

    graphs_to_show = []
    if not selected_graphs:
        default_graph_name = list(graphs.keys())[0]
        graphs_to_show.append(dcc.Graph(figure=graphs[default_graph_name].figure))
    else:
        for graph_name in selected_graphs:
            if graph_name in graphs:
                graphs_to_show.append(dcc.Graph(figure=graphs[graph_name].figure))

    return graphs_to_show
def setup_layout():
    graphs = {
        'Солнечная радиация': dcc.Graph(id='graph1', figure=fig1),
        'Температура': dcc.Graph(id='graph2', figure=fig2),
        'Влажность': dcc.Graph(id='graph3', figure=fig3),
        'Входной ток I': dcc.Graph(id='graph4', figure=fig4),
        'Входная мощность W': dcc.Graph(id='graph5', figure=fig5),
        'Входная энергия KwH': dcc.Graph(id='graph6', figure=fig6),
        'Входное напряжение V': dcc.Graph(id='graph7', figure=fig7),
        'Напряжение на батарее V ': dcc.Graph(id='graph8', figure=fig8),
        'Ток на батарее I': dcc.Graph(id='graph9', figure=fig9),
        'Мощность батареи W ': dcc.Graph(id='graph10', figure=fig10),
        'Энергия батареи kWh': dcc.Graph(id='graph11', figure=fig11),
        'Емкость батареи': dcc.Graph(id='graph12', figure=fig12),
        'Облачность %': dcc.Graph(id='graph13', figure=fig13),
        'Облачность и Солнечная радиация': dcc.Graph(id='graph14', figure=fig_combined),
    }
    dropdown = dcc.Dropdown(
        id='graph-dropdown',
        options=[{'label': graph_name, 'value': graph_name} for graph_name in graphs.keys()],
        multi=True
    )
    app.layout = html.Div([
        html.H1(children='Дашборд по солнечной радиации и погоде'),
        html.A("Скачать БД", id="download-db-link", href="/download/1.3_SolarData_ExpU.db", className='btn btn-dark', target="_blank"),
        html.A("Скачать базу данных облачности", href="/download/cloud_data_db", className='btn btn-primary', target="_blank"),
        dcc.Download(id="download-data"),
        html.Br(),
        html.H1(children='Динамическое управление графиками'),
        dropdown,
        html.Div(id='graph-container'),
        dcc.Interval(
            id='interval-component',
            interval=1 * 1000 * 3600,
            n_intervals=0
        )
    ])

fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11, fig12, fig13, fig_combined = create_figures()
def run_server():
    setup_layout()
    @app.server.route("/download/1.3_SolarData_ExpU.db")
    def download_db():
        return send_file(DATABASE_PATH, as_attachment='1.3_SolarData_ExpU.db')

    @app.server.route("/download/cloud_data_db")
    def download_cloud_db():
        base_date = "2024-03-20"  # Базовая дата, которая уже встроена в название
        current_date = datetime.now().strftime("%Y-%m-%d")  # Текущая дата
        db_path = os.path.join(os.getcwd(), f'1.2_WeatherData_VS-1_{base_date}_.db')  # Путь к файлу базы данных
        download_name = f"1.2_WeatherData_VS-1_{base_date}_{current_date}.db"  # Формируемое название файла
        return send_file(db_path, as_attachment=True, attachment_filename=download_name)

    app.run_server(debug=False, use_reloader=False)
if __name__ == "__main__":
    run_server()
