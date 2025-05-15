import torch


def generate_objects_location_string(xyxy, cls):
    """
    根据检测到的对象的边界框坐标和类别（张量格式），生成描述这些对象位置的字符串。

    Generate a string describing the locations of detected objects based on their bounding box coordinates and classes (in tensor format).

    参数:
    xyxy : torch.Tensor
        边界框坐标的二维张量，每行代表一个边界框的左上角和右下角坐标 (x1, y1, x2, y2)。
        A 2D tensor of bounding box coordinates, where each row represents the top-left and bottom-right coordinates of a bounding box (x1, y1, x2, y2).
    cls : torch.Tensor
        每个边界框对应的类别ID的一维张量，类别ID范围从0到10。
        A 1D tensor of class IDs corresponding to each bounding box, with class IDs ranging from 0 to 10.

    返回:
    str
        描述检测到的对象位置的字符串。每个类别的对象位置用英文名称表示，并按照 "(x_center, y_bottom)" 的格式输出。
        If multiple objects of the same category are detected, their locations are separated by commas. Categories with no detected objects are not included in the string.

    示例:
        cls_example = torch.tensor([0., 1., 0.])
        xyxy_example = torch.tensor([[3051.3687, 744.3865, 3129.1760, 827.1392],
                                     [3092.5938, 744.1696, 3110.1521, 761.4154],
                                     [1111.6494, 1109.0299, 1150.4453, 1166.9314]])
        print(generate_objects_location_string(xyxy_example, cls_example))
        Person: (3089.8,827.1), (1131.0,1166.9) Helmet: (3101.4,761.4)
    """
    # Define class names in English
    # 定义类别对应的英文名
    class_names = {
        0: 'Person',  # 人
        1: 'Helmet',  # 头盔
        2: 'Life Jacket',  # 救生衣
        3: 'Heavy Truck',  # 重型卡车
        4: 'Excavator',  # 挖掘机
        5: 'Truck Crane',  # 汽车吊机
        6: 'Crawler Crane',  # 履带吊机
        7: 'Rotary Drilling Rig',  # 旋挖钻机
        8: 'Cement Truck',  # 水泥车
        9: 'Flame',  # 火焰
        10: 'Smoke'  # 烟雾
    }

    # Initialize a dictionary to store coordinates for each category
    # 初始化存储每个类别坐标的字典
    coordinates = {class_name: [] for class_name in class_names.values()}

    # Calculate the center x and bottom y coordinates for each bounding box and add them to the corresponding category list
    # 计算每个盒子的中心点坐标，并将其添加到相应类别的列表中
    for box, class_id in zip(xyxy, cls):
        x_center = (box[0] + box[2]) / 2
        y_bottom = box[3]
        class_name = class_names[int(class_id)]
        coordinates[class_name].append(f"({x_center:.1f},{y_bottom:.1f})")

    # Create the final string in the format "Category: coord1, coord2 ..."
    # 创建最终的字符串，格式为 "类别：坐标1，坐标2 ..."
    result = []
    for class_name, coords in coordinates.items():
        if coords:
            result.append(f"{class_name}: {', '.join(coords)}")

    return ' '.join(result)

# Example
# 示例
# cls_example = torch.tensor([0., 1., 0.])
# xyxy_example = torch.tensor([[3051.3687, 744.3865, 3129.1760, 827.1392],
#                              [3092.5938, 744.1696, 3110.1521, 761.4154],
#                              [1111.6494, 1109.0299, 1150.4453, 1166.9314]])
# print(generate_objects_location_string(xyxy_example, cls_example))
