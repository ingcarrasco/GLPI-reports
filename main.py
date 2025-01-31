import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
import sshtunnel
from sshtunnel import SSHTunnelForwarder
import pymysql
from datetime import datetime

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

close_ssh_tunnel()
mysql_disconnect()

#### Preview 
st.markdown('# '+ APP_TITLE)

st.logo(
    'images/new-logo.png',
    link="https://streamlit.io/gallery",
    # icon_image='images/solana.png',
)

current_day = datetime.now().day
current_month = datetime.now().month
current_year = datetime.now().year

i =2021
while i <= current_year:
    print(i)
    i += 1
op_anio_hoy=[]
op_mes_hoy=[]
####### Agregamos el Sidebar
with st.sidebar:
    op_ingeniero = st.selectbox(
        "Seleciona algun ingeniero:",
        (tecnicos[['nombre']].sort_values(by='nombre'))
    )
    i =2021
    while i <= current_year:
        op_anio_hoy.append(str(i))
        i += 1
    op_anio = st.selectbox(
        "Seleciona el año a evaluar:",
        (op_anio_hoy),
    )
    i = 1
    while i <= 12:
        op_mes_hoy.append(i)
        i += 1
    op_anio = st.selectbox(
        "Seleciona mes:",
        (op_mes_hoy),
    )

st.markdown('### '+ op_ingeniero)
filtro = (tecnicos['nombre']==op_ingeniero)
id_tecnico= tecnicos['id'][filtro]
st.metric(label='Total de tickets', value=len(x.index))

filtro = (x['users_id']==id_tecnico.values[0])
ticket_ingeniero= x[filtro]
st.metric(label='Total ingeniero', value=len(ticket_ingeniero.index))

promedio_tickets = len(ticket_ingeniero.index)/len(x.index)
st.metric(label='Promedio Tickets (%)', value=round(promedio_tickets*100,4))


