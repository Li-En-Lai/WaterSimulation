using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class EyeTest : MonoBehaviour
{
    public Camera Cameraman; // 將類型改為 Camera
    public ParticleSystem ripple;
    private bool inWater;
    private float heightOffset = 0.1f; // 調整高度

    void Start()
    {
        Application.targetFrameRate = 60;

        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
    }

    void Update()
    {
        UpdatePlayerPosition();
        CheckWaterCollision();
    }

    void UpdatePlayerPosition()
    {
        // 將物件的位置設置為頭盔的位置
        transform.position = Cameraman.transform.position + new Vector3(0, heightOffset, 0); // 調整高度使其在頭盔底下
        transform.rotation = Cameraman.transform.rotation; // 讓物件跟隨頭盔的旋轉
    }

    void CheckWaterCollision()
    {
        // 檢查水面碰撞
        float height = Mathf.Abs(heightOffset); // 使用高度偏移的絕對值
        inWater = Physics.Raycast(transform.position + -Vector3.up * height, Vector3.down, height * 2, LayerMask.GetMask("Water"));

        if (inWater)
        {
            ripple.transform.position = transform.position;
            ripple.gameObject.SetActive(true);
            ripple.Emit(transform.position, Vector3.zero, 5, 0.1f, Color.white);
        }
        else
        {
            ripple.gameObject.SetActive(false);
        }
    }
}