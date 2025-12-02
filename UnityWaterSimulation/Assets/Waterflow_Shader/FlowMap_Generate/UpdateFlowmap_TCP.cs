using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using System.Linq;
using System.Net.Sockets; // 建立TCP連線
using System.Threading;
using System.Threading.Tasks;

public class UpdateFlowMapTCP : MonoBehaviour
{
    [Header("水面材質設定")]
    public Material waterMaterial;

    [Header("FlowMap於Shader Graph當中的屬性名稱")]
    public string flowMapPropertyName = "_FlowMap";

    [Header("FlowMap資料夾路徑")]
    public string flowMapFolderPath = "C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/FlowMap_Image/test/SSSSSS/";

    [Header("FlowMap更新頻率")]
    public float updateInterval = 1.0f;

    [Header("伺服器連線設定")]
    // 查看方式: CMD輸入ipconfig指令，查看IPv4
    public string serverIP = "140.118.157.14";
    public int serverPort = 8888;
    public bool useServerConnection = true;

    public bool debugLog = true;

    private float lerpTime = 0.0f; //FlowMap切換的平滑過度參數
    private List<string> flowMapFiles;
    private int currentIndex = 0;
    private Texture2D[] flowMapTextures;

    // 網路連線相關
    private TcpClient client; // 與Server連線的物件(用於建立Client)
    private NetworkStream stream; // 用於與Server進行資料傳輸的管道
    private Thread receiveThread; // 開啟背景Thread，用以持續監聽Server傳遞的資料(避免佔用主Thread)
    private bool isConnected = false; // 紀錄當前Client是否與Server建立連線
    private byte[] receivedImageData;
    private bool newImageReceived = false;
    private Texture2D currentFlowMapTexture;
    private Texture2D nextFlowMapTexture;
    private bool isFirstImage = true;

    void Start()
    {
        if (waterMaterial == null)
        {
            Debug.LogError("請指定水面材質!");
            enabled = false;
            return;
        }

        // 初始化材質
        currentFlowMapTexture = new Texture2D(1024, 1024, TextureFormat.RGB24, false, true);
        nextFlowMapTexture = new Texture2D(1024, 1024, TextureFormat.RGB24, false, true);

        // 設置材質屬性
        currentFlowMapTexture.wrapMode = TextureWrapMode.Clamp;
        currentFlowMapTexture.filterMode = FilterMode.Bilinear;
        currentFlowMapTexture.anisoLevel = 1;

        nextFlowMapTexture.wrapMode = TextureWrapMode.Clamp;
        nextFlowMapTexture.filterMode = FilterMode.Bilinear;
        nextFlowMapTexture.anisoLevel = 1;

        // 如果使用伺服器連線，則連接伺服器
        if (useServerConnection)
        {
            ConnectToServer();
        }
        else
        {
            // 使用原有的本地檔案載入方式
            if (!Directory.Exists(flowMapFolderPath))
            {
                Debug.LogError($"FlowMap 資料夾不存在: {flowMapFolderPath}");
                enabled = false;
                return;
            }
            LoadAllFlowMaps();
        }
    }

    void OnDestroy()
    {
        // 關閉連線
        DisconnectFromServer();
    }

    void Update()
    {
        if (useServerConnection)
        {
            // 處理從伺服器接收的新圖像
            if (newImageReceived)
            {
                ProcessReceivedImage();
            }
        }
        else
        {
            // 原有的本地檔案更新邏輯
            lerpTime += Time.deltaTime / updateInterval;
            if (lerpTime >= 1.0f)
            {
                lerpTime = 0.0f;
                currentIndex = (currentIndex + 1) % flowMapTextures.Length;
            }
        }

        // 更新材質
        UpdateFlowMapTexture();
    }

    void ConnectToServer()
    {
        try
        {
            // 建立TCP連線
            client = new TcpClient();
            client.Connect(serverIP, serverPort);
            stream = client.GetStream();
            isConnected = true;

            if (debugLog)
                Debug.Log($"已連接到伺服器 {serverIP}:{serverPort}");

            // 開始接收資料的執行緒
            receiveThread = new Thread(new ThreadStart(ReceiveData));
            receiveThread.IsBackground = true;
            receiveThread.Start();
        }
        catch (System.Exception e)
        {
            Debug.LogError($"連接伺服器失敗: {e.Message}");
            isConnected = false;
        }
    }

    void DisconnectFromServer()
    {
        isConnected = false;

        if (receiveThread != null && receiveThread.IsAlive)
        {
            receiveThread.Join();
            receiveThread = null;
        }

        if (stream != null)
        {
            stream.Close();
        }

        if (client != null)
        {
            client.Close();
        }
    }

