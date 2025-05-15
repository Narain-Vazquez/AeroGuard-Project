import os
import cv2
import sys
import numpy as np
import torch

from valid import find_people_without_helmets
import random
import math

from PIL import Image, ImageDraw, ImageFont


# ---------------------------角点美化---------------------------
# ---------------------------Corner Beautification---------------------------
def draw_box_corner(draw_img, bbox, length, corner_color):
    """
    角点美化
    Beautify the corners of bounding boxes.

    :param draw_img: 输入图像
    :param draw_img: Input image.
    :param bbox: 目标检测框 形式(x1,y1,x2,y2)
    :param bbox: Bounding box in the format (x1, y1, x2, y2).
    :param length: 角点描绘的直线长度
    :param length: Length of lines drawn for corners.
    :param corner_color: 直线颜色
    :param corner_color: Line color for corners.
    """
    # Top Left
    cv2.line(draw_img, (bbox[0], bbox[1]), (bbox[0] + length, bbox[1]), corner_color, thickness=2)
    cv2.line(draw_img, (bbox[0], bbox[1]), (bbox[0], bbox[1] + length), corner_color, thickness=2)
    # Top Right
    cv2.line(draw_img, (bbox[2], bbox[1]), (bbox[2] - length, bbox[1]), corner_color, thickness=2)
    cv2.line(draw_img, (bbox[2], bbox[1]), (bbox[2], bbox[1] + length), corner_color, thickness=2)
    # Bottom Left
    cv2.line(draw_img, (bbox[0], bbox[3]), (bbox[0] + length, bbox[3]), corner_color, thickness=2)
    cv2.line(draw_img, (bbox[0], bbox[3]), (bbox[0], bbox[3] - length), corner_color, thickness=2)
    # Bottom Right
    cv2.line(draw_img, (bbox[2], bbox[3]), (bbox[2] - length, bbox[3]), corner_color, thickness=2)
    cv2.line(draw_img, (bbox[2], bbox[3]), (bbox[2], bbox[3] - length), corner_color, thickness=2)


