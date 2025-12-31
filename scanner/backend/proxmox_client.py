import os
import logging
from proxmoxer import ProxmoxAPI
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

class ProxmoxClient:
    def __init__(self):
        self.host = os.getenv("PROXMOX_HOST")
        self.user = os.getenv("PROXMOX_USER")  # e.g., root@pam
        self.token_id = os.getenv("PROXMOX_TOKEN_ID")
        self.token_secret = os.getenv("PROXMOX_TOKEN_SECRET")
        self.verify_ssl = os.getenv("PROXMOX_VERIFY_SSL", "false").lower() == "true"
        self.proxmox = None
        self.enabled = False

        if self.host and self.user and self.token_id and self.token_secret:
            try:
                self.proxmox = ProxmoxAPI(
                    self.host,
                    user=self.user,
                    token_name=self.token_id,
                    token_value=self.token_secret,
                    verify_ssl=self.verify_ssl
                )
                self.enabled = True
                logger.info(f"Proxmox integration enabled for host {self.host}")
            except Exception as e:
                logger.error(f"Failed to initialize Proxmox client: {e}")
        else:
            logger.warning("Proxmox integration disabled. Missing credential variables.")

    def get_all_vms(self):
        """
        Retorna una lista plana de todas las VMs y Contenedores
        con sus propiedades clave (vmid, name, status, type, macs, ips)
        """
        if not self.enabled:
            return []

        inventory = []
        try:
            nodes = self.proxmox.nodes.get()
            for node in nodes:
                node_name = node['node']
                
                # 1. Get QEMU (VMs)
                vms = self.proxmox.nodes(node_name).qemu.get()
                for vm in vms:
                    vm_info = {
                        'vmid': vm.get('vmid'),
                        'name': vm.get('name'),
                        'status': vm.get('status'),
                        'type': 'qemu',
                        'node': node_name,
                        'macs': [],
                        'ips': []
                    }
                    
                    # Try to get network info (MACs) from config
                    try:
                        config = self.proxmox.nodes(node_name).qemu(vm['vmid']).config.get()
                        # Parse net0, net1, etc looking for mac=...
                        for key, value in config.items():
                            if key.startswith('net'):
                                # Format: virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0...
                                parts = value.split(',')
                                for p in parts:
                                    if '=' in p and len(p.split('=')[0]) == 0: # implicit
                                        pass
                                    elif '=' in p:
                                        k, v = p.split('=', 1)
                                        if len(v) == 17 and ':' in v: # Simple MAC check
                                            vm_info['macs'].append(v.lower())
                                    elif len(p) == 17 and ':' in p: # direct mac
                                            vm_info['macs'].append(p.lower())
                    except:
                        pass
                    
                    # Try to get IPs from Guest Agent
                    if vm.get('status') == 'running':
                        try:
                            net_ifaces = self.proxmox.nodes(node_name).qemu(vm['vmid']).agent('network-get-interfaces').get()
                            for iface in net_ifaces.get('result', []):
                                for ip_info in iface.get('ip-addresses', []):
                                    if ip_info['ip-address-type'] == 'ipv4' and ip_info['ip-address'] != '127.0.0.1':
                                        vm_info['ips'].append(ip_info['ip-address'])
                        except:
                            pass # Agent not running or not installed
                            
                    inventory.append(vm_info)

                # 2. Get LXC (Containers)
                lxcs = self.proxmox.nodes(node_name).lxc.get()
                for lxc in lxcs:
                    lxc_info = {
                        'vmid': lxc.get('vmid'),
                        'name': lxc.get('name'),
                        'status': lxc.get('status'),
                        'type': 'lxc',
                        'node': node_name,
                        'macs': [],
                        'ips': []
                    }
                    
                    # Get config for IPs and MACs
                    try:
                        config = self.proxmox.nodes(node_name).lxc(lxc['vmid']).config.get()
                        for key, value in config.items():
                            if key.startswith('net'):
                                # Format: name=eth0,bridge=vmbr0,hwaddr=AA:BB:CC:...,ip=192.168.x.x/24
                                parts = value.split(',')
                                for p in parts:
                                    if 'hwaddr=' in p:
                                        lxc_info['macs'].append(p.split('=')[1].lower())
                                    if 'ip=' in p:
                                        ip_part = p.split('=')[1]
                                        if ip_part != 'dhcp' and '/' in ip_part:
                                            lxc_info['ips'].append(ip_part.split('/')[0])
                    except:
                        pass
                    
                    inventory.append(lxc_info)

        except Exception as e:
            logger.error(f"Error fetching Proxmox inventory: {e}")
            
        return inventory

proxmox_client = ProxmoxClient()
