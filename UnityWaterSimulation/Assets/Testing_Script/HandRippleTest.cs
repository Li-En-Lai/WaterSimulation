using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class HandRippleTest : MonoBehaviour
{
    public GameObject ParticleHand_L;
    public GameObject ParticleHand_R;
    public GameObject OculusHand_L;
    public GameObject OculusHand_R;

    [Header("水面設定")]
    public Transform waterSurface; // 水面物件，在Inspector中指定
    [Header("手與水面高度差閥值")]
    public float threshold = 0.5f;

    void Start()
    {
        ParticleHand_L.SetActive(false);
        ParticleHand_R.SetActive(false);

        if (waterSurface == null)
        {
            Debug.LogError("未指定水面物件!");
        }
    }

    void FixedUpdate()
    {
        if (waterSurface == null) return;

        float waterHeight = waterSurface.position.y;

        Debug.Log($"水面高度: {waterHeight}, 左手高度: {OculusHand_L.transform.position.y}, 右手高度: {OculusHand_R.transform.position.y}");

        // 檢查左手是否在水面以下
        if (Mathf.Abs(waterHeight-OculusHand_L.transform.position.y) <= threshold)
        {
            ParticleHand_L.SetActive(true);
            ParticleHand_L.transform.position = new Vector3(
                OculusHand_L.transform.position.x,
                waterHeight, // 將粒子系統放在水面高度
                OculusHand_L.transform.position.z
            );
        }
        else
        {
            ParticleHand_L.SetActive(false);
        }

        // 檢查右手是否在水面以下
        if (Mathf.Abs(waterHeight-OculusHand_R.transform.position.y) < threshold)
        {
            ParticleHand_R.SetActive(true);
            ParticleHand_R.transform.position = new Vector3(
                OculusHand_R.transform.position.x,
                waterHeight, // 將粒子系統放在水面高度
                OculusHand_R.transform.position.z
            );
        }
        else
        {
            ParticleHand_R.SetActive(false);
        }
    }
}
