using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Net.Sockets;
using System.Threading;

public class FlowMapClient : MonoBehaviour
{
    [Header("伺服器連線設定")]
    public string serverIP = "140.118.157.14";
    public int serverPort = 8888;
    public bool autoConnect = true; //自動與Server連線
    public bool debugLog = true; //打印除錯訊息於Console

    [Header("水面材質設定")]
    public Material waterMaterial;
    public string flowMapPropertyName = "_FlowMap";
    public string flowMapProperty2Name = "_FlowMap_2";
    public string lerpPropertyName = "_LerpValue";
    public float updateInterval = 1.0f;

    // 網路連線相關
    private TcpClient client;
    private NetworkStream stream;
    private Thread receiveThread;
    private bool isConnected = false;
    private object lockObject = new object();

    // 圖像處理相關
    private Texture2D currentFlowMapTexture;
    private Texture2D nextFlowMapTexture;
    private Texture2D frameTexture;
    private byte[] receivedImageData;
    private byte[] receivedFrameData;
    private bool newImageReceived = false;
    private bool newFrameReceived = false;
    private bool isFirstImage = true;
    private float lerpTime = 0.0f;

    // 事件
    public Action<bool> OnConnectionStatusChanged;
    public Action<Texture2D> OnFrameReceived;
    public Action<Texture2D> OnFlowMapReceived;

    // 連線狀態屬性
    public bool IsConnected { get { return isConnected; } }

    void Start()
    {
        InitializeTextures();

        if (autoConnect)
        {
            Connect();
        }
    }

    void OnDestroy()
    {
        Disconnect();
    }

    void Update()
    {
        if (isConnected)
        {
            // 處理接收到的新 FlowMap
            if (newImageReceived)
            {
                ProcessReceivedFlowMap();
            }

            // 處理接收到的新 Frame
            if (newFrameReceived)
            {
                ProcessReceivedFrame();
            }

            // 更新水面材質
            UpdateFlowMapTexture();
        }
    }

    /// <summary>
    /// 連接到伺服器
    /// </summary>
    public void Connect()
    {
        try
        {
            // 如果已經連接，先斷開
            if (isConnected)
            {
                Disconnect();
            }

            // 建立 TCP 連線
            client = new TcpClient();
            client.Connect(serverIP, serverPort);
            stream = client.GetStream();
            isConnected = true;

            if (debugLog)
                Debug.Log($"[已連接到伺服器] {serverIP}:{serverPort}");

            // 開始接收資料的執行緒
            receiveThread = new Thread(ReceiveLoop);
            receiveThread.IsBackground = true;
            receiveThread.Start();

            // 觸發連線狀態變更事件
            OnConnectionStatusChanged?.Invoke(true);
        }
        catch (Exception e)
        {
            Debug.LogError($"[連接伺服器失敗]: {e.Message}");
            isConnected = false;
            OnConnectionStatusChanged?.Invoke(false);
        }
    }

    /// <summary>
    /// 斷開與伺服器的連接
    /// </summary>
    public void Disconnect()
    {
        if (!isConnected)
            return;

        isConnected = false;

        if (receiveThread != null && receiveThread.IsAlive)
        {
            receiveThread.Join(1000); // 等待最多 1 秒
            receiveThread = null;
        }

        if (stream != null)
        {
            stream.Close();
            stream = null;
        }

        if (client != null)
        {
            client.Close();
            client = null;
        }

        if (debugLog)
            Debug.Log("已斷開與伺服器的連線");

        // 觸發連線狀態變更事件
        OnConnectionStatusChanged?.Invoke(false);
    }

    /// <summary>
    /// 向伺服器請求當前 Frame
    /// </summary>
    public void RequestCurrentFrame()
    {
        if (!isConnected)
        {
            Debug.LogWarning("尚未連接到伺服器，無法請求 Frame");
            return;
        }

        try
        {
            // 發送請求當前 Frame 的命令 (命令代碼 1)
            byte[] commandBytes = new byte[] { 1 };
            stream.Write(commandBytes, 0, commandBytes.Length);

            if (debugLog)
                Debug.Log("已向伺服器請求當前 Frame");
        }
        catch (Exception e)
        {
            Debug.LogError($"請求當前 Frame 時發生錯誤: {e.Message}");
            Disconnect();
        }
    }

