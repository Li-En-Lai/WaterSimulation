using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class DynamicFlowmap : MonoBehaviour
{
    [Header("原始 Flowmap 設定")]
    public Texture2D originalFlowmap; // 原始靜態 Flowmap

    [Header("Ripple 設定")]
    public RenderTexture rippleHeightRT; // Ripple 高度圖，可以從外部傳入

    [Header("動態 Flowmap 設定")]
    [SerializeField] private RenderTexture dynamicFlowmapRT; // 動態 Flowmap RenderTexture
    private RenderTexture tempRippleFlowRT; // 臨時存儲 Ripple 流向的 RenderTexture

    [Header("Shader 參考")]
    public Shader rippleFlowShader; // 計算 Ripple 流向的 Shader
    public Shader flowmapBlendShader; // 混合 Flowmap 的 Shader
    private Material rippleFlowMaterial;
    private Material flowmapBlendMaterial;

    [Header("參數設定")]
    [Range(0.001f, 0.1f)]
    public float rippleScale = 0.01f; // Ripple 梯度計算的尺度
    [Range(0.1f, 10f)]
    public float flowStrength = 1.0f; // Ripple 流向強度
    [Range(0f, 1f)]
    public float blendFactor = 0.5f; // Ripple 對 Flowmap 的影響強度
    [Range(0f, 1f)]
    public float persistence = 0.9f; // Flowmap 的持續性（值越高，變化越慢恢復越慢）

    [Header("目標材質設定")]
    public Material targetMaterial; // 需要使用 Flowmap 的目標材質
    public string flowmapPropertyName = "_FlowMap"; // 材質中 Flowmap 的屬性名稱

    // 提供對動態 Flowmap 的公開訪問
    public RenderTexture DynamicFlowmapTexture => dynamicFlowmapRT;

    void Start()
    {
        InitializeDynamicFlowmap();
    }

    void Update()
    {
        // 如果有 Ripple 高度圖，更新 Flowmap
        if (rippleHeightRT != null)
        {
            UpdateFlowmapWithRipple();
        }
    }

    void OnDestroy()
    {
        // 釋放資源
        if (dynamicFlowmapRT != null) dynamicFlowmapRT.Release();
        if (tempRippleFlowRT != null) tempRippleFlowRT.Release();

        // 釋放材質
        if (rippleFlowMaterial != null) Destroy(rippleFlowMaterial);
        if (flowmapBlendMaterial != null) Destroy(flowmapBlendMaterial);
    }

    // 初始化動態 Flowmap
    void InitializeDynamicFlowmap()
    {
        // 確保原始 Flowmap 存在
        if (originalFlowmap == null)
        {
            Debug.LogError("原始 Flowmap 未指定！請指定一個 Texture2D 作為基礎 Flowmap。");
            return;
        }

        // 檢查 Shader 是否存在
        if (rippleFlowShader == null || flowmapBlendShader == null)
        {
            Debug.LogError("缺少必要的 Shader！請確保 RippleFlow 和 FlowmapBlend Shader 已指定。");
            return;
        }

        // 創建材質
        rippleFlowMaterial = new Material(rippleFlowShader);
        flowmapBlendMaterial = new Material(flowmapBlendShader);

        // 設置材質參數
        rippleFlowMaterial.SetFloat("_RippleScale", rippleScale);
        rippleFlowMaterial.SetFloat("_FlowStrength", flowStrength);

        // 創建動態 Flowmap RenderTexture
        dynamicFlowmapRT = new RenderTexture(
            originalFlowmap.width,
            originalFlowmap.height,
            0,
            RenderTextureFormat.ARGBFloat, // 使用浮點格式以保持精確度
            RenderTextureReadWrite.Linear
        );
        dynamicFlowmapRT.Create();

        // 創建臨時 RenderTexture 用於存儲 Ripple 流向
        tempRippleFlowRT = new RenderTexture(
            dynamicFlowmapRT.width,
            dynamicFlowmapRT.height,
            0,
            dynamicFlowmapRT.format,
            RenderTextureReadWrite.Linear
        );
        tempRippleFlowRT.Create();

        // 將原始 Flowmap 複製到動態 Flowmap
        Graphics.Blit(originalFlowmap, dynamicFlowmapRT);

        // 將動態 Flowmap 設置到目標材質
        if (targetMaterial != null)
        {
            targetMaterial.SetTexture(flowmapPropertyName, dynamicFlowmapRT);
        }
        else
        {
            Debug.LogWarning("未指定目標材質！動態 Flowmap 已創建，但未應用到任何材質。");
        }
    }

    // 使用 Ripple 高度圖更新 Flowmap
    void UpdateFlowmapWithRipple()
    {
        // 更新材質參數
        rippleFlowMaterial.SetFloat("_RippleScale", rippleScale);
        rippleFlowMaterial.SetFloat("_FlowStrength", flowStrength);
        flowmapBlendMaterial.SetFloat("_BlendFactor", blendFactor);
        flowmapBlendMaterial.SetFloat("_Persistence", persistence);

        // 步驟 1: 從 Ripple 高度圖計算流向
        rippleFlowMaterial.SetTexture("_RippleTex", rippleHeightRT);
        Graphics.Blit(null, tempRippleFlowRT, rippleFlowMaterial);

        // 步驟 2: 混合原始 Flowmap 和 Ripple 流向
        flowmapBlendMaterial.SetTexture("_OriginalFlowmap", originalFlowmap);
        flowmapBlendMaterial.SetTexture("_RippleFlowmap", tempRippleFlowRT);
        flowmapBlendMaterial.SetTexture("_CurrentFlowmap", dynamicFlowmapRT);

        // 創建臨時 RenderTexture 用於存儲混合結果
        RenderTexture blendResultRT = RenderTexture.GetTemporary(
            dynamicFlowmapRT.width,
            dynamicFlowmapRT.height,
            0,
            dynamicFlowmapRT.format
        );

        // 將混合結果寫入臨時 RenderTexture
        Graphics.Blit(null, blendResultRT, flowmapBlendMaterial);

        // 將結果複製到動態 Flowmap
        Graphics.Blit(blendResultRT, dynamicFlowmapRT);

        // 釋放臨時 RenderTexture
        RenderTexture.ReleaseTemporary(blendResultRT);
    }

    // 重置 Flowmap 到原始狀態
    public void ResetFlowmap()
    {
        if (originalFlowmap != null && dynamicFlowmapRT != null)
        {
            Graphics.Blit(originalFlowmap, dynamicFlowmapRT);
        }
    }

    // 設置 Ripple 高度圖（可從外部調用）
    public void SetRippleHeightTexture(RenderTexture rippleTexture)
    {
        rippleHeightRT = rippleTexture;
    }
}
