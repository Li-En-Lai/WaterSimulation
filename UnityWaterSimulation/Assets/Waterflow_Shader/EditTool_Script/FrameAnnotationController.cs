using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using Oculus.Interaction;
using Oculus.Interaction.Input;

public class FrameAnnotationController : MonoBehaviour
{
    public RawImage frameDisplay;      // 顯示Frame的UI
    public FlowMapClient flowMapClient; // 用來傳送座標
    public Transform pokeLocation; // 射線起點
    public Transform oculusCursor; // 射線終點
    public Camera vrCamera; //VR camera
    public OVRInput.Button triggerButton = OVRInput.Button.SecondaryIndexTrigger; //手把Trigger按鍵
    private LineRenderer lineRenderer;
    public float rayLength = 5f; // 射線長度

    private Texture2D workingTexture;
    private List<Vector2Int> annotationPoints = new List<Vector2Int>();
    private bool isFrameReady = false; //控制是否可以對Frame進行標註

    void Start()
    {
        // 初始化 LineRenderer
        /*lineRenderer = gameObject.AddComponent<LineRenderer>();
        lineRenderer.positionCount = 2;
        lineRenderer.material = new Material(Shader.Find("Sprites/Default"));
        lineRenderer.startColor = Color.blue;
        lineRenderer.endColor = Color.blue;
        lineRenderer.startWidth = 0.005f;
        lineRenderer.endWidth = 0.005f;
        lineRenderer.useWorldSpace = true;*/
        // 確保 frameDisplay 的 texture 存在
        if (frameDisplay.texture == null)
        {
            Debug.LogWarning("frameDisplay.texture 是 null，自動建立空白 workingTexture");
            workingTexture = new Texture2D(640, 480, TextureFormat.RGBA32, false);
            frameDisplay.texture = workingTexture;
        }
        else
        {
            CopyFrameTexture();
        }
        SyncBoxCollider(); // 自動補上 BoxCollider(用於射線碰撞)並正確同步大小

        // 當接收到新的Frame時複製一份可編輯的
        flowMapClient.OnFrameReceived += (tex) =>
        {
            Debug.LogWarning($"接收到 Frame 尺寸：{tex.width}x{tex.height}");
            // 先建立 RenderTexture 進行 GPU 到 CPU 的轉換
            RenderTexture rt = RenderTexture.GetTemporary(tex.width, tex.height, 0);
            Graphics.Blit(tex, rt); // 將原始 texture 渲染進 rt 中

            RenderTexture.active = rt;
            workingTexture = new Texture2D(tex.width, tex.height, TextureFormat.RGBA32, false);
            workingTexture.ReadPixels(new Rect(0, 0, tex.width, tex.height), 0, 0);
            workingTexture.Apply();
            RenderTexture.active = null;
            RenderTexture.ReleaseTemporary(rt);

            frameDisplay.texture = workingTexture;
            isFrameReady = true;
        };
    }
    void Update()
    {
        Vector3 start = pokeLocation.position;// 起點位置
        Vector3 end = oculusCursor.position;// 終點位置

        // 更新 LineRenderer 線段位置
        //lineRenderer.SetPosition(0, start);
        //lineRenderer.SetPosition(1, end);

        // 沒有接收到來自 Server傳遞的Frame 時不允許標註
        if (!isFrameReady) return;

        // 按下 Trigger 時進行點擊偵測
        if (OVRInput.GetDown(triggerButton))
        {
            Vector3 direction = (end - start).normalized;
            Debug.LogWarning("按下Trigger");
            // 發出射線
            Ray ray = new Ray(start, direction);
            RaycastHit hit;
            if (Physics.Raycast(ray, out hit))
            {
                if (hit.collider != null && hit.collider.gameObject == frameDisplay.gameObject)
                {
                    Debug.LogWarning($"命中:{hit.collider.gameObject}");

                    Vector2 localPoint = frameDisplay.rectTransform.InverseTransformPoint(hit.point);

                    Vector2Int pixelPos = UIPosToPixel(localPoint);
                    DrawRedDot(pixelPos);
                    annotationPoints.Add(pixelPos);
                    Debug.Log("標註成功於：" + pixelPos);
                }
            }
        }
    }

    void DrawRedDot(Vector2Int pixel)
    {
        if (workingTexture == null)
        {
            Debug.LogWarning("WorkingTexture 尚未初始化！");
            return;
        }

        int radius = 5;
        for (int y = -radius; y <= radius; y++)
        {
            for (int x = -radius; x <= radius; x++)
            {
                if (x * x + y * y <= radius * radius)
                {
                    int px = Mathf.Clamp(pixel.x + x, 0, workingTexture.width - 1);
                    int py = Mathf.Clamp(pixel.y + y, 0, workingTexture.height - 1);
                    workingTexture.SetPixel(px, py, Color.red);
                }
            }
        }
        workingTexture.Apply();
        // 確保 UI 看到的是這張修改過的 texture
        frameDisplay.texture = workingTexture;
        Debug.LogWarning($"workingTex尺寸大小:{workingTexture.width}x{workingTexture.height}");
    }

    Vector2Int UIPosToPixel(Vector2 localPos)
    {
        Rect rect = frameDisplay.rectTransform.rect;

        float u = (localPos.x + rect.width * 0.5f) / rect.width;
        float v = (localPos.y + rect.height * 0.5f) / rect.height;

        int px = Mathf.Clamp(Mathf.RoundToInt(u * workingTexture.width), 0, workingTexture.width - 1);
        int py = Mathf.Clamp(Mathf.RoundToInt(v * workingTexture.height), 0, workingTexture.height - 1);

        return new Vector2Int(px, py);
    }

    public void SendPointsToServer()
    {
        if (annotationPoints.Count > 0)
        {
            flowMapClient.SendAnnotationPoints(annotationPoints);
            annotationPoints.Clear();
            //Debug.Log("標記點座標已送出並清空");
        }
        else
        {
            Debug.Log("沒有標記點可送出");
        }
    }

    void CopyFrameTexture()
    {
        Texture2D src = (Texture2D)frameDisplay.texture;
        workingTexture = new Texture2D(src.width, src.height, TextureFormat.RGBA32, false);
        Graphics.CopyTexture(src, workingTexture);
        frameDisplay.texture = workingTexture;
    }

    void SyncBoxCollider()
    {
        RectTransform rt = frameDisplay.rectTransform;
        BoxCollider collider = frameDisplay.GetComponent<BoxCollider>();
        if (collider == null)
            collider = frameDisplay.gameObject.AddComponent<BoxCollider>();

        Vector2 size = rt.rect.size;
        collider.size = new Vector3(size.x, size.y, 0.01f);
        collider.center = Vector3.zero;
    }

}
