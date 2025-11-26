using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR;

public class PlayerMovement : MonoBehaviour
{
    public Camera headsetCamera; // 在 Inspector 中設置的相機
    public float assignY = 0;
    private Vector3 pos = Vector3.zero;

    void Start()
    {
        if (headsetCamera == null)
        {
            Debug.LogError("Set Camera");
        }
    }

    void Update()
    {
        if (headsetCamera != null)
        {
            // 讓物件的位置和方向跟隨相機
            pos = headsetCamera.transform.position;
            pos.y = assignY;
            transform.position = pos;

            // transform.rotation = headsetCamera.transform.rotation;
        }
    }
}