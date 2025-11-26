import sys
import os
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, QLabel, 
                           QVBoxLayout, QHBoxLayout, QStackedWidget, QGridLayout, 
                           QFrame, QSizePolicy)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRect, QSize, QCoreApplication

class FlowMapUI(QMainWindow):
    """主UI視窗類"""
    # 添加信號
    start_tracking_signal = pyqtSignal()  # 開始追蹤信號
    pool_shape_signal = pyqtSignal(str) # 水池形狀信號
    
    def __init__(self):
        super().__init__()
        
        # 新增：儲存當前選擇的水池形狀
        self.current_pool_shape = "circle"  # 預設為圓形
        
        # 設置窗口標題和大小
        self.setWindowTitle("ArUco FlowMap 系統")
        self.setGeometry(100, 100, 1280, 800)
        
        # 創建堆疊式頁面管理器
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # 創建4個主要頁面
        self.home_page = HomePage(self)
        self.pool_shape_page = PoolShapePage(self)
        self.perspective_page = PerspectiveCalibrationPage(self)
        self.water_jet_page = WaterJetCalibrationPage(self)

        # 連接水池形狀選擇頁面的信號
        self.pool_shape_page.pool_shape_signal.connect(self.on_pool_shape_selected)
        
        # 將頁面添加到堆疊式頁面管理器
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.pool_shape_page)
        self.stacked_widget.addWidget(self.perspective_page)
        self.stacked_widget.addWidget(self.water_jet_page)
        
        # 初始顯示首頁
        self.stacked_widget.setCurrentIndex(0)
    
    def show_home_page(self):
        """顯示首頁"""
        self.stacked_widget.setCurrentIndex(0)

    def show_pool_shape_page(self):
        """顯示水池形狀選擇頁面"""
        self.stacked_widget.setCurrentIndex(1)
    
    def show_perspective_page(self):
        """顯示透視變換校準頁面"""
        self.stacked_widget.setCurrentIndex(2)
    
    def show_water_jet_page(self):
        """顯示射水向量校準頁面"""
        self.stacked_widget.setCurrentIndex(3)
    
    def on_pool_shape_selected(self, shape):
        """處理水池形狀選擇"""
        self.current_pool_shape = shape
        print(f"水池形狀已設置為: {shape}")

        # 重置UI顯示
        self.perspective_page.reset_ui_display()
        self.water_jet_page.reset_ui_display()
    
        # 傳遞信號
        self.pool_shape_signal.emit(shape)
        # 更新透視變換頁面的標題內容
        self.perspective_page.update_for_pool_shape(shape)
    
    def update_original_frame(self, frame):
        """更新原始幀到透視變換校準頁面"""
        if frame is not None:
            self.perspective_page.update_frame_from_camera(frame)
    
    def update_transformed_frame(self, frame):
        """更新透視變換後的幀到射水向量校準頁面"""
        if frame is not None:
            self.water_jet_page.update_frame_from_camera(frame)
    
    def update_tracking_display(self, frame):
        """更新追蹤畫面到射水向量校準頁面"""
        if self.stacked_widget.currentIndex() == 3:  # 當前是射水向量校準頁面
            self.water_jet_page.update_tracking_display(frame)

    def update_flowmap_display(self, flowmap):
        """更新FlowMap到射水向量校準頁面"""
        if self.stacked_widget.currentIndex() == 3:  # 當前是射水向量校準頁面
            self.water_jet_page.update_flowmap_display(flowmap)

