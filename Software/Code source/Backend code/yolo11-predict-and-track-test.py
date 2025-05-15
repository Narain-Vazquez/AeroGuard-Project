# track by yolo_model   ---------------   yolo模型预测+追踪 / YOLO model prediction + tracking

import datetime
import os

import requests

from ClassCountFormatter import generate_detailed_statistics_string, generate_detailed_vehicle_statistics_string
from ObjectLocationFormatter import generate_objects_location_string
from get_UAV_status import get_UAV_status

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
import time
import cv2
import supervision as sv
import threading
import numpy as np
from alarm import cap_alarm
from ultralytics.models import YOLO
from draw import test_corner_boxes
from vehicle_alarm import vehicle_alarm, vehicle_alarm_last


# ----------------函数（等待放置于相关工具类）---------------------------------- / ----------------Function (to be placed in relevant utility classes)----------------------------------
# 对于每一帧的处理/Process each frame
def process_frame(results, max_id_per_class, count_per_class):
    # 获取当前帧的类别ID和跟踪ID/Get the class IDs and tracking IDs of the current frame
    class_ids = results.boxes.cls.cpu().numpy().astype(int)
    track_ids = results.boxes.id.cpu().numpy().astype(int)

    # 更新每个类别的最大ID和计数/Update the maximum ID and count for each class
    for class_id, track_id in zip(class_ids, track_ids):
        # 如果这是这个类别见过的最大ID，更新max_id_per_class/If this is the maximum ID seen for this class, update max_id_per_class
        if track_id > max_id_per_class[class_id]:
            # 更新这个类别的最大ID/Update the maximum ID for this class
            max_id_per_class[class_id] = track_id
            # 对于每个新的track_id，增加该类别的计数/For each new track_id, increment the count for this class
            count_per_class[class_id] += 1

# 在文件顶部集中放一个函数，便于以后复用
def collect_site_stats(class_ids, consecutive_fire_count):
    """返回一个 dict，描述当前帧统计结果"""
    n_person  = int(np.sum(class_ids == 0))
    n_vehicle = int(np.sum(np.isin(class_ids, [3,4,5,6,7,8])))   # 3~8 都算车辆
    n_helmet  = int(np.sum(class_ids == 1))
    helmet_ok = round(100 * n_helmet/max(n_person,1))            # 百分比
    fire_risk = consecutive_fire_count >= 10                     # True / False
    return dict(
        people=n_person, vehicles=n_vehicle,
        helmet_percent=helmet_ok, fire_risk=fire_risk
    )



# ----------------路径设置---------------------------------- / ----------------Path Settings----------------------------------
# source_path = "rtmp://154.201.89.38/live/stream"  #"test_video/test1.MP4"  # 视频路径 / video paths
source_path = "test_video\\helmet.mp4"
weights_path = "best/best1.pt"  # 权重文件路径 / weights file path
weights_path = "weights/yolo11-1280-batch-1-all.pt"  # 权重文件路径 / weights file path
# weights_path = "yolo11n.pt"


save_path = "runs"  # 运行结果保存路径 / path to save run results
tracker = "botsort.yaml"  # 所采用的跟踪算法 / tracking algorithm used
save_directory = "runs/screenshot"  # 异常图片保存路径 / path to save anomaly images
vehicle_directory = "runs/vehicle_screenshot"  # 车辆截图保存路径 / path to save vehicle screenshots

# 新增：定义存放最新帧的目录
OUTPUT_DIR = "video_feed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------参数设置------------------------------------ / ----------------Parameter Settings------------------------------------
# 设置报警帧间隔 / Set alarm frame interval
alarm_clock = 30
# 设置人数变动阈值 / Set threshold for number of people changes
person_increase_or_decrease = 10
# 帧计数 / Frame count
frame_count = 0
# 帧计数 / Frame count
frame_count_latest_frame = 0
# 人数变动计数 / Count of changes in the number of people
person_change_count = 0
# 初始人数 / Initial number of people
num_person = 0

# 获取无人机状态 / Get UAV status
UAV_status = get_UAV_status()