    /// <summary>
    /// 向伺服器發送編輯後的 Frame
    /// </summary>
    public void SendEditedFrame(Texture2D editedFrame)
    {
        if (!isConnected)
        {
            Debug.LogWarning("尚未連接到伺服器，無法發送編輯後的 Frame");
            return;
        }

        try
        {
            // 將 Texture2D 轉換為 JPG 格式的 byte 陣列
            byte[] frameData = editedFrame.EncodeToJPG();

            // 發送編輯後 Frame 的命令 (命令代碼 2)
            byte[] commandBytes = new byte[] { 2 };
            stream.Write(commandBytes, 0, commandBytes.Length);

            // 發送 Frame 大小
            byte[] sizeBytes = BitConverter.GetBytes(frameData.Length);
            if (BitConverter.IsLittleEndian)
                Array.Reverse(sizeBytes);
            stream.Write(sizeBytes, 0, sizeBytes.Length);

            // 發送 Frame 資料
            stream.Write(frameData, 0, frameData.Length);

            if (debugLog)
                Debug.Log($"已向伺服器發送編輯後的 Frame，大小: {frameData.Length} 位元組");
        }
        catch (Exception e)
        {
            Debug.LogError($"發送編輯後的 Frame 時發生錯誤: {e.Message}");
            Disconnect();
        }
    }

    /// <summary>
    /// 獲取當前接收到的 Frame
    /// </summary>
    public Texture2D GetCurrentFrame()
    {
        return frameTexture;
    }


    private void InitializeTextures()
    {
        if (waterMaterial == null)
        {
            Debug.LogError("請指定水面材質!");
            enabled = false;
            return;
        }

        // 初始化 FlowMap Texture2D
        currentFlowMapTexture = new Texture2D(1024, 1024, TextureFormat.RGB24, false, true);
        nextFlowMapTexture = new Texture2D(1024, 1024, TextureFormat.RGB24, false, true);
        frameTexture = new Texture2D(1024, 1024, TextureFormat.RGB24, false, true);

        // 設置紋理參數
        currentFlowMapTexture.wrapMode = TextureWrapMode.Clamp;
        currentFlowMapTexture.filterMode = FilterMode.Bilinear;
        currentFlowMapTexture.anisoLevel = 1;

        nextFlowMapTexture.wrapMode = TextureWrapMode.Clamp;
        nextFlowMapTexture.filterMode = FilterMode.Bilinear;
        nextFlowMapTexture.anisoLevel = 1;

        frameTexture.wrapMode = TextureWrapMode.Clamp;
        frameTexture.filterMode = FilterMode.Bilinear;
        frameTexture.anisoLevel = 1;
    }

    private void ReceiveLoop()
    {
        while (isConnected)
        {
            try
            {
                // 接收命令類型 (1 byte)
                byte[] cmdTypeBuffer = new byte[1];
                int bytesRead = stream.Read(cmdTypeBuffer, 0, 1);
                if (bytesRead != 1) continue;

                int cmdType = cmdTypeBuffer[0];

                // 接收圖像大小 (4 bytes)
                byte[] sizeBytes = new byte[4];
                bytesRead = stream.Read(sizeBytes, 0, 4);
                if (bytesRead != 4) continue;

                int imageSize = (sizeBytes[0] << 24) | (sizeBytes[1] << 16) | (sizeBytes[2] << 8) | sizeBytes[3];

                // 接收圖像資料
                byte[] imageBuffer = new byte[imageSize];
                int totalRead = 0;
                while (totalRead < imageSize)
                {
                    int read = stream.Read(imageBuffer, totalRead, imageSize - totalRead);
                    if (read == 0)
                    {
                        Debug.LogWarning("檢測到伺服器已關閉");
                        Disconnect();
                        return;
                    }
                    totalRead += read;
                }

                // 根據命令類型處理不同的圖像資料
                if (cmdType == 1) // FlowMap
                {
                    lock (lockObject)
                    {
                        receivedImageData = imageBuffer;
                        newImageReceived = true;
                    }
                    /*if (debugLog)
                        Debug.Log($"已接收 FlowMap，大小: {imageSize} 位元組");*/
                }
                else if (cmdType == 2) // Frame
                {
                    lock (lockObject)
                    {
                        receivedFrameData = imageBuffer;
                        newFrameReceived = true;
                    }
                    /*if (debugLog)
                        Debug.Log($"已接收 Frame，大小: {imageSize} 位元組");*/
                }
                else
                {
                    Debug.LogWarning($"收到未知命令類型: {cmdType}");
                }
            }
            catch (Exception e)
            {
                if (isConnected)
                    Debug.LogError($"接收資料時發生錯誤: {e.Message}");
                Disconnect();
                break;
            }
        }
    }

