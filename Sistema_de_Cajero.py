import datetime
import os
import sys
import random
from collections import defaultdict

# Configuración de colores para la interfaz
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Clases principales del sistema
class Cliente:
    def __init__(self, id, nombre, password):
        self.id = id
        self.nombre = nombre
        self.password = password

class Cuenta:
    def __init__(self, numero, cliente_id, saldo=0):
        self.numero = numero
        self.cliente_id = cliente_id
        self.saldo = saldo
        self.movimientos = []

class Dispensador:
    def __init__(self, id, ubicacion):
        self.id = id
        self.ubicacion = ubicacion
        self.billetes = {200: 0, 100: 0, 50: 0, 20: 0}

class Movimiento:
    def __init__(self, tipo, monto, cuenta_numero, cuenta_destino=None, servicio=None):
        self.fecha = datetime.datetime.now()
        self.tipo = tipo
        self.monto = monto
        self.cuenta_numero = cuenta_numero
        self.cuenta_destino = cuenta_destino
        self.servicio = servicio

class Banco:
    def __init__(self):
        self.clientes = []
        self.cuentas = []
        self.dispensadores = []
        self.cuentas_por_cliente = {}
        self.clientes_por_id = {}
        
    # Algoritmo de ordenamiento: Quicksort
    def quicksort(self, arr, key='id'):
        if len(arr) <= 1:
            return arr
        pivot = arr[0]
        left = [x for x in arr[1:] if getattr(x, key) <= getattr(pivot, key)]
        right = [x for x in arr[1:] if getattr(x, key) > getattr(pivot, key)]
        return self.quicksort(left, key) + [pivot] + self.quicksort(right, key)
    
    # Algoritmo de búsqueda: Binaria
    def busqueda_binaria(self, arr, target, key='id'):
        low, high = 0, len(arr) - 1
        while low <= high:
            mid = (low + high) // 2
            mid_val = getattr(arr[mid], key)
            if mid_val == target:
                return arr[mid]
            elif mid_val < target:
                low = mid + 1
            else:
                high = mid - 1
        return None
    
    def agregar_cliente(self, cliente):
        self.clientes.append(cliente)
        self.clientes_por_id[cliente.id] = cliente
    
    def agregar_cuenta(self, cuenta):
        self.cuentas.append(cuenta)
        self.cuentas_por_cliente[cuenta.cliente_id] = cuenta

# Funciones para la interfaz de usuario
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    clear_screen()
    print(Colors.BOLD + Colors.CYAN + "=" * 60)
    print(f"{title:^60}")
    print("=" * 60 + Colors.END)

def print_menu(options):
    for key, value in options.items():
        print(f"{Colors.BOLD}{key}.{Colors.END} {value}")
    print("-" * 60)

def get_valid_input(prompt, input_type=str, valid_options=None, min_value=None):
    while True:
        try:
            user_input = input(prompt)
            if input_type == int:
                user_input = int(user_input)
                if min_value is not None and user_input < min_value:
                    print(Colors.RED + f"Error: El valor debe ser al menos {min_value}" + Colors.END)
                    continue
            elif input_type == float:
                user_input = float(user_input)
                if min_value is not None and user_input < min_value:
                    print(Colors.RED + f"Error: El valor debe ser al menos {min_value}" + Colors.END)
                    continue
                    
            if valid_options and user_input not in valid_options:
                raise ValueError
            return user_input
        except ValueError:
            print(Colors.RED + "Entrada inválida. Intente nuevamente." + Colors.END)