# ----------------初始化------------------------------------ / ----------------Initialization------------------------------------
# 每个类别当前的最大ID / Current maximum ID for each class
max_id_per_class = {i: -1 for i in range(11)}  # 假设类别ID范围为0到8 / Assuming class ID range is 0 to 11
# 每个类别的计数 / Count for each class
count_per_class = {i: 0 for i in range(11)}
# 用于计时：每隔五秒输出一次各个类的累计数量 / For timing: output the cumulative count of each class every five seconds
p_start = time.time()

# 在文件的开头或在 for 循环之前定义（全局计数器）
consecutive_fire_count = 0


# ------------------推理模块----------------------------------- / ------------------Inference Module-----------------------------------
start = time.time()
model = YOLO(weights_path)
results = model.track(
    source=source_path,
    stream=True,  # 流模式处理，防止因为因为堆积而内存溢出 / Stream mode processing to prevent memory overflow due to accumulation
    show=True,  # 实时推理演示 / Real-time inference demonstration
    tracker=tracker,  # 默认tracker为botsort / Default tracker is botsort
    save=False,
    save_dir=save_path,
    # vid_stride=2,  # 视频帧数的步长，即隔几帧检测跟踪一次 / Video frame stride, i.e., detect and track every few frames
    # save_txt=True,  # 把结果以txt形式保存 / Save results in txt format
    # save_conf=True,  # 保存置信度得分 / Save confidence scores
    save_crop=False,  # 保存剪裁的图像 / Save cropped images
    conf=0.4,
    iou=0.5,
    device=0,
)

"""
# result.names输出的class为： / # result.names output classes are:
# {0: 'person', 1: 'helmet', 2: 'life jacket', 3: 'truck', 4: 'excavator',
# 5: 'car crane', 6: 'crawler crane', 7: 'rotary drill rig', 8: 'concrete tanker', 9: 'flame', 10: 'smoke'}
# 其中 0:person 和 1:helmet 是重点要处理的 / Among them, 0:person and 1:helmet are the focus for processing
"""

