from flask import Flask, render_template, request, send_file
import requests
import os
import pandas as pd
import io

def reverse_geocode(lat, lng, ak, coordtype="wgs84ll"):
    url = "https://api.map.baidu.com/reverse_geocoding/v3/"
    params = {"ak": ak, "output": "json", "coordtype": coordtype, "location": f"{lat},{lng}"}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        return ""
    data = r.json()
    if data.get("status") != 0:
        return ""
    return data.get("result", {}).get("formatted_address", "")

app = Flask(__name__)

@app.route("/", methods=["GET"]) 
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"]) 
def process():
    f = request.files.get("file")
    ak = request.form.get("ak") or os.environ.get("BAIDU_MAPS_AK", "")
    lat_col = request.form.get("lat_col")
    lng_col = request.form.get("lng_col")
    addr_col = request.form.get("addr_col")
    coordtype = request.form.get("coordtype") or "wgs84ll"
    if not f or not ak or not lat_col or not lng_col or not addr_col:
        return "缺少必要参数或AK", 400
    try:
        df = pd.read_excel(f, engine="openpyxl")
    except Exception:
        return "读取Excel失败，仅支持xlsx格式", 400
    if lat_col not in df.columns or lng_col not in df.columns:
        return "经纬度列名不存在", 400
    def to_addr(row):
        try:
            lat = float(row[lat_col])
            lng = float(row[lng_col])
        except Exception:
            return ""
        return reverse_geocode(lat, lng, ak, coordtype)
    df[addr_col] = df.apply(to_addr, axis=1)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="processed.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