# Algoritmo voraz para desglose de billetes
def calcular_desglose_billetes(monto, dispensador):
    denominaciones = sorted(dispensador.billetes.keys(), reverse=True)
    desglose = {}
    restante = monto
    
    for denom in denominaciones:
        if restante <= 0:
            break
            
        disponible = dispensador.billetes[denom]
        if denom <= restante and disponible > 0:
            cantidad = min(restante // denom, disponible)
            desglose[denom] = cantidad
            restante -= denom * cantidad
    
    return desglose if restante == 0 else None

# Funciones principales del sistema
def realizar_retiro(banco, cuenta, dispensador):
    print_header("RETIRO DE EFECTIVO")
    
    # Obtener monto válido
    max_retiro = min(cuenta.saldo, sum(k*v for k,v in dispensador.billetes.items()))
    monto = get_valid_input(f"Ingrese monto a retirar (máximo ${max_retiro}): ", int, min_value=1)
    
    # Validar fondos
    if monto > cuenta.saldo:
        print(Colors.RED + "Error: Saldo insuficiente en la cuenta" + Colors.END)
        return False
    if monto > sum(k*v for k,v in dispensador.billetes.items()):
        print(Colors.RED + "Error: No hay suficiente efectivo en el cajero" + Colors.END)
        return False
    
    # Calcular desglose
    desglose = calcular_desglose_billetes(monto, dispensador)
    if not desglose:
        print(Colors.RED + "Error: No se puede desglosar el monto con los billetes disponibles" + Colors.END)
        return False
    
    # Actualizar saldos y billetes
    cuenta.saldo -= monto
    for denom, cant in desglose.items():
        dispensador.billetes[denom] -= cant
    
    # Registrar movimiento
    movimiento = Movimiento("RETIRO", -monto, cuenta.numero)
    cuenta.movimientos.append(movimiento)
    
    # Mostrar resultado
    print("\n" + Colors.GREEN + "Retiro exitoso!" + Colors.END)
    print(f"Desglose de billetes:")
    for denom, cant in desglose.items():
        print(f" - ${denom}: {cant} billete(s)")
    print(f"\nNuevo saldo: ${cuenta.saldo}")
    return True

def realizar_deposito(banco, cuenta, dispensador):
    print_header("DEPÓSITO DE EFECTIVO")
    
    # Obtener billetes
    billetes_deposito = {}
    total = 0
    for denom in [200, 100, 50, 20]:
        cantidad = get_valid_input(f"Ingrese cantidad de billetes de ${denom}: ", int, min_value=0)
        billetes_deposito[denom] = cantidad
        total += denom * cantidad
    
    if total <= 0:
        print(Colors.RED + "Error: Debe ingresar al menos un billete" + Colors.END)
        return False
    
    # Actualizar saldos y billetes
    cuenta.saldo += total
    for denom, cant in billetes_deposito.items():
        dispensador.billetes[denom] += cant
    
    # Registrar movimiento
    movimiento = Movimiento("DEPÓSITO", total, cuenta.numero)
    cuenta.movimientos.append(movimiento)
    
    # Mostrar resultado
    print("\n" + Colors.GREEN + "Depósito exitoso!" + Colors.END)
    print(f"Monto depositado: ${total}")
    print(f"Nuevo saldo: ${cuenta.saldo}")
    return True

def realizar_transferencia(banco, cuenta_origen):
    print_header("TRANSFERENCIA ENTRE CUENTAS")
    
    # Obtener ID del destinatario
    destinatario_id = get_valid_input("Ingrese ID del cliente destinatario: ", int)
    
    # Buscar cuenta de destino
    cuenta_destino = banco.cuentas_por_cliente.get(destinatario_id)
    
    if not cuenta_destino:
        print(Colors.RED + "Error: Cliente destinatario no encontrado" + Colors.END)
        return False
    
    if cuenta_destino.numero == cuenta_origen.numero:
        print(Colors.RED + "Error: No puede transferir a su propia cuenta" + Colors.END)
        return False
    
    # Obtener monto a transferir
    monto = get_valid_input(f"Ingrese monto a transferir (máximo ${cuenta_origen.saldo}): ", float, min_value=0.01)
    
    # Validar fondos
    if monto > cuenta_origen.saldo:
        print(Colors.RED + "Error: Saldo insuficiente para realizar la transferencia" + Colors.END)
        return False
    
    # Realizar transferencia
    cuenta_origen.saldo -= monto
    cuenta_destino.saldo += monto
    
    # Registrar movimientos
    movimiento_origen = Movimiento("TRANSFERENCIA", -monto, cuenta_origen.numero, cuenta_destino.numero)
    movimiento_destino = Movimiento("TRANSFERENCIA", monto, cuenta_destino.numero, cuenta_origen.numero)
    
    cuenta_origen.movimientos.append(movimiento_origen)
    cuenta_destino.movimientos.append(movimiento_destino)
    
    # Mostrar resultado
    print("\n" + Colors.GREEN + "Transferencia exitosa!" + Colors.END)
    print(f"Monto transferido: ${monto}")
    print(f"Destinatario: {banco.clientes_por_id[destinatario_id].nombre}")
    print(f"Nuevo saldo: ${cuenta_origen.saldo}")
    return True

def realizar_pago_servicios(cuenta):
    print_header("PAGO DE SERVICIOS")
    
    # Menú de servicios
    servicios = {
        "1": ("Luz", 180, 350),
        "2": ("Agua", 80, 200),
        "3": ("Gas", 120, 300),
        "4": ("Internet", 250, 500)
    }
    
    print("Seleccione el servicio a pagar:")
    for key, (nombre, min_cobro, max_cobro) in servicios.items():
        print(f"{key}. {nombre} (${min_cobro}-${max_cobro})")
    print("5. Volver")
    
    opcion = get_valid_input("Seleccione una opción: ", str, servicios.keys() | {"5"})
    
    if opcion == "5":
        return False
    
    servicio, min_cobro, max_cobro = servicios[opcion]
    
    # Generar monto aleatorio basado en rangos típicos
    monto = random.randint(min_cobro, max_cobro)
    print(f"\nMonto a pagar por {servicio}: {Colors.BOLD}${monto}{Colors.END}")
    
    # Confirmar pago
    confirmar = input("\n¿Desea realizar el pago? (s/n): ").lower()
    if confirmar != 's':
        print(Colors.YELLOW + "Pago cancelado" + Colors.END)
        return False
    
    # Validar fondos
    if monto > cuenta.saldo:
        print(Colors.RED + "Error: Saldo insuficiente para realizar el pago" + Colors.END)
        return False
    
    # Realizar pago
    cuenta.saldo -= monto
    
    # Generar número de referencia
    referencia = f"REF-{random.randint(100000, 999999)}"
    
    # Registrar movimiento
    movimiento = Movimiento("PAGO_SERVICIO", -monto, cuenta.numero, servicio=servicio)
    cuenta.movimientos.append(movimiento)
    
    # Mostrar resultado
    print("\n" + Colors.GREEN + "Pago exitoso!" + Colors.END)
    print(f"Servicio: {servicio}")
    print(f"Referencia: {referencia}")
    print(f"Monto pagado: ${monto}")
    print(f"Nuevo saldo: ${cuenta.saldo}")
    return True

def consultar_saldo(cuenta):
    print_header("CONSULTA DE SALDO")
    print(f"Saldo actual: {Colors.BOLD}${cuenta.saldo}{Colors.END}")
    return True

def mostrar_movimientos(cuenta):
    print_header("HISTORIAL DE MOVIMIENTOS")
    if not cuenta.movimientos:
        print("No hay movimientos registrados")
        return
    
    print(f"{'Fecha/Hora':<20} {'Tipo':<15} {'Monto':<15} {'Detalle':<25}")
    print("-" * 60)
    for mov in cuenta.movimientos:
        color = Colors.RED if mov.monto < 0 else Colors.BLUE
        monto_str = f"${abs(mov.monto)}" if mov.monto < 0 else f"${mov.monto}"
        
        if mov.tipo == "TRANSFERENCIA":
            destino = f"A: {mov.cuenta_destino}" if mov.monto < 0 else f"De: {mov.cuenta_destino}"
            detalle = destino
        elif mov.tipo == "PAGO_SERVICIO":
            detalle = mov.servicio
        else:
            detalle = ""
            
        print(f"{mov.fecha.strftime('%d/%m/%Y %H:%M'):<20} {mov.tipo:<15} {color}{monto_str:<15}{Colors.END} {detalle:<25}")

def gestion_clientes(banco):
    print_header("GESTIÓN DE CLIENTES")
    menu = {
        "1": "Agregar cliente",
        "2": "Listar clientes",
        "3": "Editar cliente",
        "4": "Volver al menú principal"
    }
    print_menu(menu)
    
    opcion = get_valid_input("Seleccione una opción: ", str, menu.keys())
    
    if opcion == "1":
        print("\n" + "="*30)
        print("NUEVO CLIENTE")
        print("="*30)
        cliente_id = get_valid_input("ID del cliente: ", int)
        nombre = input("Nombre completo: ")
        password = input("Contraseña: ")
        
        nuevo_cliente = Cliente(cliente_id, nombre, password)
        banco.agregar_cliente(nuevo_cliente)
        
        # Crear cuenta automáticamente
        cuenta_numero = f"CTA-{cliente_id:04d}"
        nueva_cuenta = Cuenta(cuenta_numero, cliente_id, 0)
        banco.agregar_cuenta(nueva_cuenta)
        
        print(Colors.GREEN + "\nCliente y cuenta creados exitosamente!" + Colors.END)
        print(f"ID Cliente: {cliente_id}")
        print(f"Cuenta asignada: {cuenta_numero}")
    
    elif opcion == "2":
        print("\n" + "="*30)
        print("LISTADO DE CLIENTES")
        print("="*30)
        if not banco.clientes:
            print("No hay clientes registrados")
        else:
            clientes_ordenados = banco.quicksort(banco.clientes, 'id')
            print(f"{'ID':<10} {'Nombre':<25} {'Cuenta Asignada':<15}")
            print("-" * 50)
            for cliente in clientes_ordenados:
                cuenta = banco.cuentas_por_cliente.get(cliente.id)
                cuenta_num = cuenta.numero if cuenta else "Sin cuenta"
                print(f"{cliente.id:<10} {cliente.nombre:<25} {cuenta_num:<15}")
    
    input("\nPresione Enter para continuar...")

def gestion_cajeros(banco):
    print_header("GESTIÓN DE CAJEROS")
    menu = {
        "1": "Agregar cajero",
        "2": "Listar cajeros",
        "3": "Editar billetes",
        "4": "Volver al menú principal"
    }
    print_menu(menu)
    
    opcion = get_valid_input("Seleccione una opción: ", str, menu.keys())
    
    if opcion == "1":
        print("\n" + "="*30)
        print("NUEVO CAJERO")
        print("="*30)
        cajero_id = get_valid_input("ID del cajero: ", int)
        ubicacion = input("Ubicación: ")
        
        nuevo_cajero = Dispensador(cajero_id, ubicacion)
        banco.dispensadores.append(nuevo_cajero)
        
        print(Colors.GREEN + "\nCajero creado exitosamente!" + Colors.END)
    
    elif opcion == "2":
        print("\n" + "="*30)
        print("LISTADO DE CAJEROS")
        print("="*30)
        if not banco.dispensadores:
            print("No hay cajeros registrados")
        else:
            cajeros_ordenados = banco.quicksort(banco.dispensadores, 'id')
            print(f"{'ID':<10} {'Ubicación':<25} {'Billetes Disponibles'}")
            print("-" * 60)
            for cajero in cajeros_ordenados:
                billetes_info = ", ".join([f"${k}:{v}" for k, v in cajero.billetes.items()])
                print(f"{cajero.id:<10} {cajero.ubicacion:<25} {billetes_info}")
    
    elif opcion == "3":
        if not banco.dispensadores:
            print(Colors.RED + "No hay cajeros registrados" + Colors.END)
        else:
            cajero_id = get_valid_input("ID del cajero a editar: ", int)
            cajero = next((c for c in banco.dispensadores if c.id == cajero_id), None)
            
            if cajero:
                print("\n" + "="*30)
                print(f"EDITAR CAJERO #{cajero_id}")
                print("="*30)
                print("Ingrese nueva cantidad de billetes:")
                
                for denom in [200, 100, 50, 20]:
                    cantidad = get_valid_input(f"Billetes de ${denom}: ", int, min_value=0)
                    cajero.billetes[denom] = cantidad
                
                print(Colors.GREEN + "\nCajero actualizado exitosamente!" + Colors.END)
            else:
                print(Colors.RED + f"No se encontró cajero con ID {cajero_id}" + Colors.END)
    
    input("\nPresione Enter para continuar...")

def autenticar_usuario(banco):
    print_header("AUTENTICACIÓN")
    try:
        cliente_id = int(input("Ingrese su ID de cliente: "))
        password = input("Ingrese su contraseña: ")
    except:
        return None
    
    cliente = banco.clientes_por_id.get(cliente_id)
    if cliente and cliente.password == password:
        return banco.cuentas_por_cliente.get(cliente_id)
    return None

# Función principal con menús jerárquicos
def main():
    # Crear banco y datos de ejemplo
    banco = Banco()
    
    # Crear clientes de ejemplo
    cliente1 = Cliente(1, "Luis Sánchez", "1234")
    cliente2 = Cliente(2, "Paola Olivos", "5678")
    cliente3 = Cliente(3, "Luis Salazar", "9012")
    banco.agregar_cliente(cliente1)
    banco.agregar_cliente(cliente2)
    banco.agregar_cliente(cliente3)
    
    # Crear cuentas de ejemplo
    cuenta1 = Cuenta("001-123456", 1, 5000)
    cuenta2 = Cuenta("001-654321", 2, 3000)
    cuenta3 = Cuenta("001-987654", 3, 7000)
    banco.agregar_cuenta(cuenta1)
    banco.agregar_cuenta(cuenta2)
    banco.agregar_cuenta(cuenta3)
    
    # Crear dispensadores de ejemplo
    dispensador1 = Dispensador(1, "Sucursal Central")
    dispensador1.billetes = {200: 10, 100: 20, 50: 30, 20: 40}
    banco.dispensadores.append(dispensador1)
    
    dispensador2 = Dispensador(2, "Sucursal Norte")
    dispensador2.billetes = {200: 5, 100: 15, 50: 25, 20: 35}
    banco.dispensadores.append(dispensador2)
    
    # Menú principal
    while True:
        print_header("CAJERO AUTOMÁTICO MULTIFUNCIÓN")
        main_menu = {
            "1": "Operaciones Bancarias",
            "2": "Gestión de Clientes",
            "3": "Gestión de Cajeros",
            "4": "Salir del Sistema"
        }
        print_menu(main_menu)
        
        opcion = get_valid_input("Seleccione una opción: ", str, main_menu.keys())
        
        if opcion == "1":  # Operaciones Bancarias
            cuenta_actual = autenticar_usuario(banco)
            if not cuenta_actual:
                print(Colors.RED + "\nError: Autenticación fallida" + Colors.END)
                input("\nPresione Enter para continuar...")
                continue
                
            while True:
                print_header(f"OPERACIONES BANCARIAS - Cliente: {banco.clientes_por_id[cuenta_actual.cliente_id].nombre}")
                operaciones_menu = {
                    "1": "Retiro de Efectivo",
                    "2": "Depósito",
                    "3": "Transferencia",
                    "4": "Pago de Servicios",
                    "5": "Consulta de Saldo",
                    "6": "Historial de Movimientos",
                    "7": "Volver al Menú Principal"
                }
                print_menu(operaciones_menu)
                
                sub_opcion = get_valid_input("Seleccione una operación: ", str, operaciones_menu.keys())
                
                if sub_opcion == "1":  # Retiro
                    if banco.dispensadores:
                        realizar_retiro(banco, cuenta_actual, banco.dispensadores[0])
                    else:
                        print(Colors.RED + "No hay dispensadores disponibles" + Colors.END)
                    input("\nPresione Enter para continuar...")
                
                elif sub_opcion == "2":  # Depósito
                    if banco.dispensadores:
                        realizar_deposito(banco, cuenta_actual, banco.dispensadores[0])
                    else:
                        print(Colors.RED + "No hay dispensadores disponibles" + Colors.END)
                    input("\nPresione Enter para continuar...")
                
                elif sub_opcion == "3":  # Transferencia
                    realizar_transferencia(banco, cuenta_actual)
                    input("\nPresione Enter para continuar...")
                
                elif sub_opcion == "4":  # Pago de Servicios
                    realizar_pago_servicios(cuenta_actual)
                    input("\nPresione Enter para continuar...")
                
                elif sub_opcion == "5":  # Consulta de Saldo
                    consultar_saldo(cuenta_actual)
                    input("\nPresione Enter para continuar...")
                
                elif sub_opcion == "6":  # Movimientos
                    mostrar_movimientos(cuenta_actual)
                    input("\nPresione Enter para continuar...")
                
                elif sub_opcion == "7":
                    break
        
        elif opcion == "2":  # Gestión de Clientes
            gestion_clientes(banco)
        
        elif opcion == "3":  # Gestión de Cajeros
            gestion_cajeros(banco)
        
        elif opcion == "4":  # Salir
            print(Colors.YELLOW + "\nGracias por usar nuestro sistema. ¡Hasta pronto!" + Colors.END)
            sys.exit()

if __name__ == "__main__":
    main()