    private void ProcessReceivedFlowMap()
    {
        lock (lockObject)
        {
            try
            {
                if (isFirstImage)
                {
                    currentFlowMapTexture.LoadImage(receivedImageData);
                    currentFlowMapTexture.Apply();
                    isFirstImage = false;

                    // 觸發 FlowMap 接收事件
                    OnFlowMapReceived?.Invoke(currentFlowMapTexture);
                }
                else
                {
                    // 交換兩個紋理
                    Texture2D temp = currentFlowMapTexture;
                    currentFlowMapTexture = nextFlowMapTexture;
                    nextFlowMapTexture = temp;

                    // 載入新圖像到下一個紋理
                    nextFlowMapTexture.LoadImage(receivedImageData);
                    nextFlowMapTexture.Apply();
                    lerpTime = 0.0f;

                    // 觸發 FlowMap 接收事件
                    OnFlowMapReceived?.Invoke(nextFlowMapTexture);
                }
                newImageReceived = false;
            }
            catch (Exception e)
            {
                Debug.LogError($"處理接收到的 FlowMap 時發生錯誤: {e.Message}");
                newImageReceived = false;
            }
        }
    }

    private void ProcessReceivedFrame()
    {
        lock (lockObject)
        {
            try
            {
                frameTexture.LoadImage(receivedFrameData);
                frameTexture.Apply();

                // 觸發 Frame 接收事件
                OnFrameReceived?.Invoke(frameTexture);

                newFrameReceived = false;
            }
            catch (Exception e)
            {
                Debug.LogError($"處理接收到的 Frame 時發生錯誤: {e.Message}");
                newFrameReceived = false;
            }
        }
    }

    private void UpdateFlowMapTexture()
    {
        if (isFirstImage)
        {
            waterMaterial.SetTexture(flowMapPropertyName, currentFlowMapTexture);
            waterMaterial.SetFloat(lerpPropertyName, 0f);
            if (debugLog && Time.frameCount % 60 == 0)
            {
                Debug.Log("目前僅收到一張 FlowMap，無法執行過渡插值。");
            }
        }
        else
        {
            lerpTime += Time.deltaTime / updateInterval;
            lerpTime = Mathf.Clamp01(lerpTime);
            waterMaterial.SetTexture(flowMapPropertyName, currentFlowMapTexture);
            waterMaterial.SetTexture(flowMapProperty2Name, nextFlowMapTexture);
            waterMaterial.SetFloat(lerpPropertyName, lerpTime);
            /*if (debugLog && Time.frameCount % 30 == 0)
            {
                Debug.Log($"使用伺服器 FlowMap，Lerp 值: {lerpTime}");
            }*/
        }
    }

    public void SendAnnotationPoints(List<Vector2Int> points)
    {
        if (!isConnected)
        {
            Debug.LogWarning("尚未連接到伺服器，無法發送標記座標");
            return;
        }

        try
        {
            // 將座標序列化為字串，例如: "x1,y1;x2,y2;..."
            string data = "";
            for (int i = 0; i < points.Count; i++)
            {
                data += points[i].x + "," + points[i].y;
                if (i < points.Count - 1) data += ";";
            }

            byte[] pointBytes = System.Text.Encoding.UTF8.GetBytes(data);

            // 發送命令代碼 (假設3代表發送標記座標)
            byte[] cmd = new byte[] { 3 };
            stream.Write(cmd, 0, cmd.Length);

            // 發送資料大小
            byte[] sizeBytes = BitConverter.GetBytes(pointBytes.Length);
            if (BitConverter.IsLittleEndian) Array.Reverse(sizeBytes);
            stream.Write(sizeBytes, 0, sizeBytes.Length);

            // 發送座標資料
            stream.Write(pointBytes, 0, pointBytes.Length);

            Debug.Log($"已發送標記座標: {data}");
        }
        catch (Exception e)
        {
            Debug.LogError($"發送標記座標時發生錯誤: {e.Message}");
            Disconnect();
        }
    }
}