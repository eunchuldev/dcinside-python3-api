import requests
from pprint import pprint
import subprocess, base64, os, sys, tempfile, time

def getVpngateServerList(country_keyword="Korea"):
    raw_data = requests.get('http://www.vpngate.net/api/iphone/').text
    lines = (i.split(',') for i in raw_data.splitlines())
    if country_keyword: 
        filtered = [i for i in lines if len(i)>1 and country_keyword in i[6 if len(country_keyword)==2 else 5]]
        return filtered
    else:
        return [i for i in lines[2:] if len(i) > 1]
    #print([i[2] for i in filtered])
    #sorted = sorted(filtered, key=lambda i: float(i[2]), reverse=True)
    #print(best)
    
def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)

def start(config_data):
    _, temp_path = tempfile.mkstemp()
    with open(temp_path, 'w') as f:
        f.write(base64.b64decode(config_data).decode("utf-8"))
        f.write('\nscript-security 2\nup /etc/openvpn/update-resolv-conf\ndown /etc/openvpn/update-resolv-conf\ndown-pre')
    p = subprocess.Popen(['openvpn', '--config', temp_path], stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(p.stdout.readline, ""):
        if "Initialization Sequence Completed" in stdout_line:
            break
        elif "will try again" in stdout_line or "process restarting" in stdout_line:
            stop(p)
            return None
        else:
            print(stdout_line)
    return p

def stop(p):
    p.kill()
    #os.system("sudo kill %d"%(p.pid))
    while p.poll() == None:
        time.sleep(0.5)

def do(func, n=1):
    vpn_list = getVpngateServerList()
    n = min(n, len(vpn_list))
    for i in range(n):
        print("starting..")
        p = start(vpn_list[i][-1])
        print(p)
        if p:
            func()
            stop(p)

if __name__ == '__main__':
    vpn_list = getVpngateServerList()
    print('pull-filter ignore "dhcp-option DNS"\n' + base64.b64decode(vpn_list[0][-1]).decode("utf-8"))
    exit(1)
    l = getVpngateServerList()
    p = start(l[0][-1])
    try:
        time.sleep(1000)
    except:
        pass
    stop(p)
