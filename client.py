import os
import subprocess
import re
import requests
import json
import time

# 執行命令並獲取結果
def run_command(command):
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

# 取得符合範圍的 IP 地址：192.168.x.x、10.x.x.x 和 172.x.x.x
def get_ip_addresses():
    ipconfig_output = run_command("ipconfig")
    ip_pattern = r"IPv4\s*.*:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    matches = re.findall(ip_pattern, ipconfig_output)
    filtered_ips = [ip for ip in matches if ip.startswith("192.168") or ip.startswith("10.") or ip.startswith("172.")]
    return filtered_ips if filtered_ips else ["Unknown"]

# 收集系統資訊並返回所需資料
def collect_system_info(ip_addresses, hostname):
    java8_version = ""
    java7_version = ""
    adobe_reader_version = ""
    acrobat_version = ""
    winpatch_info = ""
    antivirus_info = ""

    # 查詢 Java 版本
    wmic_output = run_command("wmic product get name,version")
    for line in wmic_output.splitlines():
        if "Java 8" in line:
            java8_version = line.split()[-1]
        if "Java 7" in line:
            java7_version = line.split()[-1]
        if "Adobe Reader" in line:
            adobe_reader_version = line.split()[-1]
        if "Acrobat" in line:
            acrobat_version = line.split()[-1]
    
    # 查詢所有 Windows 更新資訊
    powershell_command = "powershell -Command \"Get-WmiObject -Class Win32_QuickFixEngineering | Sort-Object InstalledOn -Descending | Select-Object -First 3 | Format-Table InstalledOn, HotFixID\""
    winpatch_output = run_command(powershell_command)
    if winpatch_output:
        winpatch_info = winpatch_output
    
    # 查詢防毒軟體資訊
    antivirus_info = run_command('powershell -Command "Get-CimInstance -Namespace \\"root\\SecurityCenter2\\" -ClassName AntiVirusProduct | Select-Object displayName, productState, timestamp | Format-Table -AutoSize"')

    return ip_addresses, hostname, java8_version, java7_version, adobe_reader_version, acrobat_version, winpatch_info, antivirus_info

# 發送資料到伺服器
def send_data_to_server(data):
    url = "http://127.0.0.1:5000/upload"  # 替換為伺服器的 IP 地址
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print("Data sent successfully!")
        else:
            print(f"Failed to send data: {response.status_code}")
            print(f"Server Error: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# 主程式
def main():
    ip_addresses = get_ip_addresses()
    hostname = run_command("hostname")
    system_info = collect_system_info(ip_addresses, hostname)
    
    # 準備資料並發送到伺服器
    data = {
        "hostname": hostname,
        "ip_addresses": ip_addresses,
        "java8_version": system_info[2],
        "java7_version": system_info[3],
        "adobe_reader_version": system_info[4],
        "acrobat_version": system_info[5],
        "winpatch_info": system_info[6],
        "antivirus_info": system_info[7]
    }
    
    send_data_to_server(data)

if __name__ == "__main__":
    main()
