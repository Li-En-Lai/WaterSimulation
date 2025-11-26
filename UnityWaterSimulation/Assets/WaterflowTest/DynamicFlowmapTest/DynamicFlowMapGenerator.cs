using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class DynamicFlowMapGenerator : MonoBehaviour
{
    [Header("FlowMap 設置")]
    public Texture2D staticFlowMap; // 預先製作的靜態 FlowMap
    public RenderTexture dynamicFlowMap; // 動態 FlowMap
    public int resolution = 1024; // FlowMap 解析度

    [Header("物體影響設置")]
    public float influenceRadius = 1.0f; // 物體影響半徑
    public float influenceStrength = 0.5f; // 物體影響強度
    public float recoveryRate = 0.01f; // 水流恢復速度

    [Header("材質設置")]
    public Material waterMaterial; // 水面材質

    // 繪製用材質
    private Material flowDrawMaterial;

    // 暫存 RenderTexture
    private RenderTexture tempRenderTexture;

    [Header("物體檢測")]
    public LayerMask objectLayer; // 需要檢測的物體層
    public float checkInterval = 0.05f; // 檢測間隔

    //用於Render Flowmap的Camera
    private Camera flowMapCamera;

    [Range(0, 1)]
    public float minVelocityThreshold = 0.1f; // 最小速度閾值

    [Range(0, 10)]
    public float velocityMultiplier = 1.0f; // 速度乘數


    // Start is called before the first frame update
    void Start()
    {
        InitializeFlowMap();
        StartCoroutine(UpdateFlowMap());

    }
    IEnumerator UpdateFlowMap()
    {
        while (true)
        {
            // 檢測並更新水面上的物體
            UpdateObjectsInfluence();

            // 緩慢恢復到靜態 FlowMap
            RecoverFlowMap();

            yield return new WaitForSeconds(checkInterval);
        }
    }

    // Update is called once per frame
    void Update()
    {
        waterMaterial.SetTexture("_FlowMap", dynamicFlowMap);
    }
    void OnDestroy()
    {
        // 釋放資源
        if (dynamicFlowMap != null)
        {
            dynamicFlowMap.Release();
        }

        if (tempRenderTexture != null)
        {
            tempRenderTexture.Release();
        }
    }

    void InitializeFlowMap()
    {
        // 創建動態 FlowMap
        dynamicFlowMap = new RenderTexture(resolution, resolution, 0, RenderTextureFormat.ARGBFloat);
        dynamicFlowMap.enableRandomWrite = true;
        dynamicFlowMap.Create();

        // 創建暫存 RenderTexture
        tempRenderTexture = new RenderTexture(resolution, resolution, 0, RenderTextureFormat.ARGBFloat);
        tempRenderTexture.enableRandomWrite = true;
        tempRenderTexture.Create();

        // 創建繪製用材質
        flowDrawMaterial = new Material(Shader.Find("Hidden/FlowMapDraw"));

        // 將靜態 FlowMap 複製到動態 FlowMap
        Graphics.Blit(staticFlowMap, dynamicFlowMap);
        Debug.Log("靜態 FlowMap 已複製到動態 FlowMap");

        // 將動態 FlowMap 設置到水面材質
        waterMaterial.SetTexture("_FlowMap", dynamicFlowMap);
        Debug.Log($"動態 FlowMap 已設置到水面材質，屬性名稱:_FlowMap");
    }

    void UpdateObjectsInfluence()
    {
        // 獲取場景中所有符合條件的物體
        Collider[] objects = Physics.OverlapBox(transform.position,
            new Vector3(transform.localScale.x * 0.5f, influenceRadius, transform.localScale.z * 0.5f),
            transform.rotation, objectLayer);

        foreach (Collider obj in objects)
        {
            // 獲取物體在水面上的投影位置
            Vector3 objPos = obj.transform.position;
            Vector3 localPos = transform.InverseTransformPoint(objPos);

            // 轉換為 UV 座標 (假設水面是 XZ 平面)
            Vector2 uvPos = new Vector2(localPos.x / transform.localScale.x + 0.5f,
                                       localPos.z / transform.localScale.z + 0.5f);

            // 獲取物體的移動方向和速度
            Rigidbody rb = obj.GetComponent<Rigidbody>();
            Vector3 velocity = Vector3.zero;

            if (rb != null)
            {
                velocity = rb.velocity;
            }

            // 將速度投影到水面平面
            Vector2 flowDirection = new Vector2(velocity.x, velocity.z).normalized;
            float speed = new Vector2(velocity.x, velocity.z).magnitude;

            // 設置材質參數
            flowDrawMaterial.SetVector("_Position", new Vector4(uvPos.x, uvPos.y, 0, 0));

            // 只有當速度超過閾值時才影響 FlowMap
            if (speed > minVelocityThreshold)
            {
                // 將速度映射到合適的範圍
                float normalizedSpeed = Mathf.Clamp01(speed * velocityMultiplier);
                flowDrawMaterial.SetVector("_Direction", new Vector4(flowDirection.x, flowDirection.y, 0, 0) * normalizedSpeed);
                flowDrawMaterial.SetFloat("_Radius", influenceRadius / Mathf.Max(transform.localScale.x, transform.localScale.z));
                flowDrawMaterial.SetFloat("_Strength", influenceStrength);

                // 繪製物體影響
                Graphics.Blit(dynamicFlowMap, tempRenderTexture, flowDrawMaterial, 0);

                // 交換 RenderTexture
                RenderTexture rt = dynamicFlowMap;
                dynamicFlowMap = tempRenderTexture;
                tempRenderTexture = rt;
            }
            //flowDrawMaterial.SetVector("_Direction", new Vector4(flowDirection.x, flowDirection.y, 0, 0) * Mathf.Min(speed, 1.0f));
            //flowDrawMaterial.SetFloat("_Radius", influenceRadius / Mathf.Max(transform.localScale.x, transform.localScale.z));
            //flowDrawMaterial.SetFloat("_Strength", influenceStrength);

            // 繪製物體影響
            //Graphics.Blit(dynamicFlowMap, tempRenderTexture, flowDrawMaterial, 0);

            // 交換 RenderTexture
            //RenderTexture rt = dynamicFlowMap;
            //dynamicFlowMap = tempRenderTexture;
            //tempRenderTexture = rt;
        }
    }

    void RecoverFlowMap()
    {
        // 設置恢復參數
        flowDrawMaterial.SetTexture("_StaticFlowMap", staticFlowMap);
        flowDrawMaterial.SetFloat("_RecoveryRate", recoveryRate);

        // 使用恢復 Pass
        Graphics.Blit(dynamicFlowMap, tempRenderTexture, flowDrawMaterial, 1);

        // 交換 RenderTexture
        RenderTexture rt = dynamicFlowMap;
        dynamicFlowMap = tempRenderTexture;
        tempRenderTexture = rt;
    }
    // 添加公開方法以便外部調用
    public void ResetFlowMap()
    {
        Graphics.Blit(staticFlowMap, dynamicFlowMap);
    }

    public void SetInfluenceParameters(float radius, float strength)
    {
        influenceRadius = radius;
        influenceStrength = strength;
    }
}
