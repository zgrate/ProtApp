import netifaces
import scapy.all as scapy
import socket
from kivy.logger import Logger


def network_scan(ip=socket.gethostbyname(socket.gethostname()), timeout=5):
    arp_req_frame = scapy.ARP(pdst=ip)
    broadcast_ether_frame = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")

    broadcast_ether_arp_req_frame = broadcast_ether_frame / arp_req_frame
    answered_list = scapy.srp(broadcast_ether_arp_req_frame, timeout=timeout, verbose=False)[0]
    result = []
    for i in range(0, len(answered_list)):
        client_dict = {"ip": answered_list[i][1].psrc, "mac": answered_list[i][1].hwsrc}
        result.append(client_dict)

    return list(map(lambda d: d["ip"], result))


def ping_check(ip, port=48999):
    return True
    with socket.socket() as a_socket:
        a_socket.settimeout(1)
        return a_socket.connect_ex((ip, port)) == 0


def open_socket(ip, port=48999):
    s = socket.socket()
    s.settimeout(5)
    print(s.connect((ip, port)))
    return s


def get_host(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception as e:
        Logger.warn("NetworkHelper: Error from discovery " + str(e))
        return "Unknown"



def get_hostnames(listIp):
    return list(map(lambda d: (get_host(d), d), listIp))


def send(packet: bytes, s=None, ip="", port=48999):
    if s is None:
        print("Connecting to socket...")
        s = socket.socket()
        print(s.connect((ip, port)))
        s.settimeout(5)


    try:
        if s.send(packet) == 0:
            Logger.warning("NetworkHelper: Sent empty packet! " + str(packet))
            return "Empty Response"
    except Exception as e:
        Logger.exception("Exception while sending packet!", e)
        return "Error sending packet!"

    return "ok"


def get_current_default_ip_address_with_mask():
    default = netifaces.gateways()["default"]
    addresses = netifaces.ifaddresses(default[netifaces.AF_INET][1])[netifaces.AF_INET][0]
    return addresses["addr"] + "/" + str(sum(bin(int(x)).count('1') for x in addresses['netmask'].split('.')))