for r in results:
    frame_count_latest_frame += 1
    frame_count += 1

    boxes = r.boxes                      # ultralytics.Box 对象（可能为空）

    im_array = r.plot(conf=False, line_width=1, font_size=1.5)
    # -------- Always build class_ids, even when nothing detected ----------
    if boxes is not None and len(boxes):           # 有检测框
        class_ids = boxes.cls.cpu().numpy().astype(int)
    else:                                          # 没检测框 → 空数组
        class_ids = np.array([], dtype=int)

    # 只有当 tracker 真正给出了 id 时再去累计 & 处理
    if boxes is not None and len(boxes) and boxes.id is not None:
        process_frame(r, max_id_per_class, count_per_class)
        # 其他依赖 boxes.xyxy / boxes.id 的语句也必须放在这里面

        class_ids_string        = generate_detailed_statistics_string(class_ids)
        class_ids_vehicle_string= generate_detailed_vehicle_statistics_string(class_ids)
        objects_location_string = generate_objects_location_string(boxes.xyxy, boxes.cls)

        # 检测火焰：class_id==9 代表火焰
        if 9 in class_ids:
            consecutive_fire_count += 1
            # 当连续10帧都检测到火焰时，触发报警
            if consecutive_fire_count >= 10:
                try:
                    response = requests.get("http://154.201.89.38:8000/trigger?alarm=fire", timeout=5)
                    if response.status_code == 200:
                        print("Fire alarm triggered successfully.")
                    else:
                        print("Failed to trigger fire alarm. Status code:", response.status_code)
                except Exception as e:
                    print("Error triggering fire alarm:", e)
                # 触发报警后重置计数器（或根据需要设置其他逻辑）
                consecutive_fire_count = 0
        else:
            # 如果本帧没有火焰，重置计数器
            consecutive_fire_count = 0

        if time.time() - p_start >= 6:
            # ---------------------先保存numpy数组格式的图像-------------------- / ---------------------First save the image in numpy array format--------------------
            # 形成文件名 / Create filename
            filename = str(int(time.time())) + ".png"  # 使用当前时间的时间戳（无小数点） / Using current timestamp (no decimal)
            _file_path = os.path.join(vehicle_directory, filename)

            # 保存图像 / Save image
            cv2.imwrite(_file_path, im_array)  # OpenCV的方法来保存numpy数组格式的图像 / Save image in numpy array format using OpenCV
            # ---------------------------------------------------------------

            vehicle_alarm(_file_path, count_per_class, UAV_status, class_ids_vehicle_string,
                          objects_location_string)
            p_start = time.time()
            # print("6秒时间到") / print("6 seconds elapsed")

        # ----------------------------------------------------------------

        # 首先保存上一帧的人数 / First save the number of people from the previous frame
        last_frame_persons = num_person
        # 接下来对目前帧的person和helmet个数进行统计 / Next, count the number of persons and helmets in the current frame
        num_person = np.sum(class_ids == 0)
        num_helmet = np.sum(class_ids == 1)
        # 统计变动人数 / Count the change in the number of people
        person_change_count += abs(last_frame_persons - num_person)
        # 报警条件判断 / Alarm condition judgment
        # 时间/检测帧数足够了,若检测到未戴安全帽立即警报 / If time/frame count is sufficient and an unhelmeted person is detected, trigger alarm immediately
        if frame_count >= alarm_clock:
            # ----------------------处理选框------------------------ / ----------------------Process bounding boxes------------------------
            # 得到某一帧的检测结果(转化为PIL图片)/Get detection results for a frame (convert to PIL image)
            out_img = test_corner_boxes(im_array, boxes.xywh, boxes.xyxy, boxes.cls, boxes.id, l=5,
                                        is_transparent=True,
                                        draw_type=True, draw_corner=True)
            # 形成文件名 / Create filename
            filename = str(int(time.time())) + ".png"  # 使用当前时间的时间戳（无小数点） / Using current timestamp (no decimal)
            file_path = os.path.join(save_directory, filename)
            # 保存图像 / Save image
            cv2.imwrite(file_path, out_img)  # OpenCV的方法来保存numpy数组格式的图像 / Save image in numpy array format using OpenCV
            # -----------------------------------------------------
            person_change_count = 0
            print(objects_location_string)
            cap_alarm(UAV_status, file_path, num_person, num_helmet, class_ids_string, objects_location_string)
            print("此帧异常检测图片已保存至", file_path, ",并同步上传至数据库。 / Anomaly detection image for this frame has been saved to", file_path, ", and uploaded to the database.")
            frame_count = 0

        # 没检测到目标也要保存最新帧 / 上报统计 -----------------------
        im_array = r.plot(conf=False, line_width=1, font_size=1.5)

        if frame_count_latest_frame % 30 == 0:
            cv2.imwrite(os.path.join(OUTPUT_DIR, "latest_frame.jpg"), im_array)

        if frame_count_latest_frame % 10 == 0:
            stats = collect_site_stats(class_ids, consecutive_fire_count)
            try:
                requests.post("http://154.201.89.38:6700/api/site_stats",
                              json=stats, timeout=1)
            except requests.exceptions.RequestException as e:
                print("send site_stats failed:", e)

# ---------------------推理结束调vehicle_alarm接口--------------------- / ---------------------Inference finished, call vehicle_alarm interface---------------------
# 先保存numpy数组格式的图像 / First save the image in numpy array format
# 形成文件名 / Create filename
filename = str(int(time.time())) + ".png"  # 使用当前时间的时间戳（无小数点） / Using current timestamp (no decimal)
_file_path = os.path.join(vehicle_directory, filename)

# 保存图像 / Save image
cv2.imwrite(_file_path, im_array)  # OpenCV的方法来保存numpy数组格式的图像 / Save image in numpy array format using OpenCV
# ---------------------------------------------------------------
print(objects_location_string)
vehicle_alarm_last(_file_path, count_per_class, UAV_status, class_ids_string, objects_location_string)
# ----------------------------------------------------------------

end = time.time()
print("Inference time:", end - start)  # print("推理所用时间:", end - start)


# -----------------------------------------------------------------------------------------------------------------------------
# 同一帧检测到多个对象且可被跟踪的情况 / Multiple objects detected and trackable in the same frame
# 其中要处理的是 / The ones to handle are
"""
cls: tensor([0., 1., 0.])
id: tensor([10., 24., 35.])
xywh: tensor([[3090.2725,  785.7628,   77.8074,   82.7527],
        [3101.3730,  752.7925,   17.5583,   17.2458],
        [1131.0474, 1137.9807,   38.7959,   57.9015]])
"""
"""
cls: tensor([0., 1., 0.])
id: tensor([10., 24., 35.])
xywh: tensor([[3090.2725,  785.7628,   77.8074,   82.7527],
        [3101.3730,  752.7925,   17.5583,   17.2458],
        [1131.0474, 1137.9807,   38.7959,   57.9015]])
"""

