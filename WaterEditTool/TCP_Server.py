import socket
import threading
import struct
import cv2
import numpy as np

class FlowMapServer:
    def __init__(self, host='0.0.0.0', port=8888):
        '''Server初始化'''
        self.host = host # IP位址(設置為'0.0.0.0'，接受所有IP連線)
        self.port = port # 通訊Port號碼 (設置為8888，Client請求連線時須使用相同Port號碼)
        # 建立Socket通訊Server(指定網路位址為IPv4、通訊協定為TCP)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket = None # 儲存連接的Client Socket
        self.client_address = None # 儲存Client位址資訊
        self.client_connected = False # 標記是否有Client端連接
        self.running = False # Server運行狀態

        self.received_img = None # 儲存從Client端接收到的圖片
        self.video_frame = None # 儲存Video Frame

        self.frame_request = False # Client端是否請求當前串流影片的Frame
        self.command_lock = threading.Lock() # 用於同步命令處理

        self.flowmap_streaming = False # 決定是否要開始傳遞生成完成的FlowMap給Client

        self.annotation_points = None # 紀錄Client傳遞的透是矩陣參考點像素座標值
        self.annotation_points_received = False # 是否接收到Client傳遞的參考點像素座標值

        self.frame_request_transformed = False  # Client端是否請求當前透視變換後的Frame

        #=== 射水向量相關變數 ===
        self.water_jet_vectors= [] # 儲存Client傳遞的射水向量
        self.water_jet_vectors_received = False # 檢查是否有接收到Client傳遞的射水向量資料

    def start(self):
        self.server_socket.bind((self.host, self.port)) # Server位址綁定
        # 開始監聽，等待Client連線
        # 設置最多允許5個(backlog)Client同時排隊等待accept
        self.server_socket.listen(5)

        self.running = True # Server運行狀態設為運行中
        print("Server已啟動")
        print(f"[Server started on {self.host}:{self.port}]")
        threading.Thread(target=self.accept_client, daemon=True).start()
    
    def accept_client(self):
        """接受Client連接的Thread函數"""
        while self.running:
            try:
                # Server接受Client連線請求
                client_socket, addr = self.server_socket.accept()
                print(f"[Client已連線，位址: {addr}]")
            
                # 如果已有Client端連接，關閉舊連接
                if self.client_socket:
                    try:
                        self.client_socket.close()
                    except:
                        pass
                
                # 保存新的客戶端連接
                self.client_socket = client_socket
                self.client_address = addr
                self.client_connected = True

                # 建立並啟動用於監控Client連接狀態的Thread
                threading.Thread(target=self.monitor_client,daemon=True).start()
                # 建立並啟動用於處理Client命令的Thread
                threading.Thread(target=self.handle_client_commands,daemon=True).start()


            # 接受Client連線出現問題
            except OSError as e:
                if not self.running:
                    # 正常關閉時產生的錯誤，可忽略
                    break
                print(f"[Error accepting client] {e}")
    
    def monitor_client(self):
        '''檢查Client是否仍連線'''
        try:
            while self.client_connected and self.running:
                if not self.client_socket:
                    break
                # 短暫睡眠以減少 CPU 使用率
                threading.Event().wait(1.0)
        except:
            pass

        finally:
            if self.client_connected:
                print(f"Client斷開連線: {self.client_address}")
                # 清除Client連線狀態
                if self.client_socket:
                    self.client_socket.close()
                self.client_socket = None
                self.client_connected = False
    
    def handle_client_commands(self):
        '''處理客戶端發送的命令'''
        try:
            while self.client_connected and self.running:
                try:
                    # 接收命令類型 (1 byte)
                    cmd_type = self.client_socket.recv(1)
                    if not cmd_type:
                        break  # 客戶端斷開連線
                    
                    cmd = int.from_bytes(cmd_type, byteorder='big')
                    print(f"[收到客戶端命令: {cmd}]")
                    
                    with self.command_lock:
                        if cmd == 1:  # 請求當前 Frame
                            self.frame_request = True
                            print("[客戶端請求當前 Frame]")
                        elif cmd == 2:  # 客戶端將發送編輯後的 Frame
                            print("[客戶端將發送編輯後的 Frame]")
                            received_data = self.receive_image_from_client()
                            if received_data:
                                print(f"[成功接收編輯後的 Frame: {len(received_data)} bytes]")
                            else:
                                print("[接收編輯後的 Frame 失敗]")
                        elif cmd == 3: # 接收Client請求發送FlowMap
                            print("Client請求傳遞生成完成的FlowMap")
                            self.flowmap_streaming = True
                        elif cmd == 4: # 接收Client請求停止發送FlowMap
                            print("Client請求停止傳遞生成完成的FlowMap")
                            self.flowmap_streaming = False
                        elif cmd == 5: # 接收Client發送的參考點像素座標數值
                            print("接收Client傳遞的參考點像素座標數值")
                            points = self.receive_annotation_point()
                            if points:
                                self.annotation_points = points
                                self.annotation_points_received = True
                                print(f"[成功接收參考點座標: {points}]")
                            else:
                                print("[接收參考點座標失敗]")
                        elif cmd == 6: # 接收Client請求傳遞透視變換後的Frame
                            print("Client請求傳遞透視變換後的Frame")
                            self.frame_request_transformed = True
                        elif cmd == 7: #接收Client傳遞的射水向量標註點像素座標數值
                            print("接收Client傳遞的射水向量像素座標數值")
                            vectors = self.receive_water_jet_vectors()
                            if vectors:
                                self.water_jet_vectors = vectors
                                self.water_jet_vectors_received = True
                                print(f"[成功接收射水向量像素座標數值: {vectors}]")
                            else:
                                print("[接收射水向量像素座標數值失敗]")
                        else:
                            print(f"[未知命令: {cmd}]")
                except socket.timeout:
                    continue  # 超時，繼續等待
                except Exception as e:
                    print(f"[處理客戶端命令時發生錯誤] {e}")
                    break
        except:
            pass
        finally:
            if self.client_connected:
                print(f"Client端: {self.client_address}斷開連線")

    def send_flowmap(self,img_bytes):
        '''傳遞FlowMap(圖片bytes)給Client'''

        # 傳遞FlowMap前檢查是否有Client連接
        if not self.client_connected:
            print("尚未有Client連線，無法傳送FlowMap")
            return
        try:
            # 傳送命令類型 (1 = FlowMap)
            self.client_socket.sendall(bytes([1]))
            # 傳送圖片之前，先傳送圖片長度
            self.client_socket.sendall(struct.pack('!I', len(img_bytes)))
            # 傳送實際圖片的 bytes 資料
            self.client_socket.sendall(img_bytes)
            # print(f"[Sent image ({len(img_bytes)} bytes)]")
        except Exception as e:
            # 傳遞FlowMap失敗
            print("無法傳遞FlowMap")
            # print(f"[Error sending image] {e}")
            # 傳遞FlowMap失敗視為Client斷線
            self.client_connected = False
    
    def receive_annotation_point(self):
        '''接收Client傳遞的標註參考點像素座標數值'''
        if not self.client_connected:
            print("尚未有Client連線，無法接收標註的參考點座標")
            return None
        try:
            # 接收資料大小
            size_data = self.client_socket.recv(4)
            if not size_data:
                print("接收標註的參考點座標大小失敗")
                return None
            
            # 解析資料大小
            data_size = struct.unpack('!I', size_data)[0]
            print(f"[準備接收標註的參考點座標，大小: {data_size} bytes]")
            
            # 接收資料
            received_data = b''
            remaining = data_size
            
            while remaining > 0:
                chunk = self.client_socket.recv(min(4096, remaining))
                if not chunk:
                    print("接收標註的參考點座標資料中斷")
                    return None
                received_data += chunk
                remaining -= len(chunk)
            
            # 解析座標資料 (格式: "x1,y1;x2,y2;x3,y3;x4,y4" -> 根據Unity Client傳遞的格式進行處理)
            points_str = received_data.decode('utf-8')
            points = []
            
            for point_str in points_str.split(';'):
                if ',' in point_str:
                    x, y = point_str.split(',')
                    points.append((int(x), int(y)))
            
            # 確保有4個點
            if len(points) != 4:
                print(f"[警告] 接收到 {len(points)} 個點，但需要4個點")
                return None
                
            return points
            
        except Exception as e:
            print(f"接收標註點座標時發生錯誤: {e}")
            return None
    
    def has_annotation_points(self):
        '''檢查是否已接收到標註點座標(功能函數提供外部呼叫)'''
        return self.annotation_points_received
    
    def get_annotation_points(self):
        '''獲取標註點座標(功能函數提供外部呼叫)'''
        if self.annotation_points_received:
            return self.annotation_points
        return None
    
    def reset_annotation_points(self):
        '''重置標註點座標狀態(功能函數提供外部呼叫)'''
        self.annotation_points = None
        self.annotation_points_received = False

    def receive_image_from_client(self):
        '''接收Client編輯後的Frame'''
        # 確認是否有Client連線
        if not self.client_connected:
            print("尚未有Client連線，無法接收圖片")
            return None
        try:
            # 接收圖片大小
            size_data = self.client_socket.recv(4) # Client傳送的圖片大小資訊
            if not size_data:
                print("接收圖片大小失敗")
                return None
            
            # 解析圖片大小
            image_size = struct.unpack('!I', size_data)[0]
            print(f"[準備接收圖片，大小: {image_size} bytes]")
            
            # 接收圖片數據
            received_data = b''
            remaining = image_size
            
            while remaining > 0:
                chunk = self.client_socket.recv(min(4096, remaining)) # 分批讀取接收的圖片資料(分批讀取最多4096 bytes)
                if not chunk:
                    print("接收圖片數據中斷")
                    return None
                received_data += chunk
                remaining -= len(chunk)
            
            # 儲存接收到的圖片
            self.received_image = received_data
            print(f"[接收到來自Client傳遞的圖片，圖片大小: ({image_size} bytes)]")
            # 顯示圖片 5 秒
            try:
                # 解碼 byte 為 OpenCV 圖片
                nparr = np.frombuffer(received_data, np.uint8)
                img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img_np is not None:
                    cv2.imshow("Received Image", img_np)
                    cv2.waitKey(5000)  # 顯示 5 秒（5000 毫秒）
                    cv2.destroyWindow("Received Image")
                else:
                    print("[警告] 圖片解碼失敗")
            except Exception as e:
                print(f"[顯示圖片失敗] {e}")
            return received_data # 回傳圖片大小
            
        except Exception as e:
            print(f"接收圖片時發生錯誤: {e}")
            return None
    
    def receive_water_jet_vectors(self):
        '''接收Client傳遞的射水向量座標'''
        if not self.client_connected:
            print("尚未有Client連線，無法接收射水向量座標")
            return None
        try:
            # 接收資料大小
            size_data = self.client_socket.recv(4)
            if not size_data:
                print("接收射水向量座標大小失敗")
                return None
            
            # 解析資料大小
            data_size = struct.unpack('!I', size_data)[0]
            print(f"[準備接收射水向量座標，大小: {data_size} bytes]")
            
            # 接收資料
            received_data = b''
            remaining = data_size
            
            while remaining > 0:
                chunk = self.client_socket.recv(min(4096, remaining))
                if not chunk:
                    print("接收射水向量座標資料中斷")
                    return None
                received_data += chunk
                remaining -= len(chunk)
            
            # 解析座標資料 (格式: "startX,startY,endX,endY;startX,startY,endX,endY;...")
            vectors_str = received_data.decode('utf-8')
            vectors = []
            
            for vector_str in vectors_str.split(';'):
                if vector_str and vector_str.count(',') == 3:  # 確保有4個值 (startX,startY,endX,endY)
                    parts = vector_str.split(',')
                    start_x = int(parts[0])
                    start_y = int(parts[1])
                    end_x = int(parts[2])
                    end_y = int(parts[3])
                    vectors.append((start_x, start_y, end_x, end_y))
            
            return vectors
            
        except Exception as e:
            print(f"接收射水向量座標時發生錯誤: {e}")
            return None
    
    def has_water_jet_vectors(self):
        '''檢查是否已接收到射水向量座標'''
        return self.water_jet_vectors_received
    
    def get_water_jet_vectors(self):
        '''獲取射水向量座標'''
        if self.water_jet_vectors_received:
            return self.water_jet_vectors
        return []
    
    def reset_water_jet_vectors(self):
        '''重置射水向量狀態'''
        self.water_jet_vectors_received = False

    def save_video_frame(self,frame_bytes):
        '''儲存串流影片中特定的Frame，用於傳遞給Client進行後續編輯處理'''
        self.video_frame = frame_bytes
        # print("已儲存串流影片的Frame!")
    
    def send_video_frame_to_client(self):
        '''傳遞串流影片中特定的Frame給Client進行編輯'''
        # 確認是否有串流影片的Frame可傳遞給Client
        if not self.video_frame:
            print("尚未有串流影片的Frame可傳送")
            return False
        
        if not self.client_connected or not self.client_socket:
            print("尚未有Client連線，無法傳遞串流影片的Frame")
            return False
        
        try:
            # 傳送命令類型 (2 = 當前 Frame)
            self.client_socket.sendall(bytes([2]))
            # 傳送圖片大小給Client(傳遞實際圖片前先傳遞圖片大小)
            self.client_socket.sendall(struct.pack('!I', len(self.video_frame)))
            # 傳送實際圖片給Client
            self.client_socket.sendall(self.video_frame)
            print(f"[已傳遞串流影片的Frame給Client]大小:({len(self.video_frame)} bytes)")

        except Exception as e:
            print(f"傳遞串流影片的Frame給Client發生錯誤: {e}")
            self.client_connected = False
            return False
    
    def check_frame_request(self):
        '''檢查客戶端是否請求當前 Frame'''
        with self.command_lock:
            if self.frame_request:
                self.frame_request = False
                return True
            return False
        
    def check_transformed_frame_request(self):
        '''檢查客戶端是否請求透視變換後的 Frame'''
        with self.command_lock:
            if self.frame_request_transformed:
                self.frame_request_transformed = False
                return True
            return False
    
    def should_stream_flowmap(self):
        '''檢查是否要傳遞生成完成的Flowmap給Client(只有當接收到Client端發送傳遞的Command才進行)'''
        return self.client_connected and self.flowmap_streaming
    
    def send_transformed_frame(self,frame_bytes):
        '''發送透視變換後的Frame給Client'''
        # 確認是否有Client連線
        if not self.client_connected or not self.client_socket:
            print("尚未有Client連線，無法傳遞透視變換後的Frame")
            return False
        try:
            # 傳送命令類型(3=透視變換後的Frame)
            self.client_socket.sendall(bytes([3]))
            # 傳送圖片大小給Client
            self.client_socket.sendall(struct.pack('!I',len(frame_bytes)))
            # 傳送實際透視變換後的Frame圖片給Client
            self.client_socket.sendall(frame_bytes)
            return True
        except Exception as e:
            print(f"傳遞透視變換後的Frame給Client發生錯誤:{e}")
            self.client_connected = False
            return False
        
    def stop(self):
        '''手動關閉Server'''
        self.running = False # Server運行狀態設為關閉

        # 關閉Server之前先關閉Client Socket(如果當前有Client連線)
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        # 關閉Server Socket
        try:
            self.server_socket.close()
            print("Server已關閉")
        except Exception as e:
            print(f"關閉Server時發生錯誤: {e}")