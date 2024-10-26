import threading
import socket
import time

## Metodos de sockets que cambian 
## AF_INET -> Protocolo de direccionamiento IPv4
## SOCK_DGRAM -> Protocolo de comunicacion UDP
## A diferencia de TCP, UDP no tiene un metodo de conexion, por lo que no hay un metodo connect()

puerto = 9999
ip = 'localhost'
direccion = (ip, puerto)
cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Primero se le pide al usuario que ingrese su token o si quiere crear un nuevo usuario
print("~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~")
print("Si desea crear un nuevo usuario escriba 'y' y pulse enter")
print("Si desea usar un token de un usuario existente escriba 'n' y pulse enter")
print("~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~")
tipo_identificacion = input("¿Quieres crear un nuevo usuario? (y/n) : ")

if tipo_identificacion == "y":
    identificador = input("Usuario : ")
    if identificador:
        cliente.sendto("reg".encode("UTF-8"), direccion)
        cliente.sendto(identificador.encode("UTF-8"), direccion)

        token, dirr = cliente.recvfrom(1024)
        identificador = token.decode("UTF-8")
        print("Tu token es: " + identificador + " guardalo bien, lo necesitaras para iniciar sesion")
else:
    identificador = input("Token : ")
    if identificador:
        cliente.sendto("log".encode("UTF-8"), direccion)
        cliente.sendto(identificador.encode("UTF-8"), direccion)


# Funcion que se encarga de recibir los mensajes del servidor
def recibir():
    while True:
        datos, servidor = cliente.recvfrom(1024)
        if datos:

            # Si el mensaje es el token del usuario seguido de .exit, se cierra el cliente , si no se imprime el mensaje
            if datos.decode("utf-8") == identificador + ".exit":
                exit(0)
            else:
                print(datos.decode("utf-8"))

# Funcion que se encarga de mandar mensajes al servidor
def mandar():
    try:
        while True:
            mensaje = input("").encode("UTF-8")
            if mensaje:
                cliente.sendto(("mensaje:" + identificador).encode("UTF-8"), direccion)
                cliente.sendto(mensaje, direccion)
    except:
        exit(0)


hiloRecibir = threading.Thread(target=recibir)
hiloMandar = threading.Thread(target=mandar)

hiloRecibir.start()
hiloMandar.start()
