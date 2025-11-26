import cv2
import cv2.aruco as aruco
import numpy as np
import time
import threading
import sys
from TCP_Server import FlowMapServer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from ArUcoFlowMap_UI import FlowMapUI

class KalmanMarkerTracker:
    """使用卡爾曼濾波器追蹤 ArUco 標記"""
    
    def __init__(self, marker_id, initial_position, initial_rotation, dt=1/30.0):
        """
        初始化標記追蹤器
        
        參數:
        marker_id: 標記ID
        initial_position: 初始位置 [x, y]
        initial_rotation: 初始旋轉角度
        dt: 時間步長（預設為30FPS的倒數）
        """
        self.marker_id = marker_id
        self.last_update_time = time.time()
        self.missed_frames = 0
        self.max_missed_frames = 30  # 最多允許連續丟失30幀
        
        # 初始化卡爾曼濾波器 (8維狀態: x, y, vx, vy, ax, ay, rotation, rotation_velocity)
        self.kf = cv2.KalmanFilter(8, 3)  # 8維狀態，3維測量 (x, y, rotation)
        
        # 狀態轉移矩陣 (物理運動模型)
        self.kf.transitionMatrix = np.array([
            [1, 0, dt, 0, 0.5*dt*dt, 0, 0, 0],          # x = x + vx*dt + 0.5*ax*dt^2
            [0, 1, 0, dt, 0, 0.5*dt*dt, 0, 0],          # y = y + vy*dt + 0.5*ay*dt^2
            [0, 0, 1, 0, dt, 0, 0, 0],                  # vx = vx + ax*dt
            [0, 0, 0, 1, 0, dt, 0, 0],                  # vy = vy + ay*dt
            [0, 0, 0, 0, 1, 0, 0, 0],                   # ax = ax
            [0, 0, 0, 0, 0, 1, 0, 0],                   # ay = ay
            [0, 0, 0, 0, 0, 0, 1, dt],                  # rotation = rotation + w*dt
            [0, 0, 0, 0, 0, 0, 0, 1]                    # w = w
        ], np.float32)
        
        # 測量矩陣 (只測量位置和旋轉角度)
        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0, 0, 0, 0, 0],                   # 測量 x
            [0, 1, 0, 0, 0, 0, 0, 0],                   # 測量 y
            [0, 0, 0, 0, 0, 0, 1, 0]                    # 測量 rotation
        ], np.float32)
        
        # 過程雜訊共變異數矩陣
        self.kf.processNoiseCov = np.eye(8, dtype=np.float32) * 0.01
        self.kf.processNoiseCov[4:6, 4:6] *= 1.0  # 加速度雜訊較大
        
        # 測量雜訊共變異數矩陣
        self.kf.measurementNoiseCov = np.eye(3, dtype=np.float32) * 0.1
        
        # 後驗錯誤估計共變異數矩陣
        self.kf.errorCovPost = np.eye(8, dtype=np.float32) * 1.0
        
        # 初始狀態
        self.kf.statePost = np.array([
            [initial_position[0]],  # x
            [initial_position[1]],  # y
            [0],                    # vx
            [0],                    # vy
            [0],                    # ax
            [0],                    # ay
            [initial_rotation],     # rotation
            [0]                     # rotation velocity
        ], np.float32)
    
    def update(self, position, rotation):
        """
        使用新的測量值更新濾波器
        
        參數:
        position: [x, y] 位置
        rotation: 旋轉角度
        """
        # 計算時間差
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # 更新狀態轉移矩陣中的時間步長
        self.kf.transitionMatrix[0, 2] = dt
        self.kf.transitionMatrix[1, 3] = dt
        self.kf.transitionMatrix[0, 4] = 0.5 * dt * dt
        self.kf.transitionMatrix[1, 5] = 0.5 * dt * dt
        self.kf.transitionMatrix[2, 4] = dt
        self.kf.transitionMatrix[3, 5] = dt
        self.kf.transitionMatrix[6, 7] = dt
        
        # 預測
        self.kf.predict()
        
        # 更新
        measurement = np.array([[position[0]], [position[1]], [rotation]], np.float32)
        self.kf.correct(measurement)
        
        # 重置丟失幀計數
        self.missed_frames = 0
        
        return self.get_state()
    
    def predict(self):
        """
        預測下一個狀態（當標記未被檢測到時使用）
        """
        # 計算時間差
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # 更新狀態轉移矩陣中的時間步長
        self.kf.transitionMatrix[0, 2] = dt
        self.kf.transitionMatrix[1, 3] = dt
        self.kf.transitionMatrix[0, 4] = 0.5 * dt * dt
        self.kf.transitionMatrix[1, 5] = 0.5 * dt * dt
        self.kf.transitionMatrix[2, 4] = dt
        self.kf.transitionMatrix[3, 5] = dt
        self.kf.transitionMatrix[6, 7] = dt
        
        # 預測
        self.kf.predict()
        
        # 增加丟失幀計數
        self.missed_frames += 1
        
        return self.get_state()
    
    def get_state(self):
        """
        獲取當前狀態
        """
        state = self.kf.statePost
        return {
            "position": [float(state[0][0]), float(state[1][0])],
            "velocity": [float(state[2][0]), float(state[3][0])],
            "rotation": float(state[6][0]),
            "is_predicted": self.missed_frames > 0,
            "missed_frames": self.missed_frames
        }
    
    def is_valid(self):
        """
        檢查追蹤器是否仍然有效（未超過最大丟失幀數）
        """
        return self.missed_frames <= self.max_missed_frames

