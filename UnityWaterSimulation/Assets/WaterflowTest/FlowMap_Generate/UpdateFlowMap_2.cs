using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using System.Linq;

public class UpdateFlowMap_2 : MonoBehaviour
{
    [Header("水面材質設定")]
    public Material waterMaterial;

    [Header("FlowMap於Shader Graph當中的屬性名稱")]
    public string flowMapPropertyName = "_FlowMap";

    [Header("FlowMap資料夾路徑")]
    public string flowMapFolderPath = "C:/Users/Li-En_Lai/Desktop/ArUcoMarker_Test/FlowMap_Image/test/SSSSSS/";

    [Header("FlowMap更新頻率")]
    public float updateInterval = 1.0f;

    public bool debugLog = true;

    private float lerpTime = 0.0f; //FlowMap切換的平滑過度參數
    private List<string> flowMapFiles;
    private int currentIndex = 0;
    private Texture2D[] flowMapTextures;

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
    }

    void Update()
    {
        lerpTime += Time.deltaTime / updateInterval;
        Debug.Log(lerpTime);

        if (lerpTime >= 1.0f)
        {
            lerpTime = 0.0f;
            currentIndex = (currentIndex + 1) % flowMapTextures.Length;
        }


        UpdateFlowMapTexture();
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
        int nextIndex = (currentIndex + 1) % flowMapTextures.Length;

        // 線性插值兩個Texture
        Texture2D currentTexture = flowMapTextures[currentIndex];
        Texture2D nextTexture = flowMapTextures[nextIndex];

        // 在 Shader 中進行插值
        waterMaterial.SetTexture("_FlowMap", currentTexture);
        waterMaterial.SetTexture("_FlowMap_2", nextTexture);
        waterMaterial.SetFloat("_LerpValue", lerpTime);

        if (debugLog)
        {
            Debug.Log($"當前FlowMap:{Path.GetFileName(flowMapFiles[currentIndex])}");
            //Debug.Log($"當前Lerp Time:{lerpTime}");
        }

    }
}
