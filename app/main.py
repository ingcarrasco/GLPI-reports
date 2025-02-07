import streamlit as st
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import sshtunnel
from sshtunnel import SSHTunnelForwarder
import pymysql
from datetime import datetime
import plotly.express as px



load_dotenv()

APP_TITLE=os.getenv("APP_TITLE")
SSH_HOST=os.getenv("SSH_HOST")
SSH_USR=os.getenv("SSH_USR")
SSH_PSW=os.getenv("SSH_PSW")
DB_HOST=os.getenv("DB_HOST")
DB_USR=os.getenv("DB_USR")
DB_PSW=os.getenv("DB_PSW")
DB_NAME=os.getenv("DB_NAME")


def open_ssh_tunnel(verbose=False):
    """Open an SSH tunnel and connect using a username and password.
    
    :param verbose: Set to True to show logging
    :return tunnel: Global SSH tunnel connection
    """
    
    if verbose:
        sshtunnel.DEFAULT_LOGLEVEL = logging.DEBUG
    
    global tunnel
    tunnel = SSHTunnelForwarder(
        (SSH_HOST, 22),
        ssh_username = SSH_USR,
        ssh_password = SSH_PSW,
        remote_bind_address = (DB_HOST, 3306)
    )
    
    tunnel.start()

def mysql_connect():
    """Connect to a MySQL server using the SSH tunnel connection
    
    :return connection: Global MySQL database connection
    """
    
    global connection
    
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USR,
        passwd=DB_PSW,
        db=DB_NAME,
        port=tunnel.local_bind_port
    )
def run_query(sql):
    """Runs a given SQL query via the global database connection.
    
    :param sql: MySQL query
    :return: Pandas dataframe containing results
    """
    
    return pd.read_sql_query(sql, connection)

def mysql_disconnect():
    """Closes the MySQL database connection.
    """
    connection.close()

def close_ssh_tunnel():
    """Closes the SSH tunnel connection.
    """
    tunnel.close()

open_ssh_tunnel()
mysql_connect()

# Querys personalizados
def leer_usuarios(list1):
    s = ' ,'.join(repr(item) for item in list1)
    query = '''
        SELECT 
            id, CONCAT(firstname, ' ', realname) as name
                FROM
                    glpi_users
                    WHERE id in (''' + s + ''');
        '''
    return pd.read_sql_query(query, connection)

# ########## Ingenieros de sitio
query = '''
SELECT 
    *
FROM
    glpi_users;
'''
x = run_query(query)
x['nombre'] = x['firstname'] + ' ' + x['realname']

filtro = ( x["is_active"]== 1 ) & ( x["profiles_id"].isin([3,6]) )
tecnicos= x[filtro]

query = '''
SELECT * FROM glpi_tickets_users
WHERE type = 2;
'''
x = run_query(query)

query = '''
SELECT 
    id as id_ticket, date_creation, 
    closedate, solvedate, status,
    users_id_recipient, itilcategories_id,
    type, time_to_resolve,
    time_to_own, sla_waiting_duration,
    internal_time_to_resolve, waiting_duration
    solve_delay_stat, locations_id
    
FROM glpi_tickets
    WHERE is_deleted = 0;
'''
tickets = run_query(query)
tickets['year'] = tickets['date_creation'].dt.year
tickets['month'] = tickets['date_creation'].dt.month
# tickets['year']  = pd.DatetimeIndex(tickets['date_creation']).year
# tickets['month']  = pd.DatetimeIndex(tickets['date_creation']).month

close_ssh_tunnel()
mysql_disconnect()

#### Preview 
st.set_page_config(page_title=APP_TITLE, page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)
st.markdown('# '+ APP_TITLE)
##### Borra el boton de Deploy
st.markdown(
    """
    <style>
        .stAppDeployButton {
            visibility: hidden;
        }
    </style>
    """, 
    unsafe_allow_html=True
)

st.logo(
    'images/new-logo.png',
    link="https://gruposolana.com",
    # icon_image='images/solana.png',
)

current_day = datetime.now().day
current_month = datetime.now().month
current_year = datetime.now().year

i =2021
op_anio_hoy=[]
op_mes_hoy=[]
####### Agregamos el Sidebar
with st.sidebar:
    op_ingeniero = st.selectbox(
        "Seleciona algun ingeniero:",
        (tecnicos[['nombre']].sort_values(by='nombre'))
    )
    i =2021
    op_anio_hoy.append('Todos')
    while i <= current_year:
        op_anio_hoy.append(str(i))
        i += 1
    op_anio = st.selectbox(
        "Seleciona el año a evaluar:",
        (op_anio_hoy),
    )
    i = 1
    op_mes_hoy.append('Todos')
    while i <= 12:
        op_mes_hoy.append(str(i))
        i += 1
    op_mes = st.selectbox(
        "Seleciona mes:",
        (op_mes_hoy),
    )

