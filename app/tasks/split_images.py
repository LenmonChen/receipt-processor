#阿里云之中的安装指令：pip3 install ultralytics --break-system-packages
from ultralytics import YOLO
import cv2
import os
import numpy as np
import glob
import shutil
from celery_app import celery_app
import shutil

@celery_app.task
def xywhr2vertices(x_center, y_center, width, height, angle_rad):
    # 创建旋转矩形的旋转矩阵
    rect = ((x_center, y_center), (width, height), np.degrees(angle_rad))
    box = cv2.boxPoints(rect)  # 获取旋转框的4个顶点
    box = np.int32(np.round(box))        # 转成整数坐标
    return box

@celery_app.task
# 写图片
def write_imgs(box, i, img, img_path):
    """
    box: 单个旋转框 tensor, 格式为 x_center, y_center, width, height, angle_rad
    i: 编号，用来命名保存的裁剪图像
    img: 原始图像（cv2.imread 对象）
    save_folder: 保存路径
    """
    pts = np.array(box, dtype=np.float32)
    # src_pts = np.array(pts, dtype=np.float32)
    # 定义目标矩形的宽度和高度
    width = np.int32(np.linalg.norm(pts[0] - pts[3]))  # 可根据具体方向更改
    height = np.int32(np.linalg.norm(pts[0] - pts[1]))

    # # 四点正确顺序为：左上、右上、右下、左下（按 OpenCV 排序要求）
    src_pts = np.array([
        [pts[1][0], pts[1][1]],  # 左上角点
        [pts[2][0], pts[2][1]],  # 右上角点
        [pts[3][0], pts[3][1]],  # 右下角点
        [pts[0][0], pts[0][1]],  # 左下角点
    ])

    # 计算目标矩形顶点
    dst_pts = np.array([
        [0, 0],  # 左上
        [width - 1, 0],  # 右上
        [width - 1, height - 1],  # 右下
        [0, height - 1]  # 左下
    ], dtype=np.float32)

    # ---- 4. 检查输入是否合法 ----
    if src_pts.shape != (4, 2) or dst_pts.shape != (4, 2):
        print(f"警告：第 {i} 个框点数不对，跳过")
        return

    # 获取透视变换矩阵
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)

    # 应用透视变换
    warped = cv2.warpPerspective(img, M, (width, height))

    # 显示和保存
    # cv2.imshow("Cropped Rotated Area", warped)
    # cv2.waitKey(0)
    # cv2.imwrite('cropped_result.jpg', warped)
    # save_folder = r"C:\Users\13916\Desktop\voucher_output"

    save_folder = img_path.replace(".jpg", "")
    # 检查文件夹是否存在, 删除历史上存在的文件夹
    os.makedirs(save_folder, exist_ok=True)
    # 保存图像（防中文路径错误）✅
    save_path = os.path.join(save_folder, f"{i}.jpg")
    cv2.imwrite(save_path, warped)
    # print(f"已保存第 {i} 个裁剪图像至: {save_path}")

@celery_app.task
def split_imgs(img_path: str):
    # 删除已经存在的图片路径, 预防重复解析的场景
    if os.path.exists(img_path.split('.')[0]):
        shutil.rmtree(img_path.split('.')[0])


    # 1. 加载训练好的 OBB 模型（请替换为你自己的 .pt 文件路径）
    # model = YOLO(r'C:\Users\13916\runs\obb\train11\weights\best.pt')  # 例如 'yolov8s-obb.pt', windows本地环境
    model = YOLO(r'/root/models/best.pt')  #阿里云服务器上的模型地址
    # /root/models/best.pt
    # 服务器上的地址: /root/models/best.pt
    # 2. 读取图片
    # img_path = r"D:\py_task\voucher_dataset\voucher_dataset\train\images\8c56f413-E012450240700180_01.jpg"
    img = cv2.imread(img_path)

    # 3. 推理
    results = model(img)

    # 4. 查看结果（rect 是水平框，obb 是旋转框）
    for result in results:
        # 获取旋转框结果
        obb = result.obb  # OBB 对象，包含旋转框信息

        if obb is not None:
            boxes = obb.xywhr  # 旋转框坐标和旋转角度（x_center, y_center, width, height, angle）
            confidences = obb.conf  # 置信度
            class_ids = obb.cls  # 类别 ID

            if len(boxes) == 1| sum(confidences >= 0.8) == 1:  #不考虑置信度低的那部分, 置信度的阈值考虑0.8
                return 'simple'
            else:
                # print("检测到的旋转框信息：")
                # save_folder = img_path.replace(".jpg", "")
                # if os.path.exists(save_folder):
                #     # 删除文件夹（包括所有内容）
                #     shutil.rmtree(save_folder)
                #     print(f"已删除文件夹: {save_folder}")

                for i in range(len(boxes)):
                    if confidences[i] <= 0.8: #针对部分图片的置信度, 不保存下来
                        continue
                    xywhr = boxes[i].cpu().numpy()
                    x_center, y_center, w, h, angle = xywhr
                    # 转换为 4 个顶点坐标
                    vertices = xywhr2vertices(x_center, y_center, w, h, angle)
                    write_imgs(vertices, i, img, img_path)
                    # write_obb_img(boxes[i], i, img)
                return 'multiple'

# if __name__ == '__main__':
#     # img_path = r"C:\Users\13916\Desktop\voucher_output\test\水单7月28-30日.jpg"
#     # split_imgs(img_path)
#     folder_path = r"C:\Users\13916\Desktop\voucher_output\test"
#     jpg_files = glob.glob(os.path.join(folder_path, "*.jpg"))
#     for jpg_file in jpg_files:
#         split_imgs(jpg_file)
