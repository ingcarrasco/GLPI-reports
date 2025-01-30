import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
import sshtunnel
from sshtunnel import SSHTunnelForwarder
import pymysql

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


# 1911 Angel Arturo Carrasco Avila
# 2405 Jaime Arturo Gutierrez Rubio

# 993 Manuel Edgardo Morales Yañez
# 1525 Israel Marin
# 1885 Israel Alejandro Marin Piña

# ########## Ingenieros de sitio
# 2620 Daniel Bellot
# 27 Carlos Alberto Castelo Gonzalez
# 2477 Martin Arvizu Posos
# 2921 Maria Guadalupe Antonio Rita
# 4410 Jose Manuel Zamudio Lopez
# 5500 David Alejandro Triana Ochoa


query = '''
SELECT 
    *
FROM
    glpi_users;
'''
x = run_query(query)
x['nombre'] = x['firstname'] + ' ' + x['realname']
# x
# filter= x['is_active'] == 1
# view = x.where(filter)
# view['name','realname','profiles_id']

close_ssh_tunnel()
mysql_disconnect()

#### Preview 
st.markdown('# '+ APP_TITLE)

filtro = ( x["is_active"]== 1 ) & ( x["profiles_id"].isin([3,6]) )
tecnicos= x[filtro]
# st.markdown('# Tecnicos')
# tecnicos[['id','name','nombre']]

with st.sidebar:
    opcion = st.radio(
        "Seleciona algun ingeniero:",
        (tecnicos[['nombre']].sort_values(by='nombre'))
    )

st.markdown('### '+ opcion)
filtro = (tecnicos['nombre']==opcion)
tecnicos['id'][filtro]


