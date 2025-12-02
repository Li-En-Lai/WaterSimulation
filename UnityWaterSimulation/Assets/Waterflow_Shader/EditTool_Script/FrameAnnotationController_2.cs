using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using Oculus.Interaction; // 確保已引入 Oculus Interaction SDK

public class FrameAnnotationController_2 : MonoBehaviour
{
    [Header("UI 元件")]
    public RawImage targetImage; // 用於顯示和標註的圖像

    [Header("標註設定")]
    public Color annotationColor = Color.red; // 標註點的顏色
    public float pointSize = 5f; // 標註點的大小(像素)

    [Header("互動設定")]
    public Transform rayInteractor; // Oculus Interaction SDK 的 RayInteractor

    [Header("網路連線")]
    public FlowMapClient flowMapClient; // 用於與伺服器通訊的客戶端

    // 儲存所有標註點的像素座標
    private List<Vector2Int> annotationPoints = new List<Vector2Int>();

    // 用於繪製標註點的紋理
    private Texture2D annotationTexture;
    private Texture2D originalTexture;
    private bool isAnnotating = false;

    // 上一次標註的位置，用於防止重複標註同一位置
    private Vector2Int lastAnnotatedPosition = new Vector2Int(-1, -1);

    void Start()
    {
        // 確保目標圖像已設置
        if (targetImage == null)
        {
            Debug.LogError("請設置目標圖像 (RawImage)!");
            enabled = false;
            return;
        }

        // 訂閱 FlowMapClient 的 Frame 接收事件
        if (flowMapClient != null)
        {
            flowMapClient.OnFrameReceived += OnFrameReceived;
        }
        else
        {
            Debug.LogError("請設置 FlowMapClient!");
            enabled = false;
        }
    }

    void Update()
    {
        // 檢查是否有有效的紋理可以標註
        if (!isAnnotating || annotationTexture == null)
            return;

        // 檢查 Trigger 按鈕是否被按下
        bool triggerPressed = OVRInput.GetDown(OVRInput.Button.PrimaryIndexTrigger) ||
                              OVRInput.GetDown(OVRInput.Button.SecondaryIndexTrigger);

        if (triggerPressed && rayInteractor != null)
        {
            // 執行射線檢測，檢查是否點擊了 UI 元素
            Ray ray = new Ray(rayInteractor.position, rayInteractor.forward);
            RaycastHit hit;

            // 檢查是否擊中了 UI 元素
            if (Physics.Raycast(ray, out hit))
            {
                // 如果擊中的是 RawImage 所在的 GameObject
                if (hit.collider.gameObject == targetImage.gameObject)
                {
                    // 將世界座標轉換為 UI 座標
                    Vector2 localPoint;
                    RectTransformUtility.ScreenPointToLocalPointInRectangle(
                        targetImage.rectTransform,
                        hit.point,
                        null, // 不使用相機，因為我們已經有世界座標
                        out localPoint
                    );

                    // 將 UI 座標轉換為紋理座標 (像素座標)
                    Vector2 normalizedPoint = new Vector2(
                        (localPoint.x + targetImage.rectTransform.rect.width / 2) / targetImage.rectTransform.rect.width,
                        (localPoint.y + targetImage.rectTransform.rect.height / 2) / targetImage.rectTransform.rect.height
                    );

                    Vector2Int pixelPoint = new Vector2Int(
                        Mathf.FloorToInt(normalizedPoint.x * annotationTexture.width),
                        Mathf.FloorToInt(normalizedPoint.y * annotationTexture.height)
                    );

                    // 防止重複標註同一位置
                    if (pixelPoint != lastAnnotatedPosition)
                    {
                        // 添加標註點
                        AddAnnotationPoint(pixelPoint);
                        lastAnnotatedPosition = pixelPoint;
                    }
                }
            }
        }

        // 重置上一次標註的位置，當 Trigger 釋放時
        if (OVRInput.GetUp(OVRInput.Button.PrimaryIndexTrigger) ||
            OVRInput.GetUp(OVRInput.Button.SecondaryIndexTrigger))
        {
            lastAnnotatedPosition = new Vector2Int(-1, -1);
        }
    }

