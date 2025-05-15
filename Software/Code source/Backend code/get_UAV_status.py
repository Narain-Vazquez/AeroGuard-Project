import requests

# URL for UAV status
# 无人机状态的URL
url_for_UAV_status = "http://127.0.0.1:5000/sysapi/Task/GetUAVStatus?projectId=28"

# 默认的 UAV 状态
DEFAULT_UAV_STATUS = {
    "code": 0,
    "msg": "成功",
    "data": {
        "planId": None,
        "time": "1970-01-01 00:00:00", # 设为默认时间，避免 None 导致 SQL 错误
        "uavRecordId": 0,
        "projectId": 0,
        "status": "Idle",  # 默认状态：空闲
        "battery": 100,  # 默认电量
        "altitude": 0,  # 默认高度
        "speed": 0,  # 默认速度
    },
    "error": None
}

def get_UAV_status():
    try:
        response = requests.get(url_for_UAV_status, timeout=5)  # 设置超时时间
        if response.status_code == 200:
            UAV_status = response.json()

            # Test interface
            # 测试接口
            '''
            plan_id = UAV_status["data"]["planId"]
            flight_time = UAV_status["data"]["time"]

            # print(plan_id)
            # print(flight_time)
            '''

            if UAV_status.get("data") is None:
                print("Warning: UAV data is None, returning default status.")
                return DEFAULT_UAV_STATUS
            return UAV_status
        else:
            # Failed to retrieve UAV status
            # 无人机状态获取失败
            print(f"Failed to retrieve UAV status\nError: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Request failed: {e}")

    # 返回默认状态
    return DEFAULT_UAV_STATUS



if __name__ == "__main__":
    url = get_UAV_status()
    print(url)