"""
ultralytics.engine.results.Boxes object with attributes:

cls: tensor([0., 1., 0.])
conf: tensor([0.7931, 0.6240, 0.5696])
data: tensor([[3.0514e+03, 7.4439e+02, 3.1292e+03, 8.2714e+02, 1.0000e+01, 7.9314e-01, 0.0000e+00],
        [3.0926e+03, 7.4417e+02, 3.1102e+03, 7.6142e+02, 2.4000e+01, 6.2397e-01, 1.0000e+00],
        [1.1116e+03, 1.1090e+03, 1.1504e+03, 1.1669e+03, 3.5000e+01, 5.6956e-01, 0.0000e+00]])
id: tensor([10., 24., 35.])
is_track: True
orig_shape: (2160, 3840)
shape: torch.Size([3, 7])
xywh: tensor([[3090.2725,  785.7628,   77.8074,   82.7527],
        [3101.3730,  752.7925,   17.5583,   17.2458],
        [1131.0474, 1137.9807,   38.7959,   57.9015]])
xywhn: tensor([[0.8048, 0.3638, 0.0203, 0.0383],
        [0.8076, 0.3485, 0.0046, 0.0080],
        [0.2945, 0.5268, 0.0101, 0.0268]])
xyxy: tensor([[3051.3687,  744.3865, 3129.1760,  827.1392],
        [3092.5938,  744.1696, 3110.1521,  761.4154],di
        [1111.6494, 1109.0299, 1150.4453, 1166.9314]])
xyxyn: tensor([[0.7946, 0.3446, 0.8149, 0.3829],
        [0.8054, 0.3445, 0.8099, 0.3525],
        [0.2895, 0.5134, 0.2996, 0.5402]])
"""

"""
# 用 supervision 解析预测结果 supervision的from_ultralytics方法对yolo和rt-detr均适用 / # Use supervision to parse prediction results. The from_ultralytics method of supervision is suitable for both YOLO and RT-DETR
# 此外supervision可以划分区域，并检测区域内有没有目标，这个对于"工地重载车辆周围的安全性判断"有重要意义 / Additionally, supervision can partition regions and detect whether there are targets within the regions, which is important for "safety assessment around heavy-duty vehicles on construction sites"
detections = sv.Detections.from_ultralytics(r)
# 只保留人和头盔，也就是class_id=0或1 / Keep only persons and helmets, i.e., class_id=0 or 1
detections = detections[(detections.class_id == 0) | (detections.class_id == 1)]
# 解析追踪ID / Parse tracking IDs
if r.boxes.id is not None: print(boxes)

detections.tracker_id = r.boxes.id.cpu().numpy().astype(int)
# 获取每个目标的：追踪ID、类别名称、置信度 / Get each target's: tracking ID, class name, confidence
# 1) 类别ID，如第一帧中检测出17个值，对应类别分别为[0 0 0 0 0 0 1 1 1 1 0 1 1 0 0 1 1] / 1) Class IDs, e.g., 17 detections in the first frame with classes [0 0 0 0 0 0 1 1 1 1 0 1 1 0 0 1 1]
class_ids = detections.class_id
# 2) 置信度，表示某一帧中检测出来的目标的置信度 / 2) Confidence scores, indicating the confidence of detected targets in a frame
confidences = detections.confidence
# 3) 多目标追踪ID，如第一帧共检测粗了9个人+8个头盔，该数组就有17个元素1~17 / 3) Multi-object tracking IDs, e.g., 9 persons + 8 helmets detected in the first frame, resulting in 17 elements from 1~17
tracker_ids = detections.tracker_id
# labels为目前帧所有被检测出来目标的 编号+类别名+置信度 / labels are the current frame's detected targets' ID + class name + confidence
# labels = ['#{} {} {:.1f}'.format(tracker_ids[i], model.names[class_ids[i]], confidences[i] * 100) for i in
#           range(len(class_ids))]
"""