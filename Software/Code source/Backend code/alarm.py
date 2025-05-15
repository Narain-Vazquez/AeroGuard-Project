# -------------------预警模块-未戴安全帽-----------------------------------------------
# -------------------Warning Module - Missing Helmet----------------------------------


from drone_video_alarm import analysis_results, analysis_results_for_QDEQ
import requests


def cap_alarm(UAV_status, path, persons=0, helmets=0, class_ids_string="", objects_location_string=""):
    """
    关于未戴安全帽的报警模块
    Warning module for missing helmets.

    :param path: img，必须，某一帧的检测画面
    :param path: img, required. The detected frame.

    :param persons: int，非必须，某一帧检测到的人数
    :param persons: int, optional. Number of people detected in the frame.

    :param helmets: int，非必须，某一帧检测到的头盔数
    :param helmets: int, optional. Number of helmets detected in the frame.
    """
    # 判断是否要预警(当前只能通过比较persons和helmets的数目来判断是否有人没戴安全帽,不能精准定位到是哪个人违规了)
    # Determine whether to issue a warning. (Currently, the comparison between `persons` and `helmets` is used to decide if someone is not wearing a helmet, but it cannot precisely locate the violator.)
    if persons > helmets:
        # print("当前人数:", persons, ",当前头盔数:", helmets, ",检测到有人未戴头盔！")
        print("Current number of people:", persons, ",Current number of helmets:", helmets,
              ",Someone is detected without a helmet!")
        # Current number of people: <persons>, Current number of helmets: <helmets>, Someone is detected without a helmet!
        # 调用接口 将违规信息写入数据库
        # Call the interface to write violation information into the database.
        # analysis_results("-1", "50", "anJiu1", path)
        # 调用接口 将违规信息写入数据库
        analysis_results_for_QDEQ("-1", "50", "QDEQ-WRJ", violation_photo=path, UAV_status=UAV_status,
                                  CurrentObject=class_ids_string, CurrentLocation=objects_location_string)

        # 新增：调用报警接口触发未戴安全帽报警
        try:
            # 使用GET请求，通过传递alarm参数触发对应报警
            response = requests.get("http://154.201.89.38:8000/trigger?alarm=helmet", timeout=5)
            if response.status_code == 200:
                print("Helmet alarm triggered successfully.")
            else:
                print("Failed to trigger helmet alarm. Status code:", response.status_code)
        except Exception as e:
            print("Error triggering helmet alarm:", e)
    else:
        # print("当前人数:", persons, ",当前头盔数:", helmets, ",符合工地安全要求。")
        print("Current number of people:", persons, ",Current number of helmets:", helmets,
              ",Meeting construction site safety requirements.")
        # Current number of people: <persons>, Current number of helmets: <helmets>, Meeting construction site safety requirements.
