import os
from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

# 資料庫設置
DB_NAME = 'system_info.db'

# 版本基準號
JAVA8_BASE_VERSION = "1.8.0_291"  # 這是 Java 8 的基準版本號
JAVA7_BASE_VERSION = "1.7.0_80"  # 這是 Java 7 的基準版本號
ACROBAT_BASE_VERSION = "2020.013.20074"  # 這是 Acrobat 的基準版本號

# 初始化資料庫，若資料表不存在則創建
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_info (
            hostname TEXT PRIMARY KEY,
            ip_addresses TEXT,
            java8_version TEXT,
            java7_version TEXT,
            adobe_reader_version TEXT,
            acrobat_version TEXT,
            winpatch_info TEXT,
            antivirus_info TEXT
        )
    ''')
    conn.commit()
    conn.close()

# 儲存或更新資料
def save_to_db(hostname, ip_addresses, java8_version, java7_version, adobe_reader_version, acrobat_version, winpatch_info, antivirus_info):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO system_info (hostname, ip_addresses, java8_version, java7_version, adobe_reader_version, acrobat_version, winpatch_info, antivirus_info)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (hostname, ip_addresses, java8_version, java7_version, adobe_reader_version, acrobat_version, winpatch_info, antivirus_info))
    conn.commit()
    conn.close()

# 獲取所有資料
def get_all_data():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM system_info')
    data = c.fetchall()
    conn.close()
    return data

# 比對版本
def compare_version(current_version, base_version):
    if current_version is None:
        return "missing"  # 表示沒有安裝
    if current_version < base_version:
        return "old"  # 版本過舊
    return "new"  # 版本較新

# 刪除資料，處理 DELETE 請求
@app.route('/delete/<hostname>', methods=['DELETE'])
def delete_data(hostname):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('DELETE FROM system_info WHERE hostname = ?', (hostname,))
        conn.commit()
        conn.close()

        return jsonify({"message": f"Data for {hostname} deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# 修改資產，處理 PUT 請求
@app.route('/update/<hostname>', methods=['PUT'])
def update_data(hostname):
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data received"}), 400  # 如果沒有接收到資料，返回 400 錯誤

        # 提取資料
        ip_addresses = data.get("ip_addresses")[0]  # 假設取第一個 IP
        java8_version = data.get("java8_version")
        java7_version = data.get("java7_version")
        adobe_reader_version = data.get("adobe_reader_version")
        acrobat_version = data.get("acrobat_version")
        winpatch_info = data.get("winpatch_info")
        antivirus_info = data.get("antivirus_info")

        # 儲存或更新資料
        save_to_db(hostname, ip_addresses, java8_version, java7_version, adobe_reader_version, acrobat_version, winpatch_info, antivirus_info)

        return jsonify({"message": f"Data for {hostname} updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# 根路徑處理 GET 請求，顯示資料
@app.route('/', methods=['GET'])
def index():
    data = get_all_data()
    for item in data:
        item = list(item)
        item[2] = compare_version(item[2], JAVA8_BASE_VERSION)
        item[3] = compare_version(item[3], JAVA7_BASE_VERSION)
        item[5] = compare_version(item[5], ACROBAT_BASE_VERSION)
    return render_template('index.html', data=data)

# 上傳資料，處理 POST 請求
@app.route('/upload', methods=['POST'])
def upload_data():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data received"}), 400  # 如果沒有接收到資料，返回 400 錯誤

        # 提取資料
        hostname = data.get("hostname")
        ip_addresses = data.get("ip_addresses")[0]  # 假設取第一個 IP
        java8_version = data.get("java8_version")
        java7_version = data.get("java7_version")
        adobe_reader_version = data.get("adobe_reader_version")
        acrobat_version = data.get("acrobat_version")
        winpatch_info = data.get("winpatch_info")
        antivirus_info = data.get("antivirus_info")

        # 儲存資料到資料庫（SQLite）
        save_to_db(hostname, ip_addresses, java8_version, java7_version, adobe_reader_version, acrobat_version, winpatch_info, antivirus_info)

        return jsonify({"message": "Data received and saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # 若沒有設定 PORT，預設使用 5000
    app.run(host='0.0.0.0', port=port)