st.markdown('### '+ op_ingeniero)
filtro = (tecnicos['nombre']==op_ingeniero)
id_tecnico= tecnicos['id'][filtro]
if op_anio == 'Todos' and op_mes == 'Todos':
    print(1)
    tickets_filtrado = tickets
elif op_anio != 'Todos' and op_mes == 'Todos':
    print(2)
    filtro = ( tickets["year"]== int(op_anio) )
    tickets_filtrado = tickets[filtro]
elif op_anio == 'Todos' and op_mes != 'Todos':
    print(3)
    filtro = ( tickets["month"]== int(op_mes) )
    tickets_filtrado = tickets[filtro]
elif op_anio != 'Todos' and op_mes != 'Todos':
    filtro = ( tickets["year"]== int(op_anio) ) & ( tickets["month"]== int(op_mes) )
    print(4)
    tickets_filtrado = tickets[filtro]


print(op_anio)
print(op_mes)
col1, col2, col3, col4 = st.columns(4)
filtro = (x['users_id']==id_tecnico.values[0])
ticket_ingeniero= x[filtro]

data2 = pd.DataFrame(
    {
        "Etiqueta": ['Total', "Tickets Ingeniero",],
        "Cantidad": [len(tickets_filtrado.index)-len(tickets_filtrado[tickets_filtrado['id_ticket'].isin(ticket_ingeniero['tickets_id'])]), len(tickets_filtrado[tickets_filtrado['id_ticket'].isin(ticket_ingeniero['tickets_id'])])],
    }
)
 
graph_tickets_tot_ing = px.pie(data2,labels='Etiqueta', values='Cantidad', title='Año('+op_anio+') mes('+op_mes+')')

print(len(tickets_filtrado.index))

tickets_abiertos = tickets_filtrado[tickets_filtrado['id_ticket'].isin(ticket_ingeniero['tickets_id'])]
tickets_solucionados = tickets_abiertos
tickets_abiertos = tickets_abiertos[tickets_abiertos['status']!=5]
tickets_abiertos = tickets_abiertos[tickets_abiertos['status']!=6]
tickets_solucionados = tickets_solucionados[tickets_solucionados['status']!=1]
tickets_solucionados = tickets_solucionados[tickets_solucionados['status']!=2]
tickets_solucionados = tickets_solucionados[tickets_solucionados['status']!=3]
tickets_solucionados = tickets_solucionados[tickets_solucionados['status']!=4]
tickets_solucionados['x'] = tickets_solucionados['date_creation'].dt.year

tickets_solucionados['horas'] = (  tickets_solucionados.solvedate - tickets_solucionados.date_creation ) / pd.Timedelta(hours=1)
tickets_solucionados['diferencia'] = (  tickets_solucionados.solvedate - tickets_solucionados.date_creation )
tickets_solucionados
mas_tiempo_resolver=tickets_solucionados['horas'].max()



with col1:
    st.metric(label='Total de tickets (2021 Hasta hoy)', value=len(tickets.index))
    st.metric(label='1.Por agencia', value=0)
    st.metric(label='5.Tiempo promedio por ticket.',value=0)
    graph_tickets_tot_ing
    
with col2:
    
    st.metric(label='Total año('+op_anio+') mes('+op_mes+')', value=len(tickets_filtrado.index))
    st.metric(label='2.Por usuario',value=0)
    st.metric(label='Ticket con mas tiempo por resolver. (Hr)',value=round(mas_tiempo_resolver,2))


with col3:
    st.metric(label='Total ingeniero', value=len(tickets_filtrado[tickets_filtrado['id_ticket'].isin(ticket_ingeniero['tickets_id'])]))
    st.metric(label='Abiertos',value=len(tickets_abiertos.index))


promedio_tickets = len(tickets_filtrado[tickets_filtrado['id_ticket'].isin(ticket_ingeniero['tickets_id'])])/len(tickets_filtrado.index)

with col4:
    st.metric(label='Promedio Tickets (%)', value=round(promedio_tickets*100,4))
    st.metric(label='Terminados',value=len(tickets_filtrado[tickets_filtrado['id_ticket'].isin(ticket_ingeniero['tickets_id'])])-len(tickets_abiertos.index))



tickets_abiertos

ticket_ingeniero
# 1 En Curso
# 2 En Curso
# 4 En Espera
# 5 Resuelto
# 6 Cerrado



