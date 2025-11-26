using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class RippleToFlowMap : MonoBehaviour
{
    [Header("Textures")]
    public RenderTexture rippleTexture;      // 波紋高度場紋理
    public Texture2D baseFlowMapTexture;     // 基礎 FlowMap 紋理 (從 FlowMap Painter)
    public RenderTexture dynamicFlowMapRT;   // 動態生成的 FlowMap
    public RenderTexture tempFlowMapRT;      // 臨時紋理用於 ping-pong 渲染

    [Header("Conversion Settings")]
    [Range(0, 1)]
    public float rippleInfluence = 0.5f;     // 波紋對流動的影響強度
    [Range(0, 1)]
    public float flowPersistence = 0.95f;    // 流動的持續性

    [Header("Update Settings")]
    public bool updateEveryFrame = true;
    public int updateInterval = 2;           // 每隔幾幀更新一次

    [Header("Debug")]
    public bool showDebug = false;
    public Material debugMaterial;
    public GameObject debugPlane;

    private Material conversionMaterial;     // 用於轉換的材質
    private int frameCount = 0;
    private bool initialized = false;

    void Start()
    {
        // 創建轉換材質
        conversionMaterial = new Material(Shader.Find("Custom/RippleToFlowMap"));

        // 初始化動態 FlowMap
        InitializeDynamicFlowMap();

        // 如果需要調試顯示
        if (showDebug)
        {
            SetupDebugDisplay();
        }
    }

    void InitializeDynamicFlowMap()
    {
        if (baseFlowMapTexture == null || dynamicFlowMapRT == null)
            return;

        // 將基礎 FlowMap 複製到動態 FlowMap
        Graphics.Blit(baseFlowMapTexture, dynamicFlowMapRT);
        Graphics.Blit(baseFlowMapTexture, tempFlowMapRT);

        initialized = true;
    }

    void SetupDebugDisplay()
    {
        if (debugMaterial == null)
        {
            debugMaterial = new Material(Shader.Find("Unlit/Texture"));
        }

        if (debugPlane == null)
        {
            // 創建一個平面來顯示 FlowMap
            debugPlane = GameObject.CreatePrimitive(PrimitiveType.Quad);
            debugPlane.name = "FlowMapDebugDisplay";
            debugPlane.transform.position = new Vector3(2, 1, 0);
            debugPlane.transform.parent = transform;
            debugPlane.GetComponent<Renderer>().material = debugMaterial;
        }

        // 將 FlowMap 分配給調試材質
        if (dynamicFlowMapRT != null)
        {
            debugMaterial.SetTexture("_MainTex", dynamicFlowMapRT);
        }
    }

    void Update()
    {
        if (!initialized)
            return;

        // 如果設置為不是每幀更新，則按照指定間隔更新
        if (!updateEveryFrame)
        {
            frameCount++;
            if (frameCount % updateInterval != 0)
                return;
        }

        UpdateFlowMapFromRipple();
    }

    void UpdateFlowMapFromRipple()
    {
        if (rippleTexture == null || baseFlowMapTexture == null ||
            dynamicFlowMapRT == null || tempFlowMapRT == null ||
            conversionMaterial == null)
            return;

        // 設置材質參數
        conversionMaterial.SetTexture("_RippleTexture", rippleTexture);
        conversionMaterial.SetTexture("_BaseFlowMap", baseFlowMapTexture);
        conversionMaterial.SetTexture("_PreviousFlowMap", dynamicFlowMapRT);
        conversionMaterial.SetFloat("_RippleInfluence", rippleInfluence);
        conversionMaterial.SetFloat("_FlowPersistence", flowPersistence);

        // 執行轉換（ping-pong 渲染）
        Graphics.Blit(null, tempFlowMapRT, conversionMaterial);
        Graphics.Blit(tempFlowMapRT, dynamicFlowMapRT);

        // 如果需要調試顯示
        if (showDebug && debugMaterial != null)
        {
            debugMaterial.SetTexture("_MainTex", dynamicFlowMapRT);
        }
    }

    // 提供一個公共方法，讓其他腳本可以獲取動態 FlowMap
    public RenderTexture GetDynamicFlowMap()
    {
        return dynamicFlowMapRT;
    }

    // 提供一個公共方法，讓其他腳本可以重置 FlowMap 到基礎狀態
    public void ResetFlowMap()
    {
        if (baseFlowMapTexture != null && dynamicFlowMapRT != null)
        {
            Graphics.Blit(baseFlowMapTexture, dynamicFlowMapRT);
        }
    }

    void OnDestroy()
    {
        if (conversionMaterial != null)
            Destroy(conversionMaterial);
    }
}
