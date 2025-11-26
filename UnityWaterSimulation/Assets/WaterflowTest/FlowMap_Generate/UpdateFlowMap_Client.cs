using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using System.Linq;

public class UpdateFlowMap_Client : MonoBehaviour
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
    public string serverIP = "140.118.157.14";
    public int serverPort = 8888;
    public bool useServerConnection = true;

    public bool debugLog = true;

    private float lerpTime = 0.0f;
    private List<string> flowMapFiles;
    private int currentIndex = 0;
    private Texture2D[] flowMapTextures;

    // TCP 客戶端物件
    private TCPClientClass tcpClient; // 與Server連線的物件(用於建立Client)
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

        // 初始化 Texture2D
        currentFlowMapTexture = new Texture2D(1024, 1024, TextureFormat.RGB24, false, true);
        nextFlowMapTexture = new Texture2D(1024, 1024, TextureFormat.RGB24, false, true);

        currentFlowMapTexture.wrapMode = TextureWrapMode.Clamp;
        currentFlowMapTexture.filterMode = FilterMode.Bilinear;
        currentFlowMapTexture.anisoLevel = 1;

        nextFlowMapTexture.wrapMode = TextureWrapMode.Clamp;
        nextFlowMapTexture.filterMode = FilterMode.Bilinear;
        nextFlowMapTexture.anisoLevel = 1;

        if (useServerConnection)
        {
            tcpClient = new TCPClientClass();
            tcpClient.DebugLog = debugLog;
            tcpClient.OnImageReceived = (imageData) =>
            {
                receivedImageData = imageData;
                newImageReceived = true;
            };
            tcpClient.Connect(serverIP, serverPort);
        }
        else
        {
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
        if (useServerConnection)
        {
            if (tcpClient != null)
            {
                tcpClient.Disconnect();
            }
        }
    }

    void Update()
    {
        if (useServerConnection)
        {
            if (newImageReceived)
            {
                ProcessReceivedImage();
            }
        }
        else
        {
            lerpTime += Time.deltaTime / updateInterval;
            if (lerpTime >= 1.0f)
            {
                lerpTime = 0.0f;
                currentIndex = (currentIndex + 1) % flowMapTextures.Length;
            }
        }

        UpdateFlowMapTexture();
    }

    void ProcessReceivedImage()
    {
        try
        {
            if (isFirstImage)
            {
                currentFlowMapTexture.LoadImage(receivedImageData);
                currentFlowMapTexture.Apply();
                isFirstImage = false;
            }
            else
            {
                Texture2D temp = currentFlowMapTexture;
                currentFlowMapTexture = nextFlowMapTexture;
                nextFlowMapTexture = temp;

                nextFlowMapTexture.LoadImage(receivedImageData);
                nextFlowMapTexture.Apply();

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
            if (isFirstImage)
            {
                waterMaterial.SetTexture("_FlowMap", currentFlowMapTexture);
                waterMaterial.SetFloat("_LerpValue", 0f);
                if (debugLog && Time.frameCount % 60 == 0)
                {
                    Debug.Log("目前僅收到一張 FlowMap，無法執行過渡插值。");
                }
            }
            else
            {
                lerpTime += Time.deltaTime / updateInterval;
                lerpTime = Mathf.Clamp01(lerpTime);

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
            int nextIndex = (currentIndex + 1) % flowMapTextures.Length;

            Texture2D currentTexture = flowMapTextures[currentIndex];
            Texture2D nextTexture = flowMapTextures[nextIndex];

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
