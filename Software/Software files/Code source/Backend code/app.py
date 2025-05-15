# app.py (Flask API 部分)
import os

import time
from flask import Flask, jsonify, request, send_from_directory, Response, jsonify
from flask_cors import CORS
from db_config import get_connection

app = Flask(__name__)
CORS(app)

# 全局缓存一份最新数据
LATEST_STATS = {
    "people": 0, "vehicles": 0, "helmet_percent": 0, "fire_risk": False
}

# 获取 UAVStatus 记录接口
@app.route('/api/uavstatus', methods=['GET'])
def api_get_uavstatus():
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM UAVStatus ORDER BY id DESC LIMIT 10;"
            cursor.execute(sql)
            records = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "data": records})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 插入生产环境异常报警记录接口
@app.route('/api/productionEvent', methods=['POST'])
def api_production_event():
    try:
        data = request.get_json()
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO ProductionEvents 
            (Violator_LSNumber, EventType, time, CameraID, ViolationPhoto, T2, EventDescription)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(sql, (
                data.get("Violator_LSNumber"),
                data.get("EventType"),
                data.get("time"),
                data.get("CameraID"),
                data.get("ViolationPhoto"),
                data.get("T2", 6),
                data.get("EventDescription", "")
            ))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 插入 QDEQ 异常报警记录接口
@app.route('/api/qdeqEvent', methods=['POST'])
def api_qdeq_event():
    try:
        data = request.get_json()
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO QDEQEvents 
            (Violator_LSNumber, EventType, time, CameraID, ViolationPhoto, T2, EventDescription, ProjectId, RobotId, PlanId, RecordId, FlightTime, CurrentObject, Location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(sql, (
                data.get("Violator_LSNumber"),
                data.get("EventType"),
                data.get("time"),
                data.get("CameraID"),
                data.get("ViolationPhoto"),
                data.get("T2", 6),
                data.get("EventDescription", ""),
                data.get("ProjectId"),
                data.get("RobotId", "0"),
                data.get("PlanId"),
                data.get("RecordId"),
                data.get("FlightTime"),
                data.get("CurrentObject", ""),
                data.get("Location", "")
            ))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 插入 UAVStatus 记录接口
@app.route('/api/insertUAVStatus', methods=['POST'])
def api_insert_uav_status():
    try:
        data = request.get_json()
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO UAVStatus (PlanId, uavRecordId, FlightTime, FlvUrl, WebRtcUrl, RtmpSubUrl, hlsUrl, ProjectId, RetrievedAt)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(sql, (
                data.get("PlanId"),
                data.get("uavRecordId"),
                data.get("FlightTime"),
                data.get("FlvUrl"),
                data.get("WebRtcUrl"),
                data.get("RtmpSubUrl"),
                data.get("hlsUrl"),
                data.get("ProjectId"),
                data.get("RetrievedAt")
            ))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 设置上传文件存放目录（可根据需要调整路径）
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件最大 16MB

# 上传接口，同时将上传记录写入数据库
@app.route('/upload', methods=['POST'])
def upload_file():
    # 检查请求中是否包含文件部分
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "没有找到文件参数"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "未选择文件"}), 400

    # 生成保存文件名，这里直接使用原文件名；实际生产中可添加随机字符串或时间戳避免重复
    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # 保存文件到本地
    file.save(file_path)

    # 构造文件访问的 URL（假设服务运行在本地 5000 端口）
    file_url = request.host_url + 'uploads/' + filename

    # 插入上传记录到数据库 FileUploads 表
    try:
        conn = get_connection()  # 从 db_config 导入的数据库连接函数
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO FileUploads 
            (originalName, saveName, virtulPath, thumbnailVirtulPath, thumbnailName)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(sql, (
                file.filename,
                filename,
                file_url,
                file_url,  # 如有缩略图可单独处理
                filename
            ))
        conn.commit()
        conn.close()
    except Exception as e:
        return jsonify({"success": False, "message": "数据库写入失败", "error": str(e)}), 500

    # 返回上传成功信息及数据库记录信息
    return jsonify({
        "success": True,
        "datas": [{
            "originalName": file.filename,
            "saveName": filename,
            "virtulPath": file_url,
            "thumbnailVirtulPath": file_url,
            "thumbnailName": filename
        }],
        "message": "上传成功，文件记录已写入数据库"
    })

# 用于访问上传文件（供前端访问上传后的图片等）
@app.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/test_db', methods=['GET'])
def test_db():
    """
    测试数据库连接是否正常，执行简单查询
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 执行简单查询，确保数据库连接正常
            cursor.execute("SELECT 1 AS test_result;")
            result = cursor.fetchone()
        conn.close()
        return jsonify({
            "success": True,
            "message": "数据库连接成功",
            "result": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 新增视频流接口：直接读取 detection.py 输出的文件 latest_frame.jpg
@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            if os.path.exists("video_feed\latest_frame.jpg"):
                try:
                    with open("video_feed\latest_frame.jpg", "rb") as f:
                        frame = f.read()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                except Exception as e:
                    print("Error reading latest_frame.jpg:", e)
            time.sleep(0.05)  # 控制读取间隔，约20 FPS
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

# 获取网站右侧栏的视频列表
@app.route('/api/videos', methods=['GET'])
def get_video_list():
    # 确定 videos 文件夹所在路径
    # !! 重要：这个路径是相对于 Flask 服务器运行的位置 !!
    # 如果前端和后端不在同一个根目录，这个相对路径可能不正确
    # 建议使用环境变量或配置文件来指定 videos 目录的绝对路径
    # 假设前端构建后的 'videos' 目录位于 Flask 项目根目录下的 'frontend_dist/videos'
    # frontend_root = os.path.join(os.getcwd(), "drone-frontend/drone-frontend/public") # 这是你原来的路径，假设前端代码在此
    # videos_folder = os.path.join(frontend_root, "videos")

    # 更可靠的方式是假设 videos 目录在 Flask app.py 所在目录的某个固定相对位置
    # 例如，如果 videos 目录在 app.py 同级的 'static/videos' 下
    # videos_folder = os.path.join(os.path.dirname(__file__), 'static', 'videos')

    # 保持你原来的路径，但要确保 Flask 运行时该路径有效
    videos_folder = os.path.join(os.getcwd(), "drone-frontend/drone-frontend/public/videos")

    if not os.path.isdir(videos_folder):
         print(f"Video directory not found: {videos_folder}")
         return jsonify({"success": False, "error": "Video directory not found on server."}), 404

    try:
        # 读取 videos 文件夹中所有后缀为 .mp4 的文件
        video_files = [f for f in os.listdir(videos_folder) if f.lower().endswith(".mp4")]
        return jsonify({"success": True, "files": video_files})
    except Exception as e:
        print(f"Error reading video directory {videos_folder}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# site_stats的动态数据
@app.route("/api/site_stats", methods=["POST"])
def site_stats_post():
    global LATEST_STATS
    data = request.get_json(force=True)
    # 粗略校验
    for k in ["people","vehicles","helmet_percent","fire_risk"]:
        if k not in data: return jsonify(success=False, error="missing "+k), 400
    LATEST_STATS = data
    return jsonify(success=True)

# site_stats的动态数据
@app.route("/api/site_stats", methods=["GET"])
def site_stats_get():
    return jsonify(success=True, data=LATEST_STATS)

# 最后启动 Flask 服务
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