class HomePage(QWidget):
    """首頁Class"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 創建主佈局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  # 移除邊距，使內容填滿整個頁面
        main_layout.setSpacing(0)  # 移除間距
        
        # 創建背景圖片框架
        bg_frame = QFrame(self)
        bg_frame.setStyleSheet("background-color: #2D2D30;")  # 設置背景顏色
        bg_frame.setGeometry(0, 0, self.width(), self.height())
        
        # 使用QLabel顯示背景圖片
        bg_label = QLabel(bg_frame)
        bg_label.setGeometry(0, 0, self.width(), self.height())
        bg_label.setScaledContents(True)  # 圖片縮放以填滿整個標籤
        
        # 背景圖片，使用以下程式加載
        bg_pixmap = QPixmap(r"C:\Users\Li-En_Lai\Desktop\ArUcoMarker_Test\UI_Img\HomePage.png")
        bg_label.setPixmap(bg_pixmap)
        
        # 創建按鈕區域 (使用透明背景)
        button_frame = QFrame()
        button_frame.setStyleSheet("background-color: transparent;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(20)
        
        # 開始編輯按鈕
        start_edit_btn = QPushButton("")
        start_edit_btn.setMinimumHeight(60)
        start_edit_btn.setMinimumWidth(200)
        start_edit_bg_pth = r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/EditButton.png"
        
        # 設置圖標
        start_edit_btn.setIcon(QIcon(start_edit_bg_pth))
        start_edit_btn.setIconSize(QSize(200, 60))  # 設置圖標大小，稍小於按鈕尺寸
        start_edit_btn.clicked.connect(self.parent.show_pool_shape_page)  # 直接進入水池形狀選擇頁面
        
        # 退出按鈕
        exit_btn = QPushButton("")
        exit_btn.setMinimumHeight(60)
        exit_btn.setMinimumWidth(200)
        exit_btn_bg_pth = r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/ExitButton.png"
        # 設置圖標
        exit_btn.setIcon(QIcon(exit_btn_bg_pth))
        exit_btn.setIconSize(QSize(200, 60))  # 設置圖標大小，稍小於按鈕尺寸

        exit_btn.clicked.connect(self.exit_application)
        
        # 添加按鈕到佈局
        button_layout.addWidget(start_edit_btn)
        button_layout.addWidget(exit_btn)
        button_layout.addStretch(1)  # 添加彈性空間
        
        # 創建一個容器來放置按鈕，並將其置於底部中央
        button_container = QWidget()
        container_layout = QHBoxLayout(button_container)
        container_layout.addStretch(1)  # 左側彈性空間
        container_layout.addWidget(button_frame)  # 按鈕框架
        container_layout.addStretch(1)  # 右側彈性空間
        
        # 添加所有元素到主佈局
        main_layout.addStretch(2)  # 添加彈性空間
        main_layout.addWidget(button_container, 0, Qt.AlignBottom)  # 底部
        main_layout.addStretch(1)  # 添加彈性空間
        
        # 設置主佈局
        self.setLayout(main_layout)
        
        # 確保背景框架隨窗口大小變化
        self.resizeEvent = self.on_resize
    
    def on_resize(self, event):
        """處理窗口大小變化事件"""
        # 更新背景框架大小
        for child in self.children():
            if isinstance(child, QFrame):
                child.setGeometry(0, 0, self.width(), self.height())
                # 更新背景圖片標籤大小
                for label in child.children():
                    if isinstance(label, QLabel):
                        label.setGeometry(0, 0, self.width(), self.height())
        
        # 調用原始的 resizeEvent
        super().resizeEvent(event)
    
    def exit_application(self):
        """退出應用程序"""
        QApplication.quit()

class PoolShapePage(QWidget):
    '''水池形狀選擇頁面Class'''

    # 添加信號
    pool_shape_signal = pyqtSignal(str) # 水池形狀選擇信號

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        '''初始化UI'''
        # 設置整個頁面的背景色為淺藍色
        self.setAutoFillBackground(True)  # 確保背景自動填充
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#EEFFFE"))  # 設置淺藍背景
        self.setPalette(palette)

        # 設置樣式表(Style Sheet)，確保子元件皆為透明的
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QLabel {
                background-color: transparent;
            }
        """)

        # 創建主佈局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 創建頂部區域(標題文字內容、返回首頁按鈕)
        top_layout = QHBoxLayout() # 水平佈局
        top_layout.setContentsMargins(20,20,20,10)
        top_layout.setSpacing(10)

        # 標題
        title_label = QLabel("Select Pool Shape")
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft) # 文字內容水平靠左對齊，垂直置中對齊)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000; background-color: transparent")

        # 返回首頁按鈕
        home_btn = QPushButton("")
        home_btn.setFixedSize(50,50)
        home_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/To Home Page Button.png"))
        home_btn.setIconSize(QSize(40,40))
        home_btn.clicked.connect(self.parent.show_home_page)

        # 添加到頂部佈局
        top_layout.addWidget(title_label,1)
        top_layout.addWidget(home_btn)

        # 創建水池形狀選擇按鈕區域
        shape_container = QWidget()
        shape_container.setStyleSheet("background-color: transparent;")
        shape_layout = QHBoxLayout(shape_container)
        shape_layout.setSpacing(30)

        # 圓形水池按鈕
        circle_btn = QPushButton("")
        circle_btn.setMinimumHeight(80)
        circle_btn.setMinimumWidth(200)
        circle_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/CirclePoolButton.png"))
        circle_btn.setIconSize(QSize(200, 80))
        circle_btn.clicked.connect(lambda: self.select_pool_shape("circle"))
        
        # 矩形水池按鈕
        rectangle_btn = QPushButton("")
        rectangle_btn.setMinimumHeight(80)
        rectangle_btn.setMinimumWidth(200)
        rectangle_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/RectanglePoolButton.png"))
        rectangle_btn.setIconSize(QSize(200, 80))
        rectangle_btn.clicked.connect(lambda: self.select_pool_shape("rectangle"))
        
        # 橢圓形水池按鈕
        # oval_btn = QPushButton("")
        # oval_btn.setMinimumHeight(80)
        # oval_btn.setMinimumWidth(200)
        # oval_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/OvalPoolButton.png"))
        # oval_btn.setIconSize(QSize(200, 80))
        # oval_btn.setStyleSheet("background-color: transparent; border: none;")
        # oval_btn.clicked.connect(lambda: self.select_pool_shape("oval"))
        
        # 添加按鈕到形狀選擇佈局
        shape_layout.addWidget(circle_btn)
        shape_layout.addWidget(rectangle_btn)
        # shape_layout.addWidget(oval_btn)
        
        # 創建一個容器來放置按鈕，並將其置於中央
        button_container = QWidget()
        container_layout = QHBoxLayout(button_container)
        container_layout.addStretch(1)  # 左側彈性空間
        container_layout.addWidget(shape_container)  # 按鈕框架
        container_layout.addStretch(1)  # 右側彈性空間
        
        # 創建底部導航按鈕區域
        bottom_nav_layout = QHBoxLayout()
        bottom_nav_layout.setContentsMargins(20, 0, 20, 20)
        bottom_nav_layout.setSpacing(10)

        # 上一步按鈕
        prev_btn = QPushButton("")
        prev_btn.setFixedSize(180, 50)
        prev_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/PreviousStep.png"))
        prev_btn.setIconSize(QSize(180, 50))
        prev_btn.setStyleSheet("background-color: transparent; border: none;")
        prev_btn.clicked.connect(self.parent.show_home_page)
        
        # 添加按鈕到底部佈局
        bottom_nav_layout.addWidget(prev_btn)
        bottom_nav_layout.addStretch(1)  # 中間彈性空間
        
        # 添加所有元素到主佈局
        main_layout.addLayout(top_layout)
        main_layout.addStretch(1)  # 上方彈性空間
        main_layout.addWidget(button_container)  # 形狀選擇按鈕
        main_layout.addStretch(1)  # 下方彈性空間
        main_layout.addLayout(bottom_nav_layout)
        
        # 設置主佈局
        self.setLayout(main_layout)
    
    def select_pool_shape(self, shape):
        """選擇水池形狀"""
        print(f"選擇水池形狀: {shape}")

        # 重置UI顯示
        if hasattr(self.parent, 'perspective_page'):
            self.parent.perspective_page.reset_ui_display()
        if hasattr(self.parent, 'water_jet_page'):
            self.parent.water_jet_page.reset_ui_display()

        self.pool_shape_signal.emit(shape) # 發送水池形狀訊號
        self.parent.show_perspective_page()

