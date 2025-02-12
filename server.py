from flask import Flask, request, jsonify, render_template, send_file
import sqlite3
import pandas as pd
from io import BytesIO
import traceback  # 用于打印详细的错误日志

app = Flask(__name__)

# 資料庫設置
DB_NAME = 'system_info.db'

# 版本基準號
JAVA8_BASE_VERSION = "1.8.0_291"
JAVA7_BASE_VERSION = "1.7.0_80"
ACROBAT_BASE_VERSION = "2020.013.20074"

# 初始化資料庫，若資料表不存在則創建
def init_db():
    try:
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
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        traceback.print_exc()

# 儲存或更新資料
def save_to_db(hostname, ip_addresses, java8_version, java7_version, adobe_reader_version, acrobat_version, winpatch_info, antivirus_info):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO system_info (hostname, ip_addresses, java8_version, java7_version, adobe_reader_version, acrobat_version, winpatch_info, antivirus_info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (hostname, ip_addresses, java8_version, java7_version, adobe_reader_version, acrobat_version, winpatch_info, antivirus_info))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving data to DB: {str(e)}")
        traceback.print_exc()

# 獲取所有資料
def get_all_data():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT * FROM system_info')
        data = c.fetchall()
        conn.close()
        return data
    except Exception as e:
        print(f"Error fetching data from DB: {str(e)}")
        traceback.print_exc()
        return []

# 比對版本
def compare_version(current_version, base_version):
    if current_version is None:
        return "missing"  # 表示沒有安裝
    if current_version < base_version:
        return "old"  # 版本過舊
    return "new"  # 版本較新

# 根路徑處理 GET 請求，顯示資料
@app.route('/', methods=['GET'])
def index():
    try:
        data = get_all_data()
        for item in data:
            item = list(item)
            item[2] = compare_version(item[2], JAVA8_BASE_VERSION)
            item[3] = compare_version(item[3], JAVA7_BASE_VERSION)
            item[5] = compare_version(item[5], ACROBAT_BASE_VERSION)
        return render_template('index.html', data=data)
    except Exception as e:
        print(f"Error in index route: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

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
        print(f"Error in upload route: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# 导出 Excel 文件
@app.route('/export_excel', methods=['GET'])
def export_excel():
    try:
        data = get_all_data()

        # Prepare the data to be exported to Excel
        formatted_data = []
        for item in data:
            formatted_item = list(item)
            formatted_item[2] = compare_version(formatted_item[2], JAVA8_BASE_VERSION)
            formatted_item[3] = compare_version(formatted_item[3], JAVA7_BASE_VERSION)
            formatted_item[5] = compare_version(formatted_item[5], ACROBAT_BASE_VERSION)
            formatted_data.append(formatted_item)

        # Create a DataFrame from the formatted data
        columns = ['Hostname', 'IP 地址', 'Java 8 版本', 'Java 7 版本', 'Adobe Reader 版本', 'Acrobat 版本', 'Windows 更新', '防毒軟體', 'Java 8 比對結果', 'Java 7 比對結果', 'Acrobat 比對結果', 'KB 更新結果', '防毒軟體檢查']
        df = pd.DataFrame(formatted_data, columns=columns)

        # Create a BytesIO buffer to store the Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="System Info")
        output.seek(0)

        # Return the Excel file as an attachment
        return send_file(output, as_attachment=True, download_name="system_info.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        print(f"Error in /export_excel route: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "Failed to generate Excel file"}), 500

if __name__ == '__main__':
    init_db()  # 初始化資料庫
    app.run(host='0.0.0.0', port=5000)