class PoolDetector:
    """水池檢測和校準類""" 
    def __init__(self, fixed_marker_ids, world_radius=2.5,pool_shape = "circle"):
        """初始化水池檢測器"""
        # 共同參數
        self.transform_matrix = None      # 透視變換矩陣
        self.world_radius = world_radius  # 世界水池半徑 (公尺)
        self.pool_shape = pool_shape      # 水池形狀(預設為圓形)
        self.pool_center = None           # 變換後的水池中心
        # 針對[圓形水池]的參數
        self.pool_radius = None           # 變換後的水池半徑
        self.target_size = None           # 輸出目標大小
        # 針對[矩形水池]的參數
        self.pool_rect = None             # 矩形水池邊界
        self.output_width = None          # 矩形水池透視變換輸出寬度
        self.output_height = None          # 矩形水池透視變換輸出高度
        # ArUco 設定
        self.fixed_marker_ids = fixed_marker_ids # 固定Marker ID
        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        self.aruco_params = aruco.DetectorParameters()
        # ArUco Marker檢測參數調整
        self.aruco_params.adaptiveThreshWinSizeMin = 3
        self.aruco_params.adaptiveThreshWinSizeMax = 40
        self.aruco_params.adaptiveThreshWinSizeStep = 2

    def image_to_canvas_coords(self, img_x, img_y, canvas_width, canvas_height=None):
        """將圖像座標轉換為畫布座標[用於訂定FlowMap的畫布大小]"""

        if canvas_height is None:
            canvas_height = canvas_width # 針對圓形水池的處理(透視變換結果為方形)

        if self.pool_shape == "circle":
            # 原有的圓形處理邏輯
            u_c, v_c = self.pool_center
            dx, dy = img_x - u_c, img_y - v_c
            
            rho = np.sqrt(dx**2 + dy**2) / self.pool_radius
            theta = np.arctan2(dy, dx)
            
            canvas_x = int(canvas_width/2 + canvas_width/2 * rho * np.cos(theta))
            canvas_y = int(canvas_height/2 + canvas_height/2 * rho * np.sin(theta))
            
        elif self.pool_shape == "rectangle" and self.pool_rect is not None:
            # 矩形處理邏輯
            rect_x, rect_y, rect_w, rect_h = self.pool_rect
            
            # 計算輸入點在矩形內的相對位置 (0~1)
            rel_x = max(0, min(1, (img_x - rect_x) / rect_w))
            rel_y = max(0, min(1, (img_y - rect_y) / rect_h))

            # 直接映射到畫布座標
            canvas_x = int(rel_x * canvas_width)
            canvas_y = int(rel_y * canvas_height)
            
        return canvas_x, canvas_y
    
    def fit_rectangle_to_points(self, points):
        """使用標註點擬合矩形"""
        if len(points) <= 4:
            return None
        
        # 計算最小外接矩形
        rect = cv2.minAreaRect(points)
        box = cv2.boxPoints(rect)
        box = np.int32(box)
        
        # 獲取矩形的中心、寬度、高度和角度
        center, (width, height), angle = rect
        
        return {
            'center': center,
            'width': width,
            'height': height,
            'angle': angle,
            'box': box
        }
    
    def setup_perspective_transform_with_client_points(self, frame, client_points):
        """使用Client傳送的標註點設置透視變換矩陣"""
        print("使用Client傳送的標註點建立透視變換...")
        
        if len(client_points) != 4:
            print(f"錯誤: 需要4個點，但收到 {len(client_points)} 個點")
            return False
        
        # 取得影像的寬、高
        frame_height, frame_width = frame.shape[:2]
        
        # 顯示原始畫面與標註點
        display_frame = frame.copy()
        
        # 將標註點轉換為numpy數組
        points = np.array(client_points, dtype=np.float32)
        
        if self.pool_shape == "circle":
            # 原有的圓形處理邏輯
            center, radius = self.fit_circle_to_points(points)
            if center is None or radius is None:
                print("錯誤: 無法從標註點擬合圓")
                return False
            
            # 確保圓完全在影像內
            max_radius = min(
                center[0],                    # 距離左邊界
                center[1],                    # 距離上邊界
                frame_width - center[0],      # 距離右邊界
                frame_height - center[1]      # 距離下邊界
            )
            print(f"最大半徑:{max_radius}")
            
            if radius > max_radius:
                print(f"警告: 檢測到的半徑 ({radius}) 超出了最大可能半徑 ({max_radius})")
                print("無法進行透視變換，因為圓形無法完整包含水池區域")
                return False
            horizon_offset = 50
            # 計算圓的最小外接矩形的四個頂點
            rect_points = np.array([
                [center[0] - radius-horizon_offset, center[1] - radius],  # 左上
                [center[0] + radius+horizon_offset, center[1] - radius],  # 右上
                [center[0] + radius+horizon_offset, center[1] + radius],  # 右下
                [center[0] - radius-horizon_offset, center[1] + radius]   # 左下
            ], dtype=np.float32)

            # 在畫面上標記擬合的圓
            cv2.circle(display_frame, (int(center[0]), int(center[1])), int(radius), (0, 255, 0), 2)
            
            # 在畫面上標記矩形頂點
            for i, point in enumerate(rect_points):
                cv2.circle(display_frame, tuple(point.astype(int)), 5, (0, 0, 255), -1)
                cv2.putText(display_frame, f"P{i}", 
                        (int(point[0]) + 10, int(point[1]) + 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # 在畫面上標記矩形
            cv2.polylines(display_frame, [rect_points.astype(int)], True, (0, 255, 0), 2)
            
            # 設定目標點 (正方形輸出)
            target_size = min(frame_height, frame_width)
            target_points = np.array([
                [0, 0],                # 左上
                [target_size, 0],      # 右上
                [target_size, target_size], # 右下
                [0, target_size]       # 左下
            ], dtype=np.float32)
            
            # 計算透視變換矩陣
            self.transform_matrix = cv2.getPerspectiveTransform(rect_points, target_points)
            self.target_size = target_size
            
            # 設置初始水池參數
            self.pool_center = (target_size // 2, target_size // 2)
            self.pool_radius = target_size // 2
            
            print("計算完成的透視變換矩陣:")
            print(self.transform_matrix)

            return True # 代表圓形水池透視變換成功
            
        elif self.pool_shape == "rectangle":
            print("處理矩形水池透視變換...")
        
            # ===== 排序點的順序 =====
            # 確保點的順序為：左上、右上、右下、左下 [確保使用者隨意點選也能夠依照排序得到參考點]
            sorted_points = self.sort_rectangle_points(points)
            
            # 繪製標註點和順序
            for i, pt in enumerate(sorted_points):
                cv2.circle(display_frame, tuple(pt.astype(int)), 8, (0, 255, 0), -1)
                cv2.putText(display_frame, f"P{i+1}", tuple(pt.astype(int)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            
            # 繪製矩形邊界
            cv2.polylines(display_frame, [sorted_points.astype(np.int32)], 
                        True, (0, 255, 0), 2)
            
            # 計算矩形的寬度和高度（在原始圖像中）
            width_top = np.linalg.norm(sorted_points[1] - sorted_points[0])
            width_bottom = np.linalg.norm(sorted_points[2] - sorted_points[3])
            height_left = np.linalg.norm(sorted_points[3] - sorted_points[0])
            height_right = np.linalg.norm(sorted_points[2] - sorted_points[1])

            # 計算資訊打印
            print(f"\n邊長測量：")
            print(f"上邊: {width_top:.1f} px")
            print(f"下邊: {width_bottom:.1f} px")
            print(f"左邊: {height_left:.1f} px")
            print(f"右邊: {height_right:.1f} px")

            # === 計算輸出尺寸[保持與原始標註點範圍面積相同] ===
            def calc_area(points):
                x = points[:, 0]
                y = points[:, 1]
                return 0.5 * abs(
                    x[0]*y[1] + x[1]*y[2] + x[2]*y[3] + x[3]*y[0] -
                    x[1]*y[0] - x[2]*y[1] - x[3]*y[2] - x[0]*y[3]
                )
            
            area = calc_area(sorted_points)
            avg_width = (width_top + width_bottom) / 2
            avg_height = (height_left + height_right) / 2
            
            # 計算寬高比
            aspect_ratio = avg_width / avg_height

            # 計算透視變換後的圖片輸出寬、高
            output_height = int(np.sqrt(area / aspect_ratio)) # 透視變換後輸出的圖片寬度
            output_width = int(output_height * aspect_ratio) # 透視變換後輸出的圖片高度

            # 計算結果打印
            print(f"\n矩形水池透視變換輸出尺寸計算：")
            print(f"方法: 保持面積 ({area:.0f} pixel 平方)")
            print(f"輸出尺寸: {output_width} × {output_height} px")
            print(f"輸出面積: {output_width * output_height:,} pixel 平方")

            # 確保透視變換後的圖片大小合理[限制寬度&高度最大值為2048] -> 進階影響最終FlowMap的畫布大小
            max_dimension = 1024
            if output_width > max_dimension or output_height > max_dimension:
                scale = max_dimension / max(output_width, output_height)
                output_width = int(output_width * scale)
                output_height = int(output_height * scale)
                print(f"輸出尺寸過大，已縮小至: {output_width} × {output_height} px")

            # 設置透視變換目標點(針對矩形水池)
            target_points = np.array([
                [0, 0],                          # 左上
                [output_width, 0],               # 右上
                [output_width, output_height],   # 右下
                [0, output_height]               # 左下
            ], dtype=np.float32)

            # 計算透視變換矩陣
            self.transform_matrix = cv2.getPerspectiveTransform(sorted_points, target_points)

            # 保存矩形水池透視變換後的輸出圖片尺寸
            self.output_width = output_width # 寬
            self.output_height = output_height # 高
            self.target_size = max(output_width, output_height)
            
            # 儲存矩形水池參數
            self.pool_rect = (0, 0, output_width, output_height)
            self.pool_center = (output_width // 2, output_height // 2)
            
            print("透視變換矩陣計算完成:")
            print(self.transform_matrix)
            print(f"矩形水池參數: {self.pool_rect}")
             
            return True # 代表矩形水池透視變換成功
        
        return False # 不屬於圓形水池/矩形水池
    
    def sort_rectangle_points(self, points):
        """
        [透視矩陣參考點排序]
        將四個點排序為：左上、右上、右下、左下
        """
        # 計算質心
        center = np.mean(points, axis=0)
        
        # 根據相對於質心的角度排序
        def angle_from_center(point):
            return np.arctan2(point[1] - center[1], point[0] - center[0])
        
        # 按角度排序（從左上開始，逆時針）
        sorted_points = sorted(points, key=angle_from_center)
        sorted_points = np.array(sorted_points, dtype=np.float32)
        
        # 找到最左上的點作為起點
        # 計算每個點到 (0, 0) 的距離
        distances = np.sum(sorted_points**2, axis=1)
        top_left_idx = np.argmin(distances)
        
        # 重新排列，使左上角點在第一位
        sorted_points = np.roll(sorted_points, -top_left_idx, axis=0)
        
        # 驗證順序：確保是逆時針順序
        # 外積計算來判斷方向
        v1 = sorted_points[1] - sorted_points[0]
        v2 = sorted_points[2] - sorted_points[1]
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        
        # 如果是順時針，反轉順序（除了第一個點）
        if cross < 0:
            sorted_points = np.array([
                sorted_points[0],
                sorted_points[3],
                sorted_points[2],
                sorted_points[1]
            ])
        
        print("排序後的點順序:")
        for i, pt in enumerate(sorted_points):
            print(f"  P{i+1} (左上右上右下左下): ({pt[0]:.1f}, {pt[1]:.1f})")
        
        return sorted_points

    def fit_circle_to_points(self, points):
        """使用最小二乘法擬合圓"""
        if len(points) < 3:
            return None, None
        
        x = points[:, 0]
        y = points[:, 1]
        
        # 計算平均值
        x_m = np.mean(x)
        y_m = np.mean(y)
        
        # 計算中心偏移的值
        u = x - x_m
        v = y - y_m
        
        # 計算輔助變數
        Suv  = np.sum(u * v)
        Suu  = np.sum(u * u)
        Svv  = np.sum(v * v)
        Suuv = np.sum(u * u * v)
        Suvv = np.sum(u * v * v)
        Suuu = np.sum(u * u * u)
        Svvv = np.sum(v * v * v)
        
        # 解方程組
        A = np.array([
            [Suu, Suv],
            [Suv, Svv]
        ])
        
        b = np.array([
            [0.5 * (Suuu + Suvv)],
            [0.5 * (Svvv + Suuv)]
        ])
        
        try:
            uc, vc = np.linalg.solve(A, b)
            uc = float(uc)
            vc = float(vc)
        except np.linalg.LinAlgError:
            # 如果無法求解，使用簡單的平均值
            return (x_m, y_m), np.mean(np.sqrt((x - x_m)**2 + (y - y_m)**2))
        
        # 計算圓心和半徑
        xc = x_m + uc
        yc = y_m + vc
        
        # 計算半徑
        r = np.sqrt(uc*uc + vc*vc + (Suu + Svv) / len(x))
        
        return (xc, yc), r
    
    def calibrate_pool_with_water_jets(self, water_jet_vectors):
        """使用射水向量的起點來校準水池參數"""
        print("使用射水向量起點校準水池參數...")
        
        if not water_jet_vectors or len(water_jet_vectors) < 6:
            print(f"錯誤: 需要6個射水向量，但收到 {len(water_jet_vectors)} 個")
            return False
        
        # 提取所有射水向量的起點
        start_points = []
        for vector in water_jet_vectors:
            start_x, start_y, _, _ = vector
            start_points.append((start_x, start_y))
        
        # 將起點轉換為numpy數組
        points = np.array(start_points, dtype=np.float32)
        
        if self.pool_shape == "circle":
            # 原有的圓形處理邏輯
            center, radius = self.fit_circle_to_points(points)
            if center is not None and radius is not None:
                self.pool_center = tuple(map(int, center))
                self.pool_radius = int(radius)
                
                # 確保圓完全在影像內
                max_radius = min(
                    self.pool_center[0],                    # 距離左邊界
                    self.pool_center[1],                    # 距離上邊界
                    self.target_size - self.pool_center[0], # 距離右邊界
                    self.target_size - self.pool_center[1]  # 距離下邊界
                )
                
                # 如果檢測到的半徑超出了最大可能半徑，則使用最大可能半徑
                if self.pool_radius > max_radius:
                    print(f"警告: 檢測到的半徑 ({self.pool_radius}) 超出了最大可能半徑 ({max_radius})")
                    self.pool_radius = int(max_radius * 0.95)  # 留一點邊距
                
                print("射水向量起點校準完成!")
                print(f"水池圓心: {self.pool_center}, 半徑: {self.pool_radius}")
                return True
            else:
                print("射水向量起點校準失敗，未能擬合圓")
                # 使用預設值
                self.pool_center = (self.target_size // 2, self.target_size // 2)
                self.pool_radius = self.target_size // 2
                print(f"使用預設值 - 水池圓心: {self.pool_center}, 半徑: {self.pool_radius}")
                return False
            
        elif self.pool_shape == "rectangle":
            # 矩形處理邏輯
            rect_info = self.fit_rectangle_to_points(points)
            print(f"矩形參數:{rect_info}")
            if rect_info is not None:
                # 更新矩形參數
                center = rect_info['center']
                width = rect_info['width']
                height = rect_info['height']
                
                # 獲取透視變換後的圖像尺寸
                if self.transform_matrix is not None and self.output_width is not None and self.output_height is not None:
                    # 使用透視變換後的圖像尺寸來判斷矩形方向
                    warped_aspect_ratio = self.output_width / self.output_height
                    print(f"透視變換後圖像寬高比: {warped_aspect_ratio:.2f} (寬={self.output_width}, 高={self.output_height})")
                    
                    if warped_aspect_ratio > 1:
                        # 透視變換後的圖像是橫向的
                        rect_width = self.target_size
                        rect_height = int(self.target_size / warped_aspect_ratio)
                        rect_x = 0
                        rect_y = (self.target_size - rect_height) // 2
                        print("根據透視變換後的圖像判斷: 寬大於高(橫矩形)")
                    else:
                        # 透視變換後的圖像是縱向的
                        rect_height = self.target_size
                        rect_width = int(self.target_size * warped_aspect_ratio)
                        rect_x = (self.target_size - rect_width) // 2
                        rect_y = 0
                        print("根據透視變換後的圖像判斷: 高大於寬(縱矩形)")
                else:
                    # 如果沒有透視變換資訊，則使用標註點擬合的矩形尺寸
                    aspect_ratio = width / height
                    print(f"擬合矩形寬高比: {aspect_ratio:.2f} (寬={width:.1f}, 高={height:.1f})")
                    
                    if aspect_ratio > 1:
                        rect_width = self.target_size
                        rect_height = int(self.target_size / aspect_ratio)
                        rect_x = 0
                        rect_y = (self.target_size - rect_height) // 2
                        print("根據擬合矩形判斷: 寬大於高(橫矩形)")
                    else:
                        rect_height = self.target_size
                        rect_width = int(self.target_size * aspect_ratio)
                        rect_x = (self.target_size - rect_width) // 2
                        rect_y = 0
                        print("根據擬合矩形判斷: 高大於寬(縱矩形)")
                
                self.pool_rect = (rect_x, rect_y, rect_width, rect_height)
                self.pool_center = (int(center[0]), int(center[1]))
                
                print("射水向量起點校準完成!")
                print(f"矩形水池: 中心={self.pool_center}, 矩形={self.pool_rect}")
                return True
            else:
                print("射水向量起點校準失敗，使用預設值")
                return False
        
        return True
        
class FlowMapGenerator:
    """FlowMap 生成器類"""
    
    def __init__(self, canvas_width=1024, canvas_height=None, sample_frames=30):
        """初始化 FlowMap 生成器"""
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height if canvas_height is not None else canvas_width
        self.sample_frames = sample_frames
        
        self.background_color = (0,128,128) # 背景色
        self.reset_flow_map()  # 使用方法來初始化和重置
        self.marker_history = {}  # 記錄每個 marker 的歷史位置
        self.current_frame = 0
        self.last_saved_frame = 0  # 追蹤上次儲存的幀號

        # ** 速度追蹤 **
        self.velocity_history = []  # 用於記錄所有 marker 的速度歷史資料
        self.max_velocity = 0.5     # 初始最大速度
        self.velocity_window = 30   # 速度窗口大小
        self.velocity_percent = 95  # 使用第95百分位數作為最大速度

        #筆刷半徑大小設定(圓形筆刷)
        self.brush_radius = 20

        # 平滑過度處理
        self.decay_factor = 0.95
        # 初始化累積用的FlowMap
        self.accumulated_flowmap = np.zeros((self.canvas_height, self.canvas_width, 3), dtype=np.uint8)
        self.accumulated_flowmap[:, :] = self.background_color
        
    def reset_flow_map(self):
        """重置 FlowMap 為初始狀態"""
        self.flow_map = np.ones((self.canvas_height, self.canvas_width, 3), dtype=np.uint8)
        self.flow_map[:, :] = self.background_color
    
    def add_marker_data(self, marker_id, position, velocity):
        """
        添加 marker 數據到歷史記錄
        
        參數:
        marker_id: marker ID
        position: [x, y] 位置，歸一化到 -1 到 1 的範圍
        velocity: [vx, vy] 速度向量
        """
        if marker_id not in self.marker_history:
            self.marker_history[marker_id] = []
        
        # 添加當前數據到歷史記錄
        self.marker_history[marker_id].append({
            'position': position,
            'velocity': velocity,
            'frame': self.current_frame
        })

        # 只保留最近 sample_frames 幀的數據
        if len(self.marker_history[marker_id]) > self.sample_frames:
            self.marker_history[marker_id].pop(0)
        
        # ** 紀錄速度大小至Globa1 歷史資料中
        velocity_magnitude = np.linalg.norm(velocity)
        self.velocity_history.append(velocity_magnitude)

        # 只保留最近 velocity_window 個速度記錄
        if len(self.velocity_history) > self.velocity_window:
            self.velocity_history.pop(0)

        # **更新最大速度(使用百分位數)
        if len(self.velocity_history) > 10:
            self.max_velocity = np.percentile(self.velocity_history, self.velocity_percent)

    def update_flow_map(self):
        """根據所有 marker 的平均速度更新 FlowMap"""
        # 增加當前幀計數
        self.current_frame += 1
        
        # 如果沒有足夠的歷史數據，則不更新
        if self.current_frame < self.sample_frames:
            return
        
        background = np.ones_like(self.flow_map, dtype=np.uint8)
        background[:, :] = self.background_color

        self.flow_map = cv2.addWeighted(
            self.flow_map, self.decay_factor,
            background, 1 - self.decay_factor,
            0
        )
        
        for marker_id, history in self.marker_history.items():
            if len(history) < 2 :  # 至少要有兩個點的位置資訊，才能繪製ArUco Marker的移動軌跡
                continue

            # 獲取最近 sample_frames 幀的歷史數據
            recent_history = history[-self.sample_frames:]

            # 計算平均速度
            velocities = np.array([data['velocity'] for data in recent_history])
            avg_velocity = np.mean(velocities, axis=0)
            avg_speed = np.linalg.norm(avg_velocity)

            # 只有當平均速度大於閾值時才繪製
            if avg_speed < 0.01:
                continue
            
            # 計算速度因子 (用於顏色更改)
            velocity_factor = min(avg_speed / self.max_velocity, self.max_velocity)

            # 計算軌跡顏色 (根據速度方向)
            if np.linalg.norm(avg_velocity) > 0:
                direction = avg_velocity / np.linalg.norm(avg_velocity)
            else:
                direction = np.array([0, 0])
            
            # 計算顏色強度 (根據速度大小)
            # 速度越大，顏色越深；速度越小，顏色越接近背景色
            intensity = 0.1 + 0.9 * velocity_factor  # 0.1~1.0 範圍，保留一些基本可見度
            
            # 計算 R 和 G 值 (根據方向)
            r_base = int(75 + 125 * (direction[0] + 1) / 2)  # 基本 R 值
            g_base = int(75 + 125 * ((-direction[1]) + 1) / 2)  # 基本 G 值
            
            # 根據速度調整顏色強度
            r_value = int(self.background_color[2] * (1 - intensity) + r_base * intensity)
            g_value = int(self.background_color[1] * (1 - intensity) + g_base * intensity)
            b_value = int(self.background_color[0] * (1 - intensity))

            color = (b_value,g_value,r_value)

            # 繪製軌跡(使用固定筆刷大小)
            for i in range(1,len(recent_history)):
                # 獲取前一個點和當前點
                prev_pos = recent_history[i-1]['position']
                curr_pos = recent_history[i]['position']
                
                # 將位置從 -1 到 1 映射到 0 到 canvas_width/height-1
                prev_x = int((prev_pos[0] + 1) / 2 * (self.canvas_width - 1))
                prev_y = int((prev_pos[1] + 1) / 2 * (self.canvas_height - 1))
                curr_x = int((curr_pos[0] + 1) / 2 * (self.canvas_width - 1))
                curr_y = int((curr_pos[1] + 1) / 2 * (self.canvas_height - 1))
                
                # 確保座標在有效範圍內
                prev_x = max(0, min(self.canvas_width - 1, prev_x))
                prev_y = max(0, min(self.canvas_height - 1, prev_y))
                curr_x = max(0, min(self.canvas_width - 1, curr_x))
                curr_y = max(0, min(self.canvas_height - 1, curr_y))
                
                # 計算兩點之間的距離
                dist = np.sqrt((curr_x - prev_x)**2 + (curr_y - prev_y)**2)
                
                # 如果距離太大，直接繪製兩個點
                if dist > 50:
                    cv2.circle(self.flow_map, (prev_x, prev_y), self.brush_radius, color, -1)
                    cv2.circle(self.flow_map, (curr_x, curr_y), self.brush_radius, color, -1)
                else:
                    # 在兩點之間插值多個點，使軌跡平滑
                    num_points = max(2, int(dist / 2))  # 每2個像素插一個點
                    for j in range(num_points + 1):
                        alpha = j / num_points
                        x = int(prev_x + alpha * (curr_x - prev_x))
                        y = int(prev_y + alpha * (curr_y - prev_y))
                        cv2.circle(self.flow_map, (x, y), self.brush_radius, color, -1)

        # 應用高斯模糊使 FlowMap 更平滑
        temp = self.flow_map.copy()
        for _ in range(3):
            temp = cv2.GaussianBlur(temp, (31,31), 0)
        self.flow_map = temp

        self.accumulated_flowmap = cv2.addWeighted(self.accumulated_flowmap,0.5,self.flow_map,0.5,0) # 將過去累積的FlowMap結果與當前FlowMap結合
        self.accumulated_flowmap = np.clip(self.accumulated_flowmap, 0, 255)  # 確保不超過 255

    def get_flow_map(self):
        """獲取當前的 FlowMap"""
        return self.flow_map
    
    def should_save_and_reset(self, save_interval=30 ,image_server=None):
        """檢查是否應該傳送FlowMap"""
        if self.current_frame - self.last_saved_frame >= save_interval:
            self.last_saved_frame = self.current_frame

            #將FlowMap轉換為png格式的bytes
            _,img_encoded = cv2.imencode('.jpg',self.accumulated_flowmap)
            img_bytes = img_encoded.tobytes()

            #透過Server即時的將最終生成的FlowMap傳送給連接的Client [FlowMap傳遞]
            if image_server:
                image_server.send_flowmap(img_bytes)
                # print(f"已傳送最終生成完成FlowMap給Client於Frame{self.current_frame}")
            return True
        return False
    
class WaterJet:
    """射水模擬類"""
    
    def __init__(self, pool_detector, flow_map_generator):
        """初始化射水模擬"""
        self.pool_detector = pool_detector
        self.flow_map_generator = flow_map_generator
        self.water_jet_vectors = []  # 存儲射水向量 [(start_x, start_y, end_x, end_y), ...]
        self.jet_length_pixels = 100  # 射水長度（像素）
        
    def update_water_jet_vectors(self, vectors):
        """更新射水向量
        vectors: [(start_x, start_y, end_x, end_y), ...]
        """
        self.water_jet_vectors = vectors
        print(f"已更新射水向量: {len(self.water_jet_vectors)} 個")
    
    def apply_water_jets(self, frame):
        """在畫面上應用射水效果並更新FlowMap"""
        if not self.water_jet_vectors:
            return frame  # 如果沒有射水向量，直接返回原始幀
        
        output_frame = frame.copy()

        canvas_width = self.flow_map_generator.canvas_width
        canvas_height = self.flow_map_generator.canvas_height

        if self.pool_detector.pool_shape == "rectangle":
            # 獲取原始透視變換後的圖片尺寸
            orig_width = self.pool_detector.output_width
            orig_height = self.pool_detector.output_height
        
        for start_x, start_y, end_x, end_y in self.water_jet_vectors:
            # 計算射水方向向量
            jet_dx = end_x - start_x
            jet_dy = end_y - start_y
            
            # 向量長度
            jet_length = np.sqrt(jet_dx**2 + jet_dy**2)
            
            if jet_length > 0:
                # 歸一化方向向量
                jet_dx /= jet_length
                jet_dy /= jet_length
                
                if self.pool_detector.pool_shape == "circle":
                    # 將畫面座標轉換為FlowMap座標[原始圓形水池處理邏輯]
                    start_canvas_x, start_canvas_y = self.pool_detector.image_to_canvas_coords(
                        start_x, start_y, canvas_width, canvas_height)
                    
                if self.pool_detector.pool_shape == "rectangle":
                    # 將畫面座標轉換為FlowMap座標
                    # 確保起點座標在原始透視變換後的圖片範圍內
                    start_x_norm = min(max(0, start_x), orig_width - 1) / orig_width
                    start_y_norm = min(max(0, start_y), orig_height - 1) / orig_height
                    
                    # 將歸一化座標映射到FlowMap畫布
                    start_canvas_x = int(start_x_norm * canvas_width)
                    start_canvas_y = int(start_y_norm * canvas_height)
                
                # 繪製射水效果
                for i in range(1, self.jet_length_pixels + 1):
                    # 計算當前點的位置
                    t = i / self.jet_length_pixels
                    x = int(start_canvas_x + jet_dx * canvas_width * t * 0.4)  # 縮放因子0.4使射水不會太長
                    y = int(start_canvas_y + jet_dy * canvas_height * t * 0.4)
                    
                    # 確保座標在有效範圍內
                    x = max(0, min(canvas_width - 1, x))
                    y = max(0, min(canvas_height - 1, y))
                    
                    # 添加射水顏色隨距離逐漸淡化
                    max_intensity = 1.0  # 最大射水強度
                    min_intensity = 0.1  # 最小射水強度
                    
                    intensity = max_intensity - (max_intensity - min_intensity) * t  # 射水強度考慮距離來逐漸衰減
                    
                    # 計算 R 和 G 值 (根據方向)
                    direction = [jet_dx, jet_dy]
                    r_base = int(75 + 125 * (direction[0] + 1) / 2)
                    g_base = int(75 + 125 * ((-direction[1]) + 1) / 2)
                    
                    # 根據速度調整顏色強度
                    bg_color = self.flow_map_generator.background_color
                    r_value = int(bg_color[2] * (1 - intensity) + r_base * intensity)
                    g_value = int(bg_color[1] * (1 - intensity) + g_base * intensity)
                    b_value = int(bg_color[0] * (1 - intensity))
                    
                    color = (b_value, g_value, r_value)
                    
                    # 在 FlowMap 上繪製點
                    brush_radius = self.flow_map_generator.brush_radius
                    cv2.circle(self.flow_map_generator.flow_map, (x, y), brush_radius, color, -1)
                    
                    # 同時更新累積的FlowMap
                    cv2.circle(self.flow_map_generator.accumulated_flowmap, (x, y), brush_radius, color, -1)
        
        return output_frame

class ArUcoTracker:
    """ArUco Marker 追蹤"""
    
    def __init__(self, pool_detector):
        """初始化 ArUco 追蹤器"""
        self.pool_detector = pool_detector
        self.marker_trackers = {}  # 儲存所有標記的卡爾曼濾波器
        self.last_seen = {}        # 儲存最後一次看到的標記信息
        # 根據水池形狀決定畫布尺寸
        if pool_detector.pool_shape == "rectangle" and pool_detector.pool_rect is not None:
            rect_x, rect_y, rect_w, rect_h = pool_detector.pool_rect
            
            # 使用與水池相同的寬高比例，但最大尺寸限制為1024
            max_dim = 1024
            if rect_w >= rect_h:
                # 寬度大於或等於高度
                print("編輯的水池範圍寬度大於高度")
                canvas_width = max_dim
                canvas_height = int(max_dim * rect_h / rect_w)
            else:
                # 高度大於寬度
                print("編輯的水池範圍高度大於寬度")
                canvas_height = max_dim
                canvas_width = int(max_dim * rect_w / rect_h)
                
            self.flow_map_generator = FlowMapGenerator(
                canvas_width=canvas_width, 
                canvas_height=canvas_height, 
                sample_frames=30
            )
            print(f"創建矩形FlowMap畫布: {canvas_width}x{canvas_height}")
        else:
            # 圓形水池使用正方形畫布
            self.flow_map_generator = FlowMapGenerator(
                canvas_width=1024, 
                canvas_height=1024, 
                sample_frames=30
            )
        self.water_jet = WaterJet(pool_detector, self.flow_map_generator)  # 射水模擬class
        self.running = True  # 控制追蹤執行緒的標誌
    
    def world_to_image(self, X, Y):
        """將世界座標轉換為影像座標"""
        if self.pool_detector.pool_shape == "circle":
            # 從世界座標轉回極座標
            rho = np.sqrt(X**2 + Y**2) / self.pool_detector.world_radius
            theta = np.arctan2(Y, X)
            
            # 從極座標轉回畫面座標
            u = int(self.pool_detector.pool_center[0] + 
                self.pool_detector.pool_radius * rho * np.cos(theta))
            v = int(self.pool_detector.pool_center[1] + 
                self.pool_detector.pool_radius * rho * np.sin(theta))
            
        elif self.pool_detector.pool_shape == "rectangle" and self.pool_detector.pool_rect is not None:
            # 矩形水池處理邏輯
            rect_x, rect_y, rect_w, rect_h = self.pool_detector.pool_rect
            
            # 將世界座標 (-world_radius ~ world_radius) 映射到矩形水池座標 (0 ~ rect_w/rect_h)
            norm_x = (X / self.pool_detector.world_radius + 1) / 2
            norm_y = (Y / self.pool_detector.world_radius + 1) / 2
            
            u = int(rect_x + norm_x * rect_w)
            v = int(rect_y + norm_y * rect_h)
            
        else:
            # 參數未正確初始化，使用預設值
            print(f"警告: 水池參數未正確初始化 (形狀: {self.pool_detector.pool_shape})")
            u, v = 0, 0
        return u, v
    
    def update_water_jet_vectors(self, vectors):
        """更新射水向量"""
        self.water_jet.update_water_jet_vectors(vectors)
        print("已更新射水向量")
        
    def process_frame(self, frame):
        """處理一幀並追蹤 ArUco 標記"""
        # 先在原始影像中檢測 ArUco Marker
        gray_original = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners_original, ids_original, _ = cv2.aruco.detectMarkers(
            gray_original, self.pool_detector.aruco_dict, 
            parameters=self.pool_detector.aruco_params
        )

        # 應用透視變換[依照圓形/矩形水池決定最終透視變換後的圖片大小]
        if self.pool_detector.pool_shape == "rectangle" and self.pool_detector.output_width is not None and self.pool_detector.output_height is not None:
            # 矩形水池使用指定的寬高
            warped_frame = cv2.warpPerspective(
                frame, 
                self.pool_detector.transform_matrix, 
                (self.pool_detector.output_width, self.pool_detector.output_height),
                flags=cv2.INTER_NEAREST,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0)
            )
        else:
            # 圓形水池使用正方形輸出
            warped_frame = cv2.warpPerspective(
                frame, 
                self.pool_detector.transform_matrix, 
                (self.pool_detector.target_size, self.pool_detector.target_size),
                flags=cv2.INTER_NEAREST,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0)
            )
        
        # 在變換後的影像中檢測 ArUco Marker
        gray_warped = cv2.cvtColor(warped_frame, cv2.COLOR_BGR2GRAY)
        corners_warped, ids_warped, _ = cv2.aruco.detectMarkers(
            gray_warped, self.pool_detector.aruco_dict, 
            parameters=self.pool_detector.aruco_params
        )
        
        # 合併兩次檢測結果
        corners = []
        ids_list = []

        # 處理變換後影像中的檢測結果
        if ids_warped is not None:
            for i, marker_id in enumerate(ids_warped.flatten()):
                corners.append(corners_warped[i])
                ids_list.append([marker_id])

        # 處理原始影像中的檢測結果
        if ids_original is not None:
            for i, marker_id in enumerate(ids_original.flatten()):
                # 檢查這個 marker 是否已經在變換後的影像中檢測到
                if ids_list and marker_id in np.array(ids_list).flatten():
                    continue

                # 將原始影像中的角點轉換到變換後的座標系統
                marker_corners = corners_original[i][0]
                transformed_corners = []

                for corner in marker_corners:
                    # 應用透視變換到每個角點
                    corner_homogeneous = np.array([corner[0], corner[1], 1])
                    transformed = np.dot(self.pool_detector.transform_matrix, corner_homogeneous)
                    transformed = transformed / transformed[2]  # 歸一化
                    transformed_corners.append([transformed[0], transformed[1]])

                # 將轉換後的角點添加到結果中
                corners.append(np.array([transformed_corners], dtype=np.float32))
                ids_list.append([marker_id])

        # 標記水池圓心和邊界
        output_frame = warped_frame.copy()
      
        # 追蹤到的標記ID集合
        detected_markers = set()
        
        # **處理檢測到的 Marker**
        if corners and ids_list:
            # 將 ids_list 轉換為 numpy 數組
            ids = np.array(ids_list)
            # 在變換後的畫面上標記檢測到的 Marker
            cv2.aruco.drawDetectedMarkers(output_frame, corners, ids)
            
            for i, marker_id in enumerate(ids.flatten()):
                    # 計算 Marker 中心座標
                    marker_corner = corners[i][0]
                    u = int(np.mean(marker_corner[:, 0]))
                    v = int(np.mean(marker_corner[:, 1]))
                    
                    # 轉換為世界座標 (極座標轉換)
                    if self.pool_detector.pool_shape == "circle" and self.pool_detector.pool_radius is not None:
                        u_c, v_c = self.pool_detector.pool_center
                        dx, dy = u - u_c, v - v_c
                        
                        rho = np.sqrt(dx**2 + dy**2) / self.pool_detector.pool_radius
                        theta = np.arctan2(dy, dx)
                        X = float(rho * self.pool_detector.world_radius * np.cos(theta))
                        Y = float(rho * self.pool_detector.world_radius * np.sin(theta))
                    
                    elif self.pool_detector.pool_shape == "rectangle" and self.pool_detector.pool_rect is not None:
                        # 矩形水池處理邏輯
                        rect_x, rect_y, rect_w, rect_h = self.pool_detector.pool_rect
                        
                        # 計算在矩形內的相對位置 (0~1)
                        rel_x = max(0, min(1, (u - rect_x) / rect_w))
                        rel_y = max(0, min(1, (v - rect_y) / rect_h))
                        
                        # 轉換為世界座標 (-world_radius ~ world_radius)
                        X = float((2 * rel_x - 1) * self.pool_detector.world_radius)
                        Y = float((2 * rel_y - 1) * self.pool_detector.world_radius)
                    else:
                        # 參數未正確初始化，使用預設值
                        print(f"警告: 水池參數未正確初始化 (形狀: {self.pool_detector.pool_shape})")
                        # 使用預設值
                        X, Y = 0.0, 0.0
                        continue  # 跳過此標記

                    if marker_id not in self.pool_detector.fixed_marker_ids:
                        '''處理浮動Marker'''
                        detected_markers.add(marker_id)
                        # 計算旋轉
                        p1 = marker_corner[1]  # 右上
                        p2 = marker_corner[2]  # 右下
                        direction_vector = p2 - p1
                        rotation_angle = np.arctan2(direction_vector[1], direction_vector[0])
                        rotation_angle_degrees = float(np.degrees(rotation_angle))
                        unity_rotation = -rotation_angle_degrees
                    
                        # 更新或創建卡爾曼濾波器
                        if marker_id in self.marker_trackers:
                            # 更新現有的追蹤器
                            state = self.marker_trackers[marker_id].update([X, Y], unity_rotation)
                        else:
                            # 創建新的追蹤器
                            self.marker_trackers[marker_id] = KalmanMarkerTracker(
                                marker_id, [X, Y], unity_rotation
                            )
                            state = self.marker_trackers[marker_id].get_state()
                    
                        # 使用卡爾曼濾波後的位置和旋轉
                        X_filtered, Y_filtered = state["position"]
                        vx, vy = state["velocity"]
                        unity_rotation_filtered = state["rotation"]
                        
                        # 更新最後一次看到的信息
                        marker_key = f"marker_id_{marker_id}"
                        self.last_seen[marker_key] = {
                            "timestamp": time.time(),
                            "position": [X_filtered, Y_filtered],
                            "rotation": unity_rotation_filtered,
                            "is_predicted": False
                        }
                        
                        # 在畫面上標記浮動 Marker
                        cv2.circle(output_frame, (u, v), 5, (0, 0, 255), -1)
                        
                        # 將位置和速度轉換為 FlowMap 所需的歸一化格式 (-1 到 1)
                        norm_x = X_filtered / self.pool_detector.world_radius
                        norm_y = Y_filtered / self.pool_detector.world_radius
                        norm_vx = vx 
                        norm_vy = vy 
                        
                        # 添加到 FlowMap 生成器
                        self.flow_map_generator.add_marker_data(
                            marker_id, [norm_x, norm_y], [norm_vx, norm_vy]
                        )
        
        # 處理未檢測到但仍在追蹤的標記
        for marker_id, tracker in list(self.marker_trackers.items()):
            if marker_id not in detected_markers:
                # 預測標記位置
                state = tracker.predict()
                
                # 檢查追蹤器是否仍然有效
                if not tracker.is_valid():
                    del self.marker_trackers[marker_id]
                    continue
                
                # 獲取預測的位置和旋轉
                X_pred, Y_pred = state["position"]
                vx, vy = state["velocity"]
                unity_rotation_pred = state["rotation"]
                missed_frames = state["missed_frames"]
                
                # 反向計算畫面上的位置
                u, v = self.world_to_image(X_pred, Y_pred)
                
                # 更新最後一次看到的訊息
                marker_key = f"marker_id_{marker_id}"
                self.last_seen[marker_key] = {
                    "timestamp": time.time(),
                    "position": [X_pred, Y_pred],
                    "rotation": unity_rotation_pred,
                    "is_predicted": True,
                    "missed_frames": missed_frames
                }
                
                # 在畫面上標記預測的 Marker 位置(使用相同顏色)
                cv2.circle(output_frame, (u, v), 5, (0, 0, 255), -1)
                
                # 將位置和速度轉換為 FlowMap 所需的歸一化格式 (-1 到 1)
                norm_x = X_pred / self.pool_detector.world_radius
                norm_y = Y_pred / self.pool_detector.world_radius
                norm_vx = vx 
                norm_vy = vy 
                
                # 添加到 FlowMap 生成器
                self.flow_map_generator.add_marker_data(
                    marker_id, [norm_x, norm_y], [norm_vx, norm_vy]
                )
        
        # 應用射水效果
        output_frame = self.water_jet.apply_water_jets(output_frame)

        # 更新 FlowMap
        self.flow_map_generator.update_flow_map()
        
        # 獲取當前的 FlowMap
        flow_map = self.flow_map_generator.get_flow_map()
        
        return output_frame, flow_map

def main():
    """主程式"""
    # 初始化 UI 介面
    app = QApplication(sys.argv) # 建立app物件，PyQt創建GUI應用程式必要實例
    ui = FlowMapUI()# 呼叫ArUcoFlowMap_UI_v2.py當中的FlowMapUI Class建立ui物件，自動執行建構子(初始化變數)
    
    # 初始化相機
    cap = cv2.VideoCapture(4)  # (原始值為0)
    
    # 檢查相機是否能夠成功開啟
    if not cap.isOpened():
        print("無法開啟攝像頭")
        return # 無法返回則退出

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) # 相機捕捉影像寬度
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) # 相機捕捉影像高度
    print(f"即時影像畫面大小: {frame_width}x{frame_height}") # 打印相機捕捉影像大小
    
    # 初始化Server
    # [ToDo:將FlowMap傳遞給VR端顯示]
    image_server = FlowMapServer(host='0.0.0.0', port=8888)

    image_server.start()  # 啟動Server
    print("TCP Server 已啟動，等待Client連線...")
    
    # 固定 Marker ID(在當前測試的水池串流影片中，在進行ArUco Marker追蹤時僅針對水面浮動Marker，將固定Marker排除)
    # 註: 事後實際應用若無擺放固定Marker後可移除
    fixed_marker_ids = [11, 12, 13, 14, 16, 17]
    
    # 初始化水池檢測器
    pool_detector = PoolDetector(fixed_marker_ids, world_radius=2.5,pool_shape="circle")
    
    # 儲存編輯後產生的射水向量
    water_jet_vectors = []
    
    # [UI介面訊號傳遞控制相關方法]

    # [水池形狀選擇]連接水池形狀選擇訊號
    # 使用者在UI介面中選擇水池形狀時調用update_pool_shape函式，更新PoolDetector Class的傳入參數pool_shape[circle/rectangle]
    def update_pool_shape(shape):
        # 更新水池形狀
        pool_detector.pool_shape = shape
        # 重置關鍵參數
        pool_detector.transform_matrix = None
        pool_detector.pool_center = None
        pool_detector.target_size = None
        # 根據形狀重置特定參數
        if shape == "circle":
            pool_detector.pool_radius = None
        else:  # rectangle
            pool_detector.pool_rect = None
            pool_detector.output_width = None
            pool_detector.output_height = None
        print(f"水池檢測器形狀已更新為: {shape}")

        # 清空射水向量
        water_jet_vectors.clear()
        
        # 如果有正在運行的追蹤器，停止它
        if hasattr(start_tracking_mode, 'current_tracker') and start_tracking_mode.current_tracker is not None:
            start_tracking_mode.current_tracker.running = False
        
        # 重置UI顯示[透視變換參考點編輯頁面&射水向量編輯頁面]
        ui.perspective_page.reset_ui_display()
        ui.water_jet_page.reset_ui_display()
    
    ui.pool_shape_signal.connect(update_pool_shape) # 水池形狀選擇介面的連接訊號

    # [透視變換參考點標註]
    # 點擊透視變換參考點編輯頁面中的"Apply Points"按鈕後觸發訊號
    # 調用setup_perspective_transform函式
    # 調用流程: 使用者於UI介面中編輯參考點 -> 點擊Apply Points按鈕 -> 觸發訊號 -> 傳入編輯的參考點(points) -> 執行setup_perspective_transform(執行透視變換)
    ui.perspective_page.annotation_points_signal.connect(
        lambda points: setup_perspective_transform(pool_detector, cap, points))
    
    # [射水向量編輯]
    # 點擊射水編輯頁面中的"Apply Water Jet Vector"按鈕後觸發訊號
    # 調用setup_water_jets函式(傳入編輯的射水向量(vectors))
    ui.water_jet_page.water_jet_vectors_signal.connect(
        lambda vectors: setup_water_jets(pool_detector, vectors, water_jet_vectors, ui, cap,image_server))
    
    # [射水向量編輯]
    # 點擊射水編輯頁面中的"Capture Image"按鈕後觸發訊號
    # 調用update_transformed_frame(用於更新透視變換後的Frame)
    ui.water_jet_page.request_transformed_frame_signal.connect(
        lambda: update_transformed_frame(ui, cap, pool_detector))
    
    # [編輯皆完成後開始Marker的追蹤並產生FlowMap]
    ui.start_tracking_signal.connect(
        lambda: start_tracking_mode(ui, cap, pool_detector, water_jet_vectors, image_server))
    
    # 創建定時器用於更新原始Frame
    frame_timer = QTimer()
    frame_timer.timeout.connect(lambda: update_original_frame(ui, cap))
    frame_timer.start(30)  # 每30ms更新一次
    
    # 顯示 UI
    ui.show()
    
    # 執行應用程序
    sys.exit(app.exec_())

def setup_perspective_transform(pool_detector, cap, points):
    """設置透視變換"""
    ret, frame = cap.read()
    if ret:
        if pool_detector.setup_perspective_transform_with_client_points(frame, points):
            print("已使用標註點設置透視變換")
            return True
    print("設置透視變換失敗")
    return False

def setup_water_jets(pool_detector, vectors, water_jet_vectors, ui=None, cap=None, image_server=None):
    """設置射水向量"""
    # 使用射水向量起點重新校準水池
    if pool_detector.calibrate_pool_with_water_jets(vectors):
        print("已使用射水向量校準水池參數")
        # 更新全局射水向量
        water_jet_vectors.clear()
        water_jet_vectors.extend(vectors)
        print(f"已更新全局射水向量: {len(water_jet_vectors)} 個")

        # 如果提供了UI和cap參數，則啟動追蹤
        if ui is not None and cap is not None:
            start_tracking_mode(ui, cap, pool_detector, water_jet_vectors, image_server)
        return True
    print("校準水池參數失敗")
    return False

def update_original_frame(ui, cap):
    """更新原始Frame到UI"""
    ret, frame = cap.read()
    if ret:
        ui.update_original_frame(frame)

def update_transformed_frame(ui, cap, pool_detector):
    """更新透視變換後的Frame到UI"""
    ret, frame = cap.read()
    # 應用透視變換[依照圓形/矩形水池決定最終透視變換後的圖片大小]
    if ret and pool_detector.transform_matrix is not None:
        if pool_detector.pool_shape == "rectangle" and pool_detector.output_width is not None and pool_detector.output_height is not None:
            # 矩形水池使用指定的寬高
            warped_frame = cv2.warpPerspective(
                frame, 
                pool_detector.transform_matrix, 
                (pool_detector.output_width, pool_detector.output_height)
            )
        else:
            # 圓形水池使用正方形輸出
            warped_frame = cv2.warpPerspective(
                frame, 
                pool_detector.transform_matrix, 
                (pool_detector.target_size, pool_detector.target_size)
            )
        ui.update_transformed_frame(warped_frame)
        print("已更新透視變換後的Frame")
    else:
        print("無法獲取Frame或透視變換矩陣未設置")

def start_tracking_mode(ui, cap, pool_detector, water_jet_vectors, image_server=None):
    """開始追蹤模式"""
    print("開始追蹤模式")
    

    # 檢查必要參數
    if pool_detector.transform_matrix is None:
        print("錯誤: 透視變換矩陣未設置，請先完成透視變換設置")
        return None
    
    if pool_detector.pool_shape == "circle" and pool_detector.pool_radius is None:
        print("錯誤: 圓形水池半徑未設置，請先完成水池校準")
        return None
    
    if pool_detector.pool_shape == "rectangle" and pool_detector.pool_rect is None:
        print("錯誤: 矩形水池邊界未設置，請先完成水池校準")
        return None
    
    # hasattr()函數:用於判斷對象是否包含對應的屬性
    # 語法: hasattr(object,name)
    # 檢查是否有正在運行的追蹤執行緒
    if hasattr(start_tracking_mode, 'current_tracker') and start_tracking_mode.current_tracker is not None:
        # 停止舊的追蹤執行緒
        start_tracking_mode.current_tracker.running = False
        # 等待舊執行緒結束
        import time
        time.sleep(0.1)
    
    # 初始化 ArUco 追蹤器
    tracker = ArUcoTracker(pool_detector)
    
    # 如果有射水向量，則更新到追蹤器
    if water_jet_vectors:
        tracker.update_water_jet_vectors(water_jet_vectors)
        print(f"已將 {len(water_jet_vectors)} 個射水向量應用到追蹤器")
    
    # 設置一個共享變數來控制執行緒
    tracker.running = True
    
    # 保存當前追蹤器的引用
    start_tracking_mode.current_tracker = tracker
    
    # 啟動一個新的執行緒來執行追蹤邏輯
    tracking_thread = threading.Thread(
        target=run_tracking,
        args=(ui, cap, tracker, image_server),
        daemon=True
    )
    tracking_thread.start()
    
    # 返回追蹤器，以便在需要時可以停止追蹤
    return tracker

def run_tracking(ui, cap, tracker, image_server=None):
    """
    [執行追蹤邏輯]
    在背景執行緒中運行的主追蹤迴圈
    主要作用:
    從相機(cap)持續讀取影像 -> 讓tracker(ArUcoTracker Class)處理影像(追蹤ArUco Marker) ->
    更新UI介面的Marker追蹤畫面&FlowMap -> 控制執行速度，並處理執行過程的錯誤 -> 結束時安全的停止tracker
    """
    try:
        # # 導入輸出FlowMap的輔助函數[測試用]
        # from flowmap_export import save_first_flowmap_and_tracking
        # # 添加標記，用於確保只保存第一張FlowMap
        # first_frame_saved = False

        save_interval = 30  # 每30幀檢查一次是否需要傳送FlowMap
        last_saved_frame = 0  # 上次傳送FlowMap的幀數

        while tracker.running:
            try:
                ret, frame = cap.read()
                if not ret:
                    print("無法讀取影像，嘗試重新獲取...")
                    time.sleep(0.1)  # 短暫暫停後重試
                    continue
                
                # 處理當前幀
                output_frame, flow_map = tracker.process_frame(frame)

                # 更新UI中的透視變換後幀
                ui.update_transformed_frame(output_frame)

                # 更新UI中的追蹤畫面和FlowMap
                ui.update_tracking_display(output_frame)
                ui.update_flowmap_display(flow_map)

                # 檢查是否需要傳送FlowMap給Client
                current_frame = tracker.flow_map_generator.current_frame
                if image_server and current_frame - last_saved_frame >= save_interval:
                    # 檢查Client是否請求傳送FlowMap
                    if image_server.should_stream_flowmap():
                        # 將FlowMap轉換為jpg格式的bytes
                        _, img_encoded = cv2.imencode('.jpg', tracker.flow_map_generator.accumulated_flowmap)
                        img_bytes = img_encoded.tobytes()
                        
                        # 透過Server傳送FlowMap給Client
                        image_server.send_flowmap(img_bytes)
                        last_saved_frame = current_frame
                        print(f"已傳送FlowMap給Client於Frame {current_frame}")
                
                # 保存第一張FlowMap和水池追蹤畫面 [測試用]
                # if not first_frame_saved and tracker.flow_map_generator.current_frame > 30:
                #     # 等待至少30幀後再保存，確保FlowMap有足夠的數據
                #     tracking_path, flowmap_path = save_first_flowmap_and_tracking(
                #         output_frame, 
                #         tracker.flow_map_generator.accumulated_flowmap
                #     )
                #     print(f"已保存第一張FlowMap和水池追蹤畫面")
                #     print(f"追蹤畫面: {tracking_path}")
                #     print(f"FlowMap: {flowmap_path}")
                #     first_frame_saved = True

                # 短暫暫停
                time.sleep(0.03)  # 約 30 FPS
                    
            except Exception as e:
                print(f"追蹤過程中發生錯誤: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)  # 錯誤後暫停一下再繼續
                
    except Exception as e:
        print(f"追蹤執行緒發生嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("追蹤執行緒結束")
        # 確保追蹤器狀態被正確設置
        tracker.running = False

if __name__ == "__main__":
    main()