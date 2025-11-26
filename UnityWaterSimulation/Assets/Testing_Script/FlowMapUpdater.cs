using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class FlowMapUpdater : MonoBehaviour
{
    public RippleToFlowMap flowMapConverter;
    public Renderer waterRenderer;
    public string flowMapPropertyName = "_DynamicFlowMap";

    void Start()
    {
        if (flowMapConverter == null || waterRenderer == null)
        {
            Debug.LogError("FlowMapUpdater: Missing required references!");
            return;
        }
    }

    void Update()
    {
        if (flowMapConverter == null || waterRenderer == null)
            return;

        // 獲取動態 FlowMap
        RenderTexture dynamicFlowMap = flowMapConverter.GetDynamicFlowMap();

        if (dynamicFlowMap != null)
        {
            // 將動態 FlowMap 分配給水面材質
            waterRenderer.material.SetTexture(flowMapPropertyName, dynamicFlowMap);
        }
    }
}
