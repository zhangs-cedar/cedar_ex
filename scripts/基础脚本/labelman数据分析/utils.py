import cv2
import numpy as np
import pandas as pd
import os
import json
import random
from collections import defaultdict
from PIL import Image
from io import BytesIO
from cedar.image import array_to_base64, path_to_url
from cedar.image import imread
from cedar.utils import split_filename
import os.path as osp
import altair as alt
from loguru import logger
import yaml
from typing import Dict, Any

class ImageProcessing:
    def __init__(self, img_cv2: np.ndarray, points: np.ndarray):
        """
        Initializes the ImageProcessing class.

        Args:
            img_cv2 (np.ndarray): The input image in cv2 format.
            points (np.ndarray): The list of points defining the contour.

        Returns:
            None: The function does not return anything, but sets instance variables.

        """
        self.img_cv2 = img_cv2
        # 将点集转换为int32类型，因为cv2.boundingRect需要int32类型的数组
        self.contours_rect = np.array(points).reshape(1, -1, 2).astype(np.int32)
        self.long_side = self.get_minAreaRect()
        self.hue_percentage = self.get_hue_percentage()
        self.area = cv2.contourArea(self.contours_rect)
        self.roi = self.get_roi()

    def get_minAreaRect(self) -> float:
        """
        Calculates the length of the longest side of the minimum bounding rectangle of the contour.

        Returns:
            float: The length of the longest side.

        """
        rect = cv2.minAreaRect(self.contours_rect)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        width = np.linalg.norm(box[0] - box[1])
        height = np.linalg.norm(box[1] - box[2])
        long_side = max(width, height)
        return long_side

    def get_hue_percentage(self) -> float:
        """
        Calculates the average grayscale value within the contour.

        Returns:
            float: The average grayscale value.

        """
        img_cv2 = self.img_cv2.copy()
        gray_im = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2GRAY)
        defect_mask = np.zeros_like(gray_im)
        cv2.drawContours(defect_mask, self.contours_rect, -1, (1), -1)  # 填充轮廓区域,值为1
        # cv2.fillPoly(defect_mask, self.contours_rect, (1), -1)
        min_hue_value = np.min(gray_im[defect_mask == 1])
        max_hue_percentage = (255 - min_hue_value) / 255
        return max_hue_percentage

    def get_roi(self, padding_size: int = 20) -> np.ndarray:
        """
        Gets the region of interest (ROI) and returns two horizontally concatenated ROI images.

        Args:
            padding_size (int): The padding size for the ROI.

        Returns:
            np.ndarray: A concatenated image of two ROIs.

        """
        img_cv2 = self.img_cv2.copy()
        draw = img_cv2[:, :, 0].copy()
        cv2.drawContours(draw, self.contours_rect, -1, (255), 3)
        img_cv2[:, :, 0] = draw
        # 设置边框的参数
        top, bottom, left, right = 5, 5, 5, 5  # 边框的像素数
        border_type = cv2.BORDER_CONSTANT  # 边框类型，这里是常数，即填充一个固定的颜色
        # 定义边框的颜色为白色 (255, 255, 255)
        value = [255, 255, 255]
        # 找到点集的边界矩形
        x, y, w, h = cv2.boundingRect(self.contours_rect)
        roi1 = self.img_cv2[y - padding_size : y + h + padding_size, x - padding_size : x + w + padding_size]
        roi1 = cv2.copyMakeBorder(roi1, top, bottom, left, right, border_type, value=value)

        roi2 = img_cv2[y - padding_size : y + h + padding_size, x - padding_size : x + w + padding_size]
        roi2 = cv2.copyMakeBorder(roi2, top, bottom, left, right, border_type, value=value)

        return np.hstack((roi1, roi2))


def get_num(max: int = 24) -> str:
    """
    Returns a two-digit string from a random number between 1 and max (inclusive).

    Args:
        max (int, optional): The maximum value for the list of numbers to generate (inclusive), default is 24.

    Returns:
        str: A randomly selected two-digit string.

    """
    # 每个数字都是两位数的形式
    formatted_numbers = [f"{i:02}" for i in range(1, max)]
    # 打乱列表顺序
    random.shuffle(formatted_numbers)

    return formatted_numbers[0]


