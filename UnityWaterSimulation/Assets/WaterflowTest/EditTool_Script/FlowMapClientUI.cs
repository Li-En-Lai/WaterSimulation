using UnityEngine;
using UnityEngine.UI;

public class FlowMapClientUI : MonoBehaviour
{
    [Header("UI 元件")]
    public Button connectButton;
    public Button disconnectButton;
    public Button requestFrameButton;
    public Button sendEditedFrameButton;
    public Button sendAnnotationPointsButton; // 新增按鈕
    public RawImage frameDisplay; // 顯示 Frame 的 UI

    [Header("控制的 FlowMapClient")]
    public FlowMapClient flowMapClient;

    [Header("標註控制器")]
    public FrameAnnotationController annotationController; // 新增：用來呼叫SendPointsToServer

    void Start()
    {
        if (connectButton) connectButton.onClick.AddListener(OnConnectClicked);
        if (disconnectButton) disconnectButton.onClick.AddListener(OnDisconnectClicked);
        if (requestFrameButton) requestFrameButton.onClick.AddListener(OnRequestFrameClicked);
        if (sendEditedFrameButton) sendEditedFrameButton.onClick.AddListener(OnSendEditedFrameClicked);

        // 新增按鈕綁定
        if (sendAnnotationPointsButton)
            sendAnnotationPointsButton.onClick.AddListener(OnSendAnnotationPointsClicked);

        // 當 Frame 接收完成，顯示到 UI 上
        flowMapClient.OnFrameReceived += (Texture2D tex) =>
        {
            if (frameDisplay != null)
            {
                frameDisplay.texture = tex;
                Debug.Log("UI 已更新顯示接收到的 Frame");
            }
        };
    }

    void OnConnectClicked()
    {
        flowMapClient.Connect();
        Debug.Log("[UI] Connect Button 點擊：嘗試連接伺服器");
    }

    void OnDisconnectClicked()
    {
        flowMapClient.Disconnect();
        Debug.Log("[UI] Disconnect Button 點擊：中斷與伺服器連線");
    }

    void OnRequestFrameClicked()
    {
        flowMapClient.RequestCurrentFrame();
        Debug.Log("[UI] Request Frame Button 點擊：請求當前 Frame");
    }

    void OnSendEditedFrameClicked()
    {
        Texture2D currentFrame = flowMapClient.GetCurrentFrame();
        if (currentFrame != null)
        {
            flowMapClient.SendEditedFrame(currentFrame); // 模擬編輯（實際上是原封不動送回）
            Debug.Log("[UI] Send Edited Frame Button 點擊：送出未修改的 Frame 給 Server");
        }
        else
        {
            Debug.LogWarning("[UI] 尚未接收到 Frame，無法送出");
        }
    }

    void OnSendAnnotationPointsClicked()
    {
        if (annotationController != null)
        {
            annotationController.SendPointsToServer();
        }
        else
        {
            Debug.LogWarning("[UI] annotationController 未綁定，無法發送標記點");
        }
    }
}