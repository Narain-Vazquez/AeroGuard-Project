import numpy as np

def generate_detailed_statistics_string(class_ids):
    # Define class names corresponding to each ID
    # 定义类别对应的中文名
    class_names = {
        0: 'Person',       # 人
        1: 'Helmet',       # 头盔
        2: 'Life Jacket',  # 救生衣
        3: 'Heavy Truck',  # 重型卡车
        4: 'Excavator',    # 挖掘机
        5: 'Truck Crane',  # 汽车吊机
        6: 'Crawler Crane',# 履带吊机
        7: 'Rotary Drill', # 旋挖钻机
        8: 'Cement Truck', # 水泥车
        9: 'Flame',        # 火焰
        10: 'Smoke'        # 烟雾
    }

    # Count the number of occurrences for each class
    # 统计每个类别的数量
    counts = {class_name: np.sum(class_ids == class_id) for class_id, class_name in class_names.items()}

    # Remove classes with a count of 0
    # 移除数量为0的类别
    counts = {class_name: count for class_name, count in counts.items() if count > 0}

    # Create a statistics string in the format "\"Class: Count\""
    # 创建统计字符串，格式为 "\"类别:数量\""
    statistics_lines = ['"' + f'{class_name}:{count}' + '"' for class_name, count in counts.items()]

    # Concatenate all statistics into a single line, separated by commas and newlines
    # 将所有统计字符串连接成一行，以逗号和换行符分隔
    statistics_string = "Statistics for the current frame:\n" + ",\n".join(statistics_lines)
    # print(statistics_string)

    return statistics_string

def generate_detailed_vehicle_statistics_string(class_ids):
    # Define class names corresponding to each ID
    # 定义类别对应的中文名
    class_names = {
        0: 'Person',       # 人
        1: 'Helmet',       # 头盔
        2: 'Life Jacket',  # 救生衣
        3: 'Heavy Truck',  # 重型卡车
        4: 'Excavator',    # 挖掘机
        5: 'Truck Crane',  # 汽车吊机
        6: 'Crawler Crane',# 履带吊机
        7: 'Rotary Drill', # 旋挖钻机
        8: 'Cement Truck', # 水泥车
        9: 'Flame',        # 火焰
        10: 'Smoke'        # 烟雾
    }

    # Count the number of occurrences for each class
    # 统计每个类别的数量
    counts = {class_name: np.sum(class_ids == class_id) for class_id, class_name in class_names.items()}

    # Remove classes with a count of 0 and exclude 'Helmet' and 'Life Jacket'
    # 移除数量为0的类别，并排除 '头盔' 和 '救生衣'
    counts = {class_name: count for class_name, count in counts.items() if count > 0 and class_name not in ['Helmet', 'Life Jacket']}

    # Create a statistics string in the format "\"Class: Count\""
    # 创建统计字符串，格式为 "\"类别:数量\""
    statistics_lines = ['"' + f'{class_name}:{count}' + '"' for class_name, count in counts.items()]

    # Concatenate all statistics into a single line, separated by commas and newlines
    # 将所有统计字符串连接成一行，以逗号和换行符分隔
    statistics_string = "Current recognition results:\n" + ",\n".join(statistics_lines)
    # print(statistics_string)

    return statistics_string

# Example usage
# 示例
# class_ids_example = np.array([0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 5, 5])
# print(generate_detailed_vehicle_statistics_string(class_ids_example))
