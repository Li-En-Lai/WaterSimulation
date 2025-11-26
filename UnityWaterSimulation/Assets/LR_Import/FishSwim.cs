using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class FishSwim : MonoBehaviour
{
    public float radius = 5f; // 魚的旋轉半徑
    public float speed = 1f; // 旋轉速度
    private float angle;

    void Update()
    {
        // 計算當前角度
        angle += speed * Time.deltaTime;

        // 計算魚的位置
        float x = Mathf.Cos(angle) * radius;
        float z = Mathf.Sin(angle) * radius;

        // 設定魚的位置
        transform.position = new Vector3(x, transform.position.y, z);
    }
}