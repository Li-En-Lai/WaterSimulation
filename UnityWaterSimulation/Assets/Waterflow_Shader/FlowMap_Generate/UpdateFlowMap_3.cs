using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using System.Linq;

public class UpdateFlowMap_3 : MonoBehaviour
{
    [Header("水面材質設定")]
    public Material waterMaterial;

    [Header("FlowMap於Shader Graph當中的屬性名稱")]
    public string flowMapPropertyName = "_FlowMap";
    public string flowMapProperty2Name = "_FlowMap_2";
    public string lerpValuePropertyName = "_LerpValue";

    [Header("FlowMap資料夾路徑")]
    public string flowMapFolderPath = "C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/FlowMap_Image/test/SSSSSS/";

    [Header("FlowMap更新頻率")]
    public float updateInterval = 1.0f;

    [Header("平滑過渡設定")]
    [Range(0.1f, 5.0f)]
    public float transitionDuration = 1.0f;  // 過渡持續時間
    public AnimationCurve transitionCurve = AnimationCurve.EaseInOut(0, 0, 1, 1);  // 過渡曲線

    public bool debugLog = true;

    private float lerpTime = 0.0f; // FlowMap切換的平滑過度參數
    private List<string> flowMapFiles;
    private int currentIndex = 0;
    private int nextIndex = 1;
    private Texture2D[] flowMapTextures;
    private float timeSinceLastUpdate = 0.0f;
    private bool isTransitioning = false;

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

        // 初始化材質
        if (flowMapTextures.Length >= 2)
        {
            waterMaterial.SetTexture(flowMapPropertyName, flowMapTextures[0]);
            waterMaterial.SetTexture(flowMapProperty2Name, flowMapTextures[1]);
            waterMaterial.SetFloat(lerpValuePropertyName, 0.0f);
        }
    }

    void Update()
    {
        if (flowMapTextures.Length < 2) return;

        timeSinceLastUpdate += Time.deltaTime;

        // 開始新的過渡
        if (timeSinceLastUpdate >= updateInterval && !isTransitioning)
        {
            timeSinceLastUpdate = 0.0f;
            lerpTime = 0.0f;
            isTransitioning = true;

            // 更新索引
            currentIndex = nextIndex;
            nextIndex = (currentIndex + 1) % flowMapTextures.Length;

            // 設置材質
            waterMaterial.SetTexture(flowMapPropertyName, flowMapTextures[currentIndex]);
            waterMaterial.SetTexture(flowMapProperty2Name, flowMapTextures[nextIndex]);

            if (debugLog)
            {
                Debug.Log($"開始過渡: {Path.GetFileName(flowMapFiles[currentIndex])} -> {Path.GetFileName(flowMapFiles[nextIndex])}");
            }
        }

        // 處理過渡
        if (isTransitioning)
        {
            lerpTime += Time.deltaTime / transitionDuration;

            if (lerpTime >= 1.0f)
            {
                lerpTime = 0.0f;
                isTransitioning = false;
            }
            else
            {
                // 使用動畫曲線獲取平滑的插值值
                float smoothLerp = transitionCurve.Evaluate(lerpTime);
                waterMaterial.SetFloat(lerpValuePropertyName, smoothLerp);
            }
        }
    }

    void LoadAllFlowMaps()
    {
        flowMapFiles = Directory.GetFiles(flowMapFolderPath, "*.png").OrderBy(f => f).ToList();

        if (flowMapFiles.Count == 0)
        {
            Debug.LogWarning("找不到任何 FlowMap 圖像!");
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
            texture.anisoLevel = 1;
            texture.Apply(true, true);
            flowMapTextures[i] = texture;
        }

        Debug.Log($"已載入 {flowMapTextures.Length} 張 FlowMap 圖像");
    }
}
