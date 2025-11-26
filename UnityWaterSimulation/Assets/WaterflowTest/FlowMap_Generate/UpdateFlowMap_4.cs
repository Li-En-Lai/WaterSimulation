using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using System.Linq;

public class UpdateFlowMap_4 : MonoBehaviour
{
    [Header("水面材質設定")]
    public Material waterMaterial;

    [Header("FlowMap資料夾路徑")]
    public string flowMapFolderPath = "C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/FlowMap_Image/test/SSSSSS/";

    [Header("FlowMap更新設定")]
    [Range(0.1f, 5.0f)]
    public float updateInterval = 1.0f;  // FlowMap 更新間隔
    [Range(0.1f, 3.0f)]
    public float transitionDuration = 0.5f;  // 過渡時間
    [Range(0.01f, 0.5f)]
    public float flowSpeed = 0.1f;  // 流動速度

    public bool debugLog = false;

    private float lerpTime = 0.0f;  // FlowMap 切換的平滑過渡參數
    private List<string> flowMapFiles;
    private int currentIndex = 0;
    private int nextIndex = 1;
    private Texture2D[] flowMapTextures;
    private float timeSinceLastUpdate = 0.0f;

    void Start()
    {
        if (waterMaterial == null)
        {
            Debug.LogError("請指定水面材質!");
            enabled = false;
            return;
        }

        if (!Directory.Exists(flowMapFolderPath))
        {
            Debug.LogError($"FlowMap 資料夾不存在: {flowMapFolderPath}");
            enabled = false;
            return;
        }

        // 預加載所有 FlowMap 圖像
        LoadAllFlowMaps();

        // 初始化材質參數
        waterMaterial.SetTexture("_FlowMap", flowMapTextures[currentIndex]);
        waterMaterial.SetTexture("_FlowMap_2", flowMapTextures[nextIndex]);
        waterMaterial.SetFloat("_LerpTime", 0.0f);
        waterMaterial.SetFloat("_Speed", flowSpeed);
    }

    void Update()
    {
        timeSinceLastUpdate += Time.deltaTime;

        // 當達到更新間隔時，準備切換到下一個 FlowMap
        if (timeSinceLastUpdate >= updateInterval)
        {
            // 重置計時器
            timeSinceLastUpdate = 0.0f;

            // 重置過渡參數
            lerpTime = 0.0f;

            // 更新索引
            currentIndex = nextIndex;
            nextIndex = (nextIndex + 1) % flowMapTextures.Length;

            // 更新材質中的紋理
            waterMaterial.SetTexture("_FlowMap", flowMapTextures[currentIndex]);
            waterMaterial.SetTexture("_FlowMap_2", flowMapTextures[nextIndex]);

            if (debugLog)
            {
                Debug.Log($"切換 FlowMap: {Path.GetFileName(flowMapFiles[currentIndex])} -> {Path.GetFileName(flowMapFiles[nextIndex])}");
            }
        }

        // 計算過渡參數 (0 到 1 之間)
        lerpTime = Mathf.Clamp01(timeSinceLastUpdate / transitionDuration);

        // 更新材質中的過渡參數
        waterMaterial.SetFloat("_LerpTime", lerpTime);
    }

    void LoadAllFlowMaps()
    {
        flowMapFiles = Directory.GetFiles(flowMapFolderPath, "*.png").OrderBy(f => f).ToList();

        if (flowMapFiles.Count < 2)
        {
            Debug.LogError($"FlowMap 資料夾中至少需要 2 個圖像文件，但只找到 {flowMapFiles.Count} 個");
            enabled = false;
            return;
        }

        flowMapTextures = new Texture2D[flowMapFiles.Count];

        for (int i = 0; i < flowMapFiles.Count; i++)
        {
            byte[] fileData = File.ReadAllBytes(flowMapFiles[i]);
            Texture2D texture = new Texture2D(2, 2, TextureFormat.RGB24, false, true);
            texture.LoadImage(fileData);
            texture.wrapMode = TextureWrapMode.Clamp;
            texture.filterMode = FilterMode.Bilinear;
            texture.anisoLevel = 2;  // 增加各向異性過濾級別以提高視覺質量
            texture.Apply(true, true);
            flowMapTextures[i] = texture;
        }

        currentIndex = 0;
        nextIndex = 1;

        Debug.Log($"已加載 {flowMapTextures.Length} 個 FlowMap 紋理");
    }
}
