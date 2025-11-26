using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using System.Linq;

public class UpdateFlowMap : MonoBehaviour
{
    [Header("設定")]
    [Tooltip("水面材質")]
    public Material waterMaterial;

    [Tooltip("FlowMap 材質屬性名稱")]
    public string flowMapPropertyName = "_FlowMap";

    [Tooltip("FlowMap 資料夾路徑")]
    public string flowMapFolderPath = "C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/FlowMap_Image/test/SSSSSS/";

    [Tooltip("更新頻率 (秒)")]
    public float updateInterval = 1.0f;

    [Tooltip("是否在控制台輸出日誌")]
    public bool debugLog = true;

    // 內部變數
    private float nextUpdateTime = 0f;
    private string lastLoadedFile = "";
    private List<string> processedFiles = new List<string>();
    private Texture2D flowMapTexture;

    void Start()
    {
        // 初始化
        if (waterMaterial == null)
        {
            Debug.LogError("請指定水面材質!");
            enabled = false;
            return;
        }

        // 檢查資料夾是否存在
        if (!Directory.Exists(flowMapFolderPath))
        {
            Debug.LogError($"FlowMap 資料夾不存在: {flowMapFolderPath}");
            enabled = false;
            return;
        }

        // 立即嘗試載入第一個 FlowMap
        TryLoadLatestFlowMap();
    }

    void Update()
    {
        // 檢查是否到了更新時間
        if (Time.time >= nextUpdateTime)
        {
            TryLoadLatestFlowMap();
            nextUpdateTime = Time.time + updateInterval;
        }
    }

    void TryLoadLatestFlowMap()
    {
        try
        {
            // 獲取資料夾中的所有 png 文件
            string[] flowMapFiles = Directory.GetFiles(flowMapFolderPath, "*.png")
                .OrderBy(f => f)
                .ToArray();

            if (flowMapFiles.Length == 0)
            {
                if (debugLog) Debug.Log("資料夾中沒有找到 FlowMap 圖像");
                return;
            }

            // 找出最新的未處理文件
            string latestFile = null;
            foreach (string file in flowMapFiles)
            {
                if (!processedFiles.Contains(file))
                {
                    latestFile = file;
                    break;
                }
            }

            // 如果沒有新文件，則檢查是否需要重置處理列表
            if (latestFile == null)
            {
                // 如果已處理所有文件，重置處理列表以允許重新使用文件
                if (processedFiles.Count >= flowMapFiles.Length)
                {
                    processedFiles.Clear();
                    latestFile = flowMapFiles[0];
                }
                else
                {
                    return; // 沒有新文件可處理
                }
            }

            // 避免重複加載相同的文件
            if (latestFile == lastLoadedFile)
                return;

            if (debugLog) Debug.Log($"載入 FlowMap: {Path.GetFileName(latestFile)}");

            // 載入圖像文件
            byte[] fileData = File.ReadAllBytes(latestFile);

            // 釋放舊紋理
            if (flowMapTexture != null)
                Destroy(flowMapTexture);

            // 創建新紋理並設置正確的參數
            flowMapTexture = new Texture2D(2, 2, TextureFormat.RGB24, false, true); // 第五個參數 linear=true，表示不使用 sRGB
            flowMapTexture.LoadImage(fileData);

            // 設置紋理參數
            flowMapTexture.wrapMode = TextureWrapMode.Clamp;
            flowMapTexture.filterMode = FilterMode.Bilinear;
            flowMapTexture.anisoLevel = 1;
            flowMapTexture.Apply(true, true); // 強制更新並使其可讀寫

            // 更新材質
            waterMaterial.SetTexture(flowMapPropertyName, flowMapTexture);

            // 更新已處理文件列表
            processedFiles.Add(latestFile);
            lastLoadedFile = latestFile;
        }
        catch (System.Exception e)
        {
            Debug.LogError($"載入 FlowMap 時發生錯誤: {e.Message}");
        }
    }
}