# ---------------------------标签美化---------------------------
# ---------------------------Label Beautification---------------------------
def draw_label_type(draw_img, bbox, cls, label_color):
    """
    标签美化
    Beautify the labels of bounding boxes.

    :param draw_img: 输入图像
    :param draw_img: Input image.
    :param bbox: 目标检测框 形式(x1,y1,x2,y2)
    :param bbox: Bounding box in the format (x1, y1, x2, y2).
    :param cls: 标签类别
    :param cls: Class label of the bounding box.
    :param label_color: 标签颜色
    :param label_color: Color of the label background.
    """
    # class对应的类
    # Class names for corresponding IDs
    all_cls = {0: 'person', 1: 'helmet', 2: 'life jacket', 3: 'truck', 4: 'excavator', 5: 'car crane',
               6: 'crawler crane', 7: 'rotary drill rig', 8: 'concrete tanker', 9: 'flame', 10: 'smoke',
               11: 'person without helmet'}
    label = all_cls[cls]  # 获取标签 / Get label name
    labelSize = cv2.getTextSize(label + '0', cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
    if bbox[1] - labelSize[1] - 3 < 0:
        # If the label would go out of the top boundary
        cv2.rectangle(draw_img,
                      (bbox[0], bbox[1] + 2),
                      (bbox[0] + labelSize[0], bbox[1] + labelSize[1] + 3),
                      color=label_color,
                      thickness=-1
                      )
        cv2.putText(draw_img, label,
                    (bbox[0], bbox[1] + labelSize[1] + 3),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    thickness=1
                    )
    else:
        # If the label fits above the box
        cv2.rectangle(draw_img,
                      (bbox[0], bbox[1] - labelSize[1] - 3),
                      (bbox[0] + labelSize[0], bbox[1] - 3),
                      color=label_color,
                      thickness=-1
                      )
        cv2.putText(draw_img, label,
                    (bbox[0], bbox[1] - 3),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    thickness=1
                    )

    return draw_img


# 单个的情况
# For a single bounding box
def test_corner_box(img, bbox, cls, l=20, is_transparent=False, draw_type=False, draw_corner=False,
                    box_color=(255, 0, 255)):
    """
    测试单个框的绘制
    Test drawing for a single bounding box.

    :param img: 输入图像
    :param img: Input image.
    :param bbox: 目标检测框
    :param bbox: Bounding box coordinates.
    :param cls: 类别
    :param cls: Class of the object.
    :param l: 角点长度
    :param l: Length of corners.
    :param is_transparent: 是否透明
    :param is_transparent: Whether the box is transparent.
    :param draw_type: 是否绘制类别标签
    :param draw_type: Whether to draw class labels.
    :param draw_corner: 是否绘制角点
    :param draw_corner: Whether to beautify the corners.
    :param box_color: 框的颜色
    :param box_color: Color of the bounding box.
    :return: 绘制结果的图片
    :return: Image with drawn bounding box.
    """
    draw_img = img.copy()
    pt1 = (bbox[0], bbox[1])  # 左上角坐标 / Top-left corner
    pt2 = (bbox[2], bbox[3])  # 右下角坐标 / Bottom-right corner

    out_img = img
    if is_transparent:
        alpha = 0.8
        cv2.rectangle(draw_img, pt1, pt2, color=box_color, thickness=-1)
        out_img = cv2.addWeighted(img, alpha, draw_img, 1 - alpha, 0)

    cv2.rectangle(out_img, pt1, pt2, color=box_color, thickness=2)

    if draw_type:
        draw_label_type(out_img, bbox, cls, label_color=box_color)
    if draw_corner:
        draw_box_corner(out_img, bbox, length=l, corner_color=(0, 255, 0))
    return out_img


# 多个bbox的情况
# For multiple bounding boxes
def test_corner_boxes(img, xywh, xyxy, cls, ids, l, is_transparent=False, draw_type=False,
                      draw_corner=False, box_color=(255, 0, 255)):
    """
    处理多个目标检测框
    Process multiple bounding boxes.

    :param img: 输入图像
    :param img: Input image.
    :param xywh: 格式为左上角坐标和宽高(归一化后的结果)的盒子集，用于计算IOU 形式(x1,y1,width,height)
    :param xywh: Bounding boxes in normalized (x, y, width, height) format.
    :param xyxy: 目标检测框集左上角坐标和右下角坐标 形式(x1,y1,x2,y2)
    :param xyxy: Bounding boxes in (x1, y1, x2, y2) format.
    :param cls: 各个盒子的对应类
    :param cls: Class of each bounding box.
    :param ids: 各个盒子的id值
    :param ids: IDs of each bounding box.
    :param l: 角点长度
    :param l: Length of the corner lines.
    :param is_transparent: 是否透明
    :param is_transparent: Whether the bounding boxes should be transparent.
    :param draw_type: 是否绘制类别标签
    :param draw_type: Whether to draw class labels.
    :param draw_corner: 是否绘制角点
    :param draw_corner: Whether to beautify the corners.
    :param box_color: 框的颜色
    :param box_color: Color of the bounding boxes.
    :return: 绘制结果的图片
    :return: Image with drawn bounding boxes.
    """

    # 获取没带安全帽的人的id列表
    # Get IDs of people without helmets
    people_without_helmets = find_people_without_helmets(cls, ids, xywh)

    # 初始化颜色列表以分配给不同的类别
    # Initialize color list for different classes
    colors = [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for _ in range(9)]

    draw_img = img.copy()
    out_img = img.copy()

    for i, box in enumerate(xyxy):
        class_id = int(cls[i])
        current_id = ids[i]

        # ------------只标注未带安全帽的人时------------
        # Only annotate people without helmets
        if current_id not in people_without_helmets:
            continue
        # ----------------------------------------

        #  ----------坐标处理-----------
        # Coordinate processing
        x_left_top = math.floor(box[0])
        y_left_top = math.floor(box[1])
        x_right_bottom = math.ceil(box[2])
        y_right_bottom = math.ceil(box[3])
        #  --------------------------

        pt1 = (x_left_top, y_left_top)  # 左上角坐标 / Top-left corner
        pt2 = (x_right_bottom, y_right_bottom)  # 右下角坐标 / Bottom-right corner

        # 如果当前框是人，且此人未佩戴安全帽，使用特殊颜色
        # Use a special color for people without helmets
        if class_id == 0 and current_id in people_without_helmets:
            current_box_color = box_color
            if is_transparent:
                class_id = 11
                alpha = 0.8
                cv2.rectangle(draw_img, pt1, pt2, color=current_box_color, thickness=-1)
                out_img = cv2.addWeighted(out_img, alpha, draw_img, 1 - alpha, 0)
                draw_img = out_img.copy()
        else:
            # 为其他类别分配颜色 / Assign colors for other classes
            current_box_color = colors[class_id]

        # 画出框 / Draw the bounding box
        cv2.rectangle(out_img, pt1, pt2, color=current_box_color, thickness=1)

        bbox_new = [x_left_top, y_left_top, x_right_bottom, y_right_bottom]

        # 判断是否需要添加标签美化和角点美化
        # Determine whether to add label or corner beautification
        if draw_type:
            draw_label_type(out_img, bbox_new, cls=class_id, label_color=current_box_color)
        if draw_corner:
            draw_box_corner(out_img, bbox_new, length=l, corner_color=(0, 255, 0))

        draw_img = out_img.copy()

    return out_img


# cv2写中文
# Add Chinese text to the image using OpenCV
def cv2ImgAddText(img, text, left, top, textColor=(0, 0, 255), textSize=20):
    if isinstance(img, np.ndarray):  # 判断是否OpenCV图片类型 / Check if the image is in OpenCV format
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    # 创建一个可以在给定图像上绘图的对象 / Create a drawable object
    draw = ImageDraw.Draw(img)
    # 字体的格式 / Set the font style
    fontStyle = ImageFont.truetype(
        "simsun.ttc", textSize, encoding="utf-8")
    # 绘制文本 / Draw text
    draw.text((left, top), text, textColor, font=fontStyle)
    # 转换回OpenCV格式 / Convert back to OpenCV format
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def test1():
    img_name = './pikachu.jpg'
    img = cv2.imread(img_name)
    box = [140, 16, 468, 390]
    box_color = (255, 0, 255)  # pink
    out_img = test_corner_box(img, box, cls=0, l=30, is_transparent=False, draw_type=False, draw_corner=False,
                              box_color=box_color)
    cv2.imshow("1", out_img)
    cv2.waitKey(0)


def test2():
    img_name = './pikachu.jpg'
    img = cv2.imread(img_name)
    box = [140, 16, 468, 390]
    box_color = (255, 0, 255)  # pink
    out_img = test_corner_box(img, box, cls=0, l=30, is_transparent=False, draw_type=True, draw_corner=False,
                              box_color=box_color)
    cv2.imshow("2", out_img)
    cv2.waitKey(0)


def test3():
    img_name = './pikachu.jpg'
    img = cv2.imread(img_name)
    box = [140, 16, 468, 390]
    box_color = (255, 0, 255)  # pink
    out_img = test_corner_box(img, box, cls=0, l=30, is_transparent=False, draw_type=True, draw_corner=True,
                              box_color=box_color)
    cv2.imshow("3", out_img)
    cv2.waitKey(0)


def test4():
    img_name = './pikachu.jpg'
    img = cv2.imread(img_name)
    box = [140, 16, 468, 390]
    box_color = (255, 0, 255)  # pink
    out_img = test_corner_box(img, box, cls=0, l=30, is_transparent=True, draw_type=True, draw_corner=True,
                              box_color=box_color)
    cv2.imshow("4", out_img)
    cv2.waitKey(0)


def test5():
    img1 = cv2.imread("./sample/src.jpg")
    img2 = cv2.imread("./sample/fill.jpg")
    alpha = 0.6
    out_img = cv2.addWeighted(img1, alpha, img2, 1 - alpha, 0)
    small_image = cv2.resize(out_img, (960, 600))
    cv2.imshow("5", small_image)
    cv2.waitKey(0)


def test6():
    img_name = 'result.jpg'
    img = cv2.imread(img_name)
    xywh = [[3090.2725, 785.7628, 77.8074, 82.7527],
            [3101.3730, 752.7925, 17.5583, 17.2458],
            [1131.0474, 1137.9807, 38.7959, 57.9015]]
    cls = [0., 1., 0.]
    ids = [10., 24., 35.]
    box_color = (255, 0, 255)  # pink
    out_img = test_corner_boxes(img, xywh, cls, ids, l=20, is_transparent=True, draw_type=True, draw_corner=True,
                                box_color=box_color)
    cv2.imshow("6", out_img)
    cv2.waitKey(0)


def test7():
    img_name = './pikachu.jpg'
    img = cv2.imread(img_name)
    xywh = [[140, 16, 328, 374]]
    cls = [0., ]
    ids = [10., ]
    box_color = (255, 0, 255)  # pink
    out_img = test_corner_boxes(img, xywh, cls, ids, l=20, is_transparent=True, draw_type=True, draw_corner=True,
                                box_color=box_color)
    cv2.imshow("6", out_img)
    cv2.waitKey(0)


def test8():
    img_name = './000011.jpg'
    img = cv2.imread(img_name)
    xywh = [[767, 430, 27, 41]]
    cls = [0., ]
    ids = [10., ]
    box_color = (255, 0, 255)  # pink
    out_img = test_corner_boxes(img, xywh, cls, ids, l=20, is_transparent=True, draw_type=True, draw_corner=True,
                                box_color=box_color)
    cv2.imshow("6", out_img)
    cv2.waitKey(0)


if __name__ == "__main__":
    # test1()
    # test2()
    # test3()
    # test4()
    # test5()
    # test6()
    # test7()
    test8()
