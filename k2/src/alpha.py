import sys
import time
import signal
import subprocess
import platform

if platform.system() != "Linux":
    print("This script only works on Linux.")
    sys.exit(1)

class bcolors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[31m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    BGRED = '\033[41m'
    WHITE = '\033[37m'
    CYAN = '\033[36m'

def timelog():
    current_time = time.localtime()
    ctime = time.strftime('%H:%M:%S', current_time)
    return "["+ ctime + "]"

def shutdown():
    print("")
    print(bcolors.BGRED + bcolors.WHITE + timelog() + "[info] shutting down k2anon" + bcolors.ENDC +"\n\n")
    sys.exit()

def sigint_handler(signum, frame):
    print('\n user interrupt ! shutting down')
    shutdown()

signal.signal(signal.SIGINT, sigint_handler)

def logo():
    print(bcolors.CYAN + bcolors.BOLD)
    print(r"""
@@@  @@@   @@@@@@   
@@@  @@@  @@@@@@@@  
@@!  !@@       @@@  
!@!  @!!      @!@   
@!@@!@!      !!@    
!!@!!!      !!:     
!!: :!!    !:!      
:!:  !:!  :!:       
 ::  :::  :: :::::  
 :   :::  :: : :::
    """)
    print(bcolors.ENDC)

def usage():
    logo()
    print(bcolors.YELLOW + bcolors.BOLD + "    LINUX TOR ANONYMIZATION TOOL" + bcolors.ENDC)
    print("""
    USAGE:
        k2anon start -----(start k2anon)
        k2anon start -i <interface(s)> -----(start with macchanger)
        k2anon stop  -----(stop k2anon)
    """)
    sys.exit()

def internet_on():
    while True:
        try:
            import urllib.request
            urllib.request.urlopen('https://check.torproject.org/', timeout=1)
            return True
        except:
            continue
        break

def tor_status():
    try:
        import urllib.request
        response = urllib.request.urlopen('https://check.torproject.org/')
        status_message = response.read().decode('utf-8')
        if 'Congratulations' in status_message:
            return True
        else:
            return False
    except:
        return False

def ip():
    try:
        import urllib.request
        if(internet_on() and tor_status()):
            response = urllib.request.urlopen('https://check.torproject.org/')
            ipadd = "Tor is enabled\n" + response.read().decode('utf-8')
        elif (internet_on() and not tor_status()):
            response = urllib.request.urlopen('http://ipinfo.io/ip')
            ipadd = "Tor is disabled\nYour IP address appears to be: " + response.read().decode('utf-8')
        return ipadd
    except:
        return "Unable to fetch IP information"

def change_macaddr(interfaces):
    print(timelog()+" Changing MAC Addresses...")
    for interface in interfaces:
        print(timelog() + bcolors.BLUE + bcolors.BOLD + " Changing: " + interface + bcolors.ENDC)
        try:
            subprocess.call(["ifconfig", interface ,"down"])
            subprocess.call(["macchanger", "-r" , interface])
            subprocess.call(["ifconfig", interface ,"up"])
            print(timelog() + bcolors.GREEN + "Successfully changed MAC for " + interface + bcolors.ENDC)
        except Exception as e:
            print(timelog() + bcolors.RED + "Failed to change MAC for " + interface + ": " + str(e) + bcolors.ENDC)
    print(timelog()+bcolors.GREEN+" MAC Addresses changed"+bcolors.ENDC)
    print(timelog()+" Restarting Network Manager...")
    try:
        subprocess.call(["service", "network-manager", "restart"])
        print(bcolors.GREEN+"[done]"+bcolors.ENDC)
    except:
        print(bcolors.RED+"[failed - trying systemctl]"+bcolors.ENDC)
        try:
            subprocess.call(["systemctl", "restart", "NetworkManager"])
            print(bcolors.GREEN+"[done]"+bcolors.ENDC)
        except Exception as e:
            print(bcolors.RED+"[failed]"+bcolors.ENDC)
            print(timelog() + "Error restarting network manager: " + str(e))

def start_k2anon():
    TorrcCfgString = """
VirtualAddrNetwork 10.0.0.0/10
AutomapHostsOnResolve 1
TransPort 9040
DNSPort 53
"""

    resolvString = "nameserver 127.0.0.1"

    Torrc = "/etc/tor/torrc"
    resolv = "/etc/resolv.conf"

    print(timelog()+" Configuring torrc file...")
    try:
        with open(Torrc, "a") as myfile:
            myfile.write(TorrcCfgString)
        print(bcolors.GREEN+"[torrc configured]"+bcolors.ENDC)
    except Exception as e:
        print(bcolors.RED+"[torrc configuration failed]"+bcolors.ENDC)
        print(timelog() + "Error: " + str(e))

    print(timelog()+" Configuring DNS resolv.conf file...")
    try:
        with open(resolv, "w") as myfile:
            myfile.write(resolvString)
        print(bcolors.GREEN+"[resolv.conf configured]"+bcolors.ENDC)
    except Exception as e:
        print(bcolors.RED+"[resolv.conf configuration failed]"+bcolors.ENDC)
        print(timelog() + "Error: " + str(e))

    print(timelog()+" Starting tor service...")
    try:
        subprocess.call(["service", "tor", "start"])
        print(bcolors.GREEN+"[tor started]"+bcolors.ENDC)
    except:
        print(bcolors.RED+"[tor start failed - trying systemctl]"+bcolors.ENDC)
        try:
            subprocess.call(["systemctl", "start", "tor"])
            print(bcolors.GREEN+"[tor started]"+bcolors.ENDC)
        except Exception as e:
            print(bcolors.RED+"[tor failed to start]"+bcolors.ENDC)
            print(timelog() + "Error: " + str(e))

    print(timelog()+" Setting up iptables rules...")
    try:
        import pwd
        tor_uid = pwd.getpwnam('debian-tor').pw_uid
    except:
        try:
            import pwd
            tor_uid = pwd.getpwnam('tor').pw_uid
        except:
            tor_uid = "unknown"

    iptables_rules = """
NON_TOR="192.168.1.0/24 192.168.0.0/24"
TOR_UID=%s
TRANS_PORT="9040"

iptables -F
iptables -t nat -F
iptables -t nat -A OUTPUT -m owner --uid-owner $TOR_UID -j RETURN
iptables -t nat -A OUTPUT -p udp --dport 53 -j REDIRECT --to-ports 53
for NET in $NON_TOR 127.0.0.0/9 127.128.0.0/10; do
 iptables -t nat -A OUTPUT -d $NET -j RETURN
done
iptables -t nat -A OUTPUT -p tcp --syn -j REDIRECT --to-ports $TRANS_PORT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
for NET in $NON_TOR 127.0.0.0/8; do
 iptables -A OUTPUT -d $NET -j ACCEPT
done
iptables -A OUTPUT -m owner --uid-owner $TOR_UID -j ACCEPT
iptables -A OUTPUT -j REJECT
""" % (tor_uid)

    try:
        subprocess.call(['bash', '-c', iptables_rules])
        print(bcolors.GREEN+"[iptables configured]"+bcolors.ENDC)
    except Exception as e:
        print(bcolors.RED+"[iptables configuration failed]"+bcolors.ENDC)
        print(timelog() + "Error: " + str(e))

    print(timelog()+" Fetching current status and IP...")
    print(timelog()+" CURRENT STATUS AND IP : "+bcolors.GREEN+ip()+bcolors.ENDC)

def stop_k2anon():
    print(bcolors.RED+timelog()+" STOPPING k2anon"+bcolors.ENDC)
    
    print(timelog()+" Flushing iptables...")
    IpFlush = """
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
iptables -t nat -F
iptables -t mangle -F
iptables -F
iptables -X
"""
    try:
        subprocess.call(['bash', '-c', IpFlush])
        print(bcolors.GREEN+"[iptables flushed]"+bcolors.ENDC)
    except Exception as e:
        print(bcolors.RED+"[iptables flush failed]"+bcolors.ENDC)
        print(timelog() + "Error: " + str(e))

    print(timelog()+" Restarting Network manager...")
    try:
        subprocess.call(["service", "network-manager", "restart"])
        print(bcolors.GREEN+"[network manager restarted]"+bcolors.ENDC)
    except:
        print(bcolors.RED+"[network manager restart failed - trying systemctl]"+bcolors.ENDC)
        try:
            subprocess.call(["systemctl", "restart", "NetworkManager"])
            print(bcolors.GREEN+"[network manager restarted]"+bcolors.ENDC)
        except Exception as e:
            print(bcolors.RED+"[network manager failed to restart]"+bcolors.ENDC)
            print(timelog() + "Error: " + str(e))

    print(timelog()+" Stopping tor service...")
    try:
        subprocess.call(["service", "tor", "stop"])
        print(bcolors.GREEN+"[tor stopped]"+bcolors.ENDC)
    except:
        print(bcolors.RED+"[tor stop failed - trying systemctl]"+bcolors.ENDC)
        try:
            subprocess.call(["systemctl", "stop", "tor"])
            print(bcolors.GREEN+"[tor stopped]"+bcolors.ENDC)
        except Exception as e:
            print(bcolors.RED+"[tor failed to stop]"+bcolors.ENDC)
            print(timelog() + "Error: " + str(e))

    print(timelog()+" Fetching current status and IP...")
    print(timelog()+" CURRENT STATUS AND IP : "+bcolors.GREEN+ip()+bcolors.ENDC)

arg = sys.argv[1:]

if len(arg) >= 1:
    if sys.argv[1] == "start":
        logo()
        if len(arg) >= 2:
            if sys.argv[2] == "-i":
                interfaces = []
                for interface in sys.argv[3:]:
                    interfaces.append(interface)
                change_macaddr(interfaces)
        start_k2anon()
    elif sys.argv[1] == "stop":
        logo()
        stop_k2anon()
else:
    usage()
