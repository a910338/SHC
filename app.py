import os
from flask import Flask, request, jsonify, render_template
import sqlite3
import csv
import io

app = Flask(__name__)

# 資料庫名稱
DB_NAME = 'system_info.db'

# 版本基準號（如果你希望後端做初步比對，可使用這些基準）
JAVA8_BASE_VERSION = "1.8.0_291"
JAVA7_BASE_VERSION = "1.7.0_80"
ACROBAT_BASE_VERSION = "2020.013.20074"

#############################
# 資料庫相關函數
#############################

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

def save_to_db(hostname, ip_addresses, java8_version, java7_version,
               adobe_reader_version, acrobat_version, winpatch_info, antivirus_info):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO system_info 
        (hostname, ip_addresses, java8_version, java7_version, adobe_reader_version, acrobat_version, winpatch_info, antivirus_info)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (hostname, ip_addresses, java8_version, java7_version,
          adobe_reader_version, acrobat_version, winpatch_info, antivirus_info))
    conn.commit()
    conn.close()

def get_all_data():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM system_info')
    data = c.fetchall()
    conn.close()
    return data

# 版本比對函數（目前 GET / 傳回的資料未做比對，前端可自行比對）
def compare_version(current_version, base_version):
    if current_version is None:
        return "missing"  # 未安裝
    # 此處僅做字串比較，依需求可改為數值比對
    return "old" if current_version < base_version else "new"

#############################
# API 端點
#############################

# 首頁：顯示所有資產資料（傳回原始資料給前端，由前端動態比對）
@app.route('/', methods=['GET'])
def index():
    data = get_all_data()
    data_list = []
    for item in data:
        # 每筆資產為一個包含 8 個欄位的列表：
        # [hostname, ip_addresses, java8_version, java7_version, adobe_reader_version, acrobat_version, winpatch_info, antivirus_info]
        data_list.append(list(item))
    return render_template('index.html', data=data_list)

# 新增資產 (POST)
@app.route('/upload', methods=['POST'])
def upload_data():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data received"}), 400
        hostname = data.get("hostname")
        ip_addresses = data.get("ip_addresses")[0] if data.get("ip_addresses") else ""
        java8_version = data.get("java8_version")
        java7_version = data.get("java7_version")
        adobe_reader_version = data.get("adobe_reader_version")
        acrobat_version = data.get("acrobat_version")
        winpatch_info = data.get("winpatch_info")
        antivirus_info = data.get("antivirus_info")
        save_to_db(hostname, ip_addresses, java8_version, java7_version,
                   adobe_reader_version, acrobat_version, winpatch_info, antivirus_info)
        return jsonify({"message": "Data received and saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# 更新資產 (PUT)
@app.route('/update/<hostname>', methods=['PUT'])
def update_data(hostname):
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data received"}), 400
        ip_addresses = data.get("ip_addresses")[0] if data.get("ip_addresses") else ""
        java8_version = data.get("java8_version")
        java7_version = data.get("java7_version")
        adobe_reader_version = data.get("adobe_reader_version")
        acrobat_version = data.get("acrobat_version")
        winpatch_info = data.get("winpatch_info")
        antivirus_info = data.get("antivirus_info")
        save_to_db(hostname, ip_addresses, java8_version, java7_version,
                   adobe_reader_version, acrobat_version, winpatch_info, antivirus_info)
        return jsonify({"message": f"Data for {hostname} updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# 刪除資產 (DELETE)
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

# 匯入資產 (POST)，假設 CSV 檔案
@app.route('/import', methods=['POST'])
def import_assets():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    try:
        # 將上傳的檔案內容解碼為字串，假設檔案編碼為 UTF-8
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        headers = next(csv_input)  # 略過標題列
        count = 0
        for row in csv_input:
            if len(row) < 8:
                continue  # 欄位不足略過
            # CSV 欄位依序為：hostname, ip_addresses, java8_version, java7_version,
            # adobe_reader_version, acrobat_version, winpatch_info, antivirus_info
            hostname, ip_addresses, java8_version, java7_version, adobe_reader_version, acrobat_version, winpatch_info, antivirus_info = row[:8]
            save_to_db(hostname, ip_addresses, java8_version, java7_version,
                       adobe_reader_version, acrobat_version, winpatch_info, antivirus_info)
            count += 1
        return jsonify({'message': f'Successfully imported {count} assets.'}), 200
    except Exception as e:
        return jsonify({'error': f'Error importing assets: {str(e)}'}), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