class DataProcessor:
    def __init__(self, input_dir: str):
        """
        Initializes the DataProcessor class.

        Args:
            input_dir (str): The path to the input directory, used as the root for subsequent data processing or file reading.

        Returns:
            None: The function does not return anything, but sets instance variables.

        """
        self.input_dir = input_dir
        self.df_data = {
            "label": [],
            "name": [],
            "image": [],
            "image_area": [],
            "image_length": [],
            "image_hue_percentage": [],
            "time": [],
            "url": [],
            "path": [],
        }
        # self.process_directory()

    def process_directory(self):
        """
        Processes all JSON files in the folder.

        Returns:
            None: The function does not return anything, but processes files.

        """
        print(f"开始处理目录: {self.input_dir}")
        for root, dirs, files in os.walk(self.input_dir):
            total_files = len(files)
            for idx, file in enumerate(files, 1):
                self.process_file(root, file)
                print(f"已处理进度: {idx}/{total_files}")
                if idx % 10 == 0 or idx == total_files:
                    logger.info(f"已处理进度: {idx}/{total_files}")


    def process_file(self, root: str, file: str):
        file_path = osp.join(root, file)
        names = osp.basename(file_path)
        name, suffix = split_filename(names)
        if name == "info":
            print("Skipping file {}".format(file_path))
            return None
        if suffix == ".json":
            self.process_json(file_path, name)

    def process_json(self, file_path: str, name: str):
        img_path = self.find_image_path(file_path, name)
        if img_path is None:
            raise FileNotFoundError("Image file does not exist")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.validate_version(data)
        img_cv2 = imread(img_path)
        self.add_shapes_to_df_data(data, img_cv2, name, img_path)

    def find_image_path(self, file_path: str, name: str):
        extensions = [".png", ".bmp", ".jpg"]
        for ext in extensions:
            img_path = osp.join(osp.dirname(file_path), f"{name}{ext}")
            if osp.exists(img_path):
                return img_path
        return None

    def validate_version(self, data: dict):
        if data.get("version") != "3.1.0":
            data["lastTime"] = "2023-11-10 10:00:00"

    def add_shapes_to_df_data(self, data: dict, img_cv2: np.ndarray, name: str, img_path: str):
        for shape in data.get("shapes", []):
            self.add_shape_to_df_data(shape, data, img_cv2, name, img_path)

    def add_shape_to_df_data(self, shape: dict, data: dict, img_cv2: np.ndarray, name: str, img_path: str):
        shape_instance = defaultdict(dict, shape)
        if shape_instance["label"] == "ignore":
            return
        self.df_data["label"].append(shape_instance["label"])
        self.df_data["name"].append(name)
        lastTime = self.format_last_time(data["lastTime"])
        self.df_data["time"].append(lastTime)
        imgp = ImageProcessing(img_cv2, shape_instance["points"])
        # roi = get_roi(img_cv2, shape_instance["points"])
        self.df_data["image"].append(array_to_base64(self.process_roi(imgp.roi)))
        self.df_data["image_area"].append(imgp.area)
        self.df_data["image_length"].append(imgp.long_side)
        self.df_data["image_hue_percentage"].append(imgp.hue_percentage)
        self.df_data["path"].append(img_path)
        self.df_data["url"].append(path_to_url(img_path))

    def format_last_time(self, lastTime: str) -> str:
        # 这里需要根据你的具体逻辑来格式化时间
        y, m, d = lastTime.split("-")[:3]
        hour, minute, second = get_num(24), get_num(60), get_num(60)  # 随机生成时间
        return f"{y}-{m}-{d} {hour}:{minute}:{second}"

    def process_roi(self, roi: np.ndarray) -> np.ndarray:
        while roi.shape[0] > 200 or roi.shape[1] > 500:
            roi = cv2.pyrDown(roi)  # 缩小图像
        return roi


class DefectChart:
    def __init__(self, df: pd.DataFrame):
        """
        Initializes the DefectChart class.

        Args:
            df (pandas.DataFrame): A pandas DataFrame object used to store data.

        Returns:
            None: The method does not return anything, but sets the df attribute of the instance.

        """
        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time")
        value_counts = df.label.value_counts().reset_index()
        value_counts.columns = ["label", "counts"]
        self.value_counts = value_counts
        self.df = self.process_df(df)
        self.labels = list(self.df.label.unique())
        self.labels_num = len(self.labels)

    def process_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Performs some preprocessing operations on the given DataFrame, including:
        1. Select specific columns and normalize them.
        2. Calculate the 25th percentile (Q1) and 75th percentile (Q3), and normalize specific columns.
        3. Ensure the normalized values are between 0 and 1.
        """

        all_dfs = []
        for _label, _df in df.groupby("label"):
            # 选择特定列
            columns_to_normalize = ["image_area", "image_length", "image_hue_percentage"]

            # 计算25分位数（Q1）和75分位数（Q3）
            Q1 = _df[columns_to_normalize].quantile(0)
            Q3 = _df[columns_to_normalize].quantile(0.85)
            # print(Q1,Q3)
            # 对特定列进行归一化
            df_normalized = _df.copy()
            df_normalized[columns_to_normalize] = (df_normalized[columns_to_normalize] - Q1) / (Q3 - Q1)
            df_normalized[columns_to_normalize] = np.sqrt(df_normalized[columns_to_normalize]) + 0.4

            _Q3 = df_normalized[columns_to_normalize].quantile(0.95) + 2

            # 确保归一化后的值在0到1之间
            df_normalized[columns_to_normalize] = df_normalized[columns_to_normalize].clip(lower=0, upper=_Q3.max())
            all_dfs.append(df_normalized)

        # 使用pd.concat来合并所有归一化后的子DataFrame
        df_combined = pd.concat(all_dfs)
        return df_combined

    def create_scatter_chart(self) -> alt.Chart:
        """
        """
        height = self.labels_num * 45
        dropdown_size = alt.binding_radio(options=["image_area", "image_length", "image_hue_percentage"], name="选择 size : ")
        size_param = alt.param(value="image_area", bind=dropdown_size)

        return (
            alt.Chart(self.df, title="缺陷object基于时间的标签分布散点图")
            .mark_circle(size=140)
            .encode(
                x="time",
                y="label",
                yOffset="jitter:Q",
                tooltip=["image", "time", "name", "image_area", "image_length", "image_hue_percentage"],
                color="label",
                size=alt.Size("size:Q").title(""),  # "image_area",
                href="url:N",
                opacity="image_hue_percentage",
            )
            .transform_calculate(jitter="random()*0.3", size=f"datum[{size_param.name}]")
            .add_params(
                size_param,
            )
            .interactive()
            .properties(width=1100, height=height)
        )

    def create_bar_chart(self, value_counts: pd.DataFrame) -> alt.Chart:
        return alt.Chart(value_counts).mark_bar().encode(alt.X("counts"), alt.Y("label"), tooltip=["counts"]).properties(width=100)





