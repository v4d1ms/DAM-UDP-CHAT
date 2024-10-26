import socket
import threading
import time
import json
from uuid import uuid4

clientes = dict()
tokens = dict()
baneados = dict()

## Metodos de sockets que cambian 
## AF_INET -> Protocolo de direccionamiento IPv4
## SOCK_DGRAM -> Protocolo de comunicacion UDP

servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
servidor.bind(('localhost', 9999))

# Cargamos los baneados del archivo baneados.json al principio del programa
with open("baneados.json", "r") as r:
    try:
        baneados = json.load(r)
    except json.decoder.JSONDecodeError:
        baneados = dict()

# Funcion que se encarga de desbanear a los usuarios
def hiloBaneos():
    while True:
        print(baneados)
        clientes_a_desbanear = list()

        for token in baneados.keys():
            if time.time() >= baneados[token]:
                clientes_a_desbanear.append(token)

        for token in clientes_a_desbanear:
            baneados.pop(token)
    

        with open("baneados.json", "w") as w:
            json.dump(baneados, w)
        
        time.sleep(60)

# Funcion que se encarga de verificar si un usuario esta baneado
def estaBaneado(token):
    try:
        file = open("baneados.json", "r")
        data = json.loads(file.read())

        if data[token]:
            file.close()
            return True
        
    except KeyError:
        file.close()
        return False
    except json.decoder.JSONDecodeError:
        file.close()
        return False

# Funcion que se encarga de validar si un usuario existe
def validarUsuarioPorToken(token):
    try:
        file = open("datos.json", "r")
        data = json.loads(file.read())

        if data[token]:
            return data[token]
        else:
            return None
        
    except KeyError:
        return None

# Funcion que comprueba si un usuario esta baneado , si no esta baneado le deja loguearse a partir de un token
def logueo():
    token, direccion = servidor.recvfrom(1024)
    nickname = validarUsuarioPorToken(str(token.decode("UTF-8")))

    if estaBaneado(str(token.decode("UTF-8"))):
        servidor.sendto(("Estas baneado!").encode("UTF-8"), direccion)
        servidor.sendto((str(token.decode("UTF-8")) + ".exit").encode("UTF-8"), direccion)
    else:
        if nickname:
            clientes[nickname] = direccion
            tokens[nickname] = str(token.decode("UTF-8"))
            servidor.sendto(("Bienvenido al chat, " + nickname).encode("UTF-8"), direccion)
        else:
            servidor.sendto("Token invalido, vuelve a iniciar el chat..".encode("UTF-8"), direccion)

# Funcion que se encarga de registrar a un usuario y asignarle un token
def registro():
    datos, dirr = servidor.recvfrom(1024)
    clientes[str(datos.decode("UTF-8"))] = dirr
    token = uuid4()
    tokens[str(datos.decode("UTF-8"))] = str(token)
    servidor.sendto((str(token)).encode("UTF-8"), dirr)

    with open("datos.json", "r") as r:
        try:
            data = json.load(r)
        except json.decoder.JSONDecodeError:
            data = dict()

    data[str(token)] = datos.decode("UTF-8")

    with open("datos.json", "w") as w:
        data = json.dump(data, w)


# Funcion que se encarga de banear a un usuario durante un tiempo determinado en minutos
def banear(token, tiempo):

    tiempo_actual_en_segundos = time.time()
    tiempo_para_desbanear = tiempo_actual_en_segundos + (int(tiempo) * 60)

    with open("baneados.json", "r") as r:
        try:
            bans = json.load(r)
        except json.decoder.JSONDecodeError:
            bans = dict()

    bans[str(token)] = tiempo_para_desbanear
    baneados[str(token)] = tiempo_para_desbanear

    with open("baneados.json", "w") as w:
        bans = json.dump(baneados, w)

# Funcion que se encarga de gestionar todos los comandos que pueda ejecutar un usuario / admin
def ejecutarComando(comando, usuario, direccion, token):
    try:
        comando = comando.decode("UTF-8")

        if comando.startswith("/salir"):
            print(usuario + " ha salido del chat")
            clientes.pop(usuario)
            servidor.sendto(("Has salido del chat!").encode("UTF-8"), direccion)
            servidor.sendto((token + ".exit").encode("UTF-8"), direccion)
            return

        if usuario == "admin":
            if comando.startswith("/list"):
                for cliente in clientes.keys():
                    servidor.sendto((cliente + " -- " + tokens[cliente]).encode("UTF-8"), direccion)
            elif comando.startswith("/kick"):
                cliente = comando.split(" ")[1]
                
                if clientes[cliente] and tokens[cliente]:
                    servidor.sendto(("Has sido expulsado del chat!").encode("UTF-8"), clientes[cliente])
                    servidor.sendto((tokens[cliente] + ".exit").encode("UTF-8"), clientes[cliente])
                    servidor.sendto((cliente + " ha sido expulsado del chat").encode("UTF-8"), direccion)
                    tokens.pop(cliente)
                    clientes.pop(cliente)
            elif comando.startswith("/ban"):
                cliente = comando.split(" ")[1]
                tiempo = comando.split(" ")[2]

                if clientes[cliente] and tokens[cliente]:
                    servidor.sendto(("Has sido baneado del chat durante " + tiempo + " minutos." ).encode("UTF-8"), clientes[cliente])
                    servidor.sendto((tokens[cliente] + ".exit").encode("UTF-8"), clientes[cliente])
                    servidor.sendto((cliente + " ha sido expulsado del chat").encode("UTF-8"), direccion)
                    banear(tokens[cliente], tiempo)
                    tokens.pop(cliente)
                    clientes.pop(cliente)
    except:
        servidor.sendto("Se ha producido un error al ejecutar un comando!".encode("UTF-8"), direccion)       

# Funcion que propaga los mensajes a todos los usuarios conectados
def mensaje(usuario, token):
    mensaje, direccion = servidor.recvfrom(1024)

    if mensaje.decode("utf-8").startswith("/"):
        ejecutarComando(mensaje, usuario, direccion, token)
    else: 
        for nombre in clientes.keys():
            if nombre != "admin":
                servidor.sendto((usuario + ">>").encode("utf-8") + mensaje, clientes[nombre])
            else:
                servidor.sendto((usuario + " (" + token + ") " + " >> ").encode("utf-8") + mensaje, clientes[nombre])

threading.Thread(target=hiloBaneos).start()


# hilo principal que obtiene el tipo de peticion que se esta realizando al servidor y ejecuta la funcion correspondiente
while True:
    datos, dirr = servidor.recvfrom(1024)
    dato = datos.decode("UTF-8")

    if dato == "reg":
        registro()
    elif dato == "log":
        logueo()
    elif "mensaje:" in dato:
        token = dato.split(":")[1]
        usuario = validarUsuarioPorToken(token)
        if usuario:
            threading.Thread(target=mensaje, args=(usuario, token)).start()
    

    time.sleep(0.1)