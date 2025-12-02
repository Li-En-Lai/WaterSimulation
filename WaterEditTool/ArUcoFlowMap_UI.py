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
    # 添加訊號
    start_tracking_signal = pyqtSignal()  # 開始追蹤訊號
    pool_shape_signal = pyqtSignal(str) # 水池形狀訊號
    
    def __init__(self):
        super().__init__()
        
        # 儲存當前選擇的水池形狀
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

        # 連接水池形狀選擇頁面的訊號
        self.pool_shape_page.pool_shape_signal.connect(self.on_pool_shape_selected)
        
        # 將頁面添加到堆疊式頁面管理器
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.pool_shape_page)
        self.stacked_widget.addWidget(self.perspective_page)
        self.stacked_widget.addWidget(self.water_jet_page)
        
        # 初始顯示HomePage
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
    
        # 傳遞訊號
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
        bg_pixmap = QPixmap(r"WaterEditTool\UI_Images\HomePage.png")
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
        start_edit_bg_pth = r"WaterEditTool\UI_Images\EditButton.png"
        
        # 設置圖標
        start_edit_btn.setIcon(QIcon(start_edit_bg_pth))
        start_edit_btn.setIconSize(QSize(200, 60))  # 設置圖標大小，稍小於按鈕尺寸
        start_edit_btn.setCursor(Qt.PointingHandCursor)  # 滑鼠停滯於按鈕上變成手指形狀[代表可點擊，進行選擇]
        start_edit_btn.clicked.connect(self.parent.show_pool_shape_page)  # 直接進入水池形狀選擇頁面
        
        # 退出按鈕
        exit_btn = QPushButton("")
        exit_btn.setMinimumHeight(60)
        exit_btn.setMinimumWidth(200)
        exit_btn_bg_pth = r"WaterEditTool\UI_Images\ExitButton.png"

        # 設置圖標
        exit_btn.setIcon(QIcon(exit_btn_bg_pth))
        exit_btn.setIconSize(QSize(200, 60))  # 設置圖標大小，稍小於按鈕尺寸
        exit_btn.setCursor(Qt.PointingHandCursor)  # 滑鼠停滯於按鈕上變成手指形狀[代表可點擊，進行選擇]
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

    # 添加訊號
    pool_shape_signal = pyqtSignal(str) # 水池形狀選擇訊號

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

        # 設置Style Sheet，確保子元件皆為透明的
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QLabel {
                background-color: transparent;
            }
            /* 定義 ToolTip 樣式 */
            QToolTip {
                border: 1px solid #76797C;
                background-color: #5A5A5A;
                color: white;
                padding: 5px;
                opacity: 200;
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
        title_label = QLabel("First Stage: Select Pool Shape")
        title_label.setFont(QFont("Arial"))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft) # 文字內容水平靠左對齊，垂直置中對齊)
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #000000; background-color: transparent") # 稍微加大標題字體

        # 返回首頁按鈕
        home_btn = QPushButton("")
        home_btn.setFixedSize(50,50)
        home_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\ToHomePageButton.png"))
        home_btn.setIconSize(QSize(40,40))
        # home_btn.setToolTip("Back to Home Page") # 提示文字內容
        home_btn.setCursor(Qt.PointingHandCursor) # 滑鼠停滯於按鈕上變成手指形狀[代表可點擊，進行選擇]
        home_btn.clicked.connect(self.parent.show_home_page)

        # 添加到頂部佈局
        top_layout.addWidget(title_label,1)
        top_layout.addWidget(home_btn)

        # 創建引導說明文字區域
        instruction_container = QWidget()
        instruction_layout = QVBoxLayout(instruction_container)
        instruction_layout.setContentsMargins(0, 0, 0, 0)
        instruction_layout.setSpacing(5)

        # 主要引導文字
        hint_label = QLabel("Please select the geometry of your pool to initialize the calibration process")
        hint_label.setFont(QFont("Arial"))
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #000000; font-weight: 500;")

        # 次要引導說明文字
        sub_hint_label = QLabel("Different shapes will correspond to different perspective transformation algorithms")
        sub_hint_label.setFont(QFont("Arial"))
        sub_hint_label.setAlignment(Qt.AlignCenter)
        sub_hint_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #666666;")

        instruction_layout.addWidget(hint_label)
        instruction_layout.addWidget(sub_hint_label)

        # 創建水池形狀選擇按鈕區域
        shape_container = QWidget()
        shape_container.setStyleSheet("background-color: transparent;")
        shape_layout = QHBoxLayout(shape_container)
        shape_layout.setSpacing(50) # 增加按鈕之間的間距，讓畫面更寬敞

        # 圓形水池按鈕
        circle_btn = QPushButton("")
        circle_btn.setMinimumHeight(100)
        circle_btn.setMinimumWidth(220)
        circle_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\CirclePoolButton.png"))
        circle_btn.setIconSize(QSize(360, 360))
        # ToolTip 提示
        circle_btn.setToolTip("Select <b>Circle Pool Button</b> if your pool is round")
        circle_btn.setCursor(Qt.PointingHandCursor) # 滑鼠停滯於按鈕上變成手指形狀[代表可點擊，進行選擇]
        circle_btn.clicked.connect(lambda: self.select_pool_shape("circle"))
        
        # 矩形水池按鈕
        rectangle_btn = QPushButton("")
        rectangle_btn.setMinimumHeight(100)
        rectangle_btn.setMinimumWidth(220)
        rectangle_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\RectanglePoolButton.png"))
        rectangle_btn.setIconSize(QSize(360, 360))
        # ToolTip 提示
        rectangle_btn.setToolTip("Select <b>Rectangle Pool Button</b> if your pool is square or rectangular")
        rectangle_btn.setCursor(Qt.PointingHandCursor) # 滑鼠停滯於按鈕上變成手指形狀[代表可點擊，進行選擇]
        rectangle_btn.clicked.connect(lambda: self.select_pool_shape("rectangle"))
        
        # 添加按鈕到形狀選擇佈局
        shape_layout.addStretch(1) # 左側彈性空間
        shape_layout.addWidget(circle_btn)
        shape_layout.addWidget(rectangle_btn)
        shape_layout.addStretch(1) # 右側彈性空間
        
        # 創建底部按鈕區域
        bottom_nav_layout = QHBoxLayout()
        bottom_nav_layout.setContentsMargins(20, 0, 20, 20)
        bottom_nav_layout.setSpacing(10)
        
        # 添加所有元素到主佈局
        main_layout.addLayout(top_layout)
        
        main_layout.addStretch(1)       # 上方彈性空間
        main_layout.addWidget(instruction_container) # 加入引導文字
        main_layout.addSpacing(30)      # 文字與按鈕間的固定距離
        main_layout.addWidget(shape_container)  # 形狀選擇按鈕
        main_layout.addStretch(2)       # 下方彈性空間
        
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
    annotation_points_signal = pyqtSignal(list)  # 標註點訊號
    
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
        # 設置背景色
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#EEFFFE"))
        self.setPalette(palette)
        
        # 設置通用樣式表
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QLabel {
                background-color: transparent;
                color: #333333;
            }
            
            /* --- 步驟指引的樣式邏輯 --- */
            
            /* 1. 尚未執行的步驟 (Pending) - 灰色文字 */
            QLabel.step-label {
                font-size: 16px;
                font-weight: bold;
                color: #AAAAAA; /* 較淺的灰色，代表還沒輪到 */
                padding: 5px;
            }
            
            /* 2. 當前步驟 (Active) - 綠色文字 + 強調背景 */
            QLabel.step-active {
                font-size: 18px;
                font-weight: bold;
                color: #2E7D32; /* 深綠色文字，清晰易讀 */
                background-color: #E8F5E9; /* 極淺的綠色背景，增加層次感 */
                border: 2px solid #4CAF50; /* 綠色邊框 */
                border-radius: 5px; /* 圓角 */
                padding: 8px; /* 增加內距讓文字不要貼邊 */
            }
            
            /* 3. 已完成 (Done) - 灰色文字 + 刪除線 */
            QLabel.step-done {
                font-size: 16px;
                font-weight: bold;         
                color: #888888; /* 深灰色 */
                text-decoration: line-through; /* 關鍵：刪除線 */
                padding: 5px;
            }
        """)
        
        # === 主佈局 ===
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === 頂部區域 ===
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(20, 20, 20, 10)
        
        # 標題
        self.title_label = QLabel("")
        self.title_label.setFont(QFont("Arial")) # 設置標題的字型
        self.title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #2D2D30;")

        # 返回首頁按鈕
        home_btn = QPushButton("")
        home_btn.setFixedSize(50, 50)
        home_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\ToHomePageButton.png"))
        home_btn.setIconSize(QSize(40, 40))
        home_btn.setCursor(Qt.PointingHandCursor) # 滑鼠停滯於按鈕上變成手指形狀[代表可點擊，進行選擇]
        home_btn.clicked.connect(self.parent.show_home_page)
        
        # 將標題和返回按鈕添加到頂部區域
        top_layout.addWidget(self.title_label, 1)
        top_layout.addWidget(home_btn)
        
        # === 中間內容區域 ===
        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(20, 10, 20, 10)
        content_layout.setSpacing(20)
        
        # 左側：圖片顯示區
        image_container = QWidget()
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0,0,0,0)
        
        self.image_frame = QLabel()
        self.image_frame.setAlignment(Qt.AlignCenter)

        # 設定圖框樣式
        # 背景顏色:透明；邊框寬度:2px；邊框圓角:10px；邊框樣式:虛線；邊框顏色:#CCCCCC(淺灰色)
        self.image_frame.setStyleSheet("background-color: transparent; border-radius: 10px; border: 2px dashed #CCCCCC;")
        self.image_frame.setMinimumSize(640, 480)
        self.image_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_frame.mousePressEvent = self.on_image_click

        image_content = QLabel("Camera stream image of the current frame")
        image_content.setFont(QFont("Arial"))
        image_content.setAlignment(Qt.AlignCenter)
        image_content.setStyleSheet("font-size: 18px; font-weight: bold; color: #2D2D30; margin-bottom: 5px;")
        
        image_layout.addWidget(self.image_frame)
        image_layout.addWidget(image_content)
        
        # 右側：操作指引與按鈕
        control_panel = QFrame()
        control_panel.setFixedWidth(400) # 固定右側面板寬度
        control_panel.setStyleSheet("background-color: rgba(255,255,255,0.7); border-radius: 15px;") # 稍微增加不透明度
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(20, 30, 20, 30)
        control_layout.setSpacing(15)
        
        # 標題
        panel_title = QLabel("Setup Guide")
        panel_title.setFont(QFont("Arial")) # 設置標題的字型
        # margin-bottom: 10px 添加10像素的間隔
        panel_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2D2D30; margin-bottom: 10px;")
        control_layout.addWidget(panel_title)

        # 步驟 1 指引
        self.step1_label = QLabel("Step 1: Capture the current frame\nfrom the camera stream")
        self.step1_label.setFont(QFont("Arial"))
        self.step1_label.setProperty("class", "step-label")
        control_layout.addWidget(self.step1_label)

        # 擷取按鈕 (Capture)
        self.capture_btn = QPushButton("")
        self.capture_btn.setFixedSize(180, 40)
        self.capture_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\CaptureFrame.png"))
        self.capture_btn.setIconSize(QSize(180, 40))
        self.capture_btn.setStyleSheet("background-color: transparent; border: none;")
        self.capture_btn.setCursor(Qt.PointingHandCursor)
        self.capture_btn.clicked.connect(self.capture_current_frame)
        control_layout.addWidget(self.capture_btn, 0, Qt.AlignCenter)

        # 分隔線
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Plain)
        line1.setFixedHeight(1)             
        line1.setStyleSheet("background-color: #888888;")
        control_layout.addWidget(line1)

        # 步驟 2 指引
        self.step2_label = QLabel(f"Step 2: Select {self.max_points} reference points\nin the image on the left")
        self.step2_label.setFont(QFont("Arial"))
        self.step2_label.setProperty("class", "step-label")
        control_layout.addWidget(self.step2_label)
        
        # 點數計數器
        self.points_counter = QLabel("Points: 0 / 4")
        self.points_counter.setFont(QFont("Arial"))
        self.points_counter.setAlignment(Qt.AlignCenter)
        self.points_counter.setStyleSheet("font-size: 24px; font-weight: bold; color: #555555; margin: 10px 0;")
        control_layout.addWidget(self.points_counter)

        # 重置按鈕
        self.reset_btn = QPushButton("")
        self.reset_btn.setFixedSize(180, 40)
        self.reset_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\ResetPoints.png"))
        self.reset_btn.setIconSize(QSize(180, 40))
        self.reset_btn.setStyleSheet("background-color: transparent; border: none;")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self.reset_annotations)
        control_layout.addWidget(self.reset_btn, 0, Qt.AlignCenter)

        # 分隔線
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Plain)
        line2.setFixedHeight(1)             
        line2.setStyleSheet("background-color: #888888;")
        control_layout.addWidget(line2)

        # 步驟 3 指引
        self.step3_label = QLabel("Step 3: Set reference points\nfor perspective transformation")
        self.step3_label.setFont(QFont("Arial"))
        self.step3_label.setProperty("class", "step-label")
        control_layout.addWidget(self.step3_label)

        # 確認按鈕 (Confirm)
        self.confirm_btn = QPushButton("")
        self.confirm_btn.setFixedSize(180, 40)
        self.confirm_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\SetPoints.png"))
        self.confirm_btn.setIconSize(QSize(180, 40))
        self.confirm_btn.setStyleSheet("background-color: transparent; border: none;")
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.clicked.connect(self.send_annotations)
        self.confirm_btn.setEnabled(False) # 初始禁用
        control_layout.addWidget(self.confirm_btn, 0, Qt.AlignCenter)
        
        control_layout.addStretch(1) # 底部彈性空間

        # 將左右區域加入 content layout
        content_layout.addWidget(image_container, 1)
        content_layout.addWidget(control_panel)

        # --- 3. 底部按鈕區域 ---
        bottom_nav_layout = QHBoxLayout()
        bottom_nav_layout.setContentsMargins(20, 0, 20, 20)
        
        prev_btn = QPushButton("")
        prev_btn.setFixedSize(180, 50)
        prev_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\PreviousStep.png"))
        prev_btn.setIconSize(QSize(180, 50))
        prev_btn.setCursor(Qt.PointingHandCursor)
        prev_btn.clicked.connect(self.parent.show_pool_shape_page)
        
        next_btn = QPushButton("")
        next_btn.setFixedSize(180, 50)
        next_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\NextStep.png"))
        next_btn.setIconSize(QSize(180, 50))
        next_btn.setCursor(Qt.PointingHandCursor)
        next_btn.clicked.connect(self.go_to_next_step)
        
        bottom_nav_layout.addWidget(prev_btn)
        bottom_nav_layout.addStretch(1)
        bottom_nav_layout.addWidget(next_btn)

        # 添加到主佈局
        main_layout.addLayout(top_layout)
        main_layout.addWidget(content_container, 1) # 中間內容
        main_layout.addLayout(bottom_nav_layout)
        
        self.setLayout(main_layout)
        
        # 初始化指引狀態
        self.update_step_status(1)
        
        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_step_status(self, step):
        """更新步驟指引的Highlight狀態 (綠色/灰色/刪除線)"""
        # 重置所有標籤為預設狀態
        self.step1_label.setProperty("class", "step-label")
        self.step2_label.setProperty("class", "step-label")
        self.step3_label.setProperty("class", "step-label")
        
        # 根據當前步驟設置狀態
        if step == 1:
            # Step 1: 進行中 (Active)
            self.step1_label.setProperty("class", "step-active")
            # Step 2, 3: 未開始 (Pending)
        elif step == 2:
            # Step 1: 已完成 (Done)
            self.step1_label.setProperty("class", "step-done")
            # Step 2: 進行中 (Active)
            self.step2_label.setProperty("class", "step-active")
            # Step 3: 未開始 (Pending)
        elif step == 3:
            # Step 1, 2: 已完成 (Done)
            self.step1_label.setProperty("class", "step-done")
            self.step2_label.setProperty("class", "step-done")
            # Step 3: 進行中 (Active)
            self.step3_label.setProperty("class", "step-active")
            
        # 強制刷新樣式 (需要此步驟來應用動態屬性的變化)
        self.style().unpolish(self.step1_label)
        self.style().polish(self.step1_label)
        self.style().unpolish(self.step2_label)
        self.style().polish(self.step2_label)
        self.style().unpolish(self.step3_label)
        self.style().polish(self.step3_label)

    def update_for_pool_shape(self,shape):
        '''根據在水池形狀選擇頁面選擇的結果更新'''
        self.pool_shape = shape
        self.title_label.setText(f"Second Stage: Perspective transformation reference points edit for {self.pool_shape} pool")
    
    def update_camera_frame(self, frame):
        """從攝像頭更新幀"""
        if frame is not None:
            self.current_frame = frame.copy()
            # 如果尚未擷取幀，顯示預覽提示
            if not self.is_frame_captured:
                preview_frame = self.current_frame.copy()
                # 增加半透明遮罩讓文字更清楚
                overlay = preview_frame.copy()
                cv2.rectangle(overlay, (0, 0), (preview_frame.shape[1], 60), (0,0,0), -1)
                cv2.addWeighted(overlay, 0.5, preview_frame, 0.5, 0, preview_frame)
                
                cv2.putText(preview_frame, "Preview Mode - Click 'Capture' to start", 
                          (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                self.display_frame = preview_frame
    
    def capture_current_frame(self):
        """擷取當前幀"""
        print("按下 Capture 按鈕")
        if self.current_frame is not None:
            self.display_frame = self.current_frame.copy()
            self.is_frame_captured = True
            self.annotation_points = []
            
            # 更新UI狀態 -> 進入步驟 2
            self.update_step_status(2) 
            self.points_counter.setText(f"Points: 0 / {self.max_points}")
            self.points_counter.setStyleSheet("font-size: 24px; font-weight: bold; color: #888888; margin: 10px 0;") # 點數文字變深灰色
            self.image_frame.setStyleSheet("background-color: transparent; border-radius: 10px; border: 2px dashed #4CAF50;") # 邊框變綠表示已鎖定
            
            print("已擷取當前幀，可以開始標註參考點")
    
    def update_frame_from_camera(self, frame):
        """從攝像頭更新幀"""
        if frame is not None:
            self.current_frame = frame.copy()
    
    def update_frame(self):
        """更新圖像幀到 UI"""
        if self.display_frame is None:
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            blank_frame[:] = (245, 245, 240)
            cv2.putText(blank_frame, "Waiting for Camera...", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (100,100,100), 2)
            self.display_frame = blank_frame
        
        frame_with_annotations = self.display_frame.copy()
        
        # 繪製標註點
        for i, point in enumerate(self.annotation_points):
            # 畫圓圈
            cv2.circle(frame_with_annotations, point, 5, (0, 0, 255), -1)
            # 標註點編號文字
            cv2.putText(frame_with_annotations, f"P{i+1}", 
                      (point[0] + 10, point[1] + 10), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # 圖像縮放與顯示
        display_height = self.image_frame.height()
        display_width = self.image_frame.width()
        h, w = frame_with_annotations.shape[:2]
        if h == 0 or w == 0: return

        aspect_ratio = w / h
        if display_width / display_height > aspect_ratio:
            new_height = display_height
            new_width = int(new_height * aspect_ratio)
        else:
            new_width = display_width
            new_height = int(new_width / aspect_ratio)
        
        if new_width > 0 and new_height > 0:
            resized_frame = cv2.resize(frame_with_annotations, (new_width, new_height), 
                                     interpolation=cv2.INTER_LANCZOS4)
            height, width, channel = resized_frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(resized_frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            self.image_frame.setPixmap(QPixmap.fromImage(q_img))
    
    def on_image_click(self, event):
        """處理圖像點擊事件"""
        if not self.is_frame_captured:
            print("請先點擊 Capture")
            return
        
        if len(self.annotation_points) >= self.max_points:
            return
        
        pos = event.pos()
        pixmap = self.image_frame.pixmap()
        if pixmap:
            img_rect = QRect(0, 0, pixmap.width(), pixmap.height())
            img_rect.moveCenter(QPoint(self.image_frame.width() // 2, self.image_frame.height() // 2))
            
            if img_rect.contains(pos):
                x = pos.x() - img_rect.left()
                y = pos.y() - img_rect.top()
                orig_x = int(x * (self.current_frame.shape[1] / pixmap.width()))
                orig_y = int(y * (self.current_frame.shape[0] / pixmap.height()))
                
                self.annotation_points.append((orig_x, orig_y))
                
                # 更新計數器UI
                count = len(self.annotation_points)
                self.points_counter.setText(f"Points: {count} / {self.max_points}")
                
                # 檢查是否完成
                if count == self.max_points:
                    self.update_step_status(3) # 進入步驟 3
                    self.confirm_btn.setEnabled(True)
                    self.confirm_btn.setStyleSheet(self.confirm_btn.styleSheet().replace("background-color: #BDBDBD;", ""))
    
    def reset_annotations(self):
        """重置標註點"""
        self.annotation_points = []
        self.points_counter.setText(f"Points: 0 / {self.max_points}")
        self.points_counter.setStyleSheet("font-size: 24px; font-weight: bold; color: #888888; margin: 10px 0;")
        self.update_step_status(2) # 回到步驟 2
        self.confirm_btn.setEnabled(False)
        print("已重置所有標註點")
    
    def send_annotations(self):
        """發送標註點"""
        if len(self.annotation_points) != self.max_points:
            return
        
        print(f"發送標註點: {self.annotation_points}")
        self.annotation_points_signal.emit(self.annotation_points)
        self.reset_annotations()
        self.is_frame_captured = False
        self.update_step_status(1) # 重置回步驟 1
        self.image_frame.setStyleSheet("background-color: rgba(0,0,0,0.05); border-radius: 10px; border: 2px dashed #CCCCCC;")
        
        self.go_to_next_step()
    
    def go_to_next_step(self):
        """進入下一步"""
        self.parent.show_water_jet_page()
    
    def reset_ui_display(self):
        """重置UI顯示"""
        self.annotation_points = []
        self.current_frame = None
        self.display_frame = None
        self.is_frame_captured = False
        self.points_counter.setText(f"Points: 0 / {self.max_points}")
        self.points_counter.setStyleSheet("font-size: 24px; font-weight: bold; color: #888888; margin: 10px 0;")
        self.update_step_status(1)
        
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        blank_frame[:] = (245, 245, 240)
        self.display_frame = blank_frame
        self.update_frame()

class WaterJetCalibrationPage(QWidget):
    """射水向量校準頁面Class"""
    
    # 添加訊號
    water_jet_vectors_signal = pyqtSignal(list)  # 射水向量訊號
    request_transformed_frame_signal = pyqtSignal()  # 請求透視變換後的幀訊號
    
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
        self.current_start_point = None # 當前繪製的射水向量起點
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

        # 設置StyleSheet
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QLabel {
                background-color: transparent;
            }
            /* --- 步驟指引的樣式邏輯 --- */
            
            /* 1. 尚未執行的步驟 (Pending) - 灰色文字 */
            QLabel.step-label {
                font-size: 16px;
                font-weight: bold;
                color: #AAAAAA;
                padding: 5px;
            }
            
            /* 2. 當前步驟 (Active) - 綠色文字 + 強調背景 */
            QLabel.step-active {
                font-size: 18px;
                font-weight: bold;
                color: #2E7D32; /* 深綠色 */
                background-color: #E8F5E9; /* 淺綠背景 */
                border: 2px solid #4CAF50; /* 綠色邊框 */
                border-radius: 5px;
                padding: 8px;
            }
            
            /* 3. 已完成 (Done) - 灰色文字 + 刪除線 */
            QLabel.step-done {
                font-size: 16px;
                font-weight: bold;         
                color: #888888;
                text-decoration: line-through;
                padding: 5px;
            }
        """)

        # 創建主佈局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 頂部區域 ===
        top_layout = QHBoxLayout() # 水平佈局
        top_layout.setContentsMargins(20,20,20,10)
        top_layout.setSpacing(10)
         
        # 標題
        title_label = QLabel("Final Stage: Water jet vectors editing")
        title_label.setFont(QFont("Arial"))
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #2D2D30;")

        # 返回首頁按鈕
        home_btn = QPushButton("")
        home_btn.setFixedSize(50,50)
        home_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\ToHomePageButton.png"))
        home_btn.setIconSize(QSize(40,40))
        home_btn.setCursor(Qt.PointingHandCursor) # 滑鼠停滯於按鈕上變成手指形狀[代表可點擊，進行選擇]
        home_btn.clicked.connect(self.parent.show_home_page)

        top_layout.addWidget(title_label,1)
        top_layout.addWidget(home_btn)

        # === 中央內容區域 (左:編輯圖 / 中:使用者操作指引 / 右:結果圖) ===
        central_container = QWidget()
        central_layout = QHBoxLayout(central_container)
        central_layout.setContentsMargins(20, 10, 20, 10)
        central_layout.setSpacing(20)

        # [左側] 圖像顯示區域 (顯示透視變換後的Frame)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0,0,0,0)
        
        self.image_frame = QLabel()
        self.image_frame.setAlignment(Qt.AlignCenter)

        # 初始虛線邊框
        self.image_frame.setStyleSheet("background-color: rgba(0,0,0,0.05); border-radius: 10px; border: 2px dashed #CCCCCC;")
        self.image_frame.setMinimumSize(512, 512) # 固定大小
        
        # 滑鼠事件綁定
        self.image_frame.mousePressEvent = self.on_mouse_press
        self.image_frame.mouseMoveEvent = self.on_mouse_move
        self.image_frame.mouseReleaseEvent = self.on_mouse_release
        
        left_label = QLabel("Streaming image after perspective transformation")
        left_label.setFont(QFont("Arial"))
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2D2D30;")
        
        left_layout.addWidget(self.image_frame)
        left_layout.addWidget(left_label)

        # [中間] 操作指引面板 (Setup Guide)
        guide_panel = QFrame()
        guide_panel.setFixedWidth(420) # 固定寬度
        guide_panel.setStyleSheet("background-color: rgba(255,255,255,0.7); border-radius: 15px;")
        guide_layout = QVBoxLayout(guide_panel)
        guide_layout.setContentsMargins(15, 20, 15, 20)
        guide_layout.setSpacing(10)

        # 操作指引標題
        guide_title = QLabel("Setup Guide")
        guide_title.setFont(QFont("Arial"))
        guide_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2D2D30; margin-bottom: 5px;")
        guide_layout.addWidget(guide_title)

        # Step 1: Capture
        self.step1_label = QLabel("Step 1: Capture the current frame\nafter perspective transformation")
        self.step1_label.setFont(QFont("Arial"))
        self.step1_label.setProperty("class", "step-label")
        guide_layout.addWidget(self.step1_label)

        self.capture_btn = QPushButton("")
        self.capture_btn.setFixedSize(180, 40)
        self.capture_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\CaptureFrame.png"))
        self.capture_btn.setIconSize(QSize(180, 40))
        self.capture_btn.setCursor(Qt.PointingHandCursor)
        self.capture_btn.clicked.connect(self.request_transformed_frame)
        guide_layout.addWidget(self.capture_btn, 0, Qt.AlignCenter)

        # 分隔線 1
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFixedHeight(1)
        line1.setStyleSheet("background-color: #AAAAAA;")
        guide_layout.addWidget(line1)

        # Step 2: Draw Vectors
        self.step2_label = QLabel(f"Step 2: Draw {self.total_groups} water jet vectors\nin the image on the left(Drag & Drop)")
        self.step2_label.setFont(QFont("Arial"))
        self.step2_label.setProperty("class", "step-label")
        guide_layout.addWidget(self.step2_label)

        # 向量計數器
        self.vector_counter = QLabel("Vectors: 0 / 6")
        self.vector_counter.setFont(QFont("Arial"))
        self.vector_counter.setAlignment(Qt.AlignCenter)
        self.vector_counter.setStyleSheet("font-size: 24px; font-weight: bold; color: #888888; margin: 5px 0;")
        guide_layout.addWidget(self.vector_counter)

        self.reset_btn = QPushButton("")
        self.reset_btn.setFixedSize(180, 40)
        self.reset_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\ResetVectors.png"))
        self.reset_btn.setIconSize(QSize(180, 40))
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self.reset_annotations)
        guide_layout.addWidget(self.reset_btn, 0, Qt.AlignCenter)

        # 分隔線 2
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFixedHeight(1)
        line2.setStyleSheet("background-color: #AAAAAA;")
        guide_layout.addWidget(line2)

        # Step 3: Confirm
        self.step3_label = QLabel("Step 3: Apply the edited water jet vectors\nand begin tracking")
        self.step3_label.setFont(QFont("Arial"))
        self.step3_label.setProperty("class", "step-label")
        guide_layout.addWidget(self.step3_label)

        self.confirm_btn = QPushButton("")
        self.confirm_btn.setFixedSize(180, 40)
        # 這裡假設您有 Apply 的圖片，如果沒有可以使用 ApplyWaterJetVector.png
        self.confirm_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\ApplyVectors.png")) 
        self.confirm_btn.setIconSize(QSize(180, 40)) # 調整大小以適應按鈕
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.clicked.connect(self.send_annotations)
        self.confirm_btn.setEnabled(False) # 初始禁用
        guide_layout.addWidget(self.confirm_btn, 0, Qt.AlignCenter)

        guide_layout.addStretch(1) # 底部空間

        # [右側] 結果顯示區域 (Tracking + FlowMap)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setSpacing(10)

        # Tracking Display
        self.tracking_display = QLabel()
        self.tracking_display.setAlignment(Qt.AlignCenter)
        self.tracking_display.setStyleSheet("background-color: transparent; border-radius: 5px; border: 1px solid #999;")
        self.tracking_display.setMinimumSize(320, 320)
        
        track_label = QLabel("Real-time Tracking")
        track_label.setFont(QFont("Arial"))
        track_label.setAlignment(Qt.AlignCenter)
        track_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")

        # FlowMap Display
        self.flowmap_display = QLabel()
        self.flowmap_display.setAlignment(Qt.AlignCenter)
        self.flowmap_display.setStyleSheet("background-color: transparent; border-radius: 5px; border: 1px solid #999;")
        self.flowmap_display.setMinimumSize(320, 320)
        
        flow_label = QLabel("Generated Flowmap")
        flow_label.setFont(QFont("Arial"))
        flow_label.setAlignment(Qt.AlignCenter)
        flow_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")

        right_layout.addWidget(track_label)
        right_layout.addWidget(self.tracking_display)
        right_layout.addWidget(flow_label)
        right_layout.addWidget(self.flowmap_display)
        right_layout.addStretch(1)

        # 將三塊區域加入中央佈局
        central_layout.addWidget(left_panel)
        central_layout.addWidget(guide_panel)
        central_layout.addWidget(right_panel)

        # === 底部按鈕區域 (Previous Step) ===
        bottom_nav_layout = QHBoxLayout()
        bottom_nav_layout.setContentsMargins(20, 0, 20, 20)
        
        prev_btn = QPushButton("")
        prev_btn.setFixedSize(180, 50)
        prev_btn.setIcon(QIcon(r"WaterEditTool\UI_Images\PreviousStep.png"))
        prev_btn.setIconSize(QSize(180, 50))
        prev_btn.setCursor(Qt.PointingHandCursor)
        prev_btn.clicked.connect(self.go_to_previous_step)
        
        bottom_nav_layout.addWidget(prev_btn)
        bottom_nav_layout.addStretch(1)

        # 添加所有元素到主佈局
        main_layout.addLayout(top_layout)
        main_layout.addWidget(central_container, 1)
        main_layout.addLayout(bottom_nav_layout)
        
        self.setLayout(main_layout)
        
        # 初始化指引狀態
        self.update_step_status(1)

        # 創建定時器，用於更新圖像
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 每30毫秒更新一次

        # 初始化追蹤相關變數
        self.tracking_active = False
        self.tracker = None
    
    def update_step_status(self, step):
        """更新步驟指引的Highlight狀態 (綠色/灰色/刪除線)"""
        # 重置所有標籤
        self.step1_label.setProperty("class", "step-label")
        self.step2_label.setProperty("class", "step-label")
        self.step3_label.setProperty("class", "step-label")
        
        # 根據當前步驟設置
        if step == 1:
            self.step1_label.setProperty("class", "step-active")
        elif step == 2:
            self.step1_label.setProperty("class", "step-done")
            self.step2_label.setProperty("class", "step-active")
        elif step == 3:
            self.step1_label.setProperty("class", "step-done")
            self.step2_label.setProperty("class", "step-done")
            self.step3_label.setProperty("class", "step-active")
            
        # 刷新樣式
        self.style().unpolish(self.step1_label)
        self.style().polish(self.step1_label)
        self.style().unpolish(self.step2_label)
        self.style().polish(self.step2_label)
        self.style().unpolish(self.step3_label)
        self.style().polish(self.step3_label)

    def update_frame_from_camera(self, frame):
        """從攝像頭更新幀"""
        if frame is not None:
            self.current_frame = frame.copy()
    
    def capture_current_frame(self):
        """擷取當前幀"""
        print("按下 Capture 按鈕")
        if self.current_frame is not None:
            self.display_frame = self.current_frame.copy()
            self.is_frame_captured = True
            self.annotation_points = []  # 重置標註點
            
            # 更新UI狀態 -> 進入步驟 2
            self.update_step_status(2)
            self.vector_counter.setText(f"Vectors: 0 / {self.total_groups}")
            self.vector_counter.setStyleSheet("font-size: 24px; font-weight: bold; color: #888888; margin: 5px 0;")
            self.image_frame.setStyleSheet("background-color: transparent; border-radius: 10px; border: 2px solid #4CAF50;") # 綠框
            
            print("已擷取當前幀，可以開始標註射水向量")
    
    def request_transformed_frame(self):
        """請求透視變換後的畫面並擷取當前幀"""
        print("請求透視變換後的畫面")
        # 發送請求透視變換後的幀信號
        self.request_transformed_frame_signal.emit()
        # 擷取當前幀 (這會觸發 capture_current_frame)
        self.capture_current_frame()

    def update_frame(self):
        """更新圖像幀"""
        # 如果沒有幀可顯示，使用空白圖像
        if self.display_frame is None:
            blank_frame = np.zeros((512, 512, 3), dtype=np.uint8)
            blank_frame[:] = (245, 245, 245)  # 深灰色背景
            # 顯示等待文字
            cv2.putText(blank_frame, "Waiting for Capture...", (130, 256), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100,100,100), 2)
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
                
                # 轉換為原始圖像坐標 (這裡假設 display_frame 是 512x512 或與 current_frame 比例一致)
                # 注意：這裡應該用 current_frame 的尺寸來做反投影
                frame_h, frame_w = self.current_frame.shape[:2]
                
                # 簡單的比例換算
                orig_x = int(x * (frame_w / pixmap.width()))
                orig_y = int(y * (frame_h / pixmap.height()))
                
                # 設置繪製起點
                self.current_start_point = (orig_x, orig_y)
                self.current_end_point = (orig_x, orig_y)  # 初始化終點與起點相同
                self.is_drawing = True
                
                # 創建臨時顯示幀
                self.update_temp_display_frame()

    def on_mouse_move(self, event):
        """處理滑鼠移動事件"""
        if not self.is_drawing or self.current_start_point is None:
            return
        
        # 獲取當前位置
        pos = event.pos()
        pixmap = self.image_frame.pixmap()
        if pixmap:
            img_rect = QRect(0, 0, pixmap.width(), pixmap.height())
            img_rect.moveCenter(QPoint(self.image_frame.width() // 2, self.image_frame.height() // 2))
            
            if img_rect.contains(pos):
                x = pos.x() - img_rect.left()
                y = pos.y() - img_rect.top()
                
                frame_h, frame_w = self.current_frame.shape[:2]
                orig_x = int(x * (frame_w / pixmap.width()))
                orig_y = int(y * (frame_h / pixmap.height()))
                
                # 更新終點
                self.current_end_point = (orig_x, orig_y)
                
                # 更新臨時顯示幀
                self.update_temp_display_frame()

    def on_mouse_release(self, event):
        """處理滑鼠釋放事件"""
        if not self.is_drawing or self.current_start_point is None:
            return
        
        # 結束繪製，確認終點
        # 這裡直接使用 current_end_point，假設 mouseMove 已經更新了最後位置
        # 如果需要更精確，可以再次計算 event.pos()
        
        if self.current_end_point:
            # 添加起點和終點到標註點列表
            self.annotation_points.append(self.current_start_point)
            self.annotation_points.append(self.current_end_point)
            
            # 計算已完成的組數
            completed_groups = len(self.annotation_points) // self.point_per_group
            
            # 更新UI計數器
            self.vector_counter.setText(f"Vectors: {completed_groups} / {self.total_groups}")
            
            # 檢查是否完成所有向量
            if completed_groups == self.total_groups:
                self.update_step_status(3) # 進入 Step 3
                self.confirm_btn.setEnabled(True) # 啟用確認按鈕
            
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
        
        # 繪製已標註的向量 (保持原有的)
        for i in range(0, len(self.annotation_points), self.point_per_group):
            if i + 1 < len(self.annotation_points):
                start_point = self.annotation_points[i]
                end_point = self.annotation_points[i + 1]
                cv2.arrowedLine(self.temp_display_frame, start_point, end_point, (0, 255, 255), 2)
                cv2.circle(self.temp_display_frame, start_point, 5, (0, 0, 255), -1)
                cv2.circle(self.temp_display_frame, end_point, 5, (255, 0, 0), -1)
                group_num = i // self.point_per_group + 1
                cv2.putText(self.temp_display_frame, f"G{group_num}", 
                          (start_point[0] + 10, start_point[1] + 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # 繪製當前正在繪製的向量 (綠色)
        cv2.arrowedLine(self.temp_display_frame, self.current_start_point, self.current_end_point, (0, 255, 0), 2)
        cv2.circle(self.temp_display_frame, self.current_start_point, 5, (0, 0, 255), -1)
        cv2.circle(self.temp_display_frame, self.current_end_point, 5, (255, 0, 0), -1)
        
        # 標註當前組號
        current_group_num = len(self.annotation_points) // self.point_per_group + 1
        cv2.putText(self.temp_display_frame, f"G{current_group_num}", 
                  (self.current_start_point[0] + 10, self.current_start_point[1] + 10), 
                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    def reset_annotations(self):
        """重置標註點"""
        self.annotation_points = []
        self.current_start_point = None
        self.current_end_point = None
        self.temp_display_frame = None
        
        # UI 重置
        self.vector_counter.setText(f"Vectors: 0 / {self.total_groups}")
        self.vector_counter.setStyleSheet("font-size: 24px; font-weight: bold; color: #888888; margin: 5px 0;")
        self.confirm_btn.setEnabled(False)
        self.update_step_status(2) # 回到 Step 2
        
        print("已重置所有射水向量標註")
    
    def send_annotations(self):
        """發送標註點"""
        expected_points = self.total_groups * self.point_per_group
        if len(self.annotation_points) != expected_points:
            print(f"標註點數量不足，需要 {expected_points} 個點")
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
        
        # UI 狀態更新
        self.update_step_status(3)
        
        # 啟動新的追蹤
        self.start_tracking()

    def stop_tracking(self):
        """停止追蹤模式"""
        print("停止追蹤模式")
        self.tracking_active = False
        
        w = self.tracking_display.width() if self.tracking_display.width() > 0 else 320
        h = self.tracking_display.height() if self.tracking_display.height() > 0 else 320

        # 清除追蹤顯示
        blank_frame = np.zeros((h, w, 3), dtype=np.uint8) # 調整大小匹配UI
        blank_frame[:] = (240, 240, 240)
        
        height, width, channel = blank_frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(blank_frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        
        pixmap = QPixmap.fromImage(q_img)

        self.tracking_display.setPixmap(pixmap)
        self.flowmap_display.setPixmap(pixmap)
    
    def update_tracking_display(self, frame):
        """更新追蹤畫面 (顯示在右側小視窗)"""
        if frame is not None and self.tracking_active:
            # 調整大小以適應 240x240 的顯示區域
            # display_frame = cv2.resize(frame, (240, 240), interpolation=cv2.INTER_LANCZOS4)
            
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
            scaled_pixmap = pixmap.scaled(self.tracking_display.size(), 
                                        Qt.KeepAspectRatio, 
                                        Qt.SmoothTransformation)
            self.tracking_display.setPixmap(scaled_pixmap)

    def update_flowmap_display(self, flowmap):
        """更新FlowMap顯示 (顯示在右側小視窗)"""
        if flowmap is not None and self.tracking_active:
            # display_flowmap = cv2.resize(flowmap, (240, 240), interpolation=cv2.INTER_LANCZOS4)
            
            height, width, channel = flowmap.shape
            bytes_per_line = 3 * width
            q_img = QImage(flowmap.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

            pixmap = QPixmap.fromImage(q_img)

            scaled_pixmap = pixmap.scaled(self.flowmap_display.size(), 
                                        Qt.KeepAspectRatio, 
                                        Qt.SmoothTransformation)
            
            self.flowmap_display.setPixmap(scaled_pixmap)

    def start_tracking(self):
        """開始追蹤模式"""
        print("開始追蹤模式")
        self.tracking_active = True
        self.parent.start_tracking_signal.emit()
    
    def go_to_previous_step(self):
        """切換至上一步"""
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
        
        # 重置指引UI
        self.vector_counter.setText(f"Vectors: 0 / {self.total_groups}")
        self.vector_counter.setStyleSheet("font-size: 24px; font-weight: bold; color: #888888; margin: 5px 0;")
        self.update_step_status(1)
        self.confirm_btn.setEnabled(False)
        self.image_frame.setStyleSheet("background-color: rgba(0,0,0,0.05); border-radius: 10px; border: 2px dashed #CCCCCC;")

        # 清空顯示
        self.tracking_display.clear()
        self.flowmap_display.clear()
        
        blank_frame = np.zeros((512, 512, 3), dtype=np.uint8)
        blank_frame[:] = (245, 245, 240)
        self.display_frame = blank_frame
        self.update_frame()
        print("射水向量編輯頁面UI顯示已重置")

# 如果直接運行此文件，則啟動UI
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlowMapUI()
    window.show()
    sys.exit(app.exec_())