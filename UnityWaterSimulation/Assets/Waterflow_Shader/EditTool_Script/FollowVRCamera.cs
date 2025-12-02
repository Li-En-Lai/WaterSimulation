using UnityEngine;

public class FollowVRCamera : MonoBehaviour
{
    [Header("目標 VR 相機")]
    public Transform targetCamera;

    [Header("UI 距離與偏移")]
    public float distanceFromCamera = 2.0f;         // 距離相機多遠
    public Vector3 offset = new Vector3(0, -0.3f, 0); // 額外的 Y 偏移

    [Header("是否平滑跟隨")]
    public bool smoothFollow = true;
    public float followSpeed = 5f;

    void Start()
    {
        // 若未指定目標相機，預設使用 Main Camera
        if (targetCamera == null && Camera.main != null)
        {
            targetCamera = Camera.main.transform;
        }
    }

    void LateUpdate()
    {
        if (targetCamera == null) return;

        // 計算目標位置：相機前方一定距離加上偏移
        Vector3 targetPosition = targetCamera.position + targetCamera.forward * distanceFromCamera + offset;

        // 更新位置
        if (smoothFollow)
        {
            transform.position = Vector3.Lerp(transform.position, targetPosition, Time.deltaTime * followSpeed);
        }
        else
        {
            transform.position = targetPosition;
        }

        // 朝向相機（讓 UI 面向使用者）
        transform.rotation = Quaternion.LookRotation(transform.position - targetCamera.position);
    }
}