class PerspectiveCalibrationPage(QWidget):
    """透視變換編輯頁面Class"""
    
    # 添加信號
    annotation_points_signal = pyqtSignal(list)  # 標註點信號
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.annotation_points = []  # 存儲標註點
        self.max_points = 4  # 最大標註點數量
        self.current_frame = None  # 當前幀
        self.display_frame = None  # 顯示用的幀
        self.is_frame_captured = False  # 是否已擷取幀
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 設置整個頁面的背景色為淺藍色
        self.setAutoFillBackground(True)  # 確保背景自動填充
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#EEFFFE"))  # 設置淺藍背景
        self.setPalette(palette)
        
        # 設置樣式表，確保所有子元件都是透明的
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QLabel {
                background-color: transparent;
            }
            QWidget#sendBtnContainer {
                background-color: transparent;
            }
        """)
        
        # 創建主佈局
        main_layout = QVBoxLayout()
        # 設置邊距為0，確保佈局填滿整個窗口
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 創建頂部區域 (包含標題和首頁按鈕)
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(20, 20, 20, 10)
        top_layout.setSpacing(10)

        # 標題
        self.title_label = QLabel(f"Click on the image to set the reference point(Select {self.max_points} points)")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000; background-color: transparent;")
        
        # 首頁按鈕
        home_btn = QPushButton("")
        home_btn.setFixedSize(50, 50)
        home_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/To Home Page Button.png"))
        home_btn.setIconSize(QSize(40, 40))
        home_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(200, 200, 200, 100);
                border-radius: 25px;
            }
        """)
        home_btn.clicked.connect(self.parent.show_home_page)
        
        # 添加到頂部佈局
        top_layout.addWidget(self.title_label, 1)
        top_layout.addWidget(home_btn)
        
        # 創建中間內容區域 (包含圖像和按鈕)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 10, 20, 20)
        content_layout.setSpacing(15)
        
        # 創建圖像顯示區域
        self.image_frame = QLabel()
        self.image_frame.setAlignment(Qt.AlignCenter)
        self.image_frame.setStyleSheet("background-color: transparent;")
        self.image_frame.setMinimumSize(640, 480)
        self.image_frame.mousePressEvent = self.on_image_click
        
        mid_btn_container = QWidget()
        mid_btn_layout = QHBoxLayout(mid_btn_container)
        mid_btn_layout.setContentsMargins(0, 0, 0, 0)
        mid_btn_layout.setSpacing(20)  # 設置按鈕之間的間距

        # 擷取當前幀按鈕
        capture_btn = QPushButton("")
        capture_btn.setFixedSize(180, 40)
        capture_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/CaptureImage.png"))
        capture_btn.setIconSize(QSize(180, 40))
        capture_btn.setStyleSheet("background-color: transparent; border: none;")
        capture_btn.clicked.connect(self.capture_current_frame)
        
        # 重置按鈕
        reset_btn = QPushButton("")
        reset_btn.setFixedSize(180, 40)
        reset_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/Reset.png"))
        reset_btn.setIconSize(QSize(180, 40))
        reset_btn.setStyleSheet("background-color: transparent; border: none;")
        reset_btn.clicked.connect(self.reset_annotations)

        # 添加按鈕到中間佈局
        mid_btn_layout.addStretch(1)  # 左側彈性空間
        mid_btn_layout.addWidget(capture_btn)
        mid_btn_layout.addWidget(reset_btn)
        mid_btn_layout.addStretch(1)  # 右側彈性空間
        
        # 發送按鈕
        send_btn_container = QWidget()
        send_btn_container.setObjectName("sendBtnContainer")  # 設置對象名稱以便在樣式表中引用
        send_btn_container.setStyleSheet("background-color: transparent;")
        send_layout = QHBoxLayout(send_btn_container)
        send_layout.setContentsMargins(0, 0, 0, 0)
        
        send_btn = QPushButton("")
        send_btn.setFixedSize(350, 50)
        send_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/ApplyPoints.png"))
        send_btn.setIconSize(QSize(300, 50))
        send_btn.setStyleSheet("background-color: transparent; border: none;")
        send_btn.clicked.connect(self.send_annotations)
        
        send_layout.addStretch(1)
        send_layout.addWidget(send_btn)
        send_layout.addStretch(1)

        # 創建底部導航按鈕區域
        bottom_nav_layout = QHBoxLayout()
        bottom_nav_layout.setContentsMargins(20, 0, 20, 20)
        bottom_nav_layout.setSpacing(10)

        # 上一步按鈕
        prev_btn = QPushButton("")
        prev_btn.setFixedSize(180, 50)
        prev_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/PreviousStep.png"))
        prev_btn.setIconSize(QSize(180, 50))
        prev_btn.setStyleSheet("background-color: transparent; border: none;")
        prev_btn.clicked.connect(self.parent.show_pool_shape_page)

        # 下一步按鈕
        next_btn = QPushButton("")
        next_btn.setFixedSize(180, 50)
        next_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/NextStep.png"))
        next_btn.setIconSize(QSize(180, 50))
        next_btn.setStyleSheet("background-color: transparent; border: none;")
        next_btn.clicked.connect(self.go_to_next_step)
        
        # 添加按鈕到底部佈局
        bottom_nav_layout.addWidget(prev_btn)
        bottom_nav_layout.addStretch(1)  # 中間彈性空間
        bottom_nav_layout.addWidget(next_btn)
        
        # 添加元素到內容佈局
        content_layout.addWidget(self.image_frame, 1)
        content_layout.addWidget(mid_btn_container)
        content_layout.addWidget(send_btn_container)
        content_layout.addLayout(bottom_nav_layout)
        
        # 添加所有元素到主佈局
        main_layout.addLayout(top_layout)
        main_layout.addLayout(content_layout, 1)  # 添加伸展因子，確保內容區域可以填滿剩餘空間

        # 設置主佈局
        self.setLayout(main_layout)
        
        # 創建定時器，用於更新圖像
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 每30毫秒更新一次

    def update_for_pool_shape(self,shape):
        '''根據在水池形狀選擇頁面選擇的結果更新標題內容'''
        self.pool_shape = shape
        self.title_label.setText(f"[Pool Shape:{shape}]Click on the image to set the reference point(Select {self.max_points} points)")
    
    def update_camera_frame(self, frame):
        """從攝像頭更新幀"""
        if frame is not None:
            self.current_frame = frame.copy()
            # 如果尚未擷取幀，則顯示預覽
            if not self.is_frame_captured:
                # 創建一個預覽幀，添加提示文字
                preview_frame = self.current_frame.copy()
                cv2.putText(preview_frame, "預覽 - 請點擊「Capture image」按鈕", 
                          (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                self.display_frame = preview_frame
    
    def capture_current_frame(self):
        """擷取當前幀"""
        print("按下截取當前Frame按鈕")
        if self.current_frame is not None:
            self.display_frame = self.current_frame.copy()
            self.is_frame_captured = True
            self.annotation_points = []  # 重置標註點
            print("已擷取當前幀，可以開始標註參考點")
    
    def update_frame_from_camera(self, frame):
        """從攝像頭更新幀"""
        if frame is not None:
            self.current_frame = frame.copy()
    
    def update_frame(self):
        """更新圖像幀"""
        # 如果沒有幀可顯示，使用空白圖像
        if self.display_frame is None:
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            blank_frame[:] = (245, 245, 240)  # 淺米色
            self.display_frame = blank_frame
        
        # 繪製標註點
        frame_with_annotations = self.display_frame.copy()
        for i, point in enumerate(self.annotation_points):
            cv2.circle(frame_with_annotations, point, 5, (0, 0, 255), -1)
            cv2.putText(frame_with_annotations, f"P{i+1}", 
                      (point[0] + 10, point[1] + 10), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # 提高顯示品質：使用更高質量的圖像轉換
        display_height = self.image_frame.height()
        display_width = self.image_frame.width()
        
        # 計算保持比例的縮放尺寸
        h, w = frame_with_annotations.shape[:2]
        aspect_ratio = w / h
        
        if display_width / display_height > aspect_ratio:
            # 顯示區域更寬，以高度為準
            new_height = display_height
            new_width = int(new_height * aspect_ratio)
        else:
            # 顯示區域更高，以寬度為準
            new_width = display_width
            new_height = int(new_width / aspect_ratio)
        
        # 使用 OpenCV 的高質量插值方法進行縮放
        resized_frame = cv2.resize(frame_with_annotations, (new_width, new_height), 
                                 interpolation=cv2.INTER_LANCZOS4)
        
        # 將OpenCV圖像轉換為Qt圖像
        height, width, channel = resized_frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(resized_frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        
        # 顯示圖像（不需要再次縮放）
        pixmap = QPixmap.fromImage(q_img)
        self.image_frame.setPixmap(pixmap)
    
    def on_image_click(self, event):
        """處理圖像點擊事件"""
         # 如果尚未擷取幀，則不允許標註
        if not self.is_frame_captured:
            print("請先擷取當前幀，再進行標註")
            return
        
        if len(self.annotation_points) >= self.max_points:
            print(f"已達到最大標註點數量: {self.max_points}")
            return
        
        # 獲取點擊位置
        pos = event.pos()
        
        # 將點擊位置轉換為圖像坐標
        pixmap = self.image_frame.pixmap()
        if pixmap:
            # 計算圖像在標籤中的位置
            img_rect = QRect(0, 0, pixmap.width(), pixmap.height())
            img_rect.moveCenter(QPoint(self.image_frame.width() // 2, self.image_frame.height() // 2))
            
            # 檢查點擊是否在圖像內
            if img_rect.contains(pos):
                # 計算相對於圖像左上角的坐標
                x = pos.x() - img_rect.left()
                y = pos.y() - img_rect.top()
                
                # 轉換為原始圖像坐標
                orig_x = int(x * (self.current_frame.shape[1] / pixmap.width()))
                orig_y = int(y * (self.current_frame.shape[0] / pixmap.height()))
                
                # 添加標註點
                self.annotation_points.append((orig_x, orig_y))
                print(f"添加標註點: ({orig_x}, {orig_y}), 當前點數: {len(self.annotation_points)}")
    
    def reset_annotations(self):
        """重置標註點"""
        self.annotation_points = []
        print("已重置所有標註點")
    
    def send_annotations(self):
        """發送標註點"""
        if len(self.annotation_points) != self.max_points:
            print(f"標註點數量不足，需要 {self.max_points} 個點，當前有 {len(self.annotation_points)} 個點")
            return
        
        print(f"發送標註點: {self.annotation_points}")
        # 發送標註點信號
        self.annotation_points_signal.emit(self.annotation_points)
        
        # 發送後重置標註點
        self.reset_annotations()
        self.is_frame_captured = False
        
        # 發送後自動進入下一步
        self.go_to_next_step()
    
    def go_to_next_step(self):
        """進入下一步 (射水向量校準頁面)"""
        self.parent.show_water_jet_page()
    
    def reset_ui_display(self):
        """重置透視變換編輯介面中的UI顯示畫面"""
        self.annotation_points = []
        self.current_frame = None
        self.display_frame = None
        self.is_frame_captured = False
        
        # 重置圖像顯示
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        blank_frame[:] = (245, 245, 240)  # 淺米色
        self.display_frame = blank_frame
        
        # 更新顯示
        self.update_frame()
        print("透視變換頁面UI顯示已重置")

class WaterJetCalibrationPage(QWidget):
    """射水向量校準頁面Class"""
    
    # 添加信號
    water_jet_vectors_signal = pyqtSignal(list)  # 射水向量信號
    request_transformed_frame_signal = pyqtSignal()  # 請求透視變換後的幀信號
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.annotation_points = []  # 存儲標註點
        self.point_per_group = 2  # 每組點數（起點和終點）
        self.total_groups = 6  # 總組數
        self.current_frame = None  # 當前幀
        self.display_frame = None  # 顯示用的幀
        self.is_frame_captured = False  # 是否已擷取幀

        # 用於繪製射水向量的變數
        self.is_drawing = False # 是否正在繪製射水向量
        self.current_strat_point = None # 當前繪製的射水向量起點
        self.current_end_point = None # 當前繪製的射水向量終點
        self.temp_display_frame = None # 臨時顯示Frame，用於繪製拖曳過程中的向量
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""

        # 設定整個頁面的背景色為淺藍色
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(),QColor("#EEFFFE")) # 淺藍背景
        self.setPalette(palette)

        # 設置樣式表(Style Sheet)，確保子元件皆為透明的
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QLabel {
                background-color: transparent;
            }
        """)

        # 創建主佈局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 創建頂部區域(標題文字內容、返回首頁按鈕)
        top_layout = QHBoxLayout() # 水平佈局
        top_layout.setContentsMargins(20,20,20,10)
        top_layout.setSpacing(10)
         
        # 標題
        title_label = QLabel("Water Jet Calibration Page")
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft) # 文字內容水平靠左對齊，垂直置中對齊)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000; background-color: transparent")

        # 返回首頁按鈕
        home_btn = QPushButton("")
        home_btn.setFixedSize(50,50)
        home_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/To Home Page Button.png"))
        home_btn.setIconSize(QSize(40,40))
        home_btn.clicked.connect(self.parent.show_home_page)

        # 添加到頂部佈局
        top_layout.addWidget(title_label,1)
        top_layout.addWidget(home_btn)

        # 創建中央內容區域(包含圖像以及按鈕)
        central_layout = QHBoxLayout() # 設置垂直佈局
        central_layout.setContentsMargins(20,10,20,20) # 設置佈局邊距
        central_layout.setSpacing(15) # 設置Layout中各元件的間距(預設為10)

        # 創建左側射水向量編輯區域
        left_panel = QVBoxLayout() # 設置為垂直佈局
        left_panel.setSpacing(15)

        # 創建圖像顯示區域(顯示透視變換後的Frame)
        self.image_frame = QLabel()
        self.image_frame.setAlignment(Qt.AlignCenter)
        self.image_frame.setStyleSheet("background-color: transparent;")
        self.image_frame.setMinimumSize(512, 512)
        
        # 滑鼠事件處理(新方法:類似小畫家畫筆功能，用拖曳的方式進行)
        self.image_frame.mousePressEvent = self.on_mouse_press # 滑鼠點擊事件(用於設置射水向量初始點)
        self.image_frame.mouseMoveEvent = self.on_mouse_move # 滑鼠拖曳事件
        self.image_frame.mouseReleaseEvent = self.on_mouse_release # 滑鼠點擊後釋放事件(用於設置射水向量終點)
        

        mid_btn_container = QWidget() # 建立容納中央控制按鈕的容器
        mid_btn_layout = QHBoxLayout(mid_btn_container) # 設置為水平佈局
        mid_btn_layout.setContentsMargins(0,0,0,0) # 設置佈局邊距(按鈕緊密排列)
        mid_btn_layout.setSpacing(20) # 設置按鈕之間的間距
        
        # 截取透視變換後的Frame按鈕
        capture_btn = QPushButton("")
        capture_btn.setFixedSize(180,40)
        capture_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/CaptureImage.png"))
        capture_btn.setIconSize(QSize(180, 40))
        capture_btn.setStyleSheet("background-color: transparent; border: none;")
        capture_btn.clicked.connect(self.request_transformed_frame)
        
        # 重置編輯的射水向量按鈕
        reset_btn = QPushButton("")
        reset_btn.setFixedSize(180, 40)
        reset_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/Reset.png"))
        reset_btn.setIconSize(QSize(180, 40))
        reset_btn.setStyleSheet("background-color: transparent; border: none;")
        reset_btn.clicked.connect(self.reset_annotations)

        # 添加截取按鈕以及重置按鈕到中央控制按鈕容器的佈局
        mid_btn_layout.addStretch(1)  # 左側彈性空間
        mid_btn_layout.addWidget(capture_btn)
        mid_btn_layout.addWidget(reset_btn)
        mid_btn_layout.addStretch(1)  # 右側彈性空間

        # 發送按鈕
        send_btn_container = QWidget()
        send_btn_container.setObjectName("sendBtnContainer")  # 設置對象名稱方便在樣式表(Style Sheet)中引用
        send_btn_container.setStyleSheet("background-color: transparent;")
        send_layout = QHBoxLayout(send_btn_container)
        send_layout.setContentsMargins(0, 0, 0, 0)
        
        # 發送按鈕
        send_btn = QPushButton("")
        send_btn.setFixedSize(350, 50)
        send_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/ApplyWaterJetVector.png"))
        send_btn.setIconSize(QSize(300, 50))
        send_btn.setStyleSheet("background-color: transparent; border: none;")
        send_btn.clicked.connect(self.send_annotations)
        
        send_layout.addStretch(1)
        send_layout.addWidget(send_btn)
        send_layout.addStretch(1)
        
        # 創建底部按鈕區域
        bottom_btn_layout = QHBoxLayout()
        bottom_btn_layout.setContentsMargins(0,0,0,0)
        bottom_btn_layout.setSpacing(10)

        # 上一步按鈕(返回至透視變換參考點編輯頁面)
        prev_btn = QPushButton("")
        prev_btn.setFixedSize(180, 50)
        prev_btn.setIcon(QIcon(r"C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/UI_Img/PreviousStep.png"))
        prev_btn.setIconSize(QSize(180, 50))
        prev_btn.setStyleSheet("background-color: transparent; border: none;")
        # 按鈕功能綁定(切換至上個頁面)
        prev_btn.clicked.connect(self.go_to_previous_step)

        # 添加上一步按鈕到底部按鈕部局
        bottom_btn_layout.addWidget(prev_btn)
        bottom_btn_layout.addStretch(1)

        # 添加元素到左側編輯區域佈局
        left_panel.addWidget(self.image_frame,1)
        left_panel.addWidget(mid_btn_container)
        left_panel.addWidget(send_btn_container)
        left_panel.addLayout(bottom_btn_layout)

        # 右側顯示區域
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

        # 創建用於顯示即時追蹤水面畫面的圖像區域
        self.tracking_display = QLabel()
        self.tracking_display.setAlignment(Qt.AlignCenter)
        self.tracking_display.setStyleSheet("background-color: transparent;")
        self.tracking_display.setMinimumSize(320, 320)
        # self.tracking_display.setText("Tracking will be displayed here")

        # 創建用於顯示FlowMap圖像區域
        self.flowmap_display = QLabel()
        self.flowmap_display.setAlignment(Qt.AlignCenter)
        self.flowmap_display.setStyleSheet("background-color: transparent;")
        self.flowmap_display.setMinimumSize(320, 320)
        # self.flowmap_display.setText("FlowMap will be displayed here")

        # 添加元素到右側編輯區域佈局
        right_panel.addWidget(self.tracking_display, 1)
        right_panel.addWidget(self.flowmap_display, 1)

        # 將左側和右側面板添加到中央內容佈局
        central_layout.addLayout(left_panel, 1)  # 左側編輯區域
        central_layout.addLayout(right_panel, 1)  # 右側顯示區域
        
        # 添加所有元素到主佈局
        main_layout.addLayout(top_layout)
        main_layout.addLayout(central_layout,1)
        
        # 設置主佈局
        self.setLayout(main_layout)
        
        # 創建定時器，用於更新圖像
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 每30毫秒更新一次

        # 初始化追蹤相關變數
        self.tracking_active = False
        self.tracker = None
    
    def update_frame_from_camera(self, frame):
        """從攝像頭更新幀"""
        if frame is not None:
            self.current_frame = frame.copy()
    
    def capture_current_frame(self):
        """擷取當前幀"""
        print("按下截取當前Frame按鈕")
        if self.current_frame is not None:
            self.display_frame = self.current_frame.copy()
            self.is_frame_captured = True
            self.annotation_points = []  # 重置標註點
            print("已擷取當前幀，可以開始標註射水向量")
    
    def update_frame(self):
        """更新圖像幀"""
        # 如果沒有幀可顯示，使用空白圖像
        if self.display_frame is None:
            blank_frame = np.zeros((512, 512, 3), dtype=np.uint8)
            blank_frame[:] = (245, 245, 245)  # 深灰色背景
            self.display_frame = blank_frame
        
        # 使用臨時顯示幀或正常顯示幀
        if self.is_drawing and self.temp_display_frame is not None:
            frame_to_display = self.temp_display_frame
        else:
            # 繪製標註點和向量
            frame_with_annotations = self.display_frame.copy()
        
            # 繪製已標註的向量
            for i in range(0, len(self.annotation_points), self.point_per_group):
                if i + 1 < len(self.annotation_points):
                    start_point = self.annotation_points[i]
                    end_point = self.annotation_points[i + 1]
                    
                    # 繪製向量
                    cv2.arrowedLine(frame_with_annotations, start_point, end_point, (0, 255, 255), 2)
                    
                    # 繪製起點和終點
                    cv2.circle(frame_with_annotations, start_point, 5, (0, 0, 255), -1)
                    cv2.circle(frame_with_annotations, end_point, 5, (255, 0, 0), -1)
                    
                    # 標註組號
                    group_num = i // self.point_per_group + 1
                    cv2.putText(frame_with_annotations, f"G{group_num}", 
                            (start_point[0] + 10, start_point[1] + 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            frame_to_display = frame_with_annotations
        # 將OpenCV圖像轉換為Qt圖像
        height, width, channel = frame_to_display.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame_to_display.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        
        # 顯示圖像
        self.image_frame.setPixmap(QPixmap.fromImage(q_img).scaled(
            self.image_frame.width(), self.image_frame.height(), 
            Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
    def on_mouse_press(self, event):
        """處理滑鼠按下事件"""
        # 如果尚未擷取幀或已達到最大標註點數量，則不允許標註
        max_points = self.total_groups * self.point_per_group
        if not self.is_frame_captured:
            print("請先擷取當前幀，再進行標註")
            return
        
        if len(self.annotation_points) >= max_points:
            print(f"已達到最大標註點數量: {max_points}")
            return
        
        # 獲取點擊位置
        pos = event.pos()
        
        # 將點擊位置轉換為圖像坐標
        pixmap = self.image_frame.pixmap()
        if pixmap:
            # 計算圖像在標籤中的位置
            img_rect = QRect(0, 0, pixmap.width(), pixmap.height())
            img_rect.moveCenter(QPoint(self.image_frame.width() // 2, self.image_frame.height() // 2))
            
            # 檢查點擊是否在圖像內
            if img_rect.contains(pos):
                # 計算相對於圖像左上角的坐標
                x = pos.x() - img_rect.left()
                y = pos.y() - img_rect.top()
                
                # 轉換為原始圖像坐標
                orig_x = int(x * (self.current_frame.shape[1] / pixmap.width()))
                orig_y = int(y * (self.current_frame.shape[0] / pixmap.height()))
                
                # 設置繪製起點
                self.current_start_point = (orig_x, orig_y)
                self.current_end_point = (orig_x, orig_y)  # 初始化終點與起點相同
                self.is_drawing = True
                
                # 創建臨時顯示幀
                self.update_temp_display_frame()
                
                print(f"開始繪製向量，起點: ({orig_x}, {orig_y})")

    def on_mouse_move(self, event):
        """處理滑鼠移動事件"""
        if not self.is_drawing or self.current_start_point is None:
            return
        
        # 獲取當前位置
        pos = event.pos()
        
        # 將當前位置轉換為圖像坐標
        pixmap = self.image_frame.pixmap()
        if pixmap:
            # 計算圖像在標籤中的位置
            img_rect = QRect(0, 0, pixmap.width(), pixmap.height())
            img_rect.moveCenter(QPoint(self.image_frame.width() // 2, self.image_frame.height() // 2))
            
            # 檢查點擊是否在圖像內
            if img_rect.contains(pos):
                # 計算相對於圖像左上角的坐標
                x = pos.x() - img_rect.left()
                y = pos.y() - img_rect.top()
                
                # 轉換為原始圖像坐標
                orig_x = int(x * (self.current_frame.shape[1] / pixmap.width()))
                orig_y = int(y * (self.current_frame.shape[0] / pixmap.height()))
                
                # 更新終點
                self.current_end_point = (orig_x, orig_y)
                
                # 更新臨時顯示幀
                self.update_temp_display_frame()

    def on_mouse_release(self, event):
        """處理滑鼠釋放事件"""
        if not self.is_drawing or self.current_start_point is None:
            return
        
        # 獲取釋放位置
        pos = event.pos()
        
        # 將釋放位置轉換為圖像坐標
        pixmap = self.image_frame.pixmap()
        if pixmap:
            # 計算圖像在標籤中的位置
            img_rect = QRect(0, 0, pixmap.width(), pixmap.height())
            img_rect.moveCenter(QPoint(self.image_frame.width() // 2, self.image_frame.height() // 2))
            
            # 檢查點擊是否在圖像內
            if img_rect.contains(pos):
                # 計算相對於圖像左上角的坐標
                x = pos.x() - img_rect.left()
                y = pos.y() - img_rect.top()
                
                # 轉換為原始圖像坐標
                orig_x = int(x * (self.current_frame.shape[1] / pixmap.width()))
                orig_y = int(y * (self.current_frame.shape[0] / pixmap.height()))
                
                # 更新終點
                self.current_end_point = (orig_x, orig_y)
                
                # 添加起點和終點到標註點列表
                self.annotation_points.append(self.current_start_point)
                self.annotation_points.append(self.current_end_point)
                
                # 計算當前組
                group_index = (len(self.annotation_points) - 1) // self.point_per_group
                
                print(f"完成繪製向量，從 {self.current_start_point} 到 {self.current_end_point}，第{group_index+1}組")
                
                # 重置繪製狀態
                self.is_drawing = False
                self.current_start_point = None
                self.current_end_point = None
                self.temp_display_frame = None
    
    def update_temp_display_frame(self):
        """更新臨時顯示幀，用於顯示正在繪製的向量"""
        if not self.is_drawing or self.current_start_point is None or self.current_end_point is None:
            return
        
        # 創建臨時顯示幀
        self.temp_display_frame = self.display_frame.copy()
        
        # 繪製已標註的向量
        for i in range(0, len(self.annotation_points), self.point_per_group):
            if i + 1 < len(self.annotation_points):
                start_point = self.annotation_points[i]
                end_point = self.annotation_points[i + 1]
                
                # 繪製向量
                cv2.arrowedLine(self.temp_display_frame, start_point, end_point, (0, 255, 255), 2)
                
                # 繪製起點和終點
                cv2.circle(self.temp_display_frame, start_point, 5, (0, 0, 255), -1)
                cv2.circle(self.temp_display_frame, end_point, 5, (255, 0, 0), -1)
                
                # 標註組號
                group_num = i // self.point_per_group + 1
                cv2.putText(self.temp_display_frame, f"G{group_num}", 
                          (start_point[0] + 10, start_point[1] + 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # 繪製當前正在繪製的向量
        cv2.arrowedLine(self.temp_display_frame, self.current_start_point, self.current_end_point, (0, 255, 0), 2)
        cv2.circle(self.temp_display_frame, self.current_start_point, 5, (0, 0, 255), -1)
        cv2.circle(self.temp_display_frame, self.current_end_point, 5, (255, 0, 0), -1)
        
        # 標註當前組號
        current_group_num = len(self.annotation_points) // self.point_per_group + 1
        cv2.putText(self.temp_display_frame, f"G{current_group_num}", 
                  (self.current_start_point[0] + 10, self.current_start_point[1] + 10), 
                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    def request_transformed_frame(self):
        """請求透視變換後的畫面並擷取當前幀"""
        print("請求透視變換後的畫面")
        # 發送請求透視變換後的幀信號
        self.request_transformed_frame_signal.emit()
        # 擷取當前幀
        self.capture_current_frame()
    
    def reset_annotations(self):
        """重置標註點"""
        self.annotation_points = []
        self.current_start_point = None
        self.current_end_point = None
        self.temp_display_frame = None
        print("已重置所有標註點")
    
    def send_annotations(self):
        """發送標註點"""
        expected_points = self.total_groups * self.point_per_group
        if len(self.annotation_points) != expected_points:
            print(f"標註點數量不足，需要 {expected_points} 個點，當前有 {len(self.annotation_points)} 個點")
            return
        
        # 如果已經在追蹤中，先停止舊的追蹤
        if self.tracking_active:
            self.stop_tracking()
        
        # 將標註點轉換為射水向量格式
        water_jet_vectors = []
        for i in range(0, len(self.annotation_points), self.point_per_group):
            if i + 1 < len(self.annotation_points):
                start_point = self.annotation_points[i]
                end_point = self.annotation_points[i + 1]
                water_jet_vectors.append((start_point[0], start_point[1], end_point[0], end_point[1]))
        
        print(f"發送射水向量: {water_jet_vectors}")
        # 發送射水向量信號
        self.water_jet_vectors_signal.emit(water_jet_vectors)
        
        # 發送後重置標註點
        self.reset_annotations()
        # 重置顯示幀狀態，清除 image_frame 上的編輯內容
        self.is_frame_captured = False
        self.display_frame = None

        # 啟動新的追蹤
        self.start_tracking()

    def stop_tracking(self):
        """停止追蹤模式"""
        print("停止追蹤模式")
        self.tracking_active = False
        
        # 清除追蹤顯示
        blank_frame = np.zeros((320, 320, 3), dtype=np.uint8)
        blank_frame[:] = (245, 245, 245)  # 淺灰色背景
        
        # 將空白圖像轉換為Qt圖像並顯示
        height, width, channel = blank_frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(blank_frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        
        # 重置顯示
        self.tracking_display.setPixmap(QPixmap.fromImage(q_img))
        self.flowmap_display.setPixmap(QPixmap.fromImage(q_img))
    
    def update_tracking_display(self, frame):
        """更新追蹤畫面"""
        if frame is not None and self.tracking_active:
            # 獲取顯示區域的大小
            display_width = self.tracking_display.width()
            display_height = self.tracking_display.height()
            
            # 獲取原始圖像的尺寸
            h, w = frame.shape[:2]
            aspect_ratio = w / h
            
            # 計算保持比例的縮放尺寸
            if display_width / display_height > aspect_ratio:
                # 顯示區域更寬，以高度為準
                new_height = display_height
                new_width = int(new_height * aspect_ratio)
            else:
                # 顯示區域更高，以寬度為準
                new_width = display_width
                new_height = int(new_width / aspect_ratio)
            
            # 調整大小以適應顯示區域，保持原始比例
            display_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            
            # 將OpenCV圖像轉換為Qt圖像
            height, width, channel = display_frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(display_frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            
            # 顯示圖像（不需要再次縮放）
            pixmap = QPixmap.fromImage(q_img)
            self.tracking_display.setPixmap(pixmap)

    def update_flowmap_display(self, flowmap):
        """更新FlowMap顯示"""
        if flowmap is not None and self.tracking_active:
            # 獲取顯示區域的大小
            display_width = self.flowmap_display.width()
            display_height = self.flowmap_display.height()
            
            # 獲取原始圖像的尺寸
            h, w = flowmap.shape[:2]
            aspect_ratio = w / h
            
            # 計算保持比例的縮放尺寸
            if display_width / display_height > aspect_ratio:
                # 顯示區域更寬，以高度為準
                new_height = display_height
                new_width = int(new_height * aspect_ratio)
            else:
                # 顯示區域更高，以寬度為準
                new_width = display_width
                new_height = int(new_width / aspect_ratio)
            
            # 調整大小以適應顯示區域，保持原始比例
            display_flowmap = cv2.resize(flowmap, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            
            # 將OpenCV圖像轉換為Qt圖像
            height, width, channel = display_flowmap.shape
            bytes_per_line = 3 * width
            q_img = QImage(display_flowmap.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            
            # 顯示圖像（不需要再次縮放）
            pixmap = QPixmap.fromImage(q_img)
            self.flowmap_display.setPixmap(pixmap)

    def start_tracking(self):
        """開始追蹤模式"""
        print("開始追蹤模式")
        self.tracking_active = True
        
        # 發送開始追蹤信號到主窗口
        self.parent.start_tracking_signal.emit()
    
    def go_to_previous_step(self):
        """切換至上一步(透視變換編輯頁面)"""
        self.parent.show_perspective_page()
    
    def reset_ui_display(self):
        """重置射水向量編輯頁面的UI顯示畫面"""
        self.annotation_points = []
        self.current_frame = None
        self.display_frame = None
        self.is_frame_captured = False
        self.current_start_point = None
        self.current_end_point = None
        self.temp_display_frame = None
        self.tracking_active = False
        
        # 重置圖像顯示[顯示透變換後結果畫面]
        blank_frame = np.zeros((512, 512, 3), dtype=np.uint8)
        blank_frame[:] = (245, 245, 240)  # 淺米色
        self.display_frame = blank_frame

        # 清空追蹤和FlowMap顯示區域
        self.tracking_display.clear()
        self.flowmap_display.clear()

        # 更新主顯示
        self.update_frame()
        print("射水向量編輯頁面UI顯示已重置")

# 如果直接運行此文件，則啟動UI
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlowMapUI()
    window.show()
    sys.exit(app.exec_())