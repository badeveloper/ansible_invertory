#!/usr/bin/python
# -*- coding: utf8 -*-
import re
import yaml
import pyVmomi
from pyVmomi import  vim
from vconnector.core import VConnector
import os.path
import json
from itertools import groupby

# Import transliterate module if needed transliterate folders names
from transliterate import  translit, get_available_language_codes

cred_file = '/home/iyurev/inv.yaml'
cache_json_file = "/tmp/invertory.json"

#Return all vCenters from YAML cred. file
def GetCred(cred_file_obj):
    cred_file_obj = open(cred_file_obj)
    cred_hash = yaml.load(cred_file_obj)
    vcenters = cred_hash["vcenters"]
    vc_creds = []
    for vc in vcenters:
        vc_creds.append(vcenters[vc])
    return vc_creds

#Transliterate , strip and replace bad symbols in VM path
def true_name(name):
    trans = translit(name, 'ru', reversed=True)
    res = re.sub(r'\(+|\)+', '', trans)
    result = res.replace(' ', '_')
    if '!' in result:
        result = re.sub(r'!', '', result)
    if '%2f' in result:
        result = re.sub(r'%2f', '/', result)
    if ',' in result:
        result = result.replace(',', '_')

    return  result[0:-1]

#Get full VM path at Datacenter Object
def get_vm_full_path(vm_parent):
    types = (vim.Folder, vim.VirtualMachine, vim.Datacenter)
    if isinstance(vm_parent, types):
     path.append(vm_parent.name)
     if hasattr(vm_parent, 'parent'):
      return get_vm_full_path(vm_parent.parent)
     else:
      return path
#Check MACADDRESS by vendor
def check_mac_addr(mac_addr, vmware_mac_addr ='00:50:56'):
    if len(mac_addr) == 17 and mac_addr[0:8] == vmware_mac_addr:
        return True
    else: return False

#Get IPADDR
def get_vm_ipaddr(guest_ipstack, guest_net):
    networks_list = ['0.0.0.0']
    if guest_ipstack and guest_net:
        ip_route = guest_ipstack[0].ipRouteConfig.ipRoute
        if ip_route:
         gateways = []
         for r in ip_route:
                 gate = r.gateway.ipAddress
                 net = r.network
                 dev_index = r.gateway.device
                 if net in networks_list:
                     lan = guest_net[int(dev_index)].network
                     for addr in guest_net:
                         if lan == addr.network and addr.ipAddress:
                             gateways.append(addr.ipAddress[0])
                             return gateways[0]
                 else:
                     for nic in guest_net:
                         if check_mac_addr(nic.macAddress) and nic.ipAddress:
                             return nic.ipAddress[0]
        else:
            return summary.guest.ipAddress
    else: return  'NO_IPADDRESS'
##############OS_Filter_lists#################################################
win_os = ['winNetStandardGuest', 'winLonghorn', 'winLonghornGuest', 'winNetEnterprise',
          'windows8Server64Guest','winLonghorn64Guest', 'windows7Server64Guest','winNetEnterpriseGuest',
          'winNetEnterprise64Guest','windows9Server64Guest', 'win2000AdvServGuest', 'windows8_64Guest']

#####################################################################################
if os.path.exists(cache_json_file):
    cash_json = json.loads(open(cache_json_file, 'r').read())
    print json.dumps(cash_json)

else:
    all_vm = []
    #All VM Count
    count = 0
    for vc_credential in GetCred(cred_file):
        connector = VConnector(
        user = vc_credential["user"],
        pwd  = vc_credential["password"],
        host=  vc_credential["host"]
                                )
        connector.connect()
        vms = connector.get_vm_view()
        result_vm = connector.collect_properties(
        view_ref=vms,
        obj_type=pyVmomi.vim.VirtualMachine,
        path_set = [ 'summary.guest', 'summary.config',  'summary', 'config.name', 'config.guestId', 'parent', 'runtime', 'guest']
        )

        for vm in result_vm:
            if vm["summary"].runtime.powerState == 'poweredOn':
                os_check = vm["config.guestId"]
                if os_check not  in win_os:

                    vm_name = vm["config.name"]
                    runtime = vm["runtime"]
                    guest   = vm["guest"]
                    summary = vm["summary"]
                    vm_summary = vm["summary.guest"]
                    summary_config  =  vm["summary.config"]
                    ram = summary_config.memorySizeMB
                    cpu_core  =  int(summary_config.numCpu)
                    annot = summary_config.annotation
                    if "parent" in vm:
                        vm_parent = vm['parent']
                    else: vm_parent = "DONT_HAVE_FOLDER"

                    path = []

                    get_vm_full_path(vm_parent)
                    count += 1
                    print (vm_name, count, true_name("_".join(path)), get_vm_ipaddr(guest.ipStack, guest.net)) #Print for debug
                    all_vm.append([vm_name, count, true_name("_".join(path)), get_vm_ipaddr(guest.ipStack, guest.net)])
    #Set host_vars dict
    host_vars = {}
    for h in  all_vm:
        host_vars.update({h[0] : {"ansible_host": h[3], "vm_name": h[0]}})
    #Grouping by "vm_path"
        sort_key = key= lambda s:s[2]
    results = {}
    for k, v in groupby(all_vm, key=sort_key):
        results[k] = list(v1[0] for v1 in v)
    #Set inv_groups dict
    inv_groups = {}
    inv = {"_meta": {"hostvars": host_vars} }
    for i in results:
            if i != '':
             inv_groups.update({i: {"hosts": results[i]}})
     #Merge dict
    result_inv = dict(inv, **inv_groups)
    #Write JSON to cache file
    write_json =  open(cache_json_file, 'aw')
    write_json.write(json.dumps(result_inv))
    print "Rewrite cache invertory JSON data!!!"








