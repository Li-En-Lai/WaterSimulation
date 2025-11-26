using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class GetHeadsetPosition : MonoBehaviour
{
    //在Inspector中指派CenterEyeAnchor
    [SerializeField]
    private Transform centerEyeAnchor;

    //Particle System的Prefab物件
    [SerializeField]
    private GameObject particleSystemPrefab;

    //實例化的粒子系統
    //因為Prefab並非場景中的實際物件，需先進行實例化才能夠在場景中運行
    private GameObject particleSystemInstance;

    //儲存VR頭盔上一個Frame的位置
    private Vector3 lastPosition;

    //用於檢查在執行更新前是否已進行初始化
    private bool isInitialized = false;


    // Start is called before the first frame update
    private void Start()
    {
        // 檢查VR頭盔物件(CenterEyeAnchor)是否已於Inspector中指派
        if (centerEyeAnchor == null)
        {
            Debug.LogError("未在 Inspector 中指派 CenterEyeAnchor！");
            return;
        }
        // 檢查用於觸發Ripple效果的Particle System Prefab是否已於Inspector中指派
        if (particleSystemPrefab == null)
        {
            Debug.LogError("未在 Inspector 中指派 Particle System Prefab！");
            return;
        }
        // VR頭盔上一個Frame的位置初始化
        lastPosition = centerEyeAnchor.position;

        //預先實例化Particle System Prefab但不啟用
        particleSystemInstance = Instantiate(particleSystemPrefab, centerEyeAnchor.position, Quaternion.identity);
        particleSystemInstance.name = "HeadsetParticle";

        //確保初始的Particle System是停止的
        ParticleSystem particleSystem = particleSystemInstance.GetComponent<ParticleSystem>();
        if (particleSystem != null)
        {
            particleSystem.Stop();
        }
        isInitialized = true;
    }

    // Update is called once per frame
    private void Update()
    {
        if (!isInitialized) return;

        // VR頭盔當前位置
        Vector3 currentPosition = centerEyeAnchor.position;
        //Debug.Log($"頭盔當前位置:{currentPosition}");

        // 僅考慮水平位置變化(x和z軸)
        Vector2 currentHorizontalPos = new Vector2(currentPosition.x, currentPosition.z);
        Vector2 lastHorizontalPos = new Vector2(lastPosition.x, lastPosition.z);

        // 計算水平位置變化量
        float horizontalMovement = Vector2.Distance(currentHorizontalPos, lastHorizontalPos);

        // 更新Particle System位置
        particleSystemInstance.transform.position = currentPosition;
        // 檢查水平位置是否有顯著變化
        if (horizontalMovement > 0)
        {
            // 水平位置有顯著變化，啟用粒子系統
            ParticleSystem particleSystem = particleSystemInstance.GetComponent<ParticleSystem>();
            if (particleSystem != null && !particleSystem.isPlaying)
            {
                particleSystem.Play();
                Debug.Log($"頭盔水平移動: {horizontalMovement}，啟動粒子系統");
            }
        }
        else
        {
            // 水平位置變化不大，停止粒子系統
            ParticleSystem particleSystem = particleSystemInstance.GetComponent<ParticleSystem>();
            if (particleSystem != null && particleSystem.isPlaying)
            {
                particleSystem.Stop();
                Debug.Log($"頭盔水平移動: {horizontalMovement}，停止粒子系統");
            }
        }
        // 更新上一幀位置
        lastPosition = currentPosition;
    }
}
