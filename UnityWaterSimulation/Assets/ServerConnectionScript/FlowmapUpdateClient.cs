using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Net.Sockets;
using System.Threading;

public class FlowmapUpdateClient : MonoBehaviour
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

    [Header("VR裝置手把控制設定")]
    public OVRInput.Controller controller = OVRInput.Controller.RTouch; // 使用VR裝置右手手把

    // 網路連線相關
    private TcpClient client;
    private NetworkStream stream;
    private Thread receiveThread;
    private bool isConnected = false;
    private object lockObject = new object();

    // 圖像處理相關
    private Texture2D currentFlowMapTexture;
    private Texture2D nextFlowMapTexture;
    private byte[] receivedImageData;
    private bool newImageReceived = false;
    private bool isFirstImage = true;
    private float lerpTime = 0.0f;

    // 事件
    public Action<bool> OnConnectionStatusChanged;
    public Action<Texture2D> OnFlowMapReceived;

    // 連線狀態屬性
    public bool IsConnected { get { return isConnected; } }
    // Start is called before the first frame update
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
        Disconnect();//Client與Server斷開連線
    }

    // Update is called once per frame
    void Update()
    {
        //當有連線到Server時執行
        if (isConnected)
        {
            // 處理接收到的新 FlowMap
            if (newImageReceived)
            {
                ProcessReceivedFlowMap();
            }
            // 更新水面材質
            UpdateFlowMapTexture();

            // 按下Controller A鍵請求開始傳送FlowMap
            if (OVRInput.GetDown(OVRInput.Button.One, controller))
            {
                RequestStartFlowMapStreaming();
                Debug.Log("按下A鍵，請求開始傳送FlowMap");
            }

            // 按下 Controller B鍵請求停止傳送FlowMap
            if (OVRInput.GetDown(OVRInput.Button.Two, controller))
            {
                RequestStopFlowMapStreaming();
                Debug.Log("按下B鍵，請求停止傳送FlowMap");
            }
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
    /// 圖片接收迴圈
    /// </summary>
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

    /// <summary>
    /// 水面Texture初始化
    /// </summary>
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

        // 設置紋理參數
        currentFlowMapTexture.wrapMode = TextureWrapMode.Clamp;
        currentFlowMapTexture.filterMode = FilterMode.Bilinear;
        currentFlowMapTexture.anisoLevel = 1;

        nextFlowMapTexture.wrapMode = TextureWrapMode.Clamp;
        nextFlowMapTexture.filterMode = FilterMode.Bilinear;
        nextFlowMapTexture.anisoLevel = 1;
    }

    /// <summary>
    /// 向Server請求傳遞生成的Flowmap
    /// </summary>
    public void RequestStartFlowMapStreaming()
    {
        if (!isConnected)
        {
            Debug.LogWarning("尚未連接到Server，無法請求開始傳送FlowMap");
            return;
        }
        try
        {
            // 發送請求開始傳送FlowMap的命令 (命令代碼 3)
            byte[] commandBytes = new byte[] { 3 };
            stream.Write(commandBytes, 0, commandBytes.Length);
            if (debugLog)
                Debug.Log("已向Server請求開始傳送FlowMap");
        }
        catch (Exception e)
        {
            Debug.LogError($"向Server請求開始傳送FlowMap時發生錯誤: {e.Message}");
            Disconnect();
        }
    }

    /// <summary>
    /// 向Server請求停止傳遞生成的Flowmap
    /// </summary>
    public void RequestStopFlowMapStreaming()
    {
        if (!isConnected)
        {
            Debug.LogWarning("尚未連接到Server，無法請求停止傳送FlowMap");
            return;
        }
        try
        {
            // 發送請求停止傳送FlowMap的命令 (命令代碼 4)
            byte[] commandBytes = new byte[] { 4 };
            stream.Write(commandBytes, 0, commandBytes.Length);
            if (debugLog)
                Debug.Log("已向Server請求停止傳送FlowMap");
        }
        catch (Exception e)
        {
            Debug.LogError($"請求Server停止傳送FlowMap時發生錯誤: {e.Message}");
            Disconnect();
        }
    }

    /// <summary>
    /// 處理Server傳遞的Flowmap
    /// </summary>
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

    ///<summary>
    /// 更新水面材質使用的Flowmap Texture
    /// <summary>
    private void UpdateFlowMapTexture()
    {
        if (isFirstImage)
        {
            waterMaterial.SetTexture(flowMapPropertyName, currentFlowMapTexture);
            waterMaterial.SetFloat(lerpPropertyName, 0f);
            /*if (debugLog && Time.frameCount % 60 == 0)
            {
                Debug.Log("目前僅收到一張 FlowMap，無法執行過渡插值。");
            }*/
        }
        else
        {
            lerpTime += Time.deltaTime / updateInterval;
            lerpTime = Mathf.Clamp01(lerpTime);
            waterMaterial.SetTexture(flowMapPropertyName, currentFlowMapTexture);
            waterMaterial.SetTexture(flowMapProperty2Name, nextFlowMapTexture);
            waterMaterial.SetFloat(lerpPropertyName, lerpTime);
        }
    }
}