    // 當接收到新的 Frame 時調用
    private void OnFrameReceived(Texture2D frameTexture)
    {
        // 清空之前的標註點
        annotationPoints.Clear();

        // 保存原始紋理的副本
        if (originalTexture != null)
            Destroy(originalTexture);

        originalTexture = new Texture2D(frameTexture.width, frameTexture.height, TextureFormat.RGB24, false);
        Graphics.CopyTexture(frameTexture, originalTexture);

        // 創建新的標註紋理
        if (annotationTexture != null)
            Destroy(annotationTexture);

        annotationTexture = new Texture2D(frameTexture.width, frameTexture.height, TextureFormat.RGB24, false);
        Graphics.CopyTexture(frameTexture, annotationTexture);

        // 設置標註紋理到 UI
        targetImage.texture = annotationTexture;

        // 開始標註模式
        isAnnotating = true;

        Debug.Log($"已接收新 Frame，尺寸: {frameTexture.width}x{frameTexture.height}，準備標註");
    }

    // 添加標註點
    private void AddAnnotationPoint(Vector2Int pixelPoint)
    {
        // 檢查座標是否在紋理範圍內
        if (pixelPoint.x < 0 || pixelPoint.x >= annotationTexture.width ||
            pixelPoint.y < 0 || pixelPoint.y >= annotationTexture.height)
        {
            Debug.LogWarning($"標註點 ({pixelPoint.x}, {pixelPoint.y}) 超出紋理範圍!");
            return;
        }

        // 添加到標註點列表
        annotationPoints.Add(pixelPoint);

        // 在紋理上繪製標註點
        int halfSize = Mathf.FloorToInt(pointSize / 2);
        for (int y = -halfSize; y <= halfSize; y++)
        {
            for (int x = -halfSize; x <= halfSize; x++)
            {
                int drawX = pixelPoint.x + x;
                int drawY = pixelPoint.y + y;

                // 確保繪製範圍在紋理內
                if (drawX >= 0 && drawX < annotationTexture.width &&
                    drawY >= 0 && drawY < annotationTexture.height)
                {
                    annotationTexture.SetPixel(drawX, drawY, annotationColor);
                }
            }
        }

        // 應用變更
        annotationTexture.Apply();

        Debug.Log($"添加標註點: ({pixelPoint.x}, {pixelPoint.y})，目前共有 {annotationPoints.Count} 個標註點");
    }

    // 清除所有標註點
    public void ClearAnnotations()
    {
        if (originalTexture != null && annotationTexture != null)
        {
            // 恢復原始紋理
            Graphics.CopyTexture(originalTexture, annotationTexture);
            annotationTexture.Apply();

            // 清空標註點列表
            annotationPoints.Clear();

            Debug.Log("已清除所有標註點");
        }
    }

    // 將標註點發送到伺服器
    public void SendPointsToServer()
    {
        if (flowMapClient != null && annotationPoints.Count > 0)
        {
            // 使用 FlowMapClient 發送標註點
            flowMapClient.SendAnnotationPoints(annotationPoints);

            Debug.Log($"已發送 {annotationPoints.Count} 個標註點到伺服器");

            // 發送後可以選擇清除標註
            // ClearAnnotations();
        }
        else
        {
            Debug.LogWarning("沒有標註點可發送或 FlowMapClient 未設置!");
        }
    }

    void OnDestroy()
    {
        // 取消訂閱事件
        if (flowMapClient != null)
        {
            flowMapClient.OnFrameReceived -= OnFrameReceived;
        }

        // 釋放資源
        if (originalTexture != null)
            Destroy(originalTexture);

        if (annotationTexture != null)
            Destroy(annotationTexture);
    }
}