    void ReceiveData()
    {
        while (isConnected)
        {
            try
            {
                // 首先接收圖像大小 (4 bytes)
                byte[] sizeBytes = new byte[4];
                int bytesRead = stream.Read(sizeBytes, 0, 4);
                if (bytesRead != 4)
                {
                    continue;
                }

                // 將位元組轉換為整數 (大端序)
                int imageSize = (sizeBytes[0] << 24) | (sizeBytes[1] << 16) | (sizeBytes[2] << 8) | sizeBytes[3];

                // 接收圖像資料
                byte[] imageBuffer = new byte[imageSize];
                int totalBytesRead = 0;

                while (totalBytesRead < imageSize)
                {
                    int bytesRemaining = imageSize - totalBytesRead;
                    int bytesReadThisTime = stream.Read(imageBuffer, totalBytesRead, bytesRemaining);

                    if (bytesReadThisTime == 0)
                    {
                        // Server關閉
                        //isConnected = false;
                        Debug.LogWarning("檢測到Server已關閉");
                        DisconnectFromServer();
                        break;
                    }

                    totalBytesRead += bytesReadThisTime;
                }

                if (totalBytesRead == imageSize)
                {
                    // 儲存接收到的圖像資料
                    receivedImageData = imageBuffer;
                    newImageReceived = true;

                    if (debugLog)
                        Debug.Log($"已接收 FlowMap 圖像，大小: {imageSize} 位元組");
                }
            }
            catch (System.Exception e)
            {
                if (isConnected)
                {
                    Debug.LogError($"接收資料時發生錯誤: {e.Message}");
                    isConnected = false;
                }
                break;
            }
        }
    }

    void ProcessReceivedImage()
    {
        try
        {
            // 在主執行緒中處理圖像資料
            if (isFirstImage)
            {
                // 第一張圖像
                currentFlowMapTexture.LoadImage(receivedImageData);
                currentFlowMapTexture.Apply();
                isFirstImage = false;
            }
            else
            {
                // 交換材質
                Texture2D temp = currentFlowMapTexture;
                currentFlowMapTexture = nextFlowMapTexture;
                nextFlowMapTexture = temp;

                // 載入新圖像到下一個材質
                nextFlowMapTexture.LoadImage(receivedImageData);
                nextFlowMapTexture.Apply();

                // 重置過渡時間
                lerpTime = 0.0f;
            }

            newImageReceived = false;
        }
        catch (System.Exception e)
        {
            Debug.LogError($"處理接收到的圖像時發生錯誤: {e.Message}");
            newImageReceived = false;
        }
    }

    void LoadAllFlowMaps()
    {
        flowMapFiles = Directory.GetFiles(flowMapFolderPath, "*.png").OrderBy(f => f).ToList();
        flowMapTextures = new Texture2D[flowMapFiles.Count];
        for (int i = 0; i < flowMapFiles.Count; i++)
        {
            byte[] fileData = File.ReadAllBytes(flowMapFiles[i]);
            Texture2D texture = new Texture2D(2, 2, TextureFormat.RGB24, false, true);
            texture.LoadImage(fileData);
            texture.wrapMode = TextureWrapMode.Clamp;
            texture.filterMode = FilterMode.Bilinear;
            texture.anisoLevel = 1;
            texture.Apply(true, true);
            flowMapTextures[i] = texture;
        }
    }

    void UpdateFlowMapTexture()
    {
        if (useServerConnection)
        {
            if(isFirstImage)
            {
                waterMaterial.SetTexture("_FlowMap", currentFlowMapTexture);
                waterMaterial.SetFloat("_LerpValue", 0f); // 不進行過渡
                if (debugLog && Time.frameCount % 60 == 0)
                {
                    Debug.Log("目前僅收到一張 FlowMap，無法執行過渡插值。");
                }
            }
            else
            {
                // 使用從伺服器接收的材質
                lerpTime += Time.deltaTime / updateInterval;
                lerpTime = Mathf.Clamp01(lerpTime);

                // 設置材質
                waterMaterial.SetTexture("_FlowMap", currentFlowMapTexture);
                waterMaterial.SetTexture("_FlowMap_2", nextFlowMapTexture);
                waterMaterial.SetFloat("_LerpValue", lerpTime);

                if (debugLog && Time.frameCount % 30 == 0)
                {
                    Debug.Log($"使用伺服器 FlowMap，Lerp 值: {lerpTime}");
                }
            }
        }
        else
        {
            // 原有的本地檔案更新邏輯
            int nextIndex = (currentIndex + 1) % flowMapTextures.Length;

            // 線性插值兩個 Texture
            Texture2D currentTexture = flowMapTextures[currentIndex];
            Texture2D nextTexture = flowMapTextures[nextIndex];

            // 在 Shader 中進行插值
            waterMaterial.SetTexture("_FlowMap", currentTexture);
            waterMaterial.SetTexture("_FlowMap_2", nextTexture);
            waterMaterial.SetFloat("_LerpValue", lerpTime);

            if (debugLog)
            {
                Debug.Log($"當前 FlowMap: {Path.GetFileName(flowMapFiles[currentIndex])}");
            }
        }
    }
}