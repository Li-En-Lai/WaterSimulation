using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class RippleEffect2 : MonoBehaviour
{
    [Header("Ripple 基本設定")]
    public int TextureSize = 512; // Render 的 Texture 大小
    public RenderTexture ObjectsRT; // 用於產生 Ripple 效果的 Render Texture
    private RenderTexture CurrRT, PrevRT, TempRT; // 用於 Ripple 計算的 RenderTexture
    public Shader RippleShader, AddShader; // 兩個用於產生 Ripple 效果的 Shader
    private Material RippleMat, AddMat; // 基於兩個 Shader 創建的材質

    [Header("動態 Flowmap 設定")]
    public bool enableFlowmapIntegration = true; // 是否啟用 Flowmap 整合
    public Texture2D originalFlowmap; // 原始靜態 Flowmap
    public Shader rippleFlowShader; // 計算 Ripple 流向的 Shader
    public Shader flowmapBlendShader; // 混合 Flowmap 的 Shader

    [Header("Flowmap 參數")]
    [Range(0.001f, 0.1f)]
    public float rippleScale = 0.01f; // Ripple 梯度計算的尺度
    [Range(0.1f, 10f)]
    public float flowStrength = 1.0f; // Ripple 流向強度
    [Range(0f, 1f)]
    public float rippleInfluence = 0.5f; // Ripple 對 Flowmap 的影響強度
    [Range(0f, 1f)]
    public float flowPersistence = 0.9f; // Flowmap 的持續性

    // 動態 Flowmap 組件引用
    private DynamicFlowmap dynamicFlowmap;

    void Start()
    {
        // 初始化 Ripple RenderTexture
        CurrRT = new RenderTexture(TextureSize, TextureSize, 0, RenderTextureFormat.RFloat);
        PrevRT = new RenderTexture(TextureSize, TextureSize, 0, RenderTextureFormat.RFloat);
        TempRT = new RenderTexture(TextureSize, TextureSize, 0, RenderTextureFormat.RFloat);

        // 初始化 Ripple 材質
        RippleMat = new Material(RippleShader);
        AddMat = new Material(AddShader);

        // 設置 Ripple 紋理到當前物體的材質
        GetComponent<Renderer>().material.SetTexture("_RippleTex", CurrRT);

        // 如果啟用了 Flowmap 整合，設置動態 Flowmap
        if (enableFlowmapIntegration)
        {
            SetupDynamicFlowmap();
        }

        // 啟動 Ripple 計算協程
        StartCoroutine(ripples());
    }

    // 設置動態 Flowmap
    void SetupDynamicFlowmap()
    {
        // 檢查是否已有 DynamicFlowmap 組件
        dynamicFlowmap = GetComponent<DynamicFlowmap>();

        // 如果沒有，添加一個
        if (dynamicFlowmap == null)
        {
            dynamicFlowmap = gameObject.AddComponent<DynamicFlowmap>();
        }

        // 設置 DynamicFlowmap 的參數
        dynamicFlowmap.originalFlowmap = originalFlowmap;
        dynamicFlowmap.rippleHeightRT = CurrRT; // 使用 Ripple 高度圖
        dynamicFlowmap.rippleFlowShader = rippleFlowShader;
        dynamicFlowmap.flowmapBlendShader = flowmapBlendShader;
        dynamicFlowmap.rippleScale = rippleScale;
        dynamicFlowmap.flowStrength = flowStrength;
        dynamicFlowmap.blendFactor = rippleInfluence;
        dynamicFlowmap.persistence = flowPersistence;
        dynamicFlowmap.targetMaterial = GetComponent<Renderer>().material;
    }

    // 更新 DynamicFlowmap 的參數
    void UpdateDynamicFlowmapParameters()
    {
        if (dynamicFlowmap != null)
        {
            dynamicFlowmap.rippleScale = rippleScale;
            dynamicFlowmap.flowStrength = flowStrength;
            dynamicFlowmap.blendFactor = rippleInfluence;
            dynamicFlowmap.persistence = flowPersistence;
        }
    }

    IEnumerator ripples()
    {
        // 原有的 Ripple 計算邏輯
        AddMat.SetTexture("_ObjectsRT", ObjectsRT);
        AddMat.SetTexture("_CurrentRT", CurrRT);
        Graphics.Blit(null, TempRT, AddMat);

        RenderTexture rt0 = TempRT;
        TempRT = CurrRT;
        CurrRT = rt0;

        RippleMat.SetTexture("_PrevRT", PrevRT);
        RippleMat.SetTexture("_CurrentRT", CurrRT);
        Graphics.Blit(null, TempRT, RippleMat);
        Graphics.Blit(TempRT, PrevRT);

        RenderTexture rt = PrevRT;
        PrevRT = CurrRT;
        CurrRT = rt;

        // 如果啟用了 Flowmap 整合，更新 DynamicFlowmap 的參數
        if (enableFlowmapIntegration && dynamicFlowmap != null)
        {
            UpdateDynamicFlowmapParameters();
            // 注意：DynamicFlowmap 會在其自己的 Update 方法中更新 Flowmap
        }

        yield return null;
        StartCoroutine(ripples());
    }

    void OnDestroy()
    {
        // 釋放資源
        if (CurrRT != null) CurrRT.Release();
        if (PrevRT != null) PrevRT.Release();
        if (TempRT != null) TempRT.Release();
    }
}